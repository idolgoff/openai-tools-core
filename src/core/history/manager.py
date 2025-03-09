"""History manager for storing and retrieving conversation history."""
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

from core.logger import get_logger
from core.history.models import Conversation, Message, MessageRole, ConversationSummary

# Get logger for this module
logger = get_logger(__name__)

# Directory for storing conversation history
# Get the project root directory (3 levels up from this file)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
HISTORY_DIR = os.path.join(PROJECT_ROOT, "data", "history")


class HistoryManager:
    """Manager for conversation history."""
    
    def __init__(self, history_dir: Optional[str] = None):
        """
        Initialize the history manager.
        
        Args:
            history_dir: Directory for storing conversation history
        """
        self.history_dir = history_dir or HISTORY_DIR
        
        # Create history directory if it doesn't exist
        os.makedirs(self.history_dir, exist_ok=True)
        
        logger.info(f"History manager initialized with directory: {self.history_dir}")
        
        # In-memory cache of active conversations
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
        
        conversation = Conversation(
            id=conversation_id,
            user_id=user_id,
            metadata=metadata or {}
        )
        
        # Store in memory
        self._active_conversations[conversation_id] = conversation
        
        # Save to disk
        self._save_conversation(conversation)
        
        logger.info(f"Created conversation {conversation_id} for user {user_id}")
        
        return conversation_id
    
    def add_message(self, conversation_id: str, role: Union[str, MessageRole], 
                   content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
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
        message = Message(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        
        # Add message to conversation
        conversation.messages.append(message)
        conversation.updated_at = datetime.now()
        
        # Save conversation
        self._save_conversation(conversation)
        
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
        
        # Try to load from disk
        conversation_path = os.path.join(self.history_dir, f"{conversation_id}.json")
        if not os.path.exists(conversation_path):
            logger.warning(f"Conversation {conversation_id} not found on disk")
            return None
        
        try:
            with open(conversation_path, "r") as f:
                conversation_data = json.load(f)
            
            # Convert to Conversation object
            conversation = Conversation.model_validate(conversation_data)
            
            # Cache in memory
            self._active_conversations[conversation_id] = conversation
            
            return conversation
        except Exception as e:
            logger.error(f"Error loading conversation {conversation_id}: {str(e)}", exc_info=True)
            return None
    
    def get_messages(self, conversation_id: str) -> List[Dict[str, str]]:
        """
        Get messages from a conversation in a format suitable for OpenAI API.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            List of messages in OpenAI format
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return []
        
        # Convert to OpenAI format
        return [{"role": msg.role.value, "content": msg.content} for msg in conversation.messages]
    
    def list_conversations(self, user_id: Optional[str] = None) -> List[ConversationSummary]:
        """
        List conversations, optionally filtered by user ID.
        
        Args:
            user_id: Optional user ID to filter by
            
        Returns:
            List of conversation summaries
        """
        conversations = []
        
        # List all conversation files
        for filename in os.listdir(self.history_dir):
            if not filename.endswith(".json"):
                continue
            
            try:
                with open(os.path.join(self.history_dir, filename), "r") as f:
                    conversation_data = json.load(f)
                
                # Skip if not matching user_id
                if user_id and conversation_data.get("user_id") != user_id:
                    continue
                
                # Create summary
                messages = conversation_data.get("messages", [])
                first_message_at = datetime.fromisoformat(messages[0]["timestamp"]) if messages else datetime.now()
                last_message_at = datetime.fromisoformat(messages[-1]["timestamp"]) if messages else datetime.now()
                
                summary = ConversationSummary(
                    id=conversation_data["id"],
                    user_id=conversation_data["user_id"],
                    message_count=len(messages),
                    first_message_at=first_message_at,
                    last_message_at=last_message_at
                )
                
                conversations.append(summary)
            except Exception as e:
                logger.error(f"Error processing conversation file {filename}: {str(e)}", exc_info=True)
        
        # Sort by last message timestamp (newest first)
        conversations.sort(key=lambda x: x.last_message_at, reverse=True)
        
        return conversations
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            True if successful, False otherwise
        """
        # Remove from memory
        if conversation_id in self._active_conversations:
            del self._active_conversations[conversation_id]
        
        # Remove from disk
        conversation_path = os.path.join(self.history_dir, f"{conversation_id}.json")
        if os.path.exists(conversation_path):
            try:
                os.remove(conversation_path)
                logger.info(f"Deleted conversation {conversation_id}")
                return True
            except Exception as e:
                logger.error(f"Error deleting conversation {conversation_id}: {str(e)}", exc_info=True)
                return False
        
        logger.warning(f"Conversation {conversation_id} not found for deletion")
        return False
    
    def _save_conversation(self, conversation: Conversation) -> None:
        """
        Save a conversation to disk.
        
        Args:
            conversation: Conversation to save
        """
        conversation_path = os.path.join(self.history_dir, f"{conversation.id}.json")
        
        try:
            # Convert to JSON
            conversation_data = conversation.model_dump(mode="json")
            
            # Save to disk
            with open(conversation_path, "w") as f:
                json.dump(conversation_data, f, indent=2)
            
            logger.debug(f"Saved conversation {conversation.id} to disk")
        except Exception as e:
            logger.error(f"Error saving conversation {conversation.id}: {str(e)}", exc_info=True)


# Singleton instance
_history_manager: Optional[HistoryManager] = None


def get_history_manager() -> HistoryManager:
    """
    Get the singleton history manager instance.
    
    Returns:
        History manager instance
    """
    global _history_manager
    
    if _history_manager is None:
        _history_manager = HistoryManager()
    
    return _history_manager
