"""Interrupt handler for managing speech interruption."""
import asyncio
from typing import Optional, Callable
from loguru import logger


class InterruptHandler:
    """Handles speech interruption with debouncing."""

    def __init__(self, debounce_ms: int = 100):
        """
        Initialize interrupt handler.

        Args:
            debounce_ms: Debounce duration in milliseconds
        """
        self.interrupt_event = asyncio.Event()
        self.debounce_ms = debounce_ms
        self.last_interrupt_time = 0.0
        self.on_interrupt: Optional[Callable] = None
        self.is_active = False

    def trigger_interrupt(self) -> bool:
        """
        Trigger an interrupt.

        Returns:
            True if interrupt was processed (not debounced)
        """
        import time

        current_time = time.time() * 1000  # Convert to milliseconds

        # Debounce check
        if current_time - self.last_interrupt_time < self.debounce_ms:
            logger.debug("Interrupt debounced")
            return False

        self.last_interrupt_time = current_time
        self.interrupt_event.set()
        logger.info("Interrupt triggered")

        # Call callback if registered
        if self.on_interrupt:
            try:
                self.on_interrupt()
            except Exception as e:
                logger.error(f"Interrupt callback error: {e}")

        return True

    def is_interrupted(self) -> bool:
        """Check if interrupted."""
        return self.interrupt_event.is_set()

    async def wait_for_interrupt(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for interrupt signal.

        Args:
            timeout: Timeout in seconds

        Returns:
            True if interrupted, False if timeout
        """
        try:
            await asyncio.wait_for(self.interrupt_event.wait(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False

    def clear(self) -> None:
        """Clear interrupt signal."""
        self.interrupt_event.clear()

    def reset(self) -> None:
        """Reset interrupt handler."""
        self.interrupt_event.clear()
        self.last_interrupt_time = 0.0

    def register_callback(self, callback: Callable) -> None:
        """
        Register callback to run on interrupt.

        Args:
            callback: Function to call on interrupt
        """
        self.on_interrupt = callback

    async def wait_with_interrupt(
        self, coro, timeout: Optional[float] = None
    ) -> tuple:
        """
        Wait for a coroutine or interrupt, whichever comes first.

        Args:
            coro: Coroutine to wait for
            timeout: Optional timeout

        Returns:
            Tuple of (completed, was_interrupted, result)
        """
        self.clear()
        self.is_active = True

        try:
            if timeout:
                done, pending = await asyncio.wait(
                    [coro, self.interrupt_event.wait()],
                    timeout=timeout,
                    return_when=asyncio.FIRST_COMPLETED,
                )
            else:
                done, pending = await asyncio.wait(
                    [coro, self.interrupt_event.wait()],
                    return_when=asyncio.FIRST_COMPLETED,
                )

            # Check which completed first
            interrupted = any(
                isinstance(task, asyncio.Task) and task._coro.__name__ == "wait"
                for task in done
            )

            result = None
            completed = False

            for task in done:
                if not isinstance(task._coro, type(self.interrupt_event.wait())):
                    try:
                        result = task.result()
                        completed = True
                    except Exception as e:
                        logger.error(f"Task error: {e}")

            # Cancel pending tasks
            for task in pending:
                task.cancel()

            return completed, interrupted, result

        finally:
            self.is_active = False
