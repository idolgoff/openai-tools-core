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
    PROJECT_TOOLS,
    get_project_tool_schemas
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
                
                if function_name in PROJECT_TOOLS:
                    try:
                        # Execute the tool
                        result = PROJECT_TOOLS[function_name](**function_args)
                        
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
                        tool_response = generate_nl_response(function_name, function_args, result)
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


def generate_nl_response(tool_name: str, args: Dict[str, Any], result: Optional[Union[str, Dict]]) -> str:
    """
    Generate a natural language response based on the tool result.
    
    Args:
        tool_name: Name of the executed tool
        args: Tool arguments
        result: Tool execution result
        
    Returns:
        Natural language response
    """
    if result is None:
        if tool_name == "list_projects_tool":
            return "You don't have any projects yet. Would you like to create one?"
        elif tool_name == "delete_project_tool":
            return f"I couldn't find a project with ID {args.get('project_id')}."
        elif tool_name == "switch_project_tool":
            return f"I couldn't find a project with ID {args.get('project_id')}."
        elif tool_name == "get_project_details_tool":
            return f"I couldn't find a project with ID {args.get('project_id')}."
        elif tool_name == "get_active_project_tool":
            return "There is no active project. Would you like to create one or switch to an existing one?"
        else:
            return "I couldn't complete that action. Please try again."
    
    if tool_name == "list_projects_tool":
        return f"Here are your projects:\n\n{result}"
    elif tool_name == "delete_project_tool":
        return result
    elif tool_name == "switch_project_tool":
        return result
    elif tool_name == "create_project_tool":
        return f"I've created a new project with ID: {result}"
    elif tool_name == "get_project_details_tool":
        if isinstance(result, dict):
            active_status = " (ACTIVE)" if result.get("is_active") else ""
            return f"Project details:{active_status}\nID: {result.get('id')}\nName: {result.get('name')}\nDescription: {result.get('description')}"
        return str(result)
    elif tool_name == "get_active_project_tool":
        if isinstance(result, dict):
            return f"Your active project is:\nID: {result.get('id')}\nName: {result.get('name')}\nDescription: {result.get('description')}"
        return str(result)
    else:
        return str(result)
