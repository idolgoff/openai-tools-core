import pytest
from datetime import datetime

from ai_tools_core.usage.events import UsageEvent
from ai_tools_core.history.models import Conversation, Message, MessageRole

@pytest.fixture
def mock_openai_response():
    # Create mock tool call
    mock_tool_call = type('ToolCall', (), {
        'id': 'call_123',
        'type': 'function',
        'function': type('Function', (), {
            'name': 'test_tool',
            'arguments': '{"test": "value"}'
        })
    })()
    
    # Create mock message with tool calls
    mock_message = type('Message', (), {
        'content': 'Test response',
        'tool_calls': [mock_tool_call]
    })()
    
    # Create mock choice and response
    mock_choice = type('Choice', (), {'message': mock_message})()
    mock_usage = type('Usage', (), {'completion_tokens': 10, 'prompt_tokens': 5})()
    mock_response = type('Response', (), {})()
    
    mock_response.choices = [mock_choice]
    mock_response.usage = mock_usage
    return mock_response

@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset all singletons before each test"""
    # Import here to avoid circular imports
    import ai_tools_core.services.openai_service as openai_service
    import ai_tools_core.services.openai_message_service as message_service
    import ai_tools_core.services.tool_service as tool_service
    import ai_tools_core.history.manager as history_manager
    
    openai_service._openai_service = None
    message_service._openai_message_service = None
    tool_service._tool_service = None
    history_manager._history_manager = None

@pytest.fixture
def sample_usage_event():
    return UsageEvent(
        model="gpt-4o-mini",
        input_tokens=10,
        output_tokens=20,
        request_type="chat",
        user_id="test_user",
        session_id="test_session"
    )

@pytest.fixture
def sample_conversation():
    return Conversation(
        id="test_conv",
        user_id="test_user",  # Add required user_id
        messages=[
            Message(role=MessageRole.SYSTEM, content="You are a helpful assistant"),
            Message(role=MessageRole.USER, content="Hello"),
            Message(role=MessageRole.ASSISTANT, content="Hi there!"),
        ]
    )

@pytest.fixture
def conversation_with_tool_calls():
    tool_call = {
        "id": "call_123",
        "type": "function",
        "function": {
            "name": "get_weather",
            "arguments": '{"location": "London"}'
        }
    }
    
    return Conversation(
        id="test_conv_tools",
        user_id="test_user",  # Add required user_id
        messages=[
            Message(
                role=MessageRole.ASSISTANT,
                content="Let me check the weather",
                metadata={"tool_calls": [tool_call]}
            ),
            Message(
                role=MessageRole.TOOL,
                content="Sunny, 22°C",
                metadata={"name": "get_weather"}
            )
        ]
    )

@pytest.fixture
def history_manager():
    from ai_tools_core.history.manager import HistoryManager
    return HistoryManager(storage_type="memory", formatter_type="openai")

@pytest.fixture
def populated_history_manager(history_manager):
    conv_id = history_manager.create_conversation("test_user")
    history_manager.add_message(conv_id, "system", "You are a helpful assistant")
    history_manager.add_message(conv_id, "user", "Hello")
    history_manager.add_message(conv_id, "assistant", "Hi there!")
    return history_manager, conv_id

@pytest.fixture
def temp_storage_dir(tmp_path):
    return str(tmp_path / "test_history")

@pytest.fixture
def memory_storage():
    from ai_tools_core.history.storage import create_storage_backend
    return create_storage_backend("memory")

@pytest.fixture
def file_storage(temp_storage_dir):
    from ai_tools_core.history.storage import create_storage_backend
    return create_storage_backend("file", storage_dir=temp_storage_dir)

@pytest.fixture
def sample_tool_registry():
    def test_tool(**kwargs):
        return {"result": "success", **kwargs}
    
    return {"test_tool": test_tool}

@pytest.fixture
def mock_tool_response_processor():
    def processor(tool_name, args, result, conversation_id):
        return {"processed": True, "tool": tool_name}
    return processor

@pytest.fixture
def temp_history_dir(tmp_path):
    """Provide temporary directory for history files"""
    history_dir = tmp_path / "test_history"
    history_dir.mkdir()
    return str(history_dir)

@pytest.fixture
def mock_openai_client(mocker, mock_openai_response):
    """Create a mock OpenAI client"""
    mock_client = mocker.Mock()
    mock_client.chat.completions.create.return_value = mock_openai_response
    # Patch OpenAI at module level
    mocker.patch('ai_tools_core.services.openai_service.OpenAI', return_value=mock_client)
    return mock_client

@pytest.fixture
def mock_openai_service(mock_openai_client):
    """Get OpenAI service with mocked client"""
    from ai_tools_core.services.openai_service import get_openai_service
    service = get_openai_service()
    return service

@pytest.fixture
def message_service(temp_history_dir):
    """Provide initialized message service with temp storage"""
    from ai_tools_core.services.openai_message_service import get_openai_message_service
    from ai_tools_core.history.manager import get_history_manager
    
    # Reset singletons
    import ai_tools_core.services.openai_message_service as message_service
    import ai_tools_core.history.manager as history_manager
    message_service._openai_message_service = None
    history_manager._history_manager = None
    
    # Set history directory in environment
    import os
    os.environ['AI_TOOLS_HISTORY_DIR'] = temp_history_dir
    
    # Create new service with temp storage
    service = get_openai_message_service()
    return service
