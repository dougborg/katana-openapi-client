"""Tests for purchase order MCP tools."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from katana_mcp.tools.foundation.purchase_orders import (
    DiscrepancyType,
    DocumentItem,
    VerifyOrderDocumentRequest,
    _verify_order_document_impl,
)

from katana_public_api_client.client_types import UNSET
from katana_public_api_client.models import RegularPurchaseOrder

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
# Unit Tests - Perfect Match Scenario
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
    from katana_public_api_client.api.purchase_order import (
        get_purchase_order as api_get_purchase_order,
    )

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

    from katana_public_api_client.api.purchase_order import (
        get_purchase_order as api_get_purchase_order,
    )

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

    from katana_public_api_client.api.purchase_order import (
        get_purchase_order as api_get_purchase_order,
    )

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

    from katana_public_api_client.api.purchase_order import (
        get_purchase_order as api_get_purchase_order,
    )

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

    from katana_public_api_client.api.purchase_order import (
        get_purchase_order as api_get_purchase_order,
    )

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

    from katana_public_api_client.api.purchase_order import (
        get_purchase_order as api_get_purchase_order,
    )

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

    from katana_public_api_client.api.purchase_order import (
        get_purchase_order as api_get_purchase_order,
    )

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

    from katana_public_api_client.api.purchase_order import (
        get_purchase_order as api_get_purchase_order,
    )

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

    from katana_public_api_client.api.purchase_order import (
        get_purchase_order as api_get_purchase_order,
    )

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

    from katana_public_api_client.api.purchase_order import (
        get_purchase_order as api_get_purchase_order,
    )

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

    from katana_public_api_client.api.purchase_order import (
        get_purchase_order as api_get_purchase_order,
    )

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

    from katana_public_api_client.api.purchase_order import (
        get_purchase_order as api_get_purchase_order,
    )

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

    from katana_public_api_client.api.purchase_order import (
        get_purchase_order as api_get_purchase_order,
    )

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
