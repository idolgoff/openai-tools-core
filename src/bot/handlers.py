"""Message handlers for the Telegram bot."""

import json
from typing import Dict, Any, Optional, List, Union

from core.logger import get_logger

# Import project tools and schemas
from bot.projects import (
    get_project_tools,
    get_project_tool_schemas,
    generate_tool_response,
)

# Import services from core module
from core.services import get_openai_service, get_openai_message_service

# Get logger for this module
logger = get_logger(__name__)

# Get service instances
openai_service = get_openai_service()
openai_message_service = get_openai_message_service()


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
            # Process each tool call
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                tool_call_id = tool_call.id

                logger.info(
                    f"Tool call detected: {function_name} with args: {function_args}, id: {tool_call_id}"
                )

                # Store tool call in history
                openai_message_service.add_tool_call_message(
                    conversation_id, function_name, function_args, tool_call_id
                )

            # Process and execute each tool call
            structured_responses = []

            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                tool_call_id = tool_call.id

                # Get the project tools dictionary
                project_tools = get_project_tools()

                if function_name in project_tools:
                    try:
                        # Execute the tool
                        result = project_tools[function_name](**function_args)

                        # Store tool result in history
                        openai_message_service.add_tool_result_message(
                            conversation_id,
                            function_name,
                            function_args,
                            result,
                            tool_call_id,
                        )

                        # Get structured response data for this tool call
                        structured_response = generate_tool_response(
                            function_name, function_args, result
                        )
                        structured_responses.append(structured_response)

                    except Exception as e:
                        logger.error(f"Error executing tool {function_name}: {str(e)}")

                        # Store error in history
                        openai_message_service.add_tool_error_message(
                            conversation_id,
                            function_name,
                            function_args,
                            str(e),
                            tool_call_id,
                        )

                        # Add error to structured responses
                        error_response = {
                            "tool": function_name,
                            "status": "error",
                            "error": str(e),
                            "args": function_args,
                        }
                        structured_responses.append(error_response)
                else:
                    error_message = f"Unknown tool: {function_name}"
                    logger.error(error_message)

                    # Store error in history
                    openai_message_service.add_tool_error_message(
                        conversation_id,
                        function_name,
                        function_args,
                        error_message,
                        tool_call_id,
                    )

                    # Add unknown tool error to structured responses
                    error_response = {
                        "tool": function_name,
                        "status": "error",
                        "error": error_message,
                        "args": function_args,
                    }
                    structured_responses.append(error_response)

            # If we have structured responses, generate a single natural language response
            responses = []
            if structured_responses:
                # Add structured responses to history for the OpenAI model to use
                openai_message_service.add_system_message_with_tool_responses(
                    conversation_id, structured_responses
                )

                # Get updated conversation messages
                updated_messages = openai_message_service.get_conversation_messages(
                    conversation_id
                )

                # Generate a natural language response for all tools
                nl_content = openai_service.generate_response(updated_messages)
                responses = [nl_content]  # Single response for all tools

            # Combine all responses
            combined_response = "\n\n".join(responses)

            # Store final assistant response in history
            openai_message_service.add_assistant_message(conversation_id, combined_response)

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


# Note: The message handling logic has been moved to the OpenAIMessageService class
# and the OpenAI API interaction has been moved to the OpenAIService class
