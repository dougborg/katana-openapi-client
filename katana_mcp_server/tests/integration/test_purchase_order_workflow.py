"""Integration tests for purchase order workflows.

These tests verify end-to-end purchase order workflows against the real Katana API.
They test multi-tool scenarios such as:
- Create PO (preview) → Confirm PO → Verify document
- Search items → Create PO with found items

All tests require KATANA_API_KEY environment variable.

NOTE: These tests use preview mode by default to avoid creating real orders.
Tests that create actual orders are marked with @pytest.mark.creates_data.
"""

from datetime import UTC

import pytest
from katana_mcp.tools.foundation.items import (
    SearchItemsRequest,
    _search_items_impl,
)
from katana_mcp.tools.foundation.purchase_orders import (
    CreatePurchaseOrderRequest,
    PurchaseOrderItem,
    _create_purchase_order_impl,
)


@pytest.mark.integration
@pytest.mark.asyncio
class TestPurchaseOrderPreviewWorkflow:
    """Test purchase order preview workflows (no actual data creation)."""

    async def test_create_purchase_order_preview(
        self, integration_context, unique_order_number
    ):
        """Test creating a purchase order in preview mode.

        Preview mode allows reviewing order details without actually
        creating the order in Katana.
        """
        # Create a preview PO with test data
        request = CreatePurchaseOrderRequest(
            supplier_id=1,  # Test supplier ID
            location_id=1,  # Test location ID
            order_number=unique_order_number,
            items=[
                PurchaseOrderItem(
                    variant_id=1,
                    quantity=10,
                    price_per_unit=25.50,
                ),
                PurchaseOrderItem(
                    variant_id=2,
                    quantity=5,
                    price_per_unit=100.00,
                ),
            ],
            notes="Integration test order - preview only",
            confirm=False,  # Preview mode
        )

        result = await _create_purchase_order_impl(request, integration_context)

        # Verify preview response
        assert result.is_preview is True
        assert result.order_number == unique_order_number
        assert result.supplier_id == 1
        assert result.location_id == 1

        # Verify calculations
        expected_total = (10 * 25.50) + (5 * 100.00)  # 255 + 500 = 755
        assert result.total_cost == expected_total

        # Preview should have next actions
        assert len(result.next_actions) > 0
        assert "Preview" in result.message or "preview" in result.message.lower()

    async def test_search_items_then_create_po_preview(self, integration_context):
        """Workflow: Search for items, then create a PO with found items.

        This tests the common workflow of:
        1. Search for items to order
        2. Create a purchase order for those items
        """
        # Step 1: Search for items
        search_request = SearchItemsRequest(query="material", limit=3)

        try:
            search_result = await _search_items_impl(
                search_request, integration_context
            )
        except Exception as e:
            error_msg = str(e).lower()
            if any(word in error_msg for word in ["connection", "auth", "timeout"]):
                pytest.skip(f"API unavailable: {e}")
            raise

        if not search_result.items:
            pytest.skip("No items found to create PO")

        # Step 2: Create PO preview with found items
        po_items = []
        for item in search_result.items[:3]:
            po_items.append(
                PurchaseOrderItem(
                    variant_id=item.id,
                    quantity=5,
                    price_per_unit=10.00,
                )
            )

        import time

        order_number = f"TEST-PO-{int(time.time())}"

        po_request = CreatePurchaseOrderRequest(
            supplier_id=1,
            location_id=1,
            order_number=order_number,
            items=po_items,
            notes="Test PO created from search results",
            confirm=False,  # Preview only
        )

        result = await _create_purchase_order_impl(po_request, integration_context)

        # Verify preview
        assert result.is_preview is True
        assert len(po_items) > 0
        assert result.total_cost == len(po_items) * 5 * 10.00

    async def test_purchase_order_with_all_options(
        self, integration_context, unique_order_number
    ):
        """Test PO preview with all optional fields populated."""
        from datetime import datetime

        request = CreatePurchaseOrderRequest(
            supplier_id=1,
            location_id=1,
            order_number=unique_order_number,
            items=[
                PurchaseOrderItem(
                    variant_id=1,
                    quantity=100,
                    price_per_unit=5.99,
                    tax_rate_id=1,
                    purchase_uom="box",
                    purchase_uom_conversion_rate=12.0,
                    arrival_date=datetime.now(UTC),
                ),
            ],
            notes="Full options test",
            currency="USD",
            status="NOT_RECEIVED",
            confirm=False,
        )

        result = await _create_purchase_order_impl(request, integration_context)

        assert result.is_preview is True
        assert result.order_number == unique_order_number
        assert result.currency == "USD"
        assert result.status == "NOT_RECEIVED"


