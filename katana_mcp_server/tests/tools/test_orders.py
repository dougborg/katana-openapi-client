"""Tests for order fulfillment MCP tools."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from katana_mcp.tools.foundation.orders import (
    FulfillOrderRequest,
    _fulfill_order_impl,
)

from katana_public_api_client.models import (
    ManufacturingOrder,
    ManufacturingOrderStatus,
    SalesOrder,
)
from katana_public_api_client.models.sales_order_status import SalesOrderStatus
from katana_public_api_client.utils import APIError
from tests.conftest import create_mock_context

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

    get_manufacturing_order.asyncio_detailed = AsyncMock(return_value=mock_response)

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

    get_manufacturing_order.asyncio_detailed = AsyncMock(return_value=mock_get_response)
    update_manufacturing_order.asyncio_detailed = AsyncMock(
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
    update_manufacturing_order.asyncio_detailed.assert_called_once()


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

    get_manufacturing_order.asyncio_detailed = AsyncMock(return_value=mock_response)

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

    get_manufacturing_order.asyncio_detailed = AsyncMock(return_value=mock_response)

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

    get_manufacturing_order.asyncio_detailed = AsyncMock(return_value=mock_response)

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

    get_sales_order.asyncio_detailed = AsyncMock(return_value=mock_response)

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

    get_sales_order.asyncio_detailed = AsyncMock(return_value=mock_get_response)

    from katana_public_api_client.models import SalesOrderFulfillment

    fulfillment_obj = MagicMock(spec=SalesOrderFulfillment)
    fulfillment_obj.id = 9999
    mock_create_response = MagicMock(status_code=201, parsed=fulfillment_obj)
    create_mock = AsyncMock(return_value=mock_create_response)
    create_sales_order_fulfillment.asyncio_detailed = create_mock

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

    get_sales_order.asyncio_detailed = AsyncMock(return_value=mock_response)
    create_mock = AsyncMock()
    create_sales_order_fulfillment.asyncio_detailed = create_mock

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

    get_sales_order.asyncio_detailed = AsyncMock(return_value=mock_response)

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

    get_sales_order.asyncio_detailed = AsyncMock(return_value=mock_response)

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

    get_manufacturing_order.asyncio_detailed = AsyncMock(return_value=mock_get_response)
    update_manufacturing_order.asyncio_detailed = AsyncMock(
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
