"""Tests for purchase order MCP tools."""

import os
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from katana_mcp.tools.foundation.purchase_orders import (
    ReceiveItemRequest,
    ReceivePurchaseOrderRequest,
    ReceivePurchaseOrderResponse,
    _receive_purchase_order_impl,
    receive_purchase_order,
)

from katana_public_api_client.client_types import UNSET
from katana_public_api_client.models import (
    PurchaseOrderReceiveRow,
    RegularPurchaseOrder,
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
async def test_receive_purchase_order_preview():
    """Test receive_purchase_order in preview mode (confirm=false)."""
    context, lifespan_ctx = create_mock_context()

    # Mock the get_purchase_order API response
    mock_po = MagicMock(spec=RegularPurchaseOrder)
    mock_po.id = 1234
    mock_po.order_no = "PO-2024-001"
    mock_po.status = MagicMock()
    mock_po.status.value = "NOT_RECEIVED"

    mock_get_response = MagicMock()
    mock_get_response.status_code = 200
    mock_get_response.parsed = mock_po

    lifespan_ctx.client = MagicMock()

    # Mock get_purchase_order API call
    from katana_public_api_client.api.purchase_order import (
        get_purchase_order as api_get_purchase_order,
    )

    api_get_purchase_order.asyncio_detailed = AsyncMock(return_value=mock_get_response)

    # Create request with confirm=false (preview mode)
    request = ReceivePurchaseOrderRequest(
        order_id=1234,
        items=[
            ReceiveItemRequest(purchase_order_row_id=501, quantity=100.0),
            ReceiveItemRequest(purchase_order_row_id=502, quantity=50.0),
        ],
        confirm=False,
    )

    result = await _receive_purchase_order_impl(request, context)

    # Verify preview response
    assert isinstance(result, ReceivePurchaseOrderResponse)
    assert result.order_id == 1234
    assert result.order_number == "PO-2024-001"
    assert result.items_received == 2
    assert result.is_preview is True
    assert "Review the items to receive" in result.next_actions
    assert "confirm=true" in result.next_actions[1]
    assert "Preview" in result.message


@pytest.mark.asyncio
async def test_receive_purchase_order_confirm_success():
    """Test receive_purchase_order in confirm mode with successful API call."""
    context, lifespan_ctx = create_mock_context()

    # Mock the get_purchase_order API response
    mock_po = MagicMock(spec=RegularPurchaseOrder)
    mock_po.id = 1234
    mock_po.order_no = "PO-2024-001"
    mock_po.status = MagicMock()
    mock_po.status.value = "PARTIALLY_RECEIVED"

    mock_get_response = MagicMock()
    mock_get_response.status_code = 200
    mock_get_response.parsed = mock_po

    # Mock the receive_purchase_order API response (204 No Content)
    mock_receive_response = MagicMock()
    mock_receive_response.status_code = 204

    lifespan_ctx.client = MagicMock()

    # Mock both API calls
    from katana_public_api_client.api.purchase_order import (
        get_purchase_order as api_get_purchase_order,
        receive_purchase_order as api_receive_purchase_order,
    )

    api_get_purchase_order.asyncio_detailed = AsyncMock(return_value=mock_get_response)
    api_receive_purchase_order.asyncio_detailed = AsyncMock(
        return_value=mock_receive_response
    )

    # Create request with confirm=true
    request = ReceivePurchaseOrderRequest(
        order_id=1234,
        items=[
            ReceiveItemRequest(purchase_order_row_id=501, quantity=100.0),
            ReceiveItemRequest(purchase_order_row_id=502, quantity=50.0),
        ],
        confirm=True,
    )

    result = await _receive_purchase_order_impl(request, context)

    # Verify success response
    assert isinstance(result, ReceivePurchaseOrderResponse)
    assert result.order_id == 1234
    assert result.order_number == "PO-2024-001"
    assert result.items_received == 2
    assert result.is_preview is False
    assert "Successfully received" in result.message
    assert "Inventory has been updated" in result.next_actions

    # Verify API was called with correct data
    api_receive_purchase_order.asyncio_detailed.assert_called_once()
    call_args = api_receive_purchase_order.asyncio_detailed.call_args
    body = call_args.kwargs["body"]

    # Verify the body contains correct receive rows
    assert len(body) == 2
    assert all(isinstance(row, PurchaseOrderReceiveRow) for row in body)
    assert body[0].purchase_order_row_id == 501
    assert body[0].quantity == 100.0
    assert body[1].purchase_order_row_id == 502
    assert body[1].quantity == 50.0


@pytest.mark.asyncio
async def test_receive_purchase_order_single_item():
    """Test receive_purchase_order with a single item."""
    context, lifespan_ctx = create_mock_context()

    # Mock the get_purchase_order API response
    mock_po = MagicMock(spec=RegularPurchaseOrder)
    mock_po.id = 5678
    mock_po.order_no = "PO-2024-002"
    mock_po.status = MagicMock()
    mock_po.status.value = "NOT_RECEIVED"

    mock_get_response = MagicMock()
    mock_get_response.status_code = 200
    mock_get_response.parsed = mock_po

    # Mock the receive_purchase_order API response
    mock_receive_response = MagicMock()
    mock_receive_response.status_code = 204

    lifespan_ctx.client = MagicMock()

    from katana_public_api_client.api.purchase_order import (
        get_purchase_order as api_get_purchase_order,
        receive_purchase_order as api_receive_purchase_order,
    )

    api_get_purchase_order.asyncio_detailed = AsyncMock(return_value=mock_get_response)
    api_receive_purchase_order.asyncio_detailed = AsyncMock(
        return_value=mock_receive_response
    )

    # Create request with single item
    request = ReceivePurchaseOrderRequest(
        order_id=5678,
        items=[ReceiveItemRequest(purchase_order_row_id=601, quantity=25.5)],
        confirm=True,
    )

    result = await _receive_purchase_order_impl(request, context)

    assert result.order_id == 5678
    assert result.items_received == 1
    assert result.is_preview is False


@pytest.mark.asyncio
async def test_receive_purchase_order_get_po_fails():
    """Test receive_purchase_order when get_purchase_order API fails."""
    context, lifespan_ctx = create_mock_context()

    # Mock failed get_purchase_order response
    mock_get_response = MagicMock()
    mock_get_response.status_code = 404
    mock_get_response.parsed = None

    lifespan_ctx.client = MagicMock()

    from katana_public_api_client.api.purchase_order import (
        get_purchase_order as api_get_purchase_order,
    )

    api_get_purchase_order.asyncio_detailed = AsyncMock(return_value=mock_get_response)

    request = ReceivePurchaseOrderRequest(
        order_id=9999,
        items=[ReceiveItemRequest(purchase_order_row_id=701, quantity=10.0)],
        confirm=False,
    )

    # Should raise an exception
    with pytest.raises(Exception) as exc_info:
        await _receive_purchase_order_impl(request, context)

    assert "Failed to fetch purchase order" in str(exc_info.value)
    assert "9999" in str(exc_info.value)


@pytest.mark.asyncio
async def test_receive_purchase_order_receive_api_fails():
    """Test receive_purchase_order when receive API returns non-204 status."""
    context, lifespan_ctx = create_mock_context()

    # Mock successful get_purchase_order
    mock_po = MagicMock(spec=RegularPurchaseOrder)
    mock_po.id = 1234
    mock_po.order_no = "PO-2024-001"
    mock_po.status = MagicMock()
    mock_po.status.value = "NOT_RECEIVED"

    mock_get_response = MagicMock()
    mock_get_response.status_code = 200
    mock_get_response.parsed = mock_po

    # Mock failed receive_purchase_order response
    mock_receive_response = MagicMock()
    mock_receive_response.status_code = 422

    lifespan_ctx.client = MagicMock()

    from katana_public_api_client.api.purchase_order import (
        get_purchase_order as api_get_purchase_order,
        receive_purchase_order as api_receive_purchase_order,
    )

    api_get_purchase_order.asyncio_detailed = AsyncMock(return_value=mock_get_response)
    api_receive_purchase_order.asyncio_detailed = AsyncMock(
        return_value=mock_receive_response
    )

    request = ReceivePurchaseOrderRequest(
        order_id=1234,
        items=[ReceiveItemRequest(purchase_order_row_id=501, quantity=100.0)],
        confirm=True,
    )

    # Should raise an exception
    with pytest.raises(Exception) as exc_info:
        await _receive_purchase_order_impl(request, context)

    assert "API returned unexpected status" in str(exc_info.value)
    assert "422" in str(exc_info.value)


@pytest.mark.asyncio
async def test_receive_purchase_order_order_no_unset():
    """Test receive_purchase_order when order_no is UNSET."""
    context, lifespan_ctx = create_mock_context()

    # Mock PO with UNSET order_no
    mock_po = MagicMock(spec=RegularPurchaseOrder)
    mock_po.id = 1234
    mock_po.order_no = UNSET
    mock_po.status = MagicMock()
    mock_po.status.value = "NOT_RECEIVED"

    mock_get_response = MagicMock()
    mock_get_response.status_code = 200
    mock_get_response.parsed = mock_po

    lifespan_ctx.client = MagicMock()

    from katana_public_api_client.api.purchase_order import (
        get_purchase_order as api_get_purchase_order,
    )

    api_get_purchase_order.asyncio_detailed = AsyncMock(return_value=mock_get_response)

    request = ReceivePurchaseOrderRequest(
        order_id=1234,
        items=[ReceiveItemRequest(purchase_order_row_id=501, quantity=100.0)],
        confirm=False,
    )

    result = await _receive_purchase_order_impl(request, context)

    # Should use fallback order number
    assert result.order_number == "PO-1234"
    assert result.is_preview is True


@pytest.mark.asyncio
async def test_receive_purchase_order_received_date_set():
    """Test that received_date is set correctly when receiving items."""
    context, lifespan_ctx = create_mock_context()

    # Mock successful get and receive
    mock_po = MagicMock(spec=RegularPurchaseOrder)
    mock_po.id = 1234
    mock_po.order_no = "PO-2024-001"
    mock_po.status = MagicMock()
    mock_po.status.value = "NOT_RECEIVED"

    mock_get_response = MagicMock()
    mock_get_response.status_code = 200
    mock_get_response.parsed = mock_po

    mock_receive_response = MagicMock()
    mock_receive_response.status_code = 204

    lifespan_ctx.client = MagicMock()

    from katana_public_api_client.api.purchase_order import (
        get_purchase_order as api_get_purchase_order,
        receive_purchase_order as api_receive_purchase_order,
    )

    api_get_purchase_order.asyncio_detailed = AsyncMock(return_value=mock_get_response)
    api_receive_purchase_order.asyncio_detailed = AsyncMock(
        return_value=mock_receive_response
    )

    request = ReceivePurchaseOrderRequest(
        order_id=1234,
        items=[ReceiveItemRequest(purchase_order_row_id=501, quantity=100.0)],
        confirm=True,
    )

    # Record time before call
    before_time = datetime.now(UTC)

    await _receive_purchase_order_impl(request, context)

    # Record time after call
    after_time = datetime.now(UTC)

    # Verify received_date was set
    call_args = api_receive_purchase_order.asyncio_detailed.call_args
    body = call_args.kwargs["body"]
    received_date = body[0].received_date

    # Verify it's a datetime in UTC and within reasonable bounds
    assert isinstance(received_date, datetime)
    assert received_date.tzinfo == UTC
    assert before_time <= received_date <= after_time


# ============================================================================
# Integration Tests (require KATANA_API_KEY)
# ============================================================================


@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("KATANA_API_KEY"), reason="No API key")
@pytest.mark.asyncio
async def test_receive_purchase_order_integration_preview(katana_context):
    """Integration test: Preview mode with real API."""
    # This test requires a real PO ID that exists in the test environment
    # For now, we'll skip if we don't have a test PO ID
    test_po_id = os.getenv("TEST_PO_ID")
    if not test_po_id:
        pytest.skip("TEST_PO_ID not set - cannot run integration test")

    request = ReceivePurchaseOrderRequest(
        order_id=int(test_po_id),
        items=[ReceiveItemRequest(purchase_order_row_id=1, quantity=1.0)],
        confirm=False,
    )

    # This should not fail even if the row ID doesn't exist
    # because preview mode just fetches the PO
    result = await _receive_purchase_order_impl(request, katana_context)

    assert result.is_preview is True
    assert result.order_id == int(test_po_id)
    assert result.items_received == 1


