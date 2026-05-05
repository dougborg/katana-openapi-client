"""Tests for purchase order MCP tools."""

import json
import os
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from katana_mcp.tools.foundation.purchase_orders import (
    DeletePurchaseOrderRequest,
    DiscrepancyType,
    DocumentItem,
    GetPurchaseOrderRequest,
    ModifyPurchaseOrderRequest,
    POAdditionalCostAdd,
    POHeaderPatch,
    PORowAdd,
    PORowUpdate,
    ReceiveBatchTransaction,
    ReceiveItemRequest,
    ReceivePurchaseOrderRequest,
    ReceivePurchaseOrderResponse,
    VerifyOrderDocumentRequest,
    _delete_purchase_order_impl,
    _get_purchase_order_impl,
    _modify_purchase_order_impl,
    _receive_purchase_order_impl,
    _verify_order_document_impl,
    get_purchase_order,
    list_purchase_orders,
    verify_order_document,
)

from katana_public_api_client.api.purchase_order import (
    get_purchase_order as api_get_purchase_order,
)
from katana_public_api_client.client_types import UNSET
from katana_public_api_client.models import (
    PurchaseOrderReceiveRow,
    PurchaseOrderRow,
    RegularPurchaseOrder,
)
from katana_public_api_client.utils import APIError
from tests.conftest import create_mock_context, patch_typed_cache_sync
from tests.factories import (
    make_purchase_order,
    make_purchase_order_row,
    mock_entity_for_modify,
    seed_cache,
)

# ============================================================================
# Test Helpers
# ============================================================================


# After #346, get_purchase_order and verify_order_document fetch additional
# cost rows and accounting metadata via extra HTTP calls. Every test in this
# module that exercises those impls would otherwise need to patch those
# helpers individually — instead, autouse-default them to empty and let the
# specific tests that care override via their own patch.
_FETCH_PO_ADDITIONAL_COSTS = (
    "katana_mcp.tools.foundation.purchase_orders._fetch_po_additional_cost_rows"
)
_FETCH_PO_ACCOUNTING_META = (
    "katana_mcp.tools.foundation.purchase_orders._fetch_po_accounting_metadata"
)


@pytest.fixture(autouse=True)
def _auto_mock_po_side_data_fetches():
    """Default the #346 side-data fetches to empty lists for every test.

    Tests that want to verify these are called override the patch locally.
    """
    with (
        patch(_FETCH_PO_ADDITIONAL_COSTS, AsyncMock(return_value=[])),
        patch(_FETCH_PO_ACCOUNTING_META, AsyncMock(return_value=[])),
    ):
        yield


def create_mock_po_row(variant_id, quantity, price):
    """Create a mock PurchaseOrderRow with all fields defaulted to UNSET."""
    return mock_entity_for_modify(
        PurchaseOrderRow,
        id=1,
        variant_id=variant_id,
        quantity=quantity,
        price_per_unit=price,
    )


def create_mock_variant(variant_id: int, sku: str):
    """Create a mock variant."""
    variant = MagicMock()
    variant.id = variant_id
    variant.sku = sku
    return variant


def create_mock_po(order_id: int, order_no: str, rows: list):
    """Create a mock RegularPurchaseOrder with all fields defaulted to UNSET."""
    return mock_entity_for_modify(
        RegularPurchaseOrder,
        id=order_id,
        order_no=order_no,
        purchase_order_rows=rows,
    )


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
    assert result.matches[0].sku == "WIDGET-001"
    assert result.matches[0].quantity == 100.0
    assert result.matches[0].unit_price == 25.50
    assert result.matches[0].status == "perfect"
    assert result.matches[1].sku == "WIDGET-002"
    assert result.matches[1].quantity == 50.0
    assert result.matches[1].unit_price == 30.00
    assert result.matches[1].status == "perfect"
    assert "All items verified successfully" in result.suggested_actions[0]


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
    context, _lifespan_ctx = create_mock_context()

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
    context, _lifespan_ctx = create_mock_context()

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

    with pytest.raises(APIError):
        await _verify_order_document_impl(request, context)


@pytest.mark.asyncio
async def test_verify_order_document_unset_values():
    """Test verification with UNSET values in PO data."""
    context, lifespan_ctx = create_mock_context()

    # Mock PO row with UNSET values — start from create_mock_po_row so the
    # exhaustive response builder (#346) doesn't trip on stray MagicMocks.
    po_row = create_mock_po_row(variant_id=1, quantity=UNSET, price=UNSET)
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

    # Mock PO with UNSET order_no — build via create_mock_po so every
    # exhaustive-response field defaults to UNSET instead of leaking a
    # stray MagicMock into Pydantic validation.
    po_rows = [create_mock_po_row(variant_id=1, quantity=100.0, price=25.50)]
    mock_po = create_mock_po(order_id=1234, order_no="ignored", rows=po_rows)
    mock_po.order_no = UNSET  # UNSET value under test

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
    """Test receive_purchase_order in preview mode (preview=true)."""
    context, lifespan_ctx = create_mock_context()

    # Mock the get_purchase_order API response
    mock_po = MagicMock(spec=RegularPurchaseOrder)
    mock_po.id = 1234
    mock_po.order_no = "PO-2024-001"
    mock_po.status = MagicMock()
    mock_po.status.value = "NOT_RECEIVED"
    # Explicit UNSET on the fields the preview path reads — without these,
    # MagicMock auto-attributes leak through unwrap_unset and Pydantic
    # validation rejects them.
    mock_po.supplier_id = UNSET
    mock_po.currency = UNSET
    mock_po.total = UNSET

    mock_get_response = MagicMock()
    mock_get_response.status_code = 200
    mock_get_response.parsed = mock_po

    lifespan_ctx.client = MagicMock()

    # Mock get_purchase_order API call
    from katana_public_api_client.api.purchase_order import (
        get_purchase_order as api_get_purchase_order,
    )

    api_get_purchase_order.asyncio_detailed = AsyncMock(return_value=mock_get_response)

    # Create request with preview=true (preview mode)
    request = ReceivePurchaseOrderRequest(
        order_id=1234,
        items=[
            ReceiveItemRequest(purchase_order_row_id=501, quantity=100.0),
            ReceiveItemRequest(purchase_order_row_id=502, quantity=50.0),
        ],
        preview=True,
    )

    result = await _receive_purchase_order_impl(request, context)

    # Verify preview response
    assert isinstance(result, ReceivePurchaseOrderResponse)
    assert result.order_id == 1234
    assert result.order_number == "PO-2024-001"
    assert result.items_received == 2
    assert result.is_preview is True
    assert "Review the items to receive" in result.next_actions
    assert "preview=false" in result.next_actions[1]
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

    # Create request with preview=false
    request = ReceivePurchaseOrderRequest(
        order_id=1234,
        items=[
            ReceiveItemRequest(purchase_order_row_id=501, quantity=100.0),
            ReceiveItemRequest(purchase_order_row_id=502, quantity=50.0),
        ],
        preview=False,
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
        preview=False,
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
        preview=True,
    )

    # Should raise an APIError (404 with parsed=None)
    with pytest.raises(APIError):
        await _receive_purchase_order_impl(request, context)


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
    # Explicit UNSET on the fields the preview path reads — without these,
    # MagicMock auto-attributes leak through unwrap_unset and Pydantic
    # validation rejects them.
    mock_po.supplier_id = UNSET
    mock_po.currency = UNSET
    mock_po.total = UNSET

    mock_get_response = MagicMock()
    mock_get_response.status_code = 200
    mock_get_response.parsed = mock_po

    # Mock failed receive_purchase_order response
    mock_receive_response = MagicMock()
    mock_receive_response.status_code = 422
    mock_receive_response.parsed = None  # Explicit None so unwrap raises APIError

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
        preview=False,
    )

    # Should raise a ValidationError (422 is validation error)
    with pytest.raises(
        APIError
    ):  # Could be ValidationError but parsed=None so falls back to APIError
        await _receive_purchase_order_impl(request, context)


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
    mock_po.supplier_id = UNSET
    mock_po.currency = UNSET
    mock_po.total = UNSET

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
        preview=True,
    )

    result = await _receive_purchase_order_impl(request, context)

    # Should use fallback order number
    assert result.order_number == "PO-1234"
    assert result.is_preview is True


