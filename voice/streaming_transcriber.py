"""Streaming transcriber for real-time speech recognition with low latency."""
import asyncio
import numpy as np
import wave
import tempfile
import os
from typing import AsyncGenerator, Optional, Callable
from .audio_buffer import AudioBuffer
from .silence_detector import SilenceDetector
from loguru import logger


class StreamingTranscriber:
    """
    Real-time streaming transcriber using whisper.cpp.
    
    Captures audio chunks, detects speech, and transcribes incrementally.
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        chunk_size: int = 512,
        silence_threshold: float = 0.02,
        min_silence_duration: float = 0.5,
        whisper_binary: Optional[str] = None,
        model: str = "tiny.en",
    ):
        """
        Initialize streaming transcriber.

        Args:
            sample_rate: Audio sample rate (Hz)
            chunk_size: Audio chunk size for processing
            silence_threshold: RMS threshold for silence detection
            min_silence_duration: Minimum silence before ending recording
            whisper_binary: Path to whisper.cpp binary (auto-detected if None)
            model: Whisper model name
        """
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.model = model
        self.audio_buffer = AudioBuffer(sample_rate=sample_rate)
        self.silence_detector = SilenceDetector(
            sample_rate=sample_rate,
            silence_threshold=silence_threshold,
            min_silence_duration=min_silence_duration,
        )
        self.whisper_binary = whisper_binary or self._find_whisper()
        self.is_recording = False

    def _find_whisper(self) -> Optional[str]:
        """Find whisper.cpp binary on PATH or local bin directory."""
        import shutil
        from pathlib import Path

        # Check system PATH
        binary = shutil.which("whisper.cpp") or shutil.which("whisper")
        if binary:
            return binary
            
        # Check local bin directory
        project_root = Path(__file__).parent.parent
        local_bin = project_root / "bin" / "whisper"
        if local_bin.exists():
            return str(local_bin)
            
        return None

    async def transcribe_stream(
        self, audio_generator: AsyncGenerator, on_partial: Optional[Callable] = None
    ) -> str:
        """
        Transcribe audio stream in real-time.

        Args:
            audio_generator: Async generator yielding numpy arrays
            on_partial: Callback for partial results

        Returns:
            Full transcription
        """
        self.is_recording = True
        self.audio_buffer.clear()
        self.silence_detector.reset()
        full_transcript = ""

        try:
            async for chunk in audio_generator:
                if not self.is_recording:
                    break

                # Add to buffer
                self.audio_buffer.append(chunk)

                # Check for end-of-speech
                if self.silence_detector.should_end_recording(chunk):
                    logger.info("End of speech detected, transcribing buffer")
                    # Transcribe accumulated buffer
                    transcript = await self._transcribe_buffer()
                    if transcript:
                        full_transcript += " " + transcript
                        if on_partial:
                            on_partial(full_transcript.strip())
                    # Reset for next utterance
                    self.audio_buffer.clear()
                    self.silence_detector.reset()

        except Exception as e:
            logger.error(f"Transcription stream error: {e}")

        finally:
            self.is_recording = False

        return full_transcript.strip()

    async def _transcribe_buffer(self) -> str:
        """Transcribe accumulated audio buffer."""
        audio_data = self.audio_buffer.get_all()
        if len(audio_data) < self.sample_rate * 0.5:  # less than 0.5 seconds
            return ""

        # Write to temporary WAV file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp_path = tmp.name

        try:
            # Write audio data to WAV
            with wave.open(tmp_path, "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(self.sample_rate)
                # Convert float32 to int16
                audio_int16 = np.int16(audio_data * 32767)
                wav_file.writeframes(audio_int16.tobytes())

            # Transcribe using whisper.cpp
            if self.whisper_binary:
                transcript = await self._run_whisper(tmp_path)
                return transcript

            return ""

        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    async def _run_whisper(self, wav_path: str) -> str:
        """Run whisper.cpp on a WAV file and return transcription."""
        try:
            proc = await asyncio.create_subprocess_exec(
                self.whisper_binary,
                str(wav_path),
                "--model",
                self.model,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            if stdout:
                return stdout.decode().strip()
            return ""
        except Exception as e:
            logger.error(f"Whisper.cpp error: {e}")
            return ""

    def stop(self) -> None:
        """Stop recording."""
        self.is_recording = False

    def get_current_duration(self) -> float:
        """Get current recording duration in seconds."""
        return self.audio_buffer.length_seconds()
