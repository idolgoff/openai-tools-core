"""Message handlers for the Telegram bot."""

import json
from typing import Dict, Any, Optional, List, Union

from core.logger import get_logger

# Import project tools and schemas
from bot.projects import (
    get_project_tools,
    get_project_tool_schemas,
)

# Import services from core module
from core.services import get_openai_service, get_openai_message_service, get_tool_service

# Get logger for this module
logger = get_logger(__name__)

# Get service instances
openai_service = get_openai_service()
openai_message_service = get_openai_message_service()
tool_service = get_tool_service()


async def process_message(
    message: str, user_id: str = "default_user", conversation_id: Optional[str] = None
) -> str:
    """
    Process a natural language message and execute the appropriate tool.

    Args:
        message: Natural language message from the user
        user_id: ID of the user sending the message
        conversation_id: Optional ID of the existing conversation

    Returns:
        Response message to send back to the user
    """
    logger.info(f"Processing message from user {user_id}: {message}")

    try:
        # Get or create conversation
        conversation_id = openai_message_service.create_or_get_conversation(
            user_id, conversation_id
        )

        # Add user message to history
        openai_message_service.add_user_message(conversation_id, message)

        # Get tool schemas from projects.py
        tools = get_project_tool_schemas()

        # Get conversation history for context
        messages = openai_message_service.get_conversation_messages(conversation_id)

        # Call OpenAI API to process the message
        response = openai_service.process_with_tools(messages, tools)

        # Extract the response content
        response_message = response.choices[0].message

        # Store assistant's response in history
        if response_message.content:
            openai_message_service.add_assistant_message(
                conversation_id, response_message.content
            )

        # Check if a tool call was made
        if response_message.tool_calls:
            logger.info(f"Processing {len(response_message.tool_calls)} tool calls")
            
            # Get the project tools dictionary
            project_tools = get_project_tools()
            
            # Use the tool service to process all tool calls
            # This handles executing tools, storing results in history, and generating responses
            combined_response = tool_service.process_tool_calls(
                conversation_id,
                response_message.tool_calls,
                project_tools,
                # Pass the response generator function
                lambda messages: openai_service.generate_response(messages)
            )
            
            return combined_response
        else:
            # No tool call was made, return the model's response
            response_content = (
                response_message.content or "I'm not sure how to help with that."
            )
            return response_content

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", exc_info=True)
        return "I encountered an error while processing your request. Please try again."


# Note: The message handling logic has been moved to the OpenAIMessageService class,
# the OpenAI API interaction has been moved to the OpenAIService class,
# and the tool execution logic has been moved to the ToolService class
