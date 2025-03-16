"""OpenAI service for interacting with the OpenAI API.

This module provides a service for interacting with the OpenAI API,
handling API calls, error handling, and response formatting.
"""

import json
import tiktoken
from typing import Dict, Any, List, Optional, Union

from openai import OpenAI

from ..logger import get_logger
from ..utils.env import get_openai_api_key, get_openai_model
from ..history.models import MessageRole
from ..usage import UsageEvent, UsageTracker, NoOpUsageTracker

# Get logger for this module
logger = get_logger(__name__)


class OpenAIService:
    """Service for interacting with the OpenAI API."""

    def __init__(self, usage_tracker: Optional[UsageTracker] = None):
        """Initialize the OpenAI service.

        Args:
            usage_tracker: Optional usage tracker for monitoring token consumption
        """
        self.client = OpenAI(api_key=get_openai_api_key())
        self.model = get_openai_model()
        self.usage_tracker = usage_tracker or NoOpUsageTracker()
        # Initialize tokenizer for the model
        try:
            # Try to get the specific model tokenizer
            self.tokenizer = tiktoken.encoding_for_model(self.model)
        except KeyError:
            # For models not directly supported by tiktoken (like gpt-4o-mini)
            if self.model.startswith("gpt-4o"):
                # Use cl100k_base for gpt-4o models
                self.tokenizer = tiktoken.get_encoding("cl100k_base")
                logger.info(f"Using cl100k_base tokenizer for {self.model}")
            elif self.model.startswith("gpt"):
                # Fallback for other GPT models
                self.tokenizer = tiktoken.get_encoding("cl100k_base")
                logger.info(f"Using cl100k_base tokenizer for {self.model}")
            else:
                # Default fallback
                self.tokenizer = tiktoken.get_encoding("cl100k_base")
                logger.info(f"Using default cl100k_base tokenizer for {self.model}")
        logger.info(f"OpenAI service initialized with model: {self.model}")

    def process_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Any:
        """
        Process messages with the OpenAI API using tools.

        Args:
            messages: List of messages in OpenAI format
            tools: List of tool schemas
            session_id: Optional session identifier for usage tracking
            user_id: Optional user identifier for usage tracking

        Returns:
            OpenAI API response
        """
        # Count input tokens before making the API call
        input_tokens = self.count_tokens(messages)

        try:
            response = self.client.chat.completions.create(
                model=self.model, messages=messages, tools=tools, tool_choice="auto"
            )

            # Extract usage information from response
            output_tokens = response.usage.completion_tokens if hasattr(response.usage, "completion_tokens") else 0

            # Create and track usage event
            event = UsageEvent(
                model=self.model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                request_type="tool_call" if response.choices[0].message.tool_calls else "chat",
                session_id=session_id,
                user_id=user_id,
                metadata={"tool_count": len(tools)},
            )
            self.usage_tracker.track_usage(event)

            return response
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}", exc_info=True)
            raise

    def generate_response(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: int = 300,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """
        Generate a natural language response from the OpenAI API.

        Args:
            messages: List of messages in OpenAI format
            max_tokens: Maximum number of tokens to generate
            session_id: Optional session identifier for usage tracking
            user_id: Optional user identifier for usage tracking

        Returns:
            Generated response text
        """
        # Count input tokens before making the API call
        input_tokens = self.count_tokens(messages)

        try:
            response = self.client.chat.completions.create(model=self.model, messages=messages, max_tokens=max_tokens)

            # Extract usage information from response
            output_tokens = response.usage.completion_tokens if hasattr(response.usage, "completion_tokens") else 0

            # Create and track usage event
            event = UsageEvent(
                model=self.model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                request_type="chat",
                session_id=session_id,
                user_id=user_id,
                metadata={"max_tokens": max_tokens},
            )
            self.usage_tracker.track_usage(event)

            return response.choices[0].message.content or "I processed your request."
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}", exc_info=True)
            return "I encountered an error while generating a response."

    def count_tokens(self, messages: List[Dict[str, Any]]) -> int:
        """
        Count the number of tokens in a list of messages.

        Args:
            messages: List of messages in OpenAI format

        Returns:
            Number of tokens in the messages
        """
        num_tokens = 0

        # Add tokens for each message
        for message in messages:
            # Add tokens for role
            num_tokens += 4  # Every message follows <im_start>{role/name}\n{content}<im_end>\n
            # Add tokens for content
            if "content" in message and message["content"]:
                num_tokens += self.tokenizer.encode(message["content"]).__len__()

            # Add tokens for name if present
            if "name" in message:
                num_tokens += self.tokenizer.encode(message["name"]).__len__()

            # Add tokens for tool calls if present
            if "tool_calls" in message:
                for tool_call in message["tool_calls"]:
                    # Add tokens for function name
                    if "function" in tool_call:
                        function = tool_call["function"]
                        if "name" in function:
                            num_tokens += self.tokenizer.encode(function["name"]).__len__()
                        if "arguments" in function:
                            # Arguments are usually JSON strings
                            num_tokens += self.tokenizer.encode(function["arguments"]).__len__()

        # Add tokens for the formatting of the messages
        num_tokens += 2  # Every reply is primed with <im_start>assistant\n

        return num_tokens

    def limit_messages_by_tokens(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: int,
        keep_system_messages: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Limit the number of messages to fit within a token budget, keeping the most recent messages.

        Args:
            messages: List of messages in OpenAI format
            max_tokens: Maximum number of tokens to allow
            keep_system_messages: Whether to always keep system messages regardless of age

        Returns:
            Limited list of messages
        """
        if not messages:
            return []

        # Count tokens in the current messages
        total_tokens = self.count_tokens(messages)

        # If we're already under the limit, return all messages
        if total_tokens <= max_tokens:
            return messages

        # Separate system messages if we need to keep them
        system_messages = []
        other_messages = []

        if keep_system_messages:
            for msg in messages:
                if msg.get("role") == "system":
                    system_messages.append(msg)
                else:
                    other_messages.append(msg)
        else:
            other_messages = messages.copy()

        # Check if system messages alone exceed the token limit
        system_tokens = self.count_tokens(system_messages)
        if system_tokens > max_tokens:
            logger.warning(f"System messages alone exceed token limit ({system_tokens} > {max_tokens})")
            # Keep only the most recent system messages if they exceed the limit
            while system_messages and self.count_tokens(system_messages) > max_tokens:
                system_messages.pop(0)

        # Start removing older messages (from the beginning) until we're under the limit
        limited_messages = other_messages.copy()

        while limited_messages and self.count_tokens(system_messages + limited_messages) > max_tokens:
            # Remove the oldest message
            limited_messages.pop(0)

        # Combine system messages with the limited messages
        result = system_messages + limited_messages

        logger.info(f"Limited messages from {len(messages)} to {len(result)} to fit within {max_tokens} tokens")
        return result


# Singleton instance
_openai_service: Optional[OpenAIService] = None


def get_openai_service(usage_tracker: Optional[UsageTracker] = None) -> OpenAIService:
    """
    Get the singleton OpenAI service instance.

    Args:
        usage_tracker: Optional usage tracker for monitoring token consumption

    Returns:
        OpenAI service instance
    """
    global _openai_service

    if _openai_service is None:
        _openai_service = OpenAIService(usage_tracker=usage_tracker)
    elif usage_tracker is not None:
        # Update the usage tracker if provided
        _openai_service.usage_tracker = usage_tracker

    return _openai_service
