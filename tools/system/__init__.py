"""
System Monitoring Tools
Tools for checking system status and health
"""

from ..tool_base import Tool, ToolSchema, ToolParameter, ParameterType
from automation.system_monitor import get_system_report


class GetSystemStatusTool(Tool):
    """Get current system status"""
    
    def __init__(self):
        schema = ToolSchema(
            name="system.get_status",
            description="Get current system status including CPU, memory, battery, and disk usage",
            category="system",
            parameters=[],
            returns="string"
        )
        super().__init__(schema)
    
    async def execute(self, **kwargs) -> str:
        """Execute the tool"""
        try:
            report = get_system_report()
            return str(report)
        except Exception as e:
            raise Exception(f"Failed to get system status: {str(e)}")


class GetBatterStatusTool(Tool):
    """Get battery status"""
    
    def __init__(self):
        schema = ToolSchema(
            name="system.get_battery",
            description="Get current battery level and charging status",
            category="system",
            parameters=[],
            returns="string"
        )
        super().__init__(schema)
    
    async def execute(self, **kwargs) -> str:
        """Execute the tool"""
        try:
            report = get_system_report()
            if "battery" in report:
                return report["battery"]
            return "Battery information not available"
        except Exception as e:
            raise Exception(f"Failed to get battery status: {str(e)}")


class GetDiskSpaceTool(Tool):
    """Get disk space usage"""
    
    def __init__(self):
        schema = ToolSchema(
            name="system.get_disk_space",
            description="Get disk space usage for specified or all partitions",
            category="system",
            parameters=[
                ToolParameter(
                    name="mount",
                    type=ParameterType.STRING,
                    description="Mount point to check (defaults to /home)",
                    required=False
                )
            ],
            returns="string"
        )
        super().__init__(schema)
    
    async def execute(self, **kwargs) -> str:
        """Execute the tool"""
        mount = kwargs.get("mount", "/home")
        
        try:
            report = get_system_report()
            if "disk" in report:
                return str(report["disk"])
            return f"Disk information for {mount} not available"
        except Exception as e:
            raise Exception(f"Failed to get disk space: {str(e)}")