# ============================================================================
# Tests for public wrapper function
# ============================================================================


@pytest.mark.asyncio
async def test_receive_purchase_order_wrapper():
    """Test the public receive_purchase_order wrapper function."""
    context, lifespan_ctx = create_mock_context()

    # Mock the get_purchase_order API response
    mock_po = MagicMock(spec=RegularPurchaseOrder)
    mock_po.id = 1234
    mock_po.order_no = "PO-2024-001"
    mock_po.status = MagicMock()
    mock_po.status.value = "NOT_RECEIVED"

    mock_get_response = MagicMock()
    mock_get_response.status_code = 200
    mock_get_response.parsed = mock_po

    lifespan_ctx.client = MagicMock()

    from katana_public_api_client.api.purchase_order import (
        get_purchase_order as api_get_purchase_order,
    )

    api_get_purchase_order.asyncio_detailed = AsyncMock(return_value=mock_get_response)

    # Call the public wrapper function
    request = ReceivePurchaseOrderRequest(
        order_id=1234,
        items=[ReceiveItemRequest(purchase_order_row_id=501, quantity=100.0)],
        confirm=False,
    )

    result = await receive_purchase_order(request, context)

    # Verify it returns the same type as the implementation
    assert isinstance(result, ReceivePurchaseOrderResponse)
    assert result.order_id == 1234
    assert result.is_preview is True


