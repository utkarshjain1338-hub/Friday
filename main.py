import argparse
import asyncio
import os
import sys
from pathlib import Path

# Add local bin to PATH
local_bin = Path(__file__).parent / "bin"
os.environ["PATH"] = f"{local_bin}:{os.environ.get('PATH', '')}"

from ui.cli import run_cli, run_voice_mode


def parse_args():
    parser = argparse.ArgumentParser(description="Friday — offline Linux assistant")
    parser.add_argument("--voice", action="store_true", help="Start Friday in voice mode")
    return parser.parse_args()


def main():
    args = parse_args()

    print("Welcome to Friday — your offline Linux assistant.")
    print("Type 'help' for commands or run with --voice for voice mode.")

    if args.voice:
        asyncio.run(run_voice_mode())
    else:
        asyncio.run(run_cli())


if __name__ == "__main__":
    main()
