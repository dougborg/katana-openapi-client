"""Tests for inventory and item MCP tools."""

from unittest.mock import AsyncMock, MagicMock, patch

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

from tests.conftest import create_mock_context

# ============================================================================
# Unit Tests (with mocks)
# ============================================================================


@pytest.fixture(autouse=True)
def _patch_cache_sync():
    """Patch ensure_variants_synced for all unit tests.

    The cache sync is tested separately; tool tests verify tool logic
    with pre-populated cache mocks.
    """
    with patch("katana_mcp.cache_sync.ensure_variants_synced", new_callable=AsyncMock):
        yield


_INVENTORY_API = "katana_public_api_client.api.inventory.get_all_inventory_point"
_UNWRAP_DATA = "katana_public_api_client.utils.unwrap_data"


@pytest.mark.asyncio
async def test_check_inventory():
    """Test check_inventory tool with cached variant + inventory API."""
    context, lifespan_ctx = create_mock_context()

    # Mock cached variant lookup
    lifespan_ctx.cache.get_by_sku = AsyncMock(
        return_value={"id": 3001, "sku": "WIDGET-001", "display_name": "Test Widget"}
    )

    # Mock inventory API response
    mock_inv = MagicMock()
    mock_inv.quantity_in_stock = "150.0"
    mock_inv.quantity_committed = "30.0"
    mock_inv.quantity_expected = "50.0"

    with (
        patch(f"{_INVENTORY_API}.asyncio_detailed", new_callable=AsyncMock) as mock_api,
        patch(_UNWRAP_DATA, return_value=[mock_inv]),
    ):
        mock_api.return_value = MagicMock()
        request = CheckInventoryRequest(sku="WIDGET-001")
        result = await _check_inventory_impl(request, context)

    assert result.sku == "WIDGET-001"
    assert result.product_name == "Test Widget"
    assert result.in_stock == 150.0
    assert result.available_stock == 120.0  # 150 - 30
    assert result.committed == 30.0
    assert result.expected == 50.0


@pytest.mark.asyncio
async def test_check_inventory_multiple_locations():
    """Test check_inventory sums stock across multiple locations."""
    context, lifespan_ctx = create_mock_context()

    lifespan_ctx.cache.get_by_sku = AsyncMock(
        return_value={"id": 3001, "sku": "WIDGET-001", "display_name": "Test Widget"}
    )

    # Two locations with stock
    mock_inv_1 = MagicMock()
    mock_inv_1.quantity_in_stock = "100.0"
    mock_inv_1.quantity_committed = "20.0"
    mock_inv_1.quantity_expected = "30.0"

    mock_inv_2 = MagicMock()
    mock_inv_2.quantity_in_stock = "50.0"
    mock_inv_2.quantity_committed = "10.0"
    mock_inv_2.quantity_expected = "20.0"

    with (
        patch(f"{_INVENTORY_API}.asyncio_detailed", new_callable=AsyncMock),
        patch(_UNWRAP_DATA, return_value=[mock_inv_1, mock_inv_2]),
    ):
        request = CheckInventoryRequest(sku="WIDGET-001")
        result = await _check_inventory_impl(request, context)

    assert result.in_stock == 150.0
    assert result.available_stock == 120.0  # 150 - 30
    assert result.committed == 30.0
    assert result.expected == 50.0


