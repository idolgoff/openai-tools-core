# 🚀 AI Tools Core: Toolkit for Building AI-Powered Applications

A comprehensive toolkit for developers building applications with AI services like OpenAI. This package provides core functionality for tool registration, conversation management, and AI service integration to accelerate your AI development workflow.

## ✨ Key Features

- 🔧 **Tool Registry System**: Register, validate, and execute AI tools with a unified interface
- 🧠 **AI Service Integration**: Connect with OpenAI and other AI services with proper error handling
- 📊 **Conversation History Management**: Track and analyze AI interactions with proper tool call handling
- 📝 **Comprehensive Logging**: Monitor tool execution with detailed, non-duplicative logs
- 🔄 **Hot Reload Development**: Rapid iteration with auto-reloading development server
- 🤖 **Example Telegram Bot**: Reference implementation showing how to use the toolkit in a real application

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

## 🛠️ Why Use This Toolkit?

Developing with AI services and tools can be challenging. This toolkit provides:

- **Modular Components**: Use only the parts you need for your specific application
- **Best Practices**: Implement AI tools following industry best practices
- **Conversation Management**: Properly handle tool calls in multi-turn conversations
- **Extensibility**: Easily extend the toolkit with your own tools and integrations
- **Production-Ready**: Build applications that are ready for production use

## 🚦 Getting Started

### Prerequisites

- Python 3.8+
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- OpenAI API Key

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

## 🎮 How to Use This Toolkit

This toolkit is designed to be modular and flexible. Here are some ways to use it:

### 1. Creating and Registering Tools

```python
from ai_tools_core import ToolRegistry, log_tool_execution

# Create a tool registry
registry = ToolRegistry()

# Register a tool with the decorator pattern
@registry.register()
def get_weather(location: str) -> str:
    """Get weather information for a location."""
    # In a real implementation, you would call a weather API
    return f"Weather for {location}: Sunny, 75°F"

# Execute a tool
result = registry.execute_tool("get_weather", location="New York")
print(result)  # Output: Weather for New York: Sunny, 75°F

# Get OpenAI-compatible tool schemas
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

### 3. Integrating with AI Services

```python
from ai_tools_core.services import get_openai_service, get_tool_service

# Get the OpenAI service
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
tools = registry.get_openai_schemas()
response = tool_service.process_with_tools(messages, tools)
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

## 📚 Learn More

- [OpenAI Function Calling Documentation](https://platform.openai.com/docs/guides/function-calling)
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

---

⭐ If you find this project helpful, please star it on GitHub! ⭐
