import argparse
import asyncio
import os
import sys
from pathlib import Path

# ── Package resolution ─────────────────────────────────────────────────────
# All subpackages (automation, memory, learning, workflows, intelligence,
# semantics) live under python-core/.  The orchestrator layer (core.*) lives
# under python-core/orchestrator/.  Add both to sys.path so every import
# works from whichever entry point is used.
_project_root = Path(__file__).parent
_python_core  = _project_root / "python-core"
_orchestrator = _python_core / "orchestrator"

for _p in (_project_root, _python_core, _orchestrator):
    _p_str = str(_p)
    if _p_str not in sys.path:
        sys.path.insert(0, _p_str)
# ───────────────────────────────────────────────────────────────────────────

# Add local bin to PATH
local_bin = _project_root / "bin"
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