@pytest.mark.asyncio
async def test_receive_purchase_order_multiple_items_various_quantities():
    """Test receiving multiple items with various quantities including decimals."""
    context, lifespan_ctx = create_mock_context()

    # Mock successful get and receive
    mock_po = MagicMock(spec=RegularPurchaseOrder)
    mock_po.id = 1234
    mock_po.order_no = "PO-2024-003"
    mock_po.status = MagicMock()
    mock_po.status.value = "NOT_RECEIVED"

    mock_get_response = MagicMock()
    mock_get_response.status_code = 200
    mock_get_response.parsed = mock_po

    mock_receive_response = MagicMock()
    mock_receive_response.status_code = 204

    lifespan_ctx.client = MagicMock()

    from katana_public_api_client.api.purchase_order import (
        get_purchase_order as api_get_purchase_order,
        receive_purchase_order as api_receive_purchase_order,
    )

    api_get_purchase_order.asyncio_detailed = AsyncMock(return_value=mock_get_response)
    api_receive_purchase_order.asyncio_detailed = AsyncMock(
        return_value=mock_receive_response
    )

    # Test with various quantities: integers, decimals, large numbers
    request = ReceivePurchaseOrderRequest(
        order_id=1234,
        items=[
            ReceiveItemRequest(purchase_order_row_id=501, quantity=100.0),
            ReceiveItemRequest(purchase_order_row_id=502, quantity=25.5),
            ReceiveItemRequest(purchase_order_row_id=503, quantity=0.75),
            ReceiveItemRequest(purchase_order_row_id=504, quantity=1000.0),
        ],
        confirm=True,
    )

    result = await _receive_purchase_order_impl(request, context)

    assert result.items_received == 4
    assert result.is_preview is False

    # Verify all items were sent to API
    call_args = api_receive_purchase_order.asyncio_detailed.call_args
    body = call_args.kwargs["body"]
    assert len(body) == 4
    assert body[0].quantity == 100.0
    assert body[1].quantity == 25.5
    assert body[2].quantity == 0.75
    assert body[3].quantity == 1000.0


