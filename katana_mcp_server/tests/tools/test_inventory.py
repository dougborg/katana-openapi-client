"""Tests for inventory MCP tools."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from katana_mcp.tools.inventory import (
    CheckInventoryRequest,
    LowStockRequest,
    SearchProductsRequest,
    _check_inventory_impl,
    _list_low_stock_items_impl,
    _search_products_impl,
)

# ============================================================================
# Unit Tests (with mocks)
# ============================================================================


@pytest.mark.asyncio
async def test_check_inventory():
    """Test check_inventory tool with mocked client."""
    # Mock context and client
    context = MagicMock()
    context.state.client.inventory.check_stock = AsyncMock(
        return_value={
            "sku": "WIDGET-001",
            "product_name": "Test Widget",
            "available": 100,
            "in_stock": 150,
            "allocated": 30,
        }
    )

    request = CheckInventoryRequest(sku="WIDGET-001")
    result = await _check_inventory_impl(request, context)

    assert result.sku == "WIDGET-001"
    assert result.product_name == "Test Widget"
    assert result.available_stock == 100
    assert result.in_production == 0  # Not available in API yet
    assert result.committed == 30
    context.state.client.inventory.check_stock.assert_called_once_with("WIDGET-001")


@pytest.mark.asyncio
async def test_check_inventory_missing_fields():
    """Test check_inventory handles missing optional fields."""
    context = MagicMock()
    context.state.client.inventory.check_stock = AsyncMock(
        return_value={
            "sku": "WIDGET-002",
            # Missing product_name, available, allocated
        }
    )

    request = CheckInventoryRequest(sku="WIDGET-002")
    result = await _check_inventory_impl(request, context)

    assert result.sku == "WIDGET-002"
    assert result.product_name == ""  # Default empty string
    assert result.available_stock == 0  # Default to 0
    assert result.committed == 0  # Default to 0


@pytest.mark.asyncio
async def test_list_low_stock_items():
    """Test list_low_stock_items tool with mocked client."""
    context = MagicMock()
    context.state.client.inventory.list_low_stock = AsyncMock(
        return_value=[
            {"sku": "ITEM-001", "name": "Item 1", "in_stock": 5},
            {"sku": "ITEM-002", "name": "Item 2", "in_stock": 3},
            {"sku": "ITEM-003", "name": "Item 3", "in_stock": 8},
        ]
    )

    request = LowStockRequest(threshold=10, limit=50)
    result = await _list_low_stock_items_impl(request, context)

    assert result.total_count == 3
    assert len(result.items) == 3
    assert result.items[0].sku == "ITEM-001"
    assert result.items[0].current_stock == 5
    assert result.items[0].threshold == 10
    context.state.client.inventory.list_low_stock.assert_called_once_with(threshold=10)


@pytest.mark.asyncio
async def test_list_low_stock_items_with_limit():
    """Test list_low_stock_items respects limit parameter."""
    context = MagicMock()
    context.state.client.inventory.list_low_stock = AsyncMock(
        return_value=[
            {"sku": f"ITEM-{i:03d}", "name": f"Item {i}", "in_stock": i}
            for i in range(100)
        ]
    )

    request = LowStockRequest(threshold=10, limit=20)
    result = await _list_low_stock_items_impl(request, context)

    assert result.total_count == 100  # Total available
    assert len(result.items) == 20  # But only 20 returned


@pytest.mark.asyncio
async def test_list_low_stock_items_handles_none_values():
    """Test list_low_stock_items handles None SKU and name."""
    context = MagicMock()
    context.state.client.inventory.list_low_stock = AsyncMock(
        return_value=[
            {"sku": None, "name": None, "in_stock": 5},
        ]
    )

    request = LowStockRequest(threshold=10)
    result = await _list_low_stock_items_impl(request, context)

    assert len(result.items) == 1
    assert result.items[0].sku == ""  # Converts None to empty string
    assert result.items[0].product_name == ""  # Converts None to empty string


@pytest.mark.asyncio
async def test_list_low_stock_default_parameters():
    """Test list_low_stock_items uses default threshold and limit."""
    context = MagicMock()
    context.state.client.inventory.list_low_stock = AsyncMock(return_value=[])

    request = LowStockRequest()  # Use defaults
    await _list_low_stock_items_impl(request, context)

    assert request.threshold == 10  # Default
    assert request.limit == 50  # Default
    context.state.client.inventory.list_low_stock.assert_called_once_with(threshold=10)


@pytest.mark.asyncio
async def test_search_products():
    """Test search_products tool with mocked client."""
    context = MagicMock()

    # Mock Product objects
    mock_product = MagicMock()
    mock_product.id = 123
    mock_product.sku = "WIDGET-001"
    mock_product.name = "Test Widget"
    mock_product.is_sellable = True
    mock_product.stock_level = None

    context.state.client.products.search = AsyncMock(return_value=[mock_product])

    request = SearchProductsRequest(query="widget", limit=20)
    result = await _search_products_impl(request, context)

    assert result.total_count == 1
    assert len(result.products) == 1
    assert result.products[0].id == 123
    assert result.products[0].sku == "WIDGET-001"
    assert result.products[0].name == "Test Widget"
    assert result.products[0].is_sellable is True
    context.state.client.products.search.assert_called_once_with("widget", limit=20)


@pytest.mark.asyncio
async def test_search_products_handles_optional_fields():
    """Test search_products handles missing optional fields."""
    context = MagicMock()

    # Mock Product with missing optional fields
    mock_product = MagicMock()
    mock_product.id = 456
    mock_product.sku = None
    mock_product.name = None
    mock_product.is_sellable = None

    context.state.client.products.search = AsyncMock(return_value=[mock_product])

    request = SearchProductsRequest(query="test")
    result = await _search_products_impl(request, context)

    assert result.products[0].sku == ""  # Converts None to empty string
    assert result.products[0].name == ""
    assert result.products[0].is_sellable is False


@pytest.mark.asyncio
async def test_search_products_default_limit():
    """Test search_products uses default limit."""
    context = MagicMock()
    context.state.client.products.search = AsyncMock(return_value=[])

    request = SearchProductsRequest(query="test")  # Use default limit
    await _search_products_impl(request, context)

    assert request.limit == 20  # Default
    context.state.client.products.search.assert_called_once_with("test", limit=20)


@pytest.mark.asyncio
async def test_search_products_multiple_results():
    """Test search_products with multiple results."""
    context = MagicMock()

    # Mock multiple Product objects
    mock_products = []
    for i in range(5):
        mock_product = MagicMock()
        mock_product.id = i
        mock_product.sku = f"SKU-{i:03d}"
        mock_product.name = f"Product {i}"
        mock_product.is_sellable = i % 2 == 0
        mock_products.append(mock_product)

    context.state.client.products.search = AsyncMock(return_value=mock_products)

    request = SearchProductsRequest(query="product", limit=10)
    result = await _search_products_impl(request, context)

    assert result.total_count == 5
    assert len(result.products) == 5
    assert result.products[0].id == 0
    assert result.products[0].sku == "SKU-000"
    assert result.products[0].is_sellable is True
    assert result.products[1].is_sellable is False


# ============================================================================
# Integration Tests (with real API)
# ============================================================================
# Note: Integration tests would require a real KatanaClient fixture.
# These are placeholders for future implementation once fixture infrastructure
# is set up. For now, all integration testing happens at the server level.
