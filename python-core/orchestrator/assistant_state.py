"""Centralized state manager for the Friday assistant."""
import asyncio
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Any, Dict
from loguru import logger


class AssistantMode(Enum):
    """Assistant operational mode."""

    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    ERROR = "error"


@dataclass
class AssistantState:
    """Central state for the Friday assistant."""

    # Operational state
    mode: AssistantMode = field(default=AssistantMode.IDLE)
    is_running: bool = field(default=False)

    # Audio state
    listening: bool = field(default=False)
    speaking: bool = field(default=False)
    wakeword_active: bool = field(default=False)
    microphone_busy: bool = field(default=False)
    speaker_busy: bool = field(default=False)

    # Processing state
    processing: bool = field(default=False)
    interrupted: bool = field(default=False)

    # Current operation
    current_skill: Optional[str] = field(default=None)
    current_task: Optional[str] = field(default=None)
    last_utterance: Optional[str] = field(default=None)
    last_response: Optional[str] = field(default=None)

    # Statistics
    utterances_processed: int = field(default=0)
    errors_count: int = field(default=0)

    # Custom data
    metadata: Dict[str, Any] = field(default_factory=dict)


class AssistantStateManager:
    """Thread-safe assistant state manager."""

    def __init__(self):
        """Initialize state manager."""
        self.state = AssistantState()
        self.lock = asyncio.Lock()
        self.state_change_callbacks = []

    async def update_mode(self, mode: AssistantMode) -> None:
        """
        Update assistant mode.

        Args:
            mode: New mode
        """
        async with self.lock:
            old_mode = self.state.mode
            self.state.mode = mode
            if old_mode != mode:
                logger.info(f"Mode change: {old_mode.value} → {mode.value}")
                await self._notify_change("mode", mode)

    async def set_listening(self, listening: bool) -> None:
        """Set listening state."""
        async with self.lock:
            old = self.state.listening
            self.state.listening = listening
            if old != listening:
                logger.info(f"Listening: {listening}")
                await self._notify_change("listening", listening)

    async def set_speaking(self, speaking: bool) -> None:
        """Set speaking state."""
        async with self.lock:
            old = self.state.speaking
            self.state.speaking = speaking
            if old != speaking:
                logger.info(f"Speaking: {speaking}")
                await self._notify_change("speaking", speaking)

    async def set_processing(self, processing: bool) -> None:
        """Set processing state."""
        async with self.lock:
            old = self.state.processing
            self.state.processing = processing
            if old != processing:
                logger.info(f"Processing: {processing}")
                await self._notify_change("processing", processing)

    async def set_interrupted(self, interrupted: bool) -> None:
        """Set interrupted state."""
        async with self.lock:
            old = self.state.interrupted
            self.state.interrupted = interrupted
            if old != interrupted:
                logger.info(f"Interrupted: {interrupted}")
                await self._notify_change("interrupted", interrupted)

    async def set_wakeword_active(self, active: bool) -> None:
        """Set wakeword active state."""
        async with self.lock:
            old = self.state.wakeword_active
            self.state.wakeword_active = active
            if old != active:
                logger.info(f"Wakeword active: {active}")

    async def set_microphone_busy(self, busy: bool) -> None:
        """Set microphone busy state."""
        async with self.lock:
            old = self.state.microphone_busy
            self.state.microphone_busy = busy
            if old != busy:
                logger.debug(f"Microphone busy: {busy}")

    async def set_speaker_busy(self, busy: bool) -> None:
        """Set speaker busy state."""
        async with self.lock:
            old = self.state.speaker_busy
            self.state.speaker_busy = busy
            if old != busy:
                logger.debug(f"Speaker busy: {busy}")

    async def set_current_skill(self, skill: Optional[str]) -> None:
        """Set current executing skill."""
        async with self.lock:
            self.state.current_skill = skill
            logger.info(f"Current skill: {skill}")

    async def set_current_task(self, task: Optional[str]) -> None:
        """Set current task description."""
        async with self.lock:
            self.state.current_task = task

    async def record_utterance(self, text: str) -> None:
        """Record a user utterance."""
        async with self.lock:
            self.state.last_utterance = text
            self.state.utterances_processed += 1

    async def record_response(self, text: str) -> None:
        """Record an AI response."""
        async with self.lock:
            self.state.last_response = text

    async def record_error(self) -> None:
        """Record an error occurrence."""
        async with self.lock:
            self.state.errors_count += 1
            logger.warning(f"Error count: {self.state.errors_count}")

    async def can_acquire_microphone(self) -> bool:
        """Check if microphone can be acquired."""
        async with self.lock:
            return not self.state.microphone_busy and not self.state.speaker_busy

    async def can_acquire_speaker(self) -> bool:
        """Check if speaker can be acquired."""
        async with self.lock:
            return not self.state.speaker_busy and not self.state.microphone_busy

    async def get_state(self) -> Dict[str, Any]:
        """Get full state snapshot."""
        async with self.lock:
            return {
                "mode": self.state.mode.value,
                "running": self.state.is_running,
                "listening": self.state.listening,
                "speaking": self.state.speaking,
                "processing": self.state.processing,
                "interrupted": self.state.interrupted,
                "wakeword_active": self.state.wakeword_active,
                "microphone_busy": self.state.microphone_busy,
                "speaker_busy": self.state.speaker_busy,
                "current_skill": self.state.current_skill,
                "current_task": self.state.current_task,
                "last_utterance": self.state.last_utterance,
                "last_response": self.state.last_response,
                "utterances_processed": self.state.utterances_processed,
                "errors_count": self.state.errors_count,
            }

    async def reset(self) -> None:
        """Reset state to idle."""
        async with self.lock:
            self.state = AssistantState()
            logger.info("State reset to idle")

    def register_callback(self, callback) -> None:
        """Register a callback for state changes."""
        self.state_change_callbacks.append(callback)

    async def _notify_change(self, field: str, value: Any) -> None:
        """Notify callbacks of state change."""
        for callback in self.state_change_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(field, value)
                else:
                    callback(field, value)
            except Exception as e:
                logger.error(f"Callback error: {e}")


# Global singleton
_state_manager: Optional[AssistantStateManager] = None


async def get_state_manager() -> AssistantStateManager:
    """Get or create the global state manager."""
    global _state_manager
    if _state_manager is None:
        _state_manager = AssistantStateManager()
    return _state_manager
