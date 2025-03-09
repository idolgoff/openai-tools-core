# OpenAI Tools Playground

A testing playground for OpenAI tools with Telegram bot integration.

## Features

- Telegram bot integration for natural language interaction
- Environment variable management via `.env` file
- Collection of mocked AI tools for testing
- Project management functionality:
  - List projects
  - Delete projects
  - Switch between projects
- Comprehensive logging of tool selection and execution
- Natural Language Processing (NLP) for all bot communications

## Setup

1. Clone the repository
2. Create a virtual environment: `python -m venv .venv`
3. Activate the virtual environment:
   - Windows: `.venv\Scripts\activate`
   - macOS/Linux: `source .venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Create a `.env` file with your configuration (see `.env.example`)
6. Run the application: `python src/main.py`

## Project Structure

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
    │   ├── __init__.py
    │   ├── telegram_bot.py  # Telegram bot implementation
    │   └── handlers.py      # Bot message handlers
    ├── core/
    │   ├── __init__.py
    │   ├── tools.py         # AI tools implementation
    │   └── logger.py        # Logging functionality
    └── utils/
        ├── __init__.py
        └── env.py           # Environment variable handling
```

## License

MIT
