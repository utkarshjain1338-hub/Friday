"""
Tool Orchestrator
Handles tool selection and execution based on LLM decisions
"""

import json
from typing import Any, Dict, List, Optional, Tuple, Union
from loguru import logger
from .tool_registry import ToolRegistry
from .tool_base import Tool


class ToolCall:
    """Represents a tool call request"""
    
    def __init__(self, tool_name: str, parameters: Dict[str, Any]):
        self.tool_name = tool_name
        self.parameters = parameters
    
    def __repr__(self) -> str:
        return f"ToolCall({self.tool_name}, {self.parameters})"


class ToolExecutionResult:
    """Represents the result of a tool execution"""
    
    def __init__(
        self,
        tool_name: str,
        success: bool,
        result: Union[str, Dict[str, Any]],
        error: Optional[str] = None
    ):
        self.tool_name = tool_name
        self.success = success
        self.result = result
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "tool_name": self.tool_name,
            "success": self.success,
            "result": self.result,
            "error": self.error,
        }
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())
    
    def __repr__(self) -> str:
        if self.success:
            return f"ToolExecutionResult({self.tool_name}, success, {self.result})"
        else:
            return f"ToolExecutionResult({self.tool_name}, error, {self.error})"


class ToolOrchestrator:
    """Orchestrates tool selection and execution"""
    
    def __init__(self, registry: ToolRegistry):
        self.registry = registry
        self.call_history: List[ToolCall] = []
        self.execution_history: List[ToolExecutionResult] = []
    
    async def execute_tool(self, tool_call: ToolCall) -> ToolExecutionResult:
        """
        Execute a single tool call
        
        Args:
            tool_call: ToolCall object with tool_name and parameters
            
        Returns:
            ToolExecutionResult with success status and result/error
        """
        self.call_history.append(tool_call)
        
        # Get the tool
        tool = self.registry.get_tool(tool_call.tool_name)
        if not tool:
            error_msg = f"Tool '{tool_call.tool_name}' not found in registry"
            logger.error(error_msg)
            result = ToolExecutionResult(
                tool_call.tool_name,
                success=False,
                result=None,
                error=error_msg
            )
            self.execution_history.append(result)
            return result
        
        # Validate parameters
        is_valid, error_msg = tool.validate_parameters(tool_call.parameters)
        if not is_valid:
            logger.error(f"Invalid parameters for {tool_call.tool_name}: {error_msg}")
            result = ToolExecutionResult(
                tool_call.tool_name,
                success=False,
                result=None,
                error=error_msg
            )
            self.execution_history.append(result)
            return result
        
        # Execute the tool
        try:
            logger.info(f"Executing tool: {tool_call.tool_name} with params: {tool_call.parameters}")
            tool_result = await tool.execute(**tool_call.parameters)
            
            result = ToolExecutionResult(
                tool_call.tool_name,
                success=True,
                result=tool_result,
                error=None
            )
            logger.info(f"Tool execution succeeded: {tool_call.tool_name}")
            self.execution_history.append(result)
            return result
            
        except Exception as e:
            error_msg = f"Tool execution failed: {str(e)}"
            logger.exception(error_msg)
            result = ToolExecutionResult(
                tool_call.tool_name,
                success=False,
                result=None,
                error=error_msg
            )
            self.execution_history.append(result)
            return result
    
    async def execute_tool_sequence(self, tool_calls: List[ToolCall]) -> List[ToolExecutionResult]:
        """
        Execute multiple tool calls in sequence
        
        Args:
            tool_calls: List of ToolCall objects
            
        Returns:
            List of ToolExecutionResult objects
        """
        results = []
        for tool_call in tool_calls:
            result = await self.execute_tool(tool_call)
            results.append(result)
            
            # Stop on first failure (unless you want to continue)
            if not result.success:
                logger.warning(f"Stopping execution due to tool failure: {tool_call.tool_name}")
                break
        
        return results
    
    def parse_tool_calls_from_text(self, text: str) -> List[ToolCall]:
        """
        Parse tool calls from LLM response text
        
        Expected format:
        <tool_call>
        {
          "tool_name": "browser.open_url",
          "parameters": {
            "url": "https://example.com"
          }
        }
        </tool_call>
        
        Args:
            text: Text containing tool call markup
            
        Returns:
            List of ToolCall objects
        """
        tool_calls = []
        
        # Find all tool_call blocks
        import re
        pattern = r'<tool_call>\s*(.*?)\s*</tool_call>'
        matches = re.findall(pattern, text, re.DOTALL)
        
        for match in matches:
            try:
                data = json.loads(match)
                tool_call = ToolCall(
                    tool_name=data.get("tool_name"),
                    parameters=data.get("parameters", {})
                )
                tool_calls.append(tool_call)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse tool call JSON: {e}")
        
        return tool_calls
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """
        Get summary of execution history
        
        Returns:
            Dictionary with execution stats
        """
        total_calls = len(self.execution_history)
        successful = sum(1 for r in self.execution_history if r.success)
        failed = total_calls - successful
        
        by_tool = {}
        for result in self.execution_history:
            if result.tool_name not in by_tool:
                by_tool[result.tool_name] = {"success": 0, "failed": 0}
            if result.success:
                by_tool[result.tool_name]["success"] += 1
            else:
                by_tool[result.tool_name]["failed"] += 1
        
        return {
            "total_calls": total_calls,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / total_calls if total_calls > 0 else 0,
            "by_tool": by_tool,
        }