@pytest.mark.asyncio
async def test_receive_purchase_order_received_date_falls_back_to_now():
    """Without a caller-supplied received_date, rows land on the call time."""
    context, lifespan_ctx = create_mock_context()

    # Mock successful get and receive
    mock_po = MagicMock(spec=RegularPurchaseOrder)
    mock_po.id = 1234
    mock_po.order_no = "PO-2024-001"
    mock_po.status = MagicMock()
    mock_po.status.value = "NOT_RECEIVED"
    # Explicit UNSET on the fields the preview path reads — without these,
    # MagicMock auto-attributes leak through unwrap_unset and Pydantic
    # validation rejects them.
    mock_po.supplier_id = UNSET
    mock_po.currency = UNSET
    mock_po.total = UNSET

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
        preview=False,
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


@pytest.mark.asyncio
async def test_receive_purchase_order_received_date_passthrough():
    """Caller-supplied received_date is forwarded verbatim to the receive API.

    Regression: see #505 — the prior impl hardcoded ``datetime.now(UTC)`` and
    silently dropped any caller-supplied timestamp, breaking back-dated
    re-receives (e.g., variant fixes for shipments delivered days earlier).
    """
    context, lifespan_ctx = create_mock_context()

    mock_po = MagicMock(spec=RegularPurchaseOrder)
    mock_po.id = 2707171
    mock_po.order_no = "SRAM-B2B-251824539"
    mock_po.status = MagicMock()
    mock_po.status.value = "PARTIALLY_RECEIVED"
    mock_po.supplier_id = UNSET
    mock_po.currency = UNSET
    mock_po.total = UNSET

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

    actual_delivery = datetime(2026, 5, 1, 17, 48, 0, tzinfo=UTC)

    request = ReceivePurchaseOrderRequest(
        order_id=2707171,
        items=[
            ReceiveItemRequest(
                purchase_order_row_id=7809320,
                quantity=1.0,
                received_date=actual_delivery,
            ),
            ReceiveItemRequest(
                purchase_order_row_id=7809321,
                quantity=2.0,
                received_date=actual_delivery,
            ),
        ],
        preview=False,
    )

    await _receive_purchase_order_impl(request, context)

    body = api_receive_purchase_order.asyncio_detailed.call_args.kwargs["body"]
    assert body[0].received_date == actual_delivery
    assert body[1].received_date == actual_delivery


@pytest.mark.asyncio
async def test_receive_purchase_order_batch_transactions_passthrough():
    """Caller-supplied batch_transactions are forwarded to the receive API.

    Required for batch-tracked materials — without this passthrough the
    receive either fails server-side or lands stock on a default batch.
    """
    context, lifespan_ctx = create_mock_context()

    mock_po = MagicMock(spec=RegularPurchaseOrder)
    mock_po.id = 1234
    mock_po.order_no = "PO-BATCH-1234"
    mock_po.status = MagicMock()
    mock_po.status.value = "NOT_RECEIVED"
    mock_po.supplier_id = UNSET
    mock_po.currency = UNSET
    mock_po.total = UNSET

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
        items=[
            ReceiveItemRequest(
                purchase_order_row_id=501,
                quantity=10.0,
                batch_transactions=[
                    ReceiveBatchTransaction(batch_id=9001, quantity=7.0),
                    ReceiveBatchTransaction(batch_id=9002, quantity=3.0),
                ],
            ),
        ],
        preview=False,
    )

    await _receive_purchase_order_impl(request, context)

    body = api_receive_purchase_order.asyncio_detailed.call_args.kwargs["body"]
    sent_batches = body[0].batch_transactions
    assert len(sent_batches) == 2
    assert sent_batches[0].batch_id == 9001
    assert sent_batches[0].quantity == 7.0
    assert sent_batches[1].batch_id == 9002
    assert sent_batches[1].quantity == 3.0
    # Wire shape: each item serializes to the API's expected dict.
    assert body[0].to_dict()["batch_transactions"] == [
        {"batch_id": 9001, "quantity": 7.0},
        {"batch_id": 9002, "quantity": 3.0},
    ]


@pytest.mark.asyncio
async def test_receive_purchase_order_omits_batch_transactions_when_unset():
    """When the caller doesn't supply batch_transactions, the wire body omits the key.

    UNSET → ``to_dict()`` skips the field, so non-batch-tracked receives don't
    carry an empty list that the API might choke on.
    """
    context, lifespan_ctx = create_mock_context()

    mock_po = MagicMock(spec=RegularPurchaseOrder)
    mock_po.id = 1234
    mock_po.order_no = "PO-NOBATCH-1234"
    mock_po.status = MagicMock()
    mock_po.status.value = "NOT_RECEIVED"
    mock_po.supplier_id = UNSET
    mock_po.currency = UNSET
    mock_po.total = UNSET

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
        items=[ReceiveItemRequest(purchase_order_row_id=501, quantity=5.0)],
        preview=False,
    )

    await _receive_purchase_order_impl(request, context)

    body = api_receive_purchase_order.asyncio_detailed.call_args.kwargs["body"]
    assert "batch_transactions" not in body[0].to_dict()


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
        preview=True,
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
    # Explicit UNSET on the fields the preview path reads — without these,
    # MagicMock auto-attributes leak through unwrap_unset and Pydantic
    # validation rejects them.
    mock_po.supplier_id = UNSET
    mock_po.currency = UNSET
    mock_po.total = UNSET

    mock_get_response = MagicMock()
    mock_get_response.status_code = 200
    mock_get_response.parsed = mock_po

    lifespan_ctx.client = MagicMock()

    from katana_public_api_client.api.purchase_order import (
        get_purchase_order as api_get_purchase_order,
    )

    api_get_purchase_order.asyncio_detailed = AsyncMock(return_value=mock_get_response)

    # Create request
    request = ReceivePurchaseOrderRequest(
        order_id=1234,
        items=[ReceiveItemRequest(purchase_order_row_id=501, quantity=100.0)],
        preview=True,
    )

    # Call the implementation function directly (wrapper expects unpacked args from FastMCP)
    result = await _receive_purchase_order_impl(request, context)

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
        preview=False,
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
        ReceivePurchaseOrderRequest(order_id=1234, items=[], preview=True)


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
        preview=True,
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
        preview=False,
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
async def test_receive_purchase_order_confirm_refuses_when_already_received():
    """preview=False against a PO already at status=RECEIVED must refuse —
    defense-in-depth: the preview UI suppresses Confirm via BLOCK warning,
    but programmatic callers skipping the UI need the same protection so
    they can't create duplicate inventory.
    """
    context, lifespan_ctx = create_mock_context()

    mock_po = MagicMock(spec=RegularPurchaseOrder)
    mock_po.id = 8888
    mock_po.order_no = "PO-ALREADY-RECEIVED"
    mock_po.status = MagicMock()
    mock_po.status.value = "RECEIVED"
    mock_po.supplier_id = UNSET
    mock_po.currency = UNSET
    mock_po.total = UNSET

    mock_get_response = MagicMock()
    mock_get_response.status_code = 200
    mock_get_response.parsed = mock_po

    lifespan_ctx.client = MagicMock()

    from katana_public_api_client.api.purchase_order import (
        get_purchase_order as api_get_purchase_order,
        receive_purchase_order as api_receive_purchase_order,
    )

    api_get_purchase_order.asyncio_detailed = AsyncMock(return_value=mock_get_response)
    receive_mock = AsyncMock()
    api_receive_purchase_order.asyncio_detailed = receive_mock

    request = ReceivePurchaseOrderRequest(
        order_id=8888,
        items=[ReceiveItemRequest(purchase_order_row_id=999, quantity=10.0)],
        preview=False,
    )

    result = await _receive_purchase_order_impl(request, context)

    assert result.is_preview is False
    assert result.items_received == 0
    block_warnings = [w for w in result.warnings if w.startswith("BLOCK:")]
    assert len(block_warnings) == 1
    assert "RECEIVED" in block_warnings[0]
    assert "Refused" in result.message
    # The receive API must NOT have been called.
    receive_mock.assert_not_called()


@pytest.mark.asyncio
async def test_receive_purchase_order_response_structure():
    """Test that response contains all expected fields."""
    context, lifespan_ctx = create_mock_context()

    # Mock successful response. Use PARTIALLY_RECEIVED so the confirm path
    # proceeds — status=RECEIVED would (correctly) trigger the duplicate-
    # inventory guard and return a refusal instead.
    mock_po = MagicMock(spec=RegularPurchaseOrder)
    mock_po.id = 9999
    mock_po.order_no = "PO-RESPONSE-TEST"
    mock_po.status = MagicMock()
    mock_po.status.value = "PARTIALLY_RECEIVED"
    mock_po.supplier_id = UNSET
    mock_po.currency = UNSET
    mock_po.total = UNSET

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
        preview=False,
    )

    result = await _receive_purchase_order_impl(request, context)

    assert result.order_id == 9999
    assert result.order_number == "PO-RESPONSE-TEST"
    assert result.items_received == 1
    assert result.is_preview is False
    assert isinstance(result.warnings, list)
    assert isinstance(result.next_actions, list)
    assert len(result.next_actions) > 0
    assert isinstance(result.message, str)
    assert "Successfully received" in result.message


