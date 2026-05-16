# NEXT_IMPLEMENTATION_TARGETS.md

# Friday Assistant — Next Implementation Targets

## Objective

This document defines the NEXT critical systems required to transform Friday from a partially functional prototype into a real-time conversational Linux assistant.

Current infrastructure is mostly complete.

Focus now shifts toward:

* real-time interaction
* low-latency audio
* conversational reliability
* state synchronization
* production stability

---

# CURRENT PROJECT STATUS

## Already Implemented

* async architecture
* event bus
* plugin system scaffold
* Ollama streaming scaffold
* prompt builder
* SQLite memory
* Linux automation
* command router
* permission manager
* wakeword scaffolding
* CI workflow

---

# PRIMARY OBJECTIVE

Build a fully working conversational loop:

```text id="2h3b3n"
Wake Word
→ Listen
→ Transcribe
→ Think
→ Speak
→ Return To Listening
```

This loop must run continuously and reliably.

---

# PRIORITY IMPLEMENTATION ORDER

STRICT ORDER:

1. Streaming STT pipeline
2. Interruptible TTS pipeline
3. Real wakeword engine
4. Centralized assistant state manager
5. Audio ownership system
6. Streaming AI response pipeline
7. Skill execution improvements
8. Logging and diagnostics
9. Background daemon stability
10. HUD interface

DO NOT skip order.

---

# 1. STREAMING STT PIPELINE

## Goal

Replace placeholder transcription flow with real low-latency speech recognition.

---

## Required Technology

Use:

* whisper.cpp

Repository:
https://github.com/ggml-org/whisper.cpp

---

## Required Features

### Real-Time Streaming

The assistant must:

* continuously capture microphone input
* process audio chunks
* transcribe incrementally
* minimize latency

---

## Requirements

### Audio Chunking

Implement:

* rolling buffers
* silence detection
* chunk segmentation
* temporary WAV handling

---

## Required Files

```text id="8c5lqj"
voice/
 ├── stt_engine.py
 ├── streaming_transcriber.py
 ├── audio_buffer.py
 ├── silence_detector.py
```

---

## Performance Targets

Target:

* transcription delay under 2 seconds
* low CPU usage
* stable continuous listening

---

# 2. INTERRUPTIBLE TTS PIPELINE

## Goal

Replace pyttsx3 with realistic human-like offline speech.

---

## Required Technology

Use:

* Piper TTS

Repository:
https://github.com/rhasspy/piper

---

## Required Features

### Interruptibility

The assistant must:

* stop speaking immediately if interrupted
* cancel playback safely
* resume listening instantly

---

## Speech Queue

Implement:

* queued speech requests
* cancellation tokens
* playback state tracking

---

## Required Files

```text id="55n5yn"
voice/
 ├── tts_engine.py
 ├── speech_queue.py
 ├── playback_manager.py
 ├── interrupt_handler.py
```

---

## Performance Targets

Target:

* speech startup under 2 seconds
* smooth playback
* no overlapping audio

---

# 3. REAL WAKEWORD ENGINE

## Goal

Replace typed wakeword simulation.

---

## Required Technology

Use:

* openWakeWord

Repository:
https://github.com/dscripka/openWakeWord

---

## Required Features

### Continuous Background Detection

The assistant should:

* continuously monitor microphone
* remain low CPU
* activate STT only after wake word

---

## Wake Words

Support:

* Friday
* Friday
* Computer

---

## Required Files

```text id="26sz8m"
voice/
 ├── wakeword_engine.py
 ├── wakeword_listener.py
 ├── wakeword_models/
```

---

# 4. CENTRALIZED ASSISTANT STATE MANAGER

## Goal

Prevent synchronization issues between:

* microphone
* TTS
* AI generation
* wakeword
* skills

---

## Required Architecture

Create:

```text id="wd08bh"
core/
 ├── assistant_state.py
```

---

## Required State Variables

```python id="c4a49m"
listening
speaking
processing
interrupted
wakeword_active
microphone_busy
current_skill
current_task
```

---

## Requirements

All modules must:

* read centralized state
* update state safely
* avoid conflicting operations

---

# 5. AUDIO OWNERSHIP SYSTEM

## Goal

Prevent microphone and speaker conflicts.

---

## Requirements

Only ONE system should control:

* microphone input
* speaker output
* playback
* audio streams

at a time.

---

## Required Files

```text id="qrrjba"
voice/
 ├── audio_manager.py
 ├── device_controller.py
```

---

## Required Features

### Ownership Locking

Implement:

* playback locks
* microphone locks
* stream lifecycle management

---

# 6. STREAMING AI RESPONSE PIPELINE

## Goal

Improve Ollama integration into real-time streaming conversation.

---

## Requirements

### Stream Tokens Live

The assistant should:

* begin speaking before full response completes
* stream responses incrementally

---

## Required Features

### Context Injection

Inject:

* memory
* recent messages
* assistant state
* active tasks

into prompts.

---

## Required Files

```text id="n4fkwm"
brain/
 ├── response_streamer.py
 ├── context_manager.py
 ├── token_pipeline.py
```

---

# 7. SKILL EXECUTION IMPROVEMENTS

## Goal

Improve plugin execution reliability.

---

## Required Features

### Dynamic Skill Discovery

The assistant should:

* auto-load plugins
* register commands dynamically
* support async execution

---

## Required Features

### Skill Isolation

One failed skill should NOT:

* crash assistant
* stop event loop

---

## Required Files

```text id="2j4j8h"
skills/
 ├── skill_executor.py
 ├── plugin_loader.py
 ├── sandbox.py
```

---

# 8. LOGGING + DIAGNOSTICS

## Goal

Enable debugging and performance optimization.

---

## Required Technology

Use:

* loguru

---

## Log:

* wakeword detection
* microphone state
* transcription latency
* AI latency
* TTS latency
* command execution
* exceptions
* CPU usage

---

## Required Files

```text id="3x1jwx"
logs/
diagnostics/
```

---

# 9. BACKGROUND DAEMON STABILITY

## Goal

Run assistant continuously as Linux background service.

---

## Requirements

The assistant should:

* auto-start
* restart on crash
* remain lightweight
* survive long uptime

---

## Linux Integration

```text id="qykm5m"
linux/
 ├── systemd/
 │   └── friday.service
```

---

# 10. TERMINAL HUD INTERFACE

## Goal

Create lightweight visual feedback system.

DO NOT implement heavy GUI yet.

---

## Features

Display:

* assistant state
* microphone status
* AI status
* active skill
* CPU usage
* memory usage
* logs
* currently speaking text

---

## Suggested Technologies

Use:

* rich
* textual

---

## Required Files

```text id="i0iyyb"
ui/
 ├── hud.py
 ├── dashboard.py
```

---

# CRITICAL ENGINEERING RULES

## NEVER:

* block event loop
* execute unrestricted shell commands
* allow concurrent microphone ownership
* allow overlapping TTS playback
* hardcode plugin loading
* tightly couple modules

---

# REQUIRED DESIGN PRINCIPLES

The system must remain:

* modular
* async-first
* event-driven
* CPU-efficient
* fault-tolerant
* Linux-native

---

# CURRENT PRIMARY MILESTONE

## Fully Conversational Real-Time Assistant

The assistant should reliably:

1. detect wakeword
2. listen
3. transcribe
4. process
5. respond naturally
6. speak
7. return to listening

continuously without crashing.

This is the most important milestone.
