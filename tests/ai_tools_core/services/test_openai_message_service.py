import pytest
from ai_tools_core.services.openai_message_service import get_openai_message_service

def test_create_conversation(history_manager):
    service = get_openai_message_service()
    conv_id = service.create_or_get_conversation("test_user")
    assert conv_id is not None
    
    messages = service.get_conversation_messages(conv_id)
    assert len(messages) > 0
    assert messages[0]["role"] == "system"

def test_add_messages(history_manager):
    service = get_openai_message_service()
    conv_id = service.create_or_get_conversation("test_user")
    
    service.add_user_message(conv_id, "Hello")
    service.add_assistant_message(conv_id, "Hi there!")
    
    messages = service.get_conversation_messages(conv_id)
    assert len(messages) == 3  # system + user + assistant

def test_tool_messages(message_service):
    conv_id = message_service.create_or_get_conversation("test_user")
    
    # Add assistant message with tool call
    message_service.add_assistant_message(
        conv_id,
        "Let me check that",
        metadata={
            "tool_calls": [{
                "id": "call_123",
                "type": "function",
                "function": {
                    "name": "test_tool",
                    "arguments": '{"test": "value"}'
                }
            }]
        }
    )
    
    # Add tool result using proper method
    message_service.add_tool_result_message(
        conv_id,
        "test_tool",
        {"test": "value"},
        {"result": "success"},
        "call_123"
    )
    
    messages = message_service.get_conversation_messages(conv_id)
    assert len(messages) > 2  # system + assistant + tool
    assert any("tool_calls" in m for m in messages)  # Check for tool calls
    assert any(m["role"] == "tool" for m in messages)  # Check for tool response
