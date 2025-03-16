# AI Tools Core

A comprehensive toolkit for building AI-powered applications. This package provides core functionality for tool registration, AI service integration, conversation history management, and more to accelerate your AI development workflow.

## Package Structure

```text
ai_tools_core/
├── cli/               # Command-line interface tools
├── history/           # Conversation history management
│   ├── formatters.py  # Message formatters for different AI providers
│   ├── manager.py     # Conversation history manager
│   ├── models.py      # Data models for conversations and messages
│   └── storage.py     # Storage backends for conversation history
├── services/          # AI service integrations
│   ├── openai_service.py        # OpenAI API integration
│   ├── openai_message_service.py # OpenAI message handling
│   └── tool_service.py          # Tool execution service
├── utils/             # Utility functions
│   └── env.py         # Environment variable utilities
├── tools.py           # Tool registry and implementations
└── logger.py          # Logging utilities
```

## Core Components

- **Tool Registry**: Register, validate, and execute AI tools with a unified interface
- **AI Service Integration**: Connect with OpenAI and other AI services with proper error handling
- **History Management**: Store and retrieve conversation history with multiple storage backends
- **Message Formatting**: Format messages for different AI providers (OpenAI, Anthropic)
- **Logging**: Structured logging with color formatting and tool execution tracking

## Installation

### From PyPI (Recommended)

Once published, you can install the package directly from PyPI:

```bash
# Basic installation
pip install ai-tools-core

# With development dependencies
pip install ai-tools-core[dev]

# With Telegram bot integration
pip install ai-tools-core[telegram]
```

### From Repository

You can also install the package directly from the repository:

```bash
# Install in development mode
pip install -e .

# Or install directly from the package directory
cd /path/to/ai_tools_core
pip install .
```

### Using uv (Fast Python Package Installer)

