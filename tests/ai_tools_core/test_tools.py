import pytest
from typing import Dict, List
from ai_tools_core.tools import ToolRegistry

def test_tool_registration():
    registry = ToolRegistry()
    
    @registry.register(name="custom_name", description="Custom description")
    def test_tool(param1: str, param2: int = 0) -> str:
        """Test tool docstring."""
        return f"{param1}-{param2}"
    
    schemas = registry.get_tool_schemas()
    assert len(schemas) == 1
    assert schemas[0]["function"]["name"] == "custom_name"
    assert schemas[0]["function"]["description"] == "Custom description"

def test_tool_registration_with_docstring():
    registry = ToolRegistry()
    
    @registry.register()
    def test_tool(param1: str, param2: int = 0) -> str:
        """Test tool with detailed docstring.
        
        Args:
            param1: First parameter description
            param2: Second parameter description
        """
        return f"{param1}-{param2}"
    
    schema = registry.get_tool_schemas()[0]["function"]
    assert "First parameter description" in schema["parameters"]["properties"]["param1"].get("description", "")

def test_tool_parameter_types():
    registry = ToolRegistry()
    
    @registry.register()
    def type_test_tool(
        str_param: str,
        int_param: int,
        float_param: float,
        bool_param: bool,
        dict_param: Dict,
        list_param: List,
        any_param: any,
    ):
        pass
    
    schema = registry.get_tool_schemas()[0]["function"]["parameters"]["properties"]
    assert schema["str_param"]["type"] == "string"
    assert schema["int_param"]["type"] == "integer"
    assert schema["float_param"]["type"] == "number"
    assert schema["bool_param"]["type"] == "boolean"
    assert schema["dict_param"]["type"] == "object"
    assert schema["list_param"]["type"] == "array"
    assert schema["any_param"]["type"] == "string"  # Default fallback

def test_tool_execution():
    registry = ToolRegistry()
    
    @registry.register()
    def add_numbers(a: int, b: int = 0) -> int:
        return a + b
    
    result = registry.execute_tool("add_numbers", a=1, b=2)
    assert result == 3
    
    # Test with default parameter
    result = registry.execute_tool("add_numbers", a=1)
    assert result == 1

def test_tool_retrieval():
    registry = ToolRegistry()
    
    @registry.register()
    def test_tool(): pass
    
    assert registry.get_tool("test_tool") is not None
    assert registry.get_tool("non_existent") is None
    
    all_tools = registry.get_all_tools()
    assert "test_tool" in all_tools
    assert len(all_tools) == 1

def test_required_parameters():
    registry = ToolRegistry()
    
    @registry.register()
    def test_tool(required_param: str, optional_param: int = 0):
        pass
    
    schema = registry.get_tool_schemas()[0]["function"]["parameters"]
    assert "required_param" in schema["required"]
    assert "optional_param" not in schema["required"]

def test_tool_execution_error():
    registry = ToolRegistry()
    
    with pytest.raises(ValueError):
        registry.execute_tool("non_existent_tool")

def test_method_registration():
    registry = ToolRegistry()
    
    class TestClass:
        @registry.register()
        def test_method(self, param: str):
            return f"Method called with {param}"
    
    schema = registry.get_tool_schemas()[0]["function"]["parameters"]
    assert "self" not in schema["properties"]

def test_logging_execution(caplog):
    registry = ToolRegistry()
    
    @registry.register()
    def test_tool(param: str):
        return f"Executed with {param}"
    
    registry.execute_tool("test_tool", param="test")
    assert "test_tool" in caplog.text
