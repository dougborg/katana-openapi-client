"""Tests for order fulfillment MCP tools."""

from datetime import UTC, datetime, timedelta
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from katana_mcp.tools.foundation.orders import (
    FulfillOrderRequest,
    FulfillRowOverride,
    _fulfill_order_impl,
)
from katana_mcp_server.tests.conftest import create_mock_context

from katana_public_api_client.models import (
    ManufacturingOrder,
    ManufacturingOrderStatus,
    SalesOrder,
)
from katana_public_api_client.models.sales_order_status import SalesOrderStatus
from katana_public_api_client.models_pydantic._generated import (
    CachedMaterial,
    CachedProduct,
    CachedVariant,
    InventoryItemType,
)
from katana_public_api_client.utils import APIError

# ============================================================================
# Manufacturing Order Tests
# ============================================================================


@pytest.mark.asyncio
async def test_fulfill_manufacturing_order_preview():
    """Test fulfill_order preview mode for manufacturing order."""
    context, _lifespan_ctx = create_mock_context()

    # Mock ManufacturingOrder
    mock_mo = MagicMock(spec=ManufacturingOrder)
    mock_mo.order_no = "MO-001"
    mock_mo.status = ManufacturingOrderStatus.IN_PROGRESS

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.parsed = mock_mo

    # Mock the get API call
    from katana_public_api_client.api.manufacturing_order import (
        get_manufacturing_order,
    )

    cast(Any, get_manufacturing_order).asyncio_detailed = AsyncMock(
        return_value=mock_response
    )

    request = FulfillOrderRequest(
        order_id=1234, order_type="manufacturing", preview=True
    )
    result = await _fulfill_order_impl(request, context)

    assert result.order_id == 1234
    assert result.order_type == "manufacturing"
    assert result.order_number == "MO-001"
    assert result.status == "IN_PROGRESS"
    assert result.is_preview is True
    assert len(result.inventory_updates) > 0
    assert any("finished goods" in msg.lower() for msg in result.inventory_updates)
    assert "Set preview=false" in result.next_actions[2]


@pytest.mark.asyncio
async def test_fulfill_manufacturing_order_confirm():
    """fulfill_order(manufacturing) apply path: single POST
    /manufacturing_order_productions atomically marks the MO DONE (#790).
    Replaces the prior two-call PATCH chase (#779).
    """
    context, _lifespan_ctx = create_mock_context()

    # Mock ManufacturingOrder for the initial get (pre-production).
    mock_mo = MagicMock(spec=ManufacturingOrder)
    mock_mo.order_no = "MO-002"
    mock_mo.status = ManufacturingOrderStatus.IN_PROGRESS
    mock_mo.variant_id = None
    mock_mo.actual_quantity = None

    mock_get_response = MagicMock(status_code=200, parsed=mock_mo)

    # Mock ManufacturingOrderProduction returned from POST
    # /manufacturing_order_productions.
    from katana_public_api_client.models import ManufacturingOrderProduction

    mock_production = MagicMock(spec=ManufacturingOrderProduction)
    mock_production.id = 9001
    mock_create_response = MagicMock(status_code=200, parsed=mock_production)

    # Mock ManufacturingOrder for the post-production re-fetch (cache-merge
    # contract: a single full-entity fetch at the end).
    mock_done_mo = MagicMock(spec=ManufacturingOrder)
    mock_done_mo.order_no = "MO-002"
    mock_done_mo.status = ManufacturingOrderStatus.DONE
    mock_final_response = MagicMock(status_code=200, parsed=mock_done_mo)

    from katana_public_api_client.api.manufacturing_order import (
        get_manufacturing_order,
    )
    from katana_public_api_client.api.manufacturing_order_production import (
        create_manufacturing_order_production,
    )

    # The pre-mutation get returns the IN_PROGRESS MO; the post-mutation
    # get returns the DONE MO. Use side_effect to sequence them.
    get_mock = AsyncMock(side_effect=[mock_get_response, mock_final_response])
    cast(Any, get_manufacturing_order).asyncio_detailed = get_mock

    create_mock = AsyncMock(return_value=mock_create_response)
    cast(Any, create_manufacturing_order_production).asyncio_detailed = create_mock

    request = FulfillOrderRequest(
        order_id=1234, order_type="manufacturing", preview=False
    )
    result = await _fulfill_order_impl(request, context)

    assert result.order_id == 1234
    assert result.order_type == "manufacturing"
    assert result.order_number == "MO-002"
    assert result.status == "DONE"
    assert result.is_preview is False
    assert len(result.inventory_updates) > 0
    assert "marked" in result.message.lower() or "done" in result.message.lower()

    # The production POST was called exactly once with the expected body.
    create_mock.assert_called_once()
    sent_body = create_mock.call_args.kwargs["body"]
    assert sent_body.manufacturing_order_id == 1234
    assert sent_body.is_final is True
    # actual_quantity was None → default to 1.
    assert sent_body.completed_quantity == 1


@pytest.mark.asyncio
async def test_fulfill_manufacturing_order_already_done():
    """Test fulfill_order when manufacturing order is already DONE."""
    context, _lifespan_ctx = create_mock_context()

    # Mock ManufacturingOrder already DONE
    mock_mo = MagicMock(spec=ManufacturingOrder)
    mock_mo.order_no = "MO-003"
    mock_mo.status = ManufacturingOrderStatus.DONE

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.parsed = mock_mo

    from katana_public_api_client.api.manufacturing_order import (
        get_manufacturing_order,
    )

    cast(Any, get_manufacturing_order).asyncio_detailed = AsyncMock(
        return_value=mock_response
    )

    # Preview mode
    request = FulfillOrderRequest(
        order_id=1234, order_type="manufacturing", preview=True
    )
    result = await _fulfill_order_impl(request, context)

    assert result.status == "DONE"
    assert result.is_preview is True
    assert any("already completed" in w.lower() for w in result.warnings)

    # Confirm mode - should not try to update
    request = FulfillOrderRequest(
        order_id=1234, order_type="manufacturing", preview=False
    )
    result = await _fulfill_order_impl(request, context)

    assert result.status == "DONE"
    assert result.is_preview is False
    assert "already completed" in result.message.lower()


@pytest.mark.asyncio
async def test_fulfill_manufacturing_order_blocked():
    """Test fulfill_order preview when manufacturing order is BLOCKED."""
    context, _lifespan_ctx = create_mock_context()

    # Mock ManufacturingOrder BLOCKED
    mock_mo = MagicMock(spec=ManufacturingOrder)
    mock_mo.order_no = "MO-004"
    mock_mo.status = ManufacturingOrderStatus.BLOCKED

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.parsed = mock_mo

    from katana_public_api_client.api.manufacturing_order import (
        get_manufacturing_order,
    )

    cast(Any, get_manufacturing_order).asyncio_detailed = AsyncMock(
        return_value=mock_response
    )

    request = FulfillOrderRequest(
        order_id=1234, order_type="manufacturing", preview=True
    )
    result = await _fulfill_order_impl(request, context)

    assert result.status == "BLOCKED"
    assert any("blocked" in w.lower() for w in result.warnings)


@pytest.mark.asyncio
async def test_fulfill_manufacturing_order_not_found():
    """Test fulfill_order when manufacturing order not found."""
    context, _lifespan_ctx = create_mock_context()

    # Mock 404 response
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.parsed = None

    from katana_public_api_client.api.manufacturing_order import (
        get_manufacturing_order,
    )

    cast(Any, get_manufacturing_order).asyncio_detailed = AsyncMock(
        return_value=mock_response
    )

    request = FulfillOrderRequest(
        order_id=9999, order_type="manufacturing", preview=True
    )

    with pytest.raises(APIError):
        await _fulfill_order_impl(request, context)


# ============================================================================
# Sales Order Tests
# ============================================================================


def _make_so_row(
    row_id: int,
    variant_id: int,
    quantity: float,
    *,
    linked_manufacturing_order_id: int | None = None,
):
    """Build a SalesOrderRow mock with the fields fulfill_sales_order reads.

    ``linked_manufacturing_order_id`` defaults to None so the inventory-
    ordering guard (#787) stays silent on tests that don't exercise it; set
    it explicitly to wire a linked MO for the guard.
    """
    row = MagicMock()
    row.id = row_id
    row.variant_id = variant_id
    row.quantity = quantity
    row.linked_manufacturing_order_id = linked_manufacturing_order_id
    return row


@pytest.mark.asyncio
async def test_fulfill_sales_order_preview():
    """Preview must list the rows that will ship and not raise."""
    context, _lifespan_ctx = create_mock_context()

    mock_so = MagicMock(spec=SalesOrder)
    mock_so.order_no = "SO-001"
    mock_so.status = SalesOrderStatus.NOT_SHIPPED
    mock_so.sales_order_rows = [
        _make_so_row(1, 100, 2.0),
        _make_so_row(2, 200, 5.0),
    ]

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.parsed = mock_so

    from katana_public_api_client.api.sales_order import get_sales_order

    cast(Any, get_sales_order).asyncio_detailed = AsyncMock(return_value=mock_response)

    request = FulfillOrderRequest(order_id=5678, order_type="sales", preview=True)
    result = await _fulfill_order_impl(request, context)

    assert result.order_id == 5678
    assert result.order_type == "sales"
    assert result.order_number == "SO-001"
    assert result.status == "NOT_SHIPPED"
    assert result.is_preview is True
    # Per-row identity now flows through ``fulfilled_rows`` (the Tier-3
    # DataTable on the card) — the pre-#card-ux ``inventory_updates``
    # text dump duplicated the same data row-for-row, was the source of
    # the user-cited card redundancy, and is now intentionally empty on
    # the SO branch. Cold-cache rows surface variant_id without a
    # display_name; the row entry is still emitted.
    assert result.inventory_updates == []
    assert len(result.fulfilled_rows) == 2
    assert {row.variant_id for row in result.fulfilled_rows} == {100, 200}
    # Last next_action should mention preview=false.
    assert any("preview=false" in a for a in result.next_actions)


@pytest.mark.asyncio
async def test_fulfill_sales_order_preview_lifts_display_name():
    """When the typed cache resolves each row's variant, the inventory-
    update line leads with the canonical Katana-UI display name
    (parent / value1 / value2) — matching every other variant-displaying
    surface. Falls back to the ``variant {id}`` sentinel only on cache
    miss + no parent.
    """
    context, lifespan_ctx = create_mock_context()

    mock_so = MagicMock(spec=SalesOrder)
    mock_so.order_no = "SO-DISPLAY"
    mock_so.status = SalesOrderStatus.NOT_SHIPPED
    mock_so.sales_order_rows = [
        _make_so_row(1, 100, 2.0),
        _make_so_row(2, 200, 5.0),
    ]

    mock_response = MagicMock(status_code=200, parsed=mock_so)
    from katana_public_api_client.api.sales_order import get_sales_order

    cast(Any, get_sales_order).asyncio_detailed = AsyncMock(return_value=mock_response)

    # Seed the typed cache so each variant resolves to a canonical
    # display_name (avoiding the parent-lookup branch — which is exercised
    # by the verify-card test path instead).
    def _mk_cached(vid, sku, display_name):
        m = MagicMock()
        m.id = vid
        m.sku = sku
        m.display_name = display_name
        m.product_id = None
        m.material_id = None
        m.config_attributes = []
        return m

    async def _get_many(model_cls, ids, **_kw):
        # Variant lookup: return per-variant cache rows. Product/Material
        # lookups: empty (variants don't have parents in this fixture, so
        # serial-tracked stays False, which is fine).
        from katana_public_api_client.models_pydantic._generated import CachedVariant

        if model_cls is CachedVariant:
            data = {
                100: _mk_cached(100, "WIDGET-100", "Big Widget / Red"),
                200: _mk_cached(200, "WIDGET-200", "Small Widget / Blue"),
            }
            return {vid: data[vid] for vid in ids if vid in data}
        return {}

    lifespan_ctx.typed_cache.catalog.get_many_by_ids = AsyncMock(side_effect=_get_many)

    request = FulfillOrderRequest(order_id=5678, order_type="sales", preview=True)
    result = await _fulfill_order_impl(request, context)

    # Per-row display_name now lands on ``fulfilled_rows[i].display_name``
    # (the structured data feeding the Tier-3 DataTable on the card) —
    # the legacy ``inventory_updates`` text dump that previously carried
    # the canonical Katana-UI display name was removed because it
    # duplicated the table one row at a time and exposed internal row IDs
    # the operator doesn't care about.
    display_names = [row.display_name for row in result.fulfilled_rows]
    assert "Big Widget / Red" in display_names
    assert "Small Widget / Blue" in display_names


@pytest.mark.asyncio
async def test_fulfill_manufacturing_order_preview_lifts_display_name():
    """The MO fulfillment summary surfaces the finished-good's canonical
    display name in the "will produce X" line, matching the SO sibling.
    Cold-cache fallback returns ``variant {id}`` (default behaviour pinned
    by ``test_fulfill_manufacturing_order_preview``).
    """
    context, lifespan_ctx = create_mock_context()

    mock_mo = MagicMock(spec=ManufacturingOrder)
    mock_mo.order_no = "MO-DISPLAY"
    mock_mo.status = ManufacturingOrderStatus.IN_PROGRESS
    mock_mo.variant_id = 555
    mock_mo.actual_quantity = 2

    mock_response = MagicMock(status_code=200, parsed=mock_mo)
    from katana_public_api_client.api.manufacturing_order import get_manufacturing_order

    cast(Any, get_manufacturing_order).asyncio_detailed = AsyncMock(
        return_value=mock_response
    )

    cached_variant = MagicMock()
    cached_variant.id = 555
    cached_variant.sku = "WIDGET-X1"
    cached_variant.display_name = "Premium Widget / Large / Black"
    cached_variant.product_id = None
    cached_variant.material_id = None
    cached_variant.config_attributes = []

    async def _get_many(model_cls, ids, **_kw):
        from katana_public_api_client.models_pydantic._generated import CachedVariant

        if model_cls is CachedVariant and 555 in set(ids):
            return {555: cached_variant}
        return {}

    lifespan_ctx.typed_cache.catalog.get_many_by_ids = AsyncMock(side_effect=_get_many)

    request = FulfillOrderRequest(
        order_id=9876, order_type="manufacturing", preview=True
    )
    result = await _fulfill_order_impl(request, context)

    assert result.is_preview is True
    # Lead line surfaces the canonical display name (the prior line said
    # only "Manufacturing order completion will update inventory based on BOM",
    # which gave the user no signal what was being made).
    assert any("Premium Widget / Large / Black" in u for u in result.inventory_updates)


@pytest.mark.asyncio
async def test_fulfill_sales_order_confirm_creates_fulfillment():
    """Confirm path now calls POST /sales_order_fulfillments with one row per SO row."""
    context, _lifespan_ctx = create_mock_context()

    mock_so = MagicMock(spec=SalesOrder)
    mock_so.order_no = "SO-002"
    mock_so.status = SalesOrderStatus.NOT_SHIPPED
    mock_so.sales_order_rows = [_make_so_row(1, 100, 2.0)]

    mock_get_response = MagicMock(status_code=200, parsed=mock_so)

    from katana_public_api_client.api.sales_order import get_sales_order
    from katana_public_api_client.api.sales_order_fulfillment import (
        create_sales_order_fulfillment,
    )

    cast(Any, get_sales_order).asyncio_detailed = AsyncMock(
        return_value=mock_get_response
    )

    from katana_public_api_client.models import SalesOrderFulfillment

    fulfillment_obj = MagicMock(spec=SalesOrderFulfillment)
    fulfillment_obj.id = 9999
    mock_create_response = MagicMock(status_code=200, parsed=fulfillment_obj)
    create_mock = AsyncMock(return_value=mock_create_response)
    cast(Any, create_sales_order_fulfillment).asyncio_detailed = create_mock

    request = FulfillOrderRequest(order_id=5678, order_type="sales", preview=False)
    result = await _fulfill_order_impl(request, context)

    assert result.is_preview is False
    assert result.status == "DELIVERED"
    assert "9999" in result.message
    create_mock.assert_called_once()


@pytest.mark.asyncio
async def test_fulfill_sales_order_confirm_refuses_when_no_rows():
    """preview=False against a sales order with no rows must refuse cleanly
    (no-op response with BLOCK warning + Refused message), not raise. Matches
    the defense-in-depth pattern of the other BLOCK guards.
    """
    context, _lifespan_ctx = create_mock_context()

    mock_so = MagicMock(spec=SalesOrder)
    mock_so.order_no = "SO-EMPTY"
    mock_so.status = SalesOrderStatus.NOT_SHIPPED
    mock_so.sales_order_rows = []  # no rows!

    mock_response = MagicMock(status_code=200, parsed=mock_so)

    from katana_public_api_client.api.sales_order import get_sales_order
    from katana_public_api_client.api.sales_order_fulfillment import (
        create_sales_order_fulfillment,
    )

    cast(Any, get_sales_order).asyncio_detailed = AsyncMock(return_value=mock_response)
    create_mock = AsyncMock()
    cast(Any, create_sales_order_fulfillment).asyncio_detailed = create_mock

    request = FulfillOrderRequest(order_id=5678, order_type="sales", preview=False)
    result = await _fulfill_order_impl(request, context)

    assert result.is_preview is False
    block_warnings = [w for w in result.warnings if w.startswith("BLOCK:")]
    assert len(block_warnings) == 1
    assert "no rows" in block_warnings[0].lower()
    assert "Refused" in result.message
    # The fulfillment-create endpoint must NOT have been called.
    create_mock.assert_not_called()


