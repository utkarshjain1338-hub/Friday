"""
brain/llm.py
Thin wrapper around Ollama (local LLM) for Friday.

When Ollama is not installed / not running the class falls back gracefully
so that the rest of the system keeps working in procedural mode.
"""

import asyncio
from typing import Any, Dict, List, Optional
from loguru import logger


class FridayLLM:
    """
    Async interface to a local Ollama instance.

    Usage:
        llm = FridayLLM()
        response = await llm.ask("What time is it?")
    """

    DEFAULT_MODEL = "mistral"
    DEFAULT_HOST  = "http://localhost:11434"

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        host:  str = DEFAULT_HOST,
        timeout: float = 30.0,
    ):
        self.model   = model
        self.host    = host
        self.timeout = timeout
        self._available: Optional[bool] = None  # lazily determined

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _check_available(self) -> bool:
        """Return True if Ollama is reachable."""
        if self._available is not None:
            return self._available
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.host}/api/tags", timeout=aiohttp.ClientTimeout(total=3)
                ) as resp:
                    self._available = resp.status == 200
        except Exception:
            self._available = False
        if not self._available:
            logger.warning(
                "Ollama not reachable at %s — LLM features disabled. "
                "Install Ollama and run `ollama serve` to enable them.",
                self.host,
            )
        return self._available

    async def _post(self, endpoint: str, payload: Dict[str, Any]) -> str:
        """POST to Ollama API and return the full response text."""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.host}{endpoint}",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as resp:
                    data = await resp.json()
                    return data.get("response", "").strip()
        except Exception as exc:
            logger.error("LLM request failed: %s", exc)
            return ""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def ask(self, prompt: str) -> str:
        """
        Send a single prompt and return the assistant reply.
        Returns a polite fallback string if Ollama is unavailable.
        """
        if not await self._check_available():
            return (
                "I'm running in offline procedural mode — "
                "no LLM is connected right now. "
                "Install Ollama and run `ollama serve` to unlock AI responses."
            )
        return await self._post(
            "/api/generate",
            {"model": self.model, "prompt": prompt, "stream": False},
        )

    async def ask_with_tool_context(
        self,
        original_prompt: str,
        tool_results: List[Dict[str, Any]],
    ) -> str:
        """
        Ask the LLM to summarise tool execution results into a natural reply.
        """
        if not await self._check_available():
            # Build a plain-text summary from tool results without the LLM
            parts = []
            for r in tool_results:
                if r.get("success"):
                    parts.append(str(r.get("result", "")))
            return " ".join(parts) if parts else "Done."

        results_text = "\n".join(
            f"- {r['tool_name']}: {'OK — ' + str(r['result']) if r['success'] else 'FAILED — ' + str(r['error'])}"
            for r in tool_results
        )
        composed = (
            f"The user asked: {original_prompt}\n\n"
            f"Tool execution results:\n{results_text}\n\n"
            "Summarise the outcome in one or two natural sentences."
        )
        return await self._post(
            "/api/generate",
            {"model": self.model, "prompt": composed, "stream": False},
        )
