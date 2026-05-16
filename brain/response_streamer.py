"""Streaming response pipeline for real-time AI responses."""
import asyncio
from typing import AsyncGenerator, Optional, List, Callable
from loguru import logger


class ResponseStreamer:
    """Streams AI responses token-by-token for real-time interaction."""

    def __init__(self, buffer_size: int = 5):
        """
        Initialize response streamer.

        Args:
            buffer_size: Number of tokens to buffer before yielding
        """
        self.buffer_size = buffer_size
        self.token_buffer: List[str] = []
        self.is_streaming = False
        self.total_tokens = 0

    async def stream_response(
        self, ollama_process, on_token: Optional[Callable] = None
    ) -> AsyncGenerator:
        """
        Stream response from Ollama process.

        Args:
            ollama_process: Async subprocess for Ollama
            on_token: Callback for each complete sentence/token group

        Yields:
            Streaming response tokens
        """
        self.is_streaming = True
        self.total_tokens = 0

        try:
            if ollama_process.stdout:
                async for line in self._read_stdout(ollama_process.stdout):
                    if line.strip():
                        self.token_buffer.append(line)
                        self.total_tokens += 1

                        # Yield buffered tokens when buffer is full or on sentence end
                        if (
                            len(self.token_buffer) >= self.buffer_size
                            or line.strip().endswith((".", "!", "?"))
                        ):
                            buffered_text = " ".join(self.token_buffer).strip()
                            if buffered_text:
                                yield buffered_text
                                if on_token:
                                    on_token(buffered_text)
                            self.token_buffer.clear()

                # Flush remaining tokens
                if self.token_buffer:
                    buffered_text = " ".join(self.token_buffer).strip()
                    if buffered_text:
                        yield buffered_text
                        if on_token:
                            on_token(buffered_text)
                    self.token_buffer.clear()

        except Exception as e:
            logger.error(f"Stream error: {e}")

        finally:
            self.is_streaming = False
            logger.info(f"Streaming complete: {self.total_tokens} tokens")

    async def _read_stdout(self, stdout):
        """
        Read from stdout asynchronously.

        Args:
            stdout: Async stream

        Yields:
            Lines from stream
        """
        try:
            while True:
                line = await stdout.readline()
                if not line:
                    break
                yield line.decode(errors="ignore").strip()
        except Exception as e:
            logger.error(f"Read error: {e}")

    def stop(self) -> None:
        """Stop streaming."""
        self.is_streaming = False

    def get_token_count(self) -> int:
        """Get total tokens streamed so far."""
        return self.total_tokens

    async def stream_with_timeout(
        self, ollama_process, timeout: float = 30.0
    ) -> AsyncGenerator:
        """
        Stream response with timeout.

        Args:
            ollama_process: Ollama subprocess
            timeout: Timeout in seconds

        Yields:
            Streaming tokens
        """
        try:
            async with asyncio.timeout(timeout):
                async for token in self.stream_response(ollama_process):
                    yield token
        except asyncio.TimeoutError:
            logger.warning(f"Stream timeout after {timeout}s")
