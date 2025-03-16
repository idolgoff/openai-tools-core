"""Environment variable handling utilities.

This module provides utilities for accessing environment variables in a consistent way.
It does not automatically load .env files to avoid side effects in library code.

For applications using this library, it's recommended to load environment variables
at the application level, not within the library.

Example usage in an application:
    ```python
    from dotenv import load_dotenv
    load_dotenv()  # Load .env file at application startup

    from ai_tools_core.utils.env import get_env
    api_key = get_env("OPENAI_API_KEY")
    ```
"""

import os
from typing import Optional, Dict, Any


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


def load_from_env(config_keys: Dict[str, Any]) -> Dict[str, Any]:
    """
    Load configuration from environment variables based on a configuration schema.

    This is a more flexible approach to loading configuration that allows for
    default values and type conversion.

    Args:
        config_keys: Dictionary mapping configuration keys to their default values or
                     tuples of (env_var_name, default_value, type_converter)

    Returns:
        Dictionary with configuration values loaded from environment variables

    Example:
        ```python
        config = load_from_env({
            "api_key": ("OPENAI_API_KEY", None, str),  # Required
            "model": ("OPENAI_MODEL", "gpt-4o-mini", str),  # Optional with default
            "max_tokens": ("MAX_TOKENS", 1000, int),  # With type conversion
            "log_level": "INFO",  # Simple default value
        })
        ```
    """
    result = {}

    for key, value in config_keys.items():
        if isinstance(value, tuple) and len(value) >= 2:
            # Handle tuple format (env_var_name, default_value, type_converter)
            env_var = value[0]
            default = value[1]
            converter = value[2] if len(value) > 2 else lambda x: x

            env_value = os.environ.get(env_var, default)
            if env_value is not None:
                try:
                    result[key] = converter(env_value)
                except Exception as e:
                    raise ValueError(f"Error converting {env_var}: {e}")
            elif default is None:
                raise ValueError(f"Required environment variable {env_var} is not set")
            else:
                result[key] = default
        else:
            # Handle simple default value
            result[key] = value

    return result


def get_openai_api_key() -> str:
    """Get OpenAI API key from environment variables."""
    return get_env("OPENAI_API_KEY")


def get_openai_model() -> str:
    """Get OpenAI model name from environment variables."""
    return get_env("OPENAI_MODEL", "gpt-4o-mini")


def get_log_level() -> str:
    """Get log level from environment variables."""
    return get_env("LOG_LEVEL", "INFO")


def get_openai_config() -> Dict[str, Any]:
    """Get OpenAI configuration from environment variables.

    Returns a dictionary with all OpenAI-related configuration.
    This is a more flexible approach than individual getter functions.

    Returns:
        Dictionary with OpenAI configuration
    """
    return load_from_env(
        {
            "api_key": ("OPENAI_API_KEY", None, str),
            "model": ("OPENAI_MODEL", "gpt-4o-mini", str),
            "temperature": ("OPENAI_TEMPERATURE", 0.7, float),
            "max_tokens": ("OPENAI_MAX_TOKENS", 1000, int),
        }
    )
