"""
Base Tool class and schemas for Friday tool system
"""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Union
from enum import Enum


class ParameterType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


@dataclass
class ToolParameter:
    """Represents a tool parameter"""
    name: str
    type: Union[str, ParameterType]
    description: str
    required: bool = False
    enum: Optional[List[str]] = None
    default: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary"""
        result = {
            "name": self.name,
            "type": str(self.type),
            "description": self.description,
            "required": self.required,
        }
        if self.enum:
            result["enum"] = self.enum
        if self.default is not None:
            result["default"] = self.default
        return result


@dataclass
class ToolSchema:
    """Represents tool metadata and schema"""
    name: str
    description: str
    category: str
    parameters: List[ToolParameter] = field(default_factory=list)
    returns: str = "void"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary"""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "parameters": [p.to_dict() for p in self.parameters],
            "returns": self.returns,
        }

    def to_json(self) -> str:
        """Convert schema to JSON string"""
        return json.dumps(self.to_dict())


class Tool(ABC):
    """Base class for all Friday tools"""

    def __init__(self, schema: ToolSchema):
        self.schema = schema

    @property
    def name(self) -> str:
        """Tool name"""
        return self.schema.name

    @property
    def category(self) -> str:
        """Tool category"""
        return self.schema.category

    @abstractmethod
    async def execute(self, **kwargs) -> Union[str, Dict[str, Any]]:
        """
        Execute the tool with given parameters
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            Result of tool execution (string or dict)
        """
        pass

    def validate_parameters(self, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate parameters against schema
        
        Args:
            params: Parameters to validate
            
        Returns:
            (is_valid, error_message)
        """
        # Check required parameters
        required_params = {p.name for p in self.schema.parameters if p.required}
        provided_params = set(params.keys())
        
        missing = required_params - provided_params
        if missing:
            return False, f"Missing required parameters: {', '.join(missing)}"
        
        # Check parameter types (basic validation)
        for param_schema in self.schema.parameters:
            if param_schema.name in params:
                param_value = params[param_schema.name]
                if not self._validate_param_type(param_value, param_schema.type):
                    return False, f"Invalid type for parameter '{param_schema.name}': expected {param_schema.type}"
        
        return True, None

    @staticmethod
    def _validate_param_type(value: Any, param_type: Union[str, ParameterType]) -> bool:
        """Basic type validation"""
        param_type_str = str(param_type)
        
        if param_type_str == "string":
            return isinstance(value, str)
        elif param_type_str == "integer":
            return isinstance(value, int) and not isinstance(value, bool)
        elif param_type_str == "boolean":
            return isinstance(value, bool)
        elif param_type_str == "array":
            return isinstance(value, (list, tuple))
        elif param_type_str == "object":
            return isinstance(value, dict)
        
        return True  # Unknown types pass by default
