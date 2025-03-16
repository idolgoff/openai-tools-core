"""Tool service for executing tools and processing tool calls.

This module provides a service for handling tool execution,
processing tool calls, and generating structured responses.
"""

import json
from typing import Dict, Any, List, Optional, Callable, Union

from ai_tools_core.logger import get_logger
from ai_tools_core.services.openai_message_service import get_openai_message_service

# Get logger for this module
logger = get_logger(__name__)


class ToolService:
    """Service for executing tools and processing tool calls."""

    def __init__(self):
        """Initialize the tool service."""
        self.openai_message_service = get_openai_message_service()
        logger.info("Tool service initialized")

    def execute_tool_call(
        self,
        conversation_id: str,
        tool_call_id: str,
        function_name: str,
        function_args: Dict[str, Any],
        tool_registry: Dict[str, Callable],
        tool_response_processor: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Execute a tool call and store the result in history.

        Args:
            conversation_id: ID of the conversation
            tool_call_id: ID of the tool call
            function_name: Name of the function to execute
            function_args: Arguments to pass to the function
            tool_registry: Dictionary mapping function names to callable functions

        Returns:
            Structured response containing the result or error
        """
        # Log the tool call
        logger.info(f"Executing tool: {function_name} with args: {function_args}, id: {tool_call_id}")

        # Store tool call in history
        self.openai_message_service.add_tool_call_message(conversation_id, function_name, function_args, tool_call_id)

        # Check if the tool exists in the registry
        if function_name in tool_registry:
            try:
                # Execute the tool
                result = tool_registry[function_name](**function_args)

                # Store tool result in history
                self.openai_message_service.add_tool_result_message(
                    conversation_id,
                    function_name,
                    function_args,
                    result,
                    tool_call_id,
                )

                # Generate structured response
                return self._generate_tool_response(
                    function_name, function_args, result, conversation_id, tool_response_processor
                )

            except Exception as e:
                # Log the error
                error_message = str(e)
                logger.error(f"Error executing tool {function_name}: {error_message}")

                # Store error in history
                self.openai_message_service.add_tool_error_message(
                    conversation_id,
                    function_name,
                    function_args,
                    error_message,
                    tool_call_id,
                )

                # Generate error response
                error_response = self._generate_tool_response(
                    function_name, function_args, None, conversation_id, tool_response_processor
                )
                error_response["error"] = error_message
                return error_response
        else:
            # Handle unknown tool
            error_message = f"Unknown tool: {function_name}"
            logger.error(error_message)

            # Store error in history
            self.openai_message_service.add_tool_error_message(
                conversation_id,
                function_name,
                function_args,
                error_message,
                tool_call_id,
            )

            # Generate error response
            error_response = self._generate_tool_response(
                function_name, function_args, None, conversation_id, tool_response_processor
            )
            error_response["error"] = error_message
            return error_response

    def _generate_tool_response(
        self,
        tool_name: str,
        args: Dict[str, Any],
        result: Optional[Union[str, Dict]],
        conversation_id: Optional[str] = None,
        tool_response_processor: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Generate a structured response for a tool execution.

        Args:
            tool_name: Name of the executed tool
            args: Tool arguments
            result: Tool execution result
            conversation_id: Optional conversation ID for context
            tool_response_processor: Optional callback for processing tool-specific responses

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

        # Use the tool response processor if provided
        if tool_response_processor:
            try:
                # Call the processor with all relevant information
                processor_response = tool_response_processor(tool_name, args, result, conversation_id)
                # If the processor returns a response, update our base response
                if processor_response:
                    response.update(processor_response)
            except Exception as e:
                logger.error(f"Error in tool response processor: {str(e)}")
                # Continue with the base response if the processor fails

        # Add additional context based on the tool name pattern
        # This is a simplified version of what was in the projects module
        if tool_name.endswith("_tool"):
            action = tool_name.replace("_tool", "")
            if "list" in action:
                response["context"] = {
                    "action": "list",
                    "entity": action.replace("list_", ""),
                    "empty": result is None or result == "",
                }
            elif "delete" in action:
                response["context"] = {
                    "action": "delete",
                    "entity": action.replace("delete_", ""),
                    "found": result is not None,
                }
            elif "create" in action:
                response["context"] = {
                    "action": "create",
                    "entity": action.replace("create_", ""),
                }
            elif "get" in action:
                response["context"] = {
                    "action": "get",
                    "entity": action.replace("get_", ""),
                    "found": result is not None,
                }

        return response

    def process_tool_calls(
        self,
        conversation_id: str,
        tool_calls: List[Any],
        tool_registry: Dict[str, Callable],
        response_generator: Optional[Callable] = None,
        tool_response_processor: Optional[Callable] = None,
    ) -> str:
        """
        Process multiple tool calls and generate a response.

        Args:
            conversation_id: ID of the conversation
            tool_calls: List of tool calls from OpenAI
            tool_registry: Dictionary mapping function names to callable functions
            response_generator: Optional function to generate a natural language response

        Returns:
            Combined response message
        """
        structured_responses = []

        # Process each tool call
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            tool_call_id = tool_call.id

            # Execute the tool and get structured response
            structured_response = self.execute_tool_call(
                conversation_id,
                tool_call_id,
                function_name,
                function_args,
                tool_registry,
                tool_response_processor,
            )

            structured_responses.append(structured_response)

        # Generate natural language response if we have structured responses
        responses = []
        if structured_responses and response_generator:
            # Add structured responses to history for the model to use
            self.openai_message_service.add_system_message_with_tool_responses(conversation_id, structured_responses)

            # Get updated conversation messages with token limiting
            # Use a slightly lower token limit (3500) to leave room for the response
            updated_messages = self.openai_message_service.get_conversation_messages(conversation_id, max_tokens=3500)

            # Generate a natural language response
            nl_content = response_generator(updated_messages)
            responses.append(nl_content)

        # Combine all responses
        combined_response = "\n\n".join(responses)

        # Store final response in history
        if combined_response:
            self.openai_message_service.add_assistant_message(conversation_id, combined_response)

        return combined_response or "I processed your request."


# Singleton instance
_tool_service: Optional[ToolService] = None


def get_tool_service() -> ToolService:
    """
    Get the singleton tool service instance.

    Returns:
        Tool service instance
    """
    global _tool_service

    if _tool_service is None:
        _tool_service = ToolService()

    return _tool_service
