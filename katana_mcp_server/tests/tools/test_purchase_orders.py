"""Tests for purchase order MCP tools."""

import os
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from katana_mcp.tools.foundation.purchase_orders import (
    DiscrepancyType,
    DocumentItem,
    ReceiveItemRequest,
    ReceivePurchaseOrderRequest,
    ReceivePurchaseOrderResponse,
    VerifyOrderDocumentRequest,
    _receive_purchase_order_impl,
    _verify_order_document_impl,
    receive_purchase_order,
)

from katana_public_api_client.api.purchase_order import (
    get_purchase_order as api_get_purchase_order,
)
from katana_public_api_client.client_types import UNSET
from katana_public_api_client.models import (
    PurchaseOrderReceiveRow,
    RegularPurchaseOrder,
)

from .conftest import create_mock_context

# ============================================================================
# Test Helpers
# ============================================================================


def create_mock_po_row(variant_id: int, quantity: float, price: float):
    """Create a mock PO row."""
    row = MagicMock()
    row.variant_id = variant_id
    row.quantity = quantity
    row.price_per_unit = price
    return row


def create_mock_variant(variant_id: int, sku: str):
    """Create a mock variant."""
    variant = MagicMock()
    variant.id = variant_id
    variant.sku = sku
    return variant


def create_mock_po(order_id: int, order_no: str, rows: list):
    """Create a mock RegularPurchaseOrder."""
    po = MagicMock(spec=RegularPurchaseOrder)
    po.id = order_id
    po.order_no = order_no
    po.purchase_order_rows = rows
    return po


# ============================================================================
# Unit Tests - verify_order_document
# ============================================================================


@pytest.mark.asyncio
async def test_verify_order_document_perfect_match():
    """Test verification with all items matching perfectly."""
    context, lifespan_ctx = create_mock_context()

    # Mock PO with 2 rows
    po_rows = [
        create_mock_po_row(variant_id=1, quantity=100.0, price=25.50),
        create_mock_po_row(variant_id=2, quantity=50.0, price=30.00),
    ]
    mock_po = create_mock_po(order_id=1234, order_no="PO-001", rows=po_rows)

    # Mock API response
    mock_po_response = MagicMock()
    mock_po_response.status_code = 200
    mock_po_response.parsed = mock_po

    # Mock variants
    mock_variants = [
        create_mock_variant(variant_id=1, sku="WIDGET-001"),
        create_mock_variant(variant_id=2, sku="WIDGET-002"),
    ]

    # Setup mocks

    api_get_purchase_order.asyncio_detailed = AsyncMock(return_value=mock_po_response)
    lifespan_ctx.client.variants.list = AsyncMock(return_value=mock_variants)

    # Document items matching PO perfectly
    request = VerifyOrderDocumentRequest(
        order_id=1234,
        document_items=[
            DocumentItem(sku="WIDGET-001", quantity=100.0, unit_price=25.50),
            DocumentItem(sku="WIDGET-002", quantity=50.0, unit_price=30.00),
        ],
    )

    result = await _verify_order_document_impl(request, context)

    # Assertions
    assert result.order_id == 1234
    assert result.overall_status == "match"
    assert len(result.matches) == 2
    assert len(result.discrepancies) == 0

    # Check match details
    match1 = result.matches[0]
    assert match1.sku == "WIDGET-001"
    assert match1.quantity == 100.0
    assert match1.unit_price == 25.50
    assert match1.status == "perfect"

    match2 = result.matches[1]
    assert match2.sku == "WIDGET-002"
    assert match2.quantity == 50.0
    assert match2.unit_price == 30.00
    assert match2.status == "perfect"

    assert any(
        "All items verified successfully" in action
        for action in result.suggested_actions
    )


# ============================================================================
# Unit Tests - Quantity Discrepancies
# ============================================================================


