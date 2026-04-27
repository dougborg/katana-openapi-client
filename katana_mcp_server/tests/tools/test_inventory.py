"""Tests for inventory and item MCP tools."""

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from katana_mcp.tools.foundation.inventory import (
    CheckInventoryRequest,
    CreateStockAdjustmentRequest,
    DeleteStockAdjustmentRequest,
    GetInventoryMovementsRequest,
    ListStockAdjustmentsRequest,
    LowStockRequest,
    StockAdjustmentRow,
    UpdateStockAdjustmentParams,
    _check_inventory_impl,
    _create_stock_adjustment_impl,
    _delete_stock_adjustment_impl,
    _get_inventory_movements_impl,
    _list_low_stock_items_impl,
    _list_stock_adjustments_impl,
    _update_stock_adjustment_impl,
    check_inventory,
    get_inventory_movements,
    list_low_stock_items,
    list_stock_adjustments,
)
from katana_mcp.tools.foundation.items import (
    GetVariantDetailsRequest,
    SearchItemsRequest,
    _get_variant_details_impl,
    _search_items_impl,
    get_variant_details,
    search_items,
)
from pydantic import ValidationError

from katana_public_api_client.client_types import UNSET
from tests.conftest import create_mock_context, patch_typed_cache_sync
from tests.factories import (
    make_stock_adjustment,
    make_stock_adjustment_row,
    seed_cache,
)


def _content_text(result) -> str:
    """Extract the text of a ToolResult's first content block."""
    return result.content[0].text


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
        request = CheckInventoryRequest(skus_or_variant_ids=["WIDGET-001"])
        _inv_results = await _check_inventory_impl(request, context)
        result = _inv_results[0]

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
        request = CheckInventoryRequest(skus_or_variant_ids=["WIDGET-001"])
        _inv_results = await _check_inventory_impl(request, context)
        result = _inv_results[0]

    assert result.in_stock == 150.0
    assert result.available_stock == 120.0  # 150 - 30
    assert result.committed == 30.0
    assert result.expected == 50.0


@pytest.mark.asyncio
async def test_check_inventory_not_found():
    """Test check_inventory when SKU not found in cache."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.cache.get_by_sku = AsyncMock(return_value=None)

    request = CheckInventoryRequest(skus_or_variant_ids=["NOT-FOUND"])
    _inv_results = await _check_inventory_impl(request, context)
    result = _inv_results[0]

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
# get_inventory_movements Tests
# ============================================================================

_MOVEMENTS_API = (
    "katana_public_api_client.api.inventory_movements.get_all_inventory_movements"
)


@pytest.mark.asyncio
async def test_get_inventory_movements():
    """Test get_inventory_movements with mocked API."""
    context, lifespan_ctx = create_mock_context()

    lifespan_ctx.cache.get_by_sku = AsyncMock(
        return_value={"id": 3001, "sku": "WIDGET-001", "display_name": "Test Widget"}
    )

    mock_movement = MagicMock()
    mock_movement.id = 9001
    mock_movement.variant_id = 3001
    mock_movement.location_id = 1
    mock_movement.movement_date.isoformat.return_value = "2026-04-01T12:00:00+00:00"
    mock_movement.quantity_change = -5.0
    mock_movement.balance_after = 10.0
    mock_movement.resource_type.value = "ProductionIngredient"
    mock_movement.resource_id = 5001
    mock_movement.caused_by_order_no = "MO-123"
    mock_movement.caused_by_resource_id = 5001
    mock_movement.value_per_unit = 25.50
    mock_movement.value_in_stock_after = 255.0
    mock_movement.average_cost_after = 25.50
    mock_movement.rank = 1
    mock_movement.created_at = UNSET
    mock_movement.updated_at = UNSET

    with (
        patch(f"{_MOVEMENTS_API}.asyncio_detailed", new_callable=AsyncMock),
        patch(_UNWRAP_DATA, return_value=[mock_movement]),
    ):
        request = GetInventoryMovementsRequest(sku="WIDGET-001")
        result = await _get_inventory_movements_impl(request, context)

    assert result.sku == "WIDGET-001"
    assert result.total_count == 1
    assert result.movements[0].quantity_change == -5.0
    assert result.movements[0].caused_by_order_no == "MO-123"


@pytest.mark.asyncio
async def test_get_inventory_movements_not_found():
    """Test get_inventory_movements when SKU not found."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.cache.get_by_sku = AsyncMock(return_value=None)

    request = GetInventoryMovementsRequest(sku="NOT-FOUND")
    result = await _get_inventory_movements_impl(request, context)

    assert result.sku == "NOT-FOUND"
    assert result.total_count == 0
    assert result.movements == []


