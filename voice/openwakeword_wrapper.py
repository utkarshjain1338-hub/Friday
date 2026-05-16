import asyncio
import os
import shutil
from typing import Optional, Callable


class OpenWakeWord:
    """Wrapper for an `openWakeWord` binary. If binary is not available,
    this class remains a no-op and callers should fallback to software-based detection.
    """

    def __init__(self, binary: Optional[str] = None):
        self.binary = binary or shutil.which("openWakeWord") or shutil.which("openwakeword")
        if not self.binary:
            from pathlib import Path
            project_root = Path(__file__).parent.parent
            local_bin = project_root / "bin" / "openwakeword"
            if local_bin.exists() and os.access(local_bin, os.X_OK):
                self.binary = str(local_bin)
        self._proc = None

    def available(self) -> bool:
        return bool(self.binary and os.access(self.binary, os.X_OK))

    async def run(self, on_detect: Callable[[str], None]):
        if not self.binary:
            raise RuntimeError("openWakeWord binary not available")

        from loguru import logger
        logger.debug(f"Starting OpenWakeWord binary: {self.binary}")

        self._proc = await asyncio.create_subprocess_exec(
            self.binary,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        async def _read_stderr():
            while True:
                line = await self._proc.stderr.readline()
                if not line:
                    break
                text = line.decode().strip()
                if text:
                    logger.debug(f"OpenWakeWord [STDERR]: {text}")

        asyncio.create_task(_read_stderr())

        # read lines and call on_detect when a keyword line appears
        assert self._proc.stdout
        while True:
            line = await self._proc.stdout.readline()
            if not line:
                break
            text = line.decode().strip()
            if text:
                logger.debug(f"OpenWakeWord output: {text}")
                on_detect(text)

    def stop(self):
        if self._proc:
            try:
                self._proc.terminate()
            except Exception:
                pass