@pytest.mark.asyncio
async def test_receive_purchase_order_validates_positive_quantity():
    """Test that ReceiveItemRequest validates quantity > 0."""
    # Pydantic should validate this at model creation time
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ReceiveItemRequest(purchase_order_row_id=501, quantity=0.0)

    with pytest.raises(ValidationError):
        ReceiveItemRequest(purchase_order_row_id=501, quantity=-10.0)


@pytest.mark.asyncio
async def test_receive_purchase_order_validates_min_items():
    """Test that ReceivePurchaseOrderRequest requires at least one item."""
    # Pydantic should validate min_length=1
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ReceivePurchaseOrderRequest(order_id=1234, items=[], confirm=False)


@pytest.mark.asyncio
async def test_receive_purchase_order_exception_handling():
    """Test proper exception handling and logging."""
    context, lifespan_ctx = create_mock_context()

    # Mock get_purchase_order to raise an exception
    from katana_public_api_client.api.purchase_order import (
        get_purchase_order as api_get_purchase_order,
    )

    api_get_purchase_order.asyncio_detailed = AsyncMock(
        side_effect=Exception("Network error")
    )

    lifespan_ctx.client = MagicMock()

    request = ReceivePurchaseOrderRequest(
        order_id=1234,
        items=[ReceiveItemRequest(purchase_order_row_id=501, quantity=100.0)],
        confirm=False,
    )

    # Should raise and propagate the exception
    with pytest.raises(Exception) as exc_info:
        await _receive_purchase_order_impl(request, context)

    assert "Network error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_receive_purchase_order_builds_correct_api_payload():
    """Test that the API payload is built correctly with all fields."""
    context, lifespan_ctx = create_mock_context()

    # Mock successful get and receive
    mock_po = MagicMock(spec=RegularPurchaseOrder)
    mock_po.id = 1234
    mock_po.order_no = "PO-2024-TEST"
    mock_po.status = MagicMock()
    mock_po.status.value = "NOT_RECEIVED"

    mock_get_response = MagicMock()
    mock_get_response.status_code = 200
    mock_get_response.parsed = mock_po

    mock_receive_response = MagicMock()
    mock_receive_response.status_code = 204

    lifespan_ctx.client = MagicMock()

    from katana_public_api_client.api.purchase_order import (
        get_purchase_order as api_get_purchase_order,
        receive_purchase_order as api_receive_purchase_order,
    )

    api_get_purchase_order.asyncio_detailed = AsyncMock(return_value=mock_get_response)
    api_receive_purchase_order.asyncio_detailed = AsyncMock(
        return_value=mock_receive_response
    )

    # Create request with multiple items
    request = ReceivePurchaseOrderRequest(
        order_id=1234,
        items=[
            ReceiveItemRequest(purchase_order_row_id=501, quantity=100.0),
            ReceiveItemRequest(purchase_order_row_id=502, quantity=50.5),
        ],
        confirm=True,
    )

    await _receive_purchase_order_impl(request, context)

    # Verify the API was called with correct parameters
    api_receive_purchase_order.asyncio_detailed.assert_called_once()
    call_args = api_receive_purchase_order.asyncio_detailed.call_args

    # Check client parameter
    assert "client" in call_args.kwargs
    assert call_args.kwargs["client"] == lifespan_ctx.client

    # Check body parameter (list of PurchaseOrderReceiveRow)
    body = call_args.kwargs["body"]
    assert isinstance(body, list)
    assert len(body) == 2

    # Verify first row
    assert isinstance(body[0], PurchaseOrderReceiveRow)
    assert body[0].purchase_order_row_id == 501
    assert body[0].quantity == 100.0
    assert isinstance(body[0].received_date, datetime)

    # Verify second row
    assert isinstance(body[1], PurchaseOrderReceiveRow)
    assert body[1].purchase_order_row_id == 502
    assert body[1].quantity == 50.5
    assert isinstance(body[1].received_date, datetime)


