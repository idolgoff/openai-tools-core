"""Billing module for the Telegram bot.

This module provides functionality for tracking token usage and implementing
a simple billing system for the Telegram bot.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List

from ai_tools_core.usage import UsageTracker, UsageEvent
from ai_tools_core.logger import get_logger

# Get logger for this module
logger = get_logger(__name__)


class BotBillingTracker(UsageTracker):
    """Usage tracker for the Telegram bot with billing functionality."""

    def __init__(self, storage_path: str = "data/billing"):
        """Initialize the bot billing tracker.

        Args:
            storage_path: Path to store billing data
        """
        self.storage_path = storage_path
        self._ensure_storage_exists()
        self._pricing = {
            # Default pricing in USD per 1000 tokens
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4o": {"input": 0.01, "output": 0.03},
            "gpt-4o-mini": {"input": 0.005, "output": 0.015},
            "gpt-3.5-turbo": {"input": 0.001, "output": 0.002},
            # Fallback pricing
            "default": {"input": 0.01, "output": 0.02},
        }
        logger.info(f"Bot billing tracker initialized with storage at {storage_path}")

    def _ensure_storage_exists(self) -> None:
        """Ensure the storage directory exists."""
        os.makedirs(self.storage_path, exist_ok=True)

        # Create user directory if it doesn't exist
        users_path = os.path.join(self.storage_path, "users")
        os.makedirs(users_path, exist_ok=True)

        # Create sessions directory if it doesn't exist
        sessions_path = os.path.join(self.storage_path, "sessions")
        os.makedirs(sessions_path, exist_ok=True)

    def _get_user_file_path(self, user_id: str) -> str:
        """Get the file path for a user's billing data.

        Args:
            user_id: User ID

        Returns:
            File path for the user's billing data
        """
        return os.path.join(self.storage_path, "users", f"{user_id}.json")

    def _get_session_file_path(self, session_id: str) -> str:
        """Get the file path for a session's billing data.

        Args:
            session_id: Session ID

        Returns:
            File path for the session's billing data
        """
        return os.path.join(self.storage_path, "sessions", f"{session_id}.json")

    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate the cost of a request based on token usage.

        Args:
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Cost in USD
        """
        # Get pricing for the model or use default pricing
        pricing = self._pricing.get(model, self._pricing["default"])

        # Calculate cost (convert from per 1000 tokens to per token)
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]

        return input_cost + output_cost

    def track_usage(self, event: UsageEvent) -> None:
        """Track usage event and update billing data.

        Args:
            event: Usage event
        """
        # Calculate cost
        cost = self._calculate_cost(event.model, event.input_tokens, event.output_tokens)

        # Add cost to the event data
        event_data = event.to_dict()
        event_data["cost"] = cost

        # Update user billing data if user_id is provided
        if event.user_id:
            self._update_user_billing(event.user_id, event_data)

        # Update session billing data if session_id is provided
        if event.session_id:
            self._update_session_billing(event.session_id, event_data)

        logger.info(
            f"$$$ Used model: {event.model}"
            f"Tracked usage: {event.input_tokens} input tokens, "
            f"{event.output_tokens} output tokens, ${cost:.6f} cost"
        )

    def _update_user_billing(self, user_id: str, event_data: Dict[str, Any]) -> None:
        """Update billing data for a user.

        Args:
            user_id: User ID
            event_data: Usage event data
        """
        file_path = self._get_user_file_path(user_id)

        # Load existing data or create new data
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                user_data = json.load(f)
        else:
            user_data = {"user_id": user_id, "total_tokens": 0, "total_cost": 0.0, "events": []}

        # Update totals
        user_data["total_tokens"] += event_data["input_tokens"] + event_data["output_tokens"]
        user_data["total_cost"] += event_data["cost"]

        # Add event to history
        user_data["events"].append(event_data)

        # Save updated data
        with open(file_path, "w") as f:
            json.dump(user_data, f, indent=2)

    def _update_session_billing(self, session_id: str, event_data: Dict[str, Any]) -> None:
        """Update billing data for a session.

        Args:
            session_id: Session ID
            event_data: Usage event data
        """
        file_path = self._get_session_file_path(session_id)

        # Load existing data or create new data
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                session_data = json.load(f)
        else:
            session_data = {"session_id": session_id, "total_tokens": 0, "total_cost": 0.0, "events": []}

        # Update totals
        session_data["total_tokens"] += event_data["input_tokens"] + event_data["output_tokens"]
        session_data["total_cost"] += event_data["cost"]

        # Add event to history
        session_data["events"].append(event_data)

        # Save updated data
        with open(file_path, "w") as f:
            json.dump(session_data, f, indent=2)

    def get_current_usage(
        self, user_id: Optional[str] = None, session_id: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        """Get current usage statistics.

        Args:
            user_id: Optional user ID to get usage for
            session_id: Optional session ID to get usage for

        Returns:
            Usage statistics
        """
        if user_id:
            return self._get_user_usage(user_id)
        elif session_id:
            return self._get_session_usage(session_id)
        else:
            return self._get_total_usage()

    def _get_user_usage(self, user_id: str) -> Dict[str, Any]:
        """Get usage statistics for a user.

        Args:
            user_id: User ID

        Returns:
            User usage statistics
        """
        file_path = self._get_user_file_path(user_id)

        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                user_data = json.load(f)

            # Return summary without full event history
            return {
                "user_id": user_id,
                "total_tokens": user_data["total_tokens"],
                "total_cost": user_data["total_cost"],
                "event_count": len(user_data["events"]),
            }
        else:
            return {"user_id": user_id, "total_tokens": 0, "total_cost": 0.0, "event_count": 0}

    def _get_session_usage(self, session_id: str) -> Dict[str, Any]:
        """Get usage statistics for a session.

        Args:
            session_id: Session ID

        Returns:
            Session usage statistics
        """
        file_path = self._get_session_file_path(session_id)

        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                session_data = json.load(f)

            # Return summary without full event history
            return {
                "session_id": session_id,
                "total_tokens": session_data["total_tokens"],
                "total_cost": session_data["total_cost"],
                "event_count": len(session_data["events"]),
            }
        else:
            return {"session_id": session_id, "total_tokens": 0, "total_cost": 0.0, "event_count": 0}

    def _get_total_usage(self) -> Dict[str, Any]:
        """Get total usage statistics across all users and sessions.

        Returns:
            Total usage statistics
        """
        total_tokens = 0
        total_cost = 0.0
        user_count = 0
        session_count = 0

        # Sum up user data
        users_path = os.path.join(self.storage_path, "users")
        for filename in os.listdir(users_path):
            if filename.endswith(".json"):
                with open(os.path.join(users_path, filename), "r") as f:
                    user_data = json.load(f)
                    total_tokens += user_data["total_tokens"]
                    total_cost += user_data["total_cost"]
                    user_count += 1

        # Sum up session data
        sessions_path = os.path.join(self.storage_path, "sessions")
        for filename in os.listdir(sessions_path):
            if filename.endswith(".json"):
                session_count += 1

        return {
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "user_count": user_count,
            "session_count": session_count,
        }

    def get_user_billing_report(self, user_id: str) -> Dict[str, Any]:
        """Get a detailed billing report for a user.

        Args:
            user_id: User ID

        Returns:
            Detailed billing report
        """
        file_path = self._get_user_file_path(user_id)

        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                user_data = json.load(f)

            # Calculate daily usage
            daily_usage = {}
            for event in user_data["events"]:
                date = event["timestamp"].split("T")[0]
                if date not in daily_usage:
                    daily_usage[date] = {"tokens": 0, "cost": 0.0}
                daily_usage[date]["tokens"] += event["input_tokens"] + event["output_tokens"]
                daily_usage[date]["cost"] += event["cost"]

            # Format the report
            report = {
                "user_id": user_id,
                "total_tokens": user_data["total_tokens"],
                "total_cost": user_data["total_cost"],
                "daily_usage": daily_usage,
                "generated_at": datetime.now().isoformat(),
            }

            return report
        else:
            return {
                "user_id": user_id,
                "total_tokens": 0,
                "total_cost": 0.0,
                "daily_usage": {},
                "generated_at": datetime.now().isoformat(),
            }


# Singleton instance
_bot_billing_tracker: Optional[BotBillingTracker] = None


def get_bot_billing_tracker() -> BotBillingTracker:
    """Get the singleton bot billing tracker instance.

    Returns:
        Bot billing tracker instance
    """
    global _bot_billing_tracker

    if _bot_billing_tracker is None:
        _bot_billing_tracker = BotBillingTracker()

    return _bot_billing_tracker
