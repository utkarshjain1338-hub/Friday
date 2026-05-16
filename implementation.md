# Friday Assistant — Phase 3 Real System Implementation Plan

## Objective

Convert the current prototype assistant into a REAL offline-capable Linux AI assistant with:

* real voice pipeline
* real local AI
* async architecture
* scalable plugin system
* stable automation engine

The assistant must remain:

* lightweight
* modular
* CPU-friendly
* Linux-first
* safe

Target platform:

* Arch Linux
* Python 3.12
* No dedicated GPU

---

# Current State Summary

Already implemented:

* CLI assistant
* command router
* Linux automation
* SQLite memory
* browser automation
* app launcher
* system monitor
* placeholder voice modules
* placeholder Ollama integration

Current limitations:

* fake wake word
* typed STT fallback
* weak TTS
* hardcoded skill logic
* synchronous execution
* no plugin loader
* no real streaming voice pipeline

---

# Main Goal of This Phase

Transform the assistant from:
Prototype simulation

into:
Real continuously running Linux assistant

---

# REQUIRED ARCHITECTURE CHANGES

## 1. Convert System To Async Architecture

The entire assistant must migrate toward asyncio-based execution.

Reason:
The assistant will run:

* wake word listener
* microphone stream
* STT transcription
* AI inference
* TTS playback
* notifications
* background tasks

simultaneously.

---

## Required Refactors

### Convert:

* assistant.py
* router.py
* voice pipeline
* automation handlers

to async-compatible code.

Use:

```python
asyncio
async def
await
async queues
background tasks
```

---

# 2. Real Wake Word Detection

## Replace:

typed wake-word simulation

## With:

openWakeWord integration

Repository:
https://github.com/dscripka/openWakeWord

---

## Requirements

### Continuous Background Listener

The assistant should:

* continuously listen
* consume minimal CPU
* activate only after wake word

---

## Wake Words

Support:

* Friday
* Friday
* Computer

---

## Architecture

Create:

```text
voice/
 ├── wakeword_engine.py
 ├── wakeword_listener.py
 └── models/
```

---

## Behavior

Pipeline:

```text
Microphone
→ Wake word detection
→ Start STT pipeline
→ Process command
```

---

# 3. Real Speech-To-Text Pipeline

## Replace:

typed fallback transcription

## With:

whisper.cpp integration

Repository:
https://github.com/ggml-org/whisper.cpp

---

## Requirements

### CPU Optimized

Use:

* tiny.en
* base.en

models initially.

---

## Features

### Streaming Transcription

The assistant should:

* capture microphone audio
* process chunks
* transcribe continuously

---

## Architecture

Create:

```text
voice/
 ├── stt_engine.py
 ├── audio_stream.py
 ├── transcription_manager.py
```

---

## Requirements

### Audio Processing

Implement:

* silence detection
* noise threshold
* chunk buffering
* WAV temp handling

Use:

```python
sounddevice
numpy
wave
```

---

# 4. Real Human-Like Text-To-Speech

## Replace:

pyttsx3

## With:

Piper TTS

Repository:
https://github.com/rhasspy/piper

---

## Requirements

### Offline Voice

Use realistic English voice models.

### Fast Response

TTS generation should begin immediately after AI response.

### Interrupt Support

The assistant must:

* stop speaking if user interrupts
* cancel playback safely

---

## Architecture

Create:

```text
voice/
 ├── tts_engine.py
 ├── speech_queue.py
 ├── playback_controller.py
```

---

# 5. Real Ollama AI Integration

## Replace:

stubbed fallback AI responses

## With:

real local inference

Use:

* qwen2.5:3b
* phi3:mini

through Ollama.

Repository:
https://ollama.com

---

## Requirements

### Streaming Responses

Support streamed token generation.

### Context Injection

Inject:

* memory
* recent conversation
* current system state

into prompts.

---

## Architecture

Create:

