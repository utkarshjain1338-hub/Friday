import asyncio
import os
import shutil
import subprocess
from loguru import logger


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
        
        # Determine project root and library paths
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.piper_lib_path = os.path.join(self.project_root, "third_party", "piper")
        self.piper_models_dir = os.path.join(self.project_root, "voices")

        if not self.piper_binary:
            local_piper = os.path.join(self.project_root, "bin", "piper")
            if os.path.exists(local_piper):
                self.piper_binary = local_piper

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
        """Speak text using Piper or fallback to pyttsx3."""
        
        # 1. Try Piper if available and looks configured
        if self.piper_binary:
            piper_voice = voice or os.getenv("PIPER_VOICE") or self.default_piper_voice
            # Look for model in voices/ directory: <voice>.onnx
            model_path = os.path.join(self.piper_models_dir, f"{piper_voice}.onnx")
            
            logger.debug(f"Piper binary: {self.piper_binary}")
            logger.debug(f"Piper models dir: {self.piper_models_dir}")
            logger.debug(f"Checking for Piper model at {model_path}")
            
            if os.path.exists(model_path):
                logger.info(f"Using Piper voice: {piper_voice}")
                loop = asyncio.get_running_loop()
                
                def _run_piper():
                    try:
                        # Prepare environment with libraries
                        env = os.environ.copy()
                        env["LD_LIBRARY_PATH"] = f"{self.piper_lib_path}:{env.get('LD_LIBRARY_PATH', '')}"
                        
                        # Check if it's likely a wrapper or the official binary
                        is_official = True
                        try:
                            help_out = subprocess.check_output([self.piper_binary, "--help"], stderr=subprocess.STDOUT, env=env, text=True).lower()
                            # Official piper has --model and --config
                            is_official = "--model" in help_out and "--config" in help_out
                            # If it explicitly has a 'speak' command, it's a wrapper
                            if "speak" in help_out.split():
                                is_official = False
                            
                            logger.debug(f"Piper binary detected as {'official' if is_official else 'wrapper'}")
                        except Exception as e:
                            logger.debug(f"Could not determine Piper type: {e}")
                            pass

                        if not is_official:
                            logger.debug("Using Piper wrapper (speak subcommand)")
                            args = [self.piper_binary, "speak", "--voice", str(piper_voice), text]
                            self._proc = subprocess.Popen(args, env=env)
                            return self._proc.wait() == 0
                        else:
                            logger.debug(f"Using official Piper binary pipeline with model: {model_path}")
                            # Use official piper pipeline
                            # piper -m model -f - | aplay
                            # Escape double quotes and backslashes in text
                            safe_text = text.replace('\\', '\\\\').replace('"', '\\"')
                            cmd = f'echo "{safe_text}" | LD_LIBRARY_PATH="{self.piper_lib_path}" "{self.piper_binary}" -m "{model_path}" -f - | aplay -q'
                            logger.debug(f"Running command: {cmd}")
                            return subprocess.call(cmd, shell=True, env=env) == 0
                    except Exception as e:
                        logger.error(f"Piper execution failed: {e}")
                        return False
                    finally:
                        self._proc = None

                success = await loop.run_in_executor(None, _run_piper)
                if success:
                    return
                logger.warning("Piper failed, falling back to pyttsx3")
            else:
                logger.debug(f"Piper model not found: {model_path}")

        # 2. Fallback to pyttsx3 if Piper skipped or failed
        if self._pytt_engine:
            logger.info("Using pyttsx3 fallback voice")
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
