"""Main entry point for the OpenAI tools playground application."""
import asyncio
import signal
import sys
from typing import Dict, Any, Optional

from bot.telegram_bot import TelegramBot
from ai_tools_core.logger import get_logger
from ai_tools_core.utils.env import get_env

# Get logger for this module
logger = get_logger(__name__)


def setup_signal_handlers() -> None:
    """Set up signal handlers for graceful shutdown."""
    def signal_handler(sig, frame):
        logger.info("Received shutdown signal, exiting...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def main() -> None:
    """Main entry point for the application."""
    # Set up signal handlers
    setup_signal_handlers()
    
    logger.info("Starting OpenAI tools playground")
    
    try:
        # Initialize and run the Telegram bot
        bot = TelegramBot()
        bot.run()
    except Exception as e:
        logger.error(f"Error running application: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