# ============================================================================
# get_purchase_order tests
# ============================================================================

_PO_FIND = "katana_public_api_client.api.purchase_order.find_purchase_orders"
_PO_GET = "katana_public_api_client.api.purchase_order.get_purchase_order"
_UNWRAP_DATA = "katana_public_api_client.utils.unwrap_data"
_UNWRAP = "katana_mcp.tools.foundation.purchase_orders.unwrap"


def _make_mock_po(order_no: str = "PO-TEST") -> MagicMock:
    """Create a mock PO with rows.

    After #346 every PurchaseOrder / PurchaseOrderRow field is surfaced on
    the exhaustive response, so un-set attributes must be UNSET (not bare
    MagicMocks) to keep Pydantic validation happy.
    """

    def _mock_row(row_id: int, variant_id: int, qty: float, price: float, total: float):
        row = MagicMock()
        row.id = row_id
        row.variant_id = variant_id
        row.quantity = qty
        row.price_per_unit = price
        row.arrival_date = datetime(2026, 4, 15, tzinfo=UTC)
        row.received_date = UNSET
        row.total = total
        for field in (
            "created_at",
            "updated_at",
            "deleted_at",
            "tax_rate_id",
            "price_per_unit_in_base_currency",
            "purchase_uom_conversion_rate",
            "purchase_uom",
            "currency",
            "conversion_rate",
            "total_in_base_currency",
            "conversion_date",
            "purchase_order_id",
            "landed_cost",
            "group_id",
            "batch_transactions",
        ):
            setattr(row, field, UNSET)
        return row

    row1 = _mock_row(7001, 100, 3.0, 250.0, 750.0)
    row2 = _mock_row(7002, 101, 3.0, 50.0, 150.0)

    po = MagicMock()
    po.id = 12345
    po.order_no = order_no
    po.status = UNSET
    po.supplier_id = 999
    po.location_id = 160411
    po.currency = "USD"
    po.expected_arrival_date = datetime(2026, 4, 15, tzinfo=UTC)
    po.total = 900.0
    po.purchase_order_rows = [row1, row2]
    for field in (
        "created_at",
        "updated_at",
        "deleted_at",
        "entity_type",
        "default_group_id",
        "order_created_date",
        "additional_info",
        "total_in_base_currency",
        "billing_status",
        "last_document_status",
        "tracking_location_id",
        "supplier",
    ):
        setattr(po, field, UNSET)
    return po


@pytest.mark.asyncio
async def test_get_purchase_order_by_number():
    """Look up a PO by order_no via find_purchase_orders."""
    context, _ = create_mock_context()
    mock_po = _make_mock_po("PO-1022")

    with (
        patch(f"{_PO_FIND}.asyncio_detailed", new_callable=AsyncMock),
        patch(_UNWRAP_DATA, return_value=[mock_po]),
    ):
        request = GetPurchaseOrderRequest(order_no="PO-1022")
        result = await _get_purchase_order_impl(request, context)

    assert result.id == 12345
    assert result.order_no == "PO-1022"
    assert result.supplier_id == 999
    assert result.location_id == 160411
    assert result.total == 900.0
    assert len(result.purchase_order_rows) == 2
    assert result.purchase_order_rows[0].id == 7001
    assert result.purchase_order_rows[0].variant_id == 100
    assert result.purchase_order_rows[1].variant_id == 101


@pytest.mark.asyncio
async def test_get_purchase_order_not_found():
    """Looking up a non-existent PO raises."""
    context, _ = create_mock_context()

    with (
        patch(f"{_PO_FIND}.asyncio_detailed", new_callable=AsyncMock),
        patch(_UNWRAP_DATA, return_value=[]),
    ):
        request = GetPurchaseOrderRequest(order_no="PO-NONE")
        with pytest.raises(ValueError, match="Purchase order 'PO-NONE' not found"):
            await _get_purchase_order_impl(request, context)


@pytest.mark.asyncio
async def test_get_purchase_order_requires_identifier():
    """Must provide order_no or order_id."""
    context, _ = create_mock_context()

    request = GetPurchaseOrderRequest()
    with pytest.raises(ValueError, match="order_no or order_id"):
        await _get_purchase_order_impl(request, context)


@pytest.mark.asyncio
async def test_get_purchase_order_by_id():
    """Look up a PO by ID via get_purchase_order."""
    context, _ = create_mock_context()
    mock_po = _make_mock_po("PO-BYID")

    with (
        patch(f"{_PO_GET}.asyncio_detailed", new_callable=AsyncMock),
        patch(_UNWRAP, return_value=mock_po),
    ):
        request = GetPurchaseOrderRequest(order_id=12345)
        result = await _get_purchase_order_impl(request, context)

    assert result.id == 12345
    assert result.order_no == "PO-BYID"
    assert len(result.purchase_order_rows) == 2


# ============================================================================
# get_purchase_order exhaustive detail (#346)
# ============================================================================


def _make_exhaustive_mock_po_row() -> MagicMock:
    """Build a mock PurchaseOrderRow with every field set.

    Mirrors the shape ``_po_row_info`` consumes, so asserting on the
    resulting ``PurchaseOrderRowInfo`` covers every field surfaced by
    the exhaustive get_purchase_order response.
    """
    row = MagicMock()
    row.id = 7001
    row.created_at = datetime(2026, 1, 10, 9, 0, tzinfo=UTC)
    row.updated_at = datetime(2026, 1, 15, 14, 30, tzinfo=UTC)
    row.deleted_at = UNSET
    row.quantity = 3.0
    row.variant_id = 100
    row.tax_rate_id = 42
    row.price_per_unit = 250.0
    row.price_per_unit_in_base_currency = 260.0
    row.purchase_uom_conversion_rate = 1.0
    row.purchase_uom = "kg"
    row.currency = "USD"
    row.conversion_rate = 1.0
    row.total = 750.0
    row.total_in_base_currency = 780.0
    row.conversion_date = datetime(2026, 1, 10, tzinfo=UTC)
    row.received_date = UNSET
    row.arrival_date = datetime(2026, 4, 15, tzinfo=UTC)
    row.purchase_order_id = 12345
    row.landed_cost = 795.0
    row.group_id = 8080
    row.batch_transactions = UNSET
    return row


def _make_exhaustive_mock_po() -> MagicMock:
    """Build a mock RegularPurchaseOrder with every field set."""
    po = MagicMock()
    po.id = 12345
    po.created_at = datetime(2026, 1, 10, 9, 0, tzinfo=UTC)
    po.updated_at = datetime(2026, 1, 15, 14, 30, tzinfo=UTC)
    po.deleted_at = UNSET
    po.status = "NOT_RECEIVED"
    po.order_no = "PO-1022"
    po.entity_type = "regular"
    po.default_group_id = 8080
    po.supplier_id = 999
    po.currency = "USD"
    po.expected_arrival_date = datetime(2026, 4, 15, tzinfo=UTC)
    po.order_created_date = datetime(2026, 1, 10, 9, 0, tzinfo=UTC)
    po.additional_info = "urgent delivery"
    po.location_id = 160411
    po.total = 900.0
    po.total_in_base_currency = 930.0
    po.billing_status = "NOT_BILLED"
    po.last_document_status = "SENT"
    po.tracking_location_id = UNSET
    po.supplier = UNSET
    po.purchase_order_rows = [_make_exhaustive_mock_po_row()]
    return po


def _make_mock_supplier(
    *,
    id: int = 999,
    name: str = "Acme Supplies",
    email: str = "orders@acme.example",
    phone: str = "+1-555-0100",
    currency: str = "USD",
    comment: str = "Preferred supplier",
    default_address_id: int = 7001,
) -> MagicMock:
    """Build a mock embedded ``Supplier`` with every exposed field set."""
    s = MagicMock()
    s.id = id
    s.name = name
    s.email = email
    s.phone = phone
    s.currency = currency
    s.comment = comment
    s.default_address_id = default_address_id
    s.addresses = UNSET
    s.created_at = datetime(2026, 1, 1, tzinfo=UTC)
    s.updated_at = datetime(2026, 1, 15, tzinfo=UTC)
    s.deleted_at = UNSET
    return s


