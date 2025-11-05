"""Tests for inventory and item MCP tools."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from katana_mcp.tools.foundation.inventory import (
    CheckInventoryRequest,
    LowStockRequest,
    _check_inventory_impl,
    _list_low_stock_items_impl,
)
from katana_mcp.tools.foundation.items import (
    SearchItemsRequest,
    _search_items_impl,
)

# ============================================================================
# Test Helpers
# ============================================================================


def create_mock_context():
    """Create a mock context with proper FastMCP structure.

    Returns context with request_context.lifespan_context.client accessible.
    """
    context = MagicMock()
    mock_request_context = MagicMock()
    mock_lifespan_context = MagicMock()
    context.request_context = mock_request_context
    mock_request_context.lifespan_context = mock_lifespan_context
    return context, mock_lifespan_context


# ============================================================================
# Unit Tests (with mocks)
# ============================================================================


@pytest.mark.asyncio
async def test_check_inventory():
    """Test check_inventory tool with mocked client."""
    context, lifespan_ctx = create_mock_context()

    # Mock Product with stock_information
    mock_product = MagicMock()
    mock_product.name = "Test Widget"
    mock_stock = MagicMock()
    mock_stock.available = 100
    mock_stock.allocated = 30
    mock_stock.in_stock = 150
    mock_product.stock_information = mock_stock

    lifespan_ctx.client.inventory.check_stock = AsyncMock(return_value=mock_product)

    request = CheckInventoryRequest(sku="WIDGET-001")
    result = await _check_inventory_impl(request, context)

    assert result.sku == "WIDGET-001"
    assert result.product_name == "Test Widget"
    assert result.available_stock == 100
    assert result.in_production == 0  # Not available in API yet
    assert result.committed == 30
    lifespan_ctx.client.inventory.check_stock.assert_called_once_with("WIDGET-001")


@pytest.mark.asyncio
async def test_check_inventory_missing_fields():
    """Test check_inventory handles missing optional fields."""
    context, lifespan_ctx = create_mock_context()

    # Mock Product with missing stock_information
    mock_product = MagicMock()
    mock_product.name = ""
    mock_product.stock_information = None

    lifespan_ctx.client.inventory.check_stock = AsyncMock(return_value=mock_product)

    request = CheckInventoryRequest(sku="WIDGET-002")
    result = await _check_inventory_impl(request, context)

    assert result.sku == "WIDGET-002"
    assert result.product_name == ""  # Default empty string
    assert result.available_stock == 0  # Default to 0
    assert result.committed == 0  # Default to 0


@pytest.mark.asyncio
async def test_check_inventory_not_found():
    """Test check_inventory when SKU not found."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.client.inventory.check_stock = AsyncMock(return_value=None)

    request = CheckInventoryRequest(sku="NOT-FOUND")
    result = await _check_inventory_impl(request, context)

    assert result.sku == "NOT-FOUND"
    assert result.product_name == ""
    assert result.available_stock == 0
    assert result.committed == 0


@pytest.mark.asyncio
async def test_list_low_stock_items():
    """Test list_low_stock_items tool with mocked client."""
    context, lifespan_ctx = create_mock_context()

    # Mock Product objects with stock_information
    mock_products = []
    for sku, name, stock in [
        ("ITEM-001", "Item 1", 5),
        ("ITEM-002", "Item 2", 3),
        ("ITEM-003", "Item 3", 8),
    ]:
        product = MagicMock()
        product.sku = sku
        product.name = name
        stock_info = MagicMock()
        stock_info.in_stock = stock
        product.stock_information = stock_info
        mock_products.append(product)

    lifespan_ctx.client.inventory.list_low_stock = AsyncMock(return_value=mock_products)

    request = LowStockRequest(threshold=10, limit=50)
    result = await _list_low_stock_items_impl(request, context)

    assert result.total_count == 3
    assert len(result.items) == 3
    assert result.items[0].sku == "ITEM-001"
    assert result.items[0].current_stock == 5
    assert result.items[0].threshold == 10
    lifespan_ctx.client.inventory.list_low_stock.assert_called_once_with(threshold=10)


@pytest.mark.asyncio
async def test_list_low_stock_items_with_limit():
    """Test list_low_stock_items respects limit parameter."""
    context, lifespan_ctx = create_mock_context()

    # Mock 100 Product objects
    mock_products = []
    for i in range(100):
        product = MagicMock()
        product.sku = f"ITEM-{i:03d}"
        product.name = f"Item {i}"
        stock_info = MagicMock()
        stock_info.in_stock = i
        product.stock_information = stock_info
        mock_products.append(product)

    lifespan_ctx.client.inventory.list_low_stock = AsyncMock(return_value=mock_products)

    request = LowStockRequest(threshold=10, limit=20)
    result = await _list_low_stock_items_impl(request, context)

    assert result.total_count == 100  # Total available
    assert len(result.items) == 20  # But only 20 returned


