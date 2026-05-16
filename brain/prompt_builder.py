from typing import List


def build_prompt(system_prompt: str, history: List[str], memory_snippets: List[str], user_prompt: str) -> str:
    parts = [system_prompt]
    if memory_snippets:
        parts.append("\n-- Memory --\n" + "\n".join(memory_snippets))
    if history:
        parts.append("\n-- Recent --\n" + "\n".join(history[-10:]))
    parts.append("\n-- User --\n" + user_prompt)
    return "\n\n".join(parts)
