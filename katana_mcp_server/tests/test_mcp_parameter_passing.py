"""Test MCP parameter passing behavior.

This test reproduces the issue we see when Claude Code calls MCP tools:
parameters are passed as individual kwargs, not as a nested request object.
"""

import inspect
from typing import Annotated, get_args, get_origin

import pytest
from katana_mcp.tools.foundation.inventory import (
    CheckInventoryRequest,
    LowStockRequest,
    check_inventory,
    list_low_stock_items,
)

# Import the fixture
pytest_plugins = ["tests.tools.conftest"]


class TestMCPParameterPassing:
    """Tests that reproduce Claude Code's parameter passing behavior."""

    @pytest.mark.asyncio
    async def test_list_low_stock_items_with_flat_parameters(self, mock_context):
        """Test calling list_low_stock_items with flat parameters like Claude Code does.

        This test demonstrates the issue: when Claude Code calls an MCP tool,
        it passes parameters as individual kwargs (threshold=10, limit=5) rather
        than as a nested request object (request=LowStockRequest(threshold=10, limit=5)).

        Current behavior: This will FAIL because the tool expects a request parameter.
        Expected behavior with Unpack: This should work with flat parameters.
        """
        context, _ = mock_context

        # This is how Claude Code calls the tool - with flat parameters
        # CURRENT: This fails because list_low_stock_items expects request parameter
        # EXPECTED: With Unpack decorator, this should work
        with pytest.raises(TypeError, match="unexpected keyword argument 'threshold'"):
            await list_low_stock_items(
                threshold=10,  # Flat parameter, not request.threshold
                limit=5,  # Flat parameter, not request.limit
                context=context,
            )

    @pytest.mark.asyncio
    async def test_check_inventory_with_flat_parameters(self, mock_context):
        """Test calling check_inventory with flat parameters like Claude Code does.

        Current behavior: This will FAIL because the tool expects a request parameter.
        Expected behavior with Unpack: This should work with flat parameters.
        """
        context, _ = mock_context

        # This is how Claude Code calls the tool - with flat parameters
        # CURRENT: This fails because check_inventory expects request parameter
        # EXPECTED: With Unpack decorator, this should work
        with pytest.raises(TypeError, match="unexpected keyword argument 'sku'"):
            await check_inventory(
                sku="TEST-001",  # Flat parameter, not request.sku
                context=context,
            )

    def test_current_tool_signature_expects_request_object(self):
        """Verify that current tool signatures expect a request object parameter.

        This test documents the current state: tools have a 'request' parameter
        that is a Pydantic model, not individual flat parameters.
        """
        # Check list_low_stock_items signature
        sig = inspect.signature(list_low_stock_items)
        params = list(sig.parameters.keys())

        assert params == ["request", "context"], (
            "list_low_stock_items has request + context params"
        )

        # Handle Annotated types (when Unpack decorator is applied)
        annotation = sig.parameters["request"].annotation
        if get_origin(annotation) is Annotated:
            # Get the actual type from Annotated[Type, Unpack()]
            annotation = get_args(annotation)[0]

        # Handle forward references (string annotations)
        if isinstance(annotation, str):
            assert annotation == "LowStockRequest", (
                "request parameter is LowStockRequest model"
            )
        else:
            assert annotation == LowStockRequest, (
                "request parameter is LowStockRequest model"
            )

        # Check check_inventory signature
        sig = inspect.signature(check_inventory)
        params = list(sig.parameters.keys())

        assert params == ["request", "context"], (
            "check_inventory has request + context params"
        )

        annotation = sig.parameters["request"].annotation
        if get_origin(annotation) is Annotated:
            annotation = get_args(annotation)[0]

        if isinstance(annotation, str):
            assert annotation == "CheckInventoryRequest", (
                "request parameter is CheckInventoryRequest model"
            )
        else:
            assert annotation == CheckInventoryRequest, (
                "request parameter is CheckInventoryRequest model"
            )

    def test_expected_signature_with_unpack_decorator(self):
        """Document the expected behavior after applying Unpack decorator.

        After applying @unpack_pydantic_params decorator, the tool signature
        should expose individual parameters (threshold, limit) instead of a
        nested request object.

        This test is currently SKIPPED because we haven't applied the decorator yet.
        Once we apply the Unpack decorator, this test should pass.
        """
        pytest.skip("Unpack decorator not yet applied - this is the target state")

        # After Unpack decorator, the signature should look like this:
        # async def list_low_stock_items(threshold: int = 10, limit: int = 50, context: Context)

        sig = inspect.signature(list_low_stock_items)
        params = list(sig.parameters.keys())

        # Expected: individual parameters, not request object
        assert "threshold" in params, "threshold should be a top-level parameter"
        assert "limit" in params, "limit should be a top-level parameter"
        assert "context" in params, "context should still be present"
        assert "request" not in params, "request parameter should be removed"

        # Check parameter types
        assert sig.parameters["threshold"].annotation is int
        assert sig.parameters["limit"].annotation is int
        assert sig.parameters["threshold"].default == 10
        assert sig.parameters["limit"].default == 50


class TestMCPProtocolSimulation:
    """Simulate how FastMCP exposes tool schemas to MCP clients like Claude Code."""

    def test_fastmcp_sees_nested_request_parameter(self):
        """FastMCP currently sees tools with a single 'request' parameter.

        When FastMCP generates the JSON schema for the tool, it creates:
        {
          "type": "object",
          "properties": {
            "request": {
              "type": "object",
              "properties": {
                "threshold": {"type": "integer"},
                "limit": {"type": "integer"}
              }
            }
          }
        }

        This means Claude Code needs to call:
          mcp__katana-erp__list_low_stock_items(request={"threshold": 10, "limit": 5})

        But Claude Code seems to be flattening this and calling:
          mcp__katana-erp__list_low_stock_items(threshold=10, limit=5)

        Which causes the TypeError we see.
        """
        sig = inspect.signature(list_low_stock_items)

        # Current signature has 'request' parameter
        assert "request" in sig.parameters

        annotation = sig.parameters["request"].annotation
        if get_origin(annotation) is Annotated:
            annotation = get_args(annotation)[0]

        if isinstance(annotation, str):
            assert annotation == "LowStockRequest"
        else:
            assert annotation == LowStockRequest

        # This is what FastMCP will see and expose to MCP clients
        # The nested structure causes issues with Claude Code

    def test_expected_fastmcp_schema_after_unpack(self):
        """After Unpack decorator, FastMCP should see flat parameters.

        Expected JSON schema after Unpack:
        {
          "type": "object",
          "properties": {
            "threshold": {"type": "integer", "default": 10},
            "limit": {"type": "integer", "default": 50}
          }
        }

        This matches how Claude Code is trying to call the tool.
        """
        pytest.skip("Unpack decorator not yet applied - this is the target state")

        sig = inspect.signature(list_low_stock_items)

        # After Unpack, signature should have individual parameters
        assert "threshold" in sig.parameters
        assert "limit" in sig.parameters
        assert "request" not in sig.parameters

        # FastMCP will see these flat parameters and create a flat schema
        # Claude Code can then call: tool(threshold=10, limit=5)
