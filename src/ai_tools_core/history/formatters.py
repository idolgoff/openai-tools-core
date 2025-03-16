"""Message formatters for conversation history.

This module provides abstract interfaces and concrete implementations
for different message formatters used by the history manager.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

from ai_tools_core.logger import get_logger
from ai_tools_core.history.models import Conversation, Message, MessageRole

# Get logger for this module
logger = get_logger(__name__)


class MessageFormatter(ABC):
    """Abstract base class for message formatters."""

    @abstractmethod
    def format_messages(self, conversation: Conversation) -> List[Dict[str, Any]]:
        """
        Format messages from a conversation for a specific AI provider.

        Args:
            conversation: Conversation containing messages to format

        Returns:
            List of formatted messages
        """
        pass


class OpenAIMessageFormatter(MessageFormatter):
    """Message formatter for OpenAI API."""

    def format_messages(self, conversation: Conversation) -> List[Dict[str, Any]]:
        """
        Format messages for the OpenAI API.

        Args:
            conversation: Conversation containing messages to format

        Returns:
            List of messages in OpenAI format
        """
        formatted_messages = []
        last_assistant_with_tool_calls = None

        for msg in conversation.messages:
            if msg.role == MessageRole.TOOL:
                # For tool messages, check if they're a response to a tool call
                if last_assistant_with_tool_calls and msg.metadata and "name" in msg.metadata:
                    # Find the matching tool call ID from the last assistant message
                    tool_call_id = None
                    if last_assistant_with_tool_calls and "tool_calls" in last_assistant_with_tool_calls:
                        for tool_call in last_assistant_with_tool_calls["tool_calls"]:
                            if tool_call["function"]["name"] == msg.metadata["name"]:
                                tool_call_id = tool_call["id"]
                                break

                    # Add as a function response to the OpenAI API
                    function_response = {
                        "role": MessageRole.TOOL.value,
                        "name": msg.metadata["name"],
                        "content": msg.content,
                    }

                    # Add tool_call_id if found
                    if tool_call_id:
                        function_response["tool_call_id"] = tool_call_id

                    formatted_messages.append(function_response)
            elif msg.role == MessageRole.ASSISTANT and msg.metadata and "tool_calls" in msg.metadata:
                # For assistant messages with tool calls
                message_dict = {
                    "role": MessageRole.ASSISTANT.value,
                    "content": msg.content or "",
                    "tool_calls": msg.metadata["tool_calls"],
                }
                formatted_messages.append(message_dict)
                last_assistant_with_tool_calls = message_dict
            else:
                # Regular message types (system, user, assistant without tool calls)
                formatted_messages.append({"role": msg.role.value, "content": msg.content})

        return formatted_messages


class AnthropicMessageFormatter(MessageFormatter):
    """Message formatter for Anthropic API."""

    def format_messages(self, conversation: Conversation) -> List[Dict[str, Any]]:
        """
        Format messages for the Anthropic API.

        Args:
            conversation: Conversation containing messages to format

        Returns:
            Dictionary with system prompt and messages in Anthropic format
        """
        formatted_messages = []
        system_message = None

        for msg in conversation.messages:
            if msg.role == MessageRole.SYSTEM:
                # In Anthropic, system messages are not part of the messages array
                # Store the most recent system message
                system_message = msg.content
            elif msg.role == MessageRole.USER:
                # Map USER role to HUMAN role for Anthropic
                formatted_messages.append({"role": "human", "content": msg.content})
            elif msg.role == MessageRole.ASSISTANT:
                # Keep ASSISTANT role the same
                # Skip tool calls for now as they have a different format in Anthropic
                if not (msg.metadata and "tool_calls" in msg.metadata):
                    formatted_messages.append({"role": "assistant", "content": msg.content})
            # Skip TOOL messages as they're handled differently in Anthropic

        # Return both the system message and the formatted messages
        return {"system": system_message, "messages": formatted_messages}


# Factory function to create message formatters
def create_message_formatter(formatter_type: str) -> MessageFormatter:
    """
    Create a message formatter of the specified type.

    Args:
        formatter_type: Type of message formatter ('openai' or 'anthropic')

    Returns:
        Message formatter instance

    Raises:
        ValueError: If the formatter type is unknown
    """
    if formatter_type == "openai":
        return OpenAIMessageFormatter()
    elif formatter_type == "anthropic":
        return AnthropicMessageFormatter()
    else:
        raise ValueError(f"Unknown message formatter type: {formatter_type}")