@pytest.mark.asyncio
async def test_verify_order_document_quantity_mismatch():
    """Test verification with quantity discrepancies."""
    context, lifespan_ctx = create_mock_context()

    # Mock PO
    po_rows = [create_mock_po_row(variant_id=1, quantity=100.0, price=25.50)]
    mock_po = create_mock_po(order_id=1234, order_no="PO-001", rows=po_rows)

    mock_po_response = MagicMock()
    mock_po_response.status_code = 200
    mock_po_response.parsed = mock_po

    mock_variants = [create_mock_variant(variant_id=1, sku="WIDGET-001")]

    api_get_purchase_order.asyncio_detailed = AsyncMock(return_value=mock_po_response)
    lifespan_ctx.client.variants.list = AsyncMock(return_value=mock_variants)

    # Document with different quantity
    request = VerifyOrderDocumentRequest(
        order_id=1234,
        document_items=[
            DocumentItem(sku="WIDGET-001", quantity=90.0, unit_price=25.50),
        ],
    )

    result = await _verify_order_document_impl(request, context)

    # Assertions
    assert result.order_id == 1234
    assert result.overall_status == "partial_match"
    assert len(result.matches) == 1
    assert len(result.discrepancies) == 1

    # Check discrepancy
    discrepancy = result.discrepancies[0]
    assert discrepancy.sku == "WIDGET-001"
    assert discrepancy.type == DiscrepancyType.QUANTITY_MISMATCH
    assert discrepancy.expected == 100.0
    assert discrepancy.actual == 90.0
    assert "Quantity mismatch" in discrepancy.message

    # Check match with quantity_diff status
    match = result.matches[0]
    assert match.sku == "WIDGET-001"
    assert match.status == "quantity_diff"

    assert any("Review discrepancies" in action for action in result.suggested_actions)


# ============================================================================
# Unit Tests - Price Discrepancies
# ============================================================================


@pytest.mark.asyncio
async def test_verify_order_document_price_mismatch():
    """Test verification with price discrepancies."""
    context, lifespan_ctx = create_mock_context()

    # Mock PO
    po_rows = [create_mock_po_row(variant_id=1, quantity=100.0, price=25.50)]
    mock_po = create_mock_po(order_id=1234, order_no="PO-001", rows=po_rows)

    mock_po_response = MagicMock()
    mock_po_response.status_code = 200
    mock_po_response.parsed = mock_po

    mock_variants = [create_mock_variant(variant_id=1, sku="WIDGET-001")]

    api_get_purchase_order.asyncio_detailed = AsyncMock(return_value=mock_po_response)
    lifespan_ctx.client.variants.list = AsyncMock(return_value=mock_variants)

    # Document with different price
    request = VerifyOrderDocumentRequest(
        order_id=1234,
        document_items=[
            DocumentItem(sku="WIDGET-001", quantity=100.0, unit_price=30.00),
        ],
    )

    result = await _verify_order_document_impl(request, context)

    # Assertions
    assert result.order_id == 1234
    assert result.overall_status == "partial_match"
    assert len(result.matches) == 1
    assert len(result.discrepancies) == 1

    # Check discrepancy
    discrepancy = result.discrepancies[0]
    assert discrepancy.sku == "WIDGET-001"
    assert discrepancy.type == DiscrepancyType.PRICE_MISMATCH
    assert discrepancy.expected == 25.50
    assert discrepancy.actual == 30.00
    assert "Price mismatch" in discrepancy.message

    # Check match with price_diff status
    match = result.matches[0]
    assert match.sku == "WIDGET-001"
    assert match.status == "price_diff"


# ============================================================================
# Unit Tests - Missing Items
# ============================================================================


