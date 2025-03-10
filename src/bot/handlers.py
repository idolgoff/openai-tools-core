"""Message handlers for the Telegram bot."""
import json
from typing import Dict, Any, Optional, List, Union

import openai
from openai import OpenAI

from core.logger import get_logger, log_tool_execution
from core.tools import ToolRegistry
from core.history.manager import get_history_manager
from core.history.models import MessageRole
from utils.env import get_openai_api_key, get_openai_model

# Import project tools and schemas
from bot.projects import (
    get_project_tools,
    get_project_tool_schemas,
    generate_tool_response
)

# Get logger for this module
logger = get_logger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=get_openai_api_key())

# Get history manager
history_manager = get_history_manager()

# We don't need to create a tool registry here as we're using the one from projects.py


async def process_message(message: str, user_id: str = "default_user", conversation_id: Optional[str] = None) -> str:
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
        if not conversation_id:
            conversation_id = history_manager.create_conversation(user_id)
            # Add system message to set the context
            history_manager.add_message(
                conversation_id,
                MessageRole.SYSTEM,
                "You are an AI assistant that helps users manage projects. "
                "Your task is to understand the user's intent and call the appropriate "
                "function to handle their request."
            )
        
        # Add user message to history
        history_manager.add_message(conversation_id, MessageRole.USER, message)
        # No need to register tools here as they're already registered in projects.py
        
        # Use the tools exported from projects.py
        
        # Get tool schemas from projects.py
        tools = get_project_tool_schemas()
        
        # Get conversation history for context
        messages = history_manager.get_messages(conversation_id)
        
        # Call OpenAI API to process the message
        response = client.chat.completions.create(
            model=get_openai_model(),
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        
        # Extract the response content
        response_message = response.choices[0].message
        
        # Store assistant's response in history
        if response_message.content:
            history_manager.add_message(conversation_id, MessageRole.ASSISTANT, response_message.content)
        
        # Check if a tool call was made
        if response_message.tool_calls:
            # Process each tool call
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                tool_call_id = tool_call.id
                
                logger.info(f"Tool call detected: {function_name} with args: {function_args}, id: {tool_call_id}")
                
                # Store tool call in history
                tool_call_content = f"Function: {function_name}\nArguments: {json.dumps(function_args, indent=2)}"
                history_manager.add_message(
                    conversation_id, 
                    MessageRole.TOOL, 
                    tool_call_content,
                    metadata={
                        "name": function_name,  # Changed from function_name to name for consistency
                        "arguments": function_args,
                        "tool_call_id": tool_call_id
                    }
                )
            
            # Process and execute each tool call
            responses = []
            
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
                        
                        # Format the result
                        result_content = json.dumps(result) if isinstance(result, dict) else str(result)
                        
                        # Store tool result in history
                        history_manager.add_message(
                            conversation_id,
                            MessageRole.TOOL,
                            result_content,
                            metadata={
                                "name": function_name,
                                "arguments": function_args,
                                "result": result,
                                "tool_call_id": tool_call_id
                            }
                        )
                        
                        # Generate a natural language response for this tool call
                        tool_response = generate_tool_response(function_name, function_args, result)
                        responses.append(tool_response)
                    except Exception as e:
                        logger.error(f"Error executing tool {function_name}: {str(e)}")
                        error_result = f"Error: {str(e)}"
                        
                        # Store error in history
                        history_manager.add_message(
                            conversation_id,
                            MessageRole.TOOL,
                            error_result,
                            metadata={
                                "name": function_name,
                                "arguments": function_args,
                                "error": str(e),
                                "tool_call_id": tool_call_id
                            }
                        )
                        
                        responses.append(f"Error executing {function_name}: {str(e)}")
                else:
                    error_msg = f"Unknown tool: {function_name}"
                    logger.warning(error_msg)
                    responses.append(error_msg)
            
            # Combine all responses
            combined_response = "\n\n".join(responses)
            
            # Store final assistant response in history
            history_manager.add_message(conversation_id, MessageRole.ASSISTANT, combined_response)
            
            return combined_response
        else:
            # No tool call was made, return the model's response
            response_content = response_message.content or "I'm not sure how to help with that."
            return response_content
    
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", exc_info=True)
        return "I encountered an error while processing your request. Please try again."


# The generate_nl_response function has been moved to projects.py as generate_tool_response
