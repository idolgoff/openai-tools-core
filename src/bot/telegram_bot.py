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

from ai_tools_core.logger import get_logger
from ai_tools_core.history import get_history_manager
from ai_tools_core.utils.env import get_telegram_token

# Get logger for this module
logger = get_logger(__name__)

# Get history manager
history_manager = get_history_manager()


class TelegramBot:
    """Telegram bot implementation for OpenAI tools playground."""
    
    def __init__(self):
        """Initialize the Telegram bot."""
        self.token = get_telegram_token()
        self.application = Application.builder().token(self.token).build()
        
        # Store active conversations for users
        self._user_conversations = {}
        
        # Register handlers
        self._register_handlers()
        
        logger.info("Telegram bot initialized")
    
    def _register_handlers(self) -> None:
        """Register command and message handlers."""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self._start_command))
        self.application.add_handler(CommandHandler("help", self._help_command))
        self.application.add_handler(CommandHandler("new_conversation", self._new_conversation_command))
        self.application.add_handler(CommandHandler("list_conversations", self._list_conversations_command))
        
        # Message handler for text messages
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
        
        # Error handler
        self.application.add_error_handler(self._error_handler)
    
    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command."""
        user = update.effective_user
        user_id = str(user.id)
        logger.info(f"User {user_id} ({user.username}) started the bot")
        
        # Create a new conversation for the user
        conversation_id = history_manager.create_conversation(user_id, {
            "username": user.username or "",
            "first_name": user.first_name or "",
            "last_name": user.last_name or ""
        })
        
        # Store the conversation ID for this user
        self._user_conversations[user_id] = conversation_id
        
        # Add system message to set the context
        history_manager.add_message(
            conversation_id,
            "system",
            "You are an AI assistant that helps users manage projects. "
            "Your task is to understand the user's intent and call the appropriate "
            "function to handle their request."
        )
        
        logger.info(f"Created new conversation {conversation_id} for user {user_id}")
        
        await update.message.reply_text(
            f"Hello {user.first_name}! I'm your AI Tools Playground bot. "
            f"You can interact with me using natural language to manage projects "
            f"and test AI tools. Type /help to see available commands."
        )
    
    async def _help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command."""
        help_text = (
            "Here's what you can do with this bot:\n\n"
            "Project Management:\n"
            "- List all projects\n"
            "- Create a new project\n"
            "- Delete a project\n"
            "- Switch to a different project\n"
            "- Get details about a project\n\n"
            "Conversation Management:\n"
            "- /new_conversation - Start a new conversation\n"
            "- /list_conversations - List your recent conversations\n\n"
            "Just ask me in natural language, for example:\n"
            "\"Show me all projects\"\n"
            "\"Create a new project called 'Test' with description 'A test project'\"\n"
            "\"Delete project with ID abc123\"\n"
            "\"Switch to project xyz789\"\n"
            "\"What's the active project?\""
        )
        
        await update.message.reply_text(help_text)
        
    async def _new_conversation_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /new_conversation command to start a new conversation."""
        user = update.effective_user
        user_id = str(user.id)
        
        # Create a new conversation for the user
        conversation_id = history_manager.create_conversation(user_id, {
            "username": user.username or "",
            "first_name": user.first_name or "",
            "last_name": user.last_name or ""
        })
        
        # Store the conversation ID for this user
        self._user_conversations[user_id] = conversation_id
        
        # Add system message to set the context
        history_manager.add_message(
            conversation_id,
            "system",
            "You are an AI assistant that helps users manage projects. "
            "Your task is to understand the user's intent and call the appropriate "
            "function to handle their request."
        )
        
        logger.info(f"Created new conversation {conversation_id} for user {user_id}")
        
        await update.message.reply_text(
            f"Started a new conversation! You can now interact with me using natural language."
        )
    
    async def _list_conversations_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /list_conversations command to list recent conversations."""
        user = update.effective_user
        user_id = str(user.id)
        
        # Get conversations for this user
        conversations = history_manager.list_conversations(user_id)
        
        if not conversations:
            await update.message.reply_text("You don't have any conversations yet.")
            return
        
        # Format conversation list
        conversation_text = "Your recent conversations:\n\n"
        
        for i, conv in enumerate(conversations[:5], 1):  # Show up to 5 recent conversations
            # Get first user message as a preview
            conversation = history_manager.get_conversation(conv.id)
            preview = ""
            
            if conversation and conversation.messages:
                for msg in conversation.messages:
                    if msg.role.value == "user":
                        preview = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
                        break
            
            conversation_text += f"{i}. {conv.last_message_at.strftime('%Y-%m-%d %H:%M')} - {preview}\n"
        
        # Add info about the current conversation
        current_conv_id = self._user_conversations.get(user_id)
        if current_conv_id:
            conversation_text += f"\nCurrent conversation ID: {current_conv_id}"
        
        await update.message.reply_text(conversation_text)
    
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle incoming text messages.
        
        This method processes natural language messages and routes them to the appropriate
        handler based on the intent detected by the NLP processing layer.
        """
        user = update.effective_user
        user_id = str(user.id)
        message_text = update.message.text
        
        logger.info(f"Received message from {user_id} ({user.username}): {message_text}")
        
        # Get or create conversation for this user
        conversation_id = self._user_conversations.get(user_id)
        
        # Process message with NLP to determine intent
        from bot.handlers import process_message
        response = await process_message(
            message=message_text,
            user_id=user_id,
            conversation_id=conversation_id
        )
        
        # If this is a new conversation, store the conversation ID
        if user_id not in self._user_conversations:
            # Find the most recent conversation for this user
            conversations = history_manager.list_conversations(user_id)
            if conversations:
                self._user_conversations[user_id] = conversations[0].id
                logger.info(f"Associated user {user_id} with existing conversation {conversations[0].id}")
        
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
