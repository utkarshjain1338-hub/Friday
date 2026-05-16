"""Rolling audio buffer for real-time streaming transcription."""
import numpy as np
from collections import deque
from typing import Optional


class AudioBuffer:
    """Manages a rolling circular buffer for audio chunks."""

    def __init__(self, sample_rate: int = 16000, buffer_duration: float = 5.0):
        """
        Initialize audio buffer.

        Args:
            sample_rate: Audio sample rate (Hz)
            buffer_duration: Total buffer duration in seconds
        """
        self.sample_rate = sample_rate
        self.buffer_size = int(sample_rate * buffer_duration)
        self.buffer = deque(maxlen=self.buffer_size)
        self.lock = None  # can be replaced with threading.Lock if needed

    def append(self, chunk: np.ndarray) -> None:
        """Add audio chunk to buffer."""
        if isinstance(chunk, np.ndarray):
            for sample in chunk:
                self.buffer.append(sample)
        else:
            self.buffer.append(chunk)

    def get_latest(self, duration: float) -> Optional[np.ndarray]:
        """
        Get latest N seconds of audio.

        Args:
            duration: Duration in seconds

        Returns:
            NumPy array of audio samples or None if insufficient data
        """
        num_samples = int(self.sample_rate * duration)
        if len(self.buffer) < num_samples:
            return None
        # Get last num_samples from buffer
        return np.array(list(self.buffer)[-num_samples:], dtype=np.float32)

    def get_all(self) -> np.ndarray:
        """Get all buffered audio as NumPy array."""
        return np.array(list(self.buffer), dtype=np.float32)

    def clear(self) -> None:
        """Clear the buffer."""
        self.buffer.clear()

    def length_seconds(self) -> float:
        """Get current buffer duration in seconds."""
        return len(self.buffer) / self.sample_rate