@pytest.mark.asyncio
async def test_get_inventory_movements_full_field_coverage():
    """Every InventoryMovement attrs field flows through to MovementInfo.

    Pins the exhaustive-surface contract: any future InventoryMovement field
    addition MUST either land on MovementInfo or explicitly update this test.
    Covers the previously-dropped fields: id, variant_id, location_id,
    resource_id, caused_by_resource_id, value_in_stock_after, average_cost_after,
    rank, created_at, updated_at.
    """
    context, lifespan_ctx = create_mock_context()

    lifespan_ctx.cache.get_by_sku = AsyncMock(
        return_value={"id": 3001, "sku": "WIDGET-001", "display_name": "Test Widget"}
    )

    mock_movement = MagicMock()
    mock_movement.id = 12345
    mock_movement.variant_id = 3001
    mock_movement.location_id = 1
    mock_movement.movement_date.isoformat.return_value = "2026-04-15T10:30:00+00:00"
    mock_movement.quantity_change = 100.0
    mock_movement.balance_after = 500.0
    mock_movement.resource_type.value = "PurchaseOrderRow"
    mock_movement.resource_id = 5001
    mock_movement.caused_by_order_no = "PO-2024-001"
    mock_movement.caused_by_resource_id = 5002
    mock_movement.value_per_unit = 25.5
    mock_movement.value_in_stock_after = 12750.0
    mock_movement.average_cost_after = 25.5
    mock_movement.rank = 1

    created_at = datetime(2026, 4, 15, 10, 30, 0, tzinfo=UTC)
    updated_at = datetime(2026, 4, 15, 10, 31, 0, tzinfo=UTC)
    mock_movement.created_at = created_at
    mock_movement.updated_at = updated_at

    with (
        patch(f"{_MOVEMENTS_API}.asyncio_detailed", new_callable=AsyncMock),
        patch(_UNWRAP_DATA, return_value=[mock_movement]),
    ):
        request = GetInventoryMovementsRequest(sku="WIDGET-001")
        result = await _get_inventory_movements_impl(request, context)

    assert result.total_count == 1
    m = result.movements[0]
    # Every field from InventoryMovement attrs model must flow through.
    assert m.id == 12345
    assert m.variant_id == 3001
    assert m.location_id == 1
    assert m.resource_type == "PurchaseOrderRow"
    assert m.resource_id == 5001
    assert m.caused_by_order_no == "PO-2024-001"
    assert m.caused_by_resource_id == 5002
    assert m.movement_date == "2026-04-15T10:30:00+00:00"
    assert m.quantity_change == 100.0
    assert m.balance_after == 500.0
    assert m.value_per_unit == 25.5
    assert m.value_in_stock_after == 12750.0
    assert m.average_cost_after == 25.5
    assert m.rank == 1
    assert m.created_at == created_at.isoformat()
    assert m.updated_at == updated_at.isoformat()


@pytest.mark.asyncio
async def test_get_inventory_movements_markdown_uses_canonical_names():
    """Markdown render uses canonical Pydantic field names as column headers.

    Pins the #346 follow-on convention so a future refactor can't silently
    swap back to friendly-name labels like ``Date`` or ``Change``.
    """
    from katana_mcp.tools.foundation.inventory import (
        InventoryMovementsResponse,
        MovementInfo,
    )

    movements = [
        MovementInfo(
            id=9001,
            variant_id=3001,
            location_id=1,
            resource_type="PurchaseOrderRow",
            resource_id=5001,
            caused_by_order_no="PO-2024-001",
            caused_by_resource_id=5002,
            movement_date="2026-04-15T10:30:00+00:00",
            quantity_change=100.0,
            balance_after=500.0,
            value_per_unit=25.5,
            value_in_stock_after=12750.0,
            average_cost_after=25.5,
            rank=1,
            created_at="2026-04-15T10:30:00+00:00",
            updated_at="2026-04-15T10:31:00+00:00",
        )
    ]
    with patch(
        "katana_mcp.tools.foundation.inventory._get_inventory_movements_impl",
        new_callable=AsyncMock,
    ) as mock_impl:
        mock_impl.return_value = InventoryMovementsResponse(
            sku="WIDGET-001",
            product_name="Test Widget",
            movements=movements,
            total_count=1,
        )
        context, _ = create_mock_context()
        result = await get_inventory_movements(sku="WIDGET-001", context=context)

    md = _content_text(result)
    # Parse the header row directly and assert the exact column names.
    # Substring checks like `"id" in md` are too weak: they pass even if the
    # `id` column is missing, because `variant_id` / `resource_id` also contain
    # "id". Pinning on the exact column sequence catches silent reorderings
    # and drops.
    header_line = next(line for line in md.splitlines() if line.startswith("| id |"))
    columns = [c.strip() for c in header_line.split("|")[1:-1]]
    assert columns == [
        "id",
        "movement_date",
        "variant_id",
        "location_id",
        "resource_type",
        "resource_id",
        "caused_by_order_no",
        "caused_by_resource_id",
        "quantity_change",
        "balance_after",
        "value_per_unit",
        "value_in_stock_after",
        "average_cost_after",
        "rank",
        "created_at",
        "updated_at",
    ]
    # And the header labels too
    assert "**sku**: WIDGET-001" in md
    assert "**product_name**: Test Widget" in md
    assert "**total_count**: 1" in md
    # Should NOT contain the old friendly labels
    assert "| Date |" not in md
    assert "| Change |" not in md
    assert "| Balance |" not in md
    assert "| Type |" not in md
    assert "| Order |" not in md


