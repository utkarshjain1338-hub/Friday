import logging
from .tts import TextToSpeech
from .microphone import Microphone
from .stt import SpeechToText
from .wakeword import WakeWordEngine


class AudioManager:
    def __init__(self, voice_name: str = "female", record_duration: float = 5.0):
        self.tts = TextToSpeech(voice_name=voice_name)
        self.mic = Microphone()
        self.stt = SpeechToText()
        self.wakeword = WakeWordEngine()
        self.record_duration = record_duration
        logging.debug("AudioManager initialized with voice=%s duration=%s", voice_name, record_duration)

    def speak(self, text: str):
        self.tts.speak(text)

    def listen(self) -> str:
        audio_path = self.mic.record(self.record_duration, output_path="friday_input.wav")
        return self.stt.transcribe(audio_path)

    def wait_for_wake_word(self) -> bool:
        return self.wakeword.wait_for_wake_word()
