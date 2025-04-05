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
    It also generates OpenAI-compatible tool schemas for the registered tools and
    provides a default implementation for generating tool responses.

    The registry supports two types of decorators:
    1. @registry.register() - For registering tool functions
    2. @registry.context_handler() - For registering context handlers for tool responses
    """

    def __init__(self):
        """Initialize the tool registry."""
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._context_handlers: Dict[str, Callable] = {}

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

    def generate_tool_response(
        self, tool_name: str, args: Dict[str, Any], result: Optional[Any], conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a structured response for a tool execution.

        This method provides a default implementation for generating tool responses.
        Subclasses can override this method to provide custom response generation.

        Args:
            tool_name: Name of the executed tool
            args: Tool arguments
            result: Tool execution result
            conversation_id: Optional ID of the conversation

        Returns:
            Dictionary with structured response data
        """
        # Base response structure
        response = {
            "tool": tool_name,
            "status": "success" if result is not None else "error",
            "data": result,
            "args": args,
        }

        # Add additional context based on the tool if needed
        # This is a hook for subclasses to add custom context
        response["context"] = self._get_tool_context(tool_name, args, result)

        return response

    def context_handler(self, tool_name: str):
        """Decorator to register a function as a context handler for a specific tool.

        Context handlers are used to generate additional context for tool responses.
        They receive the tool arguments and result, and return a dictionary with
        additional context information.

        Args:
            tool_name: Name of the tool to handle context for

        Returns:
            Decorator function
        """

        def decorator(func: Callable[[Dict[str, Any], Any], Dict[str, Any]]) -> Callable:
            self._context_handlers[tool_name] = func
            logger.info(f"Registered context handler for tool: {tool_name}")
            return func

        return decorator

    def _get_tool_context(self, tool_name: str, args: Dict[str, Any], result: Optional[Any]) -> Dict[str, Any]:
        """Get additional context for a tool response.

        This method checks if a context handler is registered for the tool and calls it.
        If no handler is registered, it returns an empty dictionary.

        Args:
            tool_name: Name of the executed tool
            args: Tool arguments
            result: Tool execution result

        Returns:
            Dictionary with additional context
        """
        if tool_name in self._context_handlers:
            try:
                return self._context_handlers[tool_name](args, result) or {}
            except Exception as e:
                logger.error(f"Error in context handler for {tool_name}: {str(e)}")
        return {}


# Example usage of the ToolRegistry class:
#
# # Create a tool registry
# tool_registry = ToolRegistry()
#
# # Register tools
# @tool_registry.register()
# def create_project_tool(name: str, description: str) -> str:
#     """Create a new project.
#
#     Args:
#         name: Project name
#         description: Project description
#     """
#     project_id = "123"  # In a real implementation, this would be generated
#     return project_id
#
# @tool_registry.register()
# def list_projects_tool() -> Optional[str]:
#     """List all available projects."""
#     return "Project 1\nProject 2\nProject 3"
#
# # Register context handlers for tools
# @tool_registry.context_handler("create_project_tool")
# def create_project_context(args: Dict[str, Any], result: Any) -> Dict[str, Any]:
#     """Generate context for create_project_tool responses."""
#     return {
#         "action": "create",
#         "entity": "project",
#         "name": args.get("name"),
#         "description": args.get("description"),
#         "project_id": result,
#     }
#
# @tool_registry.context_handler("list_projects_tool")
# def list_projects_context(args: Dict[str, Any], result: Any) -> Dict[str, Any]:
#     """Generate context for list_projects_tool responses."""
#     return {
#         "action": "list",
#         "entity": "projects",
#         "empty": result is None or result == "",
#     }
#
# # Get all registered tools
# tools = tool_registry.get_all_tools()
#
# # Get OpenAI-compatible schemas
# schemas = tool_registry.get_tool_schemas()
#
# # Execute a tool
# result = tool_registry.execute_tool("create_project_tool", name="My Project", description="A test project")
#
# # Generate a response for the tool execution
# response = tool_registry.generate_tool_response(
#     "create_project_tool",
#     {"name": "My Project", "description": "A test project"},
#     result
# )
#
# # The response will include the context from the registered handler:
# # {
# #     "tool": "create_project_tool",
# #     "status": "success",
# #     "data": "123",
# #     "args": {"name": "My Project", "description": "A test project"},
# #     "context": {
# #         "action": "create",
# #         "entity": "project",
# #         "name": "My Project",
# #         "description": "A test project",
# #         "project_id": "123"
# #     }
# # }


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
