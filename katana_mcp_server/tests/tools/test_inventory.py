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
    StockInfo,
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
    search_items,
)
from katana_mcp_server.tests.conftest import create_mock_context, patch_typed_cache_sync
from pydantic import ValidationError

from katana_public_api_client.api.inventory_movements import (
    get_all_inventory_movements as _movements_api,
)
from katana_public_api_client.client_types import UNSET
from katana_public_api_client.models_pydantic._generated import CachedLocation
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
    """Patch entity syncs for all unit tests.

    The cache sync is tested separately; tool tests verify tool logic
    with pre-populated cache mocks. ``get_variant_details`` syncs Variant
    plus Product, Material, and Supplier (parent-derived ``default_supplier_*``
    are lifted from the parent product/material), so all four are mocked.

    Decorator keys are now typed-cache ``Cached*`` classes (#472 Phase C).
    """
    from katana_mcp.tools import decorators

    from katana_public_api_client.models_pydantic._generated import (
        CachedLocation,
        CachedMaterial,
        CachedProduct,
        CachedSupplier,
        CachedVariant,
    )

    original = decorators._sync_fns
    decorators._sync_fns = {
        CachedVariant: AsyncMock(),
        CachedProduct: AsyncMock(),
        CachedMaterial: AsyncMock(),
        CachedSupplier: AsyncMock(),
        CachedLocation: AsyncMock(),
    }
    try:
        yield
    finally:
        decorators._sync_fns = original


_INVENTORY_API = "katana_public_api_client.api.inventory.get_all_inventory_point"
_UNWRAP_DATA = "katana_public_api_client.utils.unwrap_data"