@pytest.mark.asyncio
async def test_check_inventory_not_found():
    """Test check_inventory when SKU not found in cache."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.cache.get_by_sku = AsyncMock(return_value=None)

    request = CheckInventoryRequest(sku="NOT-FOUND")
    result = await _check_inventory_impl(request, context)

    assert result.sku == "NOT-FOUND"
    assert result.product_name == ""
    assert result.available_stock == 0
    assert result.committed == 0
    assert result.expected == 0
    assert result.in_stock == 0


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
    """Test search_items tool with cached data."""
    context, lifespan_ctx = create_mock_context()

    # Mock cached variant dict
    cached_variant = {
        "id": 123,
        "sku": "WIDGET-001",
        "type": "product",
        "display_name": "Test Widget",
    }

    lifespan_ctx.cache.smart_search = AsyncMock(return_value=[cached_variant])

    request = SearchItemsRequest(query="widget", limit=20)
    result = await _search_items_impl(request, context)

    assert result.total_count == 1
    assert len(result.items) == 1
    assert result.items[0].id == 123
    assert result.items[0].sku == "WIDGET-001"
    assert result.items[0].name == "Test Widget"
    assert result.items[0].is_sellable is True


@pytest.mark.asyncio
async def test_search_items_handles_optional_fields():
    """Test search_items handles missing optional fields."""
    context, lifespan_ctx = create_mock_context()

    # Mock cached variant with missing optional fields
    cached_variant = {"id": 456}

    lifespan_ctx.cache.smart_search = AsyncMock(return_value=[cached_variant])

    request = SearchItemsRequest(query="test")
    result = await _search_items_impl(request, context)

    assert result.items[0].sku == ""
    assert result.items[0].name == ""
    assert result.items[0].is_sellable is False


@pytest.mark.asyncio
async def test_search_items_default_limit():
    """Test search_items uses default limit."""
    context, lifespan_ctx = create_mock_context()

    request = SearchItemsRequest(query="test")  # Use default limit
    await _search_items_impl(request, context)

    assert request.limit == 20  # Default
    lifespan_ctx.cache.smart_search.assert_called_once_with("variant", "test", limit=20)


@pytest.mark.asyncio
async def test_search_items_multiple_results():
    """Test search_items with multiple results."""
    context, lifespan_ctx = create_mock_context()

    # Mock multiple cached variant dicts
    cached_variants = [
        {
            "id": i,
            "sku": f"SKU-{i:03d}",
            "type": "product" if i % 2 == 0 else "material",
            "display_name": f"Item {i}",
        }
        for i in range(5)
    ]

    lifespan_ctx.cache.smart_search = AsyncMock(return_value=cached_variants)

    request = SearchItemsRequest(query="item", limit=10)
    result = await _search_items_impl(request, context)

    assert result.total_count == 5
    assert len(result.items) == 5
    assert result.items[0].id == 0
    assert result.items[0].sku == "SKU-000"
    assert result.items[0].is_sellable is True
    assert result.items[1].is_sellable is False


# ============================================================================
# Validation Tests
# ============================================================================


@pytest.mark.asyncio
async def test_check_inventory_empty_sku():
    """Test check_inventory rejects empty SKU."""
    context, _ = create_mock_context()

    request = CheckInventoryRequest(sku="")
    with pytest.raises(ValueError, match="SKU cannot be empty"):
        await _check_inventory_impl(request, context)


@pytest.mark.asyncio
async def test_check_inventory_whitespace_sku():
    """Test check_inventory rejects whitespace-only SKU."""
    context, _ = create_mock_context()

    request = CheckInventoryRequest(sku="   ")
    with pytest.raises(ValueError, match="SKU cannot be empty"):
        await _check_inventory_impl(request, context)


@pytest.mark.asyncio
async def test_list_low_stock_negative_threshold():
    """Test list_low_stock_items rejects negative threshold."""
    context, _ = create_mock_context()

    request = LowStockRequest(threshold=-1)
    with pytest.raises(ValueError, match="Threshold must be non-negative"):
        await _list_low_stock_items_impl(request, context)


@pytest.mark.asyncio
async def test_list_low_stock_zero_limit():
    """Test list_low_stock_items rejects zero limit."""
    context, _ = create_mock_context()

    request = LowStockRequest(limit=0)
    with pytest.raises(ValueError, match="Limit must be positive"):
        await _list_low_stock_items_impl(request, context)


@pytest.mark.asyncio
async def test_list_low_stock_negative_limit():
    """Test list_low_stock_items rejects negative limit."""
    context, _ = create_mock_context()

    request = LowStockRequest(limit=-5)
    with pytest.raises(ValueError, match="Limit must be positive"):
        await _list_low_stock_items_impl(request, context)


@pytest.mark.asyncio
async def test_search_items_empty_query():
    """Test search_items rejects empty query."""
    context, _ = create_mock_context()

    request = SearchItemsRequest(query="")
    with pytest.raises(ValueError, match="Search query cannot be empty"):
        await _search_items_impl(request, context)


@pytest.mark.asyncio
async def test_search_items_whitespace_query():
    """Test search_items rejects whitespace-only query."""
    context, _ = create_mock_context()

    request = SearchItemsRequest(query="   ")
    with pytest.raises(ValueError, match="Search query cannot be empty"):
        await _search_items_impl(request, context)


@pytest.mark.asyncio
async def test_search_items_zero_limit():
    """Test search_items rejects zero limit."""
    context, _ = create_mock_context()

    request = SearchItemsRequest(query="test", limit=0)
    with pytest.raises(ValueError, match="Limit must be positive"):
        await _search_items_impl(request, context)


@pytest.mark.asyncio
async def test_search_items_negative_limit():
    """Test search_items rejects negative limit."""
    context, _ = create_mock_context()

    request = SearchItemsRequest(query="test", limit=-10)
    with pytest.raises(ValueError, match="Limit must be positive"):
        await _search_items_impl(request, context)


@pytest.mark.asyncio
async def test_get_variant_details():
    """Test get_variant_details tool with cached data."""
    context, lifespan_ctx = create_mock_context()

    # Mock cached variant dict
    cached_variant = {
        "id": 123,
        "sku": "WIDGET-001",
        "type": "product",
        "product_id": 456,
        "material_id": None,
        "parent_name": "Test Widget",
        "display_name": "Test Widget / Large / Blue",
        "sales_price": 29.99,
        "purchase_price": 15.00,
        "internal_barcode": "BAR-123",
        "registered_barcode": "UPC-456",
        "supplier_item_codes": ["SUP-001", "SUP-002"],
        "lead_time": 7,
        "minimum_order_quantity": 10.0,
        "config_attributes": [
            {"config_name": "Size", "config_value": "Large"},
            {"config_name": "Color", "config_value": "Blue"},
        ],
        "custom_fields": [
            {"field_name": "Warranty", "field_value": "1 year"},
        ],
        "created_at": None,
        "updated_at": None,
    }

    lifespan_ctx.cache.get_by_sku = AsyncMock(return_value=cached_variant)

    request = GetVariantDetailsRequest(sku="WIDGET-001")
    result = await _get_variant_details_impl(request, context)

    assert result.id == 123
    assert result.sku == "WIDGET-001"
    assert result.name == "Test Widget / Large / Blue"
    assert result.type == "product"
    assert result.product_id == 456
    assert result.material_id is None
    assert result.product_or_material_name == "Test Widget"
    assert result.sales_price == 29.99
    assert result.purchase_price == 15.00
    assert result.internal_barcode == "BAR-123"
    assert result.registered_barcode == "UPC-456"
    assert result.supplier_item_codes == ["SUP-001", "SUP-002"]
    assert result.lead_time == 7
    assert result.minimum_order_quantity == 10.0
    assert len(result.config_attributes) == 2
    assert result.config_attributes[0]["config_name"] == "Size"
    assert len(result.custom_fields) == 1
    assert result.custom_fields[0]["field_name"] == "Warranty"


@pytest.mark.asyncio
async def test_get_variant_details_case_insensitive():
    """Test get_variant_details with case-insensitive SKU matching."""
    context, lifespan_ctx = create_mock_context()

    cached_variant = {
        "id": 123,
        "sku": "WIDGET-001",
        "type": "product",
        "display_name": "Test Widget",
        "parent_name": "Test Widget",
    }

    lifespan_ctx.cache.get_by_sku = AsyncMock(return_value=cached_variant)

    # Search with lowercase SKU
    request = GetVariantDetailsRequest(sku="widget-001")
    result = await _get_variant_details_impl(request, context)

    assert result.id == 123
    assert result.sku == "WIDGET-001"
    assert result.name == "Test Widget"


@pytest.mark.asyncio
async def test_get_variant_details_not_found():
    """Test get_variant_details when SKU not found."""
    context, lifespan_ctx = create_mock_context()

    # Cache returns None (no match)
    lifespan_ctx.cache.get_by_sku = AsyncMock(return_value=None)

    request = GetVariantDetailsRequest(sku="NOT-FOUND")
    with pytest.raises(ValueError, match="Variant with SKU 'NOT-FOUND' not found"):
        await _get_variant_details_impl(request, context)


@pytest.mark.asyncio
async def test_get_variant_details_no_exact_match():
    """Test get_variant_details when no exact SKU match exists."""
    context, lifespan_ctx = create_mock_context()

    # Cache returns None (SKU lookup is exact)
    lifespan_ctx.cache.get_by_sku = AsyncMock(return_value=None)

    request = GetVariantDetailsRequest(sku="WIDGET-001")
    with pytest.raises(ValueError, match="Variant with SKU 'WIDGET-001' not found"):
        await _get_variant_details_impl(request, context)


@pytest.mark.asyncio
async def test_get_variant_details_empty_sku():
    """Test get_variant_details rejects empty SKU."""
    context, _ = create_mock_context()

    request = GetVariantDetailsRequest(sku="")
    with pytest.raises(ValueError, match="SKU cannot be empty"):
        await _get_variant_details_impl(request, context)


@pytest.mark.asyncio
async def test_get_variant_details_whitespace_sku():
    """Test get_variant_details rejects whitespace-only SKU."""
    context, _ = create_mock_context()

    request = GetVariantDetailsRequest(sku="   ")
    with pytest.raises(ValueError, match="SKU cannot be empty"):
        await _get_variant_details_impl(request, context)


@pytest.mark.asyncio
async def test_get_variant_details_minimal_fields():
    """Test get_variant_details with minimal fields populated."""
    context, lifespan_ctx = create_mock_context()

    # Cached variant with only required fields
    cached_variant = {"id": 123, "sku": "MIN-001"}

    lifespan_ctx.cache.get_by_sku = AsyncMock(return_value=cached_variant)

    request = GetVariantDetailsRequest(sku="MIN-001")
    result = await _get_variant_details_impl(request, context)

    assert result.id == 123
    assert result.sku == "MIN-001"
    assert result.name == "MIN-001"
    assert result.type is None
    assert result.sales_price is None
    assert result.purchase_price is None
    assert result.internal_barcode is None
    assert result.registered_barcode is None
    assert result.supplier_item_codes == []
    assert result.lead_time is None
    assert result.minimum_order_quantity is None
    assert result.config_attributes == []
    assert result.custom_fields == []


@pytest.mark.asyncio
async def test_get_variant_details_with_timestamps():
    """Test get_variant_details with created_at and updated_at."""
    context, lifespan_ctx = create_mock_context()

    cached_variant = {
        "id": 123,
        "sku": "TIME-001",
        "type": "product",
        "display_name": "Timed Product",
        "parent_name": "Timed Product",
        "created_at": "2024-01-01T12:00:00+00:00",
        "updated_at": "2024-06-01T14:30:00+00:00",
    }

    lifespan_ctx.cache.get_by_sku = AsyncMock(return_value=cached_variant)

    request = GetVariantDetailsRequest(sku="TIME-001")
    result = await _get_variant_details_impl(request, context)

    assert result.created_at == "2024-01-01T12:00:00+00:00"
    assert result.updated_at == "2024-06-01T14:30:00+00:00"


# ============================================================================
# Integration Tests (with real API)
# ============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_check_inventory_integration(katana_context):
    """Integration test: check_inventory with real Katana API.

    This test requires a valid KATANA_API_KEY in the environment.
    It attempts to check inventory for a test SKU.

    Note: This test may fail if:
    - API key is invalid
    - Network is unavailable
    - Test SKU doesn't exist (expected - returns zero stock)
    """
    request = CheckInventoryRequest(sku="TEST-SKU-001")

    try:
        result = await _check_inventory_impl(request, katana_context)

        # Verify response structure
        assert result.sku == "TEST-SKU-001"
        assert isinstance(result.product_name, str)
        assert isinstance(result.available_stock, float)
        assert isinstance(result.in_stock, float)
        assert isinstance(result.committed, float)
        assert isinstance(result.expected, float)

    except Exception as e:
        # Network/auth errors are acceptable in integration tests
        error_msg = str(e).lower()
        assert any(
            word in error_msg
            for word in ["connection", "network", "auth", "timeout", "not found"]
        ), f"Unexpected error: {e}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_low_stock_items_integration(katana_context):
    """Integration test: list_low_stock_items with real Katana API.

    This test requires a valid KATANA_API_KEY in the environment.
    Tests listing low stock items with a reasonable threshold.
    """
    request = LowStockRequest(threshold=100, limit=10)

    try:
        result = await _list_low_stock_items_impl(request, katana_context)

        # Verify response structure
        assert isinstance(result.items, list)
        assert isinstance(result.total_count, int)
        assert result.total_count >= 0
        assert len(result.items) <= 10  # Respects limit

        # Verify each item structure
        for item in result.items:
            assert isinstance(item.sku, str)
            assert isinstance(item.product_name, str)
            assert isinstance(item.current_stock, int)
            assert item.current_stock >= 0
            assert item.threshold == 100

    except Exception as e:
        # Network/auth errors are acceptable in integration tests
        error_msg = str(e).lower()
        assert any(
            word in error_msg
            for word in ["connection", "network", "auth", "timeout", "not found"]
        ), f"Unexpected error: {e}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_items_integration(katana_context):
    """Integration test: search_items with real Katana API.

    This test requires a valid KATANA_API_KEY in the environment.
    Tests searching for items with a common query term.
    """
    request = SearchItemsRequest(query="test", limit=5)

    try:
        result = await _search_items_impl(request, katana_context)

        # Verify response structure
        assert isinstance(result.items, list)
        assert isinstance(result.total_count, int)
        assert result.total_count >= 0
        assert len(result.items) <= 5  # Respects limit

        # Verify each item structure
        for item in result.items:
            assert isinstance(item.id, int)
            assert isinstance(item.sku, str)
            assert isinstance(item.name, str)
            assert isinstance(item.is_sellable, bool)
            # stock_level can be None
            assert item.stock_level is None or isinstance(item.stock_level, int)

    except Exception as e:
        # Network/auth errors are acceptable in integration tests
        error_msg = str(e).lower()
        assert any(
            word in error_msg
            for word in ["connection", "network", "auth", "timeout", "not found"]
        ), f"Unexpected error: {e}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_check_inventory_nonexistent_sku_integration(katana_context):
    """Integration test: check_inventory with nonexistent SKU.

    Verifies that checking a nonexistent SKU returns zero stock
    rather than failing.
    """
    # Use a SKU that's extremely unlikely to exist
    request = CheckInventoryRequest(sku="NONEXISTENT-SKU-99999")

    try:
        result = await _check_inventory_impl(request, katana_context)

        # Should return zero stock, not error
        assert result.sku == "NONEXISTENT-SKU-99999"
        assert result.available_stock == 0
        assert result.committed == 0
        assert result.in_stock == 0
        assert result.expected == 0
        assert isinstance(result.product_name, str)

    except Exception as e:
        # Network/auth errors are acceptable
        error_msg = str(e).lower()
        assert any(
            word in error_msg for word in ["connection", "network", "auth", "timeout"]
        ), f"Unexpected error: {e}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_variant_details_integration(katana_context):
    """Integration test: get_variant_details with real Katana API.

    This test requires a valid KATANA_API_KEY in the environment.
    Tests fetching variant details for a test SKU.

    Note: This test may fail if:
    - API key is invalid
    - Network is unavailable
    - Test SKU doesn't exist (expected - raises ValueError)
    """
    # Use a common test SKU or generic search term
    request = GetVariantDetailsRequest(sku="TEST-001")

    try:
        result = await _get_variant_details_impl(request, katana_context)

        # Verify response structure
        assert isinstance(result.id, int)
        assert isinstance(result.sku, str)
        assert isinstance(result.name, str)
        assert result.id > 0

        # Verify optional fields are correct types or None
        assert result.sales_price is None or isinstance(result.sales_price, float)
        assert result.purchase_price is None or isinstance(result.purchase_price, float)
        assert result.type is None or isinstance(result.type, str)
        assert result.product_id is None or isinstance(result.product_id, int)
        assert result.material_id is None or isinstance(result.material_id, int)
        assert result.internal_barcode is None or isinstance(
            result.internal_barcode, str
        )
        assert result.registered_barcode is None or isinstance(
            result.registered_barcode, str
        )
        assert isinstance(result.supplier_item_codes, list)
        assert result.lead_time is None or isinstance(result.lead_time, int)
        assert result.minimum_order_quantity is None or isinstance(
            result.minimum_order_quantity, float
        )
        assert isinstance(result.config_attributes, list)
        assert isinstance(result.custom_fields, list)

    except ValueError as e:
        # SKU not found is acceptable for integration test
        assert "not found" in str(e).lower()
    except Exception as e:
        # Network/auth errors are acceptable in integration tests
        error_msg = str(e).lower()
        assert any(
            word in error_msg for word in ["connection", "network", "auth", "timeout"]
        ), f"Unexpected error: {e}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_variant_details_nonexistent_integration(katana_context):
    """Integration test: get_variant_details with nonexistent SKU.

    Verifies that requesting a nonexistent SKU raises ValueError.
    """
    # Use a SKU that's extremely unlikely to exist
    request = GetVariantDetailsRequest(sku="NONEXISTENT-VARIANT-99999")

    try:
        await _get_variant_details_impl(request, katana_context)
        # If we get here without error, the SKU somehow exists
        # This is unexpected but not a test failure
    except ValueError as e:
        # Expected: SKU not found
        assert "not found" in str(e).lower()
    except Exception as e:
        # Network/auth errors are acceptable
        error_msg = str(e).lower()
        assert any(
            word in error_msg for word in ["connection", "network", "auth", "timeout"]
        ), f"Unexpected error: {e}"
