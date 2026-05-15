import logging


class TextToSpeech:
    def __init__(self, voice_name: str = "female", rate: int = 170, volume: float = 0.9):
        self.engine = None
        self.voice_name = voice_name
        self.rate = rate
        self.volume = volume

        try:
            import pyttsx3

            self.engine = pyttsx3.init()
            self.engine.setProperty("rate", self.rate)
            self.engine.setProperty("volume", self.volume)
            self._select_voice(voice_name)
        except Exception as exc:
            logging.warning("TTS engine unavailable, falling back to text output: %s", exc)
            self.engine = None

    def _select_voice(self, voice_name: str):
        if not self.engine:
            return

        voices = self.engine.getProperty("voices") or []
        for voice in voices:
            if voice_name.lower() in voice.name.lower() or voice_name.lower() in voice.id.lower():
                self.engine.setProperty("voice", voice.id)
                return

        for voice in voices:
            if "female" in voice.name.lower() or "female" in voice.id.lower():
                self.engine.setProperty("voice", voice.id)
                return

    def speak(self, text: str):
        if self.engine:
            self.engine.say(text)
            self.engine.runAndWait()
        else:
            print(f"Friday says: {text}")