```text
brain/
 ├── ollama_client.py
 ├── prompt_builder.py
 ├── response_streamer.py
 ├── context_manager.py
```

---

# 6. Dynamic Plugin / Skill System

## Replace:

hardcoded routing logic

## With:

dynamic plugin architecture

---

## Required Architecture

Create:

```text
skills/
 ├── base_skill.py
 ├── registry.py
 ├── loader.py
 └── plugins/
```

---

## Skill Format

Every skill must inherit:

```python
BaseSkill
```

Example:

```python
class SpotifySkill(BaseSkill):
    name = "spotify"

    commands = [
        "play music",
        "pause music"
    ]

    async def execute(self, query, context):
        pass
```

---

## Plugin Loader

The assistant should:

* auto-discover plugins
* register commands dynamically
* allow future extensions

---

# 7. Event Bus System

Implement internal event communication.

Reason:
Modules should not directly depend on each other.

---

## Required Architecture

Create:

```text
core/
 ├── event_bus.py
 ├── events.py
```

---

## Example Events

```text
wake_word_detected
transcription_completed
ai_response_generated
speech_started
speech_finished
```

---

# 8. Advanced Memory System

## Improve SQLite Memory

Add:

* timestamps
* categories
* searchable notes
* conversation history

---

## Architecture

Create:

```text
memory/
 ├── memory_manager.py
 ├── conversation_store.py
 ├── notes_store.py
 ├── retrieval.py
```

---

## Features

### User Notes

Examples:

```text
Remember this idea
Remember my project
```

### Conversation Recall

Examples:

```text
What did I say yesterday?
```

---

# 9. Improved Safety Layer

## Strengthen command security

The AI must NEVER:

* execute unrestricted shell commands
* run sudo automatically
* delete without confirmation

---

## Required Architecture

Create:

```text
security/
 ├── validator.py
 ├── permission_manager.py
 ├── command_whitelist.py
 ├── risk_levels.py
```

---

## Permission Levels

### Safe

* open apps
* read files

### Medium

* kill process
* modify files

### Dangerous

* delete directories
* shutdown
* package removal

Dangerous actions require confirmation.

---

# 10. Background Assistant Service

Convert assistant into long-running daemon.

---

## Requirements

The assistant should:

* start automatically
* run in background
* maintain low CPU usage

---

## Linux Integration

Create:

```text
linux/
 ├── systemd/
 │   └── friday.service
```

---

# 11. Logging + Diagnostics

Implement advanced logging.

---

## Log:

* microphone state
* STT latency
* AI latency
* command execution
* failures
* CPU usage

Use:

```python
loguru
```

---

# 12. Terminal HUD Interface

DO NOT build heavy GUI yet.

Instead create:
lightweight terminal dashboard.

---

## Features

Display:

* listening state
* microphone level
* current task
* CPU usage
* memory usage
* active skill
* AI status

---

# 13. Initial Skills To Build

Priority skills:

* app launcher
* VS Code controller
* browser automation
* file manager
* terminal assistant
* system monitor
* media control

---

# 14. Required Coding Standards

All code must:

* be modular
* typed where possible
* async-compatible
* documented
* production-structured

---

# 15. Performance Goals

Target:

* idle CPU usage under 10%
* wake word response under 1 second
* TTS start under 2 seconds
* lightweight memory footprint

---

# FINAL TARGET BEHAVIOR

Example:

User:
"Friday start coding mode"

Assistant should:

* detect wake word
* transcribe speech
* understand intent
* open VS Code
* open project folder
* launch terminal
* open browser tabs
* respond naturally with voice

All fully offline where possible.

---

# IMPLEMENTATION ORDER

STRICT ORDER:

1. Async architecture
2. Real wake word
3. Real STT
4. Real TTS
5. Ollama integration
6. Event bus
7. Plugin system
8. Improved memory
9. Background daemon
10. HUD interface

DO NOT skip order.