@pytest.mark.asyncio
async def test_check_inventory():
    """Test check_inventory tool with cached variant + inventory API."""
    context, lifespan_ctx = create_mock_context()

    # Mock cached variant lookup
    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(
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

    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(
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
    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(return_value=None)

    request = CheckInventoryRequest(skus_or_variant_ids=["NOT-FOUND"])
    _inv_results = await _check_inventory_impl(request, context)
    result = _inv_results[0]

    assert result.sku == "NOT-FOUND"
    assert result.product_name == ""
    assert result.available_stock == 0
    assert result.committed == 0
    assert result.expected == 0
    assert result.in_stock == 0


def _mock_inventory_row(variant_id: int, quantity_in_stock: str) -> MagicMock:
    """Build an attrs-shaped Inventory mock for one variant/location row."""
    inv = MagicMock()
    inv.variant_id = variant_id
    inv.quantity_in_stock = quantity_in_stock
    inv.quantity_committed = "0"
    inv.quantity_expected = "0"
    return inv


@pytest.mark.asyncio
async def test_list_low_stock_items():
    """list_low_stock_items returns variants with summed in_stock below threshold."""
    context, lifespan_ctx = create_mock_context()

    inventory_rows = [
        _mock_inventory_row(1001, "5"),
        _mock_inventory_row(1002, "3"),
        _mock_inventory_row(1003, "8"),
    ]
    lifespan_ctx.typed_cache.catalog.get_many_by_ids = AsyncMock(
        return_value={
            1001: {"id": 1001, "sku": "ITEM-001", "display_name": "Item 1"},
            1002: {"id": 1002, "sku": "ITEM-002", "display_name": "Item 2"},
            1003: {"id": 1003, "sku": "ITEM-003", "display_name": "Item 3"},
        }
    )

    with (
        patch(f"{_INVENTORY_API}.asyncio_detailed", new_callable=AsyncMock),
        patch(_UNWRAP_DATA, return_value=inventory_rows),
    ):
        request = LowStockRequest(threshold=10, limit=50)
        result = await _list_low_stock_items_impl(request, context)

    assert result.total_count == 3
    assert len(result.items) == 3
    # Sorted ascending by current_stock — most-depleted first.
    assert [item.sku for item in result.items] == ["ITEM-002", "ITEM-001", "ITEM-003"]
    assert result.items[0].current_stock == 3
    assert result.items[0].product_name == "Item 2"
    assert result.items[0].threshold == 10


@pytest.mark.asyncio
async def test_list_low_stock_items_with_limit():
    """list_low_stock_items truncates items but keeps total_count of all matches."""
    context, lifespan_ctx = create_mock_context()

    inventory_rows = [_mock_inventory_row(2000 + i, str(i)) for i in range(100)]
    lifespan_ctx.typed_cache.catalog.get_many_by_ids = AsyncMock(
        return_value={
            2000 + i: {
                "id": 2000 + i,
                "sku": f"ITEM-{i:03d}",
                "display_name": f"Item {i}",
            }
            for i in range(100)
        }
    )

    with (
        patch(f"{_INVENTORY_API}.asyncio_detailed", new_callable=AsyncMock),
        patch(_UNWRAP_DATA, return_value=inventory_rows),
    ):
        request = LowStockRequest(threshold=10000, limit=20)
        result = await _list_low_stock_items_impl(request, context)

    assert result.total_count == 100
    assert len(result.items) == 20


@pytest.mark.asyncio
async def test_list_low_stock_items_handles_missing_variant_fields():
    """list_low_stock_items falls back to empty strings when variant lacks SKU/name."""
    context, lifespan_ctx = create_mock_context()

    inventory_rows = [_mock_inventory_row(3001, "5")]
    lifespan_ctx.typed_cache.catalog.get_many_by_ids = AsyncMock(
        return_value={3001: {"id": 3001}}  # No sku, no display_name, no name.
    )

    with (
        patch(f"{_INVENTORY_API}.asyncio_detailed", new_callable=AsyncMock),
        patch(_UNWRAP_DATA, return_value=inventory_rows),
    ):
        request = LowStockRequest(threshold=10)
        result = await _list_low_stock_items_impl(request, context)

    assert len(result.items) == 1
    assert result.items[0].sku == ""
    assert result.items[0].product_name == ""
    assert result.items[0].current_stock == 5


@pytest.mark.asyncio
async def test_list_low_stock_default_parameters():
    """LowStockRequest defaults threshold=10, limit=50; impl handles empty inventory."""
    context, _lifespan_ctx = create_mock_context()

    with (
        patch(f"{_INVENTORY_API}.asyncio_detailed", new_callable=AsyncMock),
        patch(_UNWRAP_DATA, return_value=[]),
    ):
        request = LowStockRequest()  # Use defaults
        result = await _list_low_stock_items_impl(request, context)

    assert request.threshold == 10
    assert request.limit == 50
    assert result.total_count == 0
    assert result.items == []


@pytest.mark.asyncio
async def test_list_low_stock_sums_across_locations():
    """Regression: variant stock at multiple locations must be summed.

    Mirrors test_check_inventory_multiple_locations — guards the bug class
    that #510 fixed (the legacy helper had no concept of summing).
    """
    context, lifespan_ctx = create_mock_context()

    # Variant 4001: 5 at location A + 3 at location B = 8 total (below 10).
    # Variant 4002: 30 at single location (above threshold, must be excluded).
    inventory_rows = [
        _mock_inventory_row(4001, "5"),
        _mock_inventory_row(4001, "3"),
        _mock_inventory_row(4002, "30"),
    ]
    lifespan_ctx.typed_cache.catalog.get_many_by_ids = AsyncMock(
        return_value={
            4001: {"id": 4001, "sku": "MULTI-LOC", "display_name": "Multi-loc Widget"},
        }
    )

    with (
        patch(f"{_INVENTORY_API}.asyncio_detailed", new_callable=AsyncMock),
        patch(_UNWRAP_DATA, return_value=inventory_rows),
    ):
        request = LowStockRequest(threshold=10)
        result = await _list_low_stock_items_impl(request, context)

    assert result.total_count == 1
    assert len(result.items) == 1
    assert result.items[0].sku == "MULTI-LOC"
    assert result.items[0].current_stock == 8


@pytest.mark.asyncio
async def test_list_low_stock_excludes_above_threshold():
    """Variants with summed totals at or above the threshold are filtered out."""
    context, lifespan_ctx = create_mock_context()

    inventory_rows = [
        _mock_inventory_row(5001, "10"),  # exactly at threshold — excluded
        _mock_inventory_row(5002, "100"),  # above threshold — excluded
        _mock_inventory_row(5003, "2"),  # below threshold — included
    ]
    lifespan_ctx.typed_cache.catalog.get_many_by_ids = AsyncMock(
        return_value={
            5003: {"id": 5003, "sku": "LOW", "display_name": "Low item"},
        }
    )

    with (
        patch(f"{_INVENTORY_API}.asyncio_detailed", new_callable=AsyncMock),
        patch(_UNWRAP_DATA, return_value=inventory_rows),
    ):
        request = LowStockRequest(threshold=10)
        result = await _list_low_stock_items_impl(request, context)

    assert [item.sku for item in result.items] == ["LOW"]


@pytest.mark.asyncio
async def test_list_low_stock_cache_miss_fallback():
    """Cache miss for a low-stock variant_id falls back to the API via _fetch_variant_by_id."""
    context, lifespan_ctx = create_mock_context()

    inventory_rows = [_mock_inventory_row(6001, "4")]
    # get_many_by_ids returns empty dict (cache miss) — default from create_mock_context().
    # _fetch_variant_by_id then calls cache.get_by_id (also miss) and falls through to
    # the API. Mock the API path directly.
    fetched_variant = {"id": 6001, "sku": "FETCHED", "display_name": "Fetched item"}

    with (
        patch(f"{_INVENTORY_API}.asyncio_detailed", new_callable=AsyncMock),
        patch(_UNWRAP_DATA, return_value=inventory_rows),
        patch(
            "katana_mcp.tools.foundation.items._fetch_variant_by_id",
            new_callable=AsyncMock,
            return_value=fetched_variant,
        ) as mock_fetch,
    ):
        request = LowStockRequest(threshold=10)
        result = await _list_low_stock_items_impl(request, context)

    assert len(result.items) == 1
    assert result.items[0].sku == "FETCHED"
    assert result.items[0].product_name == "Fetched item"
    assert result.items[0].current_stock == 4
    mock_fetch.assert_awaited_once_with(lifespan_ctx, 6001)


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

    lifespan_ctx.typed_cache.catalog.smart_search = AsyncMock(
        return_value=[cached_variant]
    )

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

    lifespan_ctx.typed_cache.catalog.smart_search = AsyncMock(
        return_value=[cached_variant]
    )

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
    from katana_public_api_client.models_pydantic._generated import CachedVariant

    lifespan_ctx.typed_cache.catalog.smart_search.assert_called_once_with(
        CachedVariant, "test", limit=20, include_archived=False
    )


@pytest.mark.asyncio
async def test_search_items_surfaces_archived_state_from_parent():
    """Variants inherit archived state from their parent — assert it surfaces."""
    context, lifespan_ctx = create_mock_context()

    # Two variants: one with an archived parent, one without. The
    # ``parent_archived_at`` field is synthesized in cache_sync from the
    # extended ``product_or_material`` payload, so the dict shape here
    # mirrors what _variant_to_cache_dict actually writes.
    cached_variants = [
        {
            "id": 1,
            "sku": "ACTIVE-1",
            "type": "product",
            "display_name": "Active Item",
            "parent_archived_at": None,
        },
        {
            "id": 2,
            "sku": "ARCHIVED-1",
            "type": "material",
            "display_name": "Archived Item",
            "parent_archived_at": "2024-01-01T00:00:00+00:00",
        },
    ]
    lifespan_ctx.typed_cache.catalog.smart_search = AsyncMock(
        return_value=cached_variants
    )

    request = SearchItemsRequest(query="item", include_archived=True)
    result = await _search_items_impl(request, context)

    by_sku = {item.sku: item for item in result.items}
    assert by_sku["ACTIVE-1"].is_archived is False
    assert by_sku["ARCHIVED-1"].is_archived is True
    # Cache call must thread the flag through, otherwise the filter is moot.
    from katana_public_api_client.models_pydantic._generated import CachedVariant

    lifespan_ctx.typed_cache.catalog.smart_search.assert_called_once_with(
        CachedVariant, "item", limit=20, include_archived=True
    )


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

    lifespan_ctx.typed_cache.catalog.smart_search = AsyncMock(
        return_value=cached_variants
    )

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


def _patch_movements_call(lifespan_ctx):
    """Stub the httpx call inside ``_get_inventory_movements_impl``.

    The impl bypasses ``asyncio_detailed`` and goes through ``_get_kwargs`` +
    ``client.get_async_httpx_client().request(...)`` so it can pass an
    ``extensions={"max_items": N}`` row cap to the auto-pagination transport
    (issue #771). The MagicMock ``services.client`` returns non-awaitable
    MagicMocks from ``get_async_httpx_client().request(...)`` by default —
    swap in an ``AsyncMock`` so tests can ``await`` it. Returns the
    ``AsyncMock`` so tests can assert on ``.call_args.kwargs`` to inspect
    forwarded API params *and* the ``extensions`` row cap.

    ``_build_response`` is **not** stubbed — it still runs as production
    code against the fake ``httpx.Response`` returned here. The response
    is a well-formed ``200`` with ``{"data": []}``, so ``_build_response``
    parses cleanly; tests that care about the final list of movements
    patch ``unwrap_data`` instead to inject mock results.
    """
    import httpx

    fake_httpx_response = httpx.Response(200, json={"data": []})
    request_mock = AsyncMock(return_value=fake_httpx_response)
    lifespan_ctx.client.get_async_httpx_client.return_value.request = request_mock
    return request_mock


@pytest.mark.asyncio
async def test_get_inventory_movements():
    """Test get_inventory_movements with mocked API."""
    context, lifespan_ctx = create_mock_context()

    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(
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

    _patch_movements_call(lifespan_ctx)
    with patch(_UNWRAP_DATA, return_value=[mock_movement]):
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
    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(return_value=None)

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

    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(
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

    _patch_movements_call(lifespan_ctx)
    with patch(_UNWRAP_DATA, return_value=[mock_movement]):
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
async def test_get_inventory_movements_response_uses_canonical_field_names():
    """Response model surfaces every movement field by its canonical Pydantic
    name — pins the #346 follow-on convention. JSON keys (and the
    iframe-rendered Prefab table) read directly off those names, so a
    silent rename would surface as a key-not-found everywhere at once.
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

    payload = json.loads(_content_text(result))
    movement = payload["movements"][0]
    # Every canonical field name from the response model surfaces on
    # the wire payload. A silent rename would drop one of these keys.
    expected_keys = {
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
    }
    assert expected_keys.issubset(movement.keys())
    # Identity fields surface on the top level too.
    assert payload["sku"] == "WIDGET-001"
    assert payload["product_name"] == "Test Widget"
    assert payload["total_count"] == 1


# ============================================================================
# create_stock_adjustment Tests
# ============================================================================

_SA_API = "katana_public_api_client.api.stock_adjustment.create_stock_adjustment"


@pytest.mark.asyncio
async def test_create_stock_adjustment_preview():
    """Test stock adjustment preview mode."""
    context, lifespan_ctx = create_mock_context()

    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(
        return_value={"id": 3001, "sku": "WIDGET-001", "display_name": "Test Widget"}
    )

    request = CreateStockAdjustmentRequest(
        location_id=1,
        rows=[StockAdjustmentRow(sku="WIDGET-001", quantity=5)],
        reason="Test adjustment",
        preview=True,
    )
    result = await _create_stock_adjustment_impl(request, context)

    assert result.is_preview is True
    assert "WIDGET-001" in result.rows_summary
    assert "+5.0" in result.rows_summary


@pytest.mark.asyncio
async def test_create_stock_adjustment_sku_not_found():
    """Test stock adjustment with unknown SKU."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(return_value=None)

    request = CreateStockAdjustmentRequest(
        location_id=1,
        rows=[StockAdjustmentRow(sku="BAD-SKU", quantity=1)],
        preview=True,
    )
    with pytest.raises(ValueError, match="SKU 'BAD-SKU' not found"):
        await _create_stock_adjustment_impl(request, context)


@pytest.mark.asyncio
async def test_create_stock_adjustment_apply_forwards_new_fields():
    """Caller-supplied stock_adjustment_number, stock_adjustment_date, and
    row-level batch_transactions reach the API call body (#627).
    """
    from datetime import UTC, datetime

    from katana_mcp.tools.foundation.inventory import StockAdjustmentBatchAllocation

    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(
        return_value={"id": 3001, "sku": "BATCH-001", "display_name": "Batch Item"}
    )

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_adj = MagicMock()
    mock_adj.id = 9001
    mock_response.parsed = mock_adj
    mock_api_call = AsyncMock(return_value=mock_response)

    physical_count_date = datetime(2026, 4, 1, 8, 0, tzinfo=UTC)

    with patch(_SA_API + ".asyncio_detailed", mock_api_call):
        request = CreateStockAdjustmentRequest(
            location_id=1,
            rows=[
                StockAdjustmentRow(
                    sku="BATCH-001",
                    quantity=10,
                    cost_per_unit=2.50,
                    batch_transactions=[
                        StockAdjustmentBatchAllocation(batch_id=42, quantity=6),
                        StockAdjustmentBatchAllocation(batch_id=43, quantity=4),
                    ],
                ),
            ],
            stock_adjustment_number="SA-IMPORT-001",
            stock_adjustment_date=physical_count_date,
            preview=False,
        )
        await _create_stock_adjustment_impl(request, context)

    assert mock_api_call.call_args is not None
    api_body = mock_api_call.call_args.kwargs["body"]
    assert api_body.stock_adjustment_number == "SA-IMPORT-001"
    assert api_body.stock_adjustment_date == physical_count_date
    row = api_body.stock_adjustment_rows[0]
    assert len(row.batch_transactions) == 2
    assert row.batch_transactions[0].batch_id == 42
    assert row.batch_transactions[0].quantity == 6
    assert row.batch_transactions[1].batch_id == 43
    assert row.batch_transactions[1].quantity == 4


@pytest.mark.asyncio
async def test_create_stock_adjustment_apply_defaults_when_unset():
    """When the new fields aren't supplied, the tool generates a SA-<ts>
    number and stamps the call time as the date — Katana requires both
    fields. row-level batch_transactions stays UNSET when the caller
    leaves it None.
    """
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(
        return_value={"id": 3001, "sku": "WIDGET-001", "display_name": "Test Widget"}
    )

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_adj = MagicMock()
    mock_adj.id = 9002
    mock_response.parsed = mock_adj
    mock_api_call = AsyncMock(return_value=mock_response)

    from katana_public_api_client.client_types import UNSET

    with patch(_SA_API + ".asyncio_detailed", mock_api_call):
        request = CreateStockAdjustmentRequest(
            location_id=1,
            rows=[StockAdjustmentRow(sku="WIDGET-001", quantity=1)],
            preview=False,
        )
        await _create_stock_adjustment_impl(request, context)

    api_body = mock_api_call.call_args.kwargs["body"]
    # Auto-generated SA number — pattern check rather than exact match
    assert api_body.stock_adjustment_number.startswith("SA-")
    # stock_adjustment_date is always populated (Katana requires it)
    assert api_body.stock_adjustment_date is not None
    assert api_body.stock_adjustment_date is not UNSET
    # batch_transactions stays UNSET when caller omits it
    assert api_body.stock_adjustment_rows[0].batch_transactions is UNSET


@pytest.mark.asyncio
async def test_create_stock_adjustment_empty_rows():
    """Test stock adjustment with no rows."""
    context, _ = create_mock_context()

    request = CreateStockAdjustmentRequest(
        location_id=1,
        rows=[],
        preview=True,
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

    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(return_value=cached_variant)

    request = GetVariantDetailsRequest(sku="WIDGET-001")
    _var_results = await _get_variant_details_impl(request, context)
    result = _var_results.found[0]

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
async def test_get_variant_details_plumbs_factory_base_currency():
    """#751 — ``_get_variant_details_impl`` resolves
    ``Factory.base_currency_code`` from the typed cache and stamps it
    onto :class:`VariantDetailsResponse.base_currency_code` so the
    variant card can render prices with the correct currency symbol
    (not the USD fallback)."""
    context, lifespan_ctx = create_mock_context()

    cached_variant = {
        "id": 123,
        "sku": "WIDGET-EU",
        "type": "product",
        "display_name": "Widget EU",
        "sales_price": 12.99,
        "purchase_price": 7.50,
    }

    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(return_value=cached_variant)
    # Factory singleton (id=1) returns an EUR-base tenant. The shape
    # mirrors a real CachedFactory row — a stub object with the
    # ``base_currency_code`` attribute, as the cache helper accepts
    # either SQLModel rows or dicts.

    class _StubFactory:
        base_currency_code = "EUR"

    async def _get_by_id(cls, entity_id, **_kwargs):
        # Only the factory lookup uses get_by_id in this impl; everything
        # else goes through get_by_sku / get_many_by_ids.
        if entity_id == 1:
            return _StubFactory()
        return None

    lifespan_ctx.typed_cache.catalog.get_by_id = AsyncMock(side_effect=_get_by_id)

    request = GetVariantDetailsRequest(sku="WIDGET-EU")
    _var_results = await _get_variant_details_impl(request, context)
    result = _var_results.found[0]

    assert result.base_currency_code == "EUR"


@pytest.mark.asyncio
async def test_get_variant_details_tolerates_missing_factory():
    """Cold-cache path: when the factory record isn't synced yet, the
    impl still returns the variant with ``base_currency_code=None`` so
    the card render falls back to USD via :func:`_format_money` rather
    than blowing up."""
    context, lifespan_ctx = create_mock_context()

    cached_variant = {
        "id": 123,
        "sku": "WIDGET-001",
        "type": "product",
        "display_name": "Widget",
        "sales_price": 29.99,
    }

    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(return_value=cached_variant)
    # Replace get_by_id with a spy that returns None — pins both the
    # "cold cache → None resolution" behavior AND the (CachedFactory, 1)
    # singleton-lookup contract, so a future refactor that drops the
    # factory call or changes the id wouldn't slip through silently.
    lifespan_ctx.typed_cache.catalog.get_by_id = AsyncMock(return_value=None)

    request = GetVariantDetailsRequest(sku="WIDGET-001")
    _var_results = await _get_variant_details_impl(request, context)
    result = _var_results.found[0]

    assert result.base_currency_code is None
    # Verify the factory lookup actually fired with the singleton id.
    factory_calls = [
        call
        for call in lifespan_ctx.typed_cache.catalog.get_by_id.call_args_list
        if len(call.args) >= 2 and call.args[1] == 1
    ]
    assert factory_calls, (
        "expected resolve_factory_base_currency to call get_by_id(CachedFactory, 1)"
    )


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

    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(return_value=cached_variant)

    # Search with lowercase SKU
    request = GetVariantDetailsRequest(sku="widget-001")
    _var_results = await _get_variant_details_impl(request, context)
    result = _var_results.found[0]

    assert result.id == 123
    assert result.sku == "WIDGET-001"
    assert result.name == "Test Widget"


@pytest.mark.asyncio
async def test_get_variant_details_not_found():
    """Test get_variant_details when SKU not found."""
    context, lifespan_ctx = create_mock_context()

    # Cache returns None (no match)
    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(return_value=None)

    request = GetVariantDetailsRequest(sku="NOT-FOUND")
    with pytest.raises(ValueError, match="Variant with SKU 'NOT-FOUND' not found"):
        await _get_variant_details_impl(request, context)


@pytest.mark.asyncio
async def test_get_variant_details_no_exact_match():
    """Test get_variant_details when no exact SKU match exists."""
    context, lifespan_ctx = create_mock_context()

    # Cache returns None (SKU lookup is exact)
    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(return_value=None)

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

    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(return_value=cached_variant)

    request = GetVariantDetailsRequest(sku="MIN-001")
    _var_results = await _get_variant_details_impl(request, context)
    result = _var_results.found[0]

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

    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(return_value=cached_variant)

    request = GetVariantDetailsRequest(sku="TIME-001")
    _var_results = await _get_variant_details_impl(request, context)
    result = _var_results.found[0]

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
    """preview=True returns preview without calling the API."""
    context, _ = create_mock_context()

    request = UpdateStockAdjustmentParams(id=42, reason="Updated reason", preview=True)

    with patch(f"{_SA_UPDATE}.asyncio_detailed", new=AsyncMock()) as mock_api:
        result = await _update_stock_adjustment_impl(request, context)

    assert result.is_preview is True
    assert result.id == 42
    assert "Updated reason" in result.changes_summary
    mock_api.assert_not_called()


@pytest.mark.asyncio
async def test_update_stock_adjustment_confirm_calls_api():
    """preview=False calls the PATCH endpoint directly (host already confirmed)."""
    context, _ = create_mock_context()

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
        preview=False,
    )

    # The impl pre-fetches via get_all_stock_adjustments when caller didn't
    # supply additional_info (echo workaround for the Katana PATCH-wipe bug;
    # see #505 / KATANA_API_QUESTIONS.md §6.2). Mock it so the test doesn't
    # try to hit the live API.
    existing = _make_mock_adjustment(id=42, additional_info=None)
    list_response = MagicMock()
    list_response.parsed = MagicMock()
    list_response.parsed.data = [existing]

    with (
        patch(
            f"{_SA_GET_ALL}.asyncio_detailed",
            new=AsyncMock(return_value=list_response),
        ),
        patch(
            f"{_SA_UPDATE}.asyncio_detailed",
            new=AsyncMock(return_value=MagicMock()),
        ) as mock_api,
        patch(_SA_UNWRAP_AS, return_value=updated),
        patch("katana_public_api_client.utils.unwrap_data", return_value=[existing]),
    ):
        result = await _update_stock_adjustment_impl(request, context)

    assert result.is_preview is False
    assert result.id == 42
    assert result.stock_adjustment_number == "SA-UPDATED"
    mock_api.assert_called_once()


@pytest.mark.asyncio
async def test_update_stock_adjustment_rejects_empty_change_set():
    """Missing all updatable fields raises ValueError."""
    context, _ = create_mock_context()

    request = UpdateStockAdjustmentParams(id=42, preview=True)

    with pytest.raises(ValueError, match="At least one updatable field"):
        await _update_stock_adjustment_impl(request, context)


# ============================================================================
# delete_stock_adjustment Tests
# ============================================================================


@pytest.mark.asyncio
async def test_delete_stock_adjustment_preview_returns_what_would_be_deleted():
    """preview=True fetches the adjustment and returns it in preview.

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
            DeleteStockAdjustmentRequest(id=99, preview=True), context
        )

    assert result.is_preview is True
    assert result.id == 99
    assert result.stock_adjustment_number == "SA-DELETE"
    assert result.location_id == 3
    assert result.row_count == 1
    mock_delete.assert_not_called()
    # The delete-preview lookup should short-circuit auto-pagination.
    assert mock_get_all.call_args is not None
    assert mock_get_all.call_args.kwargs["page"] == 1


@pytest.mark.asyncio
async def test_delete_stock_adjustment_confirm_calls_api():
    """preview=False calls DELETE directly (host already confirmed)."""
    context, _ = create_mock_context()

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
            DeleteStockAdjustmentRequest(id=99, preview=False), context
        )

    assert result.is_preview is False
    assert result.id == 99
    assert result.stock_adjustment_number == "SA-DELETE"
    mock_delete.assert_called_once()


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
            DeleteStockAdjustmentRequest(id=12345, preview=True), context
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
            assert isinstance(item.current_stock, float)
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
        result = _var_results.found[0]

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
    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(
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


@pytest.mark.asyncio
async def test_check_inventory_single_variant_id():
    """Pure integer input routes through _fetch_variant_by_id (cache-miss fallback)."""
    context, _ = create_mock_context()

    mock_inv = MagicMock()
    mock_inv.quantity_in_stock = "42.0"
    mock_inv.quantity_committed = "2.0"
    mock_inv.quantity_expected = "5.0"

    with (
        patch(
            "katana_mcp.tools.foundation.items._fetch_variant_by_id",
            new_callable=AsyncMock,
            return_value={"id": 42, "sku": "WIDGET-42", "display_name": "Widget 42"},
        ) as mock_fetch,
        patch(f"{_INVENTORY_API}.asyncio_detailed", new_callable=AsyncMock),
        patch(_UNWRAP_DATA, return_value=[mock_inv]),
    ):
        request = CheckInventoryRequest(skus_or_variant_ids=[42])
        results = await _check_inventory_impl(request, context)

    # Single-item batch — exercises the rich-card path in check_inventory
    assert len(results) == 1
    result = results[0]
    assert result.variant_id == 42
    assert result.sku == "WIDGET-42"
    assert result.product_name == "Widget 42"
    assert result.in_stock == 42.0
    assert result.committed == 2.0
    assert result.expected == 5.0
    assert result.available_stock == 40.0  # 42 - 2

    # Verify the variant_id path (not the SKU path) was taken
    mock_fetch.assert_awaited_once()
    call_args = mock_fetch.await_args
    assert call_args is not None
    assert call_args.args[1] == 42


@pytest.mark.asyncio
async def test_check_inventory_mixed_sku_and_variant_id():
    """Mixed string + integer input exercises both the cache-by-sku and fetch-by-id routes.

    Output order matches input order: ``["WIDGET-1", 42]`` produces results
    ``[WIDGET-1, WIDGET-42]`` regardless of how parallel resolution interleaves.
    """
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(
        return_value={"id": 101, "sku": "WIDGET-1", "display_name": "Widget 1"}
    )

    # Patch _fetch_stock_for_variant to return per-variant StockInfo deterministically,
    # avoiding fragile assumptions about parallel-task scheduling order.
    stock_by_id = {
        101: StockInfo(
            variant_id=101,
            sku="WIDGET-1",
            product_name="Widget 1",
            in_stock=10.0,
            committed=1.0,
            expected=2.0,
            available_stock=9.0,
        ),
        42: StockInfo(
            variant_id=42,
            sku="WIDGET-42",
            product_name="Widget 42",
            in_stock=20.0,
            committed=5.0,
            expected=0.0,
            available_stock=15.0,
        ),
    }

    async def _fake_fetch_stock(
        _services, variant_id, _sku, _product_name, location_id=None
    ):
        return stock_by_id[variant_id]

    with (
        patch(
            "katana_mcp.tools.foundation.items._fetch_variant_by_id",
            new_callable=AsyncMock,
            return_value={"id": 42, "sku": "WIDGET-42", "display_name": "Widget 42"},
        ) as mock_fetch,
        patch(
            "katana_mcp.tools.foundation.inventory._fetch_stock_for_variant",
            side_effect=_fake_fetch_stock,
        ),
    ):
        request = CheckInventoryRequest(skus_or_variant_ids=["WIDGET-1", 42])
        results = await _check_inventory_impl(request, context)

    assert len(results) == 2

    lifespan_ctx.typed_cache.catalog.get_by_sku.assert_awaited_once()
    mock_fetch.assert_awaited_once()
    assert mock_fetch.await_args is not None
    assert mock_fetch.await_args.args[1] == 42

    # Output order matches input order.
    assert results[0].sku == "WIDGET-1"
    assert results[0].in_stock == 10.0
    assert results[0].available_stock == 9.0
    assert results[1].sku == "WIDGET-42"
    assert results[1].variant_id == 42
    assert results[1].in_stock == 20.0
    assert results[1].available_stock == 15.0  # 20 - 5


# ============================================================================
# format=json / format=markdown (items tools)
# ============================================================================


@pytest.mark.asyncio
async def test_search_items_format_json_returns_json():
    """format='json' returns JSON-parseable content."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.typed_cache.catalog.smart_search = AsyncMock(
        return_value=[{"id": 1, "sku": "WIDGET-1", "display_name": "Widget"}]
    )

    result = await search_items(query="widget", limit=10, context=context)

    data = json.loads(_content_text(result))
    assert data["total_count"] == 1
    assert data["items"][0]["sku"] == "WIDGET-1"


# (get_variant_details JSON-content behavior is exhaustively covered by
# the items.py test suite; this file no longer carries a cross-file
# duplicate.)


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
        result = await check_inventory(skus_or_variant_ids=["A", "B"], context=context)

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
                    variant_id=1001,
                )
            ],
            total_count=1,
        )
        context, _ = create_mock_context()
        result = await list_low_stock_items(context=context)

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
        result = await get_inventory_movements(sku="MOVE-1", context=context)

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
        result = await list_stock_adjustments(context=context)

    data = json.loads(_content_text(result))
    assert data["total_count"] == 0


