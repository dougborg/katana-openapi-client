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
    SalesOrderFulfillment,
)
from katana_public_api_client.models.sales_order_status import SalesOrderStatus

# ============================================================================
# Test Helpers
# ============================================================================


def create_mock_context():
    """Create a mock context with proper FastMCP structure.

    Returns context with request_context.lifespan_context.client accessible.
    The .client attribute is required by get_services(context).
    """
    context = MagicMock()
    mock_request_context = MagicMock()
    mock_lifespan_context = MagicMock()
    mock_lifespan_context.client = MagicMock()  # Required by get_services()
    context.request_context = mock_request_context
    mock_request_context.lifespan_context = mock_lifespan_context
    return context, mock_lifespan_context


# ============================================================================
# Manufacturing Order Tests
# ============================================================================


@pytest.mark.asyncio
async def test_fulfill_manufacturing_order_preview():
    """Test fulfill_order preview mode for manufacturing order."""
    context, lifespan_ctx = create_mock_context()

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
        order_id=1234, order_type="manufacturing", confirm=False
    )
    result = await _fulfill_order_impl(request, context)

    assert result.order_id == 1234
    assert result.order_type == "manufacturing"
    assert result.order_number == "MO-001"
    assert result.status == "IN_PROGRESS"
    assert result.is_preview is True
    assert len(result.inventory_updates) > 0
    assert any("finished goods" in msg.lower() for msg in result.inventory_updates)
    assert "Set confirm=true" in result.next_actions[2]


@pytest.mark.asyncio
async def test_fulfill_manufacturing_order_confirm():
    """Test fulfill_order confirm mode for manufacturing order."""
    context, lifespan_ctx = create_mock_context()

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
        order_id=1234, order_type="manufacturing", confirm=True
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
    context, lifespan_ctx = create_mock_context()

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
        order_id=1234, order_type="manufacturing", confirm=False
    )
    result = await _fulfill_order_impl(request, context)

    assert result.status == "DONE"
    assert result.is_preview is True
    assert any("already completed" in w.lower() for w in result.warnings)

    # Confirm mode - should not try to update
    request = FulfillOrderRequest(
        order_id=1234, order_type="manufacturing", confirm=True
    )
    result = await _fulfill_order_impl(request, context)

    assert result.status == "DONE"
    assert result.is_preview is False
    assert "already completed" in result.message.lower()


@pytest.mark.asyncio
async def test_fulfill_manufacturing_order_blocked():
    """Test fulfill_order preview when manufacturing order is BLOCKED."""
    context, lifespan_ctx = create_mock_context()

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
        order_id=1234, order_type="manufacturing", confirm=False
    )
    result = await _fulfill_order_impl(request, context)

    assert result.status == "BLOCKED"
    assert any("blocked" in w.lower() for w in result.warnings)


@pytest.mark.asyncio
async def test_fulfill_manufacturing_order_not_found():
    """Test fulfill_order when manufacturing order not found."""
    context, lifespan_ctx = create_mock_context()

    # Mock 404 response
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.parsed = None

    from katana_public_api_client.api.manufacturing_order import (
        get_manufacturing_order,
    )

    get_manufacturing_order.asyncio_detailed = AsyncMock(return_value=mock_response)

    request = FulfillOrderRequest(
        order_id=9999, order_type="manufacturing", confirm=False
    )

    with pytest.raises(Exception, match="Failed to fetch manufacturing order"):
        await _fulfill_order_impl(request, context)


# ============================================================================
# Sales Order Tests
# ============================================================================


@pytest.mark.asyncio
async def test_fulfill_sales_order_preview():
    """Test fulfill_order preview mode for sales order."""
    context, lifespan_ctx = create_mock_context()

    # Mock SalesOrder
    mock_so = MagicMock(spec=SalesOrder)
    mock_so.order_no = "SO-001"
    mock_so.status = SalesOrderStatus.NOT_SHIPPED

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.parsed = mock_so

    from katana_public_api_client.api.sales_order import get_sales_order

    get_sales_order.asyncio_detailed = AsyncMock(return_value=mock_response)

    request = FulfillOrderRequest(order_id=5678, order_type="sales", confirm=False)
    result = await _fulfill_order_impl(request, context)

    assert result.order_id == 5678
    assert result.order_type == "sales"
    assert result.order_number == "SO-001"
    assert result.status == "NOT_SHIPPED"
    assert result.is_preview is True
    assert len(result.inventory_updates) > 0
    assert any("inventory" in msg.lower() for msg in result.inventory_updates)
    assert "Set confirm=true" in result.next_actions[2]


