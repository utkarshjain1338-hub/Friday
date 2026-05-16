import asyncio
import tempfile
import wave
from pathlib import Path

import numpy as np
import sounddevice as sd

from .stt_engine import STTEngine


class TranscriptionManager:
    """Record short chunks and transcribe using STTEngine to approximate streaming.

    This is a pragmatic intermediate solution until `whisper.cpp` streaming is integrated.
    """

    def __init__(self, sample_rate: int = 16000, chunk_seconds: float = 1.0, silence_threshold: float = 0.005):
        self.sample_rate = sample_rate
        self.chunk_seconds = chunk_seconds
        self.silence_threshold = silence_threshold
        self.stt = STTEngine()

    async def transcribe_until_silence(self, max_seconds: float = 10.0) -> str:
        loop = asyncio.get_running_loop()
        collected = []
        elapsed = 0.0

        while elapsed < max_seconds:
            data = await loop.run_in_executor(None, self._record_chunk)
            rms = self._rms(data)
            if rms < self.silence_threshold and not collected:
                # no speech detected yet
                elapsed += self.chunk_seconds
                continue

            # write chunk to temp wav and transcribe
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = Path(tmp.name)
            await loop.run_in_executor(None, self._write_wav, data, str(tmp_path))
            text = await self.stt.transcribe_file(str(tmp_path))
            try:
                tmp_path.unlink()
            except Exception:
                pass

            if text:
                collected.append(text)

            # if chunk was silent after speech, break
            if rms < self.silence_threshold and collected:
                break

            elapsed += self.chunk_seconds

        return " ".join(collected).strip()

    def _record_chunk(self):
        return sd.rec(int(self.chunk_seconds * self.sample_rate), samplerate=self.sample_rate, channels=1, dtype="int16")

    def _write_wav(self, frames, out_path: str):
        with wave.open(out_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(frames.tobytes())

    def _rms(self, frames) -> float:
        data = np.asarray(frames, dtype=np.int16).astype(np.float32)
        if data.size == 0:
            return 0.0
        data = data / 32768.0
        return float(np.sqrt(np.mean(data * data)))
