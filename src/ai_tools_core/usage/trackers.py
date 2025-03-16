"""Usage trackers for monitoring token consumption."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..logger import get_logger
from .events import UsageEvent

logger = get_logger(__name__)


class UsageTracker(ABC):
    """Interface for tracking token usage.

    This abstract class defines the interface that all usage trackers must implement.
    Clients can provide their own implementation to integrate with their billing systems.
    """

    @abstractmethod
    def track_usage(self, event: UsageEvent) -> None:
        """Track token usage from an event.

        Args:
            event: The usage event to track
        """
        pass

    @abstractmethod
    def get_current_usage(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get the current usage statistics.

        Args:
            user_id: Optional filter by user ID
            session_id: Optional filter by session ID
            start_time: Optional start time for filtering
            end_time: Optional end time for filtering

        Returns:
            Usage statistics dictionary
        """
        pass


class NoOpUsageTracker(UsageTracker):
    """Usage tracker that does nothing.

    This implementation is used as the default when no tracker is provided.
    It performs no tracking and returns empty statistics.
    """

    def track_usage(self, event: UsageEvent) -> None:
        """Track token usage (does nothing)."""
        logger.debug(f"NoOpUsageTracker: Ignoring usage event for {event.model}")
        pass

    def get_current_usage(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get the current usage statistics (returns empty stats)."""
        return {"total_input_tokens": 0, "total_output_tokens": 0, "total_tokens": 0, "event_count": 0}


class InMemoryUsageTracker(UsageTracker):
    """Simple in-memory usage tracker.

    This implementation stores all usage events in memory.
    It's suitable for short-lived applications or testing,
    but not recommended for production use as it will consume
    memory over time and doesn't persist across restarts.
    """

    def __init__(self):
        """Initialize the in-memory usage tracker."""
        self.events: List[UsageEvent] = []

    def track_usage(self, event: UsageEvent) -> None:
        """Track token usage by storing the event in memory.

        Args:
            event: The usage event to track
        """
        self.events.append(event)
        logger.debug(
            f"Tracked usage: {event.input_tokens} input, " f"{event.output_tokens} output tokens for {event.model}"
        )

    def get_current_usage(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get the current usage statistics.

        Args:
            user_id: Optional filter by user ID
            session_id: Optional filter by session ID
            start_time: Optional start time for filtering
            end_time: Optional end time for filtering

        Returns:
            Usage statistics dictionary
        """
        # Filter events based on criteria
        filtered_events = self.events

        if user_id:
            filtered_events = [e for e in filtered_events if e.user_id == user_id]

        if session_id:
            filtered_events = [e for e in filtered_events if e.session_id == session_id]

        if start_time:
            start_str = start_time.isoformat()
            filtered_events = [e for e in filtered_events if e.timestamp >= start_str]

        if end_time:
            end_str = end_time.isoformat()
            filtered_events = [e for e in filtered_events if e.timestamp <= end_str]

        # Calculate totals
        total_input = sum(e.input_tokens for e in filtered_events)
        total_output = sum(e.output_tokens for e in filtered_events)

        # Group by model
        model_usage = {}
        for event in filtered_events:
            model = event.model
            if model not in model_usage:
                model_usage[model] = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
            model_usage[model]["input_tokens"] += event.input_tokens
            model_usage[model]["output_tokens"] += event.output_tokens
            model_usage[model]["total_tokens"] += event.total_tokens

        return {
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_tokens": total_input + total_output,
            "event_count": len(filtered_events),
            "model_breakdown": model_usage,
        }
