"""OpenAI message service for processing messages and tool calls.

This module provides a service for handling OpenAI-specific conversation messages,
tool calls, and interactions with the history manager.
"""

import json
from typing import Dict, Any, Optional, List, Union

from ai_tools_core.logger import get_logger
from ai_tools_core.history.manager import get_history_manager
from ai_tools_core.history.models import MessageRole
from ai_tools_core.services.openai_service import get_openai_service

# Get logger for this module
logger = get_logger(__name__)


class OpenAIMessageService:
    """Service for processing OpenAI-specific messages and tool calls."""

    system_message: str = "You are an AI assistant"

    def __init__(self, system_message: Optional[str] = None):
        """Initialize the message service."""
        # Explicitly use the OpenAI formatter for this service
        self.history_manager = get_history_manager(storage_type="file", formatter_type="openai")
        self.openai_service = get_openai_service()
        self.system_message = system_message or self.system_message
        logger.info("OpenAI message service initialized")

    def create_or_get_conversation(
        self,
        user_id: str,
        conversation_id: Optional[str] = None,
        context: Optional[str] = None,
        system_message: Optional[str] = None,
    ) -> str:
        """
        Create a new conversation or get an existing one.

        Args:
            user_id: ID of the user
            conversation_id: Optional ID of an existing conversation
            context: Optional context to set for the conversation
            system_message: Optional system message to use for this conversation

        Returns:
            Conversation ID
        """
        if not conversation_id:
            conversation_id = self.history_manager.create_conversation(user_id)
            # Add system message to set the context
            self.history_manager.add_message(conversation_id, MessageRole.SYSTEM, system_message or self.system_message)

            # Set context if provided
            if context:
                self.set_conversation_context(conversation_id, context)
        elif system_message is not None:
            # Check if there's an existing system message and update it if different
            messages = self.history_manager.get_messages(conversation_id)
            system_message_found = False

            for message in messages:
                if message["role"] == "system":
                    system_message_found = True
                    # If the system message is different, replace it
                    if message["content"] != system_message:
                        # Remove the existing system message
                        # We need to get the raw conversation to modify it
                        conversation = self.history_manager.get_conversation(conversation_id)
                        if conversation:
                            # Find and remove the system message
                            for i, msg in enumerate(conversation.messages):
                                if msg.role == MessageRole.SYSTEM:
                                    # Replace with the new system message
                                    conversation.messages[i].content = system_message
                                    # Save the updated conversation
                                    self.history_manager.save_conversation(conversation)
                                    break
                    break

            # If no system message was found, add one
            if not system_message_found:
                self.history_manager.add_message(conversation_id, MessageRole.SYSTEM, system_message)

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
        append_context_footer: bool = True,
    ) -> None:
        """
        Add an assistant message to the conversation history.

        Args:
            conversation_id: ID of the conversation
            message: Assistant message text
            metadata: Optional metadata for the message
            append_context_footer: Whether to append the context as a footer to the message
        """
        # Append context footer if requested
        if append_context_footer:
            context = self.get_conversation_context(conversation_id)
            if context:
                # Check if message already has a context footer
                if "---" in message and message.split("---")[-1].strip() != context:
                    # Remove existing context footer
                    message = message.split("---")[0].strip()

                # Add the context footer
                message += f"\n\n---\n{context}"

        self.history_manager.add_message(conversation_id, MessageRole.ASSISTANT, message, metadata)

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

    def get_conversation_messages(self, conversation_id: str, max_tokens: int = 4000) -> List[Dict[str, Any]]:
        """
        Get messages from a conversation, limited by token count.
        Also includes the current context in a system message.

        Args:
            conversation_id: ID of the conversation
            max_tokens: Maximum number of tokens to include in the context

        Returns:
            List of messages in OpenAI format, limited by token count
        """
        # Get all messages with the OpenAI formatter
        all_messages = self.history_manager.get_messages(conversation_id, formatter_type="openai")

        # Get the current context
        context = self.get_conversation_context(conversation_id)

        # If we have a context, ensure it's included in a system message
        if context:
            # Look for an existing system message to update
            system_message_found = False
            for msg in all_messages:
                if msg["role"] == "system":
                    # Update the system message with the context
                    # First, remove any existing context statement
                    base_content = msg["content"]
                    if "Current context:" in base_content:
                        # Remove the existing context part
                        base_content = base_content.split("Current context:")[0].strip()

                    # Add the new context
                    msg["content"] = f"{base_content}\n\nCurrent context: {context}"
                    system_message_found = True
                    break

            # If no system message exists, add one with the context at the beginning
            if not system_message_found:
                all_messages.insert(
                    0, {"role": "system", "content": f"You are an AI assistant. Current context: {context}"}
                )

        # Limit messages by token count
        limited_messages = self.openai_service.limit_messages_by_tokens(
            messages=all_messages, max_tokens=max_tokens, keep_system_messages=True
        )

        return limited_messages


# Singleton instance
_openai_message_service: Optional[OpenAIMessageService] = None


def get_openai_message_service(system_message: Optional[str] = None) -> OpenAIMessageService:
    """
    Get the singleton message service instance.

    Returns:
        Message service instance
    """
    global _openai_message_service

    if _openai_message_service is None:
        _openai_message_service = OpenAIMessageService(system_message=system_message)

    if system_message is not None:
        _openai_message_service.system_message = system_message

    return _openai_message_service


# Context management methods for the OpenAIMessageService
setattr(
    OpenAIMessageService,
    "set_conversation_context",
    lambda self, conversation_id, context: self.history_manager.set_conversation_context(conversation_id, context),
)
setattr(
    OpenAIMessageService,
    "get_conversation_context",
    lambda self, conversation_id: self.history_manager.get_conversation_context(conversation_id),
)
setattr(
    OpenAIMessageService,
    "clear_conversation_context",
    lambda self, conversation_id: self.history_manager.clear_conversation_context(conversation_id),
)