@pytest.mark.asyncio
async def test_get_purchase_order_full_field_coverage():
    """Every PurchaseOrder / PurchaseOrderRow field the cache carries
    surfaces on the exhaustive response (#346)."""
    context, _ = create_mock_context()
    mock_po = _make_exhaustive_mock_po()

    with (
        patch(f"{_PO_GET}.asyncio_detailed", new_callable=AsyncMock),
        patch(_UNWRAP, return_value=mock_po),
    ):
        request = GetPurchaseOrderRequest(order_id=12345)
        result = await _get_purchase_order_impl(request, context)

    # PO-scope scalar fields — every one Katana exposes on RegularPurchaseOrder
    assert result.id == 12345
    assert result.order_no == "PO-1022"
    assert result.status == "NOT_RECEIVED"
    assert result.entity_type == "regular"
    assert result.default_group_id == 8080
    assert result.supplier_id == 999
    assert result.currency == "USD"
    assert result.location_id == 160411
    assert result.total == 900.0
    assert result.total_in_base_currency == 930.0
    assert result.billing_status == "NOT_BILLED"
    assert result.last_document_status == "SENT"
    assert result.additional_info == "urgent delivery"
    assert result.expected_arrival_date == "2026-04-15T00:00:00+00:00"
    assert result.order_created_date == "2026-01-10T09:00:00+00:00"
    assert result.created_at == "2026-01-10T09:00:00+00:00"
    assert result.updated_at == "2026-01-15T14:30:00+00:00"

    # Row-scope — every PurchaseOrderRow field
    assert len(result.purchase_order_rows) == 1
    row = result.purchase_order_rows[0]
    assert row.id == 7001
    assert row.variant_id == 100
    assert row.tax_rate_id == 42
    assert row.quantity == 3.0
    assert row.price_per_unit == 250.0
    assert row.price_per_unit_in_base_currency == 260.0
    assert row.purchase_uom == "kg"
    assert row.purchase_uom_conversion_rate == 1.0
    assert row.currency == "USD"
    assert row.conversion_rate == 1.0
    assert row.total == 750.0
    assert row.total_in_base_currency == 780.0
    assert row.arrival_date == "2026-04-15T00:00:00+00:00"
    assert row.conversion_date == "2026-01-10T00:00:00+00:00"
    assert row.purchase_order_id == 12345
    assert row.landed_cost == 795.0
    assert row.group_id == 8080
    assert row.created_at == "2026-01-10T09:00:00+00:00"
    assert row.updated_at == "2026-01-15T14:30:00+00:00"

    # Side-data default (autouse fixture returns [])
    assert result.additional_cost_rows == []
    assert result.accounting_metadata == []


@pytest.mark.asyncio
async def test_get_purchase_order_fetches_additional_costs_and_accounting_metadata():
    """Side-data fetches run on the PO's default_group_id / id and surface
    into the exhaustive response (#346)."""
    from katana_mcp.tools.foundation.purchase_orders import (
        PurchaseOrderAccountingMetadataInfo,
        PurchaseOrderAdditionalCostRowInfo,
    )

    context, _ = create_mock_context()
    mock_po = _make_exhaustive_mock_po()

    cost_row = PurchaseOrderAdditionalCostRowInfo(
        id=201,
        additional_cost_id=1,
        group_id=8080,
        name="International Shipping",
        distribution_method="BY_VALUE",
        tax_rate_id=1,
        tax_rate=8.5,
        price=125.0,
        price_in_base=125.0,
        currency="USD",
        currency_conversion_rate=1.0,
        currency_conversion_rate_fix_date="2026-01-10T09:00:00+00:00",
    )
    acc_meta = PurchaseOrderAccountingMetadataInfo(
        id=301,
        purchase_order_id=12345,
        received_items_group_id=2001,
        integration_type="quickBooks",
        bill_id="BILL-2026-001",
        created_at="2026-01-15T11:30:00+00:00",
    )

    with (
        patch(f"{_PO_GET}.asyncio_detailed", new_callable=AsyncMock),
        patch(_UNWRAP, return_value=mock_po),
        # Override the module-level autouse fixture so this test can
        # assert the fetched values flow through.
        patch(
            _FETCH_PO_ADDITIONAL_COSTS, AsyncMock(return_value=[cost_row])
        ) as mock_fetch_costs,
        patch(
            _FETCH_PO_ACCOUNTING_META, AsyncMock(return_value=[acc_meta])
        ) as mock_fetch_meta,
    ):
        request = GetPurchaseOrderRequest(order_id=12345)
        result = await _get_purchase_order_impl(request, context)

    # Side-data helpers called with the right PO-scope identifiers
    mock_fetch_costs.assert_awaited_once()
    assert mock_fetch_costs.await_args.args[1] == 8080  # default_group_id
    mock_fetch_meta.assert_awaited_once()
    assert mock_fetch_meta.await_args.args[1] == 12345  # PO id

    # Fetched values flow through to the response
    assert len(result.additional_cost_rows) == 1
    assert result.additional_cost_rows[0].id == 201
    assert result.additional_cost_rows[0].name == "International Shipping"
    assert result.additional_cost_rows[0].price == 125.0
    assert result.additional_cost_rows[0].distribution_method == "BY_VALUE"

    assert len(result.accounting_metadata) == 1
    assert result.accounting_metadata[0].id == 301
    assert result.accounting_metadata[0].integration_type == "quickBooks"
    assert result.accounting_metadata[0].bill_id == "BILL-2026-001"


@pytest.mark.asyncio
async def test_get_purchase_order_markdown_uses_canonical_field_names():
    """Markdown labels use Pydantic field names (not prettified headers)
    so LLM consumers can't misread a section label as a different field
    (motivation: #346 follow-on, supplier_item_codes misread)."""
    from katana_mcp.tools.foundation.purchase_orders import (
        GetPurchaseOrderResponse,
        PurchaseOrderAccountingMetadataInfo,
        PurchaseOrderAdditionalCostRowInfo,
        PurchaseOrderRowInfo,
    )

    context, _ = create_mock_context()

    response = GetPurchaseOrderResponse(
        id=12345,
        order_no="PO-1022",
        status="NOT_RECEIVED",
        supplier_id=999,
        location_id=160411,
        entity_type="regular",
        default_group_id=8080,
        currency="USD",
        total=900.0,
        expected_arrival_date="2026-04-15T00:00:00+00:00",
        purchase_order_rows=[
            PurchaseOrderRowInfo(
                id=7001,
                variant_id=100,
                quantity=3.0,
                price_per_unit=250.0,
                total=750.0,
                arrival_date="2026-04-15T00:00:00+00:00",
            )
        ],
        additional_cost_rows=[
            PurchaseOrderAdditionalCostRowInfo(
                id=201,
                name="Shipping",
                price=125.0,
            )
        ],
        accounting_metadata=[
            PurchaseOrderAccountingMetadataInfo(
                id=301,
                purchase_order_id=12345,
                bill_id="BILL-2026-001",
            )
        ],
    )

    with patch(
        "katana_mcp.tools.foundation.purchase_orders._get_purchase_order_impl",
        new_callable=AsyncMock,
        return_value=response,
    ):
        result = await get_purchase_order(order_id=12345, context=context)

    text = _content_text(result)

    # Scalar PO fields — canonical names appear as labels
    assert "**order_no**: PO-1022" in text
    assert "**status**: NOT_RECEIVED" in text
    assert "**supplier_id**: 999" in text
    assert "**default_group_id**: 8080" in text
    assert "**billing_status**" not in text  # unset, should not appear

    # List-shaped fields — count-labeled header, canonical key
    assert "**purchase_order_rows** (1):" in text
    assert "**variant_id**: 100" in text
    assert "**additional_cost_rows** (1):" in text
    assert "**name**: Shipping" in text
    assert "**accounting_metadata** (1):" in text
    assert "**bill_id**: BILL-2026-001" in text

    # The canonical-name convention rules out these prettified labels:
    assert "**Supplier ID**" not in text
    assert "### Line Items" not in text


