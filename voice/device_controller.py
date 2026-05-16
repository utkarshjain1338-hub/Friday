"""Audio device ownership and locking system."""
import asyncio
from enum import Enum
from typing import Optional
from loguru import logger


class AudioOwner(Enum):
    """Audio device ownership types."""

    WAKEWORD = "wakeword"
    MICROPHONE = "microphone"
    SPEAKER = "speaker"
    STT = "stt"
    TTS = "tts"
    NONE = "none"


class DeviceController:
    """Manages exclusive access to audio devices."""

    def __init__(self):
        """Initialize device controller."""
        self.microphone_owner: Optional[AudioOwner] = None
        self.speaker_owner: Optional[AudioOwner] = None
        self.microphone_lock = asyncio.Lock()
        self.speaker_lock = asyncio.Lock()

    async def acquire_microphone(self, owner: AudioOwner, timeout: float = 5.0) -> bool:
        """
        Acquire exclusive microphone access.

        Args:
            owner: Component requesting access
            timeout: Timeout in seconds

        Returns:
            True if acquired, False if timeout
        """
        try:
            # Wait for lock with timeout
            await asyncio.wait_for(self.microphone_lock.acquire(), timeout=timeout)

            if self.microphone_owner and self.microphone_owner != owner:
                self.microphone_lock.release()
                logger.warning(
                    f"Microphone already owned by {self.microphone_owner.value}, "
                    f"request from {owner.value} denied"
                )
                return False

            self.microphone_owner = owner
            logger.info(f"Microphone acquired by {owner.value}")
            return True

        except asyncio.TimeoutError:
            logger.warning(f"Microphone acquisition timeout for {owner.value}")
            return False

    async def release_microphone(self, owner: AudioOwner) -> bool:
        """
        Release microphone access.

        Args:
            owner: Component releasing access

        Returns:
            True if released, False if not owner
        """
        if self.microphone_owner == owner:
            self.microphone_owner = None
            try:
                self.microphone_lock.release()
            except RuntimeError:
                pass
            logger.info(f"Microphone released by {owner.value}")
            return True
        else:
            logger.warning(f"Microphone release refused: not owner (owner={self.microphone_owner})")
            return False

    async def acquire_speaker(self, owner: AudioOwner, timeout: float = 5.0) -> bool:
        """
        Acquire exclusive speaker access.

        Args:
            owner: Component requesting access
            timeout: Timeout in seconds

        Returns:
            True if acquired, False if timeout
        """
        try:
            await asyncio.wait_for(self.speaker_lock.acquire(), timeout=timeout)

            if self.speaker_owner and self.speaker_owner != owner:
                self.speaker_lock.release()
                logger.warning(
                    f"Speaker already owned by {self.speaker_owner.value}, "
                    f"request from {owner.value} denied"
                )
                return False

            self.speaker_owner = owner
            logger.info(f"Speaker acquired by {owner.value}")
            return True

        except asyncio.TimeoutError:
            logger.warning(f"Speaker acquisition timeout for {owner.value}")
            return False

    async def release_speaker(self, owner: AudioOwner) -> bool:
        """
        Release speaker access.

        Args:
            owner: Component releasing access

        Returns:
            True if released, False if not owner
        """
        if self.speaker_owner == owner:
            self.speaker_owner = None
            try:
                self.speaker_lock.release()
            except RuntimeError:
                pass
            logger.info(f"Speaker released by {owner.value}")
            return True
        else:
            logger.warning(f"Speaker release refused: not owner (owner={self.speaker_owner})")
            return False

    async def is_microphone_free(self) -> bool:
        """Check if microphone is available."""
        return self.microphone_owner is None

    async def is_speaker_free(self) -> bool:
        """Check if speaker is available."""
        return self.speaker_owner is None

    async def get_microphone_owner(self) -> Optional[AudioOwner]:
        """Get current microphone owner."""
        return self.microphone_owner

    async def get_speaker_owner(self) -> Optional[AudioOwner]:
        """Get current speaker owner."""
        return self.speaker_owner

    async def release_all(self, owner: AudioOwner) -> None:
        """Release all devices owned by a component."""
        await self.release_microphone(owner)
        await self.release_speaker(owner)

    async def force_release_all(self) -> None:
        """Force release all devices (emergency)."""
        self.microphone_owner = None
        self.speaker_owner = None
        try:
            self.microphone_lock.release()
        except RuntimeError:
            pass
        try:
            self.speaker_lock.release()
        except RuntimeError:
            pass
        logger.warning("All audio devices force-released")


# Global singleton
_device_controller: Optional[DeviceController] = None


async def get_device_controller() -> DeviceController:
    """Get or create the global device controller."""
    global _device_controller
    if _device_controller is None:
        _device_controller = DeviceController()
    return _device_controller
