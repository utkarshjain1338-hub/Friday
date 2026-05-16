#!/usr/bin/env python
"""Friday Assistant — Quick startup verification and demo."""

import asyncio
import shutil
import sys
import os
from pathlib import Path

# Add local bin to PATH
local_bin = Path(__file__).parent / "bin"
os.environ["PATH"] = f"{local_bin}:{os.environ.get('PATH', '')}"

from pathlib import Path


async def check_binaries():
    """Check if all required binaries are available."""
    binaries = {
        "whisper.cpp": shutil.which("whisper.cpp") or shutil.which("whisper"),
        "openwakeword": shutil.which("openWakeWord") or shutil.which("openwakeword"),
        "ollama": shutil.which("ollama"),
        "piper": shutil.which("piper"),
    }

    print("=" * 60)
    print("Friday Assistant — Component Check")
    print("=" * 60)
    for name, path in binaries.items():
        status = "✓" if path else "✗"
        print(f"{status} {name:20} {path or 'NOT FOUND'}")
    print("=" * 60)

    required = ["whisper.cpp", "openwakeword", "ollama"]
    missing = [b for b in required if not binaries[b]]
    if missing:
        print(f"\nWarning: Missing {', '.join(missing)}")
        return False
    print("\n✓ All required components available!")
    return True


async def test_components():
    """Test each component individually."""
    print("\n" + "=" * 60)
    print("Testing Components")
    print("=" * 60)

    # Test STT engine
    print("\n1. STT Engine (whisper.cpp)...")
    try:
        from voice.stt_engine import STTEngine

        stt = STTEngine()
        if stt.whisper_binary:
            print(f"   ✓ Using: {stt.whisper_binary}")
        else:
            print("   ✗ whisper.cpp not found")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    # Test wake word
    print("\n2. Wake Word Engine (openWakeWord)...")
    try:
        from voice.openwakeword_wrapper import OpenWakeWord

        ww = OpenWakeWord()
        if ww.available():
            print(f"   ✓ Using: {ww.binary}")
        else:
            print("   ✗ openWakeWord not found")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    # Test LLM / Ollama
    print("\n3. LLM Engine (Ollama)...")
    try:
        from brain.llm import FridayLLM

        llm = FridayLLM()
        if llm.client.binary:
            print(f"   ✓ Using: {llm.client.binary}")
            print(f"   ✓ Model: {llm.model}")
        else:
            print("   ✗ ollama not found")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    # Test TTS engine
    print("\n4. TTS Engine...")
    try:
        from voice.tts_engine import TTSEngine

        tts = TTSEngine()
        if tts.piper_binary:
            print(f"   ✓ Piper available: {tts.piper_binary}")
        elif tts._pytt_engine:
            print("   ✓ pyttsx3 available (fallback)")
        else:
            print("   ✗ No TTS engine available")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    # Test memory
    print("\n5. Memory Database...")
    try:
        from memory.database import MemoryDatabase

        db = MemoryDatabase()
        db.save("test", "startup verification")
        entries = db.get_recent(1)
        if entries:
            print(f"   ✓ Database working")
            db.close()
        else:
            print("   ✗ Database save/retrieve failed")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    print("\n" + "=" * 60)


async def test_llm_response():
    """Test a simple LLM response."""
    print("\n" + "=" * 60)
    print("Testing LLM Response")
    print("=" * 60)

    try:
        from brain.llm import FridayLLM

        llm = FridayLLM()
        print("\nQuery: 'What can you do?'")
        print("Waiting for response...")
        response = await llm.ask("What can you do?")
        print(f"\nResponse:\n{response}")
    except Exception as e:
        print(f"Error: {e}")

    print("=" * 60)


async def run_interactive():
    """Run Friday in interactive mode."""
    print("\n" + "=" * 60)
    print("Friday CLI — Interactive Mode")
    print("Type 'help' for commands, 'voice mode' for voice mode, 'exit' to quit")
    print("=" * 60 + "\n")

    from ui.cli import run_cli

    await run_cli()


async def main():
    import os

    os.chdir(Path(__file__).parent)

    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "check":
            await check_binaries()
        elif cmd == "test":
            await test_components()
        elif cmd == "llm":
            await test_llm_response()
        elif cmd == "cli":
            await run_interactive()
        elif cmd == "voice":
            from ui.cli import run_voice_mode

            await run_voice_mode()
        else:
            print(f"Unknown command: {cmd}")
            print("Usage: python verify.py [check|test|llm|cli|voice]")
    else:
        # Default: check + test
        await check_binaries()
        await test_components()
        print("\nTo run Friday:")
        print("  python verify.py cli       # Text mode")
        print("  python verify.py voice     # Voice mode")
        print("  python verify.py llm       # Test LLM response")


if __name__ == "__main__":
    asyncio.run(main())