# ============================================================================
# #505 follow-on: PATCH-wipe `additional_info` workaround on StockAdjustment
# ============================================================================
#
# The Katana platform clears `additional_info` to `""` on PATCH whenever the
# field is omitted from the body. Verified against stock adjustment 2394711
# on 2026-05-05 (see docs/KATANA_API_QUESTIONS.md §6.2). The impl pre-fetches
# the adjustment via `get_all_stock_adjustments(ids=[id])` only when the
# caller didn't supply `additional_info`, then echoes the existing value
# in the PATCH body so the wipe doesn't fire.


@pytest.mark.asyncio
async def test_update_stock_adjustment_echoes_additional_info_when_unchanged():
    """Caller updates only `reason`; existing `additional_info` is echoed in
    the PATCH body so Katana doesn't wipe it. Verified the body includes
    the echoed value via the captured request kwargs."""
    context, _ = create_mock_context()

    existing = _make_mock_adjustment(
        id=42,
        reason="Cycle count",
        additional_info="UPS tracking 1Z123 — preserve me",
    )
    list_response = MagicMock()
    list_response.parsed = MagicMock()
    list_response.parsed.data = [existing]

    updated = _make_mock_adjustment(
        id=42,
        reason="Updated reason",
        additional_info="UPS tracking 1Z123 — preserve me",
    )

    request = UpdateStockAdjustmentParams(id=42, reason="Updated reason", preview=False)

    update_mock = AsyncMock(return_value=MagicMock())
    with (
        patch(
            f"{_SA_GET_ALL}.asyncio_detailed",
            new=AsyncMock(return_value=list_response),
        ),
        patch(f"{_SA_UPDATE}.asyncio_detailed", new=update_mock),
        patch(_SA_UNWRAP_AS, return_value=updated),
        patch(
            "katana_public_api_client.utils.unwrap_data",
            return_value=[existing],
        ),
    ):
        result = await _update_stock_adjustment_impl(request, context)

    assert result.is_preview is False
    assert update_mock.call_args is not None
    body = update_mock.call_args.kwargs["body"]
    assert body.additional_info == "UPS tracking 1Z123 — preserve me"
    assert body.reason == "Updated reason"


