# core/bus.py — shim re-export
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
python_core = project_root / "python-core"
if str(python_core) not in sys.path:
    sys.path.insert(0, str(python_core))

from orchestrator.bus import bus  # noqa: F401
