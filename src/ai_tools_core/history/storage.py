"""Storage backends for conversation history.

This module provides abstract interfaces and concrete implementations
for different storage backends used by the history manager.
"""

from abc import ABC, abstractmethod
import json
import os
from typing import Dict, List, Optional, Any, Union

from ai_tools_core.logger import get_logger
from ai_tools_core.history.models import Conversation, ConversationSummary

# Get logger for this module
logger = get_logger(__name__)


class StorageBackend(ABC):
    """Abstract base class for conversation storage backends."""

    @abstractmethod
    def save_conversation(self, conversation: Conversation) -> bool:
        """
        Save a conversation to storage.

        Args:
            conversation: Conversation to save

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def load_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """
        Load a conversation from storage.

        Args:
            conversation_id: ID of the conversation to load

        Returns:
            Loaded conversation or None if not found
        """
        pass

    @abstractmethod
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation from storage.

        Args:
            conversation_id: ID of the conversation to delete

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def list_conversations(self, user_id: Optional[str] = None) -> List[ConversationSummary]:
        """
        List conversations, optionally filtered by user ID.

        Args:
            user_id: Optional user ID to filter by

        Returns:
            List of conversation summaries
        """
        pass


class MemoryStorageBackend(StorageBackend):
    """In-memory storage backend for conversations."""

    def __init__(self):
        """Initialize the memory storage backend."""
        self._conversations: Dict[str, Conversation] = {}
        logger.info("Memory storage backend initialized")

    def save_conversation(self, conversation: Conversation) -> bool:
        """
        Save a conversation to memory.

        Args:
            conversation: Conversation to save

        Returns:
            True if successful, False otherwise
        """
        try:
            self._conversations[conversation.id] = conversation
            logger.debug(f"Saved conversation {conversation.id} to memory")
            return True
        except Exception as e:
            logger.error(f"Error saving conversation {conversation.id} to memory: {str(e)}", exc_info=True)
            return False

    def load_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """
        Load a conversation from memory.

        Args:
            conversation_id: ID of the conversation to load

        Returns:
            Loaded conversation or None if not found
        """
        conversation = self._conversations.get(conversation_id)
        if not conversation:
            logger.warning(f"Conversation {conversation_id} not found in memory")
            return None

        return conversation

    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation from memory.

        Args:
            conversation_id: ID of the conversation to delete

        Returns:
            True if successful, False otherwise
        """
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            logger.info(f"Deleted conversation {conversation_id} from memory")
            return True

        logger.warning(f"Conversation {conversation_id} not found in memory for deletion")
        return False

    def list_conversations(self, user_id: Optional[str] = None) -> List[ConversationSummary]:
        """
        List conversations, optionally filtered by user ID.

        Args:
            user_id: Optional user ID to filter by

        Returns:
            List of conversation summaries
        """
        summaries = []

        for conversation in self._conversations.values():
            # Skip if not matching user_id
            if user_id and conversation.user_id != user_id:
                continue

            # Create summary
            summary = ConversationSummary(
                id=conversation.id,
                user_id=conversation.user_id,
                message_count=len(conversation.messages),
                first_message_at=(
                    conversation.messages[0].timestamp if conversation.messages else conversation.created_at
                ),
                last_message_at=(
                    conversation.messages[-1].timestamp if conversation.messages else conversation.updated_at
                ),
            )

            summaries.append(summary)

        # Sort by last message timestamp (newest first)
        summaries.sort(key=lambda x: x.last_message_at, reverse=True)

        return summaries


