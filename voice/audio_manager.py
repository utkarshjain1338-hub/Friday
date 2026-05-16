import logging
import asyncio
import sounddevice as sd
from .tts_engine import TTSEngine
from .microphone import Microphone
from .stt_engine import STTEngine
from .wakeword_manager import WakeWordManager
from .transcription_manager import TranscriptionManager
from .streaming_transcriber import StreamingTranscriber


class AudioManager:
    def __init__(self, voice_name: str = "female", record_duration: float = 5.0):
        self.tts = TTSEngine()
        self.mic = Microphone()
        self.stt = STTEngine()
        self.wakeword = WakeWordManager()
        self.transcription_manager = TranscriptionManager()
        self.streaming_transcriber = StreamingTranscriber()
        self.record_duration = record_duration
        self.streaming_chunk_seconds = (
            self.streaming_transcriber.chunk_size / self.streaming_transcriber.sample_rate
        )
        logging.debug(
            "AudioManager initialized with voice=%s duration=%s streaming=%s",
            voice_name,
            record_duration,
            bool(self.streaming_transcriber.whisper_binary),
        )

    async def speak(self, text: str):
        await self.tts.speak(text)

    async def listen(self) -> str:
        if self.streaming_transcriber.whisper_binary:
            return await self._listen_streaming(max_seconds=self.record_duration)

        return await self.transcription_manager.transcribe_until_silence(max_seconds=self.record_duration)

    async def _listen_streaming(self, max_seconds: float = 10.0) -> str:
        loop = asyncio.get_running_loop()

        async def audio_generator():
            elapsed = 0.0
            while elapsed < max_seconds:
                chunk = await loop.run_in_executor(
                    None,
                    self._record_stream_chunk,
                    self.streaming_chunk_seconds,
                )
                if chunk is None:
                    break
                yield chunk
                elapsed += self.streaming_chunk_seconds

        return await self.streaming_transcriber.transcribe_stream(audio_generator())

    def _record_stream_chunk(self, duration: float):
        frames = sd.rec(
            int(duration * self.streaming_transcriber.sample_rate),
            samplerate=self.streaming_transcriber.sample_rate,
            channels=1,
            dtype="float32",
        )
        sd.wait()
        return frames.flatten()

    async def wait_for_wake_word(self) -> bool:
        return await self.wakeword.wait_for_wake_word()