@pytest.mark.asyncio
async def test_fulfill_sales_order_blocks_when_already_delivered():
    """Already-DELIVERED SO should emit a BLOCK warning + refuse confirm."""
    context, _lifespan_ctx = create_mock_context()

    mock_so = MagicMock(spec=SalesOrder)
    mock_so.order_no = "SO-003"
    mock_so.status = SalesOrderStatus.DELIVERED
    mock_so.sales_order_rows = [_make_so_row(1, 100, 2.0)]

    mock_response = MagicMock(status_code=200, parsed=mock_so)

    from katana_public_api_client.api.sales_order import get_sales_order

    cast(Any, get_sales_order).asyncio_detailed = AsyncMock(return_value=mock_response)

    # Preview path: BLOCK warning present.
    request = FulfillOrderRequest(order_id=5678, order_type="sales", preview=True)
    result = await _fulfill_order_impl(request, context)
    assert result.is_preview is True
    block_warnings = [w for w in result.warnings if w.startswith("BLOCK:")]
    assert len(block_warnings) == 1
    assert "DELIVERED" in block_warnings[0]

    # Confirm path: refuses without raising — returns a no-op response.
    request = FulfillOrderRequest(order_id=5678, order_type="sales", preview=False)
    result = await _fulfill_order_impl(request, context)
    assert result.is_preview is False
    assert result.status == "DELIVERED"
    assert "refusing" in result.message.lower()


@pytest.mark.asyncio
async def test_fulfill_sales_order_not_found():
    """Test fulfill_order when sales order not found."""
    context, _lifespan_ctx = create_mock_context()

    # Mock 404 response
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.parsed = None

    from katana_public_api_client.api.sales_order import get_sales_order

    cast(Any, get_sales_order).asyncio_detailed = AsyncMock(return_value=mock_response)

    request = FulfillOrderRequest(order_id=9999, order_type="sales", preview=True)

    with pytest.raises(APIError):
        await _fulfill_order_impl(request, context)


# ============================================================================
# Validation Tests
# ============================================================================


@pytest.mark.asyncio
async def test_fulfill_order_invalid_type():
    """Test fulfill_order with invalid order type (validated by Pydantic)."""
    # This should be caught by Pydantic validation
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        FulfillOrderRequest(order_id=1234, order_type="invalid", preview=True)  # type: ignore


# ============================================================================
# Error Handling Tests
# ============================================================================


@pytest.mark.asyncio
async def test_fulfill_manufacturing_order_api_error():
    """Apply path: a non-2xx from the production POST raises APIError, so
    the fail-loud contract on the upstream production endpoint is preserved.
    """
    context, _lifespan_ctx = create_mock_context()

    # Mock ManufacturingOrder
    mock_mo = MagicMock(spec=ManufacturingOrder)
    mock_mo.order_no = "MO-005"
    mock_mo.status = ManufacturingOrderStatus.IN_PROGRESS
    mock_mo.variant_id = None
    mock_mo.actual_quantity = None

    mock_get_response = MagicMock(status_code=200, parsed=mock_mo)

    # Production POST returns 500 — no parsed payload → unwrap_as raises.
    mock_create_response = MagicMock(status_code=500, parsed=None)

    from katana_public_api_client.api.manufacturing_order import (
        get_manufacturing_order,
    )
    from katana_public_api_client.api.manufacturing_order_production import (
        create_manufacturing_order_production,
    )

    cast(Any, get_manufacturing_order).asyncio_detailed = AsyncMock(
        return_value=mock_get_response
    )
    cast(Any, create_manufacturing_order_production).asyncio_detailed = AsyncMock(
        return_value=mock_create_response
    )

    request = FulfillOrderRequest(
        order_id=1234, order_type="manufacturing", preview=False
    )

    with pytest.raises(APIError):
        await _fulfill_order_impl(request, context)


# NOTE: ``test_fulfill_sales_order_api_error`` was removed — the tool no
# longer reaches the ``POST /sales_order_fulfillments`` API call (it raises
# ``NotImplementedError`` early; see
# ``test_fulfill_sales_order_confirm_not_implemented``). Once the tool is
# extended to send the live-required ``sales_order_fulfillment_rows``,
# restore an API-error test that exercises the row-aware path.


# ============================================================================
# Sales Order — Serial-Tracked Variant Tests (#547)
# ============================================================================


def _wire_non_serial_tracked_cache(lifespan_ctx, *, variant_id: int, sku: str) -> None:
    """Configure the cache so a row's variant resolves as non-serial-tracked.

    Prevents test ordering from accidentally routing variant lookups through
    leftover ``get_variant.asyncio_detailed`` mocks (which earlier tests in
    the file set to return a serial-tracked product) and surfacing a spurious
    BLOCK warning. Use whenever a fresh-context test references a variant ID
    that another test in the file has already wired into the cache.
    """
    parent_id = 9000 + variant_id
    variant_row = CachedVariant(id=variant_id, sku=sku, product_id=parent_id)
    parent_row = CachedProduct(
        id=parent_id,
        name="Parent",
        type=InventoryItemType.product,
        serial_tracked=False,
    )

    async def _get_many(cls, ids, **_kw):
        ids = list(ids or [])
        if cls is CachedVariant and variant_id in ids:
            return {variant_id: variant_row}
        if cls is CachedProduct and parent_id in ids:
            return {parent_id: parent_row}
        return {}

    lifespan_ctx.typed_cache.catalog.get_many_by_ids = AsyncMock(side_effect=_get_many)


def _wire_serial_tracked_cache(
    lifespan_ctx, *, variant_id: int, sku: str, parent_kind: str = "product"
) -> None:
    """Configure the mock cache so a row's variant resolves as serial-tracked.

    ``parent_kind`` selects whether the variant is parented to a product or a
    material — both surface ``serial_tracked`` on the parent.
    """
    parent_id = 9000 + variant_id
    variant_kwargs: dict[str, Any] = {
        "id": variant_id,
        "sku": sku,
    }
    variant_kwargs[f"{parent_kind}_id"] = parent_id
    variant_row = CachedVariant(**variant_kwargs)
    parent_cls = CachedProduct if parent_kind == "product" else CachedMaterial
    parent_kwargs: dict[str, Any] = {
        "id": parent_id,
        "name": "Parent",
        "type": parent_kind,
        "serial_tracked": True,
    }
    parent_row = parent_cls(**parent_kwargs)

    async def _get_many(cls, ids, **_kw):
        ids = list(ids or [])
        if cls is CachedVariant and variant_id in ids:
            return {variant_id: variant_row}
        if cls is CachedProduct and parent_kind == "product":
            return {parent_id: parent_row} if parent_id in ids else {}
        if cls is CachedMaterial and parent_kind == "material":
            return {parent_id: parent_row} if parent_id in ids else {}
        return {}

    lifespan_ctx.typed_cache.catalog.get_many_by_ids = AsyncMock(side_effect=_get_many)


@pytest.mark.asyncio
async def test_fulfill_sales_order_preview_blocks_serial_tracked_without_override():
    """Serial-tracked variant + no rows override → BLOCK warning naming the SKU."""
    context, lifespan_ctx = create_mock_context()
    _wire_serial_tracked_cache(lifespan_ctx, variant_id=100, sku="WIDGET-V2")

    mock_so = MagicMock(spec=SalesOrder)
    mock_so.order_no = "SO-SN-1"
    mock_so.status = SalesOrderStatus.NOT_SHIPPED
    mock_so.sales_order_rows = [_make_so_row(1, 100, 1.0)]

    mock_response = MagicMock(status_code=200, parsed=mock_so)
    from katana_public_api_client.api.sales_order import get_sales_order

    cast(Any, get_sales_order).asyncio_detailed = AsyncMock(return_value=mock_response)

    request = FulfillOrderRequest(order_id=42, order_type="sales", preview=True)
    result = await _fulfill_order_impl(request, context)

    block_warnings = [w for w in result.warnings if w.startswith("BLOCK:")]
    assert len(block_warnings) == 1
    assert "serial-tracked" in block_warnings[0]
    assert "WIDGET-V2" in block_warnings[0]
    # The block carries the MO-linked transfer caveat (Bug 7).
    # _build_row_override_warnings can't see linked_manufacturing_order_id, so
    # the caveat is stated conditionally in every serial-tracked block rather
    # than gated on linkage; this asserts the caveat text (the 422 wording +
    # the UI fallback) is present in the warning.
    assert "already been assigned" in block_warnings[0]
    assert "Deliver all" in block_warnings[0]
    assert "Resolve the issue" in result.next_actions[0]


@pytest.mark.asyncio
async def test_fulfill_sales_order_preview_accepts_serial_override():
    """Serial-tracked variant + matching override → no BLOCK warning, serials in preview."""
    context, lifespan_ctx = create_mock_context()
    _wire_serial_tracked_cache(lifespan_ctx, variant_id=100, sku="WIDGET-V2")

    mock_so = MagicMock(spec=SalesOrder)
    mock_so.order_no = "SO-SN-2"
    mock_so.status = SalesOrderStatus.NOT_SHIPPED
    mock_so.sales_order_rows = [_make_so_row(1, 100, 1.0)]

    mock_response = MagicMock(status_code=200, parsed=mock_so)
    from katana_public_api_client.api.sales_order import get_sales_order

    cast(Any, get_sales_order).asyncio_detailed = AsyncMock(return_value=mock_response)

    request = FulfillOrderRequest(
        order_id=42,
        order_type="sales",
        preview=True,
        rows=[FulfillRowOverride(sales_order_row_id=1, serial_numbers=[501])],
    )
    result = await _fulfill_order_impl(request, context)

    assert not [w for w in result.warnings if w.startswith("BLOCK:")]
    # Per-row serial overrides now flow through ``fulfilled_rows[i].serial_numbers``
    # (the structured Tier-3 payload that drives the DataTable's Serials
    # column). Pre-#card-ux the serial overrides were dumped into
    # ``inventory_updates`` as ``"with serials [501]"`` text — gone with
    # the rest of the redundant text dump.
    serials_by_row = {row.row_id: row.serial_numbers for row in result.fulfilled_rows}
    assert serials_by_row.get(1) == [501]


@pytest.mark.asyncio
async def test_fulfill_sales_order_preview_surfaces_customer_and_addresses():
    """The fulfill card needs Customer name + Shipping/Billing addresses
    to answer the operator's question "who is this for and where does
    it go?" (#card-ux). The impl resolves the customer name via the
    typed cache and fetches addresses from the ``/sales_order_addresses``
    sub-resource (raw ``GET /sales_orders/{id}`` does NOT inline them) —
    with billing deduped against shipping when they're equivalent."""
    from katana_public_api_client.models import SalesOrderAddress
    from katana_public_api_client.models.address_entity_type import AddressEntityType
    from katana_public_api_client.models_pydantic._generated import CachedCustomer

    context, lifespan_ctx = create_mock_context()

    # Address rows come from a SEPARATE /sales_order_addresses fetch
    # (review item #3) — the raw GET /sales_orders/{id} response does not
    # inline addresses. Mock the sub-resource endpoint so the production
    # flow that _fulfill_sales_order actually exercises is covered.
    ship_addr = MagicMock(spec=SalesOrderAddress)
    ship_addr.entity_type = AddressEntityType.SHIPPING
    ship_addr.to_dict = lambda: {
        "entity_type": "shipping",
        "first_name": "Sarah",
        "last_name": "Johnson",
        "company": "Acme Bikes Inc.",
        "line_1": "123 Main Street",
        "city": "Portland",
        "state": "OR",
        "zip": "97201",
        "country": "US",
    }
    bill_addr = MagicMock(spec=SalesOrderAddress)
    bill_addr.entity_type = AddressEntityType.BILLING
    bill_addr.to_dict = lambda: {
        "entity_type": "billing",
        "first_name": "Accounts",
        "last_name": "Payable",
        "company": "Acme Bikes Inc.",
        "line_1": "999 Finance Ave",
        "city": "Beaverton",
        "state": "OR",
        "zip": "97005",
        "country": "US",
    }

    mock_so = MagicMock(spec=SalesOrder)
    mock_so.order_no = "SO-ADDR"
    mock_so.status = SalesOrderStatus.NOT_SHIPPED
    mock_so.sales_order_rows = [_make_so_row(1, 100, 1.0)]
    mock_so.customer_id = 1500

    mock_response = MagicMock(status_code=200, parsed=mock_so)
    from katana_public_api_client.api.sales_order import get_sales_order
    from katana_public_api_client.api.sales_order_address import (
        get_all_sales_order_addresses,
    )

    cast(Any, get_sales_order).asyncio_detailed = AsyncMock(return_value=mock_response)

    # /sales_order_addresses returns a list-response envelope; unwrap_data
    # expects ``.data`` on the parsed body.
    mock_addresses_body = MagicMock()
    mock_addresses_body.data = [ship_addr, bill_addr]
    mock_addresses_response = MagicMock(status_code=200, parsed=mock_addresses_body)
    cast(Any, get_all_sales_order_addresses).asyncio_detailed = AsyncMock(
        return_value=mock_addresses_response
    )

    cached_customer = CachedCustomer(
        id=1500,
        name="Acme Bikes Inc.",
        email="orders@acmebikes.example",
    )

    async def _get_many(cls, ids, **_kw):
        if cls is CachedCustomer and 1500 in set(ids):
            return {1500: cached_customer}
        return {}

    async def _get_by_id(cls, entity_id, **_kw):
        # ``resolve_entity_name`` reads via ``get_by_id`` (not
        # ``get_many_by_ids``); the rest of the SO fulfill impl uses
        # ``get_many_by_ids`` for batched variant lookups. Wire both.
        if cls is CachedCustomer and entity_id == 1500:
            return cached_customer
        return None

    lifespan_ctx.typed_cache.catalog.get_many_by_ids = AsyncMock(side_effect=_get_many)
    lifespan_ctx.typed_cache.catalog.get_by_id = AsyncMock(side_effect=_get_by_id)

    request = FulfillOrderRequest(
        order_id=99,
        order_type="sales",
        preview=True,
        completed_at=datetime(2026, 5, 8, 23, 14, tzinfo=UTC),
    )
    result = await _fulfill_order_impl(request, context)

    assert result.customer_id == 1500
    assert result.customer_name == "Acme Bikes Inc."
    assert result.shipping_address is not None
    assert result.shipping_address["city"] == "Portland"
    # Billing differs from shipping → both blocks carry through.
    assert result.billing_address is not None
    assert result.billing_address["city"] == "Beaverton"
    # picked_date is promoted to its own response field for the Metric.
    assert result.picked_date == "2026-05-08T23:14:00+00:00"


@pytest.mark.asyncio
async def test_fulfill_sales_order_preview_dedups_billing_address():
    """When shipping and billing describe the same place, the impl
    returns ``billing_address=None`` so the card doesn't render two
    identical blocks. Pinned with ``_addresses_are_equivalent`` semantics
    (every user-visible field matches; entity_type / timestamps are
    excluded from comparison)."""
    from katana_public_api_client.models import SalesOrderAddress
    from katana_public_api_client.models.address_entity_type import AddressEntityType

    context, _lifespan_ctx = create_mock_context()

    shared = {
        "first_name": "Sarah",
        "last_name": "Johnson",
        "company": "Acme Bikes Inc.",
        "line_1": "123 Main Street",
        "city": "Portland",
        "state": "OR",
        "zip": "97201",
        "country": "US",
    }
    ship_addr = MagicMock(spec=SalesOrderAddress)
    ship_addr.entity_type = AddressEntityType.SHIPPING
    ship_addr.to_dict = lambda: {"entity_type": "shipping", **shared}
    bill_addr = MagicMock(spec=SalesOrderAddress)
    bill_addr.entity_type = AddressEntityType.BILLING
    bill_addr.to_dict = lambda: {"entity_type": "billing", **shared}

    mock_so = MagicMock(spec=SalesOrder)
    mock_so.order_no = "SO-DEDUP"
    mock_so.status = SalesOrderStatus.NOT_SHIPPED
    mock_so.sales_order_rows = [_make_so_row(1, 100, 1.0)]
    mock_so.customer_id = None

    mock_response = MagicMock(status_code=200, parsed=mock_so)
    from katana_public_api_client.api.sales_order import get_sales_order
    from katana_public_api_client.api.sales_order_address import (
        get_all_sales_order_addresses,
    )

    cast(Any, get_sales_order).asyncio_detailed = AsyncMock(return_value=mock_response)
    # /sales_order_addresses returns ship + bill via the sub-resource.
    mock_addresses_body = MagicMock()
    mock_addresses_body.data = [ship_addr, bill_addr]
    cast(Any, get_all_sales_order_addresses).asyncio_detailed = AsyncMock(
        return_value=MagicMock(status_code=200, parsed=mock_addresses_body)
    )

    request = FulfillOrderRequest(order_id=100, order_type="sales", preview=True)
    result = await _fulfill_order_impl(request, context)

    assert result.shipping_address is not None
    assert result.billing_address is None, (
        "Billing matches shipping field-for-field — impl must return "
        "billing_address=None so the card doesn't render a duplicate block."
    )


@pytest.mark.asyncio
async def test_fulfill_sales_order_preview_handles_addresses_endpoint_empty():
    """When /sales_order_addresses returns no rows for the SO (caller
    skipped the addresses fetch, transient endpoint hiccup, or a real
    SO without addresses), the impl returns shipping_address=None /
    billing_address=None without raising. Pinned for review item #3 —
    the production failure mode the original MagicMock-on-so.addresses
    test failed to cover."""
    context, _lifespan_ctx = create_mock_context()

    mock_so = MagicMock(spec=SalesOrder)
    mock_so.order_no = "SO-NOADDR"
    mock_so.status = SalesOrderStatus.NOT_SHIPPED
    mock_so.sales_order_rows = [_make_so_row(1, 100, 1.0)]
    mock_so.customer_id = None

    mock_response = MagicMock(status_code=200, parsed=mock_so)
    from katana_public_api_client.api.sales_order import get_sales_order
    from katana_public_api_client.api.sales_order_address import (
        get_all_sales_order_addresses,
    )

    cast(Any, get_sales_order).asyncio_detailed = AsyncMock(return_value=mock_response)

    # /sales_order_addresses returns an empty data list.
    empty_addresses_body = MagicMock()
    empty_addresses_body.data = []
    cast(Any, get_all_sales_order_addresses).asyncio_detailed = AsyncMock(
        return_value=MagicMock(status_code=200, parsed=empty_addresses_body)
    )

    request = FulfillOrderRequest(order_id=101, order_type="sales", preview=True)
    result = await _fulfill_order_impl(request, context)

    assert result.shipping_address is None
    assert result.billing_address is None
    # No exception, no BLOCK warning — the card simply elides the Tier-3
    # address block when no addresses come back.
    assert not [w for w in result.warnings if w.startswith("BLOCK:")]