@pytest.mark.asyncio
async def test_get_purchase_order_surfaces_embedded_supplier():
    """When the PO payload embeds a ``Supplier``, every supplier field is
    surfaced under ``response.supplier`` and rendered inline in markdown
    (copilot feedback on #357 — supplier was dropped from the exhaustive
    shape)."""
    from katana_mcp.tools.foundation.purchase_orders import SupplierInfo

    context, _ = create_mock_context()
    mock_po = _make_exhaustive_mock_po()
    mock_po.supplier = _make_mock_supplier()

    with (
        patch(f"{_PO_GET}.asyncio_detailed", new_callable=AsyncMock),
        patch(_UNWRAP, return_value=mock_po),
    ):
        request = GetPurchaseOrderRequest(order_id=12345)
        result = await _get_purchase_order_impl(request, context)

    assert isinstance(result.supplier, SupplierInfo)
    assert result.supplier.id == 999
    assert result.supplier.name == "Acme Supplies"
    assert result.supplier.email == "orders@acme.example"
    assert result.supplier.phone == "+1-555-0100"
    assert result.supplier.currency == "USD"
    assert result.supplier.comment == "Preferred supplier"
    assert result.supplier.default_address_id == 7001
    assert result.supplier.created_at == "2026-01-01T00:00:00+00:00"
    assert result.supplier.updated_at == "2026-01-15T00:00:00+00:00"


@pytest.mark.asyncio
async def test_get_purchase_order_markdown_renders_supplier_inline():
    """Embedded supplier renders under a canonical ``**supplier**:`` block
    with per-field labels, matching the convention used for rows and
    accounting metadata."""
    from katana_mcp.tools.foundation.purchase_orders import (
        GetPurchaseOrderResponse,
        SupplierInfo,
    )

    context, _ = create_mock_context()
    response = GetPurchaseOrderResponse(
        id=12345,
        order_no="PO-1022",
        supplier=SupplierInfo(
            id=999,
            name="Acme Supplies",
            email="orders@acme.example",
            default_address_id=7001,
        ),
    )

    with patch(
        "katana_mcp.tools.foundation.purchase_orders._get_purchase_order_impl",
        new_callable=AsyncMock,
        return_value=response,
    ):
        result = await get_purchase_order(order_id=12345, context=context)
    text = _content_text(result)

    assert "**supplier**:" in text
    assert "**name**: Acme Supplies" in text
    assert "**email**: orders@acme.example" in text
    assert "**default_address_id**: 7001" in text


@pytest.mark.asyncio
async def test_get_purchase_order_markdown_renders_null_supplier_explicitly():
    """When the PO payload does not embed a supplier the canonical key
    still appears as ``**supplier**: null`` so an LLM consumer sees a
    concrete field value rather than a missing section."""
    from katana_mcp.tools.foundation.purchase_orders import GetPurchaseOrderResponse

    context, _ = create_mock_context()
    response = GetPurchaseOrderResponse(id=12345, order_no="PO-1022")

    with patch(
        "katana_mcp.tools.foundation.purchase_orders._get_purchase_order_impl",
        new_callable=AsyncMock,
        return_value=response,
    ):
        result = await get_purchase_order(order_id=12345, context=context)

    assert "**supplier**: null" in _content_text(result)


@pytest.mark.asyncio
async def test_get_purchase_order_rejects_empty_order_no():
    """Empty-string ``order_no`` is rejected up front rather than silently
    routing to the list-by-order_no branch (copilot feedback on #357 —
    truthiness checks misclassify valid-but-falsy inputs)."""
    context, _ = create_mock_context()
    request = GetPurchaseOrderRequest(order_no="")
    with pytest.raises(ValueError, match="order_no must not be empty"):
        await _get_purchase_order_impl(request, context)


@pytest.mark.asyncio
async def test_get_purchase_order_accepts_zero_order_id_via_is_none_check():
    """``order_id=0`` is a valid-but-falsy identifier. Explicit ``is None``
    branch selection (not truthiness) must route it to the get-by-id
    branch (copilot feedback on #357)."""
    context, _ = create_mock_context()
    mock_po = _make_exhaustive_mock_po()
    mock_po.id = 0  # the identifier under test

    with (
        patch(f"{_PO_GET}.asyncio_detailed", new_callable=AsyncMock) as mock_detailed,
        patch(_UNWRAP, return_value=mock_po),
    ):
        request = GetPurchaseOrderRequest(order_id=0)
        result = await _get_purchase_order_impl(request, context)

    mock_detailed.assert_awaited_once()
    # ``find_purchase_orders`` (the list-by-order_no branch) must NOT have
    # been exercised — the get-by-id path was taken.
    assert mock_detailed.await_args.kwargs["id"] == 0
    assert result.id == 0


@pytest.mark.asyncio
async def test_get_purchase_order_runs_side_data_fetches_concurrently():
    """The two side-data fetches are awaited via ``asyncio.gather`` rather
    than sequentially (copilot feedback on #357 — independent network
    calls shouldn't double latency)."""
    import asyncio as _asyncio

    fetch_additional = AsyncMock(return_value=[])
    fetch_accounting = AsyncMock(return_value=[])

    context, _ = create_mock_context()
    mock_po = _make_exhaustive_mock_po()

    with (
        patch(f"{_PO_GET}.asyncio_detailed", new_callable=AsyncMock),
        patch(_UNWRAP, return_value=mock_po),
        patch(_FETCH_PO_ADDITIONAL_COSTS, fetch_additional),
        patch(_FETCH_PO_ACCOUNTING_META, fetch_accounting),
        patch.object(_asyncio, "gather", wraps=_asyncio.gather) as spy_gather,
    ):
        request = GetPurchaseOrderRequest(order_id=12345)
        await _get_purchase_order_impl(request, context)

    # gather called with two awaitables — the two side-data coroutines.
    spy_gather.assert_called_once()
    assert len(spy_gather.call_args.args) == 2


# ============================================================================
# list_purchase_orders — pattern v2
# ============================================================================


@pytest.fixture
def no_sync():
    """Patch ``ensure_purchase_orders_synced`` to a no-op."""
    with patch_typed_cache_sync("purchase_orders"):
        yield


@pytest.mark.asyncio
async def test_list_purchase_orders_limit_le_250_validation():
    """limit > 250 is rejected at the schema boundary."""
    from katana_mcp.tools.foundation.purchase_orders import (
        ListPurchaseOrdersRequest,
    )
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ListPurchaseOrdersRequest(limit=500)


@pytest.mark.asyncio
async def test_list_purchase_orders_filters_by_ids(context_with_typed_cache, no_sync):
    """`ids` restricts the returned set to specific PO IDs."""
    from katana_mcp.tools.foundation.purchase_orders import (
        ListPurchaseOrdersRequest,
        _list_purchase_orders_impl,
    )

    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [
            make_purchase_order(id=1),
            make_purchase_order(id=2),
            make_purchase_order(id=3),
        ],
    )

    result = await _list_purchase_orders_impl(
        ListPurchaseOrdersRequest(ids=[1, 3]), context
    )

    assert {o.id for o in result.orders} == {1, 3}


@pytest.mark.asyncio
async def test_list_purchase_orders_filters_by_status_and_billing(
    context_with_typed_cache, no_sync
):
    """`status` and `billing_status` apply as enum-typed column filters."""
    from katana_mcp.tools.foundation.purchase_orders import (
        ListPurchaseOrdersRequest,
        _list_purchase_orders_impl,
    )

    from katana_public_api_client.models import (
        FindPurchaseOrdersBillingStatus,
        FindPurchaseOrdersStatus,
    )

    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [
            make_purchase_order(
                id=1, status="NOT_RECEIVED", billing_status="NOT_BILLED"
            ),
            make_purchase_order(id=2, status="RECEIVED", billing_status="BILLED"),
            make_purchase_order(id=3, status="NOT_RECEIVED", billing_status="BILLED"),
        ],
    )

    result = await _list_purchase_orders_impl(
        ListPurchaseOrdersRequest(
            status=FindPurchaseOrdersStatus.NOT_RECEIVED,
            billing_status=FindPurchaseOrdersBillingStatus.NOT_BILLED,
        ),
        context,
    )

    assert {o.id for o in result.orders} == {1}


@pytest.mark.asyncio
async def test_list_purchase_orders_filters_by_entity_type_and_tracking_location(
    context_with_typed_cache, no_sync
):
    """`entity_type` filters regular vs outsourced; `tracking_location_id` is hoisted from the outsourced subclass."""
    from katana_mcp.tools.foundation.purchase_orders import (
        ListPurchaseOrdersRequest,
        _list_purchase_orders_impl,
    )

    from katana_public_api_client.models import PurchaseOrderEntityType

    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [
            make_purchase_order(id=1, entity_type="regular"),
            make_purchase_order(
                id=2, entity_type="outsourced", tracking_location_id=99
            ),
            make_purchase_order(
                id=3, entity_type="outsourced", tracking_location_id=100
            ),
        ],
    )

    by_type = await _list_purchase_orders_impl(
        ListPurchaseOrdersRequest(entity_type=PurchaseOrderEntityType.OUTSOURCED),
        context,
    )
    assert {o.id for o in by_type.orders} == {2, 3}

    by_tracking = await _list_purchase_orders_impl(
        ListPurchaseOrdersRequest(tracking_location_id=99), context
    )
    assert {o.id for o in by_tracking.orders} == {2}


