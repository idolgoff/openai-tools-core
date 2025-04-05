"""AI Tools Core - A core library for AI tools and integrations.

This package provides core functionality for working with AI services,
managing conversation history, and executing AI-powered tools.
"""

__version__ = "0.4.0"

# Import key components to make them available at the package level
from .tools import ToolRegistry
from .logger import get_logger, log_tool_execution

# Import services
from .services.openai_service import OpenAIService, get_openai_service
from .services.openai_message_service import OpenAIMessageService, get_openai_message_service
from .services.tool_service import ToolService, get_tool_service

# Import usage tracking components
from .usage import UsageEvent, UsageTracker, NoOpUsageTracker, InMemoryUsageTracker

# Import history components
try:
    from .history import (
        Conversation,
        Message,
        MessageRole,
        ConversationSummary,
        MessageFormatter,
        OpenAIMessageFormatter,
        AnthropicMessageFormatter,
        create_message_formatter,
        get_history_manager,
    )
except ImportError:
    # During transition, these may not be available yet
    pass

# Define what's available when using `from ai_tools_core import *`
__all__ = [
    # Version info
    "__version__",
    # Core tools
    "ToolRegistry",
    # Utilities
    "get_logger",
    "log_tool_execution",
    # Services
    "OpenAIService",
    "get_openai_service",
    "OpenAIMessageService",
    "get_openai_message_service",
    "ToolService",
    "get_tool_service",
    # History components
    "Conversation",
    "Message",
    "MessageRole",
    "ConversationSummary",
    "MessageFormatter",
    "OpenAIMessageFormatter",
    "AnthropicMessageFormatter",
    "create_message_formatter",
    "get_history_manager",
]
