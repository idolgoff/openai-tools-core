"""AI tools registry implementation.

This module provides a flexible registry for AI tools that can be used with OpenAI's
function calling API. It separates the tool registration mechanism from the actual
tool implementations, making it easier to add new tools and reuse the registry in
other projects.

The ToolRegistry class is completely decoupled from any specific domain logic and can
be used as a standalone module in any project that needs to register and execute tools.
"""

from typing import Dict, List, Optional, Union, Callable, Any, TypeVar, get_type_hints
import inspect
import json
from functools import wraps

from ai_tools_core.logger import log_tool_execution, get_logger

# Get logger for this module
logger = get_logger(__name__)

# Type definitions
T = TypeVar("T")
ToolFunction = Callable[..., T]
ToolSchema = Dict[str, Any]


class ToolRegistry:
    """Registry for AI tools.

    This class provides methods for registering, retrieving, and executing tools.
    It also generates OpenAI-compatible tool schemas for the registered tools.
    """

    def __init__(self):
        """Initialize the tool registry."""
        self._tools: Dict[str, Dict[str, Any]] = {}

    def register(self, name: Optional[str] = None, description: Optional[str] = None):
        """Decorator to register a function as a tool.

        Args:
            name: Optional custom name for the tool. If not provided, uses the function name.
            description: Optional description for the tool. If not provided, uses the function docstring.

        Returns:
            Decorator function
        """

        def decorator(func: ToolFunction) -> ToolFunction:
            tool_name = name or func.__name__
            tool_description = description or inspect.getdoc(func) or "No description provided"

            # Get function signature for parameter info
            sig = inspect.signature(func)
            type_hints = get_type_hints(func)

            # Build parameters schema
            parameters = {"type": "object", "properties": {}, "required": []}

            for param_name, param in sig.parameters.items():
                # Skip self parameter for methods
                if param_name == "self":
                    continue

                param_type = type_hints.get(param_name, Any)
                param_default = None if param.default is inspect.Parameter.empty else param.default
                param_required = param.default is inspect.Parameter.empty

                # Convert Python types to JSON schema types
                if param_type == str:
                    param_schema = {"type": "string"}
                elif param_type == int:
                    param_schema = {"type": "integer"}
                elif param_type == float:
                    param_schema = {"type": "number"}
                elif param_type == bool:
                    param_schema = {"type": "boolean"}
                elif param_type == Dict or param_type == dict:
                    param_schema = {"type": "object"}
                elif param_type == List or param_type == list:
                    param_schema = {"type": "array"}
                else:
                    param_schema = {"type": "string"}

                # Add parameter description from docstring if available
                param_doc = self._extract_param_doc(func, param_name)
                if param_doc:
                    param_schema["description"] = param_doc

                parameters["properties"][param_name] = param_schema

                if param_required:
                    parameters["required"].append(param_name)

            # Create the tool definition
            tool_def = {
                "function": func,
                "schema": {
                    "type": "function",
                    "function": {"name": tool_name, "description": tool_description, "parameters": parameters},
                },
            }

            self._tools[tool_name] = tool_def
            logger.info(f"Registered tool: {tool_name}")

            @wraps(func)
            def wrapper(*args, **kwargs):
                # Execute the function
                result = func(*args, **kwargs)

                # Log the execution (but not in the function itself)
                log_tool_execution(tool_name, kwargs if not args else {**kwargs, "args": args}, result)

                return result

            return wrapper

        return decorator

    def _extract_param_doc(self, func: Callable, param_name: str) -> Optional[str]:
        """Extract parameter documentation from function docstring.

        Args:
            func: Function to extract documentation from
            param_name: Name of the parameter

        Returns:
            Parameter documentation or None if not found
        """
        docstring = inspect.getdoc(func)
        if not docstring:
            return None

        lines = docstring.split("\n")
        param_marker = f"{param_name}:"

        for i, line in enumerate(lines):
            if param_marker in line and i < len(lines) - 1:
                # Extract the description part
                desc_part = line.split(param_marker, 1)[1].strip()
                return desc_part

        return None

    def get_tool(self, name: str) -> Optional[Callable]:
        """Get a tool by name.

        Args:
            name: Name of the tool

        Returns:
            Tool function or None if not found
        """
        tool = self._tools.get(name)
        return tool["function"] if tool else None

    def get_all_tools(self) -> Dict[str, Callable]:
        """Get all registered tools.

        Returns:
            Dictionary mapping tool names to their functions
        """
        return {name: tool["function"] for name, tool in self._tools.items()}

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Get OpenAI-compatible schemas for all registered tools.

        Returns:
            List of tool schemas
        """
        return [tool["schema"] for tool in self._tools.values()]

    def execute_tool(self, name: str, **kwargs) -> Any:
        """Execute a tool by name with the given arguments.

        Args:
            name: Name of the tool to execute
            **kwargs: Arguments to pass to the tool

        Returns:
            Result of the tool execution

        Raises:
            ValueError: If the tool is not found
        """
        tool_func = self.get_tool(name)
        if not tool_func:
            raise ValueError(f"Tool '{name}' not found")

        return tool_func(**kwargs)


# Example usage of the ToolRegistry class:
#
# # Create a tool registry
# tool_registry = ToolRegistry()
#
# # Register a tool
# @tool_registry.register()
# def example_tool(param1: str, param2: int = 0) -> str:
#     """Example tool that demonstrates how to use the registry.
#
#     Args:
#         param1: First parameter description
#         param2: Second parameter description with default value
#
#     Returns:
#         Result of the tool execution
#     """
#     return f"Executed example_tool with {param1} and {param2}"
#
# # Get all registered tools
# tools = tool_registry.get_all_tools()
#
# # Get OpenAI-compatible schemas
# schemas = tool_registry.get_tool_schemas()
#
# # Execute a tool
# result = tool_registry.execute_tool("example_tool", param1="test", param2=42)


# The following functions can be used as convenience functions when a global registry is created
# For example:
#
# tool_registry = ToolRegistry()
#
# def get_tool_schemas() -> List[Dict[str, Any]]:
#     """Get OpenAI-compatible schemas for all registered tools.
#
#     Returns:
#         List of tool schemas for use with OpenAI API
#     """
#     return tool_registry.get_tool_schemas()
#
#
# def execute_tool(name: str, **kwargs) -> Any:
#     """Execute a tool by name with the given arguments.
#
#     This is a convenience function that delegates to the tool registry.
#
#     Args:
#         name: Name of the tool to execute
#         **kwargs: Arguments to pass to the tool
#
#     Returns:
#         Result of the tool execution
#     """
#     return tool_registry.execute_tool(name, **kwargs)
