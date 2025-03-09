"""Message handlers for the Telegram bot."""
import json
from typing import Dict, Any, Optional, List, Union

import openai
from openai import OpenAI

from core.logger import get_logger, log_tool_execution
from core.tools import TOOLS
from core.history.manager import get_history_manager
from core.history.models import MessageRole
from utils.env import get_openai_api_key, get_openai_model

# Get logger for this module
logger = get_logger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=get_openai_api_key())

# Get history manager
history_manager = get_history_manager()


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
        # Define available tools for the OpenAI model
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "list_projects",
                    "description": "List all available projects",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_project",
                    "description": "Delete a project by ID",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "project_id": {
                                "type": "string",
                                "description": "ID of the project to delete"
                            }
                        },
                        "required": ["project_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "switch_project",
                    "description": "Switch to a project by ID",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "project_id": {
                                "type": "string",
                                "description": "ID of the project to switch to"
                            }
                        },
                        "required": ["project_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_project",
                    "description": "Create a new project",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Name of the project"
                            },
                            "description": {
                                "type": "string",
                                "description": "Description of the project"
                            }
                        },
                        "required": ["name", "description"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_project_details",
                    "description": "Get project details by ID",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "project_id": {
                                "type": "string",
                                "description": "ID of the project"
                            }
                        },
                        "required": ["project_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_active_project",
                    "description": "Get active project details",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        ]
        
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
            tool_call = response_message.tool_calls[0]
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            logger.info(f"Tool call detected: {function_name} with args: {function_args}")
            
            # Store tool call in history
            tool_call_content = f"Function: {function_name}\nArguments: {json.dumps(function_args, indent=2)}"
            history_manager.add_message(
                conversation_id, 
                MessageRole.TOOL, 
                tool_call_content,
                metadata={"function_name": function_name, "function_args": function_args}
            )
            
            # Execute the tool
            if function_name in TOOLS:
                result = TOOLS[function_name](**function_args)
                
                # Store tool result in history
                result_content = json.dumps(result) if isinstance(result, dict) else str(result)
                history_manager.add_message(
                    conversation_id,
                    MessageRole.TOOL,
                    f"Result: {result_content}",
                    metadata={"function_name": function_name, "result": result}
                )
                
                # Generate a natural language response based on the tool result
                nl_response = generate_nl_response(function_name, function_args, result)
                
                # Store final assistant response in history
                history_manager.add_message(conversation_id, MessageRole.ASSISTANT, nl_response)
                
                return nl_response
            else:
                error_msg = f"I'm sorry, I don't know how to perform that action: {function_name}"
                history_manager.add_message(conversation_id, MessageRole.ASSISTANT, error_msg)
                logger.warning(f"Unknown tool: {function_name}")
                return error_msg
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
        if tool_name == "list_projects":
            return "You don't have any projects yet. Would you like to create one?"
        elif tool_name == "delete_project":
            return f"I couldn't find a project with ID {args.get('project_id')}."
        elif tool_name == "switch_project":
            return f"I couldn't find a project with ID {args.get('project_id')}."
        elif tool_name == "get_project_details":
            return f"I couldn't find a project with ID {args.get('project_id')}."
        elif tool_name == "get_active_project":
            return "You don't have an active project. Would you like to create one or switch to an existing one?"
        else:
            return "I couldn't complete that action. Please try again."
    
    if tool_name == "list_projects":
        return f"Here are your projects:\n\n{result}"
    elif tool_name == "delete_project":
        return result
    elif tool_name == "switch_project":
        return result
    elif tool_name == "create_project":
        return f"I've created a new project with ID: {result}"
    elif tool_name == "get_project_details":
        if isinstance(result, dict):
            active_status = " (ACTIVE)" if result.get("is_active") else ""
            return f"Project details:{active_status}\nID: {result.get('id')}\nName: {result.get('name')}\nDescription: {result.get('description')}"
        return str(result)
    elif tool_name == "get_active_project":
        if isinstance(result, dict):
            return f"Your active project is:\nID: {result.get('id')}\nName: {result.get('name')}\nDescription: {result.get('description')}"
        return str(result)
    else:
        return str(result)
