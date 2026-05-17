import asyncio
import contextlib
import tempfile
import wave
from pathlib import Path

import numpy as np
import sounddevice as sd
from loguru import logger

from voice.stt_engine import STTEngine
from core.bus import bus
from core.events import WAKE_WORD_DETECTED


class WakeWordManager:
    """Detect wake words using openWakeWord (native Python) with STT fallback.

    Strategy:
      1. Try native openWakeWord in-process. This avoids subprocess overhead and
         correctly feeds int16 audio to the model.
      2. If OWW is unavailable or scores stay too low, fall back to Whisper STT:
         continuously record audio and transcribe chunks, looking for the wake phrase.
    """

    # Wake words the user may say. OWW model names are also included so that
    # any OWW hit (alexa, hey_jarvis, hey_mycroft …) immediately wakes Friday.
    WAKE_WORDS = [
        "hey friday", "friday", "computer",
        "hey jarvis", "hey_jarvis",
        "hey mycroft", "hey_mycroft",
        "alexa",
    ]

    def __init__(self, wake_words=None, sample_rate: int = 16000):
        self.wake_words = [w.lower() for w in (wake_words or self.WAKE_WORDS)]
        self.sample_rate = sample_rate
        self.stt = STTEngine()
        self.chunk_size = 1280          # 80 ms — openWakeWord's native chunk
        self.rms_threshold = 0.005      # below this → silence, skip STT
        self._oww_model = None
        self._oww_available = self._try_load_oww()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def wait_for_wake_word(self) -> bool:
        # NOTE: The pre-trained openWakeWord models (hey_jarvis, alexa, hey_mycroft)
        # are accent/voice-specific and do not reliably work for all users.
        # We go straight to Whisper STT detection which correctly transcribes speech.
        # To use OWW, train a custom model for your voice with:
        #   https://github.com/dscripka/openWakeWord#training-new-models
        logger.info("Listening… say 'Hey Friday' or 'Friday' to wake up.")
        return await self._wait_for_stt_wake_word()

    # ------------------------------------------------------------------
    # openWakeWord — native in-process detection
    # ------------------------------------------------------------------

    def _try_load_oww(self) -> bool:
        try:
            from openwakeword.model import Model  # type: ignore
            self._oww_model = Model()
            names = list(self._oww_model.models.keys())
            logger.info(f"openWakeWord loaded. Models: {names}")
            return True
        except Exception as exc:
            logger.warning(f"openWakeWord not available: {exc}")
            return False

    async def _wait_for_oww_native(self, timeout: float = 60.0) -> bool:
        """Run OWW in a thread, streaming int16 audio from sounddevice."""
        loop = asyncio.get_running_loop()
        detected_event = asyncio.Event()
        phrase_holder: dict = {}

        def _run_oww():
            """Blocking loop that feeds audio chunks to the OWW model."""
            try:
                with sd.InputStream(
                    samplerate=self.sample_rate,
                    channels=1,
                    dtype="int16",
                    blocksize=self.chunk_size,
                ) as stream:
                    while not detected_event.is_set():
                        chunk, _overflowed = stream.read(self.chunk_size)
                        audio = chunk[:, 0]   # int16, shape (1280,)
                        try:
                            scores = self._oww_model.predict(audio)
                        except Exception as exc:
                            logger.debug(f"OWW predict error: {exc}")
                            continue

                        for kw, score in scores.items():
                            if score > 0.5:
                                logger.info(f"Wake word detected by OWW: "
                                            f"'{kw}' score={score:.3f}")
                                phrase_holder["phrase"] = kw
                                loop.call_soon_threadsafe(detected_event.set)
                                return
                            elif score > 0.05:
                                logger.debug(f"OWW near-miss: {kw}={score:.3f}")
            except Exception as exc:
                logger.warning(f"OWW streaming error: {exc}")

        fut = loop.run_in_executor(None, _run_oww)
        try:
            await asyncio.wait_for(detected_event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            detected_event.set()   # Signal the thread to stop
            with contextlib.suppress(Exception):
                await fut
            return False

        detected_event.set()   # Ensure thread exits
        with contextlib.suppress(Exception):
            await fut

        phrase = phrase_holder.get("phrase", "")
        if phrase:
            try:
                await bus.emit(WAKE_WORD_DETECTED,
                               {"phrase": phrase, "source": "openWakeWord"})
            except Exception:
                pass
            return True
        return False

    # ------------------------------------------------------------------
    # STT fallback — continuously record then transcribe
    # ------------------------------------------------------------------

    @staticmethod
    def _is_non_speech(text: str) -> bool:
        """Return True for Whisper non-speech / ambient-audio tokens.

        Whisper produces several patterns for non-speech audio:
          (clapping)                  ← parenthetical
          [MUSIC PLAYING]             ← square bracket
          ♪ Yeah ♪ ♪ And you could ♪ ← music notes
          Short fragments             ← noise artifacts
        """
        stripped = text.strip()
        if stripped.startswith("(") and stripped.endswith(")"):
            return True
        if stripped.startswith("[") and stripped.endswith("]"):
            return True
        if "♪" in stripped:
            return True
        if len(stripped.split()) < 2:
            return True
        return False


    async def _wait_for_stt_wake_word(self) -> bool:
        """Record audio in a rolling fashion and transcribe each voiced chunk."""
        loop = asyncio.get_running_loop()

        while True:
            # Record a 3-second chunk (captures a full utterance)
            audio = await loop.run_in_executor(
                None, self._record_seconds, 3.0
            )
            rms = self._rms(audio)
            logger.debug(f"STT chunk RMS={rms:.4f} (threshold={self.rms_threshold})")

            if rms < self.rms_threshold:
                # Pure silence — skip transcription
                continue

            # Save to wav and transcribe
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = Path(tmp.name)

            await loop.run_in_executor(
                None, self._save_wav, audio, str(tmp_path)
            )
            transcription = await self.stt.transcribe_file(str(tmp_path))
            try:
                tmp_path.unlink()
            except Exception:
                pass

            if not transcription:
                continue

            # Filter out Whisper's non-speech parenthetical tokens
            if self._is_non_speech(transcription):
                logger.debug(f"STT: ignoring non-speech '{transcription}'")
                continue

            text = transcription.lower()
            logger.debug(f"STT transcribed: '{text}'")

            for w in self.wake_words:
                if w in text:
                    logger.info(f"Wake word '{w}' detected via STT: '{text}'")
                    try:
                        await bus.emit(
                            WAKE_WORD_DETECTED,
                            {"phrase": w, "transcription": transcription},
                        )
                    except Exception:
                        pass
                    return True

    # ------------------------------------------------------------------
    # Audio helpers
    # ------------------------------------------------------------------

    def _record_seconds(self, duration: float) -> np.ndarray:
        """Record `duration` seconds of 16-bit mono audio. Returns shape (N,)."""
        frames = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=1,
            dtype="int16",
        )
        sd.wait()
        return frames[:, 0]

    def _save_wav(self, audio: np.ndarray, path: str) -> None:
        with wave.open(path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio.tobytes())

    def _rms(self, frames: np.ndarray) -> float:
        if frames is None or frames.size == 0:
            return 0.0
        data = np.asarray(frames, dtype=np.int16).astype(np.float32) / 32768.0
        return float(np.sqrt(np.mean(data * data)))
