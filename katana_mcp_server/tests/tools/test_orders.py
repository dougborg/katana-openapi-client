"""Tests for order fulfillment MCP tools."""

from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from katana_mcp.cache import EntityType
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
    """Test fulfill_order confirm mode for manufacturing order."""
    context, _lifespan_ctx = create_mock_context()

    # Mock ManufacturingOrder for get
    mock_mo = MagicMock(spec=ManufacturingOrder)
    mock_mo.order_no = "MO-002"
    mock_mo.status = ManufacturingOrderStatus.IN_PROGRESS

    mock_get_response = MagicMock()
    mock_get_response.status_code = 200
    mock_get_response.parsed = mock_mo

    # Mock ManufacturingOrder for update
    mock_updated_mo = MagicMock(spec=ManufacturingOrder)
    mock_updated_mo.order_no = "MO-002"
    mock_updated_mo.status = ManufacturingOrderStatus.DONE

    mock_update_response = MagicMock()
    mock_update_response.status_code = 200
    mock_update_response.parsed = mock_updated_mo

    # Mock the API calls
    from katana_public_api_client.api.manufacturing_order import (
        get_manufacturing_order,
        update_manufacturing_order,
    )

    cast(Any, get_manufacturing_order).asyncio_detailed = AsyncMock(
        return_value=mock_get_response
    )
    cast(Any, update_manufacturing_order).asyncio_detailed = AsyncMock(
        return_value=mock_update_response
    )

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

    # Verify update was called
    cast(Any, update_manufacturing_order.asyncio_detailed).assert_called_once()


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


