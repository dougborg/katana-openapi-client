"""Tests for the Unpack decorator that flattens Pydantic models into tool parameters."""

import inspect
from typing import Annotated

import pytest
from katana_mcp.unpack import Unpack, unpack_pydantic_params
from pydantic import BaseModel, Field, ValidationError


# Test models
class SimpleRequest(BaseModel):
    """Simple request model for testing."""

    name: str = Field(..., description="Item name")
    limit: int = Field(10, description="Max results")


class OptionalFieldsRequest(BaseModel):
    """Request with optional fields."""

    required_field: str = Field(..., description="Required field")
    optional_field: str | None = Field(None, description="Optional field")
    default_field: int = Field(100, description="Field with default")


class ComplexRequest(BaseModel):
    """Request with various field types."""

    text: str
    number: int
    flag: bool = False
    items: list[str] = Field(default_factory=list)


# Tests
class TestUnpackDecorator:
    """Tests for the unpack_pydantic_params decorator."""

    def test_simple_sync_function(self):
        """Test decorator with a simple synchronous function."""

        @unpack_pydantic_params
        def process(request: Annotated[SimpleRequest, Unpack()]) -> dict:
            return {"name": request.name, "limit": request.limit}

        # Check signature was flattened
        sig = inspect.signature(process)
        assert "name" in sig.parameters
        assert "limit" in sig.parameters
        assert "request" not in sig.parameters

        # Check parameter details
        assert sig.parameters["name"].annotation is str
        assert sig.parameters["limit"].annotation is int
        assert sig.parameters["limit"].default == 10

        # Test calling with flattened params
        result = process(name="test", limit=5)
        assert result == {"name": "test", "limit": 5}

    @pytest.mark.asyncio
    async def test_simple_async_function(self):
        """Test decorator with a simple asynchronous function."""

        @unpack_pydantic_params
        async def async_process(request: Annotated[SimpleRequest, Unpack()]) -> dict:
            return {"name": request.name, "limit": request.limit}

        # Check signature was flattened
        sig = inspect.signature(async_process)
        assert "name" in sig.parameters
        assert "limit" in sig.parameters

        # Test calling with flattened params
        result = await async_process(name="test", limit=20)
        assert result == {"name": "test", "limit": 20}

    def test_optional_fields(self):
        """Test decorator handles optional fields correctly."""

        @unpack_pydantic_params
        def process(request: Annotated[OptionalFieldsRequest, Unpack()]) -> dict:
            return {
                "required": request.required_field,
                "optional": request.optional_field,
                "default": request.default_field,
            }

        # Check signature
        sig = inspect.signature(process)
        assert sig.parameters["required_field"].annotation is str
        assert sig.parameters["optional_field"].annotation == (str | None)
        assert sig.parameters["default_field"].default == 100

        # Test with only required field
        result = process(required_field="value")
        assert result == {"required": "value", "optional": None, "default": 100}

        # Test with all fields
        result = process(required_field="req", optional_field="opt", default_field=200)
        assert result == {"required": "req", "optional": "opt", "default": 200}

    def test_validation_errors(self):
        """Test that Pydantic validation still works."""

        @unpack_pydantic_params
        def process(request: Annotated[SimpleRequest, Unpack()]) -> dict:
            return {"name": request.name}

        # Missing required field should raise ValidationError
        with pytest.raises(ValidationError):
            process(limit=10)  # Missing 'name'

    def test_multiple_unpacked_params(self):
        """Test function with multiple unpacked parameters."""

        class Request1(BaseModel):
            field1: str

        class Request2(BaseModel):
            field2: int

        @unpack_pydantic_params
        def process(
            req1: Annotated[Request1, Unpack()], req2: Annotated[Request2, Unpack()]
        ) -> dict:
            return {"field1": req1.field1, "field2": req2.field2}

        # Check signature has both sets of fields
        sig = inspect.signature(process)
        assert "field1" in sig.parameters
        assert "field2" in sig.parameters

        # Test calling
        result = process(field1="test", field2=42)
        assert result == {"field1": "test", "field2": 42}

    def test_mixed_unpacked_and_regular_params(self):
        """Test function with both unpacked and regular parameters."""

        @unpack_pydantic_params
        def process(
            request: Annotated[SimpleRequest, Unpack()], extra: str = "default"
        ) -> dict:
            return {"name": request.name, "limit": request.limit, "extra": extra}

        # Check signature
        sig = inspect.signature(process)
        assert "name" in sig.parameters
        assert "limit" in sig.parameters
        assert "extra" in sig.parameters

        # Test calling
        result = process(name="test", limit=5, extra="custom")
        assert result == {"name": "test", "limit": 5, "extra": "custom"}

        # Test with default
        result = process(name="test", limit=5)
        assert result == {"name": "test", "limit": 5, "extra": "default"}

    def test_complex_field_types(self):
        """Test decorator handles complex field types."""

        @unpack_pydantic_params
        def process(request: Annotated[ComplexRequest, Unpack()]) -> dict:
            return {
                "text": request.text,
                "number": request.number,
                "flag": request.flag,
                "items": request.items,
            }

        # Test with defaults
        result = process(text="hello", number=42)
        assert result == {"text": "hello", "number": 42, "flag": False, "items": []}

        # Test with all fields
        result = process(text="hello", number=42, flag=True, items=["a", "b"])
        assert result == {
            "text": "hello",
            "number": 42,
            "flag": True,
            "items": ["a", "b"],
        }

    def test_preserves_function_metadata(self):
        """Test that decorator preserves function name and docstring."""

        @unpack_pydantic_params
        def my_function(request: Annotated[SimpleRequest, Unpack()]) -> dict:
            """This is my function's docstring."""
            return {}

        assert my_function.__name__ == "my_function"
        assert my_function.__doc__ == "This is my function's docstring."

    def test_non_pydantic_model_raises_error(self):
        """Test that using Unpack with non-Pydantic class raises TypeError."""

        class NotAModel:
            pass

        with pytest.raises(TypeError, match="must be a Pydantic BaseModel"):

            @unpack_pydantic_params
            def process(request: Annotated[NotAModel, Unpack()]) -> dict:  # type: ignore
                return {}

    def test_field_with_factory_default(self):
        """Test that fields with default_factory work correctly."""

        class RequestWithFactory(BaseModel):
            name: str
            tags: list[str] = Field(default_factory=list)

        @unpack_pydantic_params
        def process(request: Annotated[RequestWithFactory, Unpack()]) -> dict:
            return {"name": request.name, "tags": request.tags}

        # Without providing tags (should use factory default)
        result = process(name="test")
        assert result == {"name": "test", "tags": []}

        # With tags provided
        result = process(name="test", tags=["a", "b"])
        assert result == {"name": "test", "tags": ["a", "b"]}