@pytest.mark.asyncio
async def test_fulfill_sales_order_apply_passes_serials_to_api():
    """Apply with override → POST body row carries serial_numbers."""
    context, lifespan_ctx = create_mock_context()
    _wire_serial_tracked_cache(lifespan_ctx, variant_id=100, sku="WIDGET-V2")

    mock_so = MagicMock(spec=SalesOrder)
    mock_so.order_no = "SO-SN-3"
    mock_so.status = SalesOrderStatus.NOT_SHIPPED
    mock_so.sales_order_rows = [_make_so_row(1, 100, 1.0)]

    mock_get_response = MagicMock(status_code=200, parsed=mock_so)

    from katana_public_api_client.api.sales_order import get_sales_order
    from katana_public_api_client.api.sales_order_fulfillment import (
        create_sales_order_fulfillment,
    )
    from katana_public_api_client.models import SalesOrderFulfillment

    cast(Any, get_sales_order).asyncio_detailed = AsyncMock(
        return_value=mock_get_response
    )
    fulfillment_obj = MagicMock(spec=SalesOrderFulfillment)
    fulfillment_obj.id = 7777
    mock_create_response = MagicMock(status_code=200, parsed=fulfillment_obj)
    create_mock = AsyncMock(return_value=mock_create_response)
    cast(Any, create_sales_order_fulfillment).asyncio_detailed = create_mock

    request = FulfillOrderRequest(
        order_id=42,
        order_type="sales",
        preview=False,
        rows=[FulfillRowOverride(sales_order_row_id=1, serial_numbers=[501])],
    )
    result = await _fulfill_order_impl(request, context)

    assert result.is_preview is False
    assert result.status == "DELIVERED"
    create_mock.assert_called_once()
    assert create_mock.call_args is not None
    sent_body = create_mock.call_args.kwargs["body"]
    sent_rows = sent_body.sales_order_fulfillment_rows
    assert len(sent_rows) == 1
    assert sent_rows[0].sales_order_row_id == 1
    assert sent_rows[0].serial_numbers == [501]


@pytest.mark.asyncio
async def test_fulfill_sales_order_preview_accepts_traceability_serials():
    """Serials supplied via ``traceability`` satisfy the serial-tracked guard —
    no BLOCK even without a flat ``serial_numbers`` override."""
    from katana_mcp.tools.foundation._traceability import TraceabilityInput

    context, lifespan_ctx = create_mock_context()
    _wire_serial_tracked_cache(lifespan_ctx, variant_id=100, sku="WIDGET-V2")

    mock_so = MagicMock(spec=SalesOrder)
    mock_so.order_no = "SO-SN-TR"
    mock_so.status = SalesOrderStatus.NOT_SHIPPED
    mock_so.sales_order_rows = [_make_so_row(1, 100, 1.0)]

    mock_response = MagicMock(status_code=200, parsed=mock_so)
    from katana_public_api_client.api.sales_order import get_sales_order

    cast(Any, get_sales_order).asyncio_detailed = AsyncMock(return_value=mock_response)

    request = FulfillOrderRequest(
        order_id=42,
        order_type="sales",
        preview=True,
        rows=[
            FulfillRowOverride(
                sales_order_row_id=1,
                traceability=[TraceabilityInput(serial_number_id=501, quantity=1)],
            )
        ],
    )
    result = await _fulfill_order_impl(request, context)

    assert not [w for w in result.warnings if w.startswith("BLOCK:")]


@pytest.mark.asyncio
async def test_fulfill_sales_order_apply_passes_traceability_to_api():
    """Apply with a traceability override → POST body row carries ``traceability``."""
    from katana_mcp.tools.foundation._traceability import TraceabilityInput

    context, lifespan_ctx = create_mock_context()
    _wire_serial_tracked_cache(lifespan_ctx, variant_id=100, sku="WIDGET-V2")

    mock_so = MagicMock(spec=SalesOrder)
    mock_so.order_no = "SO-SN-TR2"
    mock_so.status = SalesOrderStatus.NOT_SHIPPED
    mock_so.sales_order_rows = [_make_so_row(1, 100, 1.0)]
    mock_get_response = MagicMock(status_code=200, parsed=mock_so)

    from katana_public_api_client.api.sales_order import get_sales_order
    from katana_public_api_client.api.sales_order_fulfillment import (
        create_sales_order_fulfillment,
    )
    from katana_public_api_client.models import SalesOrderFulfillment

    cast(Any, get_sales_order).asyncio_detailed = AsyncMock(
        return_value=mock_get_response
    )
    fulfillment_obj = MagicMock(spec=SalesOrderFulfillment)
    fulfillment_obj.id = 7778
    create_mock = AsyncMock(
        return_value=MagicMock(status_code=200, parsed=fulfillment_obj)
    )
    cast(Any, create_sales_order_fulfillment).asyncio_detailed = create_mock

    request = FulfillOrderRequest(
        order_id=42,
        order_type="sales",
        preview=False,
        rows=[
            FulfillRowOverride(
                sales_order_row_id=1,
                traceability=[TraceabilityInput(serial_number_id=501, quantity=1)],
            )
        ],
    )
    await _fulfill_order_impl(request, context)

    assert create_mock.call_args is not None
    sent_rows = create_mock.call_args.kwargs["body"].sales_order_fulfillment_rows
    row_dict = sent_rows[0].to_dict()
    assert row_dict["traceability"] == [{"serial_number_id": 501, "quantity": 1}]


@pytest.mark.asyncio
async def test_fulfill_sales_order_explicit_empty_traceability_reaches_wire():
    """An explicitly-supplied empty ``traceability`` list is passed through as
    ``[]`` (distinct from omission), consistent with the helper contract.

    Uses a non-serial-tracked row so the empty list isn't intercepted by the
    serial-tracked guard — the point here is purely the None-vs-[] passthrough.
    """
    context, _lifespan_ctx = create_mock_context()

    mock_so = MagicMock(spec=SalesOrder)
    mock_so.order_no = "SO-SN-TR3"
    mock_so.status = SalesOrderStatus.NOT_SHIPPED
    mock_so.sales_order_rows = [_make_so_row(1, 100, 1.0)]

    from katana_public_api_client.api.sales_order import get_sales_order
    from katana_public_api_client.api.sales_order_fulfillment import (
        create_sales_order_fulfillment,
    )
    from katana_public_api_client.models import SalesOrderFulfillment

    cast(Any, get_sales_order).asyncio_detailed = AsyncMock(
        return_value=MagicMock(status_code=200, parsed=mock_so)
    )
    fulfillment_obj = MagicMock(spec=SalesOrderFulfillment)
    fulfillment_obj.id = 7779
    create_mock = AsyncMock(
        return_value=MagicMock(status_code=200, parsed=fulfillment_obj)
    )
    cast(Any, create_sales_order_fulfillment).asyncio_detailed = create_mock

    request = FulfillOrderRequest(
        order_id=42,
        order_type="sales",
        preview=False,
        rows=[FulfillRowOverride(sales_order_row_id=1, traceability=[])],
    )
    await _fulfill_order_impl(request, context)

    assert create_mock.call_args is not None
    sent_rows = create_mock.call_args.kwargs["body"].sales_order_fulfillment_rows
    assert sent_rows[0].to_dict()["traceability"] == []


@pytest.mark.asyncio
async def test_fulfill_sales_order_apply_refuses_serial_tracked_without_override():
    """Direct apply (preview=False) without override → refusal, no API call."""
    context, lifespan_ctx = create_mock_context()
    _wire_serial_tracked_cache(lifespan_ctx, variant_id=100, sku="WIDGET-V2")

    mock_so = MagicMock(spec=SalesOrder)
    mock_so.order_no = "SO-SN-4"
    mock_so.status = SalesOrderStatus.NOT_SHIPPED
    mock_so.sales_order_rows = [_make_so_row(1, 100, 1.0)]

    mock_response = MagicMock(status_code=200, parsed=mock_so)

    from katana_public_api_client.api.sales_order import get_sales_order
    from katana_public_api_client.api.sales_order_fulfillment import (
        create_sales_order_fulfillment,
    )

    cast(Any, get_sales_order).asyncio_detailed = AsyncMock(return_value=mock_response)
    create_mock = AsyncMock()
    cast(Any, create_sales_order_fulfillment).asyncio_detailed = create_mock

    request = FulfillOrderRequest(order_id=42, order_type="sales", preview=False)
    result = await _fulfill_order_impl(request, context)

    assert result.is_preview is False
    block_warnings = [w for w in result.warnings if w.startswith("BLOCK:")]
    assert any("serial-tracked" in w for w in block_warnings)
    assert "Refused" in result.message
    create_mock.assert_not_called()


@pytest.mark.asyncio
async def test_fulfill_sales_order_blocks_quantity_serials_mismatch():
    """len(serial_numbers) != quantity → BLOCK warning."""
    context, lifespan_ctx = create_mock_context()
    _wire_serial_tracked_cache(lifespan_ctx, variant_id=100, sku="WIDGET-V2")

    mock_so = MagicMock(spec=SalesOrder)
    mock_so.order_no = "SO-SN-5"
    mock_so.status = SalesOrderStatus.NOT_SHIPPED
    # qty=2 but only 1 serial provided.
    mock_so.sales_order_rows = [_make_so_row(1, 100, 2.0)]

    mock_response = MagicMock(status_code=200, parsed=mock_so)
    from katana_public_api_client.api.sales_order import get_sales_order

    cast(Any, get_sales_order).asyncio_detailed = AsyncMock(return_value=mock_response)

    request = FulfillOrderRequest(
        order_id=42,
        order_type="sales",
        preview=True,
        rows=[FulfillRowOverride(sales_order_row_id=1, serial_numbers=[501])],
    )
    result = await _fulfill_order_impl(request, context)

    block_warnings = [w for w in result.warnings if w.startswith("BLOCK:")]
    assert any("count (1) must equal quantity (2" in w for w in block_warnings)


@pytest.mark.asyncio
async def test_fulfill_sales_order_blocks_unknown_row_override():
    """Override referencing a row ID not on the SO → BLOCK warning."""
    context, _lifespan_ctx = create_mock_context()

    mock_so = MagicMock(spec=SalesOrder)
    mock_so.order_no = "SO-SN-6"
    mock_so.status = SalesOrderStatus.NOT_SHIPPED
    mock_so.sales_order_rows = [_make_so_row(1, 100, 1.0)]

    mock_response = MagicMock(status_code=200, parsed=mock_so)
    from katana_public_api_client.api.sales_order import get_sales_order

    cast(Any, get_sales_order).asyncio_detailed = AsyncMock(return_value=mock_response)

    request = FulfillOrderRequest(
        order_id=42,
        order_type="sales",
        preview=True,
        rows=[FulfillRowOverride(sales_order_row_id=999, serial_numbers=[501])],
    )
    result = await _fulfill_order_impl(request, context)

    block_warnings = [w for w in result.warnings if w.startswith("BLOCK:")]
    assert any("unknown sales_order_row_id=999" in w for w in block_warnings)


@pytest.mark.asyncio
async def test_fulfill_sales_order_serial_tracked_detection_falls_back_to_api():
    """Cold / stale cache: variant + product missing from cache.

    Without the API fallback, a cold cache silently classifies the row as
    not-serial-tracked, so the BLOCK warning never fires and the user hits
    the original Katana 422 on apply. With the fallback, the per-ID API
    fetch resolves the variant + product and the BLOCK warning fires.
    """
    context, _lifespan_ctx = create_mock_context()
    # Default mock cache returns {} for every get_many_by_ids — simulating
    # a cold cache. We do NOT call _wire_serial_tracked_cache here.

    mock_so = MagicMock(spec=SalesOrder)
    mock_so.order_no = "SO-SN-COLD"
    mock_so.status = SalesOrderStatus.NOT_SHIPPED
    mock_so.sales_order_rows = [_make_so_row(1, 100, 1.0)]

    mock_get_so_response = MagicMock(status_code=200, parsed=mock_so)

    # API fallback: get_variant returns a variant pointing at product 9100;
    # get_product returns a serial-tracked product. Phase D's
    # ``_fetch_missing_from_api`` stores the attrs object directly
    # (callers use ``getattr`` to read fields uniformly across cache hits
    # and API-fallback rows), so we set attributes on the mocks instead
    # of the legacy ``to_dict`` shim.
    variant_obj = MagicMock()
    variant_obj.id = 100
    variant_obj.sku = "WIDGET-V2"
    variant_obj.product_id = 9100
    variant_obj.material_id = None
    mock_get_variant_response = MagicMock(status_code=200, parsed=variant_obj)

    product_obj = MagicMock()
    product_obj.id = 9100
    product_obj.serial_tracked = True
    mock_get_product_response = MagicMock(status_code=200, parsed=product_obj)

    from katana_public_api_client.api.product import get_product
    from katana_public_api_client.api.sales_order import get_sales_order
    from katana_public_api_client.api.variant import get_variant

    cast(Any, get_sales_order).asyncio_detailed = AsyncMock(
        return_value=mock_get_so_response
    )
    cast(Any, get_variant).asyncio_detailed = AsyncMock(
        return_value=mock_get_variant_response
    )
    cast(Any, get_product).asyncio_detailed = AsyncMock(
        return_value=mock_get_product_response
    )

    request = FulfillOrderRequest(order_id=42, order_type="sales", preview=True)
    result = await _fulfill_order_impl(request, context)

    block_warnings = [w for w in result.warnings if w.startswith("BLOCK:")]
    assert any("serial-tracked" in w and "WIDGET-V2" in w for w in block_warnings)
    # Verify both API endpoints were hit.
    cast(Any, get_variant.asyncio_detailed).assert_called_once()
    cast(Any, get_product.asyncio_detailed).assert_called_once()


@pytest.mark.asyncio
async def test_fulfill_sales_order_blocks_duplicate_row_override():
    """Two overrides for the same sales_order_row_id → BLOCK warning.

    Without this check the dict-comp would silently keep only the last
    override (last-key-wins), hiding conflicting input from the caller.
    """
    context, lifespan_ctx = create_mock_context()
    _wire_serial_tracked_cache(lifespan_ctx, variant_id=100, sku="WIDGET-V2")

    mock_so = MagicMock(spec=SalesOrder)
    mock_so.order_no = "SO-SN-DUP"
    mock_so.status = SalesOrderStatus.NOT_SHIPPED
    mock_so.sales_order_rows = [_make_so_row(1, 100, 2.0)]

    mock_response = MagicMock(status_code=200, parsed=mock_so)
    from katana_public_api_client.api.sales_order import get_sales_order

    cast(Any, get_sales_order).asyncio_detailed = AsyncMock(return_value=mock_response)

    request = FulfillOrderRequest(
        order_id=42,
        order_type="sales",
        preview=True,
        rows=[
            FulfillRowOverride(sales_order_row_id=1, serial_numbers=[501, 502]),
            FulfillRowOverride(sales_order_row_id=1, serial_numbers=[601, 602]),
        ],
    )
    result = await _fulfill_order_impl(request, context)

    block_warnings = [w for w in result.warnings if w.startswith("BLOCK:")]
    assert any(
        "Multiple overrides for the same sales_order_row_id ([1])" in w
        for w in block_warnings
    )


@pytest.mark.asyncio
async def test_fulfill_sales_order_blocks_serial_tracked_non_integer_quantity():
    """Serial-tracked variant with non-integer qty → BLOCK warning.

    Previously the code used ``len(serials) != int(qty)``, which silently
    truncated 1.5 → 1 and could mask genuine mismatches.
    """
    context, lifespan_ctx = create_mock_context()
    _wire_serial_tracked_cache(lifespan_ctx, variant_id=100, sku="WIDGET-V2")

    mock_so = MagicMock(spec=SalesOrder)
    mock_so.order_no = "SO-SN-FRAC"
    mock_so.status = SalesOrderStatus.NOT_SHIPPED
    mock_so.sales_order_rows = [_make_so_row(1, 100, 1.5)]

    mock_response = MagicMock(status_code=200, parsed=mock_so)
    from katana_public_api_client.api.sales_order import get_sales_order

    cast(Any, get_sales_order).asyncio_detailed = AsyncMock(return_value=mock_response)

    request = FulfillOrderRequest(
        order_id=42,
        order_type="sales",
        preview=True,
        rows=[FulfillRowOverride(sales_order_row_id=1, serial_numbers=[501])],
    )
    result = await _fulfill_order_impl(request, context)

    block_warnings = [w for w in result.warnings if w.startswith("BLOCK:")]
    assert any(
        "serial-tracked but quantity (1.5) is not a whole number" in w
        for w in block_warnings
    )


