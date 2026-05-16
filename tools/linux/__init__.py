"""
Linux/System Tools
Tools for controlling system and applications
"""

from ..tool_base import Tool, ToolSchema, ToolParameter, ParameterType
from automation.linux_controller import (
    open_application,
    list_processes,
    kill_process,
    focus_window
)
from loguru import logger


class OpenApplicationTool(Tool):
    """Open an application"""
    
    def __init__(self):
        schema = ToolSchema(
            name="linux.open_application",
            description="Open an application by name (e.g., 'firefox', 'vscode', 'spotify')",
            category="linux",
            parameters=[
                ToolParameter(
                    name="application",
                    type=ParameterType.STRING,
                    description="Name of the application to open",
                    required=True
                ),
                ToolParameter(
                    name="args",
                    type=ParameterType.STRING,
                    description="Optional arguments to pass to the application",
                    required=False
                )
            ],
            returns="string"
        )
        super().__init__(schema)
    
    async def execute(self, **kwargs) -> str:
        """Execute the tool"""
        app = kwargs.get("application")
        args = kwargs.get("args", "")
        
        try:
            open_application(app, args)
            return f"Successfully opened {app}"
        except Exception as e:
            raise Exception(f"Failed to open {app}: {str(e)}")


class ListProcessesTool(Tool):
    """List running processes"""
    
    def __init__(self):
        schema = ToolSchema(
            name="linux.list_processes",
            description="List all running processes, optionally filtered by name",
            category="linux",
            parameters=[
                ToolParameter(
                    name="filter",
                    type=ParameterType.STRING,
                    description="Optional filter to match process names",
                    required=False
                )
            ],
            returns="string"
        )
        super().__init__(schema)
    
    async def execute(self, **kwargs) -> str:
        """Execute the tool"""
        filter_str = kwargs.get("filter")
        
        try:
            processes = list_processes(filter_str)
            if not processes:
                return "No processes found"
            return "\n".join(processes)
        except Exception as e:
            raise Exception(f"Failed to list processes: {str(e)}")


class KillProcessTool(Tool):
    """Kill a running process"""
    
    def __init__(self):
        schema = ToolSchema(
            name="linux.kill_process",
            description="Kill a running process by name or PID",
            category="linux",
            parameters=[
                ToolParameter(
                    name="target",
                    type=ParameterType.STRING,
                    description="Process name or PID to kill",
                    required=True
                ),
                ToolParameter(
                    name="force",
                    type=ParameterType.BOOLEAN,
                    description="Use SIGKILL instead of SIGTERM (force kill)",
                    required=False,
                    default=False
                )
            ],
            returns="string"
        )
        super().__init__(schema)
    
    async def execute(self, **kwargs) -> str:
        """Execute the tool"""
        target = kwargs.get("target")
        force = kwargs.get("force", False)
        
        try:
            kill_process(target, force=force)
            method = "force killed" if force else "terminated"
            return f"Successfully {method} {target}"
        except Exception as e:
            raise Exception(f"Failed to kill process: {str(e)}")


class FocusWindowTool(Tool):
    """Focus a specific application window"""
    
    def __init__(self):
        schema = ToolSchema(
            name="linux.focus_window",
            description="Bring an application window to focus",
            category="linux",
            parameters=[
                ToolParameter(
                    name="application",
                    type=ParameterType.STRING,
                    description="Name of the application window to focus",
                    required=True
                )
            ],
            returns="string"
        )
        super().__init__(schema)
    
    async def execute(self, **kwargs) -> str:
        """Execute the tool"""
        app = kwargs.get("application")
        
        try:
            focus_window(app)
            return f"Successfully focused {app} window"
        except Exception as e:
            raise Exception(f"Failed to focus window: {str(e)}")
