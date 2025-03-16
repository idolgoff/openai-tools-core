"""Usage events for tracking token consumption."""

from datetime import datetime
from typing import Dict, Any, Optional


class UsageEvent:
    """Event containing token usage information.

    This class represents a single token usage event, typically generated
    when making an API call to an AI service.
    """

    def __init__(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        request_type: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a usage event.

        Args:
            model: The AI model used (e.g., 'gpt-4o-mini')
            input_tokens: Number of input tokens consumed
            output_tokens: Number of output tokens generated
            request_type: Type of request (e.g., 'chat', 'tool_call')
            session_id: Optional session identifier
            user_id: Optional user identifier
            metadata: Additional metadata about the request
        """
        self.timestamp = datetime.now().isoformat()
        self.model = model
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.total_tokens = input_tokens + output_tokens
        self.request_type = request_type
        self.session_id = session_id
        self.user_id = user_id
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert the event to a dictionary.

        Returns:
            Dictionary representation of the event
        """
        return {
            "timestamp": self.timestamp,
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "request_type": self.request_type,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "metadata": self.metadata,
        }