@pytest.mark.asyncio
async def test_fulfill_sales_order_non_serial_tracked_no_change():
    """Non-serial-tracked variant + no rows override → behaves as before
    (no BLOCK warning, apply path passes UNSET for serial_numbers).

    Wires the cache so the variant resolves to a non-serial-tracked product
    — keeps detection from spuriously firing and confirms the API fallback
    isn't required in the warm-cache path.
    """
    context, lifespan_ctx = create_mock_context()

    async def _get_many(cls, ids, **_kw):
        ids = list(ids or [])
        if cls is CachedVariant and 100 in ids:
            return {100: CachedVariant(id=100, sku="PLAIN-WIDGET", product_id=9100)}
        if cls is CachedProduct and 9100 in ids:
            return {
                9100: CachedProduct(
                    id=9100,
                    name="Widget",
                    type=InventoryItemType.product,
                    serial_tracked=False,
                )
            }
        return {}

    lifespan_ctx.typed_cache.catalog.get_many_by_ids = AsyncMock(side_effect=_get_many)

    mock_so = MagicMock(spec=SalesOrder)
    mock_so.order_no = "SO-SN-7"
    mock_so.status = SalesOrderStatus.NOT_SHIPPED
    mock_so.sales_order_rows = [_make_so_row(1, 100, 2.0)]

    mock_get_response = MagicMock(status_code=200, parsed=mock_so)

    from katana_public_api_client.api.sales_order import get_sales_order
    from katana_public_api_client.api.sales_order_fulfillment import (
        create_sales_order_fulfillment,
    )
    from katana_public_api_client.models import SalesOrderFulfillment

    cast(Any, get_sales_order).asyncio_detailed = AsyncMock(
        return_value=mock_get_response
    )
    fulfillment_obj = MagicMock(spec=SalesOrderFulfillment)
    fulfillment_obj.id = 8888
    mock_create_response = MagicMock(status_code=200, parsed=fulfillment_obj)
    create_mock = AsyncMock(return_value=mock_create_response)
    cast(Any, create_sales_order_fulfillment).asyncio_detailed = create_mock

    request = FulfillOrderRequest(order_id=42, order_type="sales", preview=False)
    result = await _fulfill_order_impl(request, context)

    assert result.status == "DELIVERED"
    assert not [w for w in result.warnings if w.startswith("BLOCK:")]
    sent_body = create_mock.call_args.kwargs["body"]
    sent_rows = sent_body.sales_order_fulfillment_rows
    # serial_numbers should be UNSET (omitted from wire), not an empty list.
    from katana_public_api_client.client_types import UNSET

    assert sent_rows[0].serial_numbers is UNSET


# ============================================================================
# Manufacturing Order — Serial-Tracked Variant Tests (#586)
# ============================================================================


def _make_serial_tracked_mo(
    *,
    order_no: str,
    variant_id: int = 100,
    actual_quantity: float = 1.0,
    sales_order_id: int | None = None,
):
    """Build a serial-tracked ManufacturingOrder mock with the fields the tool reads.

    The MO path reads ``order_no``, ``status``, ``variant_id``,
    ``actual_quantity``, and ``sales_order_id`` (inventory-ordering guard,
    #787) — set them explicitly rather than letting MagicMock autogen child
    mocks (which interact poorly with ``unwrap_unset`` + cache lookups by
    ID, and trip type-mismatch errors on the guard's datetime comparisons).
    """
    mock_mo = MagicMock(spec=ManufacturingOrder)
    mock_mo.order_no = order_no
    mock_mo.status = ManufacturingOrderStatus.IN_PROGRESS
    mock_mo.variant_id = variant_id
    mock_mo.actual_quantity = actual_quantity
    mock_mo.sales_order_id = sales_order_id
    return mock_mo


@pytest.mark.asyncio
async def test_fulfill_manufacturing_order_preview_blocks_serial_tracked_without_serials():
    """Serial-tracked MO + no serial_numbers → BLOCK warning naming the SKU."""
    context, lifespan_ctx = create_mock_context()
    _wire_serial_tracked_cache(lifespan_ctx, variant_id=100, sku="WIDGET-V2")

    mock_mo = _make_serial_tracked_mo(order_no="MO-SN-1", actual_quantity=1.0)
    mock_response = MagicMock(status_code=200, parsed=mock_mo)

    from katana_public_api_client.api.manufacturing_order import (
        get_manufacturing_order,
    )

    cast(Any, get_manufacturing_order).asyncio_detailed = AsyncMock(
        return_value=mock_response
    )

    request = FulfillOrderRequest(order_id=42, order_type="manufacturing", preview=True)
    result = await _fulfill_order_impl(request, context)

    block_warnings = [w for w in result.warnings if w.startswith("BLOCK:")]
    assert len(block_warnings) == 1
    assert "serial-tracked" in block_warnings[0]
    assert "WIDGET-V2" in block_warnings[0]
    assert "Resolve the issue" in result.next_actions[0]


@pytest.mark.asyncio
async def test_fulfill_manufacturing_order_preview_accepts_serial_numbers():
    """Serial-tracked MO + matching serial_numbers → no BLOCK, serials in preview."""
    context, lifespan_ctx = create_mock_context()
    _wire_serial_tracked_cache(lifespan_ctx, variant_id=100, sku="WIDGET-V2")

    mock_mo = _make_serial_tracked_mo(order_no="MO-SN-2", actual_quantity=1.0)
    mock_response = MagicMock(status_code=200, parsed=mock_mo)

    from katana_public_api_client.api.manufacturing_order import (
        get_manufacturing_order,
    )

    cast(Any, get_manufacturing_order).asyncio_detailed = AsyncMock(
        return_value=mock_response
    )

    request = FulfillOrderRequest(
        order_id=42,
        order_type="manufacturing",
        preview=True,
        serial_numbers=[501],
    )
    result = await _fulfill_order_impl(request, context)

    assert not [w for w in result.warnings if w.startswith("BLOCK:")]
    assert any("[501]" in u for u in result.inventory_updates)


@pytest.mark.asyncio
async def test_fulfill_manufacturing_order_apply_passes_serials_to_api():
    """Apply with serial_numbers → production POST body carries them as
    list[int] (#790). Serial-tracked MO close-out: caller must mint via
    ``POST /serial_numbers`` first; Katana silently drops unminted IDs.
    """
    context, lifespan_ctx = create_mock_context()
    _wire_serial_tracked_cache(lifespan_ctx, variant_id=100, sku="WIDGET-V2")

    mock_mo = _make_serial_tracked_mo(order_no="MO-SN-3", actual_quantity=2.0)
    mock_get_response = MagicMock(status_code=200, parsed=mock_mo)

    from katana_public_api_client.models import ManufacturingOrderProduction

    mock_production = MagicMock(spec=ManufacturingOrderProduction)
    mock_production.id = 9001
    mock_create_response = MagicMock(status_code=200, parsed=mock_production)

    mock_done_mo = MagicMock(spec=ManufacturingOrder)
    mock_done_mo.order_no = "MO-SN-3"
    mock_done_mo.status = ManufacturingOrderStatus.DONE
    mock_final_response = MagicMock(status_code=200, parsed=mock_done_mo)

    from katana_public_api_client.api.manufacturing_order import (
        get_manufacturing_order,
    )
    from katana_public_api_client.api.manufacturing_order_production import (
        create_manufacturing_order_production,
    )

    get_mock = AsyncMock(side_effect=[mock_get_response, mock_final_response])
    cast(Any, get_manufacturing_order).asyncio_detailed = get_mock

    create_mock = AsyncMock(return_value=mock_create_response)
    cast(Any, create_manufacturing_order_production).asyncio_detailed = create_mock

    request = FulfillOrderRequest(
        order_id=42,
        order_type="manufacturing",
        preview=False,
        serial_numbers=[501, 502],
    )
    result = await _fulfill_order_impl(request, context)

    assert result.is_preview is False
    assert result.status == "DONE"
    create_mock.assert_called_once()
    sent_body = create_mock.call_args.kwargs["body"]
    assert sent_body.serial_numbers == [501, 502]
    # completed_quantity sourced from the MO's actual_quantity.
    assert sent_body.completed_quantity == 2.0
    assert sent_body.is_final is True


@pytest.mark.asyncio
async def test_fulfill_manufacturing_order_apply_refuses_serial_tracked_without_serials():
    """Direct apply (preview=False) without serial_numbers → refusal, no API call."""
    context, lifespan_ctx = create_mock_context()
    _wire_serial_tracked_cache(lifespan_ctx, variant_id=100, sku="WIDGET-V2")

    mock_mo = _make_serial_tracked_mo(order_no="MO-SN-4", actual_quantity=1.0)
    mock_response = MagicMock(status_code=200, parsed=mock_mo)

    from katana_public_api_client.api.manufacturing_order import (
        get_manufacturing_order,
        update_manufacturing_order,
    )

    cast(Any, get_manufacturing_order).asyncio_detailed = AsyncMock(
        return_value=mock_response
    )
    update_mock = AsyncMock()
    cast(Any, update_manufacturing_order).asyncio_detailed = update_mock

    request = FulfillOrderRequest(
        order_id=42, order_type="manufacturing", preview=False
    )
    result = await _fulfill_order_impl(request, context)

    assert result.is_preview is False
    block_warnings = [w for w in result.warnings if w.startswith("BLOCK:")]
    assert any("serial-tracked" in w for w in block_warnings)
    assert "Refused" in result.message
    update_mock.assert_not_called()


@pytest.mark.asyncio
async def test_fulfill_manufacturing_order_blocks_quantity_serials_mismatch():
    """len(serial_numbers) != actual_quantity → BLOCK warning."""
    context, lifespan_ctx = create_mock_context()
    _wire_serial_tracked_cache(lifespan_ctx, variant_id=100, sku="WIDGET-V2")

    # actual_quantity=2 but only 1 serial provided.
    mock_mo = _make_serial_tracked_mo(order_no="MO-SN-5", actual_quantity=2.0)
    mock_response = MagicMock(status_code=200, parsed=mock_mo)

    from katana_public_api_client.api.manufacturing_order import (
        get_manufacturing_order,
    )

    cast(Any, get_manufacturing_order).asyncio_detailed = AsyncMock(
        return_value=mock_response
    )

    request = FulfillOrderRequest(
        order_id=42,
        order_type="manufacturing",
        preview=True,
        serial_numbers=[501],
    )
    result = await _fulfill_order_impl(request, context)

    block_warnings = [w for w in result.warnings if w.startswith("BLOCK:")]
    assert any("count (1) must equal actual_quantity (2" in w for w in block_warnings)


@pytest.mark.asyncio
async def test_fulfill_manufacturing_order_blocks_serial_tracked_non_integer_quantity():
    """Serial-tracked MO with non-integer actual_quantity → BLOCK warning.

    Each serial number represents a whole unit; a fractional ``actual_quantity``
    is incompatible with serial tracking.
    """
    context, lifespan_ctx = create_mock_context()
    _wire_serial_tracked_cache(lifespan_ctx, variant_id=100, sku="WIDGET-V2")

    mock_mo = _make_serial_tracked_mo(order_no="MO-SN-FRAC", actual_quantity=1.5)
    mock_response = MagicMock(status_code=200, parsed=mock_mo)

    from katana_public_api_client.api.manufacturing_order import (
        get_manufacturing_order,
    )

    cast(Any, get_manufacturing_order).asyncio_detailed = AsyncMock(
        return_value=mock_response
    )

    request = FulfillOrderRequest(
        order_id=42,
        order_type="manufacturing",
        preview=True,
        serial_numbers=[501],
    )
    result = await _fulfill_order_impl(request, context)

    block_warnings = [w for w in result.warnings if w.startswith("BLOCK:")]
    assert any(
        "serial-tracked but actual_quantity (1.5) is not a whole number" in w
        for w in block_warnings
    )


@pytest.mark.asyncio
async def test_fulfill_manufacturing_order_serial_tracked_detection_falls_back_to_api():
    """Cold / stale cache: variant + product missing from cache.

    Without the API fallback, a cold cache silently classifies the MO as
    not-serial-tracked, so the BLOCK warning never fires and the user hits
    the original Katana 422 on apply. With the fallback, the per-ID API
    fetch resolves the variant + product and the BLOCK warning fires.
    """
    context, _lifespan_ctx = create_mock_context()
    # Default mock cache returns {} for every get_many_by_ids — simulating
    # a cold cache. We do NOT call _wire_serial_tracked_cache here.

    mock_mo = _make_serial_tracked_mo(order_no="MO-SN-COLD", actual_quantity=1.0)
    mock_get_mo_response = MagicMock(status_code=200, parsed=mock_mo)

    # API fallback: get_variant returns a variant pointing at product 9100;
    # get_product returns a serial-tracked product. Phase D's
    # ``_fetch_missing_from_api`` stores the attrs object directly
    # (callers use ``getattr`` to read fields uniformly across cache hits
    # and API-fallback rows), so we set attributes on the mocks instead
    # of the legacy ``to_dict`` shim.
    variant_obj = MagicMock()
    variant_obj.id = 100
    variant_obj.sku = "WIDGET-V2"
    variant_obj.product_id = 9100
    variant_obj.material_id = None
    mock_get_variant_response = MagicMock(status_code=200, parsed=variant_obj)

    product_obj = MagicMock()
    product_obj.id = 9100
    product_obj.serial_tracked = True
    mock_get_product_response = MagicMock(status_code=200, parsed=product_obj)

    from katana_public_api_client.api.manufacturing_order import (
        get_manufacturing_order,
    )
    from katana_public_api_client.api.product import get_product
    from katana_public_api_client.api.variant import get_variant

    cast(Any, get_manufacturing_order).asyncio_detailed = AsyncMock(
        return_value=mock_get_mo_response
    )
    cast(Any, get_variant).asyncio_detailed = AsyncMock(
        return_value=mock_get_variant_response
    )
    cast(Any, get_product).asyncio_detailed = AsyncMock(
        return_value=mock_get_product_response
    )

    request = FulfillOrderRequest(order_id=42, order_type="manufacturing", preview=True)
    result = await _fulfill_order_impl(request, context)

    block_warnings = [w for w in result.warnings if w.startswith("BLOCK:")]
    assert any("serial-tracked" in w and "WIDGET-V2" in w for w in block_warnings)
    # Verify both API endpoints were hit.
    cast(Any, get_variant.asyncio_detailed).assert_called_once()
    cast(Any, get_product.asyncio_detailed).assert_called_once()


@pytest.mark.asyncio
async def test_fulfill_manufacturing_order_non_serial_tracked_no_change():
    """Non-serial-tracked MO + no serials → no BLOCK, production POST body
    carries UNSET for serial_numbers (not an empty list) (#790).
    """
    context, lifespan_ctx = create_mock_context()

    async def _get_many(cls, ids, **_kw):
        ids = list(ids or [])
        if cls is CachedVariant and 100 in ids:
            return {100: CachedVariant(id=100, sku="PLAIN-WIDGET", product_id=9100)}
        if cls is CachedProduct and 9100 in ids:
            return {
                9100: CachedProduct(
                    id=9100,
                    name="Widget",
                    type=InventoryItemType.product,
                    serial_tracked=False,
                )
            }
        return {}

    lifespan_ctx.typed_cache.catalog.get_many_by_ids = AsyncMock(side_effect=_get_many)

    mock_mo = _make_serial_tracked_mo(order_no="MO-SN-7", actual_quantity=2.0)
    mock_get_response = MagicMock(status_code=200, parsed=mock_mo)

    from katana_public_api_client.models import ManufacturingOrderProduction

    mock_production = MagicMock(spec=ManufacturingOrderProduction)
    mock_production.id = 9001
    mock_create_response = MagicMock(status_code=200, parsed=mock_production)

    mock_done_mo = MagicMock(spec=ManufacturingOrder)
    mock_done_mo.order_no = "MO-SN-7"
    mock_done_mo.status = ManufacturingOrderStatus.DONE
    mock_final_response = MagicMock(status_code=200, parsed=mock_done_mo)

    from katana_public_api_client.api.manufacturing_order import (
        get_manufacturing_order,
    )
    from katana_public_api_client.api.manufacturing_order_production import (
        create_manufacturing_order_production,
    )

    get_mock = AsyncMock(side_effect=[mock_get_response, mock_final_response])
    cast(Any, get_manufacturing_order).asyncio_detailed = get_mock

    create_mock = AsyncMock(return_value=mock_create_response)
    cast(Any, create_manufacturing_order_production).asyncio_detailed = create_mock

    request = FulfillOrderRequest(
        order_id=42, order_type="manufacturing", preview=False
    )
    result = await _fulfill_order_impl(request, context)

    assert result.status == "DONE"
    assert not [w for w in result.warnings if w.startswith("BLOCK:")]
    sent_body = create_mock.call_args.kwargs["body"]
    # serial_numbers should be UNSET (omitted from wire), not an empty list.
    from katana_public_api_client.client_types import UNSET

    assert sent_body.serial_numbers is UNSET


# ============================================================================
# completed_at Backdating Tests (#778, refactored for #790)
# ============================================================================
#
# Hybrid surface: ``FulfillOrderRequest.completed_at`` maps to two different
# wire shapes depending on the order type.
#
# - SO: forwarded as ``picked_date`` on the single
#   ``POST /sales_order_fulfillments`` call (one round-trip).
# - MO: forwarded as ``completed_date`` on the single
#   ``POST /manufacturing_order_productions`` call (one round-trip). Katana
#   propagates ``completed_date`` verbatim to ``MO.done_date``. Refactored
#   from the prior two-call PATCH chase in #790.


