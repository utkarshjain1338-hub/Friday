import os
import asyncio
from .ollama_client import OllamaClient


class FridayLLM:
    def __init__(self):
        self.system_prompt = (
            "You are Friday, a cute and stylish Linux assistant with a friendly female voice persona. "
            "Answer politely, help with Linux tasks, and avoid executing dangerous commands."
        )
        self.history = []
        self.model = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
        self.client = OllamaClient(model=self.model)

    async def ask(self, prompt: str) -> str:
        self.history.append({"role": "user", "content": prompt})
        if not self.client.binary:
            return self._fallback_response(prompt)

        try:
            return await self.client.generate(prompt, history=self.history)
        except Exception:
            return self._fallback_response(prompt)

    def _fallback_response(self, prompt: str) -> str:
        if "thank" in prompt.lower():
            return "You're welcome! If you want, I can also run commands or check system status."
        if "help" in prompt.lower() or "how" in prompt.lower() or "what" in prompt.lower():
            return (
                "Friday can open apps, check system stats, manage files, and perform safe automation. "
                "Try commands like 'open firefox', 'show battery status', or 'search file notes'."
            )
        return (
            "Friday here! I can help with Linux tasks and safe automation. "
            "Ask me to open an application, inspect system health, or find files."
        )
