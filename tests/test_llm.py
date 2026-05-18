import asyncio
from brain.llm import FridayLLM


def test_friday_llm_fallback():
    llm = FridayLLM()
    llm.client.binary = None
    response = asyncio.run(llm.ask("What can you do?"))
    assert "Friday can open apps" in response or "Friday here" in response
