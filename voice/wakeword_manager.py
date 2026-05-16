import asyncio
import contextlib
import tempfile
import wave
from pathlib import Path

import numpy as np
import sounddevice as sd
from loguru import logger

from voice.openwakeword_wrapper import OpenWakeWord
from voice.stt_engine import STTEngine
from core.bus import bus
from core.events import WAKE_WORD_DETECTED


class WakeWordManager:
    """Detect wake words using real wake-word or software fallback.

    The manager uses openWakeWord when available for low-latency detection.
    Otherwise, it falls back to a simple audio + speech transcription loop.
    """

    def __init__(self, wake_words=None, sample_rate: int = 16000):
        self.wake_words = [w.lower() for w in (wake_words or ["hey friday", "friday", "computer"])]
        self.sample_rate = sample_rate
        self.stt = STTEngine()
        self.open_wakeword = OpenWakeWord()
        self.chunk_duration = 1.0
        self.verify_duration = 3.0
        self.rms_threshold = 0.01

    async def wait_for_wake_word(self) -> bool:
        if self.open_wakeword.available():
            detected = await self._wait_for_open_wakeword()
            if detected:
                return True
            logger.warning("openWakeWord failed or timed out, falling back to STT wake word detection")
        return await self._wait_for_stt_wake_word()

    async def _wait_for_open_wakeword(self) -> bool:
        detected = asyncio.Event()
        phrase_holder = {"phrase": None}

        def on_detect(text: str):
            phrase_holder["phrase"] = text.strip().lower()
            detected.set()

        task = asyncio.create_task(self.open_wakeword.run(on_detect))
        try:
            # Wait until the process starts or fails
            while self.open_wakeword._proc is None and not task.done():
                await asyncio.sleep(0.01)

            if self.open_wakeword._proc is None:
                logger.warning("openWakeWord did not start correctly")
                return False

            wait_task = asyncio.create_task(detected.wait())
            proc_task = asyncio.create_task(self.open_wakeword._proc.wait())
            done, pending = await asyncio.wait(
                {wait_task, proc_task},
                return_when=asyncio.FIRST_COMPLETED,
                timeout=15.0,
            )

            if wait_task in done and detected.is_set():
                phrase = phrase_holder.get("phrase") or ""
                if phrase:
                    try:
                        await bus.emit(WAKE_WORD_DETECTED, {"phrase": phrase, "source": "openWakeWord"})
                    except Exception:
                        pass
                    return True
                return False

            if proc_task in done:
                logger.warning("openWakeWord process exited before detecting a wake word")
                return False

            logger.warning("openWakeWord timed out waiting for a wake word")
            return False
        finally:
            self.open_wakeword.stop()
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

    async def _wait_for_stt_wake_word(self) -> bool:
        loop = asyncio.get_running_loop()
        while True:
            data = await loop.run_in_executor(None, self._record_blocking, self.chunk_duration)
            rms = self._rms(data)
            if rms < self.rms_threshold:
                continue

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = Path(tmp.name)

            await loop.run_in_executor(None, self._record_to_wav, self.verify_duration, str(tmp_path))
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
        data = data / 32768.0
        return float(np.sqrt(np.mean(data * data)))
