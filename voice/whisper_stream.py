import asyncio
import shutil
import tempfile
from pathlib import Path
from typing import AsyncGenerator


class WhisperStreamer:
    """Simple wrapper to call a whisper binary on temporary WAV chunks and yield transcriptions.

    This is a pragmatic streaming shim: it writes short audio clips and calls the
    whisper binary (if available) to transcribe them, yielding partial results.
    Replace with a native streaming interface for production.
    """

    def __init__(self, whisper_binary: str = None, model: str = "tiny.en"):
        self.whisper_binary = whisper_binary or shutil.which("whisper.cpp") or shutil.which("whisper")
        self.model = model

    async def transcribe_chunk(self, wav_path: str) -> str:
        if not self.whisper_binary:
            return ""
        proc = await asyncio.create_subprocess_exec(
            self.whisper_binary, wav_path, "--model", self.model,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if stdout:
            return stdout.decode().strip()
        return ""

    async def transcribe_stream(self, chunks: AsyncGenerator[str, None]):
        """Accepts an async generator of WAV file paths and yields transcriptions."""
        async for wav in chunks:
            text = await self.transcribe_chunk(wav)
            yield text
