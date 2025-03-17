import pytest
from ai_tools_core.services.openai_service import OpenAIService, get_openai_service

def test_token_counting(mock_openai_service):
    messages = [
        {"role": "system", "content": "You are an assistant"},
        {"role": "user", "content": "Hello"},
    ]
    token_count = mock_openai_service.count_tokens(messages)
    assert token_count > 0

def test_message_limiting(mock_openai_service):
    messages = [
        {"role": "system", "content": "You are an assistant"},
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
    ]
    limited = mock_openai_service.limit_messages_by_tokens(messages, max_tokens=10)
    assert len(limited) < len(messages)
    assert any(m["role"] == "system" for m in limited)  # System message should be kept

def test_generate_response(mock_openai_client):
    service = get_openai_service()
    messages = [{"role": "user", "content": "Hello"}]
    response = service.generate_response(messages)
    
    # Verify mock was called
    mock_openai_client.chat.completions.create.assert_called_once()
    assert response == "Test response"

def test_process_with_tools(mock_openai_service, mock_openai_client):
    messages = [{"role": "user", "content": "Hello"}]
    tools = [{
        "type": "function",
        "function": {
            "name": "test_tool",
            "parameters": {"type": "object", "properties": {}}
        }
    }]
    
    response = mock_openai_service.process_with_tools(messages, tools)
    
    # Verify mock was called with correct arguments
    mock_openai_client.chat.completions.create.assert_called_once_with(
        model=mock_openai_service.model,
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )
    assert response.choices[0].message.tool_calls[0].function.name == "test_tool"
