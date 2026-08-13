# Project Architecture Overview

This document summarizes the high-level architecture, main modules, and responsibilities for the Friday assistant repository.

## High-level summary
- Purpose: Offline-first Linux assistant with real-time voice pipeline and plugin skill system.
- Execution: Async-first Python, optional native binaries (whisper.cpp, piper, openWakeWord, ollama).

## Primary components

- `main.py`: application entrypoint and CLI/voice mode switch.
- `brain/`: LLM integration, token streaming, context management, and token pipeline.
- `voice/` and `voices/`: audio I/O, STT integration, wake-word and TTS playback (device control, buffers, queues).
- `skills/`: plugin discovery, skill execution sandbox, skill registry and implementations.
- `shared/` and `python-core/`: shared utilities, core orchestration, automation and semantic helpers.
- `security/`: permission manager, validation, safe command execution.
- `system_state/`: activity tracking and runtime state monitoring.
- `config/`: YAML configs (`commands.yaml`, `prompts.yaml`, `settings.yaml`).
- `tests/`: unit and integration tests.
- `examples/`: runnable examples such as `examples/quickstart.py`.
- `rust-core/`: optional performance-sensitive components and native helpers.

## Directory responsibilities (short)

- `brain/` — orchestrates LLM responses and token streaming (`response_streamer.py`, `context_manager.py`, `token_pipeline.py`).
- `voice/` — audio capture, silence detection, streaming transcription and playback helpers.
- `skills/` — plugin loader, sandboxed executor, built-in skills (system, spotify, vscode, etc.).
- `shared/` — cross-cutting configs, event definitions, utilities used by multiple modules.
- `security/` — central place for permission checks and safe command wrappers.
- `system_state/` — stores runtime flags (listening/speaking) and activity history.
- `tests/` — test suite covering intent classification, audio, LLM integration and plugins.

## Key files to inspect first

- `README.md` — project overview and quickstart.
- `ARCHITECTURE.md` — detailed architecture and diagrams (existing).
- `COMPLETE_IMPLEMENTATION.md` — integration notes and production checklist.
- `main.py` — program entry.
- `examples/quickstart.py` — end-to-end example demonstrating the loop.

## Conversation loop (short)

1. Wake/Listen: wake-word or CLI input triggers audio capture.
2. Transcribe: streaming STT produces text events.
3. Process: `brain/context_manager` + `skills/router` decide action.
4. Execute: `skills/skill_executor` runs skill (sandboxed, timeout).
5. Respond: LLM via `brain/response_streamer` → `token_pipeline` → `voice/playback`.
6. Cleanup: release devices, update `system_state`, emit diagnostics.

## Mermaid component diagram

```mermaid
graph TD
  User[User Input]
  Wake[Wake Word / CLI]
  Audio[Audio I/O]
  STT[Streaming STT]
  Brain[Brain (LLM + Token Pipeline)]
  Skills[Skills / Plugin Executor]
  Security[Security / Sandbox]
  Playback[TTS / Playback Manager]
  State[System State / Diagnostics]
  UI[UI / HUD / CLI]
  Storage[Config + Memory + Shared]

  User --> Wake --> Audio --> STT --> Brain
  Brain --> Skills
  Skills --> Security --> Brain
  Brain --> Playback --> Audio
  Brain --> State
  UI --> State
  Storage --> Brain
  Skills --> Storage

  style Brain fill:#f9f,stroke:#333,stroke-width:1px
  style Skills fill:#bbf,stroke:#333,stroke-width:1px
  style Audio fill:#bfb,stroke:#333,stroke-width:1px
```

## Quick mapping of notable folders/files

- `brain/` — `response_streamer.py`, `context_manager.py`, `token_pipeline.py`.
- `skills/` — `loader.py`, `skill_executor.py`, `sandbox.py`, `plugins/`.
- `voice/` — streaming transcriber, `tts_engine`, `device_controller` (see voice files in README).
- `shared/` — `configs/`, `events/` and shared helpers.
- `python-core/` — layered libraries for semantics, memory, orchestrator, workflows.
- `rust-core/` — native helpers; see `Cargo.toml`.
- `tests/` — unit tests: `test_intent_classifier.py`, `test_audio_manager.py`, `test_llm.py`, etc.

## Next recommended steps

1. Open `main.py` to see program startup and flag handling.
2. Run `examples/quickstart.py` to exercise the full loop (requires optional binaries).
3. Generate a more detailed class/sequence diagram for `brain/` and `voice/` if desired.

---

If you want, I can now: (a) generate per-module file lists, (b) create sequence diagrams for the conversation loop, or (c) run tests. Which next? 
