import asyncio
import logging
import os
import shutil
import subprocess
from pathlib import Path
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
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.piper_lib_path = os.path.join(self.project_root, "third_party", "piper")
        self.piper_models_dirs = [
            os.path.join(self.project_root, "voices"),
            os.path.join(self.project_root, "voice"),
            os.path.join(str(Path.home()), ".local", "share", "piper"),
            os.path.join(str(Path.home()), ".piper"),
        ]
        self.piper_binary = piper_binary or shutil.which("piper")
        if not self.piper_binary:
            local_piper = os.path.join(self.project_root, ".venv", "bin", "piper")
            if os.path.exists(local_piper):
                self.piper_binary = local_piper
        if not self.piper_binary:
            local_piper = os.path.join(self.project_root, "bin", "piper")
            if os.path.exists(local_piper):
                self.piper_binary = local_piper
        self.fallback = fallback
        self.preferred_voice = preferred_voice or "female"
        self.default_piper_voice = default_piper_voice
        self.rate = rate
        self.volume = volume
        self._pytt_engine = None
        self._proc = None
        self.piper_config_path = None
        self.piper_model_path = None
        self._resolve_piper_model(self.default_piper_voice)

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
                logger.warning("pyttsx3 not available (eSpeak/espeak-ng may not be installed): %s", exc)

    def _resolve_piper_model(self, voice_name: str):
        self.piper_model_path = None
        self.piper_config_path = None
        voice_name = (voice_name or self.default_piper_voice).lower()
        aliases = {voice_name}
        if "cori" in voice_name:
            aliases.update({"cori-high", "cori-medium", "en_gb-cori-medium", "en-gb-cori-medium", "en_gb-cori-high", "en-gb-cori-high"})
        if voice_name == "cori-high":
            aliases.update({"en_gb-cori-medium", "en-gb-cori-medium", "cori-medium"})

        for model_dir in self.piper_models_dirs:
            if not model_dir or not os.path.isdir(model_dir):
                continue
            for root, _, files in os.walk(model_dir):
                if not os.path.isdir(root):
                    continue
                for filename in files:
                    lower = filename.lower()
                    base = os.path.splitext(filename)[0].lower()
                    if lower.endswith(".onnx"):
                        for alias in aliases:
                            alias_l = alias.lower()
                            if base == alias_l or base.startswith(f"{alias_l}-") or alias_l.startswith(f"{base}-"):
                                self.piper_model_path = os.path.join(root, filename)
                                break
                        if self.piper_model_path:
                            break
                    if lower.endswith(".onnx.json"):
                        for alias in aliases:
                            alias_l = alias.lower()
                            if base == alias_l or base.startswith(f"{alias_l}-") or alias_l.startswith(f"{base}-"):
                                self.piper_config_path = os.path.join(root, filename)
                                break
                    if self.piper_model_path and self.piper_config_path:
                        break
                if self.piper_model_path and self.piper_config_path:
                    break
            if self.piper_model_path and self.piper_config_path:
                break

        if self.piper_model_path is None:
            for model_dir in self.piper_models_dirs:
                if not os.path.isdir(model_dir):
                    continue
                for candidate in sorted(Path(model_dir).rglob("*.onnx")):
                    label = candidate.stem.lower()
                    if "cori" in label:
                        self.piper_model_path = str(candidate)
                        break
                if self.piper_model_path:
                    break

        if self.piper_config_path is None and self.piper_model_path:
            base = os.path.splitext(self.piper_model_path)[0]
            for candidate in [base + ".onnx.json", base + ".json"]:
                if os.path.exists(candidate):
                    self.piper_config_path = candidate
                    break
            if self.piper_config_path is None:
                for model_dir in self.piper_models_dirs:
                    candidate = os.path.join(model_dir, os.path.basename(base) + ".onnx.json")
                    if os.path.exists(candidate):
                        self.piper_config_path = candidate
                        break

        if self.piper_model_path:
            logger.info("Resolved Piper model: %s", self.piper_model_path)
        else:
            logger.warning("No local Piper model found for voice '%s' in %s", voice_name, self.piper_models_dirs)
        return self.piper_model_path

    async def speak(self, text: str, voice: str = None):
        """Speak text using Piper or fallback to pyttsx3."""
        if not text:
            logger.debug("speak() called with empty/None text — skipping")
            return
        text = str(text)

        piper_voice = voice or os.getenv("PIPER_VOICE") or self.default_piper_voice
        self._resolve_piper_model(piper_voice)

        # 1. Try Piper if available and looks configured
        if self.piper_binary and self.piper_model_path:
            model_path = self.piper_model_path
            config_path = self.piper_config_path or os.path.splitext(model_path)[0] + ".onnx.json"

            logger.debug(f"Piper binary: {self.piper_binary}")
            logger.debug(f"Piper model: {model_path}")
            logger.debug(f"Piper config: {config_path}")

            if os.path.exists(model_path) and os.path.exists(config_path):
                logger.info(f"Using Piper voice: {piper_voice} -> {model_path}")
                loop = asyncio.get_running_loop()

                def _run_piper():
                    try:
                        env = os.environ.copy()
                        if os.path.isdir(self.piper_lib_path):
                            env["LD_LIBRARY_PATH"] = f"{self.piper_lib_path}:{env.get('LD_LIBRARY_PATH', '')}"

                        safe_text = text.replace('\\', '\\\\').replace('"', '\\"')
                        wav_path = os.path.join(self.project_root, "tmp_friday_speech.wav")
                        cmd = [
                            self.piper_binary,
                            "-m", model_path,
                            "-c", config_path,
                            "-f", wav_path,
                        ]
                        logger.debug(f"Running Piper command: {cmd}")
                        proc = subprocess.run(cmd, input=safe_text, text=True, capture_output=True, env=env)
                        if proc.returncode != 0:
                            logger.error("Piper failed: %s", proc.stderr)
                            return False
                        if os.path.exists(wav_path):
                            if shutil.which("paplay"):
                                return subprocess.run(["paplay", wav_path], env=env, capture_output=True, text=True).returncode == 0
                            if shutil.which("aplay"):
                                return subprocess.run(["aplay", "-q", wav_path], env=env, capture_output=True, text=True).returncode == 0
                            if shutil.which("ffplay"):
                                return subprocess.run(["ffplay", "-nodisp", "-autoexit", "-hide_banner", wav_path], env=env, capture_output=True, text=True).returncode == 0
                        return True
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
                logger.debug(f"Piper model/config not found for {piper_voice}. model={self.piper_model_path} config={config_path}")

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