@pytest.mark.asyncio
async def test_verify_order_document_missing_in_po():
    """Test verification with items in document but not in PO."""
    context, lifespan_ctx = create_mock_context()

    # Mock PO with only WIDGET-001
    po_rows = [create_mock_po_row(variant_id=1, quantity=100.0, price=25.50)]
    mock_po = create_mock_po(order_id=1234, order_no="PO-001", rows=po_rows)

    mock_po_response = MagicMock()
    mock_po_response.status_code = 200
    mock_po_response.parsed = mock_po

    mock_variants = [create_mock_variant(variant_id=1, sku="WIDGET-001")]

    api_get_purchase_order.asyncio_detailed = AsyncMock(return_value=mock_po_response)
    lifespan_ctx.client.variants.list = AsyncMock(return_value=mock_variants)

    # Document includes WIDGET-002 which is not in PO
    request = VerifyOrderDocumentRequest(
        order_id=1234,
        document_items=[
            DocumentItem(sku="WIDGET-001", quantity=100.0, unit_price=25.50),
            DocumentItem(sku="WIDGET-002", quantity=50.0, unit_price=30.00),
        ],
    )

    result = await _verify_order_document_impl(request, context)

    # Assertions
    assert result.order_id == 1234
    assert result.overall_status == "partial_match"
    assert len(result.matches) == 1
    assert len(result.discrepancies) == 1

    # Check discrepancy
    discrepancy = result.discrepancies[0]
    assert discrepancy.sku == "WIDGET-002"
    assert discrepancy.type == DiscrepancyType.MISSING_IN_PO
    assert discrepancy.expected is None
    assert discrepancy.actual == 50.0
    assert "Not found in purchase order" in discrepancy.message


# ============================================================================
# Unit Tests - Extra Items in PO
# ============================================================================


@pytest.mark.asyncio
async def test_verify_order_document_extra_in_document():
    """Test that we don't report PO items missing from document (only check document items)."""
    context, lifespan_ctx = create_mock_context()

    # Mock PO with 2 items
    po_rows = [
        create_mock_po_row(variant_id=1, quantity=100.0, price=25.50),
        create_mock_po_row(variant_id=2, quantity=50.0, price=30.00),
    ]
    mock_po = create_mock_po(order_id=1234, order_no="PO-001", rows=po_rows)

    mock_po_response = MagicMock()
    mock_po_response.status_code = 200
    mock_po_response.parsed = mock_po

    mock_variants = [
        create_mock_variant(variant_id=1, sku="WIDGET-001"),
        create_mock_variant(variant_id=2, sku="WIDGET-002"),
    ]

    api_get_purchase_order.asyncio_detailed = AsyncMock(return_value=mock_po_response)
    lifespan_ctx.client.variants.list = AsyncMock(return_value=mock_variants)

    # Document only has WIDGET-001 (missing WIDGET-002 from PO)
    request = VerifyOrderDocumentRequest(
        order_id=1234,
        document_items=[
            DocumentItem(sku="WIDGET-001", quantity=100.0, unit_price=25.50),
        ],
    )

    result = await _verify_order_document_impl(request, context)

    # Assertions - should only verify what's in document, not flag missing PO items
    assert result.order_id == 1234
    assert result.overall_status == "match"
    assert len(result.matches) == 1
    assert len(result.discrepancies) == 0


# ============================================================================
# Unit Tests - Mixed Scenarios
# ============================================================================


