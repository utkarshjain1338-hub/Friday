"""
Filesystem Tools
Tools for file and directory operations
"""

from ..tool_base import Tool, ToolSchema, ToolParameter, ParameterType
from automation.file_manager import (
    list_home,
    search_files,
    create_folder,
    move_file,
    delete_path
)
from pathlib import Path


class ListFilesTool(Tool):
    """List files in a directory"""
    
    def __init__(self):
        schema = ToolSchema(
            name="filesystem.list_files",
            description="List files and directories in a specified path",
            category="filesystem",
            parameters=[
                ToolParameter(
                    name="path",
                    type=ParameterType.STRING,
                    description="Path to list (defaults to home directory)",
                    required=False
                )
            ],
            returns="string"
        )
        super().__init__(schema)
    
    async def execute(self, **kwargs) -> str:
        """Execute the tool"""
        path = kwargs.get("path", "~")
        
        try:
            results = list_home(path)
            if not results:
                return f"Directory is empty: {path}"
            return "\n".join(results)
        except Exception as e:
            raise Exception(f"Failed to list files: {str(e)}")


class SearchFilesTool(Tool):
    """Search for files"""
    
    def __init__(self):
        schema = ToolSchema(
            name="filesystem.search_files",
            description="Search for files matching a pattern",
            category="filesystem",
            parameters=[
                ToolParameter(
                    name="pattern",
                    type=ParameterType.STRING,
                    description="Filename pattern to search for (e.g., '*.txt')",
                    required=True
                ),
                ToolParameter(
                    name="path",
                    type=ParameterType.STRING,
                    description="Path to search in (defaults to home directory)",
                    required=False
                )
            ],
            returns="string"
        )
        super().__init__(schema)
    
    async def execute(self, **kwargs) -> str:
        """Execute the tool"""
        pattern = kwargs.get("pattern")
        path = kwargs.get("path", "~")
        
        try:
            results = search_files(pattern, path)
            if not results:
                return f"No files found matching: {pattern}"
            return "\n".join(results)
        except Exception as e:
            raise Exception(f"Failed to search files: {str(e)}")


class CreateFolderTool(Tool):
    """Create a new folder"""
    
    def __init__(self):
        schema = ToolSchema(
            name="filesystem.create_folder",
            description="Create a new folder/directory",
            category="filesystem",
            parameters=[
                ToolParameter(
                    name="path",
                    type=ParameterType.STRING,
                    description="Path for the new folder",
                    required=True
                )
            ],
            returns="string"
        )
        super().__init__(schema)
    
    async def execute(self, **kwargs) -> str:
        """Execute the tool"""
        path = kwargs.get("path")
        
        try:
            create_folder(path)
            return f"Successfully created folder: {path}"
        except Exception as e:
            raise Exception(f"Failed to create folder: {str(e)}")


class MoveFileTool(Tool):
    """Move or rename a file"""
    
    def __init__(self):
        schema = ToolSchema(
            name="filesystem.move_file",
            description="Move or rename a file",
            category="filesystem",
            parameters=[
                ToolParameter(
                    name="source",
                    type=ParameterType.STRING,
                    description="Source file path",
                    required=True
                ),
                ToolParameter(
                    name="destination",
                    type=ParameterType.STRING,
                    description="Destination file path",
                    required=True
                )
            ],
            returns="string"
        )
        super().__init__(schema)
    
    async def execute(self, **kwargs) -> str:
        """Execute the tool"""
        source = kwargs.get("source")
        destination = kwargs.get("destination")
        
        try:
            move_file(source, destination)
            return f"Successfully moved {source} to {destination}"
        except Exception as e:
            raise Exception(f"Failed to move file: {str(e)}")


class DeletePathTool(Tool):
    """Delete a file or folder"""
    
    def __init__(self):
        schema = ToolSchema(
            name="filesystem.delete_path",
            description="Delete a file or folder (recursively for folders)",
            category="filesystem",
            parameters=[
                ToolParameter(
                    name="path",
                    type=ParameterType.STRING,
                    description="Path to delete",
                    required=True
                ),
                ToolParameter(
                    name="confirm",
                    type=ParameterType.BOOLEAN,
                    description="Require user confirmation before deletion",
                    required=False,
                    default=True
                )
            ],
            returns="string"
        )
        super().__init__(schema)
    
    async def execute(self, **kwargs) -> str:
        """Execute the tool"""
        path = kwargs.get("path")
        confirm = kwargs.get("confirm", True)
        
        try:
            delete_path(path)
            return f"Successfully deleted: {path}"
        except Exception as e:
            raise Exception(f"Failed to delete path: {str(e)}")