class FileStorageBackend(StorageBackend):
    """File-based storage backend for conversations."""

    def __init__(self, storage_dir: str):
        """
        Initialize the file storage backend.

        Args:
            storage_dir: Directory for storing conversation files
        """
        self.storage_dir = storage_dir

        # Create storage directory if it doesn't exist
        os.makedirs(self.storage_dir, exist_ok=True)

        logger.info(f"File storage backend initialized with directory: {self.storage_dir}")

    def save_conversation(self, conversation: Conversation) -> bool:
        """
        Save a conversation to a file.

        Args:
            conversation: Conversation to save

        Returns:
            True if successful, False otherwise
        """
        conversation_path = os.path.join(self.storage_dir, f"{conversation.id}.json")

        try:
            # Convert to JSON
            conversation_data = conversation.model_dump(mode="json")

            # Save to disk
            with open(conversation_path, "w") as f:
                json.dump(conversation_data, f, indent=2)

            logger.debug(f"Saved conversation {conversation.id} to file")
            return True
        except Exception as e:
            logger.error(f"Error saving conversation {conversation.id} to file: {str(e)}", exc_info=True)
            return False

    def load_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """
        Load a conversation from a file.

        Args:
            conversation_id: ID of the conversation to load

        Returns:
            Loaded conversation or None if not found
        """
        conversation_path = os.path.join(self.storage_dir, f"{conversation_id}.json")
        if not os.path.exists(conversation_path):
            logger.warning(f"Conversation file {conversation_id}.json not found")
            return None

        try:
            with open(conversation_path, "r") as f:
                conversation_data = json.load(f)

            # Convert to Conversation object
            conversation = Conversation.model_validate(conversation_data)

            return conversation
        except Exception as e:
            logger.error(f"Error loading conversation {conversation_id} from file: {str(e)}", exc_info=True)
            return None

    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation file.

        Args:
            conversation_id: ID of the conversation to delete

        Returns:
            True if successful, False otherwise
        """
        conversation_path = os.path.join(self.storage_dir, f"{conversation_id}.json")
        if os.path.exists(conversation_path):
            try:
                os.remove(conversation_path)
                logger.info(f"Deleted conversation file {conversation_id}.json")
                return True
            except Exception as e:
                logger.error(f"Error deleting conversation file {conversation_id}.json: {str(e)}", exc_info=True)
                return False

        logger.warning(f"Conversation file {conversation_id}.json not found for deletion")
        return False

    def list_conversations(self, user_id: Optional[str] = None) -> List[ConversationSummary]:
        """
        List conversations from files, optionally filtered by user ID.

        Args:
            user_id: Optional user ID to filter by

        Returns:
            List of conversation summaries
        """
        summaries = []

        # List all conversation files
        for filename in os.listdir(self.storage_dir):
            if not filename.endswith(".json"):
                continue

            try:
                with open(os.path.join(self.storage_dir, filename), "r") as f:
                    conversation_data = json.load(f)

                # Skip if not matching user_id
                if user_id and conversation_data.get("user_id") != user_id:
                    continue

                # Create summary
                messages = conversation_data.get("messages", [])
                first_message = messages[0] if messages else {}
                last_message = messages[-1] if messages else {}

                summary = ConversationSummary(
                    id=conversation_data["id"],
                    user_id=conversation_data["user_id"],
                    message_count=len(messages),
                    first_message_at=first_message.get("timestamp", conversation_data.get("created_at")),
                    last_message_at=last_message.get("timestamp", conversation_data.get("updated_at")),
                )

                summaries.append(summary)
            except Exception as e:
                logger.error(f"Error processing conversation file {filename}: {str(e)}", exc_info=True)

        # Sort by last message timestamp (newest first)
        summaries.sort(key=lambda x: x.last_message_at, reverse=True)

        return summaries


# Factory function to create storage backends
def create_storage_backend(backend_type: str, **kwargs) -> StorageBackend:
    """
    Create a storage backend of the specified type.

    Args:
        backend_type: Type of storage backend ('memory' or 'file')
        **kwargs: Additional arguments for the storage backend

    Returns:
        Storage backend instance

    Raises:
        ValueError: If the backend type is unknown
    """
    if backend_type == "memory":
        return MemoryStorageBackend()
    elif backend_type == "file":
        storage_dir = kwargs.get("storage_dir")
        if not storage_dir:
            raise ValueError("storage_dir is required for file storage backend")
        return FileStorageBackend(storage_dir)
    else:
        raise ValueError(f"Unknown storage backend type: {backend_type}")
