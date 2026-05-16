from skills.base_skill import BaseSkill
import asyncio
from automation.linux_controller import open_application


class VSCodeSkill(BaseSkill):
    name = "vscode"
    commands = ["open code", "open vscode", "launch vscode", "start vscode"]

    async def execute(self, query: str, context: dict):
        # Use to_thread to call blocking launcher
        await asyncio.to_thread(open_application, "code")
        return "Opened VS Code."


skill = VSCodeSkill()