def _make_so_row(row_id: int, variant_id: int, quantity: float):
    """Build a SalesOrderRow mock with the fields fulfill_sales_order reads."""
    row = MagicMock()
    row.id = row_id
    row.variant_id = variant_id
    row.quantity = quantity
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
    # Preview now lists the rows that will ship — one entry per SO row.
    assert len(result.inventory_updates) == 2
    assert any("variant 100" in u for u in result.inventory_updates)
    assert any("variant 200" in u for u in result.inventory_updates)
    # Last next_action should mention preview=false.
    assert any("preview=false" in a for a in result.next_actions)


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
    mock_create_response = MagicMock(status_code=201, parsed=fulfillment_obj)
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
    """Test fulfill_order when manufacturing order API returns error."""
    context, _lifespan_ctx = create_mock_context()

    # Mock ManufacturingOrder
    mock_mo = MagicMock(spec=ManufacturingOrder)
    mock_mo.order_no = "MO-005"
    mock_mo.status = ManufacturingOrderStatus.IN_PROGRESS

    mock_get_response = MagicMock()
    mock_get_response.status_code = 200
    mock_get_response.parsed = mock_mo

    # Mock update API returning error
    mock_update_response = MagicMock()
    mock_update_response.status_code = 500
    mock_update_response.parsed = None

    from katana_public_api_client.api.manufacturing_order import (
        get_manufacturing_order,
        update_manufacturing_order,
    )

    cast(Any, get_manufacturing_order).asyncio_detailed = AsyncMock(
        return_value=mock_get_response
    )
    cast(Any, update_manufacturing_order).asyncio_detailed = AsyncMock(
        return_value=mock_update_response
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


def _wire_serial_tracked_cache(
    lifespan_ctx, *, variant_id: int, sku: str, parent_kind: str = "product"
) -> None:
    """Configure the mock cache so a row's variant resolves as serial-tracked.

    ``parent_kind`` selects whether the variant is parented to a product or a
    material — both surface ``serial_tracked`` on the parent.
    """
    parent_id = 9000 + variant_id
    parent_key = f"{parent_kind}_id"
    variant_data = {"id": variant_id, "sku": sku, parent_key: parent_id}
    parent_data = {"id": parent_id, "serial_tracked": True}

    async def _get_many(entity_type: str, ids):
        ids = list(ids or [])
        if entity_type == EntityType.VARIANT and variant_id in ids:
            return {variant_id: variant_data}
        if entity_type == EntityType.PRODUCT and parent_kind == "product":
            return {parent_id: parent_data} if parent_id in ids else {}
        if entity_type == EntityType.MATERIAL and parent_kind == "material":
            return {parent_id: parent_data} if parent_id in ids else {}
        return {}

    lifespan_ctx.cache.get_many_by_ids = AsyncMock(side_effect=_get_many)


@pytest.mark.asyncio
async def test_fulfill_sales_order_preview_blocks_serial_tracked_without_override():
    """Serial-tracked variant + no rows override → BLOCK warning naming the SKU."""
    context, lifespan_ctx = create_mock_context()
    _wire_serial_tracked_cache(lifespan_ctx, variant_id=100, sku="ROCKER-V2")

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
    assert "ROCKER-V2" in block_warnings[0]
    assert "Resolve the issue" in result.next_actions[0]


@pytest.mark.asyncio
async def test_fulfill_sales_order_preview_accepts_serial_override():
    """Serial-tracked variant + matching override → no BLOCK warning, serials in preview."""
    context, lifespan_ctx = create_mock_context()
    _wire_serial_tracked_cache(lifespan_ctx, variant_id=100, sku="ROCKER-V2")

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
    assert any("serials [501]" in u for u in result.inventory_updates)


@pytest.mark.asyncio
async def test_fulfill_sales_order_apply_passes_serials_to_api():
    """Apply with override → POST body row carries serial_numbers."""
    context, lifespan_ctx = create_mock_context()
    _wire_serial_tracked_cache(lifespan_ctx, variant_id=100, sku="ROCKER-V2")

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
    mock_create_response = MagicMock(status_code=201, parsed=fulfillment_obj)
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
async def test_fulfill_sales_order_apply_refuses_serial_tracked_without_override():
    """Direct apply (preview=False) without override → refusal, no API call."""
    context, lifespan_ctx = create_mock_context()
    _wire_serial_tracked_cache(lifespan_ctx, variant_id=100, sku="ROCKER-V2")

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
    _wire_serial_tracked_cache(lifespan_ctx, variant_id=100, sku="ROCKER-V2")

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
    # get_product returns a serial-tracked product.
    variant_obj = MagicMock()
    variant_obj.to_dict = MagicMock(
        return_value={"id": 100, "sku": "ROCKER-V2", "product_id": 9100}
    )
    mock_get_variant_response = MagicMock(status_code=200, parsed=variant_obj)

    product_obj = MagicMock()
    product_obj.to_dict = MagicMock(return_value={"id": 9100, "serial_tracked": True})
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
    assert any("serial-tracked" in w and "ROCKER-V2" in w for w in block_warnings)
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
    _wire_serial_tracked_cache(lifespan_ctx, variant_id=100, sku="ROCKER-V2")

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
    _wire_serial_tracked_cache(lifespan_ctx, variant_id=100, sku="ROCKER-V2")

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

    async def _get_many(entity_type: str, ids):
        ids = list(ids or [])
        if entity_type == EntityType.VARIANT and 100 in ids:
            return {100: {"id": 100, "sku": "PLAIN-WIDGET", "product_id": 9100}}
        if entity_type == EntityType.PRODUCT and 9100 in ids:
            return {9100: {"id": 9100, "serial_tracked": False}}
        return {}

    lifespan_ctx.cache.get_many_by_ids = AsyncMock(side_effect=_get_many)

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
    mock_create_response = MagicMock(status_code=201, parsed=fulfillment_obj)
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
    *, order_no: str, variant_id: int = 100, actual_quantity: float = 1.0
):
    """Build a serial-tracked ManufacturingOrder mock with the fields the tool reads.

    The MO path reads ``order_no``, ``status``, ``variant_id``, and
    ``actual_quantity`` — set them explicitly rather than letting MagicMock
    autogen child mocks (which interact poorly with ``unwrap_unset`` +
    cache lookups by ID).
    """
    mock_mo = MagicMock(spec=ManufacturingOrder)
    mock_mo.order_no = order_no
    mock_mo.status = ManufacturingOrderStatus.IN_PROGRESS
    mock_mo.variant_id = variant_id
    mock_mo.actual_quantity = actual_quantity
    return mock_mo


@pytest.mark.asyncio
async def test_fulfill_manufacturing_order_preview_blocks_serial_tracked_without_serials():
    """Serial-tracked MO + no serial_numbers → BLOCK warning naming the SKU."""
    context, lifespan_ctx = create_mock_context()
    _wire_serial_tracked_cache(lifespan_ctx, variant_id=100, sku="ROCKER-V2")

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
    assert "ROCKER-V2" in block_warnings[0]
    assert "Resolve the issue" in result.next_actions[0]


