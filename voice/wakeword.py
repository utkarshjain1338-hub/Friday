class WakeWordEngine:
    def __init__(self, wake_words=None):
        self.wake_words = wake_words or ["hey friday", "friday", "computer"]

    def is_wake_word(self, text: str) -> bool:
        return text.strip().lower() in self.wake_words

    def wait_for_wake_word(self) -> bool:
        phrase = input("Type the wake word to start listening (e.g. 'hey friday'): ")
        return self.is_wake_word(phrase)
