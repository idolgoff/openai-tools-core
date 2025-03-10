"""OpenAI service for interacting with the OpenAI API.

This module provides a service for interacting with the OpenAI API,
handling API calls, error handling, and response formatting.
"""

from typing import Dict, Any, List, Optional

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
