import asyncio
import os
from core.router import FridayRouter


def test_no_llm_routing():
    os.environ["NO_LLM_MODE"] = "true"
    router = FridayRouter()
    response = asyncio.run(router.route("show battery status"))
    assert "CPU usage" in response or "Memory usage" in response or "Battery" in response


def test_no_llm_memory_recording():
    os.environ["NO_LLM_MODE"] = "true"
    router = FridayRouter()
    response = asyncio.run(router.route("remember that my favorite color is blue"))
    assert "committed that to memory" in response.lower()
