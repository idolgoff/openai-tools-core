import pytest
from datetime import datetime

from ai_tools_core.history.models import MessageRole
from ai_tools_core.history.manager import get_history_manager

def test_create_conversation(history_manager):
    conv_id = history_manager.create_conversation("test_user")
    assert conv_id is not None
    conversation = history_manager.get_conversation(conv_id)
    assert conversation.user_id == "test_user"
    assert len(conversation.messages) == 0

def test_add_message(populated_history_manager):
    manager, conv_id = populated_history_manager
    conversation = manager.get_conversation(conv_id)
    assert len(conversation.messages) == 3
    assert conversation.messages[0].role == MessageRole.SYSTEM
    assert conversation.messages[1].role == MessageRole.USER

def test_message_formatting(populated_history_manager):
    manager, conv_id = populated_history_manager
    formatted = manager.get_messages(conv_id)
    assert len(formatted) == 3
    assert formatted[0]["role"] == "system"
    assert formatted[1]["role"] == "user"
    assert formatted[1]["content"] == "Hello"

def test_conversation_context(history_manager):
    conv_id = history_manager.create_conversation("test_user")
    assert history_manager.set_conversation_context(conv_id, "Test context")
    assert history_manager.get_conversation_context(conv_id) == "Test context"
    assert history_manager.clear_conversation_context(conv_id)
    assert history_manager.get_conversation_context(conv_id) is None

def test_list_conversations(history_manager):
    conv_id1 = history_manager.create_conversation("user1")
    conv_id2 = history_manager.create_conversation("user2")
    
    all_convs = history_manager.list_conversations()
    user1_convs = history_manager.list_conversations("user1")
    
    assert len(all_convs) == 2
    assert len(user1_convs) == 1
    assert user1_convs[0].id == conv_id1

def test_delete_conversation(populated_history_manager):
    manager, conv_id = populated_history_manager
    assert manager.delete_conversation(conv_id)
    assert manager.get_conversation(conv_id) is None

def test_singleton_manager():
    manager1 = get_history_manager()
    manager2 = get_history_manager()
    assert manager1 is manager2

def test_invalid_conversation_operations(history_manager):
    assert history_manager.get_conversation("invalid_id") is None
    assert not history_manager.delete_conversation("invalid_id")
    assert not history_manager.set_conversation_context("invalid_id", "test")
    assert history_manager.get_conversation_context("invalid_id") is None
