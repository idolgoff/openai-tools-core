# AI Tools Core

A core library for AI tools and integrations. This package provides core functionality for working with AI services, managing conversation history, and executing AI-powered tools.

## Package Structure

```text
ai_tools_core/
├── cli/               # Command-line interface tools
├── history/           # Conversation history management
├── services/          # AI service integrations (OpenAI, etc.)
├── tools.py           # Tool registry and implementations
└── logger.py          # Logging utilities
```

## Features

- **Tool Registry**: Register and execute AI-powered tools with a unified interface
- **History Management**: Store and retrieve conversation history
- **AI Service Integration**: Interact with AI services like OpenAI
- **Logging**: Structured logging with color formatting

## Usage Examples

### Tool Registry

```python
from ai_tools_core import ToolRegistry

# Create a tool registry
registry = ToolRegistry()

# Register a tool
@registry.register(name="echo", description="Echo the input")
def echo_tool(text: str) -> str:
    return text

# Execute a tool
result = registry.execute_tool("echo", text="Hello, world!")
print(result)  # Output: Hello, world!
```

### Logging

```python
from ai_tools_core import get_logger

# Get a logger
logger = get_logger(__name__)

# Log messages
logger.info("This is an info message")
logger.error("This is an error message")
```

## Installation

```bash
# Install from the repository
pip install -e .
```
