"""OpenAI message service for processing messages and tool calls.

This module provides a service for handling OpenAI-specific conversation messages,
tool calls, and interactions with the history manager.
"""

import json
from typing import Dict, Any, Optional, List, Union

from core.logger import get_logger
from core.history.manager import get_history_manager
from core.history.models import MessageRole
from core.services.openai_service import get_openai_service

# Get logger for this module
logger = get_logger(__name__)


class OpenAIMessageService:
    """Service for processing OpenAI-specific messages and tool calls."""

    def __init__(self):
        """Initialize the message service."""
        self.history_manager = get_history_manager()
        self.openai_service = get_openai_service()
        logger.info("OpenAI message service initialized")

    def create_or_get_conversation(
        self, user_id: str, conversation_id: Optional[str] = None
    ) -> str:
        """
        Create a new conversation or get an existing one.

        Args:
            user_id: ID of the user
            conversation_id: Optional ID of an existing conversation

        Returns:
            Conversation ID
        """
        if not conversation_id:
            conversation_id = self.history_manager.create_conversation(user_id)
            # Add system message to set the context
            self.history_manager.add_message(
                conversation_id,
                MessageRole.SYSTEM,
                "You are an AI assistant that helps users manage projects. "
                "Your task is to understand the user's intent and call the appropriate "
                "function to handle their request.",
            )

        return conversation_id

    def add_user_message(self, conversation_id: str, message: str) -> None:
        """
        Add a user message to the conversation history.

        Args:
            conversation_id: ID of the conversation
            message: User message text
        """
        self.history_manager.add_message(conversation_id, MessageRole.USER, message)

    def add_assistant_message(
        self,
        conversation_id: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add an assistant message to the conversation history.

        Args:
            conversation_id: ID of the conversation
            message: Assistant message text
            metadata: Optional metadata for the message
        """
        self.history_manager.add_message(
            conversation_id, MessageRole.ASSISTANT, message, metadata
        )

    def add_tool_call_message(
        self,
        conversation_id: str,
        function_name: str,
        function_args: Dict[str, Any],
        tool_call_id: str,
    ) -> None:
        """
        Add a tool call message to the conversation history.

        Args:
            conversation_id: ID of the conversation
            function_name: Name of the called function
            function_args: Function arguments
            tool_call_id: ID of the tool call
        """
        tool_call_content = f"Function: {function_name}\nArguments: {json.dumps(function_args, indent=2)}"
        self.history_manager.add_message(
            conversation_id,
            MessageRole.TOOL,
            tool_call_content,
            metadata={
                "name": function_name,
                "arguments": function_args,
                "tool_call_id": tool_call_id,
            },
        )

    def add_tool_result_message(
        self,
        conversation_id: str,
        function_name: str,
        function_args: Dict[str, Any],
        result: Any,
        tool_call_id: str,
    ) -> None:
        """
        Add a tool result message to the conversation history.

        Args:
            conversation_id: ID of the conversation
            function_name: Name of the called function
            function_args: Function arguments
            result: Result of the tool execution
            tool_call_id: ID of the tool call
        """
        result_content = json.dumps(result) if isinstance(result, dict) else str(result)
        self.history_manager.add_message(
            conversation_id,
            MessageRole.TOOL,
            result_content,
            metadata={
                "name": function_name,
                "arguments": function_args,
                "result": result,
                "tool_call_id": tool_call_id,
            },
        )

    def add_tool_error_message(
        self,
        conversation_id: str,
        function_name: str,
        function_args: Dict[str, Any],
        error: str,
        tool_call_id: str,
    ) -> None:
        """
        Add a tool error message to the conversation history.

        Args:
            conversation_id: ID of the conversation
            function_name: Name of the called function
            function_args: Function arguments
            error: Error message
            tool_call_id: ID of the tool call
        """
        self.history_manager.add_message(
            conversation_id,
            MessageRole.TOOL,
            f"Error: {error}",
            metadata={
                "name": function_name,
                "arguments": function_args,
                "error": error,
                "tool_call_id": tool_call_id,
            },
        )

    def add_system_message_with_tool_responses(
        self, conversation_id: str, structured_responses: List[Dict[str, Any]]
    ) -> None:
        """
        Add a system message with tool responses to the conversation history.

        Args:
            conversation_id: ID of the conversation
            structured_responses: List of structured tool responses
        """
        all_responses_json = json.dumps(structured_responses)
        self.history_manager.add_message(
            conversation_id,
            MessageRole.SYSTEM,
            f"Tool response data: {all_responses_json}\n\nPlease format a SINGLE, COHERENT response to the user based on ALL this data. Avoid repetition. Respond in the same language the user is using.",
        )

    def get_conversation_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Get messages from a conversation.

        Args:
            conversation_id: ID of the conversation

        Returns:
            List of messages in OpenAI format
        """
        return self.history_manager.get_messages(conversation_id)


# Singleton instance
_openai_message_service: Optional[OpenAIMessageService] = None


def get_openai_message_service() -> OpenAIMessageService:
    """
    Get the singleton message service instance.

    Returns:
        Message service instance
    """
    global _openai_message_service

    if _openai_message_service is None:
        _openai_message_service = OpenAIMessageService()

    return _openai_message_service
