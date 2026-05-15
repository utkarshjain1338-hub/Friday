import shutil
import subprocess


class FridayLLM:
    def __init__(self):
        self.system_prompt = (
            "You are Friday, a cute and stylish Linux assistant with a friendly female voice persona. "
            "Answer politely, help with Linux tasks, and avoid executing dangerous commands."
        )
        self.history = []
        self.model = "qwen2.5:3b"
        self.ollama_binary = shutil.which("ollama")

    def ask(self, prompt: str) -> str:
        self.history.append({"role": "user", "content": prompt})
        if self.ollama_binary:
            return self._request_ollama(prompt)
        return self._fallback_response(prompt)

    def _request_ollama(self, prompt: str) -> str:
        try:
            result = subprocess.run(
                [self.ollama_binary, "run", self.model, prompt],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
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