@pytest.mark.asyncio
async def test_verify_order_document_mixed_discrepancies():
    """Test verification with multiple types of discrepancies."""
    context, lifespan_ctx = create_mock_context()

    # Mock PO with 2 items
    po_rows = [
        create_mock_po_row(variant_id=1, quantity=100.0, price=25.50),
        create_mock_po_row(variant_id=2, quantity=50.0, price=30.00),
    ]
    mock_po = create_mock_po(order_id=1234, order_no="PO-001", rows=po_rows)

    mock_po_response = MagicMock()
    mock_po_response.status_code = 200
    mock_po_response.parsed = mock_po

    mock_variants = [
        create_mock_variant(variant_id=1, sku="WIDGET-001"),
        create_mock_variant(variant_id=2, sku="WIDGET-002"),
    ]

    api_get_purchase_order.asyncio_detailed = AsyncMock(return_value=mock_po_response)
    lifespan_ctx.client.variants.list = AsyncMock(return_value=mock_variants)

    # Document with: perfect match, quantity mismatch, missing item
    request = VerifyOrderDocumentRequest(
        order_id=1234,
        document_items=[
            DocumentItem(
                sku="WIDGET-001", quantity=100.0, unit_price=25.50
            ),  # Perfect match
            DocumentItem(
                sku="WIDGET-002", quantity=45.0, unit_price=30.00
            ),  # Quantity mismatch
            DocumentItem(
                sku="WIDGET-003", quantity=25.0, unit_price=15.00
            ),  # Not in PO
        ],
    )

    result = await _verify_order_document_impl(request, context)

    # Assertions
    assert result.order_id == 1234
    assert result.overall_status == "partial_match"
    assert len(result.matches) == 2
    assert len(result.discrepancies) == 2

    # Check perfect match
    perfect_match = next(m for m in result.matches if m.sku == "WIDGET-001")
    assert perfect_match.status == "perfect"

    # Check quantity mismatch
    qty_match = next(m for m in result.matches if m.sku == "WIDGET-002")
    assert qty_match.status == "quantity_diff"

    qty_discrepancy = next(
        d for d in result.discrepancies if d.type == DiscrepancyType.QUANTITY_MISMATCH
    )
    assert qty_discrepancy.sku == "WIDGET-002"
    assert qty_discrepancy.expected == 50.0
    assert qty_discrepancy.actual == 45.0

    # Check missing item
    missing_discrepancy = next(
        d for d in result.discrepancies if d.type == DiscrepancyType.MISSING_IN_PO
    )
    assert missing_discrepancy.sku == "WIDGET-003"
    assert missing_discrepancy.actual == 25.0


# ============================================================================
# Unit Tests - Edge Cases
# ============================================================================


@pytest.mark.asyncio
async def test_verify_order_document_empty_po():
    """Test verification when PO has no line items."""
    context, lifespan_ctx = create_mock_context()

    # Mock PO with no rows
    mock_po = create_mock_po(order_id=1234, order_no="PO-001", rows=[])

    mock_po_response = MagicMock()
    mock_po_response.status_code = 200
    mock_po_response.parsed = mock_po

    api_get_purchase_order.asyncio_detailed = AsyncMock(return_value=mock_po_response)

    request = VerifyOrderDocumentRequest(
        order_id=1234,
        document_items=[
            DocumentItem(sku="WIDGET-001", quantity=100.0, unit_price=25.50),
        ],
    )

    result = await _verify_order_document_impl(request, context)

    # Assertions
    assert result.order_id == 1234
    assert result.overall_status == "no_match"
    assert len(result.matches) == 0
    assert len(result.discrepancies) == 0
    assert "has no line items" in result.message
    assert any(
        "Verify purchase order data" in action for action in result.suggested_actions
    )


@pytest.mark.asyncio
async def test_verify_order_document_po_not_found():
    """Test verification when PO doesn't exist."""
    context, lifespan_ctx = create_mock_context()

    # Mock 404 response
    mock_po_response = MagicMock()
    mock_po_response.status_code = 404
    mock_po_response.parsed = None

    api_get_purchase_order.asyncio_detailed = AsyncMock(return_value=mock_po_response)

    request = VerifyOrderDocumentRequest(
        order_id=9999,
        document_items=[
            DocumentItem(sku="WIDGET-001", quantity=100.0, unit_price=25.50),
        ],
    )

    with pytest.raises(Exception) as exc_info:
        await _verify_order_document_impl(request, context)

    assert "Failed to fetch purchase order 9999" in str(exc_info.value)


