import asyncio
import tempfile
import wave
from pathlib import Path

import numpy as np
import sounddevice as sd

from voice.stt_engine import STTEngine
from core.bus import bus
from core.events import WAKE_WORD_DETECTED


class WakeWordManager:
    """Detect wake words using simple energy threshold + STT verification.

    This is a pragmatic integration that uses the microphone stream and the
    STT engine (whisper.cpp if available) to verify whether spoken audio
    contains a wake word. Replace with `openWakeWord` integration for
    a production-ready low-latency engine.
    """

    def __init__(self, wake_words=None, sample_rate: int = 16000):
        self.wake_words = [w.lower() for w in (wake_words or ["hey friday", "friday", "computer"]) ]
        self.sample_rate = sample_rate
        self.stt = STTEngine()
        self.chunk_duration = 1.0
        self.verify_duration = 3.0
        self.rms_threshold = 0.01

    async def wait_for_wake_word(self) -> bool:
        loop = asyncio.get_running_loop()
        while True:
            # record short chunk
            data = await loop.run_in_executor(None, self._record_blocking, self.chunk_duration)
            rms = self._rms(data)
            if rms < self.rms_threshold:
                continue

            # potential speech detected; record a longer verification clip
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = Path(tmp.name)

            await loop.run_in_executor(None, self._record_to_wav, self.verify_duration, str(tmp_path))
            # transcribe and check for wake word
            transcription = await self.stt.transcribe_file(str(tmp_path))
            try:
                tmp_path.unlink()
            except Exception:
                pass

            if not transcription:
                continue

            text = transcription.lower()
            for w in self.wake_words:
                if w in text:
                    # emit event
                    try:
                        await bus.emit(WAKE_WORD_DETECTED, {"phrase": w, "transcription": transcription})
                    except Exception:
                        pass
                    return True

    def _record_blocking(self, duration: float):
        frames = sd.rec(int(duration * self.sample_rate), samplerate=self.sample_rate, channels=1, dtype="int16")
        sd.wait()
        return frames

    def _record_to_wav(self, duration: float, out_path: str):
        frames = sd.rec(int(duration * self.sample_rate), samplerate=self.sample_rate, channels=1, dtype="int16")
        sd.wait()
        with wave.open(out_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(frames.tobytes())

    def _rms(self, frames) -> float:
        if frames is None:
            return 0.0
        data = np.asarray(frames, dtype=np.int16).astype(np.float32)
        if data.size == 0:
            return 0.0
        # normalize int16 to [-1,1]
        data = data / 32768.0
        return float(np.sqrt(np.mean(data * data)))