@pytest.mark.asyncio
async def test_receive_purchase_order_response_structure():
    """Test that response contains all expected fields."""
    context, lifespan_ctx = create_mock_context()

    # Mock successful response
    mock_po = MagicMock(spec=RegularPurchaseOrder)
    mock_po.id = 9999
    mock_po.order_no = "PO-RESPONSE-TEST"
    mock_po.status = MagicMock()
    mock_po.status.value = "RECEIVED"

    mock_get_response = MagicMock()
    mock_get_response.status_code = 200
    mock_get_response.parsed = mock_po

    mock_receive_response = MagicMock()
    mock_receive_response.status_code = 204

    lifespan_ctx.client = MagicMock()

    from katana_public_api_client.api.purchase_order import (
        get_purchase_order as api_get_purchase_order,
        receive_purchase_order as api_receive_purchase_order,
    )

    api_get_purchase_order.asyncio_detailed = AsyncMock(return_value=mock_get_response)
    api_receive_purchase_order.asyncio_detailed = AsyncMock(
        return_value=mock_receive_response
    )

    request = ReceivePurchaseOrderRequest(
        order_id=9999,
        items=[ReceiveItemRequest(purchase_order_row_id=701, quantity=25.0)],
        confirm=True,
    )

    result = await _receive_purchase_order_impl(request, context)

    # Verify all response fields are populated correctly
    assert result.order_id == 9999
    assert result.order_number == "PO-RESPONSE-TEST"
    assert result.items_received == 1
    assert result.is_preview is False
    assert isinstance(result.warnings, list)
    assert isinstance(result.next_actions, list)
    assert len(result.next_actions) > 0
    assert isinstance(result.message, str)
    assert "Successfully received" in result.message