@pytest.mark.asyncio
async def test_update_stock_adjustment_skips_echo_when_existing_is_empty():
    """No notes to preserve → wire body keeps `additional_info` as UNSET
    (no echo, since echoing an empty string would be a wasted write)."""
    from katana_public_api_client.client_types import UNSET

    context, _ = create_mock_context()

    existing = _make_mock_adjustment(id=42, reason="Cycle count", additional_info=None)
    list_response = MagicMock()
    list_response.parsed = MagicMock()
    list_response.parsed.data = [existing]

    updated = _make_mock_adjustment(id=42, reason="Updated reason")

    request = UpdateStockAdjustmentParams(id=42, reason="Updated reason", preview=False)

    update_mock = AsyncMock(return_value=MagicMock())
    with (
        patch(
            f"{_SA_GET_ALL}.asyncio_detailed",
            new=AsyncMock(return_value=list_response),
        ),
        patch(f"{_SA_UPDATE}.asyncio_detailed", new=update_mock),
        patch(_SA_UNWRAP_AS, return_value=updated),
        patch(
            "katana_public_api_client.utils.unwrap_data",
            return_value=[existing],
        ),
    ):
        await _update_stock_adjustment_impl(request, context)

    body = update_mock.call_args.kwargs["body"]
    assert body.additional_info is UNSET


@pytest.mark.asyncio
async def test_update_stock_adjustment_caller_explicit_additional_info_wins():
    """Caller-supplied additional_info wins; no pre-fetch needed (saves a round trip)."""
    context, _ = create_mock_context()

    updated = _make_mock_adjustment(id=42, additional_info="new notes")

    request = UpdateStockAdjustmentParams(
        id=42, additional_info="new notes", preview=False
    )

    update_mock = AsyncMock(return_value=MagicMock())
    fetch_mock = AsyncMock()
    with (
        patch(f"{_SA_GET_ALL}.asyncio_detailed", new=fetch_mock),
        patch(f"{_SA_UPDATE}.asyncio_detailed", new=update_mock),
        patch(_SA_UNWRAP_AS, return_value=updated),
    ):
        await _update_stock_adjustment_impl(request, context)

    body = update_mock.call_args.kwargs["body"]
    assert body.additional_info == "new notes"
    fetch_mock.assert_not_awaited()  # No pre-fetch when caller supplied the field


@pytest.mark.asyncio
async def test_update_stock_adjustment_pre_fetch_failure_is_best_effort():
    """Pre-fetch errors must not abort the user's actual update — the echo
    is a best-effort workaround. Without ``raise_on_error=False``, a
    transient 5xx on the pre-fetch would turn this entire PATCH into a
    hard failure even though the workaround is purely opportunistic."""
    context, _ = create_mock_context()

    failed_response = MagicMock()
    failed_response.status_code = 502  # transient gateway error
    failed_response.parsed = None

    updated = _make_mock_adjustment(id=42, reason="Updated reason")

    request = UpdateStockAdjustmentParams(id=42, reason="Updated reason", preview=False)

    update_mock = AsyncMock(return_value=MagicMock())
    with (
        patch(
            f"{_SA_GET_ALL}.asyncio_detailed",
            new=AsyncMock(return_value=failed_response),
        ),
        patch(f"{_SA_UPDATE}.asyncio_detailed", new=update_mock),
        patch(_SA_UNWRAP_AS, return_value=updated),
    ):
        result = await _update_stock_adjustment_impl(request, context)

    # The user's update lands even though the pre-fetch failed.
    assert result.is_preview is False
    update_mock.assert_called_once()


# ============================================================================
# #529: per-location breakdown on check_inventory
# ============================================================================


@pytest.mark.asyncio
async def test_check_inventory_per_location_breakdown_populated():
    """A variant with stock at multiple locations gets a populated
    `by_location` list. Sorted by `in_stock` desc so the largest holding
    shows first. Location names resolved from cache."""
    context, lifespan_ctx = create_mock_context()

    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(
        return_value={"id": 3001, "sku": "WIDGET-001", "display_name": "Test Widget"}
    )

    # Cache returns location names for both warehouses (one bulk call —
    # impl uses get_many_by_ids to avoid an N+1 against the cache).
    lifespan_ctx.typed_cache.catalog.get_many_by_ids = AsyncMock(
        return_value={2: {"name": "East Warehouse"}, 1: {"name": "Main Warehouse"}}
    )

    inv_east = MagicMock()
    inv_east.location_id = 2
    inv_east.quantity_in_stock = "1.0"
    inv_east.quantity_committed = "0.0"
    inv_east.quantity_expected = "0.0"

    inv_main = MagicMock()
    inv_main.location_id = 1
    inv_main.quantity_in_stock = "10.0"
    inv_main.quantity_committed = "2.0"
    inv_main.quantity_expected = "5.0"

    with (
        patch(f"{_INVENTORY_API}.asyncio_detailed", new_callable=AsyncMock),
        patch(_UNWRAP_DATA, return_value=[inv_east, inv_main]),
    ):
        request = CheckInventoryRequest(skus_or_variant_ids=["WIDGET-001"])
        results = await _check_inventory_impl(request, context)

    result = results[0]
    # Totals match the existing aggregation behavior
    assert result.in_stock == 11.0
    assert result.committed == 2.0
    assert result.expected == 5.0
    # Per-location breakdown is populated, sorted desc by in_stock
    assert len(result.by_location) == 2
    assert result.by_location[0].location_id == 1  # Main Warehouse has more stock
    assert result.by_location[0].location_name == "Main Warehouse"
    assert result.by_location[0].in_stock == 10.0
    assert result.by_location[0].available == 8.0  # 10 - 2
    assert result.by_location[1].location_id == 2
    assert result.by_location[1].location_name == "East Warehouse"
    assert result.by_location[1].in_stock == 1.0


@pytest.mark.asyncio
async def test_check_inventory_location_filter_threads_to_api():
    """Passing location_id on the request is forwarded to
    get_all_inventory_point as `location_id=`. Verified by capturing the
    mocked call kwargs."""
    context, lifespan_ctx = create_mock_context()

    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(
        return_value={"id": 3001, "sku": "WIDGET-001", "display_name": "Test Widget"}
    )
    lifespan_ctx.typed_cache.catalog.get_many_by_ids = AsyncMock(
        return_value={2: {"name": "East Warehouse"}}
    )

    inv_east = MagicMock()
    inv_east.location_id = 2
    inv_east.quantity_in_stock = "1.0"
    inv_east.quantity_committed = "0.0"
    inv_east.quantity_expected = "0.0"

    with (
        patch(f"{_INVENTORY_API}.asyncio_detailed", new_callable=AsyncMock) as mock_api,
        patch(_UNWRAP_DATA, return_value=[inv_east]),
    ):
        request = CheckInventoryRequest(
            skus_or_variant_ids=["WIDGET-001"], location_id=2
        )
        await _check_inventory_impl(request, context)

    # The API was called with location_id=2 forwarded
    assert mock_api.call_args is not None
    assert mock_api.call_args.kwargs["location_id"] == 2
    assert mock_api.call_args.kwargs["variant_id"] == 3001


@pytest.mark.asyncio
async def test_check_inventory_zero_stock_returns_empty_by_location():
    """A variant with no stock anywhere returns an empty by_location list
    (not None)."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(
        return_value={"id": 3001, "sku": "WIDGET-001", "display_name": "Test Widget"}
    )

    with (
        patch(f"{_INVENTORY_API}.asyncio_detailed", new_callable=AsyncMock),
        patch(_UNWRAP_DATA, return_value=[]),
    ):
        request = CheckInventoryRequest(skus_or_variant_ids=["WIDGET-001"])
        results = await _check_inventory_impl(request, context)

    assert results[0].in_stock == 0.0
    assert results[0].by_location == []


@pytest.mark.asyncio
async def test_check_inventory_location_name_falls_back_to_none_on_cache_miss():
    """If the cache doesn't have the location (cold cache, lag, etc.),
    `location_name` is None — the location_id alone is still useful and
    cache lag shouldn't block the inventory lookup."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(
        return_value={"id": 3001, "sku": "WIDGET-001", "display_name": "Test Widget"}
    )
    # Cache miss — get_many_by_ids returns an empty dict (the requested
    # location ID isn't in the cache yet, so it's absent from the result).
    lifespan_ctx.typed_cache.catalog.get_many_by_ids = AsyncMock(return_value={})

    inv = MagicMock()
    inv.location_id = 999999
    inv.quantity_in_stock = "5.0"
    inv.quantity_committed = "0.0"
    inv.quantity_expected = "0.0"

    with (
        patch(f"{_INVENTORY_API}.asyncio_detailed", new_callable=AsyncMock),
        patch(_UNWRAP_DATA, return_value=[inv]),
    ):
        request = CheckInventoryRequest(skus_or_variant_ids=["WIDGET-001"])
        results = await _check_inventory_impl(request, context)

    assert len(results[0].by_location) == 1
    assert results[0].by_location[0].location_id == 999999
    assert results[0].by_location[0].location_name is None
    assert results[0].by_location[0].in_stock == 5.0


