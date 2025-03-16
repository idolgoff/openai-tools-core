"""Logging functionality for the application."""

import logging
import sys
from typing import Optional

import colorlog

# Import from the utils module that we need to copy over
try:
    from ai_tools_core.utils.env import get_log_level
except ImportError:
    # Fallback to the old location during transition
    from utils.env import get_log_level

# Create a color formatter
formatter = colorlog.ColoredFormatter(
    "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
    log_colors={
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "red,bg_white",
    },
)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name or __name__)

    # Set the log level from environment variable
    log_level_str = get_log_level().upper()
    # Remove any comments from the log level string
    if "#" in log_level_str:
        log_level_str = log_level_str.split("#")[0].strip()
    log_level = getattr(logging, log_level_str)
    logger.setLevel(log_level)

    # Only add a handler if the logger doesn't already have one
    if not logger.handlers:
        # Create a handler for console output
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)

        # Add the handler to the logger
        logger.addHandler(handler)

    return logger


def log_tool_execution(tool_name: str, args: dict, result: Optional[str]) -> None:
    """
    Log tool execution details.

    Args:
        tool_name: Name of the executed tool
        args: Tool arguments
        result: Tool execution result or None if execution failed
    """
    logger = get_logger("tools")

    # Format arguments for logging
    args_str = ", ".join(f"{k}={v}" for k, v in args.items())

    # Log tool execution
    if result is not None:
        # Truncate result if it's too long
        result_str = str(result)
        if len(result_str) > 100:
            result_str = result_str[:97] + "..."

        logger.info(f"Tool executed: {tool_name}({args_str}) -> {result_str}")
    else:
        logger.warning(f"Tool execution failed: {tool_name}({args_str})")
