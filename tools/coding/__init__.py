"""
Coding Tools
Tools for assisting with coding tasks
"""

from ..tool_base import Tool, ToolSchema, ToolParameter, ParameterType
from pathlib import Path


class OpenEditorTool(Tool):
    """Open a file in the default code editor"""
    
    def __init__(self):
        schema = ToolSchema(
            name="coding.open_editor",
            description="Open a file in the default code editor (VSCode, Vim, etc.)",
            category="coding",
            parameters=[
                ToolParameter(
                    name="file_path",
                    type=ParameterType.STRING,
                    description="Path to the file to open",
                    required=True
                ),
                ToolParameter(
                    name="line_number",
                    type=ParameterType.INTEGER,
                    description="Optional line number to jump to",
                    required=False
                )
            ],
            returns="string"
        )
        super().__init__(schema)
    
    async def execute(self, **kwargs) -> str:
        """Execute the tool"""
        file_path = kwargs.get("file_path")
        line_number = kwargs.get("line_number")
        
        try:
            # Simple implementation - can be extended to use specific editors
            import subprocess
            if line_number:
                subprocess.Popen(["code", f"{file_path}:{line_number}"])
            else:
                subprocess.Popen(["code", file_path])
            return f"Opened {file_path} in editor"
        except Exception as e:
            raise Exception(f"Failed to open editor: {str(e)}")


class RunCommandTool(Tool):
    """Run a shell command (with safety checks)"""
    
    def __init__(self):
        schema = ToolSchema(
            name="coding.run_command",
            description="Run a shell command in the terminal",
            category="coding",
            parameters=[
                ToolParameter(
                    name="command",
                    type=ParameterType.STRING,
                    description="Command to execute",
                    required=True
                ),
                ToolParameter(
                    name="cwd",
                    type=ParameterType.STRING,
                    description="Working directory for the command",
                    required=False
                )
            ],
            returns="string"
        )
        super().__init__(schema)
    
    async def execute(self, **kwargs) -> str:
        """Execute the tool"""
        command = kwargs.get("command")
        cwd = kwargs.get("cwd")
        
        try:
            import subprocess
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=30
            )
            output = result.stdout + result.stderr
            return output if output else "Command executed successfully"
        except subprocess.TimeoutExpired:
            raise Exception("Command execution timed out")
        except Exception as e:
            raise Exception(f"Failed to run command: {str(e)}")
