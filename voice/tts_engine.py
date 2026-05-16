import asyncio
import os
import shutil
import subprocess
import logging


class TTSEngine:
    def __init__(self, piper_binary: str = None, fallback=True, preferred_voice: str = "female", rate: int = 150, volume: float = 0.9, default_piper_voice: str = "cori-high"):
        """Text-to-speech engine.

        - Prefers `piper` if available (CLI invocation).
        - Falls back to `pyttsx3` and attempts to select a female, softer voice.
        Args:
            piper_binary: explicit piper binary path
            fallback: allow using pyttsx3 fallback
            preferred_voice: keyword to prefer when selecting a voice (e.g. 'female')
            rate: speaking rate for pyttsx3 (lower is slower)
            volume: volume for pyttsx3 (0.0 - 1.0)
            default_piper_voice: preferred piper voice when available
        """
        self.piper_binary = piper_binary or shutil.which("piper")
        self.fallback = fallback
        self.preferred_voice = preferred_voice or "female"
        self.default_piper_voice = default_piper_voice
        self.rate = rate
        self.volume = volume
        self._pytt_engine = None
        self._proc = None

        if self.fallback:
            try:
                import pyttsx3

                engine = pyttsx3.init()
                # Set rate and volume to softer defaults
                try:
                    engine.setProperty("rate", self.rate)
                except Exception:
                    pass
                try:
                    engine.setProperty("volume", float(self.volume))
                except Exception:
                    pass

                # Prefer voices matching the preferred_voice keyword
                try:
                    voices = engine.getProperty("voices") or []
                    chosen = None
                    for v in voices:
                        name = (v.name or "").lower()
                        vid = (v.id or "").lower()
                        if self.preferred_voice.lower() in name or self.preferred_voice.lower() in vid:
                            chosen = v
                            break

                    # Fallback heuristic: pick any voice that looks female
                    if not chosen:
                        for v in voices:
                            name = (v.name or "").lower()
                            vid = (v.id or "").lower()
                            if "female" in name or "female" in vid or "woman" in name:
                                chosen = v
                                break

                    if chosen:
                        try:
                            engine.setProperty("voice", chosen.id)
                        except Exception:
                            pass
                except Exception:
                    pass

                self._pytt_engine = engine
            except Exception as exc:
                logging.warning("pyttsx3 not available: %s", exc)

    async def speak(self, text: str, voice: str = None):
        # Prefer piper if available. If `PIPER_VOICE` env var is set we try to pass it.
        if self.piper_binary:
            loop = asyncio.get_running_loop()

            piper_voice = voice or os.getenv("PIPER_VOICE") or self.default_piper_voice

            def _run():
                try:
                    args = [self.piper_binary, "speak"]
                    # Best-effort: pass a --voice flag if configured (may be ignored by some piper builds)
                    if piper_voice:
                        args += ["--voice", str(piper_voice)]
                    args += [text]
                    self._proc = subprocess.Popen(args)
                    self._proc.wait()
                finally:
                    self._proc = None

            await loop.run_in_executor(None, _run)
            return

        if self._pytt_engine:
            loop = asyncio.get_running_loop()
            try:
                # Allow runtime voice override
                if voice:
                    try:
                        voices = self._pytt_engine.getProperty("voices") or []
                        for v in voices:
                            if voice.lower() in (v.name or "").lower() or voice.lower() in (v.id or "").lower():
                                try:
                                    self._pytt_engine.setProperty("voice", v.id)
                                except Exception:
                                    pass
                                break
                    except Exception:
                        pass

                await loop.run_in_executor(None, self._pytt_engine.say, text)
                await loop.run_in_executor(None, self._pytt_engine.runAndWait)
            finally:
                # restore rate/volume if needed (some backends mutate state)
                try:
                    self._pytt_engine.setProperty("rate", self.rate)
                    self._pytt_engine.setProperty("volume", float(self.volume))
                except Exception:
                    pass
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
