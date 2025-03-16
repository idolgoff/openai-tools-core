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
from ai_tools_core.services.openai_message_service import get_openai_message_service
from ai_tools_core.services.openai_service import get_openai_service
from bot.utils import get_telegram_token
from bot.billing import get_bot_billing_tracker

# Get logger for this module
logger = get_logger(__name__)

# Get history manager, message service, and billing tracker
history_manager = get_history_manager()
billing_tracker = get_bot_billing_tracker()

# Initialize OpenAI service with billing tracker
openai_service = get_openai_service(usage_tracker=billing_tracker)

# Get message service (will use the OpenAI service with billing tracker)
message_service = get_openai_message_service()


class TelegramBot:
    """Telegram bot implementation for OpenAI tools playground."""

    def __init__(self):
        """Initialize the Telegram bot."""
        self.token = get_telegram_token()
        self.application = Application.builder().token(self.token).build()

        # Store active conversations for users
        self._user_conversations = {}

        # Store active contexts for users
        self._user_contexts = {}

        # Register handlers
        self._register_handlers()

        logger.info("Telegram bot initialized")

    def _register_handlers(self) -> None:
        """Register command and message handlers."""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self._start_command))
        self.application.add_handler(CommandHandler("help", self._help_command))
        self.application.add_handler(CommandHandler("new_conversation", self._new_conversation_command))
        self.application.add_handler(CommandHandler("usage", self._usage_command))
        self.application.add_handler(CommandHandler("list_conversations", self._list_conversations_command))

        # Context management commands
        self.application.add_handler(CommandHandler("set_context", self._set_context_command))
        self.application.add_handler(CommandHandler("get_context", self._get_context_command))
        self.application.add_handler(CommandHandler("clear_context", self._clear_context_command))

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
        conversation_id = history_manager.create_conversation(
            user_id,
            {"username": user.username or "", "first_name": user.first_name or "", "last_name": user.last_name or ""},
        )

        # Store the conversation ID for this user
        self._user_conversations[user_id] = conversation_id

        # Add system message to set the context
        history_manager.add_message(
            conversation_id,
            "system",
            "You are an AI assistant that helps users manage projects. "
            "Your task is to understand the user's intent and call the appropriate "
            "function to handle their request.",
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
            "Context Management:\n"
            "- /set_context <context> - Set a context for the current conversation\n"
            "- /get_context - Show the current context\n"
            "- /clear_context - Clear the current context\n\n"
            "Usage Tracking:\n"
            "- /usage - Check your token usage and billing information\n\n"
            "Just ask me in natural language, for example:\n"
            '"Show me all projects"\n'
            "\"Create a new project called 'Test' with description 'A test project'\"\n"
            '"Delete project with ID abc123"\n'
            '"Switch to project xyz789"\n'
            '"What\'s the active project?"'
        )

        await update.message.reply_text(help_text)

    async def _new_conversation_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /new_conversation command to start a new conversation."""
        user = update.effective_user
        user_id = str(user.id)

        # Create a new conversation for the user
        conversation_id = history_manager.create_conversation(
            user_id,
            {"username": user.username or "", "first_name": user.first_name or "", "last_name": user.last_name or ""},
        )

        # Store the conversation ID for this user
        self._user_conversations[user_id] = conversation_id

        # Add system message to set the context
        history_manager.add_message(
            conversation_id,
            "system",
            "You are an AI assistant that helps users manage projects. "
            "Your task is to understand the user's intent and call the appropriate "
            "function to handle their request.",
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

        # Get the active context for this user
        context = self._user_contexts.get(user_id)

        # Process message with NLP to determine intent
        from bot.handlers import process_message

        response = await process_message(
            message=message_text, user_id=user_id, conversation_id=conversation_id, context=context
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

    async def _set_context_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /set_context command to set a context for the current conversation."""
        user = update.effective_user
        user_id = str(user.id)

        # Get the context text from the command arguments
        context_text = update.message.text.replace("/set_context", "", 1).strip()

        if not context_text:
            await update.message.reply_text("Please provide a context text. Usage: /set_context <context>")
            return

        # Get the current conversation ID
        conversation_id = self._user_conversations.get(user_id)
        if not conversation_id:
            await update.message.reply_text("You don't have an active conversation. Start one with /new_conversation")
            return

        # Set the context
        success = message_service.set_conversation_context(conversation_id, context_text)

        if success:
            # Store the context for this user
            self._user_contexts[user_id] = context_text

            await update.message.reply_text(f"Context set: {context_text}")
            logger.info(f"Set context for user {user_id}: {context_text}")
        else:
            await update.message.reply_text("Failed to set context. Please try again.")

    async def _get_context_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /get_context command to show the current context."""
        user = update.effective_user
        user_id = str(user.id)

        # Get the current conversation ID
        conversation_id = self._user_conversations.get(user_id)
        if not conversation_id:
            await update.message.reply_text("You don't have an active conversation. Start one with /new_conversation")
            return

        # Get the context
        context_text = message_service.get_conversation_context(conversation_id)

        if context_text:
            await update.message.reply_text(f"Current context: {context_text}")
        else:
            await update.message.reply_text("No context is set for the current conversation.")

    async def _clear_context_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /clear_context command to clear the current context."""
        user = update.effective_user
        user_id = str(user.id)

        # Get the current conversation ID
        conversation_id = self._user_conversations.get(user_id)
        if not conversation_id:
            await update.message.reply_text("You don't have an active conversation. Start one with /new_conversation")
            return

        # Clear the context
        success = message_service.clear_conversation_context(conversation_id)

        if success:
            # Remove the context for this user
            if user_id in self._user_contexts:
                del self._user_contexts[user_id]

            await update.message.reply_text("Context cleared.")
            logger.info(f"Cleared context for user {user_id}")
        else:
            await update.message.reply_text("Failed to clear context. Please try again.")

    async def _usage_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /usage command to check token usage and billing information."""
        user = update.effective_user
        user_id = str(user.id)

        # Get user's conversation ID if available
        conversation_id = self._user_conversations.get(user_id)

        # Get usage statistics from the billing tracker
        usage_stats = billing_tracker.get_current_usage(user_id=user_id)

        # Get detailed billing report if available
        billing_report = billing_tracker.get_user_billing_report(user_id)

        # Format the usage message
        usage_text = (
            f"📊 *Usage Statistics for {user.first_name}*\n\n"
            f"Total tokens used: {usage_stats['total_tokens']:,}\n"
            f"Estimated cost: ${usage_stats['total_cost']:.4f} USD\n"
            f"Number of API calls: {usage_stats['event_count']}\n\n"
        )

        # Add daily usage breakdown if available
        if billing_report.get("daily_usage"):
            usage_text += "*Daily Usage:*\n"
            for date, data in sorted(billing_report["daily_usage"].items()):
                usage_text += f"- {date}: {data['tokens']:,} tokens (${data['cost']:.4f})\n"

        # Add conversation usage if available
        if conversation_id:
            session_usage = billing_tracker.get_current_usage(session_id=conversation_id)
            if session_usage.get("total_tokens", 0) > 0:
                usage_text += f"\n*Current Conversation:*\n"
                usage_text += f"Tokens used: {session_usage['total_tokens']:,}\n"
                usage_text += f"Estimated cost: ${session_usage['total_cost']:.4f} USD\n"

        await update.message.reply_text(usage_text, parse_mode="Markdown")

    def run(self) -> None:
        """Run the bot."""
        logger.info("Starting Telegram bot")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)