@pytest.mark.integration
@pytest.mark.asyncio
class TestPurchaseOrderValidation:
    """Test purchase order input validation."""

    async def test_po_requires_items(self, integration_context):
        """Test that PO creation fails without items."""
        with pytest.raises(ValueError, match="at least 1"):
            CreatePurchaseOrderRequest(
                supplier_id=1,
                location_id=1,
                order_number="TEST-EMPTY",
                items=[],  # Empty items should fail
                confirm=False,
            )

    async def test_po_item_requires_positive_quantity(self, integration_context):
        """Test that PO items require positive quantity."""
        with pytest.raises(ValueError):
            PurchaseOrderItem(
                variant_id=1,
                quantity=0,  # Zero quantity should fail
                price_per_unit=10.00,
            )

        with pytest.raises(ValueError):
            PurchaseOrderItem(
                variant_id=1,
                quantity=-5,  # Negative quantity should fail
                price_per_unit=10.00,
            )

    async def test_po_preview_vs_confirm_behavior(
        self, integration_context, unique_order_number
    ):
        """Test difference between preview and confirm modes."""
        base_request_data = {
            "supplier_id": 1,
            "location_id": 1,
            "order_number": unique_order_number,
            "items": [
                PurchaseOrderItem(
                    variant_id=1,
                    quantity=10,
                    price_per_unit=100.00,
                )
            ],
        }

        # Preview mode
        preview_request = CreatePurchaseOrderRequest(
            **base_request_data,
            confirm=False,
        )
        preview_result = await _create_purchase_order_impl(
            preview_request, integration_context
        )

        assert preview_result.is_preview is True
        assert preview_result.id is None  # No ID in preview

        # Note: We don't test confirm=True here as it would create real data
        # That's tested in a separate test marked with @pytest.mark.creates_data


@pytest.mark.integration
@pytest.mark.asyncio
class TestPurchaseOrderWorkflowEdgeCases:
    """Test edge cases in purchase order workflows."""

    async def test_large_quantity_po_preview(
        self, integration_context, unique_order_number
    ):
        """Test PO preview with large quantities."""
        request = CreatePurchaseOrderRequest(
            supplier_id=1,
            location_id=1,
            order_number=unique_order_number,
            items=[
                PurchaseOrderItem(
                    variant_id=1,
                    quantity=10000,
                    price_per_unit=0.01,  # Small unit price
                ),
            ],
            confirm=False,
        )

        result = await _create_purchase_order_impl(request, integration_context)

        assert result.is_preview is True
        assert result.total_cost == 100.00  # 10000 * 0.01

    async def test_many_items_po_preview(
        self, integration_context, unique_order_number
    ):
        """Test PO preview with many line items."""
        items = [
            PurchaseOrderItem(
                variant_id=i,
                quantity=1,
                price_per_unit=float(i),
            )
            for i in range(1, 21)  # 20 items
        ]

        request = CreatePurchaseOrderRequest(
            supplier_id=1,
            location_id=1,
            order_number=unique_order_number,
            items=items,
            confirm=False,
        )

        result = await _create_purchase_order_impl(request, integration_context)

        assert result.is_preview is True
        # Sum of 1+2+3+...+20 = 210
        assert result.total_cost == sum(range(1, 21))

    async def test_decimal_quantities_po_preview(
        self, integration_context, unique_order_number
    ):
        """Test PO preview with decimal quantities."""
        request = CreatePurchaseOrderRequest(
            supplier_id=1,
            location_id=1,
            order_number=unique_order_number,
            items=[
                PurchaseOrderItem(
                    variant_id=1,
                    quantity=2.5,
                    price_per_unit=10.00,
                ),
                PurchaseOrderItem(
                    variant_id=2,
                    quantity=0.5,
                    price_per_unit=100.00,
                ),
            ],
            confirm=False,
        )

        result = await _create_purchase_order_impl(request, integration_context)

        assert result.is_preview is True
        assert result.total_cost == (2.5 * 10.00) + (0.5 * 100.00)  # 25 + 50 = 75