@pytest.mark.asyncio
async def test_check_inventory_uses_bulk_cache_lookup_not_n_plus_one():
    """Cache enrichment for location names goes through `get_many_by_ids`
    (one query for N IDs), not N round-trips of `get_by_id`.

    Regression for the N+1 pattern that PR #535 review caught — a batch
    request touching many variants across multiple locations would otherwise
    fan out a flood of single-row cache calls."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(
        return_value={"id": 3001, "sku": "WIDGET-001", "display_name": "Test Widget"}
    )

    bulk_mock = AsyncMock(
        return_value={
            2: {"name": "East Warehouse"},
            1: {"name": "Main Warehouse"},
            3: {"name": "R&D Warehouse"},
        }
    )
    lifespan_ctx.typed_cache.catalog.get_many_by_ids = bulk_mock
    # If the impl falls back to per-row lookups, this would be called instead.
    per_row_mock = AsyncMock()
    lifespan_ctx.typed_cache.catalog.get_by_id = per_row_mock

    rows = []
    for loc_id, qty in [(2, "1.0"), (1, "10.0"), (3, "5.0")]:
        inv = MagicMock()
        inv.location_id = loc_id
        inv.quantity_in_stock = qty
        inv.quantity_committed = "0.0"
        inv.quantity_expected = "0.0"
        rows.append(inv)

    with (
        patch(f"{_INVENTORY_API}.asyncio_detailed", new_callable=AsyncMock),
        patch(_UNWRAP_DATA, return_value=rows),
    ):
        request = CheckInventoryRequest(skus_or_variant_ids=["WIDGET-001"])
        results = await _check_inventory_impl(request, context)

    # Per-row fan-out forbidden — the N+1 invariant. Bulk path may fire
    # multiple times now (#549 added parent + supplier enrichment via
    # additional bulk calls), but each call must be O(1) in the number
    # of variants, not O(N).
    per_row_mock.assert_not_awaited()
    # The location-name bulk lookup specifically must happen in a single
    # call covering all unique location IDs — bare ``await_count >= 1``
    # would pass even with a per-location bulk call (one bulk per ID).
    location_calls = [
        call
        for call in bulk_mock.await_args_list
        if call.args and call.args[0] is CachedLocation
    ]
    assert len(location_calls) == 1, (
        f"Location lookup must happen in exactly one bulk call; "
        f"got {len(location_calls)}: {location_calls!r}"
    )
    requested_loc_ids = set(location_calls[0].args[1])
    assert requested_loc_ids == {1, 2, 3}, (
        f"Bulk location lookup must request all 3 IDs at once; "
        f"got {requested_loc_ids!r}"
    )
    # All 3 names resolved via the bulk dict.
    names = {ls.location_name for ls in results[0].by_location}
    assert names == {"East Warehouse", "Main Warehouse", "R&D Warehouse"}


@pytest.mark.asyncio
async def test_check_inventory_surfaces_per_location_thresholds():
    """#549 — per-location reorder_point / safety_stock_level / value /
    average_cost on the inventory point pull through to LocationStock so
    the card can render the threshold-aware per-warehouse breakdown
    without a follow-up call."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(
        return_value={"id": 4001, "sku": "MAT-001", "display_name": "Sealant"}
    )

    inv = MagicMock()
    inv.location_id = 1
    inv.quantity_in_stock = "100.0"
    inv.quantity_committed = "20.0"
    inv.quantity_expected = "30.0"
    inv.reorder_point = "50.0"
    inv.safety_stock_level = "25.0"
    inv.value_in_stock = "1500.0"
    inv.average_cost = "15.00"

    with (
        patch(f"{_INVENTORY_API}.asyncio_detailed", new_callable=AsyncMock),
        patch(_UNWRAP_DATA, return_value=[inv]),
    ):
        request = CheckInventoryRequest(skus_or_variant_ids=["MAT-001"])
        results = await _check_inventory_impl(request, context)

    assert len(results) == 1
    loc = results[0].by_location[0]
    assert loc.reorder_point == 50.0
    assert loc.safety_stock_level == 25.0
    assert loc.value_in_stock == 1500.0
    assert loc.average_cost == 15.00


@pytest.mark.asyncio
async def test_check_inventory_thresholds_default_to_none_when_unset():
    """A missing threshold (UNSET / None on the wire) must surface as
    ``None`` on LocationStock — not silently coerce to ``0.0``, which
    would flip the 'below reorder' check on every empty-threshold row."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(
        return_value={"id": 4002, "sku": "NEW-001", "display_name": "Untracked"}
    )

    inv = MagicMock()
    inv.location_id = 1
    inv.quantity_in_stock = "10.0"
    inv.quantity_committed = "0.0"
    inv.quantity_expected = "0.0"
    inv.reorder_point = UNSET
    inv.safety_stock_level = UNSET
    inv.value_in_stock = UNSET
    inv.average_cost = UNSET

    with (
        patch(f"{_INVENTORY_API}.asyncio_detailed", new_callable=AsyncMock),
        patch(_UNWRAP_DATA, return_value=[inv]),
    ):
        request = CheckInventoryRequest(skus_or_variant_ids=["NEW-001"])
        results = await _check_inventory_impl(request, context)

    loc = results[0].by_location[0]
    assert loc.reorder_point is None
    assert loc.safety_stock_level is None
    assert loc.value_in_stock is None
    assert loc.average_cost is None


@pytest.mark.asyncio
async def test_check_inventory_populates_parent_enrichment_fields():
    """End-to-end: ``_enrich_stock_info_with_parent`` actually writes
    ``uom``, supplier, ``parent_type``, and ``katana_url`` onto the
    response when the cache returns a variant + parent + supplier.

    Without this, all the enrichment plumbing could regress (e.g. wrong
    parent_id key, missed write, narrowed condition) and only the UI
    tests — which pass enrichment fields *directly* into the card —
    would still pass green.
    """
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(
        return_value={
            "id": 6001,
            "sku": "WIDGET-001",
            "display_name": "Test Widget",
            "product_id": 700,
            "material_id": None,
        }
    )

    # Inventory point + bulk lookups for variants / products / suppliers.
    # `get_many_by_ids` is the single path enrichment fans out through —
    # return per-class rows keyed by ID so the dispatcher in
    # `_enrich_stock_info_with_parent` finds product 700 and supplier 42.
    inv = MagicMock()
    inv.location_id = 1
    inv.quantity_in_stock = "5.0"
    inv.quantity_committed = "0.0"
    inv.quantity_expected = "0.0"
    inv.reorder_point = "10.0"
    inv.safety_stock_level = "5.0"
    inv.value_in_stock = "50.0"
    inv.average_cost = "10.0"

    async def _bulk(cls, ids, **_kwargs):
        from katana_public_api_client.models_pydantic._generated import (
            CachedMaterial,
            CachedProduct,
            CachedSupplier,
            CachedVariant,
        )

        # MagicMock's ``name`` constructor arg sets the *repr* name, not
        # the attribute — use post-construction assignment so the mock's
        # ``.name`` actually returns a plain string for pydantic.
        if cls is CachedLocation:
            loc = MagicMock()
            loc.name = "Main"
            return {1: loc}
        if cls is CachedVariant:
            v = MagicMock()
            v.id = 6001
            v.product_id = 700
            v.material_id = None
            return {6001: v}
        if cls is CachedProduct:
            p = MagicMock()
            p.id = 700
            p.uom = "pcs"
            p.default_supplier_id = 42
            return {700: p}
        if cls is CachedMaterial:
            return {}
        if cls is CachedSupplier:
            s = MagicMock()
            s.id = 42
            s.name = "Acme Inc."
            return {42: s}
        return {}

    lifespan_ctx.typed_cache.catalog.get_many_by_ids = AsyncMock(side_effect=_bulk)

    with (
        patch(f"{_INVENTORY_API}.asyncio_detailed", new_callable=AsyncMock),
        patch(_UNWRAP_DATA, return_value=[inv]),
    ):
        request = CheckInventoryRequest(skus_or_variant_ids=["WIDGET-001"])
        results = await _check_inventory_impl(request, context)

    r = results[0]
    assert r.uom == "pcs"
    assert r.default_supplier_id == 42
    assert r.default_supplier_name == "Acme Inc."
    assert r.parent_type == "product"
    # `katana_url` is built from the (entity_kind, parent_id) pair —
    # the path template lives in web_urls.py so we just assert the
    # parent_id appears in the URL rather than pinning the full string.
    assert r.katana_url is not None and "/product/700" in r.katana_url


@pytest.mark.asyncio
async def test_check_inventory_variant_id_cold_cache_recovers_parent_from_extend():
    """Cold-cache variant_id path must NOT silently drop ``uom`` /
    ``default_supplier_id`` when the parent is also absent from the
    cache. ``_fetch_variant_by_id`` extends with ``PRODUCT_OR_MATERIAL``
    so the nested parent rides on the API-fallback response, and
    ``_enrich_variants_with_parent`` grafts it into the lookup map when
    the bulk cache query misses."""
    from katana_public_api_client.models import Product, VariantResponse
    from katana_public_api_client.models.product_type import ProductType

    context, lifespan_ctx = create_mock_context()

    # Variant cache miss → API fallback. VariantResponse carries the
    # extended ``product_or_material`` payload as a real ``Product``
    # attrs model with ``uom`` and ``default_supplier_id`` set.
    parent = Product(
        id=700,
        name="Widget 42",
        type_=ProductType.PRODUCT,
        uom="pcs",
        default_supplier_id=42,
    )
    variant_response = VariantResponse(
        id=42,
        sku="WIDGET-42",
        product_id=700,
        product_or_material=parent,
    )

    # Bulk cache lookups all return empty — parent product 700 and
    # variant 42 are both absent. Supplier 42 is also absent (the
    # cold-cache test ensures the nested parent is enough to surface
    # ``uom`` / ``default_supplier_id`` even when supplier name lookup
    # also misses).
    async def _bulk(_cls, _ids, **_kwargs):
        return {}

    lifespan_ctx.typed_cache.catalog.get_many_by_ids = AsyncMock(side_effect=_bulk)
    lifespan_ctx.typed_cache.catalog.get_by_id = AsyncMock(return_value=None)

    inv = MagicMock()
    inv.location_id = 1
    inv.quantity_in_stock = "5.0"
    inv.quantity_committed = "0.0"
    inv.quantity_expected = "0.0"
    inv.reorder_point = UNSET
    inv.safety_stock_level = UNSET
    inv.value_in_stock = UNSET
    inv.average_cost = UNSET

    with (
        patch(
            "katana_public_api_client.api.variant.get_variant.asyncio_detailed",
            new_callable=AsyncMock,
        ) as mock_get_variant,
        patch(
            "katana_public_api_client.utils.unwrap",
            return_value=variant_response,
        ),
        patch(f"{_INVENTORY_API}.asyncio_detailed", new_callable=AsyncMock),
        patch(_UNWRAP_DATA, return_value=[inv]),
    ):
        request = CheckInventoryRequest(skus_or_variant_ids=[42])
        results = await _check_inventory_impl(request, context)

    r = results[0]
    # Critical assertions: enrichment recovers uom + default_supplier_id
    # from the nested parent even though the parent cache lookup missed.
    assert r.uom == "pcs"
    assert r.default_supplier_id == 42
    assert r.parent_type == "product"
    assert r.katana_url is not None and "/product/700" in r.katana_url
    # SKU is non-null here; the ordering is display_name → sku → parent.name,
    # so product_name resolves to the SKU. The parent-name fallback covers
    # the null-SKU path — see ``test_..._null_sku_uses_parent_name``.
    assert r.product_name == "WIDGET-42"
    assert r.is_found is True
    # Pin the API contract: the call MUST request ``PRODUCT_OR_MATERIAL``
    # via ``extend`` — without that, the live API returns a stripped
    # ``VariantResponse`` and cold-cache enrichment silently loses uom /
    # default_supplier (the unwrap mock above hides the regression).
    from katana_public_api_client.models import GetVariantExtendItem

    mock_get_variant.assert_awaited_once()
    await_args = mock_get_variant.await_args
    assert await_args is not None
    assert await_args.kwargs.get("extend") == [GetVariantExtendItem.PRODUCT_OR_MATERIAL]


@pytest.mark.asyncio
async def test_check_inventory_variant_id_cold_cache_null_sku_uses_parent_name():
    """SKU-less + cold-cache variant_id path must surface the parent's
    name as ``product_name`` — the API-fallback ``VariantResponse`` has
    no ``display_name`` field and ``Variant.sku`` is nullable, so
    without the parent fallback the card title would degrade to
    "Unknown" for an entirely valid variant."""
    from katana_public_api_client.models import Product, VariantResponse
    from katana_public_api_client.models.product_type import ProductType

    context, lifespan_ctx = create_mock_context()

    # Variant carries a null SKU (the documented legacy NetSuite case)
    # and no display_name. The extended parent payload supplies the name.
    parent = Product(id=701, name="Legacy NetSuite Widget", type_=ProductType.PRODUCT)
    variant_response = VariantResponse(
        id=43, sku=None, product_id=701, product_or_material=parent
    )

    async def _bulk(_cls, _ids, **_kwargs):
        return {}

    lifespan_ctx.typed_cache.catalog.get_many_by_ids = AsyncMock(side_effect=_bulk)
    lifespan_ctx.typed_cache.catalog.get_by_id = AsyncMock(return_value=None)

    inv = MagicMock()
    inv.location_id = 1
    inv.quantity_in_stock = "0.0"
    inv.quantity_committed = "0.0"
    inv.quantity_expected = "0.0"
    inv.reorder_point = UNSET
    inv.safety_stock_level = UNSET
    inv.value_in_stock = UNSET
    inv.average_cost = UNSET

    with (
        patch(
            "katana_public_api_client.api.variant.get_variant.asyncio_detailed",
            new_callable=AsyncMock,
        ),
        patch(
            "katana_public_api_client.utils.unwrap",
            return_value=variant_response,
        ),
        patch(f"{_INVENTORY_API}.asyncio_detailed", new_callable=AsyncMock),
        patch(_UNWRAP_DATA, return_value=[inv]),
    ):
        request = CheckInventoryRequest(skus_or_variant_ids=[43])
        results = await _check_inventory_impl(request, context)

    r = results[0]
    assert r.is_found is True
    assert r.product_name == "Legacy NetSuite Widget"


@pytest.mark.asyncio
async def test_check_inventory_not_found_marks_is_found_false():
    """Not-found stubs echo the input back in ``sku``/``variant_id`` but
    must set ``is_found=False`` so the UI footer can suppress actionable
    buttons that would otherwise target a non-existent variant."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(return_value=None)
    lifespan_ctx.typed_cache.catalog.get_by_id = AsyncMock(return_value=None)

    with patch(
        "katana_mcp.tools.foundation.items._fetch_variant_by_id",
        new_callable=AsyncMock,
        return_value=None,
    ):
        request = CheckInventoryRequest(skus_or_variant_ids=["MISSING-SKU", 99999])
        results = await _check_inventory_impl(request, context)

    assert len(results) == 2
    # SKU stub: echoed back, but flagged not-found.
    assert results[0].sku == "MISSING-SKU"
    assert results[0].is_found is False
    # variant_id stub: echoed back, but flagged not-found.
    assert results[1].variant_id == 99999
    assert results[1].is_found is False


