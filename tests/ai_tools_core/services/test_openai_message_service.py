import pytest
from ai_tools_core.services.openai_message_service import get_openai_message_service
from ai_tools_core.history.models import MessageRole

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


def test_create_conversation_with_system_message(history_manager):
    # Test creating a new conversation with a custom system message
    custom_system_message = "You are a specialized AI assistant for testing"
    service = get_openai_message_service()
    conv_id = service.create_or_get_conversation("test_user", system_message=custom_system_message)
    
    # Verify the system message was set correctly
    messages = service.get_conversation_messages(conv_id)
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == custom_system_message


def test_update_existing_conversation_system_message(history_manager):
    # Create a conversation with the default system message
    service = get_openai_message_service()
    conv_id = service.create_or_get_conversation("test_user")
    
    # Get the original system message
    messages = service.get_conversation_messages(conv_id)
    original_system_message = messages[0]["content"]
    
    # Update the conversation with a new system message
    new_system_message = "You are a specialized AI assistant for multi-agent systems"
    service.create_or_get_conversation("test_user", conversation_id=conv_id, system_message=new_system_message)
    
    # Verify the system message was updated
    updated_messages = service.get_conversation_messages(conv_id)
    assert updated_messages[0]["role"] == "system"
    assert updated_messages[0]["content"] == new_system_message
    assert updated_messages[0]["content"] != original_system_message


def test_existing_conversation_without_system_message(message_service):
    # Create a conversation manually without a system message
    # Use the message_service fixture to ensure we're using the same storage backend
    conversation_id = message_service.history_manager.create_conversation("test_user")
    message_service.history_manager.add_message(conversation_id, MessageRole.USER, "Hello")
    
    # Now use the service to get the conversation and add a system message
    custom_system_message = "You are a specialized AI assistant for testing"
    message_service.create_or_get_conversation("test_user", conversation_id=conversation_id, system_message=custom_system_message)
    
    # Verify a system message was added
    messages = message_service.get_conversation_messages(conversation_id)
    system_messages = [m for m in messages if m["role"] == "system"]
    assert len(system_messages) == 1
    assert system_messages[0]["content"] == custom_system_message


def test_get_openai_message_service_with_system_message():
    # Test that the singleton is created with the correct system message
    custom_system_message = "You are a specialized AI assistant for testing"
    service = get_openai_message_service(system_message=custom_system_message)
    
    # Verify the service has the correct system message
    assert service.system_message == custom_system_message
    
    # Create a conversation and check that it uses the correct system message
    conv_id = service.create_or_get_conversation("test_user")
    messages = service.get_conversation_messages(conv_id)
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == custom_system_message


def test_get_openai_message_service_update_system_message():
    # Create the singleton with default system message
    service1 = get_openai_message_service()
    original_system_message = service1.system_message
    
    # Update the system message
    new_system_message = "You are a specialized AI assistant for multi-agent systems"
    service2 = get_openai_message_service(system_message=new_system_message)
    
    # Verify both references point to the same singleton with updated system message
    assert service1 is service2  # Same instance
    assert service1.system_message == new_system_message
    assert service2.system_message == new_system_message
    assert service1.system_message != original_system_message
