"""
Reflex System Controls
Provides direct Wayland-native desktop controls (0ms delay) using shell commands.
Does not involve the LLM, enabling instantaneous reflexes.
"""

import asyncio
import shutil
from typing import Dict, Any, Tuple
from loguru import logger


class SystemControls:
    """
    Executes raw desktop operations instantly via Wayland tools (wpctl, playerctl, hyprctl).
    """

    def __init__(self):
        self.wpctl_path = shutil.which("wpctl")
        self.playerctl_path = shutil.which("playerctl")
        self.hyprctl_path = shutil.which("hyprctl")
        self.swaylock_path = shutil.which("swaylock") or shutil.which("hyprlock")
        self.brightnessctl_path = shutil.which("brightnessctl")
        self.systemctl_path = shutil.which("systemctl")

    async def _run_command(self, cmd: list) -> Tuple[bool, str]:
        """Helper to run system commands asynchronously."""
        if not cmd[0]:
            return False, f"Command tool '{cmd[0]}' not installed"
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            if process.returncode == 0:
                return True, stdout.decode().strip()
            return False, stderr.decode().strip()
        except Exception as e:
            logger.error(f"Error running command {' '.join(cmd)}: {e}")
            return False, str(e)

    # --- Volume Control (wpctl) ---
    async def toggle_mute(self) -> str:
        """Toggle system mute."""
        if not self.wpctl_path:
            return "Volume control is unavailable because wpctl is not installed."
        success, err = await self._run_command([self.wpctl_path, "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"])
        return "Audio toggled." if success else f"Failed to toggle audio: {err}"

    async def mute(self) -> str:
        """Mute system."""
        if not self.wpctl_path:
            return "Volume control is unavailable because wpctl is not installed."
        success, err = await self._run_command([self.wpctl_path, "set-mute", "@DEFAULT_AUDIO_SINK@", "1"])
        return "Audio muted." if success else f"Failed to mute audio: {err}"

    async def unmute(self) -> str:
        """Unmute system."""
        if not self.wpctl_path:
            return "Volume control is unavailable because wpctl is not installed."
        success, err = await self._run_command([self.wpctl_path, "set-mute", "@DEFAULT_AUDIO_SINK@", "0"])
        return "Audio unmuted." if success else f"Failed to unmute audio: {err}"

    async def volume_up(self) -> str:
        """Increase volume by 5%."""
        if not self.wpctl_path:
            return "Volume control is unavailable."
        success, err = await self._run_command([self.wpctl_path, "set-volume", "-l", "1.5", "@DEFAULT_AUDIO_SINK@", "5%+"])
        return "Volume increased." if success else f"Failed to raise volume: {err}"

    async def volume_down(self) -> str:
        """Decrease volume by 5%."""
        if not self.wpctl_path:
            return "Volume control is unavailable."
        success, err = await self._run_command([self.wpctl_path, "set-volume", "@DEFAULT_AUDIO_SINK@", "5%-"])
        return "Volume decreased." if success else f"Failed to lower volume: {err}"

    # --- Media Control (playerctl) ---
    async def media_play_pause(self) -> str:
        """Play or pause active media player."""
        if not self.playerctl_path:
            return "Media control is unavailable because playerctl is not installed."
        success, err = await self._run_command([self.playerctl_path, "play-pause"])
        return "Playback toggled." if success else f"Failed to control media: {err}"

    async def media_next(self) -> str:
        """Skip to next media track."""
        if not self.playerctl_path:
            return "Media control is unavailable."
        success, err = await self._run_command([self.playerctl_path, "next"])
        return "Playing next track." if success else f"Failed to skip track: {err}"

    async def media_previous(self) -> str:
        """Play previous media track."""
        if not self.playerctl_path:
            return "Media control is unavailable."
        success, err = await self._run_command([self.playerctl_path, "previous"])
        return "Playing previous track." if success else f"Failed to go back: {err}"

    # --- Window Management (hyprctl) ---
    async def close_active_window(self) -> str:
        """Close the currently focused window."""
        if not self.hyprctl_path:
            return "Window control is unavailable because hyprctl is not installed."
        success, err = await self._run_command([self.hyprctl_path, "dispatch", "killactive"])
        return "Window closed." if success else f"Failed to close window: {err}"

    async def switch_workspace(self, workspace: str) -> str:
        """Switch to another workspace."""
        if not self.hyprctl_path:
            return "Workspace control is unavailable."
        success, err = await self._run_command([self.hyprctl_path, "dispatch", "workspace", str(workspace)])
        return f"Switched to workspace {workspace}." if success else f"Failed to switch workspace: {err}"

    async def next_workspace(self) -> str:
        """Switch to next workspace."""
        if not self.hyprctl_path:
            return "Workspace control is unavailable."
        success, err = await self._run_command([self.hyprctl_path, "dispatch", "workspace", "+1"])
        return "Switched to next workspace." if success else f"Failed to switch workspace: {err}"

    async def prev_workspace(self) -> str:
        """Switch to previous workspace."""
        if not self.hyprctl_path:
            return "Workspace control is unavailable."
        success, err = await self._run_command([self.hyprctl_path, "dispatch", "workspace", "-1"])
        return "Switched to previous workspace." if success else f"Failed to switch workspace: {err}"

    # --- System Controls ---
    async def lock_screen(self) -> str:
        """Lock the screen."""
        if not self.swaylock_path:
            return "Screen locker (swaylock or hyprlock) is not installed."
        # Run lock screen detached
        try:
            await asyncio.create_subprocess_exec(self.swaylock_path)
            return "Screen locked."
        except Exception as e:
            return f"Failed to lock screen: {e}"

    async def toggle_fullscreen(self) -> str:
        """Toggle fullscreen mode on focused window."""
        if not self.hyprctl_path:
            return "Window control is unavailable."
        success, err = await self._run_command([self.hyprctl_path, "dispatch", "fullscreen", "0"])
        return "Fullscreen mode toggled." if success else f"Failed to toggle fullscreen: {err}"

    async def toggle_floating(self) -> str:
        """Toggle floating mode on focused window."""
        if not self.hyprctl_path:
            return "Window control is unavailable."
        success, err = await self._run_command([self.hyprctl_path, "dispatch", "togglefloating"])
        return "Floating mode toggled." if success else f"Failed to toggle floating: {err}"

    async def toggle_mic_mute(self) -> str:
        """Toggle microphone mute."""
        if not self.wpctl_path:
            return "Microphone control is unavailable."
        success, err = await self._run_command([self.wpctl_path, "set-mute", "@DEFAULT_AUDIO_SOURCE@", "toggle"])
        return "Microphone toggled." if success else f"Failed to toggle microphone: {err}"

    async def brightness_up(self) -> str:
        """Increase screen brightness by 5%."""
        if not self.brightnessctl_path:
            return "Brightness control is unavailable because brightnessctl is not installed."
        success, err = await self._run_command([self.brightnessctl_path, "set", "5%+"])
        return "Brightness increased." if success else f"Failed to adjust brightness: {err}"

    async def brightness_down(self) -> str:
        """Decrease screen brightness by 5%."""
        if not self.brightnessctl_path:
            return "Brightness control is unavailable."
        success, err = await self._run_command([self.brightnessctl_path, "set", "5%-"])
        return "Brightness decreased." if success else f"Failed to adjust brightness: {err}"

    async def system_suspend(self) -> str:
        """Put system to sleep/suspend."""
        if not self.systemctl_path:
            return "Power control is unavailable because systemctl is not installed."
        success, err = await self._run_command([self.systemctl_path, "suspend"])
        return "Putting system to sleep..." if success else f"Failed to suspend system: {err}"

    async def system_reboot(self) -> str:
        """Reboot the system."""
        if not self.systemctl_path:
            return "Power control is unavailable."
        success, err = await self._run_command([self.systemctl_path, "reboot"])
        return "Rebooting system..." if success else f"Failed to reboot system: {err}"

    async def system_shutdown(self) -> str:
        """Shutdown the system."""
        if not self.systemctl_path:
            return "Power control is unavailable."
        success, err = await self._run_command([self.systemctl_path, "poweroff"])
        return "Shutting down system..." if success else f"Failed to shutdown system: {err}"


if __name__ == "__main__":
    async def main():
        print("Testing Reflex Controls...")
        ctrl = SystemControls()
        res = await ctrl.toggle_mute()
        print(f"Mute Toggle Result: {res}")

    asyncio.run(main())