For faster installation, you can use [uv](https://github.com/astral-sh/uv), a modern Python package installer:

```bash
# Install uv if you don't have it
pip install uv

# Install the package using uv
uv pip install ai-tools-core

# Or install from the repository
uv pip install -e .
```

## Environment Configuration

The package uses environment variables for configuration. You can set these in your application or use a `.env` file in your project root.

**Required environment variables:**

```env
OPENAI_API_KEY=your_openai_api_key
```

**Optional environment variables:**

```env
OPENAI_MODEL=gpt-4o-mini  # Default model to use
LOG_LEVEL=INFO            # Logging level (DEBUG, INFO, WARNING, ERROR)
```

### Best Practices for Environment Variables

While the package provides utilities for environment variable handling, it's generally better to:

1. Configure your application to load environment variables at the application level, not within the package
2. Pass configuration explicitly to the package components when possible
3. Only use environment variables for development and testing; use more secure configuration methods for production

## Detailed Usage Examples

### Tool Registry

The `ToolRegistry` class provides a way to register and execute tools that can be used with AI models:

```python
from ai_tools_core import ToolRegistry

# Create a tool registry
registry = ToolRegistry()

# Register a simple tool with the decorator
@registry.register()
def calculate_sum(a: int, b: int) -> int:
    """Calculate the sum of two numbers."""
    return a + b

# Register a tool with custom name and description
@registry.register(name="multiply", description="Multiply two numbers together")
def multiply_numbers(a: int, b: int) -> int:
    return a * b

# Execute a tool by name with keyword arguments
result = registry.execute_tool("calculate_sum", a=5, b=3)
print(result)  # Output: 8

# Get OpenAI-compatible tool schemas
schemas = registry.get_openai_schemas()
```

### Conversation History Management

The history module provides a way to store and retrieve conversation history:

```python
from ai_tools_core.history import get_history_manager
from ai_tools_core.history import MessageRole

# Get the history manager (singleton)
history_manager = get_history_manager()

# Create a new conversation
user_id = "user123"
conversation_id = history_manager.create_conversation(user_id)

# Add messages to the conversation
history_manager.add_message(conversation_id, MessageRole.SYSTEM, 
                           "You are a helpful assistant.")
history_manager.add_message(conversation_id, MessageRole.USER, 
                           "Hello, how are you?")
history_manager.add_message(conversation_id, MessageRole.ASSISTANT, 
                           "I'm doing well, thank you for asking!")

# Get the conversation
conversation = history_manager.get_conversation(conversation_id)

# Format messages for OpenAI
from ai_tools_core.history import create_message_formatter
formatter = create_message_formatter("openai")
openai_messages = formatter.format_messages(conversation)

# List conversations for a user
conversations = history_manager.list_conversations(user_id)
```

### OpenAI Service Integration

The OpenAI service provides a way to interact with the OpenAI API:

```python
from ai_tools_core.services import get_openai_service
from ai_tools_core.services import get_tool_service

# Get the OpenAI service (singleton)
openai_service = get_openai_service()

# Generate a response
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Tell me a joke about programming."}
]
response = openai_service.generate_response(messages)
print(response)

# Process messages with tools
tool_service = get_tool_service()
tools = [...] # Your tool schemas
response = tool_service.process_with_tools(messages, tools)
```

### Logging

The logging module provides structured logging with color formatting:

```python
from ai_tools_core import get_logger, log_tool_execution

# Get a logger for your module
logger = get_logger(__name__)

# Log messages with different levels
logger.debug("This is a debug message")
logger.info("This is an info message")
logger.warning("This is a warning message")
logger.error("This is an error message")

# Log tool execution (automatically tracks execution time)
with log_tool_execution(logger, "calculate_sum", {"a": 5, "b": 3}):
    result = 5 + 3
```

## Advanced Usage

### Token Usage Tracking

The toolkit provides a flexible system for tracking token usage without implementing billing logic directly. This allows you to integrate with your own billing systems.

#### Basic Usage

```python
from ai_tools_core import get_openai_service
from ai_tools_core.usage import InMemoryUsageTracker

# Create a usage tracker
tracker = InMemoryUsageTracker()

# Create the OpenAI service with the tracker
service = get_openai_service(usage_tracker=tracker)

# Use the service as normal
response = service.process_with_tools(messages, tools)

# Get usage statistics
usage = tracker.get_current_usage()
print(f"Total tokens used: {usage['total_tokens']}")
```

#### Custom Implementation

To implement your own usage tracking system, create a class that implements the `UsageTracker` interface:

```python
from ai_tools_core.usage import UsageTracker, UsageEvent

class MyBillingTracker(UsageTracker):
    def __init__(self, api_key, billing_endpoint):
        self.api_key = api_key
        self.billing_endpoint = billing_endpoint
    
    def track_usage(self, event: UsageEvent) -> None:
        # Send usage data to your billing system
        requests.post(
            self.billing_endpoint,
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "timestamp": event.timestamp,
                "model": event.model,
                "input_tokens": event.input_tokens,
                "output_tokens": event.output_tokens,
                "total_tokens": event.input_tokens + event.output_tokens,
                "user_id": event.user_id
            }
        )
    
    def get_current_usage(self, user_id=None, **kwargs) -> Dict[str, Any]:
        # Fetch current usage from your billing system
        response = requests.get(
            f"{self.billing_endpoint}/summary",
            headers={"Authorization": f"Bearer {self.api_key}"},
            params={"user_id": user_id}
        )
        return response.json()
```

### Custom Storage Backends

You can create custom storage backends for conversation history:

```python
from ai_tools_core.history.storage import StorageBackend
from ai_tools_core.history.models import Conversation, ConversationSummary
from typing import List

class CustomStorageBackend(StorageBackend):
    def save_conversation(self, conversation: Conversation) -> None:
        # Implement your storage logic
        pass
        
    def get_conversation(self, conversation_id: str) -> Conversation:
        # Implement your retrieval logic
        pass
        
    def list_conversations(self, user_id: str) -> List[ConversationSummary]:
        # Implement your listing logic
        pass
```

## Example Applications

The toolkit can be used to build various AI-powered applications. Here are some examples:

### Command-Line Interface

```python
from ai_tools_core import ToolRegistry, get_logger
from ai_tools_core.services import get_openai_service
import argparse

def main():
    # Create a tool registry
    registry = ToolRegistry()
    
    # Register tools
    @registry.register()
    def echo(message: str) -> str:
        """Echo a message back to the user."""
        return message
    
    # Set up CLI
    parser = argparse.ArgumentParser(description="AI Tools CLI")
    parser.add_argument("message", help="Message to process")
    args = parser.parse_args()
    
    # Process with OpenAI
    service = get_openai_service()
    response = service.generate_response([
        {"role": "user", "content": args.message}
    ])
    print(response)

if __name__ == "__main__":
    main()
```

### Web API

```python
from fastapi import FastAPI
from pydantic import BaseModel
from ai_tools_core import ToolRegistry
from ai_tools_core.services import get_openai_service

app = FastAPI()
registry = ToolRegistry()

class Message(BaseModel):
    content: str

@app.post("/chat")
async def chat(message: Message):
    service = get_openai_service()
    response = service.generate_response([
        {"role": "user", "content": message.content}
    ])
    return {"response": response}
```

### Telegram Bot

A Telegram bot example is included in the repository to demonstrate how to use the toolkit in a real application.

```python
from ai_tools_core import ToolRegistry
from bot.telegram_bot import create_bot

# Create a tool registry
registry = ToolRegistry()

# Register tools
@registry.register()
def hello_world(name: str) -> str:
    """Say hello to someone."""
    return f"Hello, {name}!"

# Create and run the bot
bot = create_bot(registry)
bot.run()
```

### Custom Message Formatters

You can create custom message formatters for different AI providers:

```python
from ai_tools_core.history.formatters import MessageFormatter
from ai_tools_core.history.models import Conversation

class CustomMessageFormatter(MessageFormatter):
    def format_messages(self, conversation: Conversation) -> List[Dict[str, Any]]:
        # Implement your formatting logic
        formatted_messages = []
        for msg in conversation.messages:
            # Format each message
            formatted_messages.append({
                "role": msg.role.value,
                "content": msg.content
                # Add any other fields needed
            })
        return formatted_messages
```

## Best Practices

1. **Separation of Concerns**: Keep your business logic separate from the AI tools core
2. **Error Handling**: Always handle errors from AI services gracefully
3. **Token Management**: Be aware of token limits when working with AI models
4. **Security**: Never hardcode API keys; use environment variables or secure vaults
5. **Testing**: Write tests for your tools and services

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
