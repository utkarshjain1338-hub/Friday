# Friday Assistant — Project Summary

## Overview
Friday is an offline-first Linux assistant built in Python, modeled after the Jarvis architecture blueprint. The project is designed to run on CPU-only Linux systems and provides a modular assistant experience with CLI and voice-enabled workflows.

## Current Implementation Status

### Phase 1 — Base Infrastructure
- CLI-based assistant launched from `main.py`
- `ui/cli.py` provides typed command interaction
- `core/assistant.py` and `core/router.py` route commands and manage assistant state
- Safe command execution layer in `automation/command_executor.py`
- Configuration driven command mapping in `config/commands.yaml`
- Basic memory persistence using SQLite in `memory/database.py`
- Logging support via `loguru`

### Phase 2 — Linux Automation
- `automation/linux_controller.py` supports opening applications, killing processes, and listing processes
- `automation/system_monitor.py` provides CPU, memory, battery, temperature, and network reporting
- `automation/browser_controller.py` supports opening websites, Google search, and YouTube search
- `automation/file_manager.py` supports searching, creating, moving, and deleting files/folders
- Router updated to handle natural command phrases for automation tasks

### Voice and AI Support
- Voice subsystem scaffolding in `voice/`
- `voice/tts.py` uses `pyttsx3` for offline speech output when available
- `voice/microphone.py` records audio using `sounddevice`
- `voice/stt.py` supports `whisper.cpp` if installed, with a typed fallback transcription mode
- `voice/wakeword.py` provides a simple typed wake-word flow
- `voice/audio_manager.py` integrates microphone, STT, wake-word, and TTS
- `brain/llm.py` supports optional `ollama` integration and provides fallback AI responses

### Memory and Personalization
- `core/state_manager.py` tracks recent conversation history
- `memory/database.py` stores interaction logs and user notes in SQLite
- Assistant supports `remember <note>` and `show memory`

## Important Files and Structure
- `main.py` — app entry point, with optional `--voice` mode
- `ui/cli.py` — CLI and voice flow commands
- `core/assistant.py` — assistant orchestration and memory handling
- `core/router.py` — intent routing and automation mapping
- `automation/` — desktop automation and system utilities
- `voice/` — voice and audio subsystems
- `brain/llm.py` — local AI helper (Ollama support)
- `config/` — settings and command definitions
- `memory/` — persistent storage
- `README.md` — installation and usage instructions

## Current Feature List
- CLI assistant with typed command input
- Windows/app launching, process control, and simple system monitoring
- File search, create, move, delete operations
- Browser automation for websites, Google, and YouTube
- Local offline TTS and audio recording
- Optional voice mode using typed wake-word activation
- Basic long-term memory storage and recall
- Optional Ollama local AI model support

## Known Limitations
- Wake-word detection is not truly audio-based; it is simulated with typed input
- STT support is a fallback to typed transcription unless `whisper.cpp` is installed
- TTS depends on local `pyttsx3` backend availability
- AI responses are stubbed unless `ollama` is installed and configured
- GUI / desktop overlay is not implemented
- Advanced plugin/skill system is not fully built
- Safety policies can be improved beyond the current safe command whitelist

## Suggestions for the Next Agent
1. Verify and improve safety validation for shell commands and file operations.
2. Replace typed wake-word flow with a real audio wake-word engine (`openWakeWord` or similar).
3. Integrate `whisper.cpp` for real STT transcription from microphone input.
4. Enhance TTS with a high-quality offline voice engine like `Piper`.
5. Add a full skill/plugin system for extensibility beyond hard-coded commands.
6. Implement GUI or overlay support for better usability.
7. Harden the `ollama` integration and add prompt engineering for consistent assistant personality.
8. Add unit tests for core router, automation, memory, and voice modules.

## How to Run Locally
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

For voice mode:
```bash
python main.py --voice
```

## Notes
- The project is currently a solid Phase 1 + Phase 2 implementation with voice and AI feature scaffolding.
- The next agent should focus on converting stubbed behavior into real offline speech and reasoning capabilities.