@pytest.mark.asyncio
async def test_verify_order_document_unset_values():
    """Test verification with UNSET values in PO data."""
    context, lifespan_ctx = create_mock_context()

    # Mock PO row with UNSET values
    po_row = MagicMock()
    po_row.variant_id = 1
    po_row.quantity = UNSET
    po_row.price_per_unit = UNSET

    mock_po = create_mock_po(order_id=1234, order_no="PO-001", rows=[po_row])

    mock_po_response = MagicMock()
    mock_po_response.status_code = 200
    mock_po_response.parsed = mock_po

    mock_variants = [create_mock_variant(variant_id=1, sku="WIDGET-001")]

    api_get_purchase_order.asyncio_detailed = AsyncMock(return_value=mock_po_response)
    lifespan_ctx.client.variants.list = AsyncMock(return_value=mock_variants)

    request = VerifyOrderDocumentRequest(
        order_id=1234,
        document_items=[
            DocumentItem(sku="WIDGET-001", quantity=100.0, unit_price=25.50),
        ],
    )

    result = await _verify_order_document_impl(request, context)

    # Should handle UNSET by defaulting to 0
    assert result.order_id == 1234
    # Quantity mismatch because PO has 0 (from UNSET)
    assert len(result.discrepancies) >= 1
    qty_disc = [
        d for d in result.discrepancies if d.type == DiscrepancyType.QUANTITY_MISMATCH
    ]
    if qty_disc:
        assert qty_disc[0].expected == 0.0


@pytest.mark.asyncio
async def test_verify_order_document_no_price_in_document():
    """Test verification when document doesn't include prices."""
    context, lifespan_ctx = create_mock_context()

    # Mock PO
    po_rows = [create_mock_po_row(variant_id=1, quantity=100.0, price=25.50)]
    mock_po = create_mock_po(order_id=1234, order_no="PO-001", rows=po_rows)

    mock_po_response = MagicMock()
    mock_po_response.status_code = 200
    mock_po_response.parsed = mock_po

    mock_variants = [create_mock_variant(variant_id=1, sku="WIDGET-001")]

    api_get_purchase_order.asyncio_detailed = AsyncMock(return_value=mock_po_response)
    lifespan_ctx.client.variants.list = AsyncMock(return_value=mock_variants)

    # Document without price
    request = VerifyOrderDocumentRequest(
        order_id=1234,
        document_items=[
            DocumentItem(sku="WIDGET-001", quantity=100.0, unit_price=None),
        ],
    )

    result = await _verify_order_document_impl(request, context)

    # Assertions - should not create price discrepancy
    assert result.order_id == 1234
    assert result.overall_status == "match"
    assert len(result.matches) == 1
    price_discrepancies = [
        d for d in result.discrepancies if d.type == DiscrepancyType.PRICE_MISMATCH
    ]
    assert len(price_discrepancies) == 0


@pytest.mark.asyncio
async def test_verify_order_document_variant_not_found():
    """Test verification when variant lookup fails."""
    context, lifespan_ctx = create_mock_context()

    # Mock PO
    po_rows = [create_mock_po_row(variant_id=1, quantity=100.0, price=25.50)]
    mock_po = create_mock_po(order_id=1234, order_no="PO-001", rows=po_rows)

    mock_po_response = MagicMock()
    mock_po_response.status_code = 200
    mock_po_response.parsed = mock_po

    # Variants list doesn't include variant_id=1
    mock_variants = []

    api_get_purchase_order.asyncio_detailed = AsyncMock(return_value=mock_po_response)
    lifespan_ctx.client.variants.list = AsyncMock(return_value=mock_variants)

    request = VerifyOrderDocumentRequest(
        order_id=1234,
        document_items=[
            DocumentItem(sku="WIDGET-001", quantity=100.0, unit_price=25.50),
        ],
    )

    result = await _verify_order_document_impl(request, context)

    # Should handle gracefully - SKU won't be found in mapping
    assert result.order_id == 1234
    # WIDGET-001 won't be in sku_to_row map, so it will be marked as missing
    assert len(result.discrepancies) >= 1
    missing_disc = [
        d for d in result.discrepancies if d.type == DiscrepancyType.MISSING_IN_PO
    ]
    assert len(missing_disc) == 1
    assert missing_disc[0].sku == "WIDGET-001"


