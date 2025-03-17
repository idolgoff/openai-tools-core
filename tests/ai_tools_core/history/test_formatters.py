import pytest
from ai_tools_core.history.formatters import create_message_formatter
from ai_tools_core.history.models import MessageRole

def test_openai_basic_formatting(sample_conversation):
    formatter = create_message_formatter("openai")
    formatted = formatter.format_messages(sample_conversation)
    
    assert len(formatted) == 3
    assert formatted[0]["role"] == MessageRole.SYSTEM.value
    assert formatted[1]["role"] == MessageRole.USER.value
    assert formatted[2]["role"] == MessageRole.ASSISTANT.value
    assert formatted[1]["content"] == "Hello"

def test_openai_tool_calls_formatting(conversation_with_tool_calls):
    formatter = create_message_formatter("openai")
    formatted = formatter.format_messages(conversation_with_tool_calls)
    
    assert len(formatted) == 2
    assert "tool_calls" in formatted[0]
    assert formatted[1]["role"] == MessageRole.TOOL.value
    assert formatted[1]["name"] == "get_weather"
    assert formatted[1]["tool_call_id"] == "call_123"

def test_anthropic_basic_formatting(sample_conversation):
    formatter = create_message_formatter("anthropic")
    formatted = formatter.format_messages(sample_conversation)
    
    assert "system" in formatted
    assert formatted["system"] == "You are a helpful assistant"
    assert len(formatted["messages"]) == 2  # System message is separate
    assert formatted["messages"][0]["role"] == "human"
    assert formatted["messages"][1]["role"] == "assistant"

def test_anthropic_tool_calls_formatting(conversation_with_tool_calls):
    formatter = create_message_formatter("anthropic")
    formatted = formatter.format_messages(conversation_with_tool_calls)
    
    assert "system" in formatted
    assert len(formatted["messages"]) == 0  # Tool calls are skipped in Anthropic format

def test_formatter_factory():
    openai_formatter = create_message_formatter("openai")
    anthropic_formatter = create_message_formatter("anthropic")
    
    assert openai_formatter.__class__.__name__ == "OpenAIMessageFormatter"
    assert anthropic_formatter.__class__.__name__ == "AnthropicMessageFormatter"
    
    with pytest.raises(ValueError):
        create_message_formatter("unknown")