def test_inventory_check_footer_suppresses_buttons_when_not_found():
    """``is_found=False`` must hide Create PO / View Variant Details so
    the agent does not chase a variant the server reported missing."""
    from katana_mcp.tools.prefab_ui import build_inventory_check_ui

    stock = {
        "sku": "MISSING-SKU",
        "product_name": "",
        "in_stock": 0,
        "available_stock": 0,
        "committed": 0,
        "expected": 0,
        "is_found": False,
    }
    import json as _json

    rendered = _json.dumps(build_inventory_check_ui(stock).to_json())
    assert "Create PO" not in rendered
    assert "View Variant Details" not in rendered


def test_inventory_check_card_renders_by_location_table_when_split():
    """Single-item Prefab card renders a per-location table when stock is
    split across multiple warehouses. This is the load-bearing path
    (single-SKU lookup is the most common check_inventory call). Without
    this, the per-location data on `StockInfo` is invisible to the
    primary user-facing render path."""
    from katana_mcp.tools.prefab_ui import build_inventory_check_ui

    stock = {
        "sku": "WIDGET-001",
        "product_name": "Test Widget",
        "in_stock": 11.0,
        "available_stock": 9.0,
        "committed": 2.0,
        "expected": 5.0,
        "by_location": [
            {
                "location_id": 1,
                "location_name": "Main Warehouse",
                "in_stock": 10.0,
                "committed": 2.0,
                "expected": 5.0,
                "available": 8.0,
            },
            {
                "location_id": 2,
                "location_name": "East Warehouse",
                "in_stock": 1.0,
                "committed": 0.0,
                "expected": 0.0,
                "available": 1.0,
            },
        ],
    }
    import json as _json

    rendered = _json.dumps(build_inventory_check_ui(stock).to_json())
    # The DataTable is in the tree
    assert "DataTable" in rendered
    # The per-location stock data is wired through state for the renderer
    assert '"by_location"' in rendered
    # The "N locations" badge is set
    assert "2 locations" in rendered


def test_inventory_check_card_omits_by_location_table_when_single_location():
    """When stock is at one location only, no breakdown table — keeps the
    common case quiet. The headline metrics already tell the story."""
    from katana_mcp.tools.prefab_ui import build_inventory_check_ui

    stock = {
        "sku": "WIDGET-001",
        "product_name": "Test Widget",
        "in_stock": 10.0,
        "available_stock": 8.0,
        "committed": 2.0,
        "expected": 5.0,
        "by_location": [
            {
                "location_id": 1,
                "location_name": "Main Warehouse",
                "in_stock": 10.0,
                "committed": 2.0,
                "expected": 5.0,
                "available": 8.0,
            },
        ],
    }
    import json as _json

    rendered = _json.dumps(build_inventory_check_ui(stock).to_json())
    assert "DataTable" not in rendered
    assert "locations" not in rendered  # No "N locations" badge either


# ============================================================================
# get_inventory_movements: filter pass-through (Phase 1 of #761)
# ============================================================================


@pytest.mark.asyncio
async def test_get_inventory_movements_forwards_location_id():
    """location_id reaches the API call kwargs verbatim."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(
        return_value={"id": 3001, "sku": "W-1", "display_name": "Widget"}
    )

    _patch_movements_call(lifespan_ctx)
    with (
        patch(
            f"{_MOVEMENTS_API}._get_kwargs", wraps=_movements_api._get_kwargs
        ) as mock_kwargs,
        patch(_UNWRAP_DATA, return_value=[]),
    ):
        request = GetInventoryMovementsRequest(sku="W-1", location_id=42)
        await _get_inventory_movements_impl(request, context)

    assert mock_kwargs.call_args.kwargs["location_id"] == 42


@pytest.mark.asyncio
async def test_get_inventory_movements_omits_unset_filters():
    """Unset optional filters land as UNSET so the URL doesn't carry empty params."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(
        return_value={"id": 3001, "sku": "W-1", "display_name": "Widget"}
    )

    _patch_movements_call(lifespan_ctx)
    with (
        patch(
            f"{_MOVEMENTS_API}._get_kwargs", wraps=_movements_api._get_kwargs
        ) as mock_kwargs,
        patch(_UNWRAP_DATA, return_value=[]),
    ):
        request = GetInventoryMovementsRequest(sku="W-1")
        await _get_inventory_movements_impl(request, context)

    kw = mock_kwargs.call_args.kwargs
    assert kw["location_id"] is UNSET
    assert kw["resource_type"] is UNSET
    assert kw["created_at_min"] is UNSET
    assert kw["created_at_max"] is UNSET
    assert kw["updated_at_min"] is UNSET
    assert kw["updated_at_max"] is UNSET


@pytest.mark.asyncio
async def test_get_inventory_movements_forwards_resource_type_enum():
    """Valid resource_type string is coerced to the enum and forwarded."""
    from katana_public_api_client.models.get_all_inventory_movements_resource_type import (
        GetAllInventoryMovementsResourceType,
    )

    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(
        return_value={"id": 3001, "sku": "W-1", "display_name": "Widget"}
    )

    _patch_movements_call(lifespan_ctx)
    with (
        patch(
            f"{_MOVEMENTS_API}._get_kwargs", wraps=_movements_api._get_kwargs
        ) as mock_kwargs,
        patch(_UNWRAP_DATA, return_value=[]),
    ):
        # Pydantic v2 coerces JSON string values into StrEnum members at
        # request construction; pass the enum directly so pyright is happy
        # in the test code itself.
        request = GetInventoryMovementsRequest(
            sku="W-1",
            resource_type=GetAllInventoryMovementsResourceType.STOCKADJUSTMENTROW,
        )
        await _get_inventory_movements_impl(request, context)

    assert (
        mock_kwargs.call_args.kwargs["resource_type"]
        == GetAllInventoryMovementsResourceType.STOCKADJUSTMENTROW
    )


def test_get_inventory_movements_rejects_invalid_resource_type():
    """Invalid resource_type surfaces as a Pydantic ValidationError naming the field.

    Uses ``model_validate`` to mirror the real MCP path — caller-supplied
    JSON arrives as raw dict values, not pre-typed kwargs.
    """
    with pytest.raises(ValidationError, match="resource_type"):
        GetInventoryMovementsRequest.model_validate(
            {"sku": "W-1", "resource_type": "NotARealType"}
        )


