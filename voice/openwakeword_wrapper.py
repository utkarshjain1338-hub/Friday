import asyncio
import shutil
from typing import Optional, Callable


class OpenWakeWord:
    """Wrapper for an `openWakeWord` binary. If binary is not available,
    this class remains a no-op and callers should fallback to software-based detection.
    """

    def __init__(self, binary: Optional[str] = None):
        self.binary = binary or shutil.which("openWakeWord") or shutil.which("openwakeword")
        self._proc = None

    def available(self) -> bool:
        return bool(self.binary)

    async def run(self, on_detect: Callable[[str], None]):
        if not self.binary:
            raise RuntimeError("openWakeWord binary not available")

        self._proc = await asyncio.create_subprocess_exec(
            self.binary,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # read lines and call on_detect when a keyword line appears
        assert self._proc.stdout
        while True:
            line = await self._proc.stdout.readline()
            if not line:
                break
            text = line.decode().strip()
            if text:
                on_detect(text)

    def stop(self):
        if self._proc:
            try:
                self._proc.terminate()
            except Exception:
                pass
