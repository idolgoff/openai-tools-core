# 🚀 AI Tools Core: Python Toolkit for OpenAI Function Calling & LLM Applications

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://img.shields.io/pypi/v/ai-tools-core.svg)](https://pypi.org/project/ai-tools-core/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-brightgreen.svg)](https://conventionalcommits.org)
[![OpenAI API](https://img.shields.io/badge/OpenAI%20API-Compatible-brightgreen.svg)](https://platform.openai.com/)
[![Telegram Bot API](https://img.shields.io/badge/Telegram%20Bot%20API-Compatible-blue.svg)](https://core.telegram.org/bots/api)

A comprehensive Python toolkit for developers building AI-powered applications with OpenAI, ChatGPT, and other Large Language Models (LLMs). This package provides essential infrastructure for OpenAI function calling, conversation history management, token usage tracking, and AI service integration to accelerate your AI development workflow.

## ✨ Key Features

- 🔧 **OpenAI Function Calling**: Seamlessly register, validate, and execute AI tools with OpenAI's function calling API
- 🧠 **LLM Integration**: Connect with OpenAI GPT models and other AI services with robust error handling
- 📊 **Conversation History**: Track and manage multi-turn conversations with proper tool call handling
- 💰 **Token Usage Tracking**: Monitor and analyze token consumption with flexible billing integration
- 📝 **Structured Logging**: Comprehensive logging system for debugging and monitoring AI interactions
- 🔄 **Development Mode**: Rapid iteration with auto-reloading development server
- 🤖 **Telegram Bot Example**: Production-ready reference implementation showing real-world application

## 📦 Package Structure

The project is organized as a proper Python package for easy installation and reuse:

```text
ai_tools_core/           # Core package
├── __init__.py          # Public API exports
├── tools.py             # Tool registry implementation
├── logger.py            # Logging utilities
├── cli/                 # Command-line interface
├── history/             # Conversation history management
├── services/            # AI service integrations
└── utils/               # Utility functions
```

### Installation

#### From PyPI (Recommended)

Once published, you can install the package directly from PyPI:

```bash
# Basic installation
pip install ai-tools-core

# With development dependencies
pip install ai-tools-core[dev]

# With Telegram bot integration
pip install ai-tools-core[telegram]
```

#### From Repository

You can also install the package directly from the repository:

```bash
pip install -e .
```

Or with extra dependencies:

```bash
# For development
pip install -e ".[dev]"

# For Telegram bot integration
pip install -e ".[telegram]"
```

## 🛠️ Why Use AI Tools Core?

Building applications with OpenAI and other LLMs presents unique challenges that this toolkit solves:

- **OpenAI Function Calling Made Easy**: Simplifies the complex process of implementing OpenAI's function calling API
- **Token Efficiency**: Optimized conversation management to reduce token usage and costs
- **Production-Ready Architecture**: Battle-tested components used in real-world applications
- **Flexible Integration**: Works with multiple AI providers (OpenAI, Anthropic, etc.) through a unified interface
- **Modular Design**: Use only the components you need for your specific application
- **Best Practices Built-In**: Implements industry standards for AI safety, error handling, and performance
- **Developer Experience**: Rapid development with hot-reloading and comprehensive debugging tools

## 🚦 Getting Started

### Prerequisites

- Python 3.8+
- OpenAI API Key
- Telegram Bot Token (optional, only for the bot example)

### Basic Usage

After installation, you can import and use the package in your Python code:

```python
# Import core components
from ai_tools_core import ToolRegistry, get_logger
from ai_tools_core.services import get_openai_service
from ai_tools_core.history import get_history_manager, MessageRole

# Create a tool registry
registry = ToolRegistry()

# Register a tool
@registry.register()
def hello_world(name: str) -> str:
    """Say hello to someone."""
    return f"Hello, {name}!"

# Use the OpenAI service
openai_service = get_openai_service()
response = openai_service.generate_response([
    {"role": "user", "content": "Tell me a joke"}
])
print(response)
```

### Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/ai-tools-playground.git
   cd ai-tools-playground
   ```

2. Create a virtual environment:

   ```bash
   python -m venv .venv
   ```

3. Activate the virtual environment:
   - Windows: `.venv\Scripts\activate`
   - macOS/Linux: `source .venv/bin/activate`

4. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

5. Create a `.env` file with your configuration:

   ```env
   OPENAI_API_KEY=your_openai_api_key
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   LOG_LEVEL=INFO
   ```

6. Run the application:

   ```bash
   python src/main.py
   ```

## 🎮 How to Use AI Tools Core

This toolkit is designed to be modular and flexible. Here are some ways to implement OpenAI function calling and build AI-powered applications:

### 1. Implementing OpenAI Function Calling

```python
from ai_tools_core import ToolRegistry, log_tool_execution

# Create a tool registry for OpenAI function calling
registry = ToolRegistry()

# Register a tool with the decorator pattern
@registry.register()
def get_weather(location: str, unit: str = "fahrenheit") -> str:
    """Get current weather information for a specific location.
    
    Args:
        location: City name or geographic location
        unit: Temperature unit (celsius or fahrenheit)
    
    Returns:
        Weather information including temperature and conditions
    """
    # In a real implementation, you would call a weather API
    return f"Weather for {location}: Sunny, 75°F"

# Execute a tool directly
result = registry.execute_tool("get_weather", location="New York")
print(result)  # Output: Weather for New York: Sunny, 75°F

# Get OpenAI-compatible function schemas for ChatGPT API
schemas = registry.get_openai_schemas()
```

### 2. Managing Conversation History

The toolkit includes a conversation history manager that properly handles tool calls:

```python
from ai_tools_core.history import get_history_manager, MessageRole

# Get the history manager
history_manager = get_history_manager()

# Create a new conversation
user_id = "user123"
conversation_id = history_manager.create_conversation(user_id)

# Add messages to the conversation
history_manager.add_message(conversation_id, MessageRole.SYSTEM, 
                          "You are a helpful assistant.")
history_manager.add_message(conversation_id, MessageRole.USER, 
                          "What's the weather in New York?")

# Format messages for OpenAI
from ai_tools_core.history import create_message_formatter
formatter = create_message_formatter("openai")
openai_messages = formatter.format_messages(conversation)
```

### 3. Integrating with OpenAI and Other LLM Services

```python
from ai_tools_core.services import get_openai_service, get_tool_service
from ai_tools_core.usage import InMemoryUsageTracker

# Create a usage tracker to monitor token consumption
usage_tracker = InMemoryUsageTracker()

# Get the OpenAI service with token tracking
openai_service = get_openai_service(usage_tracker=usage_tracker)

# Generate a response with GPT-4o or other models
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Tell me a joke about programming."}
]
response = openai_service.generate_response(
    messages,
    user_id="user123",  # Optional tracking identifier
    session_id="session456"  # Optional session tracking
)
print(response)

# Process messages with OpenAI function calling
tool_service = get_tool_service()
tools = registry.get_openai_schemas()
response = tool_service.process_with_tools(messages, tools)

# Get token usage statistics
usage_stats = usage_tracker.get_current_usage()
print(f"Total tokens used: {usage_stats['total_tokens']}")
```

### 4. Example: Building a Telegram Bot

The toolkit includes a reference implementation of a Telegram bot that demonstrates how to use all the components together:

```python
from ai_tools_core import ToolRegistry
from ai_tools_core.services import get_openai_service
from bot.telegram_bot import create_bot

# Create your tools
registry = ToolRegistry()
@registry.register()
def hello_world(name: str) -> str:
    return f"Hello, {name}!"

# Create the bot with your tools
bot = create_bot(registry)
bot.run()
```

## 💻 Development Mode

For faster development iterations:

```bash
python dev.py
```

This starts the server with hot-reload capability, automatically restarting when you make changes to the code.

## 📂 Project Structure

```bash
ai-tools-core/
├── .env                  # Environment variables (not in repo)
├── .env.example          # Example environment variables
├── README.md             # Project documentation
├── progress.md           # Project progress tracking
├── pyproject.toml        # Package configuration
├── setup.py              # Package setup script
└── src/
    ├── ai_tools_core/    # Core package
    │   ├── __init__.py   # Package exports
    │   ├── tools.py      # Tool registry implementation
    │   ├── logger.py     # Logging utilities
    │   ├── cli/          # Command-line interface
    │   ├── history/      # Conversation history management
    │   ├── services/     # AI service integrations
    │   └── utils/        # Utility functions
    ├── bot/              # Example Telegram bot
    │   ├── telegram_bot.py  # Bot implementation
    │   └── handlers.py      # Message handlers
    └── main.py           # Example application entry point
```

## 📊 Token Usage Tracking and Billing

AI Tools Core includes a flexible system for tracking token usage and integrating with your own billing systems:

```python
from ai_tools_core.usage import UsageTracker, UsageEvent
from ai_tools_core.services import get_openai_service

# Create a custom usage tracker for your billing system
class MyBillingTracker(UsageTracker):
    def track_usage(self, event: UsageEvent) -> None:
        # Log the usage event
        print(f"Model: {event.model}, Tokens: {event.input_tokens + event.output_tokens}")
        print(f"Cost estimate: ${self.calculate_cost(event)}")
        
        # In a real implementation, you would store this in a database
        # or send it to your billing service
        
    def calculate_cost(self, event: UsageEvent) -> float:
        # Example pricing (adjust based on actual OpenAI pricing)
        rates = {
            "gpt-4o": {"input": 0.00001, "output": 0.00003},
            "gpt-4o-mini": {"input": 0.000005, "output": 0.000015},
        }
        
        model_rates = rates.get(event.model, rates["gpt-4o-mini"])
        input_cost = event.input_tokens * model_rates["input"]
        output_cost = event.output_tokens * model_rates["output"]
        
        return input_cost + output_cost
        
    def get_current_usage(self, **kwargs) -> dict:
        # Return usage statistics
        return {"total_tokens": 1000, "estimated_cost": 0.02}

# Use your custom tracker with the OpenAI service
tracker = MyBillingTracker()
service = get_openai_service(usage_tracker=tracker)

# Now all API calls will be tracked through your billing system
```

## 📚 Learn More

- [OpenAI Function Calling Documentation](https://platform.openai.com/docs/guides/function-calling)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [OpenAI Tokenizer](https://platform.openai.com/tokenizer)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Python Telegram Bot Library](https://python-telegram-bot.readthedocs.io/)

## ❓ Troubleshooting

### Common Issues

#### ImportError: No module named 'ai_tools_core'

Make sure the package is properly installed. Try reinstalling with:

```bash
pip uninstall ai-tools-core
pip install ai-tools-core
```

#### OpenAI API Key Issues

If you encounter errors related to the OpenAI API key:

1. Check that your API key is correctly set in the `.env` file
2. Verify that your API key has sufficient credits
3. Ensure you're using the correct environment variable name: `OPENAI_API_KEY`

#### Tool Execution Errors

If tools are failing to execute:

1. Check the logs for detailed error messages
2. Verify that tool parameters match the expected types
3. Ensure the tool is properly registered in the registry

#### Module Not Found When Using Entry Points

If you encounter issues with the `ai-tools` command:

1. Make sure the package is installed in the active Python environment
2. Try reinstalling with `pip install -e .` from the repository root
3. Verify that your PATH includes the Python scripts directory

## 📄 License

MIT

## 🔍 SEO Keywords

- OpenAI function calling Python
- ChatGPT API toolkit
- GPT-4 function calling implementation
- LLM application framework
- AI conversation management
- OpenAI token usage tracking
- AI tools registry Python
- Telegram ChatGPT bot example
- OpenAI API Python wrapper
- AI development toolkit

## 🎗️ Badge Information

| Badge | Description |
| ----- | ----------- |
| [![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/) | Indicates Python version compatibility |
| [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) | Project is released under the MIT license |
| [![PyPI version](https://img.shields.io/pypi/v/ai-tools-core.svg)](https://pypi.org/project/ai-tools-core/) | Current version on PyPI |
| [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) | Code is formatted with Black (line length 120) |
| [![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-brightgreen.svg)](https://conventionalcommits.org) | We use Conventional Commits format |
| [![OpenAI API](https://img.shields.io/badge/OpenAI%20API-Compatible-brightgreen.svg)](https://platform.openai.com/) | Compatible with the latest OpenAI API |
| [![Telegram Bot API](https://img.shields.io/badge/Telegram%20Bot%20API-Compatible-blue.svg)](https://core.telegram.org/bots/api) | Compatible with the Telegram Bot API |

---

⭐ If you find this project helpful, please star it on GitHub! ⭐
