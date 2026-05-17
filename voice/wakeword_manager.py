import asyncio
import contextlib
import os
import tempfile
import wave
from pathlib import Path

import numpy as np
import sounddevice as sd
from loguru import logger

from voice.stt_engine import STTEngine
from core.bus import bus
from core.events import WAKE_WORD_DETECTED


class WakeWordManager:
    """Detect wake words using openWakeWord (native Python) with STT fallback.

    Strategy:
      1. Try native openWakeWord in-process. This avoids subprocess overhead and
         correctly feeds int16 audio to the model.
      2. If OWW is unavailable or scores stay too low, fall back to Whisper STT:
         continuously record audio and transcribe chunks, looking for the wake phrase.
    """

    # Wake words the user may say. OWW model names are also included so that
    # any OWW hit (alexa, hey_jarvis, hey_mycroft …) immediately wakes Friday.
    WAKE_WORDS = [
        "hey friday", "friday", "computer",
        "hey jarvis", "hey_jarvis",
        "hey mycroft", "hey_mycroft",
        "alexa",
    ]

    def __init__(self, wake_words=None, sample_rate: int = 16000):
        self.wake_words = [w.lower() for w in (wake_words or self.WAKE_WORDS)]
        self.sample_rate = sample_rate
        self.stt = STTEngine()
        self.chunk_size = 1280          # 80 ms — openWakeWord's native chunk
        self.rms_threshold = 0.10       # background noise peaks ~0.07; user speech ~0.15+
        self._oww_model = None
        # OWW doesn't have a native 'Hey Friday' model and triggers false positives.
        # Force fallback to the robust STT engine.
        self._oww_available = False  
        
        # On Arch+Hyprland, the ALSA default device routes through PipeWire which
        # can include system audio loopback. Prefer the physical HDA mic instead.
        self.mic_device, self.mic_native_rate = self._find_mic_device()
        logger.info(f"Microphone device: [{self.mic_device}] "
                    f"{sd.query_devices(self.mic_device)['name']} "
                    f"@ {self.mic_native_rate} Hz")

    # ------------------------------------------------------------------
    # Audio device selection
    # ------------------------------------------------------------------

    @staticmethod
    def _find_mic_device() -> tuple[int | None, int]:
        """Return (device_index, native_sample_rate) for the best microphone.

        Priority on Arch+Hyprland/PipeWire:
          1. 'pulse' (PipeWire-pulse) — correct choice on PipeWire systems.
             Handles concurrent access so Piper TTS and mic recording
             can run simultaneously. Supports arbitrary sample rates.
          2. 'pipewire' device — also PipeWire managed.
          3. Raw hw device (hw:0,0) — LAST RESORT only. PipeWire owns it
             exclusively, so opening it directly causes 'Device unavailable'.
          4. System default.
        """
        import sounddevice as sd
        devices = sd.query_devices()

        # Priority 1: PipeWire-pulse (best for Hyprland — concurrent access OK)
        for i, d in enumerate(devices):
            if d["max_input_channels"] >= 1 and d["name"].lower() == "pulse":
                native_sr = int(d["default_samplerate"])
                logger.debug(f"Selected PipeWire-pulse mic: [{i}] {d['name']} @ {native_sr} Hz")
                return i, native_sr

        # Priority 2: pipewire device
        for i, d in enumerate(devices):
            if d["max_input_channels"] >= 1 and d["name"].lower() == "pipewire":
                native_sr = int(d["default_samplerate"])
                logger.debug(f"Selected pipewire mic: [{i}] {d['name']} @ {native_sr} Hz")
                return i, native_sr

        # Priority 3: raw hardware (last resort — may fail if PipeWire owns it)
        hw_keywords = ["alc", "hw:0", "analog", "hda intel"]
        for i, d in enumerate(devices):
            if d["max_input_channels"] < 1:
                continue
            name = d["name"].lower()
            if any(kw in name for kw in hw_keywords):
                native_sr = int(d["default_samplerate"])
                logger.warning(f"Falling back to raw hardware mic (may conflict with PipeWire): "
                               f"[{i}] {d['name']} @ {native_sr} Hz")
                return i, native_sr

        # Priority 4: system default
        logger.debug("Using system default mic device")
        default_sr = int(sd.query_devices(sd.default.device[0])["default_samplerate"])
        return None, default_sr

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def wait_for_wake_word(self) -> bool:
        logger.info("Listening… say 'Hey Friday' or 'Friday' to wake up.")
        if self._oww_available:
            detected = await self._wait_for_oww_native(timeout=30.0)
            if detected:
                return True
            logger.info("openWakeWord did not detect a wake word; falling back to STT.")

        return await self._wait_for_stt_wake_word()

    # ------------------------------------------------------------------
    # openWakeWord — native in-process detection
    # ------------------------------------------------------------------

    def _try_load_oww(self) -> bool:
        try:
            from openwakeword.model import Model  # type: ignore
            self._oww_model = Model()
            names = list(self._oww_model.models.keys())
            logger.info(f"openWakeWord loaded. Models: {names}")
            return True
        except Exception as exc:
            logger.warning(f"openWakeWord not available: {exc}")
            return False

    async def _wait_for_oww_native(self, timeout: float = 60.0) -> bool:
        """Run OWW in a thread, streaming int16 audio from sounddevice."""
        loop = asyncio.get_running_loop()
        detected_event = asyncio.Event()
        phrase_holder: dict = {}

        def _run_oww():
            """Blocking loop that feeds audio chunks to the OWW model."""
            try:
                stream = sd.InputStream(
                    device=self.mic_device,
                    samplerate=self.sample_rate,
                    channels=1,
                    dtype="int16",
                    blocksize=self.chunk_size,
                )

                with stream as stream:
                    while not detected_event.is_set():
                        chunk, _overflowed = stream.read(self.chunk_size)
                        audio = chunk[:, 0]   # int16, shape (1280,)
                        try:
                            scores = self._oww_model.predict(audio)
                        except Exception as exc:
                            logger.debug(f"OWW predict error: {exc}")
                            continue

                        for kw, score in scores.items():
                            if score > 0.5:
                                logger.info(f"Wake word detected by OWW: "
                                            f"'{kw}' score={score:.3f}")
                                phrase_holder["phrase"] = kw
                                loop.call_soon_threadsafe(detected_event.set)
                                return
                            elif score > 0.05:
                                logger.debug(f"OWW near-miss: {kw}={score:.3f}")
            except Exception as exc:
                logger.warning(f"OWW streaming error: {exc}")

        fut = loop.run_in_executor(None, _run_oww)
        try:
            await asyncio.wait_for(detected_event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            detected_event.set()   # Signal the thread to stop
            with contextlib.suppress(Exception):
                await fut
            return False

        detected_event.set()   # Ensure thread exits
        with contextlib.suppress(Exception):
            await fut

        phrase = phrase_holder.get("phrase", "")
        if phrase:
            try:
                await bus.emit(WAKE_WORD_DETECTED,
                               {"phrase": phrase, "source": "openWakeWord"})
            except Exception:
                pass
            return True
        return False

    # ------------------------------------------------------------------
    # STT fallback — continuously record then transcribe
    # ------------------------------------------------------------------

    @staticmethod
    def _is_non_speech(text: str) -> bool:
        """Return True for Whisper non-speech / ambient-audio tokens.

        Whisper produces several patterns for non-speech audio, sometimes with
        a leading prefix like '>>' or '-':
          (clapping)           ← parenthetical
          [MUSIC PLAYING]      ← square bracket
          >> [INAUDIBLE]       ← prefixed bracket (the '>>' defeats naive check)
          - [music]            ← dash-prefixed bracket
          ♪ Yeah ♪             ← music notes
        """
        stripped = text.strip()
        # Strip common leading prefixes Whisper adds: '>>', '-', '*', numbers
        import re
        core = re.sub(r'^[>\-\*\d\.\s]+', '', stripped).strip()

        if core.startswith("(") and core.endswith(")"):
            return True
        if core.startswith("[") and core.endswith("]"):
            return True
        if "♪" in stripped:
            return True
        # Also filter '[inaudible]' anywhere in short transcriptions
        if re.search(r'\[\s*inaudible\s*\]', stripped, re.IGNORECASE):
            return True
        if len(stripped.split()) < 2:
            return True
        return False

    async def _wait_for_stt_wake_word(self) -> bool:
        """Record audio in a rolling fashion and transcribe each voiced chunk."""
        loop = asyncio.get_running_loop()

        while True:
            # Record a 3-second chunk (captures a full utterance)
            audio = await loop.run_in_executor(
                None, self._record_seconds, 3.0
            )
            rms = self._rms(audio)
            logger.debug(f"STT chunk RMS={rms:.4f} (threshold={self.rms_threshold})")

            if rms < self.rms_threshold:
                # Pure silence — skip transcription
                continue

            # Save to wav and transcribe
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = Path(tmp.name)

            await loop.run_in_executor(
                None, self._save_wav, audio, str(tmp_path)
            )
            transcription = await self.stt.transcribe_file(str(tmp_path))
            try:
                tmp_path.unlink()
            except Exception:
                pass

            if not transcription:
                continue

            # Filter out Whisper's non-speech parenthetical tokens
            if self._is_non_speech(transcription):
                logger.debug(f"STT: ignoring non-speech '{transcription}'")
                continue

            text = transcription.lower()
            logger.debug(f"STT transcribed: '{text}'")

            for w in self.wake_words:
                if w in text:
                    logger.info(f"Wake word '{w}' detected via STT: '{text}'")
                    try:
                        await bus.emit(
                            WAKE_WORD_DETECTED,
                            {"phrase": w, "transcription": transcription},
                        )
                    except Exception:
                        pass
                    return True

    # ------------------------------------------------------------------
    # Audio helpers
    # ------------------------------------------------------------------

    def _record_seconds(self, duration: float) -> np.ndarray:
        """Record `duration` seconds of audio, returned as 16 kHz int16 mono.

        Uses PipeWire-pulse which supports any requested sample rate via its
        built-in resampler. Falls back to native-rate recording + scipy
        resampling if the device doesn't accept 16000 Hz directly.
        Retries on transient 'Device unavailable' errors (e.g. right after TTS).
        """
        import math, time
        from scipy.signal import resample_poly  # type: ignore

        last_exc = None
        for attempt in range(5):   # retry up to 5x on device-busy errors
            try:
                # Try recording at the target 16000 Hz directly.
                # PipeWire-pulse handles resampling internally.
                try:
                    frames = sd.rec(
                        int(duration * self.sample_rate),
                        samplerate=self.sample_rate,
                        channels=1,
                        dtype="int16",
                        device=self.mic_device,
                    )
                    sd.wait()
                    return frames[:, 0]
                except Exception as e:
                    if "sample rate" in str(e).lower() or "9997" in str(e):
                        # Device doesn't accept 16000 Hz — record at native rate
                        # and resample ourselves
                        raise
                    raise
            except Exception as exc:
                err_str = str(exc)
                if "9985" in err_str or "unavailable" in err_str.lower():
                    # Device temporarily busy (e.g. TTS just released it)
                    wait_s = 0.5 * (attempt + 1)
                    logger.debug(f"Mic device busy, retrying in {wait_s:.1f}s "
                                 f"(attempt {attempt + 1}/5)")
                    time.sleep(wait_s)
                    last_exc = exc
                    continue
                elif "sample rate" in err_str.lower() or "9997" in err_str:
                    # Device doesn't support 16000 Hz — record at native rate
                    native_sr = self.mic_native_rate
                    logger.debug(f"16000 Hz not supported, recording at {native_sr} Hz then resampling")
                    frames = sd.rec(
                        int(duration * native_sr),
                        samplerate=native_sr,
                        channels=1,
                        dtype="int16",
                        device=self.mic_device,
                    )
                    sd.wait()
                    audio = frames[:, 0]
                    gcd = math.gcd(self.sample_rate, native_sr)
                    resampled = resample_poly(
                        audio.astype(np.float32),
                        self.sample_rate // gcd,
                        native_sr // gcd,
                    )
                    return np.clip(resampled, -32768, 32767).astype(np.int16)
                else:
                    raise

        raise last_exc or RuntimeError("Failed to open microphone after retries")

    def _save_wav(self, audio: np.ndarray, path: str) -> None:
        with wave.open(path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio.tobytes())

    def _rms(self, frames: np.ndarray) -> float:
        if frames is None or frames.size == 0:
            return 0.0
        data = np.asarray(frames, dtype=np.int16).astype(np.float32) / 32768.0
        return float(np.sqrt(np.mean(data * data)))