@pytest.mark.asyncio
async def test_fulfill_mo_with_completed_at_one_call_succeeds():
    """MO apply with completed_at: one POST
    /manufacturing_order_productions fires with completed_date in the body
    (#790). No follow-up PATCH.
    """
    context, _lifespan_ctx = create_mock_context()

    mock_mo = MagicMock(spec=ManufacturingOrder)
    mock_mo.order_no = "MO-CA-1"
    mock_mo.status = ManufacturingOrderStatus.IN_PROGRESS
    mock_mo.variant_id = None
    mock_mo.actual_quantity = None
    mock_mo.sales_order_id = None  # silence #787 guard (no linked SO)

    mock_get_response = MagicMock(status_code=200, parsed=mock_mo)

    from katana_public_api_client.models import ManufacturingOrderProduction

    mock_production = MagicMock(spec=ManufacturingOrderProduction)
    mock_production.id = 9001
    mock_create_response = MagicMock(status_code=200, parsed=mock_production)

    mock_done_mo = MagicMock(spec=ManufacturingOrder)
    mock_done_mo.order_no = "MO-CA-1"
    mock_done_mo.status = ManufacturingOrderStatus.DONE
    mock_final_response = MagicMock(status_code=200, parsed=mock_done_mo)

    from katana_public_api_client.api.manufacturing_order import (
        get_manufacturing_order,
    )
    from katana_public_api_client.api.manufacturing_order_production import (
        create_manufacturing_order_production,
    )

    get_mock = AsyncMock(side_effect=[mock_get_response, mock_final_response])
    cast(Any, get_manufacturing_order).asyncio_detailed = get_mock

    create_mock = AsyncMock(return_value=mock_create_response)
    cast(Any, create_manufacturing_order_production).asyncio_detailed = create_mock

    completed = datetime(2026, 5, 1, 20, 30, tzinfo=UTC)
    request = FulfillOrderRequest(
        order_id=1234,
        order_type="manufacturing",
        preview=False,
        completed_at=completed,
    )
    result = await _fulfill_order_impl(request, context)

    assert result.is_preview is False
    assert result.status == "DONE"
    # Single production POST carries completed_date directly.
    create_mock.assert_called_once()
    sent_body = create_mock.call_args.kwargs["body"]
    assert sent_body.completed_date == completed
    assert sent_body.is_final is True
    # next_actions surfaces the backdate confirmation.
    assert any(
        "done_date set to" in a and completed.isoformat() in a
        for a in result.next_actions
    )


@pytest.mark.asyncio
async def test_fulfill_mo_completed_at_omitted_when_absent():
    """No completed_at: production POST body's completed_date stays UNSET
    (omitted from wire). Regression guard against accidentally clearing
    done_date to null.
    """
    context, _lifespan_ctx = create_mock_context()

    mock_mo = MagicMock(spec=ManufacturingOrder)
    mock_mo.order_no = "MO-CA-2"
    mock_mo.status = ManufacturingOrderStatus.IN_PROGRESS
    mock_mo.variant_id = None
    mock_mo.actual_quantity = None

    mock_get_response = MagicMock(status_code=200, parsed=mock_mo)

    from katana_public_api_client.models import ManufacturingOrderProduction

    mock_production = MagicMock(spec=ManufacturingOrderProduction)
    mock_production.id = 9001
    mock_create_response = MagicMock(status_code=200, parsed=mock_production)

    mock_done_mo = MagicMock(spec=ManufacturingOrder)
    mock_done_mo.order_no = "MO-CA-2"
    mock_done_mo.status = ManufacturingOrderStatus.DONE
    mock_final_response = MagicMock(status_code=200, parsed=mock_done_mo)

    from katana_public_api_client.api.manufacturing_order import (
        get_manufacturing_order,
    )
    from katana_public_api_client.api.manufacturing_order_production import (
        create_manufacturing_order_production,
    )

    get_mock = AsyncMock(side_effect=[mock_get_response, mock_final_response])
    cast(Any, get_manufacturing_order).asyncio_detailed = get_mock

    create_mock = AsyncMock(return_value=mock_create_response)
    cast(Any, create_manufacturing_order_production).asyncio_detailed = create_mock

    request = FulfillOrderRequest(
        order_id=1234, order_type="manufacturing", preview=False
    )
    result = await _fulfill_order_impl(request, context)

    assert result.is_preview is False
    assert result.status == "DONE"
    create_mock.assert_called_once()
    from katana_public_api_client.client_types import UNSET

    sent_body = create_mock.call_args.kwargs["body"]
    assert sent_body.completed_date is UNSET
    # No backdate next-action when completed_at is absent.
    assert not any("done_date set to" in a for a in result.next_actions)


@pytest.mark.asyncio
async def test_fulfill_mo_apply_emits_no_patch_calls():
    """Regression guard: apply path must NOT emit any PATCH /manufacturing_
    orders/{id} calls. Catches accidental re-introduction of the pre-#790
    two-call PATCH chain.
    """
    context, _lifespan_ctx = create_mock_context()

    mock_mo = MagicMock(spec=ManufacturingOrder)
    mock_mo.order_no = "MO-NOPATCH"
    mock_mo.status = ManufacturingOrderStatus.IN_PROGRESS
    mock_mo.variant_id = None
    mock_mo.actual_quantity = None
    mock_mo.sales_order_id = None  # silence #787 guard (no linked SO)

    mock_get_response = MagicMock(status_code=200, parsed=mock_mo)

    from katana_public_api_client.models import ManufacturingOrderProduction

    mock_production = MagicMock(spec=ManufacturingOrderProduction)
    mock_production.id = 9001
    mock_create_response = MagicMock(status_code=200, parsed=mock_production)

    mock_done_mo = MagicMock(spec=ManufacturingOrder)
    mock_done_mo.order_no = "MO-NOPATCH"
    mock_done_mo.status = ManufacturingOrderStatus.DONE
    mock_final_response = MagicMock(status_code=200, parsed=mock_done_mo)

    from katana_public_api_client.api.manufacturing_order import (
        get_manufacturing_order,
        update_manufacturing_order,
    )
    from katana_public_api_client.api.manufacturing_order_production import (
        create_manufacturing_order_production,
    )

    get_mock = AsyncMock(side_effect=[mock_get_response, mock_final_response])
    cast(Any, get_manufacturing_order).asyncio_detailed = get_mock

    # Wire the PATCH endpoint to a mock that records calls — must stay at 0.
    patch_mock = AsyncMock()
    cast(Any, update_manufacturing_order).asyncio_detailed = patch_mock

    create_mock = AsyncMock(return_value=mock_create_response)
    cast(Any, create_manufacturing_order_production).asyncio_detailed = create_mock

    request = FulfillOrderRequest(
        order_id=1234,
        order_type="manufacturing",
        preview=False,
        completed_at=datetime(2026, 5, 1, 20, 30, tzinfo=UTC),
    )
    result = await _fulfill_order_impl(request, context)

    assert result.status == "DONE"
    create_mock.assert_called_once()
    # Zero PATCH calls — the whole point of the #790 refactor.
    patch_mock.assert_not_called()


@pytest.mark.asyncio
async def test_fulfill_mo_completed_quantity_defaults_to_one_when_actual_unset():
    """When actual_quantity is None (MO never had a prior production),
    completed_quantity defaults to 1 in the production POST body.

    Katana stamps actual_quantity = completed_quantity on the MO when there's
    no prior production, so 1 closes the MO at qty=1 (matches the Katana
    UI's "complete one" semantics).
    """
    context, _lifespan_ctx = create_mock_context()

    mock_mo = MagicMock(spec=ManufacturingOrder)
    mock_mo.order_no = "MO-QTY1"
    mock_mo.status = ManufacturingOrderStatus.IN_PROGRESS
    mock_mo.variant_id = None
    mock_mo.actual_quantity = None

    mock_get_response = MagicMock(status_code=200, parsed=mock_mo)

    from katana_public_api_client.models import ManufacturingOrderProduction

    mock_production = MagicMock(spec=ManufacturingOrderProduction)
    mock_production.id = 9001
    mock_create_response = MagicMock(status_code=200, parsed=mock_production)

    mock_done_mo = MagicMock(spec=ManufacturingOrder)
    mock_done_mo.order_no = "MO-QTY1"
    mock_done_mo.status = ManufacturingOrderStatus.DONE
    mock_final_response = MagicMock(status_code=200, parsed=mock_done_mo)

    from katana_public_api_client.api.manufacturing_order import (
        get_manufacturing_order,
    )
    from katana_public_api_client.api.manufacturing_order_production import (
        create_manufacturing_order_production,
    )

    get_mock = AsyncMock(side_effect=[mock_get_response, mock_final_response])
    cast(Any, get_manufacturing_order).asyncio_detailed = get_mock

    create_mock = AsyncMock(return_value=mock_create_response)
    cast(Any, create_manufacturing_order_production).asyncio_detailed = create_mock

    request = FulfillOrderRequest(
        order_id=1234, order_type="manufacturing", preview=False
    )
    await _fulfill_order_impl(request, context)

    sent_body = create_mock.call_args.kwargs["body"]
    assert sent_body.completed_quantity == 1


@pytest.mark.asyncio
async def test_fulfill_mo_completed_quantity_sourced_from_actual_quantity():
    """When actual_quantity is set (e.g., partial completion of a 5-unit MO
    with 3 already produced), completed_quantity in the body matches.

    Per Probe 3: Katana honors the lower actual quantity with is_final=True
    (closes the MO at the partial value rather than refusing). #790.
    """
    context, _lifespan_ctx = create_mock_context()

    mock_mo = MagicMock(spec=ManufacturingOrder)
    mock_mo.order_no = "MO-QTY3"
    mock_mo.status = ManufacturingOrderStatus.IN_PROGRESS
    mock_mo.variant_id = None
    mock_mo.actual_quantity = 3.0

    mock_get_response = MagicMock(status_code=200, parsed=mock_mo)

    from katana_public_api_client.models import ManufacturingOrderProduction

    mock_production = MagicMock(spec=ManufacturingOrderProduction)
    mock_production.id = 9001
    mock_create_response = MagicMock(status_code=200, parsed=mock_production)

    mock_done_mo = MagicMock(spec=ManufacturingOrder)
    mock_done_mo.order_no = "MO-QTY3"
    mock_done_mo.status = ManufacturingOrderStatus.DONE
    mock_final_response = MagicMock(status_code=200, parsed=mock_done_mo)

    from katana_public_api_client.api.manufacturing_order import (
        get_manufacturing_order,
    )
    from katana_public_api_client.api.manufacturing_order_production import (
        create_manufacturing_order_production,
    )

    get_mock = AsyncMock(side_effect=[mock_get_response, mock_final_response])
    cast(Any, get_manufacturing_order).asyncio_detailed = get_mock

    create_mock = AsyncMock(return_value=mock_create_response)
    cast(Any, create_manufacturing_order_production).asyncio_detailed = create_mock

    request = FulfillOrderRequest(
        order_id=1234, order_type="manufacturing", preview=False
    )
    await _fulfill_order_impl(request, context)

    sent_body = create_mock.call_args.kwargs["body"]
    assert sent_body.completed_quantity == 3.0


@pytest.mark.asyncio
async def test_fulfill_mo_completed_at_naive_datetime_coerced_to_utc():
    """Naive datetime passed at the Pydantic boundary lands as tz-aware UTC.

    Mirrors the ``WireDatetime`` validator coverage in stock_transfers — the
    Katana wire requires a timezone offset; a naive datetime would 422.
    """
    request = FulfillOrderRequest(
        order_id=1,
        order_type="manufacturing",
        completed_at=datetime(2026, 5, 1, 20, 30),  # naive
    )
    assert request.completed_at is not None
    assert request.completed_at.tzinfo is not None
    assert (
        request.completed_at.utcoffset() == datetime(2026, 1, 1, tzinfo=UTC).utcoffset()
    )


@pytest.mark.asyncio
async def test_fulfill_mo_preview_with_completed_at_surfaces_in_inventory_updates():
    """Preview path adds a planned-backdating line to inventory_updates."""
    context, _lifespan_ctx = create_mock_context()

    mock_mo = MagicMock(spec=ManufacturingOrder)
    mock_mo.order_no = "MO-CA-PREVIEW"
    mock_mo.status = ManufacturingOrderStatus.IN_PROGRESS
    mock_mo.variant_id = None
    mock_mo.actual_quantity = None
    mock_mo.sales_order_id = None  # silence #787 guard (no linked SO)

    mock_response = MagicMock(status_code=200, parsed=mock_mo)

    from katana_public_api_client.api.manufacturing_order import (
        get_manufacturing_order,
    )

    cast(Any, get_manufacturing_order).asyncio_detailed = AsyncMock(
        return_value=mock_response
    )

    completed = datetime(2026, 5, 1, 20, 30, tzinfo=UTC)
    request = FulfillOrderRequest(
        order_id=1234,
        order_type="manufacturing",
        preview=True,
        completed_at=completed,
    )
    result = await _fulfill_order_impl(request, context)

    assert result.is_preview is True
    assert any(
        "completed_date / done_date will be set to" in u and completed.isoformat() in u
        for u in result.inventory_updates
    )


@pytest.mark.asyncio
async def test_fulfill_so_with_completed_at_one_call():
    """SO apply with completed_at: single POST carries picked_date in body."""
    context, lifespan_ctx = create_mock_context()
    # Wire the cache so variant 100 resolves to a non-serial-tracked product —
    # this also defeats the API-fallback path that earlier tests in this file
    # left mocked (test ordering would otherwise route variant lookups through
    # ``get_variant.asyncio_detailed`` AsyncMock leftovers and surface a
    # spurious serial-tracked BLOCK warning).
    _wire_non_serial_tracked_cache(lifespan_ctx, variant_id=100, sku="PLAIN-CA")

    mock_so = MagicMock(spec=SalesOrder)
    mock_so.order_no = "SO-CA-1"
    mock_so.status = SalesOrderStatus.NOT_SHIPPED
    mock_so.sales_order_rows = [_make_so_row(1, 100, 2.0)]

    mock_get_response = MagicMock(status_code=200, parsed=mock_so)

    from katana_public_api_client.api.sales_order import get_sales_order
    from katana_public_api_client.api.sales_order_fulfillment import (
        create_sales_order_fulfillment,
    )
    from katana_public_api_client.models import SalesOrderFulfillment

    cast(Any, get_sales_order).asyncio_detailed = AsyncMock(
        return_value=mock_get_response
    )
    fulfillment_obj = MagicMock(spec=SalesOrderFulfillment)
    fulfillment_obj.id = 11111
    mock_create_response = MagicMock(status_code=200, parsed=fulfillment_obj)
    create_mock = AsyncMock(return_value=mock_create_response)
    cast(Any, create_sales_order_fulfillment).asyncio_detailed = create_mock

    completed = datetime(2026, 5, 1, 20, 30, tzinfo=UTC)
    request = FulfillOrderRequest(
        order_id=5678,
        order_type="sales",
        preview=False,
        completed_at=completed,
    )
    result = await _fulfill_order_impl(request, context)

    assert result.is_preview is False
    assert result.status == "DELIVERED"
    create_mock.assert_called_once()
    sent_body = create_mock.call_args.kwargs["body"]
    assert sent_body.picked_date == completed


@pytest.mark.asyncio
async def test_fulfill_so_without_completed_at_omits_picked_date():
    """No completed_at: picked_date stays UNSET (regression guard).

    Forwarding ``None`` directly would set ``picked_date=null`` on the wire
    and Katana would 422; ``to_unset(None) is UNSET`` keeps the field off
    the wire entirely.
    """
    context, lifespan_ctx = create_mock_context()
    _wire_non_serial_tracked_cache(lifespan_ctx, variant_id=100, sku="PLAIN-CA")

    mock_so = MagicMock(spec=SalesOrder)
    mock_so.order_no = "SO-CA-2"
    mock_so.status = SalesOrderStatus.NOT_SHIPPED
    mock_so.sales_order_rows = [_make_so_row(1, 100, 2.0)]

    mock_get_response = MagicMock(status_code=200, parsed=mock_so)

    from katana_public_api_client.api.sales_order import get_sales_order
    from katana_public_api_client.api.sales_order_fulfillment import (
        create_sales_order_fulfillment,
    )
    from katana_public_api_client.client_types import UNSET
    from katana_public_api_client.models import SalesOrderFulfillment

    cast(Any, get_sales_order).asyncio_detailed = AsyncMock(
        return_value=mock_get_response
    )
    fulfillment_obj = MagicMock(spec=SalesOrderFulfillment)
    fulfillment_obj.id = 22222
    mock_create_response = MagicMock(status_code=200, parsed=fulfillment_obj)
    create_mock = AsyncMock(return_value=mock_create_response)
    cast(Any, create_sales_order_fulfillment).asyncio_detailed = create_mock

    request = FulfillOrderRequest(order_id=5678, order_type="sales", preview=False)
    result = await _fulfill_order_impl(request, context)

    assert result.is_preview is False
    sent_body = create_mock.call_args.kwargs["body"]
    assert sent_body.picked_date is UNSET


@pytest.mark.asyncio
async def test_fulfill_so_completed_at_with_row_overrides():
    """completed_at + rows= coexist cleanly on the same apply call.

    Uses a serial-tracked variant so the row override is exercised end-to-end
    (the override is the *only* way to satisfy the serial-tracked BLOCK
    warning on apply).
    """
    context, lifespan_ctx = create_mock_context()
    _wire_serial_tracked_cache(lifespan_ctx, variant_id=100, sku="WIDGET-CA")

    mock_so = MagicMock(spec=SalesOrder)
    mock_so.order_no = "SO-CA-3"
    mock_so.status = SalesOrderStatus.NOT_SHIPPED
    mock_so.sales_order_rows = [_make_so_row(1, 100, 1.0)]

    mock_get_response = MagicMock(status_code=200, parsed=mock_so)

    from katana_public_api_client.api.sales_order import get_sales_order
    from katana_public_api_client.api.sales_order_fulfillment import (
        create_sales_order_fulfillment,
    )
    from katana_public_api_client.models import SalesOrderFulfillment

    cast(Any, get_sales_order).asyncio_detailed = AsyncMock(
        return_value=mock_get_response
    )
    fulfillment_obj = MagicMock(spec=SalesOrderFulfillment)
    fulfillment_obj.id = 33333
    mock_create_response = MagicMock(status_code=200, parsed=fulfillment_obj)
    create_mock = AsyncMock(return_value=mock_create_response)
    cast(Any, create_sales_order_fulfillment).asyncio_detailed = create_mock

    completed = datetime(2026, 5, 1, 20, 30, tzinfo=UTC)
    request = FulfillOrderRequest(
        order_id=5678,
        order_type="sales",
        preview=False,
        rows=[FulfillRowOverride(sales_order_row_id=1, serial_numbers=[501])],
        completed_at=completed,
    )
    result = await _fulfill_order_impl(request, context)

    assert result.is_preview is False
    assert result.status == "DELIVERED"
    create_mock.assert_called_once()
    sent_body = create_mock.call_args.kwargs["body"]
    # Both knobs land — picked_date on the header, serial_numbers on the row.
    assert sent_body.picked_date == completed
    assert sent_body.sales_order_fulfillment_rows[0].serial_numbers == [501]


