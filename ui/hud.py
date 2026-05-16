"""Terminal HUD for real-time status and diagnostics display."""
import asyncio
from typing import Optional
from loguru import logger

try:
    from rich.live import Live
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.text import Text
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.table import Table
    from rich.console import Console
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


class TerminalHUD:
    """Terminal-based HUD for displaying assistant status."""

    def __init__(self, update_interval: float = 1.0):
        """
        Initialize Terminal HUD.

        Args:
            update_interval: How often to update display (seconds)
        """
        self.update_interval = update_interval
        self.is_running = False
        self.console = Console() if HAS_RICH else None
        self.last_state = {}

    async def start(self, state_manager, diagnostics) -> None:
        """
        Start the HUD display.

        Args:
            state_manager: AssistantStateManager instance
            diagnostics: DiagnosticsCollector instance
        """
        if not HAS_RICH:
            logger.warning("rich library not available, HUD disabled")
            return

        self.is_running = True
        logger.info("HUD started")

        try:
            with Live(self._create_layout(), refresh_per_second=1, console=self.console) as live:
                while self.is_running:
                    try:
                        # Get current state
                        state = await state_manager.get_state()
                        diag = await diagnostics.get_statistics()

                        # Update layout
                        layout = self._create_layout()
                        self._update_state_panel(layout, state)
                        self._update_metrics_panel(layout, diag)
                        self._update_logs_panel(layout)

                        live.update(layout)
                        await asyncio.sleep(self.update_interval)

                    except Exception as e:
                        logger.error(f"HUD update error: {e}")
                        await asyncio.sleep(0.5)

        except Exception as e:
            logger.error(f"HUD error: {e}")
        finally:
            self.is_running = False
            logger.info("HUD stopped")

    def stop(self) -> None:
        """Stop the HUD display."""
        self.is_running = False

    def _create_layout(self) -> Layout:
        """Create the HUD layout."""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3),
        )

        layout["body"].split_row(
            Layout(name="state", ratio=1),
            Layout(name="metrics", ratio=1),
        )

        layout["state"].split_column(
            Layout(name="status"),
            Layout(name="audio"),
        )

        layout["metrics"].split_column(
            Layout(name="performance"),
            Layout(name="errors"),
        )

        return layout

    def _update_state_panel(self, layout, state: dict) -> None:
        """Update state panel."""
        state_text = Text()
        state_text.append("FRIDAY ASSISTANT\n", style="bold green")
        state_text.append(f"Mode: {state.get('mode', 'unknown')}\n")
        state_text.append(f"Listening: {'✓' if state.get('listening') else '✗'}\n")
        state_text.append(f"Speaking: {'✓' if state.get('speaking') else '✗'}\n")
        state_text.append(f"Processing: {'✓' if state.get('processing') else '✗'}\n")
        state_text.append(f"Skill: {state.get('current_skill', 'None')}\n")

        layout["state"]["status"].update(Panel(state_text, title="Status"))

        # Audio panel
        audio_text = Text()
        audio_text.append("AUDIO STATUS\n", style="bold blue")
        audio_text.append(f"Mic: {'🔴 BUSY' if state.get('microphone_busy') else '🟢 FREE'}\n")
        audio_text.append(f"Speaker: {'🔴 BUSY' if state.get('speaker_busy') else '🟢 FREE'}\n")
        audio_text.append(f"Wakeword: {'✓ ACTIVE' if state.get('wakeword_active') else '✗ INACTIVE'}\n")

        layout["state"]["audio"].update(Panel(audio_text, title="Audio"))

    def _update_metrics_panel(self, layout, diag: dict) -> None:
        """Update metrics panel."""
        perf_text = Text()
        perf_text.append("PERFORMANCE\n", style="bold cyan")
        latency = diag.get("latency_stats", {})
        perf_text.append(f"Avg Latency: {latency.get('average', 0):.1f}ms\n")
        perf_text.append(f"Max Latency: {latency.get('max', 0):.1f}ms\n")
        uptime = diag.get("uptime_seconds", 0)
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)
        perf_text.append(f"Uptime: {hours}h {minutes}m\n")

        layout["metrics"]["performance"].update(Panel(perf_text, title="Metrics"))

        # Errors panel
        error_text = Text()
        error_text.append("ERRORS\n", style="bold red")
        error_count = diag.get("total_errors", 0)
        error_text.append(f"Total: {error_count}\n")
        recent_errors = diag.get("recent_errors", [])
        if recent_errors:
            error_text.append(f"Latest: {recent_errors[-1].get('type', 'Unknown')}\n")

        layout["metrics"]["errors"].update(Panel(error_text, title="Status"))

    def _update_logs_panel(self, layout) -> None:
        """Update logs panel."""
        log_text = Text()
        log_text.append("SYSTEM LOGS\n", style="bold yellow")
        log_text.append("Ready to assist...\n")

        layout["footer"].update(Panel(log_text, title="Activity"))

    async def display_message(self, message: str, level: str = "info") -> None:
        """Display a message in HUD."""
        if self.console:
            style = {"info": "blue", "warning": "yellow", "error": "red"}.get(level, "white")
            self.console.print(f"[{style}]{message}[/{style}]")


class SimpleDashboard:
    """Simple text-based dashboard without rich dependency."""

    def __init__(self):
        """Initialize simple dashboard."""
        self.is_running = False

    async def start(self, state_manager, diagnostics) -> None:
        """Start the dashboard."""
        self.is_running = True
        logger.info("Simple dashboard started")

        try:
            while self.is_running:
                # Clear screen
                import os

                os.system("clear" if os.name == "posix" else "cls")

                # Get state
                state = await state_manager.get_state()
                diag = await diagnostics.get_statistics()

                # Print status
                print("=" * 50)
                print("FRIDAY ASSISTANT")
                print("=" * 50)
                print(f"Mode: {state.get('mode')}")
                print(f"Listening: {state.get('listening')}")
                print(f"Speaking: {state.get('speaking')}")
                print(f"Processing: {state.get('processing')}")
                print(f"Current Skill: {state.get('current_skill')}")
                print()
                print("AUDIO STATUS")
                print("-" * 50)
                print(f"Microphone: {'BUSY' if state.get('microphone_busy') else 'FREE'}")
                print(f"Speaker: {'BUSY' if state.get('speaker_busy') else 'FREE'}")
                print(f"Wakeword: {'ACTIVE' if state.get('wakeword_active') else 'INACTIVE'}")
                print()
                print("METRICS")
                print("-" * 50)
                latency = diag.get("latency_stats", {})
                print(f"Avg Latency: {latency.get('average', 0):.1f}ms")
                print(f"Uptime: {diag.get('uptime_seconds', 0):.1f}s")
                print(f"Total Errors: {diag.get('total_errors', 0)}")
                print()

                await asyncio.sleep(1.0)

        except Exception as e:
            logger.error(f"Dashboard error: {e}")
        finally:
            self.is_running = False

    def stop(self) -> None:
        """Stop dashboard."""
        self.is_running = False
