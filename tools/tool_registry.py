"""
Tool Registry System
Manages all available tools for Friday
"""

import json
from typing import Dict, List, Optional, Set
from .tool_base import Tool, ToolSchema
from loguru import logger


class ToolRegistry:
    """Registry for managing all available tools"""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._categories: Dict[str, List[str]] = {}

    def register(self, tool: Tool) -> None:
        """
        Register a tool in the registry
        
        Args:
            tool: Tool instance to register
        """
        tool_name = tool.name
        category = tool.category
        
        if tool_name in self._tools:
            logger.warning(f"Tool '{tool_name}' already registered, overwriting")
        
        self._tools[tool_name] = tool
        
        if category not in self._categories:
            self._categories[category] = []
        
        if tool_name not in self._categories[category]:
            self._categories[category].append(tool_name)
        
        logger.info(f"Registered tool: {tool_name} (category: {category})")

    def unregister(self, tool_name: str) -> bool:
        """
        Unregister a tool from the registry
        
        Args:
            tool_name: Name of tool to unregister
            
        Returns:
            True if tool was unregistered, False if not found
        """
        if tool_name not in self._tools:
            return False
        
        tool = self._tools[tool_name]
        del self._tools[tool_name]
        
        # Remove from categories
        if tool.category in self._categories:
            self._categories[tool.category].remove(tool_name)
            if not self._categories[tool.category]:
                del self._categories[tool.category]
        
        logger.info(f"Unregistered tool: {tool_name}")
        return True

    def get_tool(self, tool_name: str) -> Optional[Tool]:
        """
        Get a tool by name
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool instance or None if not found
        """
        return self._tools.get(tool_name)

    def get_by_category(self, category: str) -> List[Tool]:
        """
        Get all tools in a category
        
        Args:
            category: Category name
            
        Returns:
            List of tools in the category
        """
        tool_names = self._categories.get(category, [])
        return [self._tools[name] for name in tool_names if name in self._tools]

    def list_tools(self) -> List[Tool]:
        """
        Get all registered tools
        
        Returns:
            List of all tools
        """
        return list(self._tools.values())

    def list_categories(self) -> List[str]:
        """
        Get all available categories
        
        Returns:
            List of category names
        """
        return list(self._categories.keys())

    def get_schemas(self) -> List[Dict]:
        """
        Get all tool schemas (for LLM context)
        
        Returns:
            List of tool schemas as dictionaries
        """
        return [tool.schema.to_dict() for tool in self.list_tools()]

    def get_schemas_json(self) -> str:
        """
        Get all tool schemas as JSON
        
        Returns:
            JSON string of tool schemas
        """
        return json.dumps(self.get_schemas(), indent=2)

    def search_tools(self, query: str, category: Optional[str] = None) -> List[Tool]:
        """
        Search for tools matching a query
        
        Args:
            query: Search query (matches tool name and description)
            category: Optional category filter
            
        Returns:
            List of matching tools
        """
        query_lower = query.lower()
        results = []
        
        for tool in self.list_tools():
            # Filter by category if specified
            if category and tool.category != category:
                continue
            
            # Match name or description
            if query_lower in tool.name.lower() or query_lower in tool.schema.description.lower():
                results.append(tool)
        
        return results

    def get_category_count(self) -> Dict[str, int]:
        """
        Get count of tools per category
        
        Returns:
            Dictionary mapping category to tool count
        """
        return {cat: len(tools) for cat, tools in self._categories.items()}
