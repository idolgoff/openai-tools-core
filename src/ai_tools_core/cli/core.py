"""Core CLI functionality for AI Tools Core."""

import argparse
import sys
from typing import List, Optional

from ai_tools_core import __version__
from ai_tools_core.logger import get_logger
from ai_tools_core.tools import ToolRegistry

# Get logger for this module
logger = get_logger(__name__)


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """
    Parse command-line arguments.

    Args:
        args: Command-line arguments (defaults to sys.argv[1:])

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="AI Tools Core - Command Line Interface", prog="ai-tools")

    # Add version argument
    parser.add_argument("--version", "-v", action="version", version=f"AI Tools Core {__version__}")

    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Add tools command
    tools_parser = subparsers.add_parser("tools", help="List available tools")
    tools_parser.add_argument("--json", "-j", action="store_true", help="Output in JSON format")

    # Add history command
    history_parser = subparsers.add_parser("history", help="Manage conversation history")
    history_subparsers = history_parser.add_subparsers(dest="history_command", help="History command to execute")

    # Add history list command
    history_list_parser = history_subparsers.add_parser("list", help="List conversations")
    history_list_parser.add_argument("--user", "-u", help="Filter by user ID")

    # Parse arguments
    return parser.parse_args(args)


def main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point for the CLI.

    Args:
        args: Command-line arguments (defaults to sys.argv[1:])

    Returns:
        Exit code
    """
    parsed_args = parse_args(args)

    if parsed_args.command == "tools":
        # List available tools
        registry = ToolRegistry()
        tools = registry.list_tools()

        if parsed_args.json:
            import json

            print(json.dumps(tools, indent=2))
        else:
            print(f"Available tools ({len(tools)}):")
            for tool in tools:
                print(f"  - {tool['name']}: {tool['description']}")
    elif parsed_args.command == "history" and parsed_args.history_command == "list":
        # List conversations
        from ai_tools_core.history.manager import get_history_manager

        history_manager = get_history_manager()
        conversations = history_manager.list_conversations(parsed_args.user)

        print(f"Conversations ({len(conversations)}):")
        for conv in conversations:
            print(f"  - {conv.id}: {conv.message_count} messages, last updated: {conv.last_message_at}")
    else:
        # No command specified, show help
        parse_args(["--help"])
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