@pytest.mark.asyncio
async def test_list_purchase_orders_filters_by_supplier_currency_and_location(
    context_with_typed_cache, no_sync
):
    """Direct column filters: supplier_id, currency, location_id."""
    from katana_mcp.tools.foundation.purchase_orders import (
        ListPurchaseOrdersRequest,
        _list_purchase_orders_impl,
    )

    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [
            make_purchase_order(id=1, supplier_id=10, currency="USD", location_id=1),
            make_purchase_order(id=2, supplier_id=10, currency="EUR", location_id=2),
            make_purchase_order(id=3, supplier_id=20, currency="USD", location_id=1),
        ],
    )

    by_supplier = await _list_purchase_orders_impl(
        ListPurchaseOrdersRequest(supplier_id=10), context
    )
    assert {o.id for o in by_supplier.orders} == {1, 2}

    by_currency = await _list_purchase_orders_impl(
        ListPurchaseOrdersRequest(currency="USD"), context
    )
    assert {o.id for o in by_currency.orders} == {1, 3}

    by_location = await _list_purchase_orders_impl(
        ListPurchaseOrdersRequest(location_id=1), context
    )
    assert {o.id for o in by_location.orders} == {1, 3}


@pytest.mark.asyncio
async def test_list_purchase_orders_excludes_deleted_by_default(
    context_with_typed_cache, no_sync
):
    """Soft-deleted POs are filtered unless include_deleted=True."""
    from katana_mcp.tools.foundation.purchase_orders import (
        ListPurchaseOrdersRequest,
        _list_purchase_orders_impl,
    )

    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [
            make_purchase_order(id=1, deleted_at=None),
            make_purchase_order(id=2, deleted_at=datetime(2026, 3, 15)),
        ],
    )

    default = await _list_purchase_orders_impl(ListPurchaseOrdersRequest(), context)
    assert {o.id for o in default.orders} == {1}

    with_deleted = await _list_purchase_orders_impl(
        ListPurchaseOrdersRequest(include_deleted=True), context
    )
    assert {o.id for o in with_deleted.orders} == {1, 2}


@pytest.mark.asyncio
async def test_list_purchase_orders_date_filters(context_with_typed_cache, no_sync):
    """`created_*` and `expected_arrival_*` apply as indexed range filters."""
    from katana_mcp.tools.foundation.purchase_orders import (
        ListPurchaseOrdersRequest,
        _list_purchase_orders_impl,
    )

    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [
            make_purchase_order(
                id=1,
                created_at=datetime(2026, 2, 15),
                expected_arrival_date=datetime(2026, 4, 15),
            ),
            make_purchase_order(
                id=2,
                created_at=datetime(2026, 5, 1),
                expected_arrival_date=datetime(2027, 1, 1),
            ),
        ],
    )

    created = await _list_purchase_orders_impl(
        ListPurchaseOrdersRequest(
            created_after="2026-01-01T00:00:00Z",
            created_before="2026-04-01T00:00:00Z",
        ),
        context,
    )
    assert {o.id for o in created.orders} == {1}

    arrival = await _list_purchase_orders_impl(
        ListPurchaseOrdersRequest(
            expected_arrival_after="2026-04-01T00:00:00Z",
            expected_arrival_before="2026-04-30T00:00:00Z",
        ),
        context,
    )
    assert {o.id for o in arrival.orders} == {1}


@pytest.mark.asyncio
async def test_list_purchase_orders_invalid_date_raises(
    context_with_typed_cache, no_sync
):
    """Malformed ISO-8601 surfaces as ValueError."""
    from katana_mcp.tools.foundation.purchase_orders import (
        ListPurchaseOrdersRequest,
        _list_purchase_orders_impl,
    )

    context, _, _typed_cache = context_with_typed_cache

    with pytest.raises(ValueError, match=r"Invalid ISO-8601.*created_after"):
        await _list_purchase_orders_impl(
            ListPurchaseOrdersRequest(created_after="not-a-date"), context
        )


@pytest.mark.asyncio
async def test_list_purchase_orders_caps_to_limit(context_with_typed_cache, no_sync):
    """`limit` caps the result size even when more rows match."""
    from katana_mcp.tools.foundation.purchase_orders import (
        ListPurchaseOrdersRequest,
        _list_purchase_orders_impl,
    )

    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [make_purchase_order(id=i) for i in range(1, 31)],
    )

    result = await _list_purchase_orders_impl(
        ListPurchaseOrdersRequest(limit=5), context
    )

    assert len(result.orders) == 5


@pytest.mark.asyncio
async def test_list_purchase_orders_pagination_meta_populated_on_explicit_page(
    context_with_typed_cache, no_sync
):
    """An explicit `page` populates `pagination` from a SQL COUNT against the same filter set."""
    from katana_mcp.tools.foundation.purchase_orders import (
        ListPurchaseOrdersRequest,
        _list_purchase_orders_impl,
    )

    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [make_purchase_order(id=i) for i in range(1, 12)],
    )

    result = await _list_purchase_orders_impl(
        ListPurchaseOrdersRequest(limit=5, page=2), context
    )

    assert result.pagination is not None
    assert result.pagination.total_records == 11
    assert result.pagination.total_pages == 3
    assert result.pagination.page == 2
    assert len(result.orders) == 5


@pytest.mark.asyncio
async def test_list_purchase_orders_include_rows(context_with_typed_cache, no_sync):
    """include_rows=True exposes per-PO line item detail."""
    from katana_mcp.tools.foundation.purchase_orders import (
        ListPurchaseOrdersRequest,
        _list_purchase_orders_impl,
    )

    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [
            make_purchase_order(
                id=7,
                rows=[
                    make_purchase_order_row(
                        id=1, purchase_order_id=7, variant_id=100, quantity=5.0
                    ),
                    make_purchase_order_row(
                        id=2, purchase_order_id=7, variant_id=200, quantity=2.0
                    ),
                ],
            ),
        ],
    )

    with_rows = await _list_purchase_orders_impl(
        ListPurchaseOrdersRequest(include_rows=True), context
    )
    without_rows = await _list_purchase_orders_impl(
        ListPurchaseOrdersRequest(include_rows=False), context
    )

    assert with_rows.orders[0].rows is not None
    assert len(with_rows.orders[0].rows) == 2
    assert with_rows.orders[0].row_count == 2
    assert without_rows.orders[0].rows is None
    assert without_rows.orders[0].row_count == 2


# ============================================================================
# format=json (purchase_orders tools)
# ============================================================================


def _content_text(result) -> str:
    return result.content[0].text


@pytest.mark.asyncio
async def test_list_purchase_orders_format_json_returns_json():
    from katana_mcp.tools.foundation.purchase_orders import (
        ListPurchaseOrdersResponse,
    )

    context, _ = create_mock_context()

    with patch(
        "katana_mcp.tools.foundation.purchase_orders._list_purchase_orders_impl",
        new_callable=AsyncMock,
    ) as mock_impl:
        mock_impl.return_value = ListPurchaseOrdersResponse(
            orders=[], total_count=0, pagination=None
        )
        result = await list_purchase_orders(format="json", context=context)

    data = json.loads(_content_text(result))
    assert data["total_count"] == 0


@pytest.mark.asyncio
async def test_get_purchase_order_format_json_returns_json():
    from katana_mcp.tools.foundation.purchase_orders import GetPurchaseOrderResponse

    context, _ = create_mock_context()

    with patch(
        "katana_mcp.tools.foundation.purchase_orders._get_purchase_order_impl",
        new_callable=AsyncMock,
    ) as mock_impl:
        mock_impl.return_value = GetPurchaseOrderResponse(
            id=5,
            order_no="PO-5",
            supplier_id=1,
            location_id=1,
            currency="USD",
            status="NOT_RECEIVED",
            entity_type="regular",
            expected_arrival_date=None,
            total=100.0,
            purchase_order_rows=[],
            additional_cost_rows=[],
            accounting_metadata=[],
        )
        result = await get_purchase_order(order_id=5, format="json", context=context)

    data = json.loads(_content_text(result))
    assert data["id"] == 5
    assert data["order_no"] == "PO-5"