# ============================================================================
# create_stock_adjustment Tests
# ============================================================================

_SA_API = "katana_public_api_client.api.stock_adjustment.create_stock_adjustment"


@pytest.mark.asyncio
async def test_create_stock_adjustment_preview():
    """Test stock adjustment preview mode."""
    context, lifespan_ctx = create_mock_context()

    lifespan_ctx.cache.get_by_sku = AsyncMock(
        return_value={"id": 3001, "sku": "WIDGET-001", "display_name": "Test Widget"}
    )

    request = CreateStockAdjustmentRequest(
        location_id=1,
        rows=[StockAdjustmentRow(sku="WIDGET-001", quantity=5)],
        reason="Test adjustment",
        confirm=False,
    )
    result = await _create_stock_adjustment_impl(request, context)

    assert result.is_preview is True
    assert "WIDGET-001" in result.rows_summary
    assert "+5.0" in result.rows_summary


@pytest.mark.asyncio
async def test_create_stock_adjustment_sku_not_found():
    """Test stock adjustment with unknown SKU."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.cache.get_by_sku = AsyncMock(return_value=None)

    request = CreateStockAdjustmentRequest(
        location_id=1,
        rows=[StockAdjustmentRow(sku="BAD-SKU", quantity=1)],
        confirm=False,
    )
    with pytest.raises(ValueError, match="SKU 'BAD-SKU' not found"):
        await _create_stock_adjustment_impl(request, context)


@pytest.mark.asyncio
async def test_create_stock_adjustment_empty_rows():
    """Test stock adjustment with no rows."""
    context, _ = create_mock_context()

    request = CreateStockAdjustmentRequest(
        location_id=1,
        rows=[],
        confirm=False,
    )
    with pytest.raises(ValueError, match="At least one adjustment row"):
        await _create_stock_adjustment_impl(request, context)


# ============================================================================
# Validation Tests
# ============================================================================


@pytest.mark.asyncio
async def test_check_inventory_empty_sku():
    """Test check_inventory rejects empty SKU string in the list."""
    context, _ = create_mock_context()

    request = CheckInventoryRequest(skus_or_variant_ids=[""])
    with pytest.raises(ValueError, match="SKU cannot be empty"):
        await _check_inventory_impl(request, context)


@pytest.mark.asyncio
async def test_check_inventory_whitespace_sku():
    """Test check_inventory rejects whitespace-only SKU."""
    context, _ = create_mock_context()

    request = CheckInventoryRequest(skus_or_variant_ids=["   "])
    with pytest.raises(ValueError, match="SKU cannot be empty"):
        await _check_inventory_impl(request, context)


@pytest.mark.asyncio
async def test_check_inventory_empty_list_rejected():
    """Test CheckInventoryRequest rejects empty skus_or_variant_ids list (min_length=1)."""
    with pytest.raises(ValidationError):
        CheckInventoryRequest(skus_or_variant_ids=[])


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
    _var_results = await _get_variant_details_impl(request, context)
    result = _var_results[0]

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
    _var_results = await _get_variant_details_impl(request, context)
    result = _var_results[0]

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
    _var_results = await _get_variant_details_impl(request, context)
    result = _var_results[0]

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
    _var_results = await _get_variant_details_impl(request, context)
    result = _var_results[0]

    assert result.created_at == "2024-01-01T12:00:00+00:00"
    assert result.updated_at == "2024-06-01T14:30:00+00:00"


# ============================================================================
# list_stock_adjustments Tests (cache-backed)
# ============================================================================
#
# Post-#376: list_stock_adjustments reads from the SQLModel typed cache via
# ``_list_stock_adjustments_impl``. Tests seed ``CachedStockAdjustment`` /
# ``CachedStockAdjustmentRow`` rows with the factories from ``tests/factories``
# and assert the impl's filter/pagination logic against the query results.
# The ``no_sync`` fixture stubs ``ensure_stock_adjustments_synced`` so the
# impl never tries to talk to the API during these unit tests.
#
# update_stock_adjustment / delete_stock_adjustment tests further down still
# go through the live API path (those tools call the Katana API directly),
# so the mock-API helpers below are kept for them.

_SA_GET_ALL = "katana_public_api_client.api.stock_adjustment.get_all_stock_adjustments"
_SA_UNWRAP_DATA = "katana_public_api_client.utils.unwrap_data"
_SA_UPDATE = "katana_public_api_client.api.stock_adjustment.update_stock_adjustment"
_SA_DELETE = "katana_public_api_client.api.stock_adjustment.delete_stock_adjustment"
_SA_UNWRAP_AS = "katana_public_api_client.utils.unwrap_as"
_SA_UNWRAP = "katana_public_api_client.utils.unwrap"


def _make_mock_adjustment(
    *,
    id: int = 500,
    stock_adjustment_number: str = "SA-TEST-001",
    location_id: int = 1,
    reason: str | None = "Cycle count",
    additional_info: str | None = None,
    rows: list | None = None,
    created_at: datetime | None = None,
) -> MagicMock:
    """Build a mock StockAdjustment attrs object for live-API-path tests
    (``update_stock_adjustment`` / ``delete_stock_adjustment``)."""
    adj = MagicMock()
    adj.id = id
    adj.stock_adjustment_number = stock_adjustment_number
    adj.location_id = location_id
    adj.reason = reason if reason is not None else UNSET
    adj.additional_info = additional_info if additional_info is not None else UNSET
    adj.stock_adjustment_date = datetime(2026, 4, 1, 9, 0, tzinfo=UTC)
    adj.created_at = (
        created_at if created_at is not None else datetime(2026, 4, 1, 9, 0, tzinfo=UTC)
    )
    adj.updated_at = datetime(2026, 4, 1, 9, 0, tzinfo=UTC)
    adj.stock_adjustment_rows = rows if rows is not None else []
    return adj


def _make_mock_adjustment_row(
    *,
    id: int = 1,
    variant_id: int = 100,
    quantity: float = 5.0,
    cost_per_unit: float | None = None,
) -> MagicMock:
    """Build a mock StockAdjustmentRow for live-API-path tests."""
    row = MagicMock()
    row.id = id
    row.variant_id = variant_id
    row.quantity = quantity
    row.cost_per_unit = cost_per_unit if cost_per_unit is not None else UNSET
    return row


@pytest.fixture
def no_sync():
    """Patch ``ensure_stock_adjustments_synced`` to a no-op for these tests."""
    with patch_typed_cache_sync("stock_adjustments"):
        yield


def test_list_stock_adjustments_rejects_limit_above_page_cap():
    """`limit > 250` is rejected at the schema boundary."""
    with pytest.raises(ValidationError):
        ListStockAdjustmentsRequest(limit=500)


@pytest.mark.asyncio
async def test_list_stock_adjustments_filters_by_ids(context_with_typed_cache, no_sync):
    """`ids` restricts the returned set to the specified adjustment IDs."""
    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [
            make_stock_adjustment(id=1),
            make_stock_adjustment(id=2),
            make_stock_adjustment(id=3),
        ],
    )

    result = await _list_stock_adjustments_impl(
        ListStockAdjustmentsRequest(ids=[1, 3]), context
    )

    assert {a.id for a in result.adjustments} == {1, 3}


@pytest.mark.asyncio
async def test_list_stock_adjustments_filters_by_stock_adjustment_number(
    context_with_typed_cache, no_sync
):
    """`stock_adjustment_number` is an exact-match filter."""
    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [
            make_stock_adjustment(id=1, stock_adjustment_number="SA-100"),
            make_stock_adjustment(id=2, stock_adjustment_number="SA-200"),
        ],
    )

    result = await _list_stock_adjustments_impl(
        ListStockAdjustmentsRequest(stock_adjustment_number="SA-200"), context
    )

    assert len(result.adjustments) == 1
    assert result.adjustments[0].id == 2


@pytest.mark.asyncio
async def test_list_stock_adjustments_filters_by_location_id(
    context_with_typed_cache, no_sync
):
    """`location_id` narrows the result to that location."""
    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [
            make_stock_adjustment(id=1, location_id=7),
            make_stock_adjustment(id=2, location_id=8),
        ],
    )

    result = await _list_stock_adjustments_impl(
        ListStockAdjustmentsRequest(location_id=7), context
    )

    assert len(result.adjustments) == 1
    assert result.adjustments[0].id == 1


@pytest.mark.asyncio
async def test_list_stock_adjustments_excludes_deleted_by_default(
    context_with_typed_cache, no_sync
):
    """Soft-deleted adjustments are filtered out unless include_deleted=True."""
    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [
            make_stock_adjustment(id=1, deleted_at=None),
            make_stock_adjustment(id=2, deleted_at=datetime(2026, 3, 15)),
        ],
    )

    default = await _list_stock_adjustments_impl(ListStockAdjustmentsRequest(), context)
    assert {a.id for a in default.adjustments} == {1}

    with_deleted = await _list_stock_adjustments_impl(
        ListStockAdjustmentsRequest(include_deleted=True), context
    )
    assert {a.id for a in with_deleted.adjustments} == {1, 2}


@pytest.mark.asyncio
async def test_list_stock_adjustments_date_filters(context_with_typed_cache, no_sync):
    """`created_after` / `created_before` apply as indexed range filters."""
    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [
            make_stock_adjustment(id=1, created_at=datetime(2025, 12, 15)),  # before
            make_stock_adjustment(id=2, created_at=datetime(2026, 2, 15)),  # inside
            make_stock_adjustment(id=3, created_at=datetime(2026, 5, 1)),  # after
        ],
    )

    result = await _list_stock_adjustments_impl(
        ListStockAdjustmentsRequest(
            created_after="2026-01-01T00:00:00Z",
            created_before="2026-04-01T00:00:00Z",
        ),
        context,
    )

    assert {a.id for a in result.adjustments} == {2}


@pytest.mark.asyncio
async def test_list_stock_adjustments_variant_id_filter_via_rows(
    context_with_typed_cache, no_sync
):
    """`variant_id` matches when ANY row of the adjustment touches the variant.

    This closes the filter-breadth bug from #342: the pre-cache impl ran
    this filter client-side after a single API page, missing matches on
    later pages. The cache-backed query uses an EXISTS subquery over the
    indexed FK column, so depth doesn't matter.
    """
    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [
            make_stock_adjustment(
                id=1,
                rows=[
                    make_stock_adjustment_row(
                        id=10, stock_adjustment_id=1, variant_id=777
                    ),
                ],
            ),
            make_stock_adjustment(
                id=2,
                rows=[
                    make_stock_adjustment_row(
                        id=11, stock_adjustment_id=2, variant_id=888
                    ),
                ],
            ),
        ],
    )

    result = await _list_stock_adjustments_impl(
        ListStockAdjustmentsRequest(variant_id=777), context
    )

    assert {a.id for a in result.adjustments} == {1}


@pytest.mark.asyncio
async def test_list_stock_adjustments_reason_filter_case_insensitive_substring(
    context_with_typed_cache, no_sync
):
    """`reason` applies a case-insensitive substring (ILIKE) match."""
    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [
            make_stock_adjustment(id=1, reason="Cycle count correction"),
            make_stock_adjustment(id=2, reason="Sample received"),
        ],
    )

    result = await _list_stock_adjustments_impl(
        ListStockAdjustmentsRequest(reason="cycle"), context
    )

    assert {a.id for a in result.adjustments} == {1}


@pytest.mark.asyncio
async def test_list_stock_adjustments_include_rows_false_omits_rows(
    context_with_typed_cache, no_sync
):
    """With `include_rows=False`, summary rows is None but row_count is set."""
    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [
            make_stock_adjustment(
                id=10,
                rows=[
                    make_stock_adjustment_row(
                        id=1, stock_adjustment_id=10, variant_id=100, quantity=5.0
                    ),
                    make_stock_adjustment_row(
                        id=2, stock_adjustment_id=10, variant_id=101, quantity=-2.0
                    ),
                ],
            ),
        ],
    )

    result = await _list_stock_adjustments_impl(
        ListStockAdjustmentsRequest(include_rows=False), context
    )

    assert result.adjustments[0].row_count == 2
    assert result.adjustments[0].rows is None


@pytest.mark.asyncio
async def test_list_stock_adjustments_include_rows_true_populates_rows(
    context_with_typed_cache, no_sync
):
    """With `include_rows=True`, summary rows carries variant/quantity/cost."""
    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [
            make_stock_adjustment(
                id=11,
                rows=[
                    make_stock_adjustment_row(
                        id=1,
                        stock_adjustment_id=11,
                        variant_id=100,
                        quantity=5.0,
                        cost_per_unit=1.23,
                    ),
                    make_stock_adjustment_row(
                        id=2, stock_adjustment_id=11, variant_id=101, quantity=-2.0
                    ),
                ],
            ),
        ],
    )

    result = await _list_stock_adjustments_impl(
        ListStockAdjustmentsRequest(include_rows=True), context
    )

    rows = result.adjustments[0].rows
    assert rows is not None
    assert len(rows) == 2
    by_variant = {r.variant_id: r for r in rows}
    assert by_variant[100].quantity == 5.0
    assert by_variant[100].cost_per_unit == 1.23
    assert by_variant[101].cost_per_unit is None


@pytest.mark.asyncio
async def test_list_stock_adjustments_limit_caps_result_size(
    context_with_typed_cache, no_sync
):
    """Result list is capped at `request.limit` even when more rows exist."""
    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [make_stock_adjustment(id=i) for i in range(20)],
    )

    result = await _list_stock_adjustments_impl(
        ListStockAdjustmentsRequest(limit=5), context
    )

    assert len(result.adjustments) == 5
    assert result.total_count == 5


@pytest.mark.asyncio
async def test_list_stock_adjustments_pagination_meta_populated_on_explicit_page(
    context_with_typed_cache, no_sync
):
    """An explicit `page` populates `pagination` from a SQL COUNT against the same filter set."""
    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [make_stock_adjustment(id=i) for i in range(1, 12)],
    )

    result = await _list_stock_adjustments_impl(
        ListStockAdjustmentsRequest(limit=5, page=2), context
    )

    assert result.pagination is not None
    assert result.pagination.total_records == 11
    assert result.pagination.total_pages == 3
    assert result.pagination.page == 2
    assert result.pagination.first_page is False
    assert result.pagination.last_page is False
    assert len(result.adjustments) == 5


@pytest.mark.asyncio
async def test_list_stock_adjustments_pagination_meta_none_without_page(
    context_with_typed_cache, no_sync
):
    """Without an explicit `page`, `pagination` is `None`."""
    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [make_stock_adjustment(id=1)],
    )

    result = await _list_stock_adjustments_impl(
        ListStockAdjustmentsRequest(limit=50), context
    )

    assert result.pagination is None


# ============================================================================
# update_stock_adjustment Tests
# ============================================================================


@pytest.mark.asyncio
async def test_update_stock_adjustment_preview_returns_is_preview_true():
    """confirm=False returns preview without calling the API."""
    context, _ = create_mock_context()

    request = UpdateStockAdjustmentParams(id=42, reason="Updated reason", confirm=False)

    with patch(f"{_SA_UPDATE}.asyncio_detailed", new=AsyncMock()) as mock_api:
        result = await _update_stock_adjustment_impl(request, context)

    assert result.is_preview is True
    assert result.id == 42
    assert "Updated reason" in result.changes_summary
    mock_api.assert_not_called()


@pytest.mark.asyncio
async def test_update_stock_adjustment_confirm_calls_api():
    """confirm=True elicits confirmation and calls the PATCH endpoint."""
    context, _ = create_mock_context(elicit_confirm=True)

    # The API returns an updated StockAdjustment. `_update_stock_adjustment_impl`
    # imports `unwrap_as` from katana_public_api_client.utils inside the
    # function, so patching the source module intercepts the lookup.
    updated = _make_mock_adjustment(
        id=42, stock_adjustment_number="SA-UPDATED", reason="Updated reason"
    )

    request = UpdateStockAdjustmentParams(
        id=42,
        reason="Updated reason",
        stock_adjustment_number="SA-UPDATED",
        confirm=True,
    )

    with (
        patch(
            f"{_SA_UPDATE}.asyncio_detailed",
            new=AsyncMock(return_value=MagicMock()),
        ) as mock_api,
        patch(_SA_UNWRAP_AS, return_value=updated),
    ):
        result = await _update_stock_adjustment_impl(request, context)

    assert result.is_preview is False
    assert result.id == 42
    assert result.stock_adjustment_number == "SA-UPDATED"
    mock_api.assert_called_once()


@pytest.mark.asyncio
async def test_update_stock_adjustment_decline_short_circuits():
    """When the user declines the elicitation, API is not called."""
    context, _ = create_mock_context(elicit_confirm=False)

    request = UpdateStockAdjustmentParams(id=42, reason="Updated reason", confirm=True)

    with patch(f"{_SA_UPDATE}.asyncio_detailed", new=AsyncMock()) as mock_api:
        result = await _update_stock_adjustment_impl(request, context)

    assert result.is_preview is True
    mock_api.assert_not_called()


@pytest.mark.asyncio
async def test_update_stock_adjustment_rejects_empty_change_set():
    """Missing all updatable fields raises ValueError."""
    context, _ = create_mock_context()

    request = UpdateStockAdjustmentParams(id=42, confirm=False)

    with pytest.raises(ValueError, match="At least one updatable field"):
        await _update_stock_adjustment_impl(request, context)


# ============================================================================
# delete_stock_adjustment Tests
# ============================================================================


@pytest.mark.asyncio
async def test_delete_stock_adjustment_preview_returns_what_would_be_deleted():
    """confirm=False fetches the adjustment and returns it in preview.

    Also asserts the lookup passes page=1 so auto-pagination doesn't chase
    extra pages for a single-record fetch.
    """
    context, _ = create_mock_context()

    adj = _make_mock_adjustment(
        id=99,
        stock_adjustment_number="SA-DELETE",
        location_id=3,
        rows=[_make_mock_adjustment_row(id=1, variant_id=100, quantity=5.0)],
    )

    with (
        patch(
            f"{_SA_GET_ALL}.asyncio_detailed",
            new_callable=AsyncMock,
        ) as mock_get_all,
        patch(_SA_UNWRAP_DATA, return_value=[adj]),
        patch(f"{_SA_DELETE}.asyncio_detailed", new=AsyncMock()) as mock_delete,
    ):
        result = await _delete_stock_adjustment_impl(
            DeleteStockAdjustmentRequest(id=99, confirm=False), context
        )

    assert result.is_preview is True
    assert result.id == 99
    assert result.stock_adjustment_number == "SA-DELETE"
    assert result.location_id == 3
    assert result.row_count == 1
    mock_delete.assert_not_called()
    # The delete-preview lookup should short-circuit auto-pagination.
    assert mock_get_all.call_args.kwargs["page"] == 1


@pytest.mark.asyncio
async def test_delete_stock_adjustment_confirm_calls_api():
    """confirm=True elicits confirmation then calls DELETE."""
    context, _ = create_mock_context(elicit_confirm=True)

    adj = _make_mock_adjustment(
        id=99,
        stock_adjustment_number="SA-DELETE",
        rows=[_make_mock_adjustment_row(id=1, variant_id=100, quantity=5.0)],
    )

    # DELETE returns 204 No Content
    mock_delete_response = MagicMock()
    mock_delete_response.status_code = 204

    with (
        patch(f"{_SA_GET_ALL}.asyncio_detailed", new=AsyncMock()),
        patch(_SA_UNWRAP_DATA, return_value=[adj]),
        patch(
            f"{_SA_DELETE}.asyncio_detailed",
            new=AsyncMock(return_value=mock_delete_response),
        ) as mock_delete,
    ):
        result = await _delete_stock_adjustment_impl(
            DeleteStockAdjustmentRequest(id=99, confirm=True), context
        )

    assert result.is_preview is False
    assert result.id == 99
    assert result.stock_adjustment_number == "SA-DELETE"
    mock_delete.assert_called_once()


@pytest.mark.asyncio
async def test_delete_stock_adjustment_decline_short_circuits():
    """When the user declines the elicitation, DELETE is not called."""
    context, _ = create_mock_context(elicit_confirm=False)

    adj = _make_mock_adjustment(id=99, stock_adjustment_number="SA-DELETE")

    with (
        patch(f"{_SA_GET_ALL}.asyncio_detailed", new=AsyncMock()),
        patch(_SA_UNWRAP_DATA, return_value=[adj]),
        patch(f"{_SA_DELETE}.asyncio_detailed", new=AsyncMock()) as mock_delete,
    ):
        result = await _delete_stock_adjustment_impl(
            DeleteStockAdjustmentRequest(id=99, confirm=True), context
        )

    assert result.is_preview is True
    mock_delete.assert_not_called()


@pytest.mark.asyncio
async def test_delete_stock_adjustment_not_found_raises():
    """A non-existent adjustment id raises ValueError."""
    context, _ = create_mock_context()

    with (
        patch(f"{_SA_GET_ALL}.asyncio_detailed", new=AsyncMock()),
        patch(_SA_UNWRAP_DATA, return_value=[]),
        pytest.raises(ValueError, match="not found"),
    ):
        await _delete_stock_adjustment_impl(
            DeleteStockAdjustmentRequest(id=12345, confirm=False), context
        )


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
    request = CheckInventoryRequest(skus_or_variant_ids=["TEST-SKU-001"])

    try:
        _inv_results = await _check_inventory_impl(request, katana_context)
        result = _inv_results[0]

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
    request = CheckInventoryRequest(skus_or_variant_ids=["NONEXISTENT-SKU-99999"])

    try:
        _inv_results = await _check_inventory_impl(request, katana_context)
        result = _inv_results[0]

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
        _var_results = await _get_variant_details_impl(request, katana_context)
        result = _var_results[0]

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


@pytest.mark.asyncio
async def test_check_inventory_batch_skus():
    """Batch check_inventory with multiple SKUs."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.cache.get_by_sku = AsyncMock(
        side_effect=[
            {"id": 101, "sku": "WIDGET-A", "display_name": "Widget A"},
            {"id": 102, "sku": "WIDGET-B", "display_name": "Widget B"},
        ]
    )

    mock_inv = MagicMock()
    mock_inv.quantity_in_stock = "10.0"
    mock_inv.quantity_committed = "3.0"
    mock_inv.quantity_expected = "5.0"

    with (
        patch(f"{_INVENTORY_API}.asyncio_detailed", new_callable=AsyncMock),
        patch(_UNWRAP_DATA, return_value=[mock_inv]),
    ):
        request = CheckInventoryRequest(skus_or_variant_ids=["WIDGET-A", "WIDGET-B"])
        results = await _check_inventory_impl(request, context)

    assert len(results) == 2
    assert results[0].sku == "WIDGET-A"
    assert results[1].sku == "WIDGET-B"
    assert results[0].in_stock == 10.0
    assert results[0].available_stock == 7.0


