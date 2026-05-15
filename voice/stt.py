import shutil
import subprocess
from pathlib import Path


class SpeechToText:
    def __init__(self, whisper_binary: str = None):
        self.whisper_binary = whisper_binary or shutil.which("whisper.cpp") or shutil.which("whisper")
        self.model = "small.en"

    def transcribe(self, audio_path: str) -> str:
        audio_path = Path(audio_path)
        if self.whisper_binary and audio_path.exists():
            try:
                result = subprocess.run(
                    [self.whisper_binary, str(audio_path), "--model", self.model],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                transcription = result.stdout.strip()
                if transcription:
                    return transcription
            except Exception:
                pass

        return input("Transcription fallback - type what you heard: ")
