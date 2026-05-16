import logging
import asyncio
from .tts_engine import TTSEngine
from .microphone import Microphone
from .stt_engine import STTEngine
from .wakeword_manager import WakeWordManager
from .transcription_manager import TranscriptionManager


class AudioManager:
    def __init__(self, voice_name: str = "female", record_duration: float = 5.0):
        self.tts = TTSEngine()
        self.mic = Microphone()
        self.stt = STTEngine()
        self.wakeword = WakeWordManager()
        self.transcription_manager = TranscriptionManager()
        self.record_duration = record_duration
        logging.debug("AudioManager initialized with voice=%s duration=%s", voice_name, record_duration)

    async def speak(self, text: str):
        await self.tts.speak(text)

    async def listen(self) -> str:
        # Use TranscriptionManager to record until silence and transcribe incrementally
        return await self.transcription_manager.transcribe_until_silence(max_seconds=self.record_duration)

    async def wait_for_wake_word(self) -> bool:
        return await self.wakeword.wait_for_wake_word()