@pytest.mark.asyncio
async def test_completed_at_validator_rejects_invalid_string():
    """Pydantic validator rejects non-ISO strings before the tool runs.

    Goes through ``model_validate`` so the test stays type-clean — the raw
    string is a runtime concern (MCP clients pass JSON), not a static-type
    one.
    """
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        FulfillOrderRequest.model_validate(
            {
                "order_id": 1,
                "order_type": "manufacturing",
                "completed_at": "not-a-datetime",
            }
        )


@pytest.mark.asyncio
async def test_fulfill_mo_completed_at_propagates_to_serial_transaction_date():
    """Integration-style: the single production POST carries both
    ``serial_numbers`` and ``completed_date`` in one body — Katana
    propagates ``completed_date`` to ``MO.done_date``, which derives the
    ``SerialNumber.transaction_date`` shown in the Traceability column.

    This test pins the **emitter side**: the tool sends Katana exactly one
    ``completed_date`` value via the production POST. The **consumer side**
    (Katana deriving ``SerialNumber.transaction_date`` from
    ``completed_date`` → ``done_date``) is asserted live (Probe 2 in #790).
    """
    context, lifespan_ctx = create_mock_context()
    _wire_serial_tracked_cache(lifespan_ctx, variant_id=100, sku="WIDGET-SN")

    mock_mo = _make_serial_tracked_mo(order_no="MO-CA-SN", actual_quantity=1.0)
    mock_get_response = MagicMock(status_code=200, parsed=mock_mo)

    from katana_public_api_client.models import ManufacturingOrderProduction

    mock_production = MagicMock(spec=ManufacturingOrderProduction)
    mock_production.id = 9001
    mock_create_response = MagicMock(status_code=200, parsed=mock_production)

    mock_done_mo = MagicMock(spec=ManufacturingOrder)
    mock_done_mo.order_no = "MO-CA-SN"
    mock_done_mo.status = ManufacturingOrderStatus.DONE
    mock_final_response = MagicMock(status_code=200, parsed=mock_done_mo)

    from katana_public_api_client.api.manufacturing_order import (
        get_manufacturing_order,
    )
    from katana_public_api_client.api.manufacturing_order_production import (
        create_manufacturing_order_production,
    )

    get_mock = AsyncMock(side_effect=[mock_get_response, mock_final_response])
    cast(Any, get_manufacturing_order).asyncio_detailed = get_mock

    create_mock = AsyncMock(return_value=mock_create_response)
    cast(Any, create_manufacturing_order_production).asyncio_detailed = create_mock

    completed = datetime(2026, 5, 1, 20, 30, tzinfo=UTC)
    request = FulfillOrderRequest(
        order_id=42,
        order_type="manufacturing",
        preview=False,
        serial_numbers=[501],
        completed_at=completed,
    )
    result = await _fulfill_order_impl(request, context)

    assert result.is_preview is False
    create_mock.assert_called_once()
    sent_body = create_mock.call_args.kwargs["body"]
    # Serials + completed_date land in the same body — atomic close (#790).
    assert sent_body.serial_numbers == [501]
    assert sent_body.completed_date == completed
    assert sent_body.is_final is True


# ============================================================================
# Tier 2 metrics + Tier 3 per-row enrichment (#553)
# ============================================================================


def _make_so_row_with_price(
    row_id: int,
    variant_id: int,
    quantity: float,
    price_per_unit: str,
    *,
    batch_transactions: Any = None,
) -> MagicMock:
    """Like ``_make_so_row`` but pins the fields the #553 enrichment reads.

    Sets ``price_per_unit`` as a string (matches the wire model — the
    Katana API returns prices as strings to preserve precision) and
    optionally a ``batch_transactions`` list so the batch_summary branch
    can be exercised.
    """
    from katana_public_api_client.client_types import UNSET

    row = MagicMock()
    row.id = row_id
    row.variant_id = variant_id
    row.quantity = quantity
    row.price_per_unit = price_per_unit
    row.batch_transactions = (
        batch_transactions if batch_transactions is not None else UNSET
    )
    return row


@pytest.mark.asyncio
async def test_fulfill_sales_order_preview_enriches_fulfilled_rows():
    """Preview path enriches ``fulfilled_rows`` with PO row + cache data (#553).

    Pinned by the receipt-card sibling pattern (#556 / PR #793). Joins:
    - request row overrides (serial_numbers)
    - SO rows (quantity, variant_id, price_per_unit, batch_transactions)
    - typed cache variants (sku, display_name)

    Plus computes the Tier 2 metric aggregates (rows_count, total_quantity,
    total_value) that drive the Metric row on the card.
    """
    context, lifespan_ctx = create_mock_context()

    mock_so = MagicMock(spec=SalesOrder)
    mock_so.order_no = "SO-T2-001"
    mock_so.status = SalesOrderStatus.NOT_SHIPPED
    mock_so.currency = "USD"
    mock_so.sales_order_rows = [
        _make_so_row_with_price(1, 100, 5.0, "10.00"),
        _make_so_row_with_price(2, 200, 2.0, "25.00"),
    ]

    mock_response = MagicMock(status_code=200, parsed=mock_so)
    from katana_public_api_client.api.sales_order import get_sales_order

    cast(Any, get_sales_order).asyncio_detailed = AsyncMock(return_value=mock_response)

    # Seed the typed cache so each variant resolves to a canonical
    # display_name; the enrichment lifts this verbatim into the row.
    def _mk_cached(vid, sku, display_name):
        m = MagicMock()
        m.id = vid
        m.sku = sku
        m.display_name = display_name
        m.product_id = None
        m.material_id = None
        m.config_attributes = []
        return m

    async def _get_many(model_cls, ids, **_kw):
        if model_cls is CachedVariant:
            data = {
                100: _mk_cached(100, "WIDGET-100", "Big Widget / Red"),
                200: _mk_cached(200, "WIDGET-200", "Small Widget / Blue"),
            }
            return {vid: data[vid] for vid in ids if vid in data}
        return {}

    lifespan_ctx.typed_cache.catalog.get_many_by_ids = AsyncMock(side_effect=_get_many)

    request = FulfillOrderRequest(
        order_id=5678,
        order_type="sales",
        preview=True,
        rows=[FulfillRowOverride(sales_order_row_id=2, serial_numbers=[9001, 9002])],
    )
    result = await _fulfill_order_impl(request, context)

    # ---- Tier 3 enrichment ----
    assert len(result.fulfilled_rows) == 2
    by_row = {r.row_id: r for r in result.fulfilled_rows}

    row_a = by_row[1]
    assert row_a.variant_id == 100
    assert row_a.sku == "WIDGET-100"
    assert row_a.display_name == "Big Widget / Red"
    assert row_a.quantity == 5.0
    assert row_a.price_per_unit == 10.0
    assert row_a.row_total == 50.0
    assert row_a.currency == "USD"
    assert row_a.serial_numbers == []
    assert row_a.batch_summary is None

    row_b = by_row[2]
    assert row_b.variant_id == 200
    assert row_b.sku == "WIDGET-200"
    assert row_b.quantity == 2.0
    assert row_b.row_total == 50.0
    # Serial overrides from the request land on the enriched row.
    assert row_b.serial_numbers == [9001, 9002]

    # ---- Tier 2 metrics ----
    assert result.rows_count == 2
    assert result.total_quantity == 7.0
    assert result.total_value == 100.0
    assert result.currency == "USD"
    # Tier 4: deep link is on the preview response so the success card
    # can pre-bind the View in Katana button.
    assert result.katana_url is not None
    assert result.katana_url.endswith("/salesorder/5678")


@pytest.mark.asyncio
async def test_fulfill_sales_order_preview_batch_summary_renders():
    """Batch-tracked rows surface the allocation in human-readable form
    (``"batch 42x30, batch 51x20"``). Pinned for the receipt-card sibling
    parity (#556) so a future change to the format keeps the two cards
    in step.
    """
    context, _lifespan_ctx = create_mock_context()

    # Batch transaction objects mirroring the wire model shape.
    bt1 = MagicMock()
    bt1.batch_id = 42
    bt1.quantity = 30.0
    bt2 = MagicMock()
    bt2.batch_id = 51
    bt2.quantity = 20.0

    mock_so = MagicMock(spec=SalesOrder)
    mock_so.order_no = "SO-BATCH"
    mock_so.status = SalesOrderStatus.NOT_SHIPPED
    mock_so.currency = "USD"
    mock_so.sales_order_rows = [
        _make_so_row_with_price(1, 300, 50.0, "5.00", batch_transactions=[bt1, bt2]),
    ]

    mock_response = MagicMock(status_code=200, parsed=mock_so)
    from katana_public_api_client.api.sales_order import get_sales_order

    cast(Any, get_sales_order).asyncio_detailed = AsyncMock(return_value=mock_response)

    request = FulfillOrderRequest(order_id=9999, order_type="sales", preview=True)
    result = await _fulfill_order_impl(request, context)

    assert len(result.fulfilled_rows) == 1
    assert result.fulfilled_rows[0].batch_summary == "batch 42x30, batch 51x20"


@pytest.mark.asyncio
async def test_fulfill_manufacturing_order_preview_enriches_fulfilled_row():
    """MO preview enriches a single ``FulfilledRowInfo`` (the MO carries
    one variant, not a row list). Tier 2 metrics: rows_count=1, total_qty
    is ``actual_quantity``, total_value is ``None`` (MOs track cost, not
    price). ``katana_url`` deep-links to the MO page.
    """
    context, lifespan_ctx = create_mock_context()

    mock_mo = MagicMock(spec=ManufacturingOrder)
    mock_mo.order_no = "MO-T2-001"
    mock_mo.status = ManufacturingOrderStatus.IN_PROGRESS
    mock_mo.variant_id = 555
    mock_mo.actual_quantity = 3.0

    mock_response = MagicMock(status_code=200, parsed=mock_mo)
    from katana_public_api_client.api.manufacturing_order import (
        get_manufacturing_order,
    )

    cast(Any, get_manufacturing_order).asyncio_detailed = AsyncMock(
        return_value=mock_response
    )

    cached_variant = MagicMock()
    cached_variant.id = 555
    cached_variant.sku = "FG-001"
    cached_variant.display_name = "Premium Widget / Large"
    cached_variant.product_id = None
    cached_variant.material_id = None
    cached_variant.config_attributes = []

    async def _get_many(model_cls, ids, **_kw):
        if model_cls is CachedVariant and 555 in set(ids):
            return {555: cached_variant}
        return {}

    lifespan_ctx.typed_cache.catalog.get_many_by_ids = AsyncMock(side_effect=_get_many)

    request = FulfillOrderRequest(
        order_id=8888, order_type="manufacturing", preview=True
    )
    result = await _fulfill_order_impl(request, context)

    # ---- Tier 3 enrichment ----
    assert len(result.fulfilled_rows) == 1
    row = result.fulfilled_rows[0]
    assert row.row_id is None  # MO has no row IDs the way SO does
    assert row.variant_id == 555
    assert row.sku == "FG-001"
    assert row.display_name == "Premium Widget / Large"
    assert row.quantity == 3.0
    # Price not surfaced on the MO branch.
    assert row.price_per_unit is None
    assert row.row_total is None
    assert row.currency is None

    # ---- Tier 2 metrics ----
    assert result.rows_count == 1
    assert result.total_quantity == 3.0
    # No price on any row → total_value omitted (None signals the card
    # to skip the Total Value metric).
    assert result.total_value is None

    # ---- Tier 4 deep link ----
    assert result.katana_url is not None
    assert result.katana_url.endswith("/manufacturingorder/8888")


@pytest.mark.asyncio
async def test_mo_card_renders_real_sku_starting_with_variant_prefix():
    """Regression: real customer SKUs starting with the literal prefix
    ``"variant "`` (note the trailing space — e.g. ``"variant 2 pack"``
    for a multi-pack, or any product-line where the word ``variant`` is
    followed by space-separated qualifiers) must round-trip to the card
    unmolested.

    The earlier ``sku.startswith("variant ")`` guard in
    ``_build_fulfilled_row_manufacturing`` was meant to filter the
    ``f"variant {id}"`` cache-miss sentinel — but that sentinel is only
    injected at the resolution sites (``_resolve_row_serial_info`` /
    ``_resolve_variant_serial_info``), so the strip was redundant *and*
    blanked legitimate SKUs for any customer with the naming convention.
    Pinned here so the bug can't silently regress — note the SKU below
    uses ``"variant "`` with a space, which is exactly the prefix the
    old guard would have caught.
    """
    context, lifespan_ctx = create_mock_context()

    mock_mo = MagicMock(spec=ManufacturingOrder)
    mock_mo.order_no = "MO-VAR-PREFIX"
    mock_mo.status = ManufacturingOrderStatus.IN_PROGRESS
    mock_mo.variant_id = 777
    mock_mo.actual_quantity = 2.0

    mock_response = MagicMock(status_code=200, parsed=mock_mo)
    from katana_public_api_client.api.manufacturing_order import (
        get_manufacturing_order,
    )

    cast(Any, get_manufacturing_order).asyncio_detailed = AsyncMock(
        return_value=mock_response
    )

    cached_variant = MagicMock()
    cached_variant.id = 777
    # Real customer SKU that *starts with* "variant " (literal space) —
    # this is the exact prefix the old buggy guard checked, so removing
    # the guard must let this SKU survive intact.
    cached_variant.sku = "variant 2 pack"
    cached_variant.display_name = "Premium Widget / 2-Pack"
    cached_variant.product_id = None
    cached_variant.material_id = None
    cached_variant.config_attributes = []

    async def _get_many(model_cls, ids, **_kw):
        if model_cls is CachedVariant and 777 in set(ids):
            return {777: cached_variant}
        return {}

    lifespan_ctx.typed_cache.catalog.get_many_by_ids = AsyncMock(side_effect=_get_many)

    request = FulfillOrderRequest(
        order_id=4242, order_type="manufacturing", preview=True
    )
    result = await _fulfill_order_impl(request, context)

    assert len(result.fulfilled_rows) == 1
    row = result.fulfilled_rows[0]
    # The SKU must survive intact — the previous startswith guard would
    # have nulled this and the card would have shown "variant {id}" instead
    # of the real SKU.
    assert row.sku == "variant 2 pack"
    assert row.display_name == "Premium Widget / 2-Pack"
    assert row.variant_id == 777


@pytest.mark.asyncio
async def test_fulfill_manufacturing_order_confirm_carries_enrichment():
    """Success path rebuilds enrichment from the *post-mutation* MO so the
    success card reflects what Katana actually stamped (matters when the
    MO had no prior production and Katana sets ``actual_quantity =
    completed_quantity``).
    """
    context, lifespan_ctx = create_mock_context()

    # Initial fetch: pre-production MO with no actual_quantity yet.
    mock_pre_mo = MagicMock(spec=ManufacturingOrder)
    mock_pre_mo.order_no = "MO-T2-CONFIRM"
    mock_pre_mo.status = ManufacturingOrderStatus.IN_PROGRESS
    mock_pre_mo.variant_id = 555
    mock_pre_mo.actual_quantity = None
    mock_get_response = MagicMock(status_code=200, parsed=mock_pre_mo)

    from katana_public_api_client.models import ManufacturingOrderProduction

    mock_production = MagicMock(spec=ManufacturingOrderProduction)
    mock_production.id = 9001
    mock_create_response = MagicMock(status_code=200, parsed=mock_production)

    # Post-mutation MO: Katana stamped actual_quantity = 1 (the default).
    mock_post_mo = MagicMock(spec=ManufacturingOrder)
    mock_post_mo.order_no = "MO-T2-CONFIRM"
    mock_post_mo.status = ManufacturingOrderStatus.DONE
    mock_post_mo.variant_id = 555
    mock_post_mo.actual_quantity = 1.0
    mock_final_response = MagicMock(status_code=200, parsed=mock_post_mo)

    from katana_public_api_client.api.manufacturing_order import (
        get_manufacturing_order,
    )
    from katana_public_api_client.api.manufacturing_order_production import (
        create_manufacturing_order_production,
    )

    cast(Any, get_manufacturing_order).asyncio_detailed = AsyncMock(
        side_effect=[mock_get_response, mock_final_response]
    )
    cast(Any, create_manufacturing_order_production).asyncio_detailed = AsyncMock(
        return_value=mock_create_response
    )

    cached_variant = MagicMock()
    cached_variant.id = 555
    cached_variant.sku = "FG-001"
    cached_variant.display_name = "Premium Widget"
    cached_variant.product_id = None
    cached_variant.material_id = None
    cached_variant.config_attributes = []

    async def _get_many(model_cls, ids, **_kw):
        if model_cls is CachedVariant and 555 in set(ids):
            return {555: cached_variant}
        return {}

    lifespan_ctx.typed_cache.catalog.get_many_by_ids = AsyncMock(side_effect=_get_many)

    request = FulfillOrderRequest(
        order_id=8888, order_type="manufacturing", preview=False
    )
    result = await _fulfill_order_impl(request, context)

    assert result.is_preview is False
    assert result.status == "DONE"
    # Quantity reflects post-mutation state (the API-stamped actual_quantity=1),
    # not the pre-mutation None.
    assert len(result.fulfilled_rows) == 1
    assert result.fulfilled_rows[0].quantity == 1.0
    assert result.rows_count == 1
    assert result.total_quantity == 1.0
    # Deep link present on the success response so the View in Katana
    # button can wire up without an extra round-trip.
    assert result.katana_url is not None