@pytest.mark.asyncio
async def test_fulfill_sales_order_confirm():
    """Test fulfill_order confirm mode for sales order."""
    context, lifespan_ctx = create_mock_context()

    # Mock SalesOrder for get
    mock_so = MagicMock(spec=SalesOrder)
    mock_so.order_no = "SO-002"
    mock_so.status = SalesOrderStatus.NOT_SHIPPED

    mock_get_response = MagicMock()
    mock_get_response.status_code = 200
    mock_get_response.parsed = mock_so

    # Mock SalesOrderFulfillment for create
    mock_fulfillment = MagicMock(spec=SalesOrderFulfillment)

    mock_create_response = MagicMock()
    mock_create_response.status_code = 201
    mock_create_response.parsed = mock_fulfillment

    # Mock the API calls
    from katana_public_api_client.api.sales_order import get_sales_order
    from katana_public_api_client.api.sales_order_fulfillment import (
        create_sales_order_fulfillment,
    )

    get_sales_order.asyncio_detailed = AsyncMock(return_value=mock_get_response)
    create_sales_order_fulfillment.asyncio_detailed = AsyncMock(
        return_value=mock_create_response
    )

    request = FulfillOrderRequest(order_id=5678, order_type="sales", confirm=True)
    result = await _fulfill_order_impl(request, context)

    assert result.order_id == 5678
    assert result.order_type == "sales"
    assert result.order_number == "SO-002"
    assert result.status == "FULFILLED"
    assert result.is_preview is False
    assert "fulfilled" in result.message.lower()

    # Verify fulfillment was created
    create_sales_order_fulfillment.asyncio_detailed.assert_called_once()


@pytest.mark.asyncio
async def test_fulfill_sales_order_already_fulfilled():
    """Test fulfill_order when sales order is already DELIVERED."""
    context, lifespan_ctx = create_mock_context()

    # Mock SalesOrder already DELIVERED
    mock_so = MagicMock(spec=SalesOrder)
    mock_so.order_no = "SO-003"
    mock_so.status = SalesOrderStatus.DELIVERED

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.parsed = mock_so

    from katana_public_api_client.api.sales_order import get_sales_order

    get_sales_order.asyncio_detailed = AsyncMock(return_value=mock_response)

    # Preview mode
    request = FulfillOrderRequest(order_id=5678, order_type="sales", confirm=False)
    result = await _fulfill_order_impl(request, context)

    assert result.status == "DELIVERED"
    assert result.is_preview is True
    # DELIVERED should have a warning
    assert any("delivered" in w.lower() for w in result.warnings)

    # Confirm mode - should still allow fulfillment (Katana allows multiple fulfillments)
    request = FulfillOrderRequest(order_id=5678, order_type="sales", confirm=True)
    # This will actually try to create fulfillment, so we need to mock it
    from katana_public_api_client.api.sales_order_fulfillment import (
        create_sales_order_fulfillment,
    )

    mock_create_response = MagicMock()
    mock_create_response.status_code = 201
    create_sales_order_fulfillment.asyncio_detailed = AsyncMock(
        return_value=mock_create_response
    )

    result = await _fulfill_order_impl(request, context)
    assert result.is_preview is False
    assert result.status == "FULFILLED"  # Status changes after fulfillment created


@pytest.mark.asyncio
async def test_fulfill_sales_order_not_found():
    """Test fulfill_order when sales order not found."""
    context, lifespan_ctx = create_mock_context()

    # Mock 404 response
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.parsed = None

    from katana_public_api_client.api.sales_order import get_sales_order

    get_sales_order.asyncio_detailed = AsyncMock(return_value=mock_response)

    request = FulfillOrderRequest(order_id=9999, order_type="sales", confirm=False)

    with pytest.raises(Exception, match="Failed to fetch sales order"):
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
        FulfillOrderRequest(order_id=1234, order_type="invalid", confirm=False)  # type: ignore


# ============================================================================
# Error Handling Tests
# ============================================================================


@pytest.mark.asyncio
async def test_fulfill_manufacturing_order_api_error():
    """Test fulfill_order when manufacturing order API returns error."""
    context, lifespan_ctx = create_mock_context()

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
        order_id=1234, order_type="manufacturing", confirm=True
    )

    with pytest.raises(Exception, match="API returned unexpected status"):
        await _fulfill_order_impl(request, context)


@pytest.mark.asyncio
async def test_fulfill_sales_order_api_error():
    """Test fulfill_order when sales order fulfillment API returns error."""
    context, lifespan_ctx = create_mock_context()

    # Mock SalesOrder
    mock_so = MagicMock(spec=SalesOrder)
    mock_so.order_no = "SO-005"
    mock_so.status = SalesOrderStatus.NOT_SHIPPED

    mock_get_response = MagicMock()
    mock_get_response.status_code = 200
    mock_get_response.parsed = mock_so

    # Mock create fulfillment API returning error
    mock_create_response = MagicMock()
    mock_create_response.status_code = 400
    mock_create_response.parsed = None

    from katana_public_api_client.api.sales_order import get_sales_order
    from katana_public_api_client.api.sales_order_fulfillment import (
        create_sales_order_fulfillment,
    )

    get_sales_order.asyncio_detailed = AsyncMock(return_value=mock_get_response)
    create_sales_order_fulfillment.asyncio_detailed = AsyncMock(
        return_value=mock_create_response
    )

    request = FulfillOrderRequest(order_id=5678, order_type="sales", confirm=True)

    with pytest.raises(Exception, match="API returned unexpected status"):
        await _fulfill_order_impl(request, context)
