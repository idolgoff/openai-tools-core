"""Environment variable handling utilities."""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
# Use override=True to ensure we always get the latest values
load_dotenv(override=True)


def get_env(key: str, default: Optional[str] = None) -> str:
    """
    Get environment variable value.

    Args:
        key: Environment variable name
        default: Default value if environment variable is not set

    Returns:
        Environment variable value or default

    Raises:
        ValueError: If environment variable is not set and no default is provided
    """
    value = os.environ.get(key, default)
    if value is None:
        raise ValueError(f"Environment variable {key} is not set")
    return value


def get_telegram_token() -> str:
    """Get Telegram bot token from environment variables."""
    return get_env("TELEGRAM_BOT_TOKEN")


def get_openai_api_key() -> str:
    """Get OpenAI API key from environment variables."""
    return get_env("OPENAI_API_KEY")


def get_openai_model() -> str:
    """Get OpenAI model name from environment variables."""
    return get_env("OPENAI_MODEL", "gpt-4o-mini")


def get_log_level() -> str:
    """Get log level from environment variables."""
    return get_env("LOG_LEVEL", "INFO")
