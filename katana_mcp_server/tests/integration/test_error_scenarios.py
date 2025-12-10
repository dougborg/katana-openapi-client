"""Integration tests for error scenarios.

These tests verify proper error handling in various failure scenarios:
- Authentication errors (invalid/missing API key)
- Validation errors (invalid input)
- API errors (rate limiting, server errors)
- Network errors (connection failures)

Most tests in this file use mocked contexts to simulate errors,
as we cannot reliably trigger real API errors in integration tests.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from katana_mcp.tools.foundation.inventory import (
    CheckInventoryRequest,
    LowStockRequest,
    _check_inventory_impl,
    _list_low_stock_items_impl,
)
from katana_mcp.tools.foundation.items import (
    GetVariantDetailsRequest,
    SearchItemsRequest,
    _get_variant_details_impl,
    _search_items_impl,
)
from katana_mcp.tools.foundation.manufacturing_orders import (
    CreateManufacturingOrderRequest,
    _create_manufacturing_order_impl,
)
from katana_mcp.tools.foundation.purchase_orders import (
    CreatePurchaseOrderRequest,
    PurchaseOrderItem,
    _create_purchase_order_impl,
)

from tests.conftest import create_mock_context


@pytest.mark.asyncio
class TestValidationErrors:
    """Test input validation error handling."""

    async def test_check_inventory_empty_sku(self):
        """Test that empty SKU raises validation error."""
        context, _ = create_mock_context()

        request = CheckInventoryRequest(sku="")
        with pytest.raises(ValueError, match="SKU cannot be empty"):
            await _check_inventory_impl(request, context)

    async def test_check_inventory_whitespace_sku(self):
        """Test that whitespace-only SKU raises validation error."""
        context, _ = create_mock_context()

        request = CheckInventoryRequest(sku="   ")
        with pytest.raises(ValueError, match="SKU cannot be empty"):
            await _check_inventory_impl(request, context)

    async def test_search_items_empty_query(self):
        """Test that empty search query raises validation error."""
        context, _ = create_mock_context()

        request = SearchItemsRequest(query="")
        with pytest.raises(ValueError, match="Search query cannot be empty"):
            await _search_items_impl(request, context)

    async def test_low_stock_negative_threshold(self):
        """Test that negative threshold raises validation error."""
        context, _ = create_mock_context()

        request = LowStockRequest(threshold=-1)
        with pytest.raises(ValueError, match="Threshold must be non-negative"):
            await _list_low_stock_items_impl(request, context)

    async def test_low_stock_zero_limit(self):
        """Test that zero limit raises validation error."""
        context, _ = create_mock_context()

        request = LowStockRequest(limit=0)
        with pytest.raises(ValueError, match="Limit must be positive"):
            await _list_low_stock_items_impl(request, context)

    async def test_get_variant_details_empty_sku(self):
        """Test that empty SKU raises validation error."""
        context, _ = create_mock_context()

        request = GetVariantDetailsRequest(sku="")
        with pytest.raises(ValueError, match="SKU cannot be empty"):
            await _get_variant_details_impl(request, context)


@pytest.mark.asyncio
class TestAPIErrorHandling:
    """Test handling of API errors."""

    async def test_check_inventory_not_found(self):
        """Test handling when product is not found."""
        context, lifespan_ctx = create_mock_context()

        # Mock client returning None (product not found)
        lifespan_ctx.client.inventory.check_stock = AsyncMock(return_value=None)

        request = CheckInventoryRequest(sku="NONEXISTENT-SKU")
        result = await _check_inventory_impl(request, context)

        # Should return zero stock, not error
        assert result.sku == "NONEXISTENT-SKU"
        assert result.available_stock == 0
        assert result.committed == 0

    async def test_get_variant_details_not_found(self):
        """Test handling when variant is not found."""
        context, lifespan_ctx = create_mock_context()

        # Mock client returning empty list
        lifespan_ctx.client.variants.search = AsyncMock(return_value=[])

        request = GetVariantDetailsRequest(sku="NONEXISTENT-SKU")
        with pytest.raises(ValueError, match="not found"):
            await _get_variant_details_impl(request, context)

    async def test_search_items_empty_results(self):
        """Test handling when search returns no results."""
        context, lifespan_ctx = create_mock_context()

        # Mock client returning empty list
        lifespan_ctx.client.variants.search = AsyncMock(return_value=[])

        request = SearchItemsRequest(query="xyznonexistent123")
        result = await _search_items_impl(request, context)

        assert result.total_count == 0
        assert result.items == []

    async def test_api_error_propagation(self):
        """Test that API errors are properly propagated."""
        context, lifespan_ctx = create_mock_context()

        # Mock client raising an exception
        lifespan_ctx.client.inventory.check_stock = AsyncMock(
            side_effect=Exception("API Error: Rate limit exceeded")
        )

        request = CheckInventoryRequest(sku="TEST-SKU")
        with pytest.raises(Exception, match="Rate limit exceeded"):
            await _check_inventory_impl(request, context)


@pytest.mark.asyncio
class TestNetworkErrorHandling:
    """Test handling of network-related errors."""

    async def test_connection_error_handling(self):
        """Test handling of connection errors."""
        context, lifespan_ctx = create_mock_context()

        # Mock client raising connection error
        lifespan_ctx.client.inventory.check_stock = AsyncMock(
            side_effect=ConnectionError("Unable to connect to API server")
        )

        request = CheckInventoryRequest(sku="TEST-SKU")
        with pytest.raises(ConnectionError, match="Unable to connect"):
            await _check_inventory_impl(request, context)

    async def test_timeout_error_handling(self):
        """Test handling of timeout errors."""
        context, lifespan_ctx = create_mock_context()

        # Mock client raising timeout error
        import asyncio

        lifespan_ctx.client.variants.search = AsyncMock(
            side_effect=TimeoutError("Request timed out")
        )

        request = SearchItemsRequest(query="test")
        with pytest.raises(asyncio.TimeoutError):
            await _search_items_impl(request, context)


@pytest.mark.asyncio
class TestElicitationErrors:
    """Test handling of user elicitation errors/declines."""

    async def test_user_declines_po_creation(self):
        """Test handling when user declines PO creation."""
        context, lifespan_ctx = create_mock_context(elicit_confirm=False)

        # Set up mock client (even though we won't reach API call)
        mock_client = MagicMock()
        lifespan_ctx.client = mock_client

        request = CreatePurchaseOrderRequest(
            supplier_id=1,
            location_id=1,
            order_number="TEST-PO-001",
            items=[
                PurchaseOrderItem(
                    variant_id=1,
                    quantity=10,
                    price_per_unit=100.00,
                )
            ],
            confirm=True,  # User will decline
        )

        result = await _create_purchase_order_impl(request, context)

        # Should return cancelled status, not error
        assert result.is_preview is True
        assert (
            "declined" in result.message.lower()
            or "cancelled" in result.message.lower()
        )

    async def test_user_declines_mo_creation(self):
        """Test handling when user declines MO creation."""
        context, lifespan_ctx = create_mock_context(elicit_confirm=False)

        mock_client = MagicMock()
        lifespan_ctx.client = mock_client

        request = CreateManufacturingOrderRequest(
            variant_id=1,
            planned_quantity=50,
            location_id=1,
            confirm=True,  # User will decline
        )

        result = await _create_manufacturing_order_impl(request, context)

        # Should return cancelled status, not error
        assert result.is_preview is True
        assert (
            "declined" in result.message.lower()
            or "cancelled" in result.message.lower()
        )


@pytest.mark.asyncio
class TestAuthenticationErrors:
    """Test authentication error handling.

    These tests verify proper error handling when authentication fails.
    They require specific environment setup or mocking.
    """

    async def test_authentication_fixture_requires_api_key(self):
        """Verify that integration fixtures properly check for API key.

        This is a documentation test - the actual skip behavior is tested
        by running the integration tests without KATANA_API_KEY set.
        """
        # This test documents the expected behavior:
        # - The api_key fixture in conftest.py checks for KATANA_API_KEY
        # - If not set, it calls pytest.skip()
        # - All integration tests depend on this fixture (via katana_client)

        # We can verify the fixture exists and has the right structure
        from katana_mcp_server.tests.integration import conftest

        # Verify the fixture is defined
        assert hasattr(conftest, "api_key")
        assert hasattr(conftest, "katana_client")
        assert hasattr(conftest, "integration_context")


@pytest.mark.asyncio
class TestDataConsistencyErrors:
    """Test handling of data consistency issues."""

    async def test_variant_disappears_between_calls(self):
        """Test handling when a variant is deleted between search and details."""
        context, lifespan_ctx = create_mock_context()

        # First call returns a variant
        mock_variant = MagicMock()
        mock_variant.id = 123
        mock_variant.sku = "TEMP-SKU"
        mock_variant.type_ = "product"
        mock_variant.get_display_name = MagicMock(return_value="Temp Item")

        # Search returns the variant
        search_mock = AsyncMock(return_value=[mock_variant])

        # But details call returns empty (item deleted)
        details_mock = AsyncMock(return_value=[])

        lifespan_ctx.client.variants.search = search_mock

        # First, search finds the item
        search_request = SearchItemsRequest(query="TEMP")
        search_result = await _search_items_impl(search_request, context)
        assert len(search_result.items) == 1

        # Now, the item disappears
        lifespan_ctx.client.variants.search = details_mock

        # Details call should fail gracefully
        details_request = GetVariantDetailsRequest(sku="TEMP-SKU")
        with pytest.raises(ValueError, match="not found"):
            await _get_variant_details_impl(details_request, context)

    async def test_partial_data_handling(self):
        """Test handling of items with missing/null fields."""
        context, lifespan_ctx = create_mock_context()

        # Mock variant with many null fields
        mock_variant = MagicMock()
        mock_variant.id = 1
        mock_variant.sku = None  # Null SKU
        mock_variant.type_ = None
        mock_variant.get_display_name = MagicMock(return_value=None)

        lifespan_ctx.client.variants.search = AsyncMock(return_value=[mock_variant])

        request = SearchItemsRequest(query="test")
        result = await _search_items_impl(request, context)

        # Should handle null values gracefully
        assert len(result.items) == 1
        assert result.items[0].sku == ""  # Converted to empty string
        assert result.items[0].name == ""  # Converted to empty string
