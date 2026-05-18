import asyncio
import shutil
import subprocess
from pathlib import Path
from typing import Optional
from loguru import logger


class STTEngine:
    def __init__(self, whisper_binary: str = None, model: str = "tiny.en"):
        self.whisper_binary = whisper_binary or shutil.which("whisper.cpp") or shutil.which("whisper")
        if not self.whisper_binary:
            silence_threshold: float = 0.005
            project_root = Path(__file__).parent.parent
            local_bin = project_root / "bin" / "whisper"
            if local_bin.exists():
                self.whisper_binary = str(local_bin)
        self.model = model

    async def transcribe_file(self, audio_path: str) -> str:
        audio_path = Path(audio_path)
        if self.whisper_binary and audio_path.exists():
            # run whisper as subprocess asynchronously
            proc = await asyncio.create_subprocess_exec(
                self.whisper_binary, str(audio_path), "--model", self.model,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            if stdout:
                text = stdout.decode().strip()
                # filter out non-speech tags from whisper like (dramatic music) or [Silence]
                import re
                text = re.sub(r'\[.*?\]', '', text)
                text = re.sub(r'\(.*?\)', '', text)
                text = re.sub(r'\*.*?\*', '', text)
                text = text.strip()
                from loguru import logger
                if text:
                    logger.debug(f"STT Result: {text}")
                    return text
                else:
                    return ""
        # fallback to asking the user
        loop = asyncio.get_running_loop()
        transcription = await loop.run_in_executor(None, input, "Transcription fallback - type your transcription: ")
        # emit transcription event if bus available
        try:
            from core.bus import bus
            from core.events import TRANSCRIPTION_COMPLETED

            await bus.emit(TRANSCRIPTION_COMPLETED, {"audio": str(audio_path), "text": transcription})
        except Exception:
            pass
        return transcription
