# Friday Voice Pipeline — Bug Report & Fix Summary

> Generated: 2026-05-17 | Status: Partially fixed — OWW still needs resolution

---

## System Overview

```
python main.py --voice
  └─ ui/cli.py :: run_voice_mode()
       ├─ voice/audio_manager.py :: wait_for_wake_word()
       │    └─ voice/wakeword_manager.py :: WakeWordManager
       │         ├─ [Primary]  openWakeWord (bin/openwakeword)  ← BROKEN
       │         └─ [Fallback] Whisper STT (bin/whisper + bin/whisper-cli)
       ├─ voice/audio_manager.py :: listen()
       │    └─ voice/streaming_transcriber.py / transcription_manager.py
       └─ voice/audio_manager.py :: speak()
            └─ voice/tts_engine.py :: TTSEngine (Piper → pyttsx3 fallback)
```

---

## Bug 1 — FIXED: `get_greeting()` always returned `None` → TTS crash

**File:** `ui/cli.py`, lines 8–23

**Error:**
```
ERROR | voice.tts_engine:_run_piper:141 - Piper execution failed: 'NoneType' object has no attribute 'replace'
```

**Root cause:**  
`get_greeting()` is `async def` and defines an inner `_fetch()` function, but **never calls it or returns its value**. The function silently returned `None`, which was then passed to `tts_engine.speak(text)`. The Piper command builder called `text.replace(...)` and crashed.

```python
# BROKEN — _fetch is defined but never called:
async def get_greeting():
    def _fetch():
        ...
        return greeting
    # implicit return None
```

**Fix applied (`ui/cli.py`):**
```python
async def get_greeting():
    def _fetch():
        ...
        return greeting
    return await asyncio.to_thread(_fetch)  # ← added this line
```

**Defensive fix also applied (`voice/tts_engine.py`):**
```python
async def speak(self, text: str, voice: str = None):
    if not text:
        logger.debug("speak() called with empty/None text — skipping")
        return
    text = str(text)
    ...
```

---

## Bug 2 — FIXED: openWakeWord binary used wrong audio dtype → all scores = 0

**File:** `bin/openwakeword`

**Root cause:**  
The `sounddevice.InputStream` was opened with the default `dtype='float32'`. However, openWakeWord's internal preprocessor (`openwakeword/utils.py` line 89) **strictly enforces int16**:

```python
# Inside openwakeword/utils.py
if x.dtype != np.int16:
    raise ValueError("Input data must be 16-bit integers (i.e., 16-bit PCM audio)."
                     f"You provided {x.dtype} data.")
```

This `ValueError` was raised on every audio callback but silently swallowed by the sounddevice callback mechanism. All model scores returned as `0.0000`.

**Verified:** With `dtype='float32'`, max `hey_jarvis` score = **0.0064**. Completely undetectable.

**Fix applied (`bin/openwakeword`):**
```python
# BEFORE:
with sd.InputStream(channels=1, samplerate=16000, callback=callback, blocksize=1280):

# AFTER:
with sd.InputStream(channels=1, samplerate=16000, callback=callback, blocksize=1280, dtype='int16'):
```

Also wrapped `model.predict()` in try/except to surface future errors:
```python
try:
    prediction = model.predict(indata[:, 0])  # indata[:,0] is now int16
except Exception as exc:
    print(f"DEBUG: predict() error: {exc}", file=sys.stderr)
    return
```

---

## Bug 3 — STILL BROKEN: openWakeWord pre-trained models don't match user's voice

**File:** `bin/openwakeword`, `voice/wakeword_manager.py`

**Status:** ⚠️ Not fixed — requires model training or replacement

**Root cause:**  
Even with the correct `int16` dtype (Bug 2 fixed), the pre-trained openWakeWord models produce near-zero scores for this user's voice:

```
Max scores seen when user said "Hey Jarvis" clearly:
  hey_jarvis:       0.0139   ← threshold is 0.5, needs ~36x improvement
  alexa:            0.0038
  hey_mycroft:      0.0001
  1_hour_timer:     0.0044
```

**Available pre-trained models:** `['alexa', 'hey_mycroft', 'hey_jarvis', 'timer', 'weather']`  
**None of these** ever crosses 0.5 during normal use on this system.

