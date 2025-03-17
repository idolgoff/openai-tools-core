import pytest
from ai_tools_core.history.storage import create_storage_backend
from ai_tools_core.history.models import Conversation, Message, MessageRole

def test_memory_storage_save_load(memory_storage, sample_conversation):
    # Test save
    assert memory_storage.save_conversation(sample_conversation)
    
    # Test load
    loaded = memory_storage.load_conversation(sample_conversation.id)
    assert loaded is not None
    assert loaded.id == sample_conversation.id
    assert len(loaded.messages) == len(sample_conversation.messages)
    assert loaded.messages[0].content == "You are a helpful assistant"

def test_memory_storage_delete(memory_storage, sample_conversation):
    memory_storage.save_conversation(sample_conversation)
    assert memory_storage.delete_conversation(sample_conversation.id)
    assert memory_storage.load_conversation(sample_conversation.id) is None

def test_memory_storage_list(memory_storage, sample_conversation):
    memory_storage.save_conversation(sample_conversation)
    conversations = memory_storage.list_conversations()
    assert len(conversations) == 1
    assert conversations[0].id == sample_conversation.id
    assert conversations[0].message_count == 3

def test_file_storage_save_load(file_storage, sample_conversation):
    # Test save
    assert file_storage.save_conversation(sample_conversation)
    
    # Test load
    loaded = file_storage.load_conversation(sample_conversation.id)
    assert loaded is not None
    assert loaded.id == sample_conversation.id
    assert len(loaded.messages) == len(sample_conversation.messages)
    assert loaded.messages[0].content == "You are a helpful assistant"

def test_file_storage_delete(file_storage, sample_conversation):
    file_storage.save_conversation(sample_conversation)
    assert file_storage.delete_conversation(sample_conversation.id)
    assert file_storage.load_conversation(sample_conversation.id) is None

def test_file_storage_list(file_storage, sample_conversation):
    file_storage.save_conversation(sample_conversation)
    conversations = file_storage.list_conversations()
    assert len(conversations) == 1
    assert conversations[0].id == sample_conversation.id
    assert conversations[0].message_count == 3

def test_storage_factory():
    with pytest.raises(ValueError):
        create_storage_backend("unknown")
    
    with pytest.raises(ValueError):
        create_storage_backend("file")  # Missing storage_dir

def test_storage_user_filter(memory_storage):
    # Create conversations for different users
    conv1 = Conversation(id="conv1", user_id="user1", messages=[
        Message(role=MessageRole.USER, content="Hello")
    ])
    conv2 = Conversation(id="conv2", user_id="user2", messages=[
        Message(role=MessageRole.USER, content="Hi")
    ])
    
    memory_storage.save_conversation(conv1)
    memory_storage.save_conversation(conv2)
    
    user1_convs = memory_storage.list_conversations("user1")
    assert len(user1_convs) == 1
    assert user1_convs[0].id == "conv1"
