from typing import List


def build_prompt(system_prompt: str, history: List[str], memory_snippets: List[str], user_prompt: str) -> str:
    parts = [system_prompt]
    if memory_snippets:
        parts.append("\n-- Memory --\n" + "\n".join(memory_snippets))
    if history:
        # history may be list of strings or list of dicts {"role": "...", "content": "..."}
        formatted_history = []
        for h in history[-10:]:
            if isinstance(h, dict):
                formatted_history.append(f"{h.get('role', 'user')}: {h.get('content', '')}")
            else:
                formatted_history.append(str(h))
        parts.append("\n-- Recent --\n" + "\n".join(formatted_history))
    parts.append("\n-- User --\n" + user_prompt)
    return "\n\n".join(parts)
