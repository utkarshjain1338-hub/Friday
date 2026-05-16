import asyncio
import shutil
import subprocess
import logging


class TTSEngine:
    def __init__(self, piper_binary: str = None, fallback=True):
        self.piper_binary = piper_binary or shutil.which("piper")
        self.fallback = fallback
        self._pytt_engine = None
        self._proc = None
        if self.fallback:
            try:
                import pyttsx3

                self._pytt_engine = pyttsx3.init()
            except Exception as exc:
                logging.warning("pyttsx3 not available: %s", exc)

    async def speak(self, text: str, voice: str = None):
        if self.piper_binary:
            # Run piper as subprocess (blocking) in executor
            loop = asyncio.get_running_loop()
            # Use Popen so we can terminate if needed
            def _run():
                try:
                    self._proc = subprocess.Popen([self.piper_binary, "speak", text])
                    self._proc.wait()
                finally:
                    self._proc = None

            await loop.run_in_executor(None, _run)
            return

        if self._pytt_engine:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._pytt_engine.say, text)
            await loop.run_in_executor(None, self._pytt_engine.runAndWait)
            return

        # Final fallback: print
        print(f"Friday says: {text}")

    def stop(self):
        # terminate piper subprocess if running
        try:
            if self._proc:
                self._proc.terminate()
                self._proc = None
                return True
        except Exception:
            pass

        # try to stop pyttsx3 engine
        try:
            if self._pytt_engine:
                self._pytt_engine.stop()
                return True
        except Exception:
            pass

        return False
