"""
Tool Loader
Discovers and loads all available tools
"""

from .tool_registry import ToolRegistry
from .tool_orchestrator import ToolOrchestrator
from loguru import logger


def load_all_tools(registry: ToolRegistry) -> int:
    """
    Load all available tools into the registry
    
    Args:
        registry: ToolRegistry instance
        
    Returns:
        Number of tools loaded
    """
    from .browser import OpenUrlTool, SearchGoogleTool, OpenYoutubeTool
    from .linux import (
        OpenApplicationTool,
        ListProcessesTool,
        KillProcessTool,
        FocusWindowTool
    )
    from .filesystem import (
        ListFilesTool,
        SearchFilesTool,
        CreateFolderTool,
        MoveFileTool,
        DeletePathTool
    )
    from .media import PlayMusicTool, AdjustVolumeTool, PausePlayTool
    from .system import GetSystemStatusTool, GetBatterStatusTool, GetDiskSpaceTool
    from .coding import OpenEditorTool, RunCommandTool
    
    tools = [
        # Browser tools
        OpenUrlTool(),
        SearchGoogleTool(),
        OpenYoutubeTool(),
        
        # Linux tools
        OpenApplicationTool(),
        ListProcessesTool(),
        KillProcessTool(),
        FocusWindowTool(),
        
        # Filesystem tools
        ListFilesTool(),
        SearchFilesTool(),
        CreateFolderTool(),
        MoveFileTool(),
        DeletePathTool(),
        
        # Media tools
        PlayMusicTool(),
        AdjustVolumeTool(),
        PausePlayTool(),
        
        # System tools
        GetSystemStatusTool(),
        GetBatterStatusTool(),
        GetDiskSpaceTool(),
        
        # Coding tools
        OpenEditorTool(),
        RunCommandTool(),
    ]
    
    for tool in tools:
        registry.register(tool)
    
    logger.info(f"Loaded {len(tools)} tools into registry")
    return len(tools)


def create_tool_system() -> tuple[ToolRegistry, ToolOrchestrator]:
    """
    Create and initialize the complete tool system
    
    Returns:
        (ToolRegistry, ToolOrchestrator) tuple
    """
    registry = ToolRegistry()
    load_all_tools(registry)
    orchestrator = ToolOrchestrator(registry)
    return registry, orchestrator