# ============================================================================
# format=json / format=markdown (items tools)
# ============================================================================


@pytest.mark.asyncio
async def test_search_items_format_json_returns_json():
    """format='json' returns JSON-parseable content."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.cache.smart_search = AsyncMock(
        return_value=[{"id": 1, "sku": "WIDGET-1", "display_name": "Widget"}]
    )

    result = await search_items(
        query="widget", limit=10, format="json", context=context
    )

    data = json.loads(_content_text(result))
    assert data["total_count"] == 1
    assert data["items"][0]["sku"] == "WIDGET-1"


@pytest.mark.asyncio
async def test_search_items_format_markdown_default():
    """Default markdown format is not JSON."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.cache.smart_search = AsyncMock(
        return_value=[{"id": 1, "sku": "WIDGET-1", "display_name": "Widget"}]
    )

    result = await search_items(query="widget", limit=10, context=context)

    text = _content_text(result)
    assert "WIDGET-1" in text
    # Markdown, not JSON
    assert not text.lstrip().startswith("{")


@pytest.mark.asyncio
async def test_get_variant_details_format_json_returns_json():
    """format='json' returns JSON-parseable content."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.cache.get_by_id = AsyncMock(
        return_value={
            "id": 42,
            "sku": "VAR-42",
            "product_id": 100,
            "type": "product",
        }
    )
    # Mock _get_variant_details_impl via patching the cache lookup chain
    # is complex; patch the impl directly.
    with patch(
        "katana_mcp.tools.foundation.items._get_variant_details_impl",
        new_callable=AsyncMock,
    ) as mock_impl:
        from katana_mcp.tools.foundation.items import VariantDetailsResponse

        mock_impl.return_value = [
            VariantDetailsResponse(
                id=42,
                sku="VAR-42",
                name="Test Variant",
                item_id=100,
                item_type="product",
                sales_price=10.0,
                purchase_price=5.0,
            )
        ]

        result = await get_variant_details(
            variant_id=42, format="json", context=context
        )

    data = json.loads(_content_text(result))
    assert data["variants"][0]["id"] == 42
    assert data["variants"][0]["sku"] == "VAR-42"


# ============================================================================
# format=json (inventory tools)
# ============================================================================


@pytest.mark.asyncio
async def test_check_inventory_format_json_returns_json():
    """format='json' returns JSON-parseable content for batch check."""
    from katana_mcp.tools.foundation.inventory import StockInfo

    with patch(
        "katana_mcp.tools.foundation.inventory._check_inventory_impl",
        new_callable=AsyncMock,
    ) as mock_impl:
        mock_impl.return_value = [
            StockInfo(
                variant_id=1,
                sku="A",
                product_name="A",
                available_stock=1,
                committed=0,
                expected=0,
                in_stock=1,
            ),
            StockInfo(
                variant_id=2,
                sku="B",
                product_name="B",
                available_stock=2,
                committed=0,
                expected=0,
                in_stock=2,
            ),
        ]
        context, _ = create_mock_context()
        result = await check_inventory(
            skus_or_variant_ids=["A", "B"], format="json", context=context
        )

    data = json.loads(_content_text(result))
    assert len(data["items"]) == 2
    assert data["items"][0]["sku"] == "A"


@pytest.mark.asyncio
async def test_list_low_stock_items_format_json_returns_json():
    """format='json' returns JSON-parseable content."""
    from katana_mcp.tools.foundation.inventory import (
        LowStockItem,
        LowStockResponse,
    )

    with patch(
        "katana_mcp.tools.foundation.inventory._list_low_stock_items_impl",
        new_callable=AsyncMock,
    ) as mock_impl:
        mock_impl.return_value = LowStockResponse(
            items=[
                LowStockItem(
                    sku="LOW-1",
                    product_name="Low Item",
                    current_stock=2,
                    threshold=10,
                )
            ],
            total_count=1,
        )
        context, _ = create_mock_context()
        result = await list_low_stock_items(format="json", context=context)

    data = json.loads(_content_text(result))
    assert data["total_count"] == 1
    assert data["items"][0]["sku"] == "LOW-1"


@pytest.mark.asyncio
async def test_get_inventory_movements_format_json_returns_json():
    """format='json' returns JSON-parseable content."""
    from katana_mcp.tools.foundation.inventory import InventoryMovementsResponse

    with patch(
        "katana_mcp.tools.foundation.inventory._get_inventory_movements_impl",
        new_callable=AsyncMock,
    ) as mock_impl:
        mock_impl.return_value = InventoryMovementsResponse(
            sku="MOVE-1",
            product_name="Move",
            movements=[],
            total_count=0,
        )
        context, _ = create_mock_context()
        result = await get_inventory_movements(
            sku="MOVE-1", format="json", context=context
        )

    data = json.loads(_content_text(result))
    assert data["sku"] == "MOVE-1"
    assert data["total_count"] == 0


@pytest.mark.asyncio
async def test_list_stock_adjustments_format_json_returns_json():
    """format='json' returns JSON-parseable content."""
    from katana_mcp.tools.foundation.inventory import ListStockAdjustmentsResponse

    with patch(
        "katana_mcp.tools.foundation.inventory._list_stock_adjustments_impl",
        new_callable=AsyncMock,
    ) as mock_impl:
        mock_impl.return_value = ListStockAdjustmentsResponse(
            adjustments=[],
            total_count=0,
            pagination=None,
        )
        context, _ = create_mock_context()
        result = await list_stock_adjustments(format="json", context=context)

    data = json.loads(_content_text(result))
    assert data["total_count"] == 0
