"""Utility functions for the Telegram bot."""

from ai_tools_core.utils.env import get_env


def get_telegram_token() -> str:
    """Get Telegram bot token from environment variables."""
    return get_env("TELEGRAM_BOT_TOKEN")
