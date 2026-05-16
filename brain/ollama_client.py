import asyncio
import os
import shutil
from typing import Optional
from .prompt_builder import build_prompt


class OllamaClient:
    def __init__(self, binary: Optional[str] = None, model: str = "qwen2.5:3b"):
        self.binary = binary or os.getenv("OLLAMA_BINARY") or shutil.which("ollama")
        self.model = model

    async def generate(self, prompt: str, history: list = None, memory: list = None) -> str:
        system_prompt = "You are Friday, a helpful Linux assistant. Respond concisely and safely."
        built = build_prompt(system_prompt, history or [], memory or [], prompt)

        if not self.binary:
            # fallback behavior
            resp = "Ollama not available; fallback response."
            try:
                from core.bus import bus
                from core.events import AI_RESPONSE_GENERATED

                await bus.emit(AI_RESPONSE_GENERATED, {"model": self.model, "response": resp})
            except Exception:
                pass
            return resp

        proc = await asyncio.create_subprocess_exec(
            self.binary,
            "run",
            self.model,
            built,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        collected = []
        if proc.stdout:
            try:
                while True:
                    line = await proc.stdout.readline()
                    if not line:
                        break
                    text = line.decode(errors="ignore").strip()
                    if text:
                        collected.append(text)
                        try:
                            from core.bus import bus
                            from core.events import AI_RESPONSE_GENERATED
                            await bus.emit(AI_RESPONSE_GENERATED, {"model": self.model, "chunk": text})
                        except Exception:
                            pass
            except Exception:
                pass

        await proc.wait()
        if not collected:
            return "Ollama did not return a response."
        return "\n".join(collected).strip()
