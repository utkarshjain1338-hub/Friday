"""
Browser Tools
Tools for controlling and interacting with web browsers
"""

from ..tool_base import Tool, ToolSchema, ToolParameter, ParameterType
from automation.browser_controller import open_website, search_google, open_youtube


class OpenUrlTool(Tool):
    """Open a URL in the default browser"""
    
    def __init__(self):
        schema = ToolSchema(
            name="browser.open_url",
            description="Open a website URL in the default web browser",
            category="browser",
            parameters=[
                ToolParameter(
                    name="url",
                    type=ParameterType.STRING,
                    description="The complete URL to open (e.g., https://example.com)",
                    required=True
                )
            ],
            returns="string"
        )
        super().__init__(schema)
    
    async def execute(self, **kwargs) -> str:
        """Execute the tool"""
        url = kwargs.get("url")
        try:
            open_website(url)
            return f"Successfully opened {url} in browser"
        except Exception as e:
            raise Exception(f"Failed to open URL: {str(e)}")


class SearchGoogleTool(Tool):
    """Search Google with a query"""
    
    def __init__(self):
        schema = ToolSchema(
            name="browser.search_google",
            description="Search Google with the given query",
            category="browser",
            parameters=[
                ToolParameter(
                    name="query",
                    type=ParameterType.STRING,
                    description="The search query",
                    required=True
                )
            ],
            returns="string"
        )
        super().__init__(schema)
    
    async def execute(self, **kwargs) -> str:
        """Execute the tool"""
        query = kwargs.get("query")
        try:
            search_google(query)
            return f"Successfully searched Google for: {query}"
        except Exception as e:
            raise Exception(f"Failed to search Google: {str(e)}")


class OpenYoutubeTool(Tool):
    """Open YouTube with optional search"""
    
    def __init__(self):
        schema = ToolSchema(
            name="browser.open_youtube",
            description="Open YouTube, optionally with a search query",
            category="browser",
            parameters=[
                ToolParameter(
                    name="query",
                    type=ParameterType.STRING,
                    description="Optional search query for YouTube",
                    required=False
                )
            ],
            returns="string"
        )
        super().__init__(schema)
    
    async def execute(self, **kwargs) -> str:
        """Execute the tool"""
        query = kwargs.get("query")
        try:
            open_youtube(query)
            if query:
                return f"Successfully opened YouTube searching for: {query}"
            else:
                return "Successfully opened YouTube"
        except Exception as e:
            raise Exception(f"Failed to open YouTube: {str(e)}")
