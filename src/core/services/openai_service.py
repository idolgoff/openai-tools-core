"""OpenAI service for interacting with the OpenAI API.

This module provides a service for interacting with the OpenAI API,
handling API calls, error handling, and response formatting.
"""

import json
import tiktoken
from typing import Dict, Any, List, Optional, Union

from openai import OpenAI

from core.logger import get_logger
from utils.env import get_openai_api_key, get_openai_model

# Get logger for this module
logger = get_logger(__name__)


class OpenAIService:
    """Service for interacting with the OpenAI API."""

    def __init__(self):
        """Initialize the OpenAI service."""
        self.client = OpenAI(api_key=get_openai_api_key())
        self.model = get_openai_model()
        # Initialize tokenizer for the model
        self.tokenizer = (
            tiktoken.encoding_for_model(self.model)
            if self.model.startswith("gpt")
            else tiktoken.get_encoding("cl100k_base")
        )
        logger.info(f"OpenAI service initialized with model: {self.model}")

    def process_with_tools(
        self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]]
    ) -> Any:
        """
        Process messages with the OpenAI API using tools.

        Args:
            messages: List of messages in OpenAI format
            tools: List of tool schemas

        Returns:
            OpenAI API response
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model, messages=messages, tools=tools, tool_choice="auto"
            )
            return response
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}", exc_info=True)
            raise

    def generate_response(
        self, messages: List[Dict[str, Any]], max_tokens: int = 300
    ) -> str:
        """
        Generate a natural language response from the OpenAI API.

        Args:
            messages: List of messages in OpenAI format
            max_tokens: Maximum number of tokens to generate

        Returns:
            Generated response text
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model, messages=messages, max_tokens=max_tokens
            )
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
            num_tokens += (
                4  # Every message follows <im_start>{role/name}\n{content}<im_end>\n
            )
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
                            num_tokens += self.tokenizer.encode(
                                function["name"]
                            ).__len__()
                        if "arguments" in function:
                            # Arguments are usually JSON strings
                            num_tokens += self.tokenizer.encode(
                                function["arguments"]
                            ).__len__()

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

        # Start removing older messages (from the beginning) until we're under the limit
        limited_messages = other_messages.copy()

        while (
            limited_messages
            and self.count_tokens(system_messages + limited_messages) > max_tokens
        ):
            # Remove the oldest message
            limited_messages.pop(0)

        # Combine system messages with the limited messages
        result = system_messages + limited_messages

        logger.info(
            f"Limited messages from {len(messages)} to {len(result)} to fit within {max_tokens} tokens"
        )
        return result


# Singleton instance
_openai_service: Optional[OpenAIService] = None


def get_openai_service() -> OpenAIService:
    """
    Get the singleton OpenAI service instance.

    Returns:
        OpenAI service instance
    """
    global _openai_service

    if _openai_service is None:
        _openai_service = OpenAIService()

    return _openai_service
