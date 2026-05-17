"""
System State Activity Tracker
Provides real-time Wayland/Hyprland window and workspace state tracking.
"""

import json
import asyncio
import shutil
from typing import Dict, Any, Optional
from loguru import logger


class ActivityTracker:
    """
    Tracks Wayland system state using Hyprland's hyprctl utility.
    Allows Friday to know which application is currently focused and active.
    """

    def __init__(self):
        self.hyprctl_path = shutil.which("hyprctl")
        if not self.hyprctl_path:
            logger.warning("hyprctl command not found. Hyprland tracking will be unavailable.")

    async def get_active_window(self) -> Dict[str, Any]:
        """
        Runs `hyprctl activewindow -j` to fetch the currently active window state.

        Returns:
            A dictionary containing:
                - active_app (str): The class/name of the active window (e.g., 'kitty', 'firefox').
                - title (str): The window's title.
                - workspace_id (int): The current workspace ID.
                - workspace_name (str): The name of the workspace.
                - status (str): 'active' or 'unknown'.
        """
        fallback_state = {
            "active_app": "unknown",
            "title": "unknown",
            "workspace_id": 0,
            "workspace_name": "unknown",
            "status": "unavailable"
        }

        if not self.hyprctl_path:
            return fallback_state

        try:
            process = await asyncio.create_subprocess_exec(
                self.hyprctl_path, "activewindow", "-j",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.error(f"hyprctl activewindow failed: {stderr.decode().strip()}")
                return fallback_state

            output = stdout.decode().strip()
            if not output:
                # No window currently focused (e.g., desktop background is active)
                return {
                    "active_app": "desktop",
                    "title": "desktop",
                    "workspace_id": 1,
                    "workspace_name": "1",
                    "status": "active"
                }

            data = json.loads(output)
            return {
                "active_app": data.get("class", "unknown"),
                "title": data.get("title", "unknown"),
                "workspace_id": data.get("workspace", {}).get("id", 0),
                "workspace_name": data.get("workspace", {}).get("name", "unknown"),
                "status": "active"
            }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse hyprctl JSON: {e}")
            return fallback_state
        except Exception as e:
            logger.error(f"Error fetching active window: {e}")
            return fallback_state


if __name__ == "__main__":
    async def main():
        print("Initializing Hyprland Activity Tracker...")
        tracker = ActivityTracker()
        state = await tracker.get_active_window()
        print("\nCurrent System State:")
        print(json.dumps(state, indent=4))

    asyncio.run(main())
