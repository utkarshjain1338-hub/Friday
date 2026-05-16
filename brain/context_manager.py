"""Context manager for AI response generation."""
import asyncio
from typing import List, Dict, Any, Optional
from loguru import logger


class ContextManager:
    """Manages context injection for AI responses."""

    def __init__(self, max_history: int = 10, max_memory_snippets: int = 5):
        """
        Initialize context manager.

        Args:
            max_history: Maximum conversation history to keep
            max_memory_snippets: Maximum memory snippets to inject
        """
        self.max_history = max_history
        self.max_memory_snippets = max_memory_snippets
        self.conversation_history: List[Dict[str, str]] = []
        self.memory_snippets: List[str] = []
        self.lock = asyncio.Lock()
        self.system_prompt = "You are Friday, a helpful Linux assistant. Respond concisely and safely."

    async def add_user_message(self, text: str) -> None:
        """Add user message to history."""
        async with self.lock:
            self.conversation_history.append({"role": "user", "content": text})
            # Keep only recent history
            if len(self.conversation_history) > self.max_history * 2:
                self.conversation_history = self.conversation_history[-(self.max_history * 2) :]

    async def add_assistant_message(self, text: str) -> None:
        """Add assistant message to history."""
        async with self.lock:
            self.conversation_history.append({"role": "assistant", "content": text})
            if len(self.conversation_history) > self.max_history * 2:
                self.conversation_history = self.conversation_history[-(self.max_history * 2) :]

    async def add_memory_snippet(self, snippet: str) -> None:
        """Add a memory snippet for context."""
        async with self.lock:
            self.memory_snippets.append(snippet)
            # Keep only recent snippets
            if len(self.memory_snippets) > self.max_memory_snippets:
                self.memory_snippets = self.memory_snippets[-self.max_memory_snippets :]

    async def set_memory_snippets(self, snippets: List[str]) -> None:
        """Set memory snippets (e.g., from retrieval)."""
        async with self.lock:
            self.memory_snippets = snippets[: self.max_memory_snippets]

    async def get_full_context(self) -> str:
        """
        Get full context string for prompt injection.

        Returns:
            Full context formatted for LLM
        """
        async with self.lock:
            parts = [self.system_prompt]

            # Add memory context
            if self.memory_snippets:
                parts.append("\n## Memory\n")
                for snippet in self.memory_snippets:
                    parts.append(f"- {snippet}")

            # Add conversation history
            if self.conversation_history:
                parts.append("\n## Conversation\n")
                for msg in self.conversation_history[-self.max_history :]:
                    role = msg["role"].upper()
                    parts.append(f"{role}: {msg['content']}")

            return "\n".join(parts)

    async def get_history(self) -> List[Dict[str, str]]:
        """Get conversation history."""
        async with self.lock:
            return self.conversation_history.copy()

    async def get_recent_history(self, count: int = 5) -> List[Dict[str, str]]:
        """Get recent N messages."""
        async with self.lock:
            return self.conversation_history[-count:]

    async def clear_history(self) -> None:
        """Clear conversation history."""
        async with self.lock:
            self.conversation_history.clear()

    async def clear_memory(self) -> None:
        """Clear memory snippets."""
        async with self.lock:
            self.memory_snippets.clear()

    async def clear_all(self) -> None:
        """Clear all context."""
        async with self.lock:
            self.conversation_history.clear()
            self.memory_snippets.clear()
            logger.info("Context cleared")

    async def get_statistics(self) -> Dict[str, Any]:
        """Get context statistics."""
        async with self.lock:
            return {
                "history_length": len(self.conversation_history),
                "memory_snippets": len(self.memory_snippets),
                "user_messages": sum(1 for m in self.conversation_history if m["role"] == "user"),
                "assistant_messages": sum(1 for m in self.conversation_history if m["role"] == "assistant"),
            }

    def set_system_prompt(self, prompt: str) -> None:
        """Update system prompt."""
        self.system_prompt = prompt
        logger.info("System prompt updated")


# Global singleton
_context_manager: Optional[ContextManager] = None


async def get_context_manager() -> ContextManager:
    """Get or create the global context manager."""
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextManager()
    return _context_manager
