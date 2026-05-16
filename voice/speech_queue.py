"""Queue for managing speech requests with cancellation support."""
import asyncio
from typing import Optional, List
from dataclasses import dataclass, field
from enum import Enum


class SpeechStatus(Enum):
    """Status of a speech request."""

    QUEUED = "queued"
    PLAYING = "playing"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class SpeechRequest:
    """A queued speech request."""

    text: str
    priority: int = 0  # Higher priority = earlier execution
    request_id: str = field(default_factory=lambda: str(id({})))
    status: SpeechStatus = field(default=SpeechStatus.QUEUED)
    cancel_token: Optional[asyncio.Event] = field(default_factory=asyncio.Event)

    def is_cancelled(self) -> bool:
        """Check if request has been cancelled."""
        return self.cancel_token.is_set() if self.cancel_token else False

    def cancel(self) -> None:
        """Cancel this request."""
        self.status = SpeechStatus.CANCELLED
        if self.cancel_token:
            self.cancel_token.set()


class SpeechQueue:
    """Queue for managing speech requests with priority and cancellation."""

    def __init__(self, max_queue_size: int = 50):
        """
        Initialize speech queue.

        Args:
            max_queue_size: Maximum number of queued requests
        """
        self.max_size = max_queue_size
        self.queue: List[SpeechRequest] = []
        self.current_request: Optional[SpeechRequest] = None
        self.lock = asyncio.Lock()

    async def enqueue(self, text: str, priority: int = 0) -> SpeechRequest:
        """
        Add speech request to queue.

        Args:
            text: Text to speak
            priority: Priority level (higher = earlier)

        Returns:
            SpeechRequest object
        """
        if len(self.queue) >= self.max_size:
            raise RuntimeError("Speech queue full")

        request = SpeechRequest(text=text, priority=priority)

        async with self.lock:
            self.queue.append(request)
            # Sort by priority (descending)
            self.queue.sort(key=lambda r: r.priority, reverse=True)

        return request

    async def get_next(self) -> Optional[SpeechRequest]:
        """Get next request from queue."""
        async with self.lock:
            if self.queue:
                request = self.queue.pop(0)
                self.current_request = request
                request.status = SpeechStatus.PLAYING
                return request
            return None

    async def cancel_request(self, request_id: str) -> bool:
        """
        Cancel a specific request.

        Args:
            request_id: ID of request to cancel

        Returns:
            True if cancelled, False if not found
        """
        async with self.lock:
            for req in self.queue:
                if req.request_id == request_id:
                    req.cancel()
                    return True
            if self.current_request and self.current_request.request_id == request_id:
                self.current_request.cancel()
                return True
        return False

    async def cancel_all(self) -> int:
        """Cancel all queued requests."""
        async with self.lock:
            count = len(self.queue)
            for req in self.queue:
                req.cancel()
            self.queue.clear()
            if self.current_request:
                self.current_request.cancel()
            return count

    async def mark_completed(self) -> None:
        """Mark current request as completed."""
        async with self.lock:
            if self.current_request:
                self.current_request.status = SpeechStatus.COMPLETED
                self.current_request = None

    async def mark_failed(self, error: str) -> None:
        """Mark current request as failed."""
        async with self.lock:
            if self.current_request:
                self.current_request.status = SpeechStatus.FAILED
                self.current_request = None

    async def size(self) -> int:
        """Get current queue size."""
        async with self.lock:
            return len(self.queue)

    async def is_empty(self) -> bool:
        """Check if queue is empty."""
        async with self.lock:
            return len(self.queue) == 0 and self.current_request is None

    async def get_queue_info(self) -> dict:
        """Get queue statistics."""
        async with self.lock:
            return {
                "queued": len(self.queue),
                "current": self.current_request is not None,
                "current_text": self.current_request.text if self.current_request else None,
            }
