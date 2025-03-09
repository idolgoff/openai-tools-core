"""Telegram bot implementation for OpenAI tools playground."""
import logging
from typing import Dict, Any, Callable, Awaitable

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from src.core.logger import get_logger
from src.utils.env import get_telegram_token

# Get logger for this module
logger = get_logger(__name__)


class TelegramBot:
    """Telegram bot implementation for OpenAI tools playground."""
    
    def __init__(self):
        """Initialize the Telegram bot."""
        self.token = get_telegram_token()
        self.application = Application.builder().token(self.token).build()
        
        # Register handlers
        self._register_handlers()
        
        logger.info("Telegram bot initialized")
    
    def _register_handlers(self) -> None:
        """Register command and message handlers."""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self._start_command))
        self.application.add_handler(CommandHandler("help", self._help_command))
        
        # Message handler for text messages
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
        
        # Error handler
        self.application.add_error_handler(self._error_handler)
    
    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command."""
        user = update.effective_user
        logger.info(f"User {user.id} ({user.username}) started the bot")
        
        await update.message.reply_text(
            f"Hello {user.first_name}! I'm your AI Tools Playground bot. "
            f"You can interact with me using natural language to manage projects "
            f"and test AI tools. Type /help to see available commands."
        )
    
    async def _help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command."""
        help_text = (
            "Here's what you can do with this bot:\n\n"
            "- List all projects\n"
            "- Create a new project\n"
            "- Delete a project\n"
            "- Switch to a different project\n"
            "- Get details about a project\n\n"
            "Just ask me in natural language, for example:\n"
            "\"Show me all projects\"\n"
            "\"Create a new project called 'Test' with description 'A test project'\"\n"
            "\"Delete project with ID abc123\"\n"
            "\"Switch to project xyz789\"\n"
            "\"What's the active project?\""
        )
        
        await update.message.reply_text(help_text)
    
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle incoming text messages.
        
        This method processes natural language messages and routes them to the appropriate
        handler based on the intent detected by the NLP processing layer.
        """
        user = update.effective_user
        message_text = update.message.text
        
        logger.info(f"Received message from {user.id} ({user.username}): {message_text}")
        
        # Process message with NLP to determine intent
        from src.bot.handlers import process_message
        response = await process_message(message_text)
        
        # Send response back to user
        await update.message.reply_text(response)
    
    async def _error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle errors in the telegram bot."""
        logger.error(f"Error occurred: {context.error}")
        
        # Send error message to user if update is available
        if isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(
                "Sorry, an error occurred while processing your request. Please try again later."
            )
    
    def run(self) -> None:
        """Run the bot."""
        logger.info("Starting Telegram bot")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)
