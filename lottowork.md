# KNOWN_ISSUES_AND_FIXES.md

# Friday Assistant — Known Issues & Fixes

This document tracks major implementation issues encountered during development, their causes, and applied or recommended fixes.

---

# 1. Python Module Import Error

## Error

```text id="k9g1o7"
ModuleNotFoundError: No module named 'core'
```

---

## Cause

Python was executing files directly from subdirectories like:

```bash id="l1b2zr"
python examples/quickstart.py
```

This caused Python to treat:

```text id="sllfce"
examples/
```

as the root instead of the full project root.

---

## Fix

Run modules from project root using:

```bash id="j3pk0d"
python -m examples.quickstart
```

---

## Additional Recommendation

Ensure every package directory contains:

```text id="2bmx8m"
__init__.py
```

Example:

```text id="1w6e0d"
core/__init__.py
```

---

# 2. SQLite Threading Error

## Error

```text id="2k6ly0"
sqlite3.ProgrammingError:
SQLite objects created in a thread can only be used in that same thread
```

---

## Cause

SQLite connection was created in the main thread but later accessed using:

```python id="eppg5u"
asyncio.to_thread()
```

which executes database operations in worker threads.

SQLite connections are thread-bound by default.

---

## Immediate Fix

Create SQLite connection with:

```python id="v5g9b0"
sqlite3.connect(
    db_path,
    check_same_thread=False
)
```

---

## Additional Fix

Add thread locking:

```python id="zhg65u"
import threading

self.lock = threading.Lock()

with self.lock:
    cursor = self.connection.cursor()
```

---

## Long-Term Recommendation

Migrate fully to:

```text id="mqpb4l"
aiosqlite
```

for proper async-native database handling.

---

# 3. Fake Speech-To-Text Pipeline

## Issue

The assistant displayed:

```text id="tk5j57"
Transcription fallback - type your transcription:
```

instead of real microphone transcription.

---

## Cause

Real STT engine (`whisper.cpp`) was not integrated yet.

Fallback typed-input mode was being used.

---

## Required Fix

Integrate:

* whisper.cpp
* streaming audio pipeline
* microphone capture
* silence detection

---

## Planned Components

```text id="9ptv0x"
voice/
 ├── stt_engine.py
 ├── streaming_transcriber.py
 ├── audio_buffer.py
```

---

# 4. Placeholder Wakeword System

## Issue

Wakeword system currently relies on typed simulation.

---

## Cause

No real wakeword engine integrated.

---

## Planned Fix

Integrate:

* openWakeWord

---

## Planned Features

* continuous listening
* low CPU detection
* automatic STT activation

---

# 5. Weak Text-To-Speech System

## Issue

Current TTS uses:

```text id="i5y4pi"
pyttsx3
```

which:

* sounds robotic
* lacks interruption handling
* has inconsistent Linux backends

---

## Planned Fix

Replace with:

* Piper TTS

---

## Required Features

* human-like speech
* interruptible playback
* async speech queue
* low latency

---

# 6. AI Stub Responses

## Issue

Fallback AI responses used when Ollama unavailable.

---

## Cause

Ollama integration scaffold existed but real inference pipeline incomplete.

---

## Planned Fix

Implement:

* streaming inference
* token streaming
* context injection
* model management

---

## Target Models

```text id="7ln1e6"
qwen2.5:3b
phi3:mini
```

---

# 7. Audio Synchronization Risks

## Issue

Potential future issues:

* overlapping TTS
* microphone conflicts
* wakeword feedback loops
* multiple audio owners

---

## Cause

Audio ownership coordination still incomplete.

---

## Planned Fix

Implement centralized:

```text id="v52zvn"
audio_manager.py
```

with:

* ownership locks
* playback control
* microphone control

---

# 8. State Synchronization Risks

## Issue

Potential future async conflicts between:

* listening
* speaking
* processing
* interruptions

---

## Cause

Concurrent async systems require centralized state management.

---

## Planned Fix

Implement:

```text id="h89p0l"
assistant_state.py
```

with synchronized shared runtime state.

---

# 9. Lack of Real-Time Streaming

## Issue

Current interaction still partially request-response based.

---

## Cause

Streaming pipeline not fully connected between:

* STT
* LLM
* TTS

---

## Planned Fix

Implement:

* token streaming
* incremental TTS
* real-time assistant loop

---

# 10. Missing Continuous Runtime Loop

## Issue

Assistant not yet fully autonomous in background runtime.

---

## Planned Fix

Implement:

* background daemon
* systemd service
* persistent runtime loop
* continuous event processing

---

# 11. Performance Constraints

## Issue

System runs on:

* 8GB RAM
* CPU-only hardware

Heavy models may cause:

* latency spikes
* swapping
* freezes

---

## Optimization Strategy

Preferred models:

```text id="pm7ixf"
qwen2.5:3b
gemma3:1b
```

Avoid:

```text id="r32g0u"
Mixtral
Large 70B models
```

---

# 12. Current Working Components

## Successfully Working

* async architecture
* CLI assistant
* router
* event bus
* plugin scaffold
* memory persistence
* Linux automation
* HUD system
* permission manager
* logging
* Ollama scaffolding

---

# Current Major Milestone

## Infrastructure Phase Complete

The project has transitioned from:
prototype scripts

to:
modular event-driven assistant architecture.

---

# Current Primary Goal

Complete the fully conversational runtime loop:

```text id="hjlwm6"
Wakeword
→ Listen
→ Transcribe
→ Think
→ Speak
→ Return To Listening
```

with:

* low latency
* stability
* interruptibility
* continuous runtime behavior
