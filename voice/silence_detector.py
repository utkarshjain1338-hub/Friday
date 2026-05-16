"""Silence detection for audio chunking and voice activity detection."""
import numpy as np


class SilenceDetector:
    """Detects silence and voice activity in audio streams."""

    def __init__(
        self,
        sample_rate: int = 16000,
        silence_threshold: float = 0.02,
        min_silence_duration: float = 0.5,
    ):
        """
        Initialize silence detector.

        Args:
            sample_rate: Audio sample rate (Hz)
            silence_threshold: RMS threshold for silence (0-1 range)
            min_silence_duration: Minimum silence duration to trigger end-of-speech (seconds)
        """
        self.sample_rate = sample_rate
        self.silence_threshold = silence_threshold
        self.min_silence_duration = min_silence_duration
        self.silence_frame_count = 0
        self.min_silence_frames = int(sample_rate * min_silence_duration / 512)  # assuming 512 frame chunks

    def is_silent(self, chunk: np.ndarray) -> bool:
        """
        Detect if audio chunk is silent.

        Args:
            chunk: NumPy audio chunk (float32, -1 to 1 range)

        Returns:
            True if chunk is silent
        """
        if len(chunk) == 0:
            return True
        rms = float(np.sqrt(np.mean(chunk**2)))
        return rms < self.silence_threshold

    def is_speech(self, chunk: np.ndarray) -> bool:
        """Detect if chunk contains speech."""
        return not self.is_silent(chunk)

    def should_end_recording(self, chunk: np.ndarray) -> bool:
        """
        Determine if recording should end based on silence pattern.

        Args:
            chunk: Audio chunk

        Returns:
            True if recording should end
        """
        if self.is_silent(chunk):
            self.silence_frame_count += 1
        else:
            self.silence_frame_count = 0

        return self.silence_frame_count >= self.min_silence_frames

    def reset(self) -> None:
        """Reset silence counter."""
        self.silence_frame_count = 0

    def get_rms(self, chunk: np.ndarray) -> float:
        """
        Calculate RMS of audio chunk.

        Args:
            chunk: Audio chunk

        Returns:
            RMS value
        """
        if len(chunk) == 0:
            return 0.0
        return float(np.sqrt(np.mean(chunk**2)))
