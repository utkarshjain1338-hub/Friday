"""Playback manager for audio output with interruption support."""
import asyncio
import subprocess
import os
import platform
from typing import Optional
from loguru import logger


class PlaybackManager:
    """Manages audio playback with interruption support."""

    def __init__(self):
        """Initialize playback manager."""
        self.current_process: Optional[subprocess.Popen] = None
        self.is_playing = False
        self.playback_lock = asyncio.Lock()
        self.system = platform.system()

    def _get_playback_command(self, audio_file: str) -> list:
        """
        Get appropriate playback command for platform.

        Args:
            audio_file: Path to audio file

        Returns:
            Command list for subprocess
        """
        if self.system == "Linux":
            # Try paplay first (PulseAudio), fall back to aplay
            if self._command_exists("paplay"):
                return ["paplay", audio_file]
            elif self._command_exists("aplay"):
                return ["aplay", audio_file]
            elif self._command_exists("ffplay"):
                return ["ffplay", "-nodisp", "-autoexit", "-hide_banner", audio_file]
        elif self.system == "Darwin":  # macOS
            return ["afplay", audio_file]
        elif self.system == "Windows":
            return ["powershell", "-Command", f"(New-Object Media.SoundPlayer '{audio_file}').PlaySync()"]

        # Fallback
        return ["aplay", audio_file]

    def _command_exists(self, command: str) -> bool:
        """Check if command exists on system."""
        result = subprocess.run(
            ["which", command] if self.system != "Windows" else ["where", command],
            capture_output=True,
        )
        return result.returncode == 0

    async def play(self, audio_file: str) -> bool:
        """
        Play audio file asynchronously.

        Args:
            audio_file: Path to audio file

        Returns:
            True if playback completed successfully
        """
        if not os.path.exists(audio_file):
            logger.error(f"Audio file not found: {audio_file}")
            return False

        async with self.playback_lock:
            if self.is_playing:
                logger.warning("Already playing audio, skipping")
                return False

            self.is_playing = True
            try:
                cmd = self._get_playback_command(audio_file)
                self.current_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

                # Wait for process in thread
                loop = asyncio.get_running_loop()
                returncode = await loop.run_in_executor(None, self.current_process.wait)

                success = returncode == 0
                if not success:
                    logger.warning(f"Playback returned code {returncode}")
                return success

            except Exception as e:
                logger.error(f"Playback error: {e}")
                return False
            finally:
                self.is_playing = False
                self.current_process = None

    async def stop(self) -> bool:
        """
        Stop current playback.

        Returns:
            True if stopped successfully
        """
        async with self.playback_lock:
            if self.current_process and self.is_playing:
                try:
                    self.current_process.terminate()
                    # Give it a moment to terminate gracefully
                    await asyncio.sleep(0.1)
                    if self.current_process.poll() is None:
                        self.current_process.kill()
                    self.is_playing = False
                    self.current_process = None
                    logger.info("Playback stopped")
                    return True
                except Exception as e:
                    logger.error(f"Error stopping playback: {e}")
                    return False
        return False

    async def is_playing_audio(self) -> bool:
        """Check if currently playing."""
        async with self.playback_lock:
            return self.is_playing

    async def wait_for_playback(self) -> None:
        """Wait for current playback to finish."""
        while await self.is_playing_audio():
            await asyncio.sleep(0.1)
