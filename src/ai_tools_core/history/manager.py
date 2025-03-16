"""History manager for storing and retrieving conversation history."""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

from ai_tools_core.logger import get_logger
from ai_tools_core.history.models import Conversation, Message, MessageRole, ConversationSummary
from ai_tools_core.history.storage import StorageBackend, create_storage_backend
from ai_tools_core.history.formatters import MessageFormatter, create_message_formatter

# Get logger for this module
logger = get_logger(__name__)

# Directory for storing conversation history
# Get the project root directory (3 levels up from this file)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
HISTORY_DIR = os.path.join(PROJECT_ROOT, "data", "history")


class HistoryManager:
    """Manager for conversation history."""

    def __init__(self, storage_type: str = "file", formatter_type: str = "openai", history_dir: Optional[str] = None):
        """
        Initialize the history manager.

        Args:
            storage_type: Type of storage backend to use ('memory' or 'file')
            formatter_type: Type of message formatter to use ('openai' or 'anthropic')
            history_dir: Directory for storing conversation history (only used for file storage)
        """
        self.history_dir = history_dir or HISTORY_DIR

        # Initialize storage backend
        storage_kwargs = {"storage_dir": self.history_dir} if storage_type == "file" else {}
        self.storage = create_storage_backend(storage_type, **storage_kwargs)

        # Initialize message formatter
        self.formatter = create_message_formatter(formatter_type)

        logger.info(f"History manager initialized with {storage_type} storage and {formatter_type} formatter")

        # In-memory cache of active conversations (used regardless of storage backend)
        self._active_conversations: Dict[str, Conversation] = {}

    def create_conversation(self, user_id: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new conversation.

        Args:
            user_id: ID of the user
            metadata: Optional metadata for the conversation

        Returns:
            ID of the created conversation
        """
        conversation_id = str(uuid.uuid4())

        conversation = Conversation(id=conversation_id, user_id=user_id, metadata=metadata or {})

        # Store in memory cache
        self._active_conversations[conversation_id] = conversation

        # Save to storage backend
        self.storage.save_conversation(conversation)

        logger.info(f"Created conversation {conversation_id} for user {user_id}")

        return conversation_id

    def add_message(
        self,
        conversation_id: str,
        role: Union[str, MessageRole],
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a message to a conversation.

        Args:
            conversation_id: ID of the conversation
            role: Role of the message sender
            content: Message content
            metadata: Optional metadata for the message
        """
        # Ensure role is a MessageRole enum
        if isinstance(role, str):
            role = MessageRole(role)

        # Get conversation
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            logger.warning(f"Conversation {conversation_id} not found")
            return

        # Create message
        message = Message(role=role, content=content, metadata=metadata or {})

        # Add message to conversation
        conversation.messages.append(message)
        conversation.updated_at = datetime.now()

        # Save conversation
        self.save_conversation(conversation)

        logger.debug(f"Added {role} message to conversation {conversation_id}")

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """
        Get a conversation by ID.

        Args:
            conversation_id: ID of the conversation

        Returns:
            Conversation or None if not found
        """
        # Check in-memory cache first
        if conversation_id in self._active_conversations:
            return self._active_conversations[conversation_id]

        # Try to load from storage backend
        conversation = self.storage.load_conversation(conversation_id)
        if not conversation:
            logger.warning(f"Conversation {conversation_id} not found in storage")
            return None

        # Cache in memory
        self._active_conversations[conversation_id] = conversation

        return conversation

    def get_messages(self, conversation_id: str, formatter_type: Optional[str] = None) -> Any:
        """
        Get messages from a conversation in a format suitable for the specified AI API.

        Args:
            conversation_id: ID of the conversation
            formatter_type: Optional formatter type to override the default

        Returns:
            Formatted messages for the specified AI API
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return []

        # Use specified formatter or default
        if formatter_type:
            formatter = create_message_formatter(formatter_type)
        else:
            formatter = self.formatter

        # Format messages using the appropriate formatter
        return formatter.format_messages(conversation)

    def list_conversations(self, user_id: Optional[str] = None) -> List[ConversationSummary]:
        """
        List conversations, optionally filtered by user ID.

        Args:
            user_id: Optional user ID to filter by

        Returns:
            List of conversation summaries
        """
        # Delegate to storage backend
        return self.storage.list_conversations(user_id)

    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation.

        Args:
            conversation_id: ID of the conversation

        Returns:
            True if successful, False otherwise
        """
        # Remove from memory cache
        if conversation_id in self._active_conversations:
            del self._active_conversations[conversation_id]

        # Delegate to storage backend
        return self.storage.delete_conversation(conversation_id)

    def save_conversation(self, conversation: Conversation) -> bool:
        """
        Save a conversation to storage.

        Args:
            conversation: Conversation to save

        Returns:
            True if successful, False otherwise
        """
        # Update in-memory cache
        self._active_conversations[conversation.id] = conversation

        # Delegate to storage backend
        return self.storage.save_conversation(conversation)

    def set_conversation_context(self, conversation_id: str, context: str) -> bool:
        """
        Set a context for a conversation.

        Args:
            conversation_id: ID of the conversation
            context: Context string to set

        Returns:
            True if successful, False otherwise
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            logger.warning(f"Cannot set context: Conversation {conversation_id} not found")
            return False

        # Set the context
        conversation.context = context

        # Save the conversation
        success = self.save_conversation(conversation)

        if success:
            logger.info(f"Set context for conversation {conversation_id}: {context}")
        else:
            logger.warning(f"Failed to save context for conversation {conversation_id}")

        return success

    def get_conversation_context(self, conversation_id: str) -> Optional[str]:
        """
        Get the context for a conversation.

        Args:
            conversation_id: ID of the conversation

        Returns:
            Context string or None if not set
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            logger.warning(f"Cannot get context: Conversation {conversation_id} not found")
            return None

        return conversation.context

    def clear_conversation_context(self, conversation_id: str) -> bool:
        """
        Clear the context for a conversation.

        Args:
            conversation_id: ID of the conversation

        Returns:
            True if successful, False otherwise
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            logger.warning(f"Cannot clear context: Conversation {conversation_id} not found")
            return False

        # Clear the context
        conversation.context = None

        # Save the conversation
        success = self.save_conversation(conversation)

        if success:
            logger.info(f"Cleared context for conversation {conversation_id}")
        else:
            logger.warning(f"Failed to clear context for conversation {conversation_id}")

        return success


# Singleton instance
_history_manager: Optional[HistoryManager] = None


def get_history_manager(storage_type: str = "file", formatter_type: str = "openai") -> HistoryManager:
    """
    Get the singleton history manager instance.

    Args:
        storage_type: Type of storage backend to use ('memory' or 'file')
        formatter_type: Type of message formatter to use ('openai' or 'anthropic')

    Returns:
        History manager instance
    """
    global _history_manager

    if _history_manager is None:
        _history_manager = HistoryManager(storage_type=storage_type, formatter_type=formatter_type)

    return _history_manager
