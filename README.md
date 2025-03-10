# 🚀 OpenAI Tools Playground: Build, Test, and Deploy AI Tools with Ease

The ultimate sandbox for developers working with OpenAI's function calling and tool integration capabilities. Experiment with AI tools in a Telegram-powered interface and accelerate your AI development workflow!

## ✨ Key Features

- 🤖 **Telegram Bot Integration**: Interact with your AI tools through natural language conversations
- 🔧 **OpenAI Function Calling**: Test and debug OpenAI tool implementations in a controlled environment
- 📊 **Conversation History Management**: Track and analyze AI interactions with proper tool call handling
- 📁 **Project Management**: Organize your work with project switching and management capabilities
- 📝 **Comprehensive Logging**: Monitor tool execution with detailed, non-duplicative logs
- 🔄 **Hot Reload Development**: Rapid iteration with auto-reloading development server

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

You can install the package directly from the repository:

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

## 🛠️ Why Use This Playground?

Developing with OpenAI's tools API can be challenging. This playground provides:

- **Rapid Prototyping**: Test tool ideas without building a full application
- **Debugging Environment**: Isolate and fix issues in your OpenAI tool implementations
- **Learning Platform**: Understand how function calling works in a practical context
- **Conversation Management**: See how to properly handle tool calls in multi-turn conversations

## 🚦 Getting Started

### Prerequisites

- Python 3.8+
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- OpenAI API Key

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

## 🎮 How to Use This Project

This playground is designed as a learning and experimentation tool. Here are some ways to use it:

### 1. Testing OpenAI Tool Implementations

```python
# Example: Adding a new tool in src/core/tools.py

def get_weather(location: str) -> str:
    """Get weather information for a location."""
    # In a real implementation, you would call a weather API
    log_tool_execution("get_weather", {"location": location}, f"Weather for {location}: Sunny, 75°F")
    return f"Weather for {location}: Sunny, 75°F"

# Add your tool to the TOOLS dictionary
TOOLS = {
    # ... existing tools
    "get_weather": get_weather,
}
```

### 2. Interacting with Your Bot

Once your bot is running, you can interact with it through Telegram:

1. Start a conversation with your bot
2. Ask it to perform tasks that trigger your tools
3. Observe how the bot processes your requests and executes tools
4. Check the logs to see detailed information about tool execution

### 3. Exploring Conversation History

The playground includes a conversation history manager that properly handles tool calls:

- Each conversation is stored with a unique ID
- Tool calls and responses are properly formatted for the OpenAI API
- You can analyze how conversations flow between user, assistant, and tools

## 💻 Development Mode

For faster development iterations:

```bash
python dev.py
```

This starts the server with hot-reload capability, automatically restarting when you make changes to the code.

## 📂 Project Structure

```bash
ai-tools-playground/
├── .env                  # Environment variables (not in repo)
├── .env.example          # Example environment variables
├── README.md             # Project documentation
├── progress.md           # Project progress tracking
├── requirements.txt      # Python dependencies
└── src/
    ├── main.py           # Application entry point
    ├── bot/
    │   ├── telegram_bot.py  # Telegram bot implementation
    │   └── handlers.py      # Bot message handlers
    ├── core/
    │   ├── tools.py         # AI tools implementation
    │   ├── history/         # Conversation history management
    │   └── logger.py        # Logging functionality
    └── utils/
        └── env.py           # Environment variable handling
```

## 📚 Learn More

- [OpenAI Function Calling Documentation](https://platform.openai.com/docs/guides/function-calling)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Python Telegram Bot Library](https://python-telegram-bot.readthedocs.io/)

## 📄 License

MIT

---

⭐ If you find this project helpful, please star it on GitHub! ⭐
