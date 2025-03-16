"""History module for conversation management.

This module provides functionality for managing conversation history,
including storing and retrieving messages, formatting them for different AI providers,
and managing conversation state.
"""

from ai_tools_core.history.models import Conversation, ConversationSummary, Message, MessageRole
from ai_tools_core.history.formatters import (
    MessageFormatter,
    OpenAIMessageFormatter,
    AnthropicMessageFormatter,
    create_message_formatter,
)
from ai_tools_core.history.manager import get_history_manager

__all__ = [
    "Conversation",
    "ConversationSummary",
    "Message",
    "MessageRole",
    "MessageFormatter",
    "OpenAIMessageFormatter",
    "AnthropicMessageFormatter",
    "create_message_formatter",
    "get_history_manager",
]