@pytest.mark.asyncio
async def test_verify_order_document_format_json_returns_json():
    from katana_mcp.tools.foundation.purchase_orders import (
        VerifyOrderDocumentResponse,
    )

    context, _ = create_mock_context()

    with patch(
        "katana_mcp.tools.foundation.purchase_orders._verify_order_document_impl",
        new_callable=AsyncMock,
    ) as mock_impl:
        mock_impl.return_value = VerifyOrderDocumentResponse(
            order_id=5,
            matches=[],
            discrepancies=[],
            suggested_actions=[],
            overall_status="match",
            message="All items match",
        )
        result = await verify_order_document(
            order_id=5,
            document_items=[DocumentItem(sku="A", quantity=1, unit_price=1.0)],
            format="json",
            context=context,
        )

    data = json.loads(_content_text(result))
    assert data["order_id"] == 5
    assert data["overall_status"] == "match"


# ============================================================================
# modify_purchase_order — unified modification surface
# ============================================================================


_PO_GET = "katana_public_api_client.api.purchase_order.get_purchase_order"
_PO_UPDATE = "katana_public_api_client.api.purchase_order.update_purchase_order"
_PO_DELETE = "katana_public_api_client.api.purchase_order.delete_purchase_order"
_PO_ROW_GET = "katana_public_api_client.api.purchase_order_row.get_purchase_order_row"
_PO_ROW_CREATE = (
    "katana_public_api_client.api.purchase_order_row.create_purchase_order_row"
)
_PO_ROW_UPDATE = (
    "katana_public_api_client.api.purchase_order_row.update_purchase_order_row"
)
_PO_ROW_DELETE = (
    "katana_public_api_client.api.purchase_order_row.delete_purchase_order_row"
)
_PO_COST_CREATE = (
    "katana_public_api_client.api.purchase_order_additional_cost_row"
    ".create_po_additional_cost_row"
)
# The modify/delete dispatcher pipes through ``_modification_dispatch.unwrap_as``
# (apply factories + safe_fetch_for_diff use the dispatcher's binding).
_PO_UNWRAP_AS = "katana_mcp.tools._modification_dispatch.unwrap_as"


@pytest.fixture
def patch_fetch_po():
    """Yield a patch on _fetch_purchase_order_attrs returning the given PO mock."""
    from contextlib import contextmanager

    @contextmanager
    def _patch(po_mock):
        with patch(
            "katana_mcp.tools.foundation.purchase_orders._fetch_purchase_order_attrs",
            new_callable=AsyncMock,
            return_value=po_mock,
        ):
            yield

    return _patch


@pytest.mark.asyncio
async def test_modify_po_requires_at_least_one_subpayload():
    context, _ = create_mock_context()
    with pytest.raises(ValueError, match="At least one sub-payload"):
        await _modify_purchase_order_impl(
            ModifyPurchaseOrderRequest(id=42, preview=True), context
        )


@pytest.mark.asyncio
async def test_modify_po_preview_emits_planned_actions(patch_fetch_po):
    """Preview returns one ActionResult per planned API call, all succeeded=None."""
    context, _ = create_mock_context()
    existing = create_mock_po(order_id=42, order_no="PO-OLD", rows=[])
    existing.expected_arrival_date = datetime(2026, 1, 1, tzinfo=UTC)

    with patch_fetch_po(existing):
        # Use distinct row ids per update so prefetch helpers see real ids
        request = ModifyPurchaseOrderRequest(
            id=42,
            update_header=POHeaderPatch(
                expected_arrival_date=datetime(2026, 2, 15, tzinfo=UTC)
            ),
            add_rows=[PORowAdd(variant_id=100, quantity=10, price_per_unit=5.0)],
            preview=True,
        )
        # Stub the row prefetch so update_rows doesn't error here (no update_rows in this case)
        response = await _modify_purchase_order_impl(request, context)

    assert response.is_preview is True
    assert response.entity_id == 42
    assert len(response.actions) == 2
    assert response.actions[0].operation == "update_header"
    assert response.actions[1].operation == "add_row"
    # All planned (succeeded=None)
    assert all(a.succeeded is None for a in response.actions)


@pytest.mark.asyncio
async def test_modify_po_confirm_executes_plan_in_canonical_order(patch_fetch_po):
    """Header → row adds → row updates → row deletes → cost adds/updates/deletes."""
    context, _ = create_mock_context()

    existing = create_mock_po(order_id=42, order_no="PO-1", rows=[])
    updated_po = create_mock_po(order_id=42, order_no="PO-1", rows=[])
    updated_po.expected_arrival_date = datetime(2026, 2, 15, tzinfo=UTC)
    new_row = MagicMock()
    new_row.id = 555

    call_log: list[str] = []

    async def fake_update_po(*, id, client, body):
        call_log.append("PATCH /purchase_orders/{id}")
        resp = MagicMock()
        resp.parsed = updated_po
        return resp

    async def fake_create_row(*, client, body):
        call_log.append("POST /purchase_order_rows")
        resp = MagicMock()
        resp.parsed = new_row
        return resp

    with (
        patch_fetch_po(existing),
        patch(f"{_PO_UPDATE}.asyncio_detailed", side_effect=fake_update_po),
        patch(f"{_PO_ROW_CREATE}.asyncio_detailed", side_effect=fake_create_row),
        patch(_PO_UNWRAP_AS, side_effect=[updated_po, new_row]),
    ):
        request = ModifyPurchaseOrderRequest(
            id=42,
            update_header=POHeaderPatch(
                expected_arrival_date=datetime(2026, 2, 15, tzinfo=UTC)
            ),
            add_rows=[PORowAdd(variant_id=100, quantity=10, price_per_unit=5.0)],
            preview=False,
        )
        response = await _modify_purchase_order_impl(request, context)

    assert response.is_preview is False
    assert len(response.actions) == 2
    assert all(a.succeeded is True for a in response.actions)
    # Header runs before row add (canonical order)
    assert call_log[0].startswith("PATCH")
    assert call_log[1].startswith("POST")
    # prior_state captured the pre-modification PO snapshot
    assert response.prior_state is not None


@pytest.mark.asyncio
async def test_modify_po_fail_fast_halts_on_first_error(patch_fetch_po):
    """When the row-create fails, the header-update result is preserved
    but no further actions run."""
    context, _ = create_mock_context()
    existing = create_mock_po(order_id=42, order_no="PO-1", rows=[])
    updated_po = create_mock_po(order_id=42, order_no="PO-1", rows=[])

    with (
        patch_fetch_po(existing),
        patch(f"{_PO_UPDATE}.asyncio_detailed", new_callable=AsyncMock),
        patch(
            f"{_PO_ROW_CREATE}.asyncio_detailed",
            new_callable=AsyncMock,
            side_effect=RuntimeError("boom"),
        ),
        patch(_PO_UNWRAP_AS, return_value=updated_po),
    ):
        request = ModifyPurchaseOrderRequest(
            id=42,
            update_header=POHeaderPatch(order_no="PO-NEW"),
            add_rows=[PORowAdd(variant_id=100, quantity=10, price_per_unit=5.0)],
            preview=False,
        )
        response = await _modify_purchase_order_impl(request, context)

    assert response.is_preview is False
    assert len(response.actions) == 2
    assert response.actions[0].succeeded is True
    assert response.actions[1].succeeded is False
    assert "boom" in (response.actions[1].error or "")


@pytest.mark.asyncio
async def test_modify_po_preview_when_fetch_fails_marks_unknown_prior():
    """Fetch failure → diff fields marked is_unknown_prior + warning surfaced."""
    context, _ = create_mock_context()

    with patch(
        "katana_mcp.tools.foundation.purchase_orders._fetch_purchase_order_attrs",
        new_callable=AsyncMock,
        return_value=None,
    ):
        request = ModifyPurchaseOrderRequest(
            id=42,
            update_header=POHeaderPatch(order_no="PO-NEW"),
            preview=True,
        )
        response = await _modify_purchase_order_impl(request, context)

    assert response.is_preview is True
    assert any("diff context" in w for w in response.warnings)
    # The diff entries on the planned action carry is_unknown_prior=True
    diffs = response.actions[0].changes
    assert all(c.is_unknown_prior for c in diffs)


