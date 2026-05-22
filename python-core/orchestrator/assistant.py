from core.router import FridayRouter
from core.state_manager import StateManager
from memory.database import MemoryDatabase
from personality import ResponseHumanizer
from loguru import logger
import asyncio


class FridayAssistant:
    def __init__(self):
        self.router = FridayRouter()
        self.state = StateManager()
        self.memory = MemoryDatabase()
        self.humanizer = ResponseHumanizer()
        logger.info("Friday assistant initialized.")

    async def handle_text(self, text: str) -> str:
        text = text.strip()
        if not text:
            return "Please say or type a command."

        logger.info("Received command: {}", text)
        self.state.add_message(text)



        # Route the command (router may be async)
        response = await self.router.route(text)
        await asyncio.to_thread(self.memory.save, "interaction", f"{text} -> {response}")
        logger.info("Response: {}", response)

        # Apply natural language humanization before returning
        try:
            humanized = self.humanizer.humanize_response(response)
        except Exception as exc:
            logger.warning("Humanization failed: %s", exc)
            humanized = response
        return humanized
