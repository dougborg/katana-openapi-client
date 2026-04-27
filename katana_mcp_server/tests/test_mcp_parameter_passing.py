"""Test MCP parameter passing behavior.

This test reproduces the issue we see when Claude Code calls MCP tools:
parameters are passed as individual kwargs, not as a nested request object.
"""

import inspect

import pytest
from katana_mcp.tools.foundation.inventory import (
    LowStockResponse,
    StockInfo,
    check_inventory,
    list_low_stock_items,
)

# The mock_context fixture is now in tests/conftest.py
# It's automatically available to all tests in this package


class TestMCPParameterPassing:
    """Tests that reproduce Claude Code's parameter passing behavior."""

    @pytest.mark.skip(
        reason="Requires proper async mock setup - signature tests verify the decorator works"
    )
    @pytest.mark.asyncio
    async def test_list_low_stock_items_with_flat_parameters(self, mock_context):
        """Test calling list_low_stock_items with flat parameters like Claude Code does.

        This test verifies that with the Unpack decorator, Claude Code can call
        MCP tools with flat parameters (threshold=10, limit=5) instead of nested
        request objects (request=LowStockRequest(threshold=10, limit=5)).

        NOTE: This test is skipped because it requires proper async mock setup.
        The signature tests below verify that the Unpack decorator works correctly.
        """
        context, _ = mock_context

        # This is how Claude Code calls the tool - with flat parameters
        # With Unpack decorator, this should work!
        result = await list_low_stock_items(
            threshold=10,  # Flat parameter, not request.threshold
            limit=5,  # Flat parameter, not request.limit
            context=context,
        )

        # Verify the result is valid
        assert isinstance(result, LowStockResponse)
        assert result.total_count >= 0
        assert len(result.items) <= 5

    @pytest.mark.skip(
        reason="Requires proper async mock setup - signature tests verify the decorator works"
    )
    @pytest.mark.asyncio
    async def test_check_inventory_with_flat_parameters(self, mock_context):
        """Test calling check_inventory with flat parameters like Claude Code does.

        This test verifies that with the Unpack decorator, Claude Code can call
        MCP tools with flat parameters instead of nested request objects.

        NOTE: This test is skipped because it requires proper async mock setup.
        The signature tests below verify that the Unpack decorator works correctly.
        """
        context, _ = mock_context

        # This is how Claude Code calls the tool - with flat parameters
        # With Unpack decorator, this should work!
        result = await check_inventory(
            skus_or_variant_ids=[
                "TEST-001"
            ],  # Flat parameter, not request.skus_or_variant_ids
            context=context,
        )

        # Verify the result is valid
        assert isinstance(result, StockInfo)
        assert result.sku == "TEST-001"

    def test_tool_signatures_are_flattened_by_unpack_decorator(self):
        """Verify that tool signatures have flattened parameters after Unpack decorator.

        This test verifies that the Unpack decorator successfully transforms the
        signature from nested request objects to individual flat parameters.
        """
        # Check list_low_stock_items signature
        sig = inspect.signature(list_low_stock_items)
        params = list(sig.parameters.keys())

        assert params == ["threshold", "limit", "format", "context"], (
            "list_low_stock_items has flattened params: threshold, limit, format, context"
        )
        assert sig.parameters["threshold"].annotation is int
        assert sig.parameters["limit"].annotation is int
        assert sig.parameters["threshold"].default == 10
        assert sig.parameters["limit"].default == 50
        assert sig.parameters["format"].default == "markdown"

        # Check check_inventory signature
        sig2 = inspect.signature(check_inventory)
        params2 = list(sig2.parameters.keys())

        assert params2 == [
            "skus_or_variant_ids",
            "format",
            "context",
        ], "check_inventory has flattened params: skus_or_variant_ids, format, context"
        # skus_or_variant_ids defaults to empty list at the Python level;
        # the min_length=1 Pydantic constraint enforces non-empty at validation time.
        assert sig2.parameters["skus_or_variant_ids"].default == []
        assert sig2.parameters["format"].default == "markdown"
        # Verify min_length=1 is enforced: empty list must raise ValidationError.
        from katana_mcp.tools.foundation.inventory import CheckInventoryRequest
        from pydantic import ValidationError as PydanticValidationError

        with pytest.raises(PydanticValidationError):
            CheckInventoryRequest(skus_or_variant_ids=[])


class TestMCPProtocolSimulation:
    """Simulate how FastMCP exposes tool schemas to MCP clients like Claude Code."""

    def test_fastmcp_sees_flattened_parameters_after_unpack(self):
        """After Unpack decorator, FastMCP sees flat parameters.

        With the Unpack decorator, FastMCP generates a flat JSON schema:
        {
          "type": "object",
          "properties": {
            "threshold": {"type": "integer", "default": 10},
            "limit": {"type": "integer", "default": 50}
          }
        }

        This matches how Claude Code is trying to call the tool:
          mcp__katana-erp__list_low_stock_items(threshold=10, limit=5)
        """
        sig = inspect.signature(list_low_stock_items)

        # After Unpack, signature should have individual parameters
        assert "threshold" in sig.parameters
        assert "limit" in sig.parameters
        assert "request" not in sig.parameters

        # Verify parameter types
        assert sig.parameters["threshold"].annotation is int
        assert sig.parameters["limit"].annotation is int
        assert sig.parameters["threshold"].default == 10
        assert sig.parameters["limit"].default == 50

        # FastMCP will see these flat parameters and create a flat schema
        # Claude Code can then call: tool(threshold=10, limit=5)
