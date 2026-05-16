# Implementation Status — Friday Assistant

## Summary
This file lists what has been implemented so far and what remains to complete the production-ready Friday assistant.

---

## Implemented
- Migrate core to async (asyncio-based runner and refactors)
- Async Event Bus (decoupled event/emitter system)
- Real wake-word integration scaffold (openWakeWord wrapper + fallback)
- Ollama client streaming integration (stdout streaming, prompt injection via `brain/prompt_builder.py`)
- Prompt builder for constructing system + memory + history prompts (`brain/prompt_builder.py`)
- Plugin/skill system base and loader (registry, discover plugins)
- Basic permission manager and router checks for risky commands (`security/permission_manager.py`)
- Sample plugin and a plugin loader test (`tests/test_plugins.py`)
- CI workflow added (`.github/workflows/ci.yml`)
- README updated with CI and systemd packaging notes

## In Progress
- Add streaming STT pipeline (whisper.cpp) — integrating low-latency token streaming and replacing chunked-shim pipeline

## Remaining / Planned work
- Replace TTS with `piper` and add robust, interruptible playback across platforms
- Harden Ollama integration: safety filters, streaming tokens to UI/event bus, robust subprocess management
- Add more concrete example skills (file manager, system controller, browser automation) and plugin loader integration tests
- Enhance memory: retrieval, embeddings, similarity search, and compacting policies
- Improve safety model: permission UI/workflow, confirmations, audit logs, and risk enforcement in router/executor
- Add logging, profiling, diagnostics, and performance tuning (loguru, trace, flamegraphs)
- Background daemon packaging: systemd service, packaging artifacts, installer scripts
- Terminal HUD / lightweight dashboard for status and logs
- Expand tests and CI: unit tests for skills, integration tests for audio and LLM flows, and packaging steps

---

If you want, I can now:
- proceed to fully implement `whisper.cpp` streaming (low-latency token streaming), or
- wire the `openWakeWord` binary as a continuously-running detector, or
- implement `piper` playback with interruptibility.

Tell me which I should start next and I will begin implementing it.