@pytest.mark.asyncio
async def test_fulfill_manufacturing_order_preview_accepts_serial_numbers():
    """Serial-tracked MO + matching serial_numbers → no BLOCK, serials in preview."""
    context, lifespan_ctx = create_mock_context()
    _wire_serial_tracked_cache(lifespan_ctx, variant_id=100, sku="ROCKER-V2")

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
    """Apply with serial_numbers → update_manufacturing_order body carries them."""
    context, lifespan_ctx = create_mock_context()
    _wire_serial_tracked_cache(lifespan_ctx, variant_id=100, sku="ROCKER-V2")

    mock_mo = _make_serial_tracked_mo(order_no="MO-SN-3", actual_quantity=2.0)
    mock_get_response = MagicMock(status_code=200, parsed=mock_mo)

    mock_updated_mo = MagicMock(spec=ManufacturingOrder)
    mock_updated_mo.order_no = "MO-SN-3"
    mock_updated_mo.status = ManufacturingOrderStatus.DONE
    mock_update_response = MagicMock(status_code=200, parsed=mock_updated_mo)

    from katana_public_api_client.api.manufacturing_order import (
        get_manufacturing_order,
        update_manufacturing_order,
    )

    cast(Any, get_manufacturing_order).asyncio_detailed = AsyncMock(
        return_value=mock_get_response
    )
    update_mock = AsyncMock(return_value=mock_update_response)
    cast(Any, update_manufacturing_order).asyncio_detailed = update_mock

    request = FulfillOrderRequest(
        order_id=42,
        order_type="manufacturing",
        preview=False,
        serial_numbers=[501, 502],
    )
    result = await _fulfill_order_impl(request, context)

    assert result.is_preview is False
    assert result.status == "DONE"
    update_mock.assert_called_once()
    assert update_mock.call_args is not None
    sent_body = update_mock.call_args.kwargs["body"]
    assert sent_body.serial_numbers == [501, 502]


@pytest.mark.asyncio
async def test_fulfill_manufacturing_order_apply_refuses_serial_tracked_without_serials():
    """Direct apply (preview=False) without serial_numbers → refusal, no API call."""
    context, lifespan_ctx = create_mock_context()
    _wire_serial_tracked_cache(lifespan_ctx, variant_id=100, sku="ROCKER-V2")

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
    _wire_serial_tracked_cache(lifespan_ctx, variant_id=100, sku="ROCKER-V2")

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
    _wire_serial_tracked_cache(lifespan_ctx, variant_id=100, sku="ROCKER-V2")

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
    # get_product returns a serial-tracked product.
    variant_obj = MagicMock()
    variant_obj.to_dict = MagicMock(
        return_value={"id": 100, "sku": "ROCKER-V2", "product_id": 9100}
    )
    mock_get_variant_response = MagicMock(status_code=200, parsed=variant_obj)

    product_obj = MagicMock()
    product_obj.to_dict = MagicMock(return_value={"id": 9100, "serial_tracked": True})
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
    assert any("serial-tracked" in w and "ROCKER-V2" in w for w in block_warnings)
    # Verify both API endpoints were hit.
    cast(Any, get_variant.asyncio_detailed).assert_called_once()
    cast(Any, get_product.asyncio_detailed).assert_called_once()


@pytest.mark.asyncio
async def test_fulfill_manufacturing_order_non_serial_tracked_no_change():
    """Non-serial-tracked MO + no serials → behaves as before (no BLOCK,
    apply path passes UNSET for serial_numbers).
    """
    context, lifespan_ctx = create_mock_context()

    async def _get_many(entity_type: str, ids):
        ids = list(ids or [])
        if entity_type == EntityType.VARIANT and 100 in ids:
            return {100: {"id": 100, "sku": "PLAIN-WIDGET", "product_id": 9100}}
        if entity_type == EntityType.PRODUCT and 9100 in ids:
            return {9100: {"id": 9100, "serial_tracked": False}}
        return {}

    lifespan_ctx.cache.get_many_by_ids = AsyncMock(side_effect=_get_many)

    mock_mo = _make_serial_tracked_mo(order_no="MO-SN-7", actual_quantity=2.0)
    mock_get_response = MagicMock(status_code=200, parsed=mock_mo)

    mock_updated_mo = MagicMock(spec=ManufacturingOrder)
    mock_updated_mo.order_no = "MO-SN-7"
    mock_updated_mo.status = ManufacturingOrderStatus.DONE
    mock_update_response = MagicMock(status_code=200, parsed=mock_updated_mo)

    from katana_public_api_client.api.manufacturing_order import (
        get_manufacturing_order,
        update_manufacturing_order,
    )

    cast(Any, get_manufacturing_order).asyncio_detailed = AsyncMock(
        return_value=mock_get_response
    )
    update_mock = AsyncMock(return_value=mock_update_response)
    cast(Any, update_manufacturing_order).asyncio_detailed = update_mock

    request = FulfillOrderRequest(
        order_id=42, order_type="manufacturing", preview=False
    )
    result = await _fulfill_order_impl(request, context)

    assert result.status == "DONE"
    assert not [w for w in result.warnings if w.startswith("BLOCK:")]
    sent_body = update_mock.call_args.kwargs["body"]
    # serial_numbers should be UNSET (omitted from wire), not an empty list.
    from katana_public_api_client.client_types import UNSET

    assert sent_body.serial_numbers is UNSET