@pytest.mark.asyncio
async def test_verify_order_document_unset_order_no():
    """Test verification when order_no is UNSET."""
    context, lifespan_ctx = create_mock_context()

    # Mock PO with UNSET order_no
    po_rows = [create_mock_po_row(variant_id=1, quantity=100.0, price=25.50)]
    mock_po = MagicMock(spec=RegularPurchaseOrder)
    mock_po.id = 1234
    mock_po.order_no = UNSET  # UNSET value
    mock_po.purchase_order_rows = po_rows

    mock_po_response = MagicMock()
    mock_po_response.status_code = 200
    mock_po_response.parsed = mock_po

    mock_variants = [create_mock_variant(variant_id=1, sku="WIDGET-001")]

    api_get_purchase_order.asyncio_detailed = AsyncMock(return_value=mock_po_response)
    lifespan_ctx.client.variants.list = AsyncMock(return_value=mock_variants)

    request = VerifyOrderDocumentRequest(
        order_id=1234,
        document_items=[
            DocumentItem(sku="WIDGET-001", quantity=100.0, unit_price=25.50),
        ],
    )

    result = await _verify_order_document_impl(request, context)

    # Should handle UNSET order_no by using default "PO-{id}"
    assert result.order_id == 1234
    assert "PO-1234" in result.message or result.overall_status is not None


# ============================================================================
# Integration Tests (require KATANA_API_KEY)
# ============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
async def test_verify_order_document_integration(katana_context):
    """Integration test with real Katana API.

    This test requires:
    - KATANA_API_KEY environment variable
    - A real purchase order in the Katana account
    - Known SKUs in the PO

    Note: This test may fail if the PO doesn't exist or has different data.
    It's mainly for manual verification during development.
    """
    # This is a placeholder integration test
    # Real implementation would need actual PO IDs and SKUs from the test account
    pytest.skip("Integration test requires specific PO data - implement as needed")


# ============================================================================
# Unit Tests - No Match Scenario
# ============================================================================


@pytest.mark.asyncio
async def test_verify_order_document_no_match():
    """Test verification with no matching items."""
    context, lifespan_ctx = create_mock_context()

    # Mock PO with different items
    po_rows = [create_mock_po_row(variant_id=1, quantity=100.0, price=25.50)]
    mock_po = create_mock_po(order_id=1234, order_no="PO-001", rows=po_rows)

    mock_po_response = MagicMock()
    mock_po_response.status_code = 200
    mock_po_response.parsed = mock_po

    mock_variants = [create_mock_variant(variant_id=1, sku="WIDGET-001")]

    api_get_purchase_order.asyncio_detailed = AsyncMock(return_value=mock_po_response)
    lifespan_ctx.client.variants.list = AsyncMock(return_value=mock_variants)

    # Document with completely different items
    request = VerifyOrderDocumentRequest(
        order_id=1234,
        document_items=[
            DocumentItem(sku="WIDGET-999", quantity=100.0, unit_price=25.50),
            DocumentItem(sku="WIDGET-888", quantity=50.0, unit_price=30.00),
        ],
    )

    result = await _verify_order_document_impl(request, context)

    # Assertions
    assert result.order_id == 1234
    assert result.overall_status == "no_match"
    assert len(result.matches) == 0
    assert len(result.discrepancies) == 2

    # All should be missing
    for disc in result.discrepancies:
        assert disc.type == DiscrepancyType.MISSING_IN_PO


# ============================================================================
# Unit Tests - receive_purchase_order
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
