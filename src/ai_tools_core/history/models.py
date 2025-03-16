"""Models for conversation history management."""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Enumeration of possible message roles in a conversation."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class Message(BaseModel):
    """Model representing a single message in a conversation."""

    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None


class Conversation(BaseModel):
    """Model representing a conversation with multiple messages."""

    id: str
    user_id: str
    messages: List[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None
    context: Optional[str] = None  # Simple string context


class ConversationSummary(BaseModel):
    """Summary of a conversation for display purposes."""

    id: str
    user_id: str
    message_count: int
    last_message_at: datetime
    first_message_at: datetime