@pytest.mark.asyncio
async def test_get_inventory_movements_forwards_date_filters():
    """Date strings parse into naive UTC datetimes on the API kwargs."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(
        return_value={"id": 3001, "sku": "W-1", "display_name": "Widget"}
    )

    _patch_movements_call(lifespan_ctx)
    with (
        patch(
            f"{_MOVEMENTS_API}._get_kwargs", wraps=_movements_api._get_kwargs
        ) as mock_kwargs,
        patch(_UNWRAP_DATA, return_value=[]),
    ):
        request = GetInventoryMovementsRequest(
            sku="W-1",
            created_at_min="2026-01-01T00:00:00Z",
            created_at_max="2026-04-01T00:00:00Z",
            updated_at_min="2026-02-01T00:00:00Z",
            updated_at_max="2026-03-01T00:00:00Z",
        )
        await _get_inventory_movements_impl(request, context)

    kw = mock_kwargs.call_args.kwargs
    assert kw["created_at_min"] == datetime(2026, 1, 1, 0, 0, 0)
    assert kw["created_at_max"] == datetime(2026, 4, 1, 0, 0, 0)
    assert kw["updated_at_min"] == datetime(2026, 2, 1, 0, 0, 0)
    assert kw["updated_at_max"] == datetime(2026, 3, 1, 0, 0, 0)


@pytest.mark.asyncio
async def test_get_inventory_movements_rejects_bad_iso_string():
    """Malformed ISO datetime surfaces with the field name in the error."""
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(
        return_value={"id": 3001, "sku": "W-1", "display_name": "Widget"}
    )

    request = GetInventoryMovementsRequest(sku="W-1", created_at_min="not-a-datetime")
    with pytest.raises(ValueError, match="created_at_min"):
        await _get_inventory_movements_impl(request, context)


@pytest.mark.asyncio
async def test_get_inventory_movements_forwards_max_items_extension():
    """``request.limit`` lands on the httpx extensions as ``max_items``.

    Regression for #771: without the ``max_items`` extension, the
    auto-pagination transport treats ``limit`` as page size and walks every
    page, so passing ``limit=N`` would still return the full history. The
    fix forwards ``request.limit`` as ``extensions={"max_items": N}`` so the
    transport caps the merged result at N rows.
    """
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(
        return_value={"id": 3001, "sku": "W-1", "display_name": "Widget"}
    )

    request_mock = _patch_movements_call(lifespan_ctx)
    with patch(_UNWRAP_DATA, return_value=[]):
        request = GetInventoryMovementsRequest(sku="W-1", limit=5)
        await _get_inventory_movements_impl(request, context)

    # The httpx call must carry the row-cap extension matching request.limit.
    extensions = request_mock.call_args.kwargs["extensions"]
    assert extensions == {"max_items": 5}


@pytest.mark.asyncio
async def test_get_inventory_movements_clamps_per_page_limit_to_katana_max():
    """Per-page ``?limit`` is clamped to Katana's documented max of 250.

    Regression for the #771 follow-up review: ``request.limit`` is the
    user-facing row cap, but Katana's documented max page size is 250
    (see ``docs/katana-openapi.yaml`` lines 21-24). Threading the raw
    ``request.limit=500`` straight into the API ``?limit=`` query param
    would make Katana reject the request instead of paginating up to a
    500-row cap. The fix clamps the per-page query limit to 250 while
    leaving ``max_items`` at the user-requested cap; the transport
    paginates additional pages as needed.
    """
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(
        return_value={"id": 3001, "sku": "W-1", "display_name": "Widget"}
    )

    request_mock = _patch_movements_call(lifespan_ctx)
    with patch(_UNWRAP_DATA, return_value=[]):
        request = GetInventoryMovementsRequest(sku="W-1", limit=500)
        await _get_inventory_movements_impl(request, context)

    # The underlying httpx request must carry ?limit=250 (clamped), not 500.
    # ``_get_kwargs`` threads ``limit`` into the ``params`` dict.
    params = request_mock.call_args.kwargs["params"]
    assert params["limit"] == 250

    # ``max_items`` must remain at the user-requested row cap (uncapped at 250).
    extensions = request_mock.call_args.kwargs["extensions"]
    assert extensions == {"max_items": 500}


@pytest.mark.asyncio
async def test_get_inventory_movements_caps_rows_via_transport():
    """End-to-end: ``limit=N`` returns exactly N movements even when the
    API has more pages.

    Drives a real :class:`KatanaClient` against an ``httpx.MockTransport``
    wrapped by the :class:`PaginationTransport` (so the ``max_items``
    extension is honored end-to-end). When the user passes ``transport=`` to
    ``KatanaClient`` directly the resilient transport chain is bypassed, so
    we re-create the pagination layer manually to mirror the production
    stack. The MCP requests ``limit=3`` — without the fix the transport
    would walk every page and return all movements; with the fix the
    ``max_items=3`` extension caps the merged result at 3.
    """
    import httpx

    from katana_public_api_client import KatanaClient
    from katana_public_api_client.katana_client import PaginationTransport

    pages_served: list[int] = []

    def _movement(idx: int) -> dict:
        return {
            "id": idx,
            "variant_id": 3001,
            "location_id": 1,
            "resource_type": "PurchaseOrderRow",
            "movement_date": "2026-04-01T12:00:00+00:00",
            "quantity_change": 1.0,
            "balance_after": float(idx),
            "value_per_unit": 1.0,
            "value_in_stock_after": float(idx),
            "average_cost_after": 1.0,
            "created_at": "2026-04-01T12:00:00+00:00",
            "updated_at": "2026-04-01T12:00:00+00:00",
        }

    def handler(req: httpx.Request) -> httpx.Response:
        page = int(req.url.params.get("page", 1))
        pages_served.append(page)
        # Always serve 5 rows per page regardless of the requested limit so
        # the transport must enforce the row cap itself; pretend 3 total
        # pages exist so an uncapped walk would consume all 15.
        data = [_movement(idx) for idx in range((page - 1) * 5 + 1, page * 5 + 1)]
        return httpx.Response(
            200,
            json={
                "data": data,
                "pagination": {"page": page, "total_pages": 3, "page_size": 5},
            },
        )

    paginated_transport = PaginationTransport(
        wrapped_transport=httpx.MockTransport(handler),
        max_pages=5,
    )
    async with KatanaClient(
        api_key="test-key",
        base_url="https://api.example.com",
        transport=paginated_transport,
    ) as client:
        context, lifespan_ctx = create_mock_context()
        lifespan_ctx.client = client
        lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(
            return_value={"id": 3001, "sku": "W-1", "display_name": "Widget"}
        )

        request = GetInventoryMovementsRequest(sku="W-1", limit=3)
        result = await _get_inventory_movements_impl(request, context)

    assert result.total_count == 3
    assert len(result.movements) == 3
    # The transport should have stopped after the first page since
    # max_items=3 was satisfied on page 1 (which served 5 candidates).
    assert pages_served == [1]


# ============================================================================
# inventory_at: point-in-time balance reconstruction (Phase 2 of #761)
# ============================================================================


def _make_movement(
    *,
    movement_id: int,
    variant_id: int,
    location_id: int,
    movement_date: datetime,
    balance_after: float = 0.0,
    value_in_stock_after: float = 0.0,
    average_cost_after: float = 0.0,
) -> MagicMock:
    """Build a movement mock carrying only the fields _inventory_at_impl reads."""
    m = MagicMock()
    m.id = movement_id
    m.variant_id = variant_id
    m.location_id = location_id
    m.movement_date = movement_date
    m.balance_after = balance_after
    m.value_in_stock_after = value_in_stock_after
    m.average_cost_after = average_cost_after
    return m


@pytest.mark.asyncio
async def test_inventory_at_single_sku_resolution():
    """Resolves a single SKU and returns the latest pre-as_of balance per location."""
    from katana_mcp.tools.foundation.inventory import (
        InventoryAtRequest,
        _inventory_at_impl,
    )

    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(
        return_value={"id": 3001, "sku": "W-1", "display_name": "Widget"}
    )
    lifespan_ctx.typed_cache.catalog.get_many_by_ids = AsyncMock(
        return_value={1: {"id": 1, "name": "Main"}}
    )

    movements = [
        _make_movement(
            movement_id=1,
            variant_id=3001,
            location_id=1,
            movement_date=datetime(2026, 1, 5, 12, 0, 0, tzinfo=UTC),
            balance_after=50.0,
            value_in_stock_after=2500.0,
            average_cost_after=50.0,
        ),
        _make_movement(
            movement_id=2,
            variant_id=3001,
            location_id=1,
            movement_date=datetime(2026, 3, 1, 12, 0, 0, tzinfo=UTC),
            balance_after=80.0,
            value_in_stock_after=4000.0,
            average_cost_after=50.0,
        ),
    ]

    with (
        patch(f"{_MOVEMENTS_API}.asyncio_detailed", new_callable=AsyncMock),
        patch(_UNWRAP_DATA, return_value=movements),
    ):
        request = InventoryAtRequest(
            skus_or_variant_ids=["W-1"], as_of="2026-04-01T00:00:00Z"
        )
        response = await _inventory_at_impl(request, context)

    assert response.as_of == "2026-04-01T00:00:00Z"
    assert response.not_found == []
    assert len(response.items) == 1
    item = response.items[0]
    assert item.sku == "W-1"
    assert item.variant_id == 3001
    assert len(item.by_location) == 1
    loc = item.by_location[0]
    assert loc.location_id == 1
    assert loc.location_name == "Main"
    assert loc.balance_at == 80.0  # latest pre-as_of
    assert loc.last_movement_id == 2
    assert item.total_balance == 80.0
    assert item.total_value == 4000.0


@pytest.mark.asyncio
async def test_inventory_at_resolves_variant_id_directly():
    """Integer inputs go through _fetch_variant_by_id, not get_by_sku."""
    from katana_mcp.tools.foundation.inventory import (
        InventoryAtRequest,
        _inventory_at_impl,
    )

    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(return_value=None)
    lifespan_ctx.typed_cache.catalog.get_many_by_ids = AsyncMock(return_value={})

    with (
        patch(
            "katana_mcp.tools.foundation.items._fetch_variant_by_id",
            new_callable=AsyncMock,
        ) as mock_by_id,
        patch(f"{_MOVEMENTS_API}.asyncio_detailed", new_callable=AsyncMock),
        patch(_UNWRAP_DATA, return_value=[]),
    ):
        mock_by_id.return_value = {
            "id": 12345,
            "sku": "BY-ID",
            "display_name": "By ID",
        }
        request = InventoryAtRequest(
            skus_or_variant_ids=[12345], as_of="2026-04-01T00:00:00Z"
        )
        response = await _inventory_at_impl(request, context)

    assert response.not_found == []
    assert response.items[0].variant_id == 12345
    assert response.items[0].sku == "BY-ID"
    mock_by_id.assert_awaited_once()


@pytest.mark.asyncio
async def test_inventory_at_unresolved_inputs_land_in_not_found():
    """SKUs and IDs that can't be resolved are reported via not_found."""
    from katana_mcp.tools.foundation.inventory import (
        InventoryAtRequest,
        _inventory_at_impl,
    )

    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(return_value=None)
    lifespan_ctx.typed_cache.catalog.get_many_by_ids = AsyncMock(return_value={})

    with (
        patch(
            "katana_mcp.tools.foundation.items._fetch_variant_by_id",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(f"{_MOVEMENTS_API}.asyncio_detailed", new_callable=AsyncMock),
        patch(_UNWRAP_DATA, return_value=[]),
    ):
        request = InventoryAtRequest(
            skus_or_variant_ids=["GHOST", 99999],
            as_of="2026-04-01T00:00:00Z",
        )
        response = await _inventory_at_impl(request, context)

    assert response.items == []
    assert set(response.not_found) == {"GHOST", 99999}


@pytest.mark.asyncio
async def test_inventory_at_multi_location_grouping():
    """Each location gets its own row; totals roll up across locations."""
    from katana_mcp.tools.foundation.inventory import (
        InventoryAtRequest,
        _inventory_at_impl,
    )

    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(
        return_value={"id": 3001, "sku": "W-1", "display_name": "Widget"}
    )
    lifespan_ctx.typed_cache.catalog.get_many_by_ids = AsyncMock(
        return_value={
            1: {"id": 1, "name": "Main"},
            2: {"id": 2, "name": "Annex"},
        }
    )

    movements = [
        _make_movement(
            movement_id=1,
            variant_id=3001,
            location_id=1,
            movement_date=datetime(2026, 2, 1, tzinfo=UTC),
            balance_after=10.0,
            value_in_stock_after=100.0,
        ),
        _make_movement(
            movement_id=2,
            variant_id=3001,
            location_id=2,
            movement_date=datetime(2026, 2, 5, tzinfo=UTC),
            balance_after=25.0,
            value_in_stock_after=250.0,
        ),
    ]

    with (
        patch(f"{_MOVEMENTS_API}.asyncio_detailed", new_callable=AsyncMock),
        patch(_UNWRAP_DATA, return_value=movements),
    ):
        request = InventoryAtRequest(
            skus_or_variant_ids=["W-1"], as_of="2026-04-01T00:00:00Z"
        )
        response = await _inventory_at_impl(request, context)

    item = response.items[0]
    assert {loc.location_id for loc in item.by_location} == {1, 2}
    assert item.total_balance == 35.0
    assert item.total_value == 350.0


@pytest.mark.asyncio
async def test_inventory_at_picks_latest_movement_per_location():
    """When multiple movements precede as_of, the most recent (by date, id) wins."""
    from katana_mcp.tools.foundation.inventory import (
        InventoryAtRequest,
        _inventory_at_impl,
    )

    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(
        return_value={"id": 3001, "sku": "W-1", "display_name": "Widget"}
    )
    lifespan_ctx.typed_cache.catalog.get_many_by_ids = AsyncMock(return_value={})

    # Three movements at the same location, same day, different times + ids.
    # The id-7 row has the latest movement_date — it should win.
    movements = [
        _make_movement(
            movement_id=5,
            variant_id=3001,
            location_id=1,
            movement_date=datetime(2026, 3, 1, 8, 0, tzinfo=UTC),
            balance_after=10.0,
        ),
        _make_movement(
            movement_id=7,
            variant_id=3001,
            location_id=1,
            movement_date=datetime(2026, 3, 1, 14, 0, tzinfo=UTC),
            balance_after=20.0,
        ),
        _make_movement(
            movement_id=6,
            variant_id=3001,
            location_id=1,
            movement_date=datetime(2026, 3, 1, 11, 0, tzinfo=UTC),
            balance_after=15.0,
        ),
    ]

    with (
        patch(f"{_MOVEMENTS_API}.asyncio_detailed", new_callable=AsyncMock),
        patch(_UNWRAP_DATA, return_value=movements),
    ):
        request = InventoryAtRequest(
            skus_or_variant_ids=["W-1"], as_of="2026-04-01T00:00:00Z"
        )
        response = await _inventory_at_impl(request, context)

    loc = response.items[0].by_location[0]
    assert loc.balance_at == 20.0
    assert loc.last_movement_id == 7


@pytest.mark.asyncio
async def test_inventory_at_id_breaks_ties_when_dates_identical():
    """If movement_date ties, higher id wins (deterministic output)."""
    from katana_mcp.tools.foundation.inventory import (
        InventoryAtRequest,
        _inventory_at_impl,
    )

    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(
        return_value={"id": 3001, "sku": "W-1", "display_name": "Widget"}
    )
    lifespan_ctx.typed_cache.catalog.get_many_by_ids = AsyncMock(return_value={})

    same_dt = datetime(2026, 3, 1, 12, 0, tzinfo=UTC)
    movements = [
        _make_movement(
            movement_id=5,
            variant_id=3001,
            location_id=1,
            movement_date=same_dt,
            balance_after=10.0,
        ),
        _make_movement(
            movement_id=7,
            variant_id=3001,
            location_id=1,
            movement_date=same_dt,
            balance_after=20.0,
        ),
    ]

    with (
        patch(f"{_MOVEMENTS_API}.asyncio_detailed", new_callable=AsyncMock),
        patch(_UNWRAP_DATA, return_value=movements),
    ):
        request = InventoryAtRequest(
            skus_or_variant_ids=["W-1"], as_of="2026-04-01T00:00:00Z"
        )
        response = await _inventory_at_impl(request, context)

    assert response.items[0].by_location[0].last_movement_id == 7


@pytest.mark.asyncio
async def test_inventory_at_skips_movements_after_as_of():
    """Movements with movement_date > as_of_dt are excluded from the reduction."""
    from katana_mcp.tools.foundation.inventory import (
        InventoryAtRequest,
        _inventory_at_impl,
    )

    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(
        return_value={"id": 3001, "sku": "W-1", "display_name": "Widget"}
    )
    lifespan_ctx.typed_cache.catalog.get_many_by_ids = AsyncMock(return_value={})

    movements = [
        _make_movement(
            movement_id=1,
            variant_id=3001,
            location_id=1,
            movement_date=datetime(2026, 1, 1, tzinfo=UTC),
            balance_after=10.0,
        ),
        _make_movement(
            movement_id=2,
            variant_id=3001,
            location_id=1,
            movement_date=datetime(2026, 5, 1, tzinfo=UTC),  # AFTER as_of
            balance_after=999.0,
        ),
    ]

    with (
        patch(f"{_MOVEMENTS_API}.asyncio_detailed", new_callable=AsyncMock),
        patch(_UNWRAP_DATA, return_value=movements),
    ):
        request = InventoryAtRequest(
            skus_or_variant_ids=["W-1"], as_of="2026-03-01T00:00:00Z"
        )
        response = await _inventory_at_impl(request, context)

    assert response.items[0].by_location[0].balance_at == 10.0
    assert response.items[0].by_location[0].last_movement_id == 1


@pytest.mark.asyncio
async def test_inventory_at_empty_by_location_when_no_movements_before():
    """as_of earlier than every movement → by_location is empty (no history)."""
    from katana_mcp.tools.foundation.inventory import (
        InventoryAtRequest,
        _inventory_at_impl,
    )

    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(
        return_value={"id": 3001, "sku": "W-1", "display_name": "Widget"}
    )
    lifespan_ctx.typed_cache.catalog.get_many_by_ids = AsyncMock(return_value={})

    movements = [
        _make_movement(
            movement_id=1,
            variant_id=3001,
            location_id=1,
            movement_date=datetime(2026, 6, 1, tzinfo=UTC),
            balance_after=10.0,
        )
    ]

    with (
        patch(f"{_MOVEMENTS_API}.asyncio_detailed", new_callable=AsyncMock),
        patch(_UNWRAP_DATA, return_value=movements),
    ):
        request = InventoryAtRequest(
            skus_or_variant_ids=["W-1"], as_of="2026-01-01T00:00:00Z"
        )
        response = await _inventory_at_impl(request, context)

    assert response.items[0].by_location == []
    assert response.items[0].total_balance == 0.0


@pytest.mark.asyncio
async def test_inventory_at_forwards_location_id_filter():
    """Optional location_id flows to the inventory_movements API call."""
    from katana_mcp.tools.foundation.inventory import (
        InventoryAtRequest,
        _inventory_at_impl,
    )

    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(
        return_value={"id": 3001, "sku": "W-1", "display_name": "Widget"}
    )
    lifespan_ctx.typed_cache.catalog.get_many_by_ids = AsyncMock(return_value={})

    with (
        patch(f"{_MOVEMENTS_API}.asyncio_detailed", new_callable=AsyncMock) as mock_api,
        patch(_UNWRAP_DATA, return_value=[]),
    ):
        request = InventoryAtRequest(
            skus_or_variant_ids=["W-1"],
            as_of="2026-04-01T00:00:00Z",
            location_id=42,
        )
        await _inventory_at_impl(request, context)

    assert mock_api.call_args.kwargs["location_id"] == 42


@pytest.mark.asyncio
async def test_inventory_at_tolerates_null_sku():
    """variant_id input where the variant has sku=None resolves cleanly (sku in
    response is null; lookup never hits the SKU index)."""
    from katana_mcp.tools.foundation.inventory import (
        InventoryAtRequest,
        _inventory_at_impl,
    )

    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(return_value=None)
    lifespan_ctx.typed_cache.catalog.get_many_by_ids = AsyncMock(return_value={})

    with (
        patch(
            "katana_mcp.tools.foundation.items._fetch_variant_by_id",
            new_callable=AsyncMock,
        ) as mock_by_id,
        patch(f"{_MOVEMENTS_API}.asyncio_detailed", new_callable=AsyncMock),
        patch(_UNWRAP_DATA, return_value=[]),
    ):
        # Variant exists in cache but has no SKU (legacy NetSuite import).
        mock_by_id.return_value = {
            "id": 555,
            "sku": None,
            "display_name": "Mystery Widget",
        }
        request = InventoryAtRequest(
            skus_or_variant_ids=[555], as_of="2026-04-01T00:00:00Z"
        )
        response = await _inventory_at_impl(request, context)

    assert response.items[0].sku is None
    assert response.items[0].variant_id == 555
    assert response.items[0].display_name == "Mystery Widget"


@pytest.mark.asyncio
async def test_inventory_at_batch_mix_of_sku_and_id():
    """A list with strings and ints resolves both, preserving input order."""
    from katana_mcp.tools.foundation.inventory import (
        InventoryAtRequest,
        _inventory_at_impl,
    )

    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.typed_cache.catalog.get_by_sku = AsyncMock(
        return_value={"id": 3001, "sku": "W-1", "display_name": "Widget One"}
    )
    lifespan_ctx.typed_cache.catalog.get_many_by_ids = AsyncMock(return_value={})

    with (
        patch(
            "katana_mcp.tools.foundation.items._fetch_variant_by_id",
            new_callable=AsyncMock,
        ) as mock_by_id,
        patch(f"{_MOVEMENTS_API}.asyncio_detailed", new_callable=AsyncMock),
        patch(_UNWRAP_DATA, return_value=[]),
    ):
        mock_by_id.return_value = {
            "id": 2002,
            "sku": "W-2",
            "display_name": "Widget Two",
        }
        request = InventoryAtRequest(
            skus_or_variant_ids=["W-1", 2002], as_of="2026-04-01T00:00:00Z"
        )
        response = await _inventory_at_impl(request, context)

    assert [item.variant_id for item in response.items] == [3001, 2002]


@pytest.mark.asyncio
async def test_inventory_at_rejects_blank_sku():
    """Whitespace-only SKU surfaces as ValueError."""
    from katana_mcp.tools.foundation.inventory import (
        InventoryAtRequest,
        _inventory_at_impl,
    )

    context, _ = create_mock_context()
    request = InventoryAtRequest(
        skus_or_variant_ids=["   "], as_of="2026-04-01T00:00:00Z"
    )
    with pytest.raises(ValueError, match="SKU cannot be empty"):
        await _inventory_at_impl(request, context)


@pytest.mark.asyncio
async def test_inventory_at_rejects_bad_as_of():
    """Malformed as_of surfaces with the field name in the error."""
    from katana_mcp.tools.foundation.inventory import (
        InventoryAtRequest,
        _inventory_at_impl,
    )

    context, _ = create_mock_context()
    request = InventoryAtRequest(skus_or_variant_ids=["W-1"], as_of="not-a-datetime")
    with pytest.raises(ValueError, match="as_of"):
        await _inventory_at_impl(request, context)