@pytest.mark.asyncio
async def test_list_low_stock_items_handles_none_values():
    """Test list_low_stock_items handles None SKU and name."""
    context, lifespan_ctx = create_mock_context()

    # Mock Product with None values
    product = MagicMock()
    product.sku = None
    product.name = None
    stock_info = MagicMock()
    stock_info.in_stock = 5
    product.stock_information = stock_info

    lifespan_ctx.client.inventory.list_low_stock = AsyncMock(return_value=[product])

    request = LowStockRequest(threshold=10)
    result = await _list_low_stock_items_impl(request, context)

    assert len(result.items) == 1
    assert result.items[0].sku == ""  # Converts None to empty string
    assert result.items[0].product_name == ""  # Converts None to empty string


@pytest.mark.asyncio
async def test_list_low_stock_default_parameters():
    """Test list_low_stock_items uses default threshold and limit."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.client.inventory.list_low_stock = AsyncMock(return_value=[])

    request = LowStockRequest()  # Use defaults
    await _list_low_stock_items_impl(request, context)

    assert request.threshold == 10  # Default
    assert request.limit == 50  # Default
    lifespan_ctx.client.inventory.list_low_stock.assert_called_once_with(threshold=10)


@pytest.mark.asyncio
async def test_search_items():
    """Test search_items tool with mocked client."""
    context, lifespan_ctx = create_mock_context()

    # Mock Variant objects
    mock_variant = MagicMock()
    mock_variant.id = 123
    mock_variant.sku = "WIDGET-001"
    mock_variant.type_ = "product"
    mock_variant.get_display_name = MagicMock(return_value="Test Widget")

    lifespan_ctx.client.variants.search = AsyncMock(return_value=[mock_variant])

    request = SearchItemsRequest(query="widget", limit=20)
    result = await _search_items_impl(request, context)

    assert result.total_count == 1
    assert len(result.items) == 1
    assert result.items[0].id == 123
    assert result.items[0].sku == "WIDGET-001"
    assert result.items[0].name == "Test Widget"
    assert result.items[0].is_sellable is True
    lifespan_ctx.client.variants.search.assert_called_once_with("widget", limit=20)


@pytest.mark.asyncio
async def test_search_items_handles_optional_fields():
    """Test search_items handles missing optional fields."""
    context, lifespan_ctx = create_mock_context()

    # Mock Variant with missing optional fields
    mock_variant = MagicMock()
    mock_variant.id = 456
    mock_variant.sku = None
    mock_variant.type_ = None
    mock_variant.get_display_name = MagicMock(return_value="")

    lifespan_ctx.client.variants.search = AsyncMock(return_value=[mock_variant])

    request = SearchItemsRequest(query="test")
    result = await _search_items_impl(request, context)

    assert result.items[0].sku == ""  # Converts None to empty string
    assert result.items[0].name == ""
    assert result.items[0].is_sellable is False


@pytest.mark.asyncio
async def test_search_items_default_limit():
    """Test search_items uses default limit."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.client.variants.search = AsyncMock(return_value=[])

    request = SearchItemsRequest(query="test")  # Use default limit
    await _search_items_impl(request, context)

    assert request.limit == 20  # Default
    lifespan_ctx.client.variants.search.assert_called_once_with("test", limit=20)


@pytest.mark.asyncio
async def test_search_items_multiple_results():
    """Test search_items with multiple results."""
    context, lifespan_ctx = create_mock_context()

    # Mock multiple Variant objects
    mock_variants = []
    for i in range(5):
        mock_variant = MagicMock()
        mock_variant.id = i
        mock_variant.sku = f"SKU-{i:03d}"
        mock_variant.type_ = "product" if i % 2 == 0 else "material"
        mock_variant.get_display_name = MagicMock(return_value=f"Item {i}")
        mock_variants.append(mock_variant)

    lifespan_ctx.client.variants.search = AsyncMock(return_value=mock_variants)

    request = SearchItemsRequest(query="item", limit=10)
    result = await _search_items_impl(request, context)

    assert result.total_count == 5
    assert len(result.items) == 5
    assert result.items[0].id == 0
    assert result.items[0].sku == "SKU-000"
    assert result.items[0].is_sellable is True
    assert result.items[1].is_sellable is False


# ============================================================================
# Integration Tests (with real API)
# ============================================================================
# Note: Integration tests would require a real KatanaClient fixture.
# These are placeholders for future implementation once fixture infrastructure
# is set up. For now, all integration testing happens at the server level.
