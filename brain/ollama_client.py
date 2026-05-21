"""Ollama client using the HTTP REST API (localhost:11434).

The subprocess-based approach (ollama run model prompt) had to load the model
from scratch on every call and could not benefit from a running ollama daemon.
This client uses the /api/generate endpoint which reuses the already-loaded
model and is significantly faster.
"""
import asyncio
import json
import os
from typing import Optional
from loguru import logger

from .prompt_builder import build_prompt


OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_TIMEOUT = 60  # seconds — generous for first-token latency on CPU


class OllamaClient:
    def __init__(self, model: str = "qwen2.5:0.5b", host: str = OLLAMA_HOST):
        # Keep binary attr for backward compat (used as availability flag in llm.py)
        self.binary = "http"
        self.available = False
        self.model = model
        self.host = host.rstrip("/")

    async def is_available(self) -> bool:
        """Return whether the Ollama daemon is reachable."""
        if self.available:
            return True
        self.available = await self._is_available()
        if not self.available:
            self.binary = None
        return self.available

    async def _is_available(self) -> bool:
        """Check if the Ollama daemon is reachable."""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(
                    self.host.replace("http://", "").split(":")[0],
                    int(self.host.split(":")[-1]),
                ),
                timeout=2.0,
            )
            writer.close()
            await writer.wait_closed()
            return True
        except Exception:
            return False

    async def generate(
        self,
        prompt: str,
        history: list = None,
        memory: list = None,
        system: str = None,
    ) -> str:
        system_prompt = system or "You are Friday, a helpful Linux assistant. Respond concisely."
        built = build_prompt(system_prompt, history or [], memory or [], prompt)

        payload = json.dumps({
            "model": self.model,
            "prompt": built,
            "stream": True,
            "keep_alive": "10m",
            "options": {
                "temperature": 0.7,
                "num_predict": 512,
            },
        }).encode()

        try:
            # Use asyncio streams to make a raw HTTP POST (no external deps)
            host = self.host.replace("http://", "").replace("https://", "")
            host_name, _, port_str = host.partition(":")
            port = int(port_str) if port_str else 80

            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host_name, port),
                timeout=5.0,
            )

            request = (
                f"POST /api/generate HTTP/1.1\r\n"
                f"Host: {host_name}:{port}\r\n"
                f"Content-Type: application/json\r\n"
                f"Content-Length: {len(payload)}\r\n"
                f"Connection: close\r\n"
                f"\r\n"
            ).encode() + payload

            writer.write(request)
            await writer.drain()

            print("\033[90mThinking: ", end="", flush=True)

            # Read HTTP headers first
            while True:
                line = await asyncio.wait_for(reader.readline(), timeout=DEFAULT_TIMEOUT)
                if not line or line == b"\r\n":
                    break

            full_response = ""
            while True:
                line = await asyncio.wait_for(reader.readline(), timeout=DEFAULT_TIMEOUT)
                if not line:
                    break
                line_text = line.decode(errors="ignore").strip()
                
                # In HTTP chunked encoding, we get hex lengths then the data.
                # Since stream: True, Ollama sends one JSON object per chunk.
                if not line_text or not line_text.startswith("{"):
                    continue
                    
                try:
                    data = json.loads(line_text)
                    chunk = data.get("response", "")
                    if chunk:
                        full_response += chunk
                        print(chunk, end="", flush=True)
                    
                    if data.get("done"):
                        break
                except json.JSONDecodeError:
                    continue

            print("\033[0m")
            writer.close()
            await writer.wait_closed()

            response_text = full_response.strip()

            if not response_text:
                logger.warning("Ollama returned empty response.")
                return "I didn't get a response from the language model."

            try:
                from core.bus import bus
                from core.events import AI_RESPONSE_GENERATED
                await bus.emit(AI_RESPONSE_GENERATED, {"model": self.model, "response": response_text})
            except Exception:
                pass

            return response_text

        except asyncio.TimeoutError:
            print("\033[0m")
            logger.error(f"Ollama HTTP request timed out after {DEFAULT_TIMEOUT}s")
            return "The language model took too long to respond. Please try again."
        except Exception as exc:
            print("\033[0m")
            logger.error(f"Ollama HTTP error: {exc}")
            return f"Could not reach the language model: {exc}"

    @staticmethod
    def _decode_chunked(body: str) -> str:
        """Decode HTTP chunked transfer encoding."""
        result = []
        remaining = body
        while remaining:
            # Find the chunk size line
            nl = remaining.find("\r\n")
            if nl == -1:
                break
            size_str = remaining[:nl].strip()
            if not size_str:
                remaining = remaining[nl + 2:]
                continue
            try:
                chunk_size = int(size_str, 16)
            except ValueError:
                break
            if chunk_size == 0:
                break
            start = nl + 2
            chunk = remaining[start:start + chunk_size]
            result.append(chunk)
            remaining = remaining[start + chunk_size + 2:]  # skip trailing \r\n
        return "".join(result)