@pytest.mark.asyncio
async def test_fulfill_sales_order_confirm_carries_enrichment():
    """Success path on the SO branch also carries the enriched rows +
    metrics + deep link so the success card matches the preview card's
    information density.
    """
    context, lifespan_ctx = create_mock_context()

    mock_so = MagicMock(spec=SalesOrder)
    mock_so.order_no = "SO-T2-CONFIRM"
    mock_so.status = SalesOrderStatus.NOT_SHIPPED
    mock_so.currency = "USD"
    mock_so.sales_order_rows = [_make_so_row_with_price(1, 100, 5.0, "10.00")]

    mock_get_response = MagicMock(status_code=200, parsed=mock_so)

    from katana_public_api_client.api.sales_order import get_sales_order
    from katana_public_api_client.api.sales_order_fulfillment import (
        create_sales_order_fulfillment,
    )
    from katana_public_api_client.models import SalesOrderFulfillment

    cast(Any, get_sales_order).asyncio_detailed = AsyncMock(
        return_value=mock_get_response
    )

    fulfillment_obj = MagicMock(spec=SalesOrderFulfillment)
    fulfillment_obj.id = 7777
    mock_create_response = MagicMock(status_code=200, parsed=fulfillment_obj)
    cast(Any, create_sales_order_fulfillment).asyncio_detailed = AsyncMock(
        return_value=mock_create_response
    )

    cached_variant = MagicMock()
    cached_variant.id = 100
    cached_variant.sku = "WIDGET-100"
    cached_variant.display_name = "Big Widget / Red"
    cached_variant.product_id = None
    cached_variant.material_id = None
    cached_variant.config_attributes = []

    async def _get_many(model_cls, ids, **_kw):
        if model_cls is CachedVariant and 100 in set(ids):
            return {100: cached_variant}
        return {}

    lifespan_ctx.typed_cache.catalog.get_many_by_ids = AsyncMock(side_effect=_get_many)

    request = FulfillOrderRequest(order_id=5678, order_type="sales", preview=False)
    result = await _fulfill_order_impl(request, context)

    assert result.is_preview is False
    assert result.status == "DELIVERED"
    assert len(result.fulfilled_rows) == 1
    assert result.fulfilled_rows[0].sku == "WIDGET-100"
    assert result.fulfilled_rows[0].row_total == 50.0
    assert result.rows_count == 1
    assert result.total_quantity == 5.0
    assert result.total_value == 50.0
    assert result.currency == "USD"
    assert result.katana_url is not None
    assert result.katana_url.endswith("/salesorder/5678")


# Inventory-Ordering Guard Tests (#787)
# ============================================================================
#
# Strict invariant: MO ``done_date`` must land **before** SO ``picked_date``.
# Equal timestamps are unsafe (Probe case A: non-deterministic ordering); SO
# before MO is unsafe (Probe case B: deterministic negative balance recorded
# on inventory_movements). Both branches BLOCK on violation; the override
# flag ``acknowledge_inventory_ordering`` demotes the BLOCK to a non-BLOCK
# warning so the apply proceeds.


def _mock_mo_response(*, done_date: Any = None) -> MagicMock:
    """Build a ``GET /manufacturing_orders/{id}`` response carrying done_date.

    The inventory-ordering guard's SO branch fans out one of these per
    linked MO ID to compare done_date against the proposed SO picked_date.
    ``done_date`` accepts ``datetime``, ``None``, or ``UNSET`` (the wire
    sentinel; ``unwrap_unset`` normalizes both to None).
    """
    mo = MagicMock(spec=ManufacturingOrder)
    mo.done_date = done_date
    return MagicMock(status_code=200, parsed=mo)


def _mock_so_response(*, picked_date: Any = None) -> MagicMock:
    """Build a ``GET /sales_orders/{id}`` response carrying header picked_date.

    The inventory-ordering guard's MO branch reads the linked SO header
    ``picked_date`` (cascading-update field; rewrites every fulfillment's
    picked_date per the spec). ``picked_date`` accepts ``datetime``,
    ``None``, or ``UNSET``.
    """
    so = MagicMock(spec=SalesOrder)
    so.picked_date = picked_date
    so.sales_order_rows = []  # not needed for the guard
    return MagicMock(status_code=200, parsed=so)


# --- SO branch -------------------------------------------------------------


@pytest.mark.asyncio
async def test_so_inventory_ordering_blocks_when_equal_to_mo_done_date():
    """SO picked_date == MO done_date → BLOCK (non-deterministic ordering)."""
    context, lifespan_ctx = create_mock_context()
    _wire_non_serial_tracked_cache(lifespan_ctx, variant_id=100, sku="PLAIN-IO")

    mo_done = datetime(2026, 5, 1, 20, 30, tzinfo=UTC)
    mock_so = MagicMock(spec=SalesOrder)
    mock_so.order_no = "SO-IO-EQ"
    mock_so.status = SalesOrderStatus.NOT_SHIPPED
    mock_so.sales_order_rows = [
        _make_so_row(1, 100, 1.0, linked_manufacturing_order_id=555),
    ]

    from katana_public_api_client.api.manufacturing_order import (
        get_manufacturing_order,
    )
    from katana_public_api_client.api.sales_order import get_sales_order

    cast(Any, get_sales_order).asyncio_detailed = AsyncMock(
        return_value=MagicMock(status_code=200, parsed=mock_so)
    )
    cast(Any, get_manufacturing_order).asyncio_detailed = AsyncMock(
        return_value=_mock_mo_response(done_date=mo_done)
    )

    request = FulfillOrderRequest(
        order_id=42, order_type="sales", preview=True, completed_at=mo_done
    )
    result = await _fulfill_order_impl(request, context)

    block_warnings = [w for w in result.warnings if w.startswith("BLOCK:")]
    assert len(block_warnings) == 1
    assert "not after linked manufacturing order 555 done_date" in block_warnings[0]


@pytest.mark.asyncio
async def test_so_inventory_ordering_clean_when_one_minute_after():
    """SO picked_date = MO done_date + 1 min → no BLOCK (safe ordering)."""
    context, lifespan_ctx = create_mock_context()
    _wire_non_serial_tracked_cache(lifespan_ctx, variant_id=100, sku="PLAIN-IO")

    mo_done = datetime(2026, 5, 1, 20, 30, tzinfo=UTC)
    so_picked = mo_done + timedelta(minutes=1)
    mock_so = MagicMock(spec=SalesOrder)
    mock_so.order_no = "SO-IO-OK"
    mock_so.status = SalesOrderStatus.NOT_SHIPPED
    mock_so.sales_order_rows = [
        _make_so_row(1, 100, 1.0, linked_manufacturing_order_id=555),
    ]

    from katana_public_api_client.api.manufacturing_order import (
        get_manufacturing_order,
    )
    from katana_public_api_client.api.sales_order import get_sales_order

    cast(Any, get_sales_order).asyncio_detailed = AsyncMock(
        return_value=MagicMock(status_code=200, parsed=mock_so)
    )
    cast(Any, get_manufacturing_order).asyncio_detailed = AsyncMock(
        return_value=_mock_mo_response(done_date=mo_done)
    )

    request = FulfillOrderRequest(
        order_id=42, order_type="sales", preview=True, completed_at=so_picked
    )
    result = await _fulfill_order_impl(request, context)

    assert not [w for w in result.warnings if "inventory_movements ledger" in w], (
        result.warnings
    )


@pytest.mark.asyncio
async def test_so_inventory_ordering_blocks_when_one_minute_before_mo_done():
    """SO picked_date = MO done_date - 1 min → BLOCK (Probe case B,
    deterministic negative balance on the inventory_movements ledger).
    """
    context, lifespan_ctx = create_mock_context()
    _wire_non_serial_tracked_cache(lifespan_ctx, variant_id=100, sku="PLAIN-IO")

    mo_done = datetime(2026, 5, 1, 20, 30, tzinfo=UTC)
    so_picked = mo_done - timedelta(minutes=1)
    mock_so = MagicMock(spec=SalesOrder)
    mock_so.order_no = "SO-IO-BAD"
    mock_so.status = SalesOrderStatus.NOT_SHIPPED
    mock_so.sales_order_rows = [
        _make_so_row(1, 100, 1.0, linked_manufacturing_order_id=555),
    ]

    from katana_public_api_client.api.manufacturing_order import (
        get_manufacturing_order,
    )
    from katana_public_api_client.api.sales_order import get_sales_order

    cast(Any, get_sales_order).asyncio_detailed = AsyncMock(
        return_value=MagicMock(status_code=200, parsed=mock_so)
    )
    cast(Any, get_manufacturing_order).asyncio_detailed = AsyncMock(
        return_value=_mock_mo_response(done_date=mo_done)
    )

    request = FulfillOrderRequest(
        order_id=42, order_type="sales", preview=True, completed_at=so_picked
    )
    result = await _fulfill_order_impl(request, context)

    block_warnings = [w for w in result.warnings if w.startswith("BLOCK:")]
    assert len(block_warnings) == 1
    assert "transient negative inventory" in block_warnings[0]
    # Suggested correction is mo_done + 1 minute.
    suggested = (mo_done + timedelta(minutes=1)).isoformat()
    assert suggested in block_warnings[0]


@pytest.mark.asyncio
async def test_so_inventory_ordering_override_demotes_block_and_applies():
    """acknowledge_inventory_ordering=True demotes BLOCK to non-BLOCK,
    apply proceeds with the fulfillment POST firing exactly once.
    """
    context, lifespan_ctx = create_mock_context()
    _wire_non_serial_tracked_cache(lifespan_ctx, variant_id=100, sku="PLAIN-IO")

    mo_done = datetime(2026, 5, 1, 20, 30, tzinfo=UTC)
    mock_so = MagicMock(spec=SalesOrder)
    mock_so.order_no = "SO-IO-ACK"
    mock_so.status = SalesOrderStatus.NOT_SHIPPED
    mock_so.sales_order_rows = [
        _make_so_row(1, 100, 1.0, linked_manufacturing_order_id=555),
    ]

    from katana_public_api_client.api.manufacturing_order import (
        get_manufacturing_order,
    )
    from katana_public_api_client.api.sales_order import get_sales_order
    from katana_public_api_client.api.sales_order_fulfillment import (
        create_sales_order_fulfillment,
    )
    from katana_public_api_client.models import SalesOrderFulfillment

    cast(Any, get_sales_order).asyncio_detailed = AsyncMock(
        return_value=MagicMock(status_code=200, parsed=mock_so)
    )
    cast(Any, get_manufacturing_order).asyncio_detailed = AsyncMock(
        return_value=_mock_mo_response(done_date=mo_done)
    )
    fulfillment_obj = MagicMock(spec=SalesOrderFulfillment)
    fulfillment_obj.id = 99999
    create_mock = AsyncMock(
        return_value=MagicMock(status_code=200, parsed=fulfillment_obj)
    )
    cast(Any, create_sales_order_fulfillment).asyncio_detailed = create_mock

    request = FulfillOrderRequest(
        order_id=42,
        order_type="sales",
        preview=False,
        completed_at=mo_done,  # equal → would BLOCK without override
        acknowledge_inventory_ordering=True,
    )
    result = await _fulfill_order_impl(request, context)

    # Apply proceeded — BLOCK was demoted.
    assert result.status == "DELIVERED"
    create_mock.assert_called_once()
    # The warning still surfaces (demoted to non-BLOCK).
    assert not [w for w in result.warnings if w.startswith("BLOCK:")]
    assert any("WARNING (acknowledged):" in w for w in result.warnings)


@pytest.mark.asyncio
async def test_so_inventory_ordering_silent_when_linked_mo_done_date_unset():
    """Linked MO with done_date = UNSET → guard silent (the future MO close
    will be subject to its own branch's guard).
    """
    context, lifespan_ctx = create_mock_context()
    _wire_non_serial_tracked_cache(lifespan_ctx, variant_id=100, sku="PLAIN-IO")

    mock_so = MagicMock(spec=SalesOrder)
    mock_so.order_no = "SO-IO-UNSET"
    mock_so.status = SalesOrderStatus.NOT_SHIPPED
    mock_so.sales_order_rows = [
        _make_so_row(1, 100, 1.0, linked_manufacturing_order_id=555),
    ]

    from katana_public_api_client.api.manufacturing_order import (
        get_manufacturing_order,
    )
    from katana_public_api_client.api.sales_order import get_sales_order
    from katana_public_api_client.client_types import UNSET

    cast(Any, get_sales_order).asyncio_detailed = AsyncMock(
        return_value=MagicMock(status_code=200, parsed=mock_so)
    )
    cast(Any, get_manufacturing_order).asyncio_detailed = AsyncMock(
        return_value=_mock_mo_response(done_date=UNSET)
    )

    request = FulfillOrderRequest(
        order_id=42,
        order_type="sales",
        preview=True,
        completed_at=datetime(2026, 5, 1, 20, 30, tzinfo=UTC),
    )
    result = await _fulfill_order_impl(request, context)

    assert not [w for w in result.warnings if "inventory_movements ledger" in w]


@pytest.mark.asyncio
async def test_so_inventory_ordering_silent_when_no_linked_mo():
    """SO row with linked_manufacturing_order_id=None → guard silent."""
    context, lifespan_ctx = create_mock_context()
    _wire_non_serial_tracked_cache(lifespan_ctx, variant_id=100, sku="PLAIN-IO")

    mock_so = MagicMock(spec=SalesOrder)
    mock_so.order_no = "SO-IO-NOMO"
    mock_so.status = SalesOrderStatus.NOT_SHIPPED
    mock_so.sales_order_rows = [_make_so_row(1, 100, 1.0)]  # no linked MO

    from katana_public_api_client.api.manufacturing_order import (
        get_manufacturing_order,
    )
    from katana_public_api_client.api.sales_order import get_sales_order

    cast(Any, get_sales_order).asyncio_detailed = AsyncMock(
        return_value=MagicMock(status_code=200, parsed=mock_so)
    )
    get_mo_mock = AsyncMock()
    cast(Any, get_manufacturing_order).asyncio_detailed = get_mo_mock

    request = FulfillOrderRequest(
        order_id=42,
        order_type="sales",
        preview=True,
        completed_at=datetime(2026, 5, 1, 20, 30, tzinfo=UTC),
    )
    result = await _fulfill_order_impl(request, context)

    assert not [w for w in result.warnings if "inventory_movements ledger" in w]
    # No linked MOs → no MO lookups fired (guard short-circuits).
    get_mo_mock.assert_not_called()


@pytest.mark.asyncio
async def test_so_inventory_ordering_silent_when_completed_at_is_none():
    """completed_at=None (server-time) → guard silent regardless of links."""
    context, lifespan_ctx = create_mock_context()
    _wire_non_serial_tracked_cache(lifespan_ctx, variant_id=100, sku="PLAIN-IO")

    mock_so = MagicMock(spec=SalesOrder)
    mock_so.order_no = "SO-IO-SVR"
    mock_so.status = SalesOrderStatus.NOT_SHIPPED
    mock_so.sales_order_rows = [
        _make_so_row(1, 100, 1.0, linked_manufacturing_order_id=555),
    ]

    from katana_public_api_client.api.manufacturing_order import (
        get_manufacturing_order,
    )
    from katana_public_api_client.api.sales_order import get_sales_order

    cast(Any, get_sales_order).asyncio_detailed = AsyncMock(
        return_value=MagicMock(status_code=200, parsed=mock_so)
    )
    get_mo_mock = AsyncMock()
    cast(Any, get_manufacturing_order).asyncio_detailed = get_mo_mock

    request = FulfillOrderRequest(order_id=42, order_type="sales", preview=True)
    result = await _fulfill_order_impl(request, context)

    assert not [w for w in result.warnings if "inventory_movements ledger" in w]
    # No completed_at → guard short-circuits before fanning out.
    get_mo_mock.assert_not_called()


@pytest.mark.asyncio
async def test_so_inventory_ordering_two_mos_one_violates():
    """Two linked MOs, one safe one violating → BLOCK fires once
    (named for the violator) and clean for the other.
    """
    context, lifespan_ctx = create_mock_context()
    _wire_non_serial_tracked_cache(lifespan_ctx, variant_id=100, sku="PLAIN-IO")

    so_picked = datetime(2026, 5, 1, 20, 30, tzinfo=UTC)
    mo_safe = so_picked - timedelta(minutes=5)  # safe — 5 min before
    mo_violating = so_picked  # equal → BLOCK

    mock_so = MagicMock(spec=SalesOrder)
    mock_so.order_no = "SO-IO-MIX"
    mock_so.status = SalesOrderStatus.NOT_SHIPPED
    mock_so.sales_order_rows = [
        _make_so_row(1, 100, 1.0, linked_manufacturing_order_id=111),
        _make_so_row(2, 100, 1.0, linked_manufacturing_order_id=222),
    ]

    async def _get_mo(**kwargs):
        # The API call uses ``id=...`` (mirrors the generated client); accept
        # via kwargs to avoid shadowing the builtin in the lambda-like helper.
        if kwargs["id"] == 111:
            return _mock_mo_response(done_date=mo_safe)
        return _mock_mo_response(done_date=mo_violating)

    from katana_public_api_client.api.manufacturing_order import (
        get_manufacturing_order,
    )
    from katana_public_api_client.api.sales_order import get_sales_order

    cast(Any, get_sales_order).asyncio_detailed = AsyncMock(
        return_value=MagicMock(status_code=200, parsed=mock_so)
    )
    cast(Any, get_manufacturing_order).asyncio_detailed = AsyncMock(side_effect=_get_mo)

    request = FulfillOrderRequest(
        order_id=42, order_type="sales", preview=True, completed_at=so_picked
    )
    result = await _fulfill_order_impl(request, context)

    block_warnings = [w for w in result.warnings if w.startswith("BLOCK:")]
    assert len(block_warnings) == 1
    # Names the violator (MO 222), not the safe one (MO 111).
    assert "manufacturing order 222" in block_warnings[0]
    assert "manufacturing order 111" not in block_warnings[0]


