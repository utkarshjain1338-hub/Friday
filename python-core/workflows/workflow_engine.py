import asyncio
from typing import Any, Dict, List, Optional
from loguru import logger
from automation.linux_controller import open_application
from automation.browser_controller import open_website, open_youtube, search_google
from reflex.system_controls import SystemControls
from automation.file_manager import create_folder, list_home


class WorkflowEngine:
    """Executes reusable workflows and automation sequences."""

    def __init__(self):
        self.system_controls = SystemControls()
        self.workflows = self._load_default_workflows()

    def _load_default_workflows(self) -> Dict[str, Dict[str, Any]]:
        return {
            "coding_mode": {
                "description": "Open VS Code, a terminal, and prepare the workspace for focused coding.",
                "steps": [
                    {"action": "open_application", "args": ["code"]},
                    {"action": "open_application", "args": ["terminal"]},
                    {"action": "open_website", "args": ["https://www.google.com"], "note": "Optional browser restore"},
                ],
            },
            "focus_mode": {
                "description": "Start a focused state by lowering volume and opening the main workspace tools.",
                "steps": [
                    {"action": "adjust_volume_down", "args": []},
                    {"action": "open_application", "args": ["code"]},
                ],
            },
            "morning_setup": {
                "description": "Open daily apps and show system status for the start of the day.",
                "steps": [
                    {"action": "open_application", "args": ["terminal"]},
                    {"action": "open_website", "args": ["https://www.google.com"], "note": "Open a browser tab"},
                ],
            },
        }

    def list_workflows(self) -> List[str]:
        return list(self.workflows.keys())

    def get_workflow(self, name: str) -> Optional[Dict[str, Any]]:
        return self.workflows.get(name)

    async def execute_workflow(self, name: str) -> str:
        workflow = self.get_workflow(name)
        if not workflow:
            return f"I do not have a workflow named '{name}'."

        results = []
        for step in workflow["steps"]:
            action = step.get("action")
            args = list(step.get("args", []))
            note = step.get("note")
            result = await self._run_action(action, *args)
            results.append(result)
            if "could not" in result.lower() or "not found" in result.lower():
                logger.warning("Workflow '%s' failed on step %s: %s", name, action, result)
                return f"Workflow '{name}' stopped: {result}"

        summary = ", ".join(results)
        return f"Workflow '{name}' completed: {summary}"

    async def _run_action(self, action: str, *args: Any) -> str:
        if action == "open_application":
            return await asyncio.to_thread(open_application, *args)
        if action == "open_website":
            return await asyncio.to_thread(open_website, *args)
        if action == "open_youtube":
            return await asyncio.to_thread(open_youtube, *args)
        if action == "search_google":
            return await asyncio.to_thread(search_google, *args)
        if action == "adjust_volume_down":
            return await self.system_controls.volume_down()
        if action == "adjust_volume_up":
            return await self.system_controls.volume_up()
        if action == "create_folder":
            return await asyncio.to_thread(create_folder, *args)
        if action == "list_home":
            return await asyncio.to_thread(list_home)

        return f"Action '{action}' is not supported by the workflow engine."
