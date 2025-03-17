import pytest
from ai_tools_core.services.tool_service import get_tool_service

def test_execute_tool_call(sample_tool_registry):
    service = get_tool_service()
    response = service.execute_tool_call(
        "test_conv",
        "call_123",
        "test_tool",
        {"test": "value"},
        sample_tool_registry
    )
    
    assert response["status"] == "success"
    assert response["tool"] == "test_tool"
    assert response["data"]["test"] == "value"

def test_process_tool_calls(sample_tool_registry, mock_tool_response_processor):
    service = get_tool_service()
    tool_calls = [
        type("ToolCall", (), {
            "id": "call_123",
            "function": type("Function", (), {
                "name": "test_tool",
                "arguments": '{"test": "value"}'
            })
        })()
    ]
    
    response = service.process_tool_calls(
        "test_conv",
        tool_calls,
        sample_tool_registry,
        tool_response_processor=mock_tool_response_processor
    )
    
    assert response == "I processed your request."

def test_unknown_tool():
    service = get_tool_service()
    response = service.execute_tool_call(
        "test_conv",
        "call_123",
        "unknown_tool",
        {},
        {}
    )
    
    assert response["status"] == "error"
    assert "Unknown tool" in response["error"]