@pytest.mark.asyncio
async def test_fetch_linked_mo_done_dates_deterministic_ordering():
    """Regression: ``_fetch_linked_mo_done_dates`` must pair responses to
    MO ids deterministically, even though the input is a ``set``.

    The pre-fix code iterated ``mo_ids`` (a set) twice — once to build
    the ``gather()`` call list, once to ``zip`` responses back to ids.
    Set iteration order is not guaranteed by the language, so a future
    Python or a different hash seed could mis-associate responses,
    silently blocking the wrong order or missing a real violation.

    Verify by passing a set with multiple ids and asserting the
    returned mapping pairs each id to its OWN ``done_date`` value.
    """
    from katana_mcp.tools.foundation.orders import _fetch_linked_mo_done_dates

    # Distinct done_date per id so we can detect mis-pairing.
    dones = {
        111: datetime(2026, 5, 1, 10, 0, tzinfo=UTC),
        222: datetime(2026, 5, 1, 11, 0, tzinfo=UTC),
        333: datetime(2026, 5, 1, 12, 0, tzinfo=UTC),
        444: datetime(2026, 5, 1, 13, 0, tzinfo=UTC),
    }

    async def _get_mo(**kwargs):
        return _mock_mo_response(done_date=dones[kwargs["id"]])

    from katana_public_api_client.api.manufacturing_order import (
        get_manufacturing_order,
    )

    cast(Any, get_manufacturing_order).asyncio_detailed = AsyncMock(side_effect=_get_mo)

    services = MagicMock()
    services.client = MagicMock()

    result = await _fetch_linked_mo_done_dates(services, set(dones.keys()))

    # Every id must map to its own done_date, not another id's.
    assert result == dones


# --- MO branch -------------------------------------------------------------


@pytest.mark.asyncio
async def test_mo_inventory_ordering_blocks_when_equal_to_so_picked():
    """MO done_date == linked SO picked_date → BLOCK."""
    context, lifespan_ctx = create_mock_context()
    _wire_non_serial_tracked_cache(lifespan_ctx, variant_id=555, sku="PLAIN-IOM")

    so_picked = datetime(2026, 5, 1, 20, 30, tzinfo=UTC)
    mock_mo = _make_serial_tracked_mo(
        order_no="MO-IO-EQ",
        variant_id=555,
        actual_quantity=1.0,
        sales_order_id=900,
    )

    from katana_public_api_client.api.manufacturing_order import (
        get_manufacturing_order,
    )
    from katana_public_api_client.api.sales_order import get_sales_order

    cast(Any, get_manufacturing_order).asyncio_detailed = AsyncMock(
        return_value=MagicMock(status_code=200, parsed=mock_mo)
    )
    cast(Any, get_sales_order).asyncio_detailed = AsyncMock(
        return_value=_mock_so_response(picked_date=so_picked)
    )

    request = FulfillOrderRequest(
        order_id=1234,
        order_type="manufacturing",
        preview=True,
        completed_at=so_picked,
    )
    result = await _fulfill_order_impl(request, context)

    block_warnings = [w for w in result.warnings if w.startswith("BLOCK:")]
    inv_blocks = [w for w in block_warnings if "inventory_movements" in w]
    assert len(inv_blocks) == 1
    assert "linked sales order 900 picked_date" in inv_blocks[0]


@pytest.mark.asyncio
async def test_mo_inventory_ordering_blocks_when_after_so_picked():
    """MO done_date > linked SO picked_date → BLOCK."""
    context, lifespan_ctx = create_mock_context()
    _wire_non_serial_tracked_cache(lifespan_ctx, variant_id=555, sku="PLAIN-IOM")

    so_picked = datetime(2026, 5, 1, 20, 30, tzinfo=UTC)
    mo_done = so_picked + timedelta(minutes=1)
    mock_mo = _make_serial_tracked_mo(
        order_no="MO-IO-AFT",
        variant_id=555,
        actual_quantity=1.0,
        sales_order_id=900,
    )

    from katana_public_api_client.api.manufacturing_order import (
        get_manufacturing_order,
    )
    from katana_public_api_client.api.sales_order import get_sales_order

    cast(Any, get_manufacturing_order).asyncio_detailed = AsyncMock(
        return_value=MagicMock(status_code=200, parsed=mock_mo)
    )
    cast(Any, get_sales_order).asyncio_detailed = AsyncMock(
        return_value=_mock_so_response(picked_date=so_picked)
    )

    request = FulfillOrderRequest(
        order_id=1234,
        order_type="manufacturing",
        preview=True,
        completed_at=mo_done,
    )
    result = await _fulfill_order_impl(request, context)

    block_warnings = [w for w in result.warnings if w.startswith("BLOCK:")]
    assert any("inventory_movements" in w for w in block_warnings)


@pytest.mark.asyncio
async def test_mo_inventory_ordering_clean_when_before_so_picked():
    """MO done_date < linked SO picked_date → no BLOCK (safe ordering)."""
    context, lifespan_ctx = create_mock_context()
    _wire_non_serial_tracked_cache(lifespan_ctx, variant_id=555, sku="PLAIN-IOM")

    so_picked = datetime(2026, 5, 1, 20, 30, tzinfo=UTC)
    mo_done = so_picked - timedelta(minutes=1)
    mock_mo = _make_serial_tracked_mo(
        order_no="MO-IO-OK",
        variant_id=555,
        actual_quantity=1.0,
        sales_order_id=900,
    )

    from katana_public_api_client.api.manufacturing_order import (
        get_manufacturing_order,
    )
    from katana_public_api_client.api.sales_order import get_sales_order

    cast(Any, get_manufacturing_order).asyncio_detailed = AsyncMock(
        return_value=MagicMock(status_code=200, parsed=mock_mo)
    )
    cast(Any, get_sales_order).asyncio_detailed = AsyncMock(
        return_value=_mock_so_response(picked_date=so_picked)
    )

    request = FulfillOrderRequest(
        order_id=1234,
        order_type="manufacturing",
        preview=True,
        completed_at=mo_done,
    )
    result = await _fulfill_order_impl(request, context)

    assert not [w for w in result.warnings if "inventory_movements" in w]


@pytest.mark.asyncio
async def test_mo_inventory_ordering_override_demotes_block_and_applies():
    """acknowledge_inventory_ordering=True demotes BLOCK to non-BLOCK,
    apply proceeds with the production POST firing exactly once.
    """
    context, lifespan_ctx = create_mock_context()
    _wire_non_serial_tracked_cache(lifespan_ctx, variant_id=555, sku="PLAIN-IOM")

    so_picked = datetime(2026, 5, 1, 20, 30, tzinfo=UTC)
    mock_mo = _make_serial_tracked_mo(
        order_no="MO-IO-ACK",
        variant_id=555,
        actual_quantity=1.0,
        sales_order_id=900,
    )
    mock_done_mo = MagicMock(spec=ManufacturingOrder)
    mock_done_mo.order_no = "MO-IO-ACK"
    mock_done_mo.status = ManufacturingOrderStatus.DONE
    mock_done_mo.sales_order_id = 900

    from katana_public_api_client.api.manufacturing_order import (
        get_manufacturing_order,
    )
    from katana_public_api_client.api.manufacturing_order_production import (
        create_manufacturing_order_production,
    )
    from katana_public_api_client.api.sales_order import get_sales_order
    from katana_public_api_client.models import ManufacturingOrderProduction

    cast(Any, get_manufacturing_order).asyncio_detailed = AsyncMock(
        side_effect=[
            MagicMock(status_code=200, parsed=mock_mo),
            MagicMock(status_code=200, parsed=mock_done_mo),
        ]
    )
    cast(Any, get_sales_order).asyncio_detailed = AsyncMock(
        return_value=_mock_so_response(picked_date=so_picked)
    )
    mock_production = MagicMock(spec=ManufacturingOrderProduction)
    mock_production.id = 9001
    create_mock = AsyncMock(
        return_value=MagicMock(status_code=200, parsed=mock_production)
    )
    cast(Any, create_manufacturing_order_production).asyncio_detailed = create_mock

    request = FulfillOrderRequest(
        order_id=1234,
        order_type="manufacturing",
        preview=False,
        completed_at=so_picked,  # equal → would BLOCK without override
        acknowledge_inventory_ordering=True,
    )
    result = await _fulfill_order_impl(request, context)

    assert result.status == "DONE"
    create_mock.assert_called_once()
    assert not [w for w in result.warnings if w.startswith("BLOCK:")]
    assert any("WARNING (acknowledged):" in w for w in result.warnings)


@pytest.mark.asyncio
async def test_mo_inventory_ordering_silent_when_no_linked_so():
    """MO with sales_order_id=None → guard silent (no linked SO to check)."""
    context, lifespan_ctx = create_mock_context()
    _wire_non_serial_tracked_cache(lifespan_ctx, variant_id=555, sku="PLAIN-IOM")

    mock_mo = _make_serial_tracked_mo(
        order_no="MO-IO-NOSO",
        variant_id=555,
        actual_quantity=1.0,
        sales_order_id=None,
    )

    from katana_public_api_client.api.manufacturing_order import (
        get_manufacturing_order,
    )
    from katana_public_api_client.api.sales_order import get_sales_order

    cast(Any, get_manufacturing_order).asyncio_detailed = AsyncMock(
        return_value=MagicMock(status_code=200, parsed=mock_mo)
    )
    get_so_mock = AsyncMock()
    cast(Any, get_sales_order).asyncio_detailed = get_so_mock

    request = FulfillOrderRequest(
        order_id=1234,
        order_type="manufacturing",
        preview=True,
        completed_at=datetime(2026, 5, 1, 20, 30, tzinfo=UTC),
    )
    result = await _fulfill_order_impl(request, context)

    assert not [w for w in result.warnings if "inventory_movements" in w]
    get_so_mock.assert_not_called()


@pytest.mark.asyncio
async def test_mo_inventory_ordering_silent_when_linked_so_picked_unset():
    """Linked SO with picked_date=UNSET (not yet fulfilled) → guard silent
    (the future SO fulfill will be subject to the SO-branch guard).
    """
    context, lifespan_ctx = create_mock_context()
    _wire_non_serial_tracked_cache(lifespan_ctx, variant_id=555, sku="PLAIN-IOM")

    mock_mo = _make_serial_tracked_mo(
        order_no="MO-IO-SOUN",
        variant_id=555,
        actual_quantity=1.0,
        sales_order_id=900,
    )

    from katana_public_api_client.api.manufacturing_order import (
        get_manufacturing_order,
    )
    from katana_public_api_client.api.sales_order import get_sales_order
    from katana_public_api_client.client_types import UNSET

    cast(Any, get_manufacturing_order).asyncio_detailed = AsyncMock(
        return_value=MagicMock(status_code=200, parsed=mock_mo)
    )
    cast(Any, get_sales_order).asyncio_detailed = AsyncMock(
        return_value=_mock_so_response(picked_date=UNSET)
    )

    request = FulfillOrderRequest(
        order_id=1234,
        order_type="manufacturing",
        preview=True,
        completed_at=datetime(2026, 5, 1, 20, 30, tzinfo=UTC),
    )
    result = await _fulfill_order_impl(request, context)

    assert not [w for w in result.warnings if "inventory_movements" in w]


@pytest.mark.asyncio
async def test_mo_inventory_ordering_silent_when_completed_at_is_none():
    """MO completed_at=None (server-time) → guard silent."""
    context, lifespan_ctx = create_mock_context()
    _wire_non_serial_tracked_cache(lifespan_ctx, variant_id=555, sku="PLAIN-IOM")

    mock_mo = _make_serial_tracked_mo(
        order_no="MO-IO-SVR",
        variant_id=555,
        actual_quantity=1.0,
        sales_order_id=900,
    )

    from katana_public_api_client.api.manufacturing_order import (
        get_manufacturing_order,
    )
    from katana_public_api_client.api.sales_order import get_sales_order

    cast(Any, get_manufacturing_order).asyncio_detailed = AsyncMock(
        return_value=MagicMock(status_code=200, parsed=mock_mo)
    )
    get_so_mock = AsyncMock()
    cast(Any, get_sales_order).asyncio_detailed = get_so_mock

    request = FulfillOrderRequest(
        order_id=1234, order_type="manufacturing", preview=True
    )
    result = await _fulfill_order_impl(request, context)

    assert not [w for w in result.warnings if "inventory_movements" in w]
    get_so_mock.assert_not_called()


@pytest.mark.asyncio
async def test_mo_inventory_ordering_apply_refuses_without_override():
    """preview=False on a violating MO without override → refused, production
    POST never fired (defense-in-depth: BLOCK propagates to apply gate).
    """
    context, lifespan_ctx = create_mock_context()
    _wire_non_serial_tracked_cache(lifespan_ctx, variant_id=555, sku="PLAIN-IOM")

    so_picked = datetime(2026, 5, 1, 20, 30, tzinfo=UTC)
    mock_mo = _make_serial_tracked_mo(
        order_no="MO-IO-REF",
        variant_id=555,
        actual_quantity=1.0,
        sales_order_id=900,
    )

    from katana_public_api_client.api.manufacturing_order import (
        get_manufacturing_order,
    )
    from katana_public_api_client.api.manufacturing_order_production import (
        create_manufacturing_order_production,
    )
    from katana_public_api_client.api.sales_order import get_sales_order

    cast(Any, get_manufacturing_order).asyncio_detailed = AsyncMock(
        return_value=MagicMock(status_code=200, parsed=mock_mo)
    )
    cast(Any, get_sales_order).asyncio_detailed = AsyncMock(
        return_value=_mock_so_response(picked_date=so_picked)
    )
    create_mock = AsyncMock()
    cast(Any, create_manufacturing_order_production).asyncio_detailed = create_mock

    request = FulfillOrderRequest(
        order_id=1234,
        order_type="manufacturing",
        preview=False,
        completed_at=so_picked,  # equal → BLOCK
    )
    result = await _fulfill_order_impl(request, context)

    assert "Refused" in result.message
    create_mock.assert_not_called()


# --- Helper unit tests -----------------------------------------------------


def test_inventory_ordering_helper_so_silent_on_none_picked():
    """Helper unit: so_picked_at=None → empty list, regardless of linked MOs."""
    from katana_mcp.tools.foundation.orders import (
        _build_inventory_ordering_warnings_so,
    )

    warnings = _build_inventory_ordering_warnings_so(
        order_number="SO-X",
        so_picked_at=None,
        linked_mo_done_dates={555: datetime(2026, 5, 1, tzinfo=UTC)},
        acknowledged=False,
    )
    assert warnings == []


def test_inventory_ordering_helper_so_silent_on_empty_links():
    """Helper unit: empty linked-MO map → empty list."""
    from katana_mcp.tools.foundation.orders import (
        _build_inventory_ordering_warnings_so,
    )

    warnings = _build_inventory_ordering_warnings_so(
        order_number="SO-X",
        so_picked_at=datetime(2026, 5, 1, tzinfo=UTC),
        linked_mo_done_dates={},
        acknowledged=False,
    )
    assert warnings == []


def test_inventory_ordering_helper_mo_silent_on_unset_so_picked():
    """Helper unit: linked_so_picked_at=None → empty list."""
    from katana_mcp.tools.foundation.orders import (
        _build_inventory_ordering_warnings_mo,
    )

    warnings = _build_inventory_ordering_warnings_mo(
        order_number="MO-X",
        mo_done_at=datetime(2026, 5, 1, tzinfo=UTC),
        linked_so_id=900,
        linked_so_picked_at=None,
        acknowledged=False,
    )
    assert warnings == []


def test_inventory_ordering_helper_mo_acknowledged_demotes_prefix():
    """Helper unit: acknowledged=True swaps BLOCK: → WARNING (acknowledged):."""
    from katana_mcp.tools.foundation.orders import (
        _build_inventory_ordering_warnings_mo,
    )

    ts = datetime(2026, 5, 1, tzinfo=UTC)
    warnings = _build_inventory_ordering_warnings_mo(
        order_number="MO-X",
        mo_done_at=ts,
        linked_so_id=900,
        linked_so_picked_at=ts,  # equal → would violate
        acknowledged=True,
    )
    assert len(warnings) == 1
    assert warnings[0].startswith("WARNING (acknowledged):")
    assert not warnings[0].startswith("BLOCK:")


def test_inventory_ordering_helper_override_clause_only_when_blocking():
    """The "Pass acknowledge_inventory_ordering=true to override" instruction
    only appears in the BLOCK variant — including it in the acknowledged
    variant would be misleading (the override is already in effect)."""
    from katana_mcp.tools.foundation.orders import (
        _build_inventory_ordering_warnings_mo,
        _build_inventory_ordering_warnings_so,
    )

    ts = datetime(2026, 5, 1, tzinfo=UTC)
    override_phrase = "acknowledge_inventory_ordering=true to override"

    so_blocking = _build_inventory_ordering_warnings_so(
        order_number="SO-X",
        so_picked_at=ts,
        linked_mo_done_dates={555: ts},
        acknowledged=False,
    )
    so_acknowledged = _build_inventory_ordering_warnings_so(
        order_number="SO-X",
        so_picked_at=ts,
        linked_mo_done_dates={555: ts},
        acknowledged=True,
    )
    mo_blocking = _build_inventory_ordering_warnings_mo(
        order_number="MO-X",
        mo_done_at=ts,
        linked_so_id=900,
        linked_so_picked_at=ts,
        acknowledged=False,
    )
    mo_acknowledged = _build_inventory_ordering_warnings_mo(
        order_number="MO-X",
        mo_done_at=ts,
        linked_so_id=900,
        linked_so_picked_at=ts,
        acknowledged=True,
    )

    assert override_phrase in so_blocking[0]
    assert override_phrase not in so_acknowledged[0]
    assert override_phrase in mo_blocking[0]
    assert override_phrase not in mo_acknowledged[0]
