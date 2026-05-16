"""Token pipeline for processing streaming AI responses."""
import asyncio
from typing import AsyncGenerator, Callable, Optional, List
from enum import Enum
from loguru import logger


class TokenType(Enum):
    """Type of token in pipeline."""

    WORD = "word"
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"
    COMPLETE = "complete"


class TokenPipeline:
    """Processes streaming tokens from LLM."""

    def __init__(self, sentence_threshold: int = 5):
        """
        Initialize token pipeline.

        Args:
            sentence_threshold: Number of tokens before emitting sentence
        """
        self.sentence_threshold = sentence_threshold
        self.token_buffer: List[str] = []
        self.is_processing = False
        self.filters: List[Callable] = []

    def add_filter(self, filter_func: Callable) -> None:
        """
        Add token filter.

        Args:
            filter_func: Function that takes token string and returns modified token or None to skip
        """
        self.filters.append(filter_func)

    async def process_tokens(
        self, token_source: AsyncGenerator, on_token: Optional[Callable] = None
    ) -> AsyncGenerator:
        """
        Process tokens from source.

        Args:
            token_source: Async generator yielding token strings
            on_token: Callback for each processed token

        Yields:
            Processed tokens
        """
        self.is_processing = True
        self.token_buffer.clear()

        try:
            async for token in token_source:
                if not token:
                    continue

                # Apply filters
                filtered_token = token
                for filter_func in self.filters:
                    if asyncio.iscoroutinefunction(filter_func):
                        filtered_token = await filter_func(filtered_token)
                    else:
                        filtered_token = filter_func(filtered_token)
                    if filtered_token is None:
                        continue

                if filtered_token:
                    self.token_buffer.append(filtered_token)

                    # Emit on threshold
                    if len(self.token_buffer) >= self.sentence_threshold:
                        combined = " ".join(self.token_buffer)
                        yield combined
                        if on_token:
                            if asyncio.iscoroutinefunction(on_token):
                                await on_token(combined)
                            else:
                                on_token(combined)
                        self.token_buffer.clear()

            # Flush remaining
            if self.token_buffer:
                combined = " ".join(self.token_buffer)
                yield combined
                if on_token:
                    if asyncio.iscoroutinefunction(on_token):
                        await on_token(combined)
                    else:
                        on_token(combined)

        finally:
            self.is_processing = False

    async def filter_safety(self, token: str) -> Optional[str]:
        """Filter potentially unsafe tokens."""
        # Basic filter: remove harmful patterns
        dangerous_keywords = ["rm -rf", "sudo", "password", "token"]
        for keyword in dangerous_keywords:
            if keyword.lower() in token.lower():
                logger.warning(f"Blocked token: {token}")
                return None
        return token

    def filter_whitespace(self, token: str) -> Optional[str]:
        """Filter excessive whitespace."""
        return token.strip() if token.strip() else None

    def get_buffer_size(self) -> int:
        """Get current buffer size."""
        return len(self.token_buffer)

    async def flush(self) -> Optional[str]:
        """Flush buffer and return remaining tokens."""
        if self.token_buffer:
            combined = " ".join(self.token_buffer)
            self.token_buffer.clear()
            return combined
        return None


class TokenAggregator:
    """Aggregates tokens into sentences/paragraphs."""

    def __init__(self):
        """Initialize aggregator."""
        self.buffer: List[str] = []
        self.sentence_buffer: List[str] = []

    async def aggregate_to_sentences(
        self, token_source: AsyncGenerator,
    ) -> AsyncGenerator:
        """
        Aggregate tokens into complete sentences.

        Args:
            token_source: Source of tokens

        Yields:
            Complete sentences
        """
        async for token in token_source:
            self.buffer.append(token)

            # Check for sentence-ending punctuation
            if any(token.endswith(p) for p in [".", "!", "?", "\n"]):
                if self.buffer:
                    sentence = " ".join(self.buffer).strip()
                    self.buffer.clear()
                    yield sentence

        # Flush remaining
        if self.buffer:
            sentence = " ".join(self.buffer).strip()
            self.buffer.clear()
            if sentence:
                yield sentence

    async def aggregate_to_paragraphs(
        self, token_source: AsyncGenerator,
    ) -> AsyncGenerator:
        """
        Aggregate tokens into paragraphs.

        Args:
            token_source: Source of tokens

        Yields:
            Paragraph strings
        """
        buffer: List[str] = []

        async for token in token_source:
            buffer.append(token)
            # Paragraph boundary on double newline or long buffer
            if token.endswith("\n\n") or len(buffer) > 20:
                if buffer:
                    paragraph = " ".join(buffer).strip()
                    buffer.clear()
                    yield paragraph

        if buffer:
            paragraph = " ".join(buffer).strip()
            if paragraph:
                yield paragraph
