# Friday

Friday is an offline-first Linux assistant designed to behave like a personal OS-level assistant with a cute, stylish female voice personality.

## Phase 1 — Base Infrastructure

This initial version provides:
- CLI-based interaction
- Modular command routing
- Safe command execution
- Logging and configuration support

## Getting Started

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Structure

- `main.py` — Launches the assistant
- `core/` — Core assistant logic and routing
- `ui/` — Command-line interface
- `automation/` — Safe command execution and system control
- `security/` — Safety policies and validation
- `config/` — YAML configuration and command mapping

## Phase 2 — Linux Automation Layer

The current version supports:
- launching applications
- monitoring CPU, memory, battery, and network usage
- searching, creating, moving, and deleting files
- opening websites and searching online safely
- voice recording fallback with `listen`
- offline text-to-speech via `pyttsx3` if available
- optional voice mode with wake word simulation

## Installation

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running Friday

- CLI mode:
  ```bash
  python main.py
  ```

- Voice mode:
  ```bash
  python main.py --voice
  ```

- In CLI mode, type `help` for more commands.

## Notes

- `listen` records audio and uses a transcription fallback when `whisper.cpp` is not available.
- `pyttsx3` provides offline speech output on systems with a TTS backend.
- `remember <note>` stores a long-term note.
- `show memory` recalls recent memory entries.
- If `ollama` is installed, Friday can optionally use it for richer local AI responses.

## Project Status

Friday is now a complete Phase 1/Phase 2 assistant with voice and local AI support stubs. Future improvements can add a real wake-word engine, `whisper.cpp` integration, and more advanced memory recall.
