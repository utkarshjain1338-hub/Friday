import asyncio


class WakeWordEngine:
    """Stub wake-word engine.

    Replace with `openWakeWord` integration later.
    """

    def __init__(self, wake_words=None):
        self.wake_words = wake_words or ["hey friday", "friday", "computer"]

    async def wait_for_wake_word(self) -> bool:
        # Fallback interactive wake-word: blocks in thread
        loop = asyncio.get_running_loop()
        phrase = await loop.run_in_executor(None, input, "Type wake word to simulate: ")
        return phrase.strip().lower() in self.wake_words