class TestUnpackWithFastMCPSimulation:
    """Test that unpacked functions work as expected when called by FastMCP."""

    @pytest.mark.asyncio
    async def test_async_tool_simulation(self):
        """Simulate how FastMCP would call an async tool with unpacked params."""

        @unpack_pydantic_params
        async def check_inventory(request: Annotated[SimpleRequest, Unpack()]) -> dict:
            """Simulated inventory check tool."""
            return {"name": request.name, "limit": request.limit, "stock": 100}

        # Simulate FastMCP extracting parameters and calling the function
        # FastMCP would see: check_inventory(name: str, limit: int = 10)
        sig = inspect.signature(check_inventory)

        # Verify FastMCP would see flattened signature
        param_names = list(sig.parameters.keys())
        assert param_names == ["name", "limit"]

        # Simulate FastMCP calling with individual parameters
        result = await check_inventory(name="WIDGET-001", limit=50)
        assert result == {"name": "WIDGET-001", "limit": 50, "stock": 100}

    def test_signature_introspection(self):
        """Test that signature introspection works as expected for tool registration."""

        @unpack_pydantic_params
        def list_items(request: Annotated[SimpleRequest, Unpack()]) -> dict:
            return {}

        sig = inspect.signature(list_items)

        # Verify parameter metadata is preserved for schema generation
        name_param = sig.parameters["name"]
        assert name_param.annotation is str
        assert name_param.default == inspect.Parameter.empty  # Required field

        limit_param = sig.parameters["limit"]
        assert limit_param.annotation is int
        assert limit_param.default == 10  # Has default value