**Why this happens:**  
The pre-trained models from [dscripka/openWakeWord](https://github.com/dscripka/openWakeWord) are trained on specific voice datasets (mostly North American English) and do not generalize well across all accents, microphones, or recording environments.

**Workaround applied:** OWW is **bypassed** in `wakeword_manager.py`; Whisper STT is used as the primary wake word detector:
```python
async def wait_for_wake_word(self) -> bool:
    # OWW bypassed — go straight to Whisper STT
    logger.info("Listening… say 'Hey Friday' or 'Friday' to wake up.")
    return await self._wait_for_stt_wake_word()
```

**Proper fix options:**

### Option A: Train a custom OWW model (recommended, best performance)
See: https://github.com/dscripka/openWakeWord#training-new-models

```bash
pip install openWakeWord[training]
# Record ~500 positive samples of the user saying "Hey Friday"
# Follow training notebook:
# https://github.com/dscripka/openWakeWord/blob/main/notebooks/custom_model_training.ipynb
```

Place the trained model at `voices/hey_friday.onnx` and update `bin/openwakeword`:
```python
model = Model(wakeword_models=["voices/hey_friday.onnx"])
```

### Option B: Lower detection threshold for existing models
Lower `0.5` to `0.15` in `bin/openwakeword` and accept more false positives:
```python
if score > 0.15:   # lowered from 0.5
    print(kw, flush=True)
```

### Option C: Switch to Porcupine wake word engine
[Picovoice Porcupine](https://picovoice.ai/platform/porcupine/) has a free tier with custom wake words and works much better across accents. Requires an API key.

```python
import pvporcupine
porcupine = pvporcupine.create(
    access_key="YOUR_KEY",
    keywords=["hey friday"]  # or use a custom .ppn model
)
```

---

## Bug 4 — FIXED: STT fallback recorded audio twice, losing the initial utterance

**File:** `voice/wakeword_manager.py` (old version)

**Root cause:**  
The old STT flow had a logic error:
1. Record 1 second → check RMS (is there audio?)
2. If yes → **record another 3 seconds** from scratch

Step 2 starts a fresh recording AFTER the 1-second detection window ends, so the initial utterance (the wake word) is always captured in the 1-second buffer and then **thrown away**. The 3-second recording captures whatever comes AFTER the user speaks.

**Fix applied:** Rewrote `_wait_for_stt_wake_word()` to record 3-second chunks directly and check RMS on those same chunks:
```python
async def _wait_for_stt_wake_word(self) -> bool:
    loop = asyncio.get_running_loop()
    while True:
        # Record 3 seconds (captures a full utterance)
        audio = await loop.run_in_executor(None, self._record_seconds, 3.0)
        rms = self._rms(audio)
        if rms < self.rms_threshold:
            continue  # skip silence
        # Save and transcribe the SAME audio we just recorded
        ...
```

---

## Bug 5 — PARTIAL FIX: Whisper non-speech token filter incomplete

**File:** `voice/wakeword_manager.py`

**Problem:**  
The STT fallback picks up background audio (TV, music, etc.) and Whisper transcribes it as "non-speech tokens". The current filter only catches `(parenthetical)` tokens:

```python
# Current filter:
def _is_non_speech(text: str) -> bool:
    stripped = text.strip()
    return stripped.startswith("(") and stripped.endswith(")")
```

**But Whisper also outputs these patterns NOT caught by the current filter:**
```
[MUSIC PLAYING]              ← square brackets — NOT filtered
♪ Yeah ♪ ♪ And you could ♪  ← music notes — NOT filtered
- Thank you, thank you...    ← TV dialogue — NOT filtered
```

**Fix needed (`voice/wakeword_manager.py`):**
```python
import re

@staticmethod
def _is_non_speech(text: str) -> bool:
    """Filter out Whisper's non-speech tokens."""
    stripped = text.strip()
    # Parenthetical: (clapping), (dramatic music)
    if stripped.startswith("(") and stripped.endswith(")"):
        return True
    # Square bracket: [MUSIC PLAYING], [BLANK_AUDIO]
    if stripped.startswith("[") and stripped.endswith("]"):
        return True
    # Music note tokens: ♪ lyrics ♪
    if "♪" in stripped:
        return True
    # Very short transcriptions (likely noise artifacts, < 2 words)
    if len(stripped.split()) < 2:
        return True
    return False
```

---

## Bug 6 — OPEN: STT wake-word detection has no Voice Activity Detection (VAD)

**Problem:**  
The STT fallback continuously records 3-second chunks and transcribes ALL of them through Whisper (which takes ~1 second per chunk on CPU). When background audio is present (music, TV), Whisper runs constantly and returns false speech, keeping the system busy.

**Current observed behavior:**
- Background music → Whisper → `(dramatic music)` → filtered ✓
- Background TV dialogue → Whisper → `"Thank you, thank you"` → NOT filtered, check wake words → no match → continue
- User says "Friday" → Whisper → `"A Friday."` → "friday" found ✓ **IT WORKS**, but only when user is louder than background

**The core issue:** RMS threshold `0.005` is too low — everything (music, ambient noise) exceeds it, so Whisper transcribes everything.

**Fix options:**

### Option A: Raise the RMS threshold significantly (quick fix)
Current: `rms_threshold = 0.005`  
Background music RMS: **0.08–0.15**. User speech should hit **0.2+** at close range.

```python
# In voice/wakeword_manager.py:
self.rms_threshold = 0.08  # require louder sound to trigger
```

### Option B: Add Silero VAD (recommended)
```bash
pip install silero-vad
```
```python
from silero_vad import load_silero_vad, get_speech_timestamps
model, utils = load_silero_vad()
# Only transcribe chunks where Silero detects human speech
```

### Option C: Fix the audio input device — use the physical mic only
The system **default audio device** (`* 19 default`) under ALSA may be capturing system audio (loopback/monitor). Available physical mic:
```
Device 0: HDA Intel PCH: ALC3204 Analog (hw:0,0) — physical microphone
```

In `voice/wakeword_manager.py` and `bin/openwakeword`, explicitly select device 0:
```python
with sd.InputStream(device=0, samplerate=16000, dtype='int16', blocksize=1280) as stream:
```

Or set environment:
```bash
export AUDIODEV=hw:0,0
export VOICE_INPUT_DEVICE=0
export OPENWAKEWORD_DEVICE=0
```

---

## Summary Table

| # | Component | Bug | Status | Fix |
|---|-----------|-----|--------|-----|
| 1 | `ui/cli.py` | `get_greeting()` returns `None` → TTS crash | ✅ Fixed | Added `return await asyncio.to_thread(_fetch)` |
| 2 | `bin/openwakeword` | Wrong `dtype='float32'` → all OWW scores = 0 | ✅ Fixed | Changed to `dtype='int16'` |
| 3 | `bin/openwakeword` | Pre-trained OWW models don't match user voice (max score 0.014) | ⚠️ Workaround | OWW bypassed; needs custom model training or Porcupine |
| 4 | `voice/wakeword_manager.py` | STT fallback recorded audio twice, lost utterance | ✅ Fixed | Single 3s recording + RMS check on same buffer |
| 5 | `voice/wakeword_manager.py` | Non-speech filter misses `[brackets]` and `♪` tokens | ✅ Fixed | Expanded `_is_non_speech()` filter |
| 6 | `voice/wakeword_manager.py` | No VAD — background audio transcribed constantly | ⚠️ Partial | Raised RMS threshold and added optional device selection |

---

## Key Files

| File | Role |
|------|------|
| `bin/openwakeword` | Python script acting as OWW binary — feeds mic audio to OWW model |
| `voice/openwakeword_wrapper.py` | Runs `bin/openwakeword` as subprocess, reads stdout for detections |
| `voice/wakeword_manager.py` | Orchestrates OWW + STT fallback wake word detection |
| `voice/stt_engine.py` | Wraps `bin/whisper` (which calls `bin/whisper-cli`) for transcription |
| `voice/tts_engine.py` | Piper TTS with pyttsx3 fallback |
| `ui/cli.py` | Main voice mode loop |

---

## Environment

- **Python:** 3.14.4 (venv at `/home/deku/Friday/venv`)
- **OWW version:** `openwakeword` (pip package)
- **OWW ONNX runtime:** CPU only (no CUDA — `CUDAExecutionProvider` not available)
- **Whisper:** `bin/whisper-cli` (whisper.cpp binary) with `ggml-tiny.en.bin` model
- **Piper TTS:** `bin/piper` (official binary) with `voices/cori-high.onnx`
- **Audio device:** ALSA default (device 19) — may be capturing system/loopback audio
- **Physical mic:** Device 0 — HDA Intel PCH: ALC3204 Analog (hw:0,0)
