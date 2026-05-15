from core.router import FridayRouter
from core.state_manager import StateManager
from memory.database import MemoryDatabase
from loguru import logger


class FridayAssistant:
    def __init__(self):
        self.router = FridayRouter()
        self.state = StateManager()
        self.memory = MemoryDatabase()
        logger.info("Friday assistant initialized.")

    def handle_text(self, text: str) -> str:
        text = text.strip()
        if not text:
            return "Please say or type a command."

        logger.info("Received command: {}", text)
        self.state.add_message(text)

        normalized = text.lower().strip()
        if normalized.startswith("remember "):
            note = text[len("remember "):].strip()
            self.memory.save("note", note)
            return f"Okay, I remembered: {note}"

        if "show memory" in normalized or "recall memory" in normalized or "what did i tell you" in normalized:
            entries = self.memory.get_recent(10)
            if not entries:
                return "I do not have any memories yet."
            return "\n".join(
                f"[{created_at}] {category}: {content}"
                for category, content, created_at in entries
            )

        response = self.router.route(text)
        self.memory.save("interaction", f"{text} -> {response}")
        logger.info("Response: {}", response)
        return response