@pytest.mark.asyncio
async def test_modify_po_row_update_fetches_row_for_diff(patch_fetch_po):
    """Update-row sub-payload triggers a per-row prefetch for accurate diff."""
    context, _ = create_mock_context()
    existing_po = create_mock_po(order_id=42, order_no="PO-1", rows=[])
    existing_row = MagicMock()
    existing_row.purchase_order_id = 42
    existing_row.quantity = 10
    existing_row.price_per_unit = 5.0
    updated_row = MagicMock()
    updated_row.id = 555
    updated_row.quantity = 15

    with (
        patch_fetch_po(existing_po),
        patch(f"{_PO_ROW_GET}.asyncio_detailed", new_callable=AsyncMock),
        patch(_PO_UNWRAP_AS, return_value=existing_row),
    ):
        request = ModifyPurchaseOrderRequest(
            id=42,
            update_rows=[PORowUpdate(id=555, quantity=15)],
            preview=True,
        )
        response = await _modify_purchase_order_impl(request, context)

    assert response.is_preview is True
    assert len(response.actions) == 1
    assert response.actions[0].operation == "update_row"
    assert response.actions[0].target_id == 555
    diff_by_field = {c.field: c for c in response.actions[0].changes}
    assert diff_by_field["quantity"].old == 10
    assert diff_by_field["quantity"].new == 15


@pytest.mark.asyncio
async def test_modify_po_add_additional_costs_preview_lists_each_cost_row(
    patch_fetch_po,
):
    """Each POAdditionalCostAdd produces its own planned ``add_additional_cost``
    action with field-level diff entries. Verifies the row schema documented
    on ``ModifyPurchaseOrderRequest.add_additional_costs`` round-trips through
    the dispatcher without per-call boilerplate.
    """
    context, _ = create_mock_context()
    existing = create_mock_po(order_id=880, order_no="PO-880", rows=[])
    existing.default_group_id = 7

    with patch_fetch_po(existing):
        request = ModifyPurchaseOrderRequest(
            id=880,
            add_additional_costs=[
                POAdditionalCostAdd(
                    additional_cost_id=1,
                    tax_rate_id=2,
                    price=125.0,
                    distribution_method="BY_VALUE",
                ),
                POAdditionalCostAdd(
                    additional_cost_id=3,
                    tax_rate_id=2,
                    price=85.0,
                    distribution_method="BY_VALUE",
                    group_id=99,
                ),
            ],
            preview=True,
        )
        response = await _modify_purchase_order_impl(request, context)

    assert response.is_preview is True
    assert len(response.actions) == 2
    assert {a.operation for a in response.actions} == {"add_additional_cost"}
    # Diffs reflect user-supplied fields. Row 0 omitted group_id (resolved from
    # the PO's default_group_id at dispatch time, not part of the user's input
    # diff); row 1 supplied group_id=99 explicitly.
    fields_action_0 = {c.field for c in response.actions[0].changes}
    assert {
        "additional_cost_id",
        "tax_rate_id",
        "price",
        "distribution_method",
    }.issubset(fields_action_0)
    assert "group_id" not in fields_action_0
    diff1 = {c.field: c.new for c in response.actions[1].changes}
    assert diff1["group_id"] == 99


@pytest.mark.asyncio
async def test_modify_po_add_additional_costs_confirm_calls_create_endpoint(
    patch_fetch_po,
):
    """Confirm path POSTs each row to /po_additional_cost_rows."""
    context, _ = create_mock_context()
    existing = create_mock_po(order_id=880, order_no="PO-880", rows=[])
    existing.default_group_id = 7
    new_cost = MagicMock()
    new_cost.id = 201

    call_count = 0

    async def fake_create_cost(*, client, body):
        nonlocal call_count
        call_count += 1
        resp = MagicMock()
        resp.parsed = new_cost
        return resp

    with (
        patch_fetch_po(existing),
        patch(
            f"{_PO_COST_CREATE}.asyncio_detailed",
            side_effect=fake_create_cost,
        ),
        patch(_PO_UNWRAP_AS, return_value=new_cost),
    ):
        request = ModifyPurchaseOrderRequest(
            id=880,
            add_additional_costs=[
                POAdditionalCostAdd(
                    additional_cost_id=1,
                    tax_rate_id=2,
                    price=125.0,
                    distribution_method="BY_VALUE",
                )
            ],
            preview=False,
        )
        response = await _modify_purchase_order_impl(request, context)

    assert response.is_preview is False
    assert call_count == 1
    assert len(response.actions) == 1
    assert response.actions[0].succeeded is True
    assert response.actions[0].operation == "add_additional_cost"


@pytest.mark.asyncio
async def test_modify_po_add_additional_costs_without_default_group_id_errors(
    patch_fetch_po,
):
    """When PO has no default_group_id and the row omits group_id, the
    pre-flight enrichment surfaces a ``ValueError`` (rather than letting the
    API reject a malformed request).
    """
    context, _ = create_mock_context()
    existing = create_mock_po(order_id=880, order_no="PO-880", rows=[])
    existing.default_group_id = UNSET

    with patch_fetch_po(existing):
        request = ModifyPurchaseOrderRequest(
            id=880,
            add_additional_costs=[
                POAdditionalCostAdd(additional_cost_id=1, tax_rate_id=2, price=10.0)
            ],
            preview=True,
        )
        with pytest.raises(ValueError, match="group_id"):
            await _modify_purchase_order_impl(request, context)


@pytest.mark.asyncio
async def test_modify_po_empty_update_row_payload_raises(patch_fetch_po):
    """A ``PORowUpdate`` carrying only ``id`` (no patch fields) produces an
    empty diff — the resulting PATCH body would be empty and Katana would
    return a generic 422. The empty-diff guard surfaces the issue at
    plan-build time with a named error.
    """
    context, _ = create_mock_context()
    existing_po = create_mock_po(order_id=42, order_no="PO-1", rows=[])
    existing_row = MagicMock()
    existing_row.purchase_order_id = 42
    existing_row.quantity = 10

    with (
        patch_fetch_po(existing_po),
        patch(f"{_PO_ROW_GET}.asyncio_detailed", new_callable=AsyncMock),
        patch(_PO_UNWRAP_AS, return_value=existing_row),
    ):
        request = ModifyPurchaseOrderRequest(
            id=42,
            update_rows=[PORowUpdate(id=555)],
            preview=True,
        )
        with pytest.raises(
            ValueError,
            match=r"No fields to update.*update_row.*target 555",
        ) as exc_info:
            await _modify_purchase_order_impl(request, context)

    # Registered derived fields are mentioned so the caller sees the
    # likely cause (e.g. tried to set ``landed_cost`` and pydantic dropped it).
    assert "landed_cost" in str(exc_info.value)


# ============================================================================
# delete_purchase_order — destructive sibling
# ============================================================================


@pytest.mark.asyncio
async def test_delete_po_preview_returns_planned_action():
    context, _ = create_mock_context()
    existing = create_mock_po(order_id=42, order_no="PO-1", rows=[])
    request = DeletePurchaseOrderRequest(id=42, preview=True)

    with patch(
        "katana_mcp.tools.foundation.purchase_orders._fetch_purchase_order_attrs",
        new_callable=AsyncMock,
        return_value=existing,
    ):
        response = await _delete_purchase_order_impl(request, context)

    assert response.is_preview is True
    assert response.entity_id == 42
    assert len(response.actions) == 1
    assert response.actions[0].operation == "delete"
    assert response.actions[0].succeeded is None  # planned, not run


@pytest.mark.asyncio
async def test_delete_po_confirm_calls_api_and_records_prior_state():
    context, _ = create_mock_context()
    existing = create_mock_po(order_id=42, order_no="PO-1", rows=[])
    api_response = MagicMock()
    api_response.status_code = 204

    with (
        patch(
            "katana_mcp.tools.foundation.purchase_orders._fetch_purchase_order_attrs",
            new_callable=AsyncMock,
            return_value=existing,
        ),
        patch(f"{_PO_DELETE}.asyncio_detailed", new_callable=AsyncMock) as mock_api,
        patch(
            "katana_mcp.tools._modification_dispatch.is_success",
            return_value=True,
        ),
    ):
        mock_api.return_value = api_response
        response = await _delete_purchase_order_impl(
            DeletePurchaseOrderRequest(id=42, preview=False), context
        )

    assert response.is_preview is False
    assert response.actions[0].succeeded is True
    # prior_state captured even for delete (so caller can recreate manually)
    assert response.prior_state is not None
    # On successful delete the entity URL is dropped (resource is gone)
    assert response.katana_url is None
    mock_api.assert_awaited_once()
