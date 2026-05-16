from brain.llm import FridayLLM


def test_friday_llm_fallback():
    llm = FridayLLM()
    # Force fallback if no Ollama binary is available
    llm.client.binary = None
    response = llm.ask("What can you do?")
    assert "Friday can open apps" in response or "Friday here" in response
