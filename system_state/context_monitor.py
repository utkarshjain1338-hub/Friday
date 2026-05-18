import asyncio
import shutil
import os
from loguru import logger
from system_state.activity_tracker import ActivityTracker


class ContextMonitor:
    """Collects system state and contextual signals for routing."""

    def __init__(self):
        self.activity_tracker = ActivityTracker()
        self.clipboard_tool = self._find_clipboard_tool()

    @staticmethod
    def _find_clipboard_tool() -> str:
        for tool in ["wl-paste", "xclip", "xsel"]:
            if shutil.which(tool):
                return tool
        return ""

    async def get_clipboard(self) -> str:
        if not self.clipboard_tool:
            return ""

        try:
            if self.clipboard_tool == "wl-paste":
                process = await asyncio.create_subprocess_exec(
                    self.clipboard_tool, "--no-newline",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
            else:
                process = await asyncio.create_subprocess_exec(
                    self.clipboard_tool, "-o",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                logger.debug("Clipboard tool failed: %s", stderr.decode().strip())
                return ""
            return stdout.decode(errors="ignore").strip()
        except Exception as exc:
            logger.warning("Clipboard capture failed: %s", exc)
            return ""

    async def get_context(self) -> dict:
        active_window = await self.activity_tracker.get_active_window()
        clipboard = await self.get_clipboard()
        return {
            "active_app": active_window.get("active_app", "unknown"),
            "window_title": active_window.get("title", "unknown"),
            "workspace_name": active_window.get("workspace_name", "unknown"),
            "clipboard": clipboard,
        }
