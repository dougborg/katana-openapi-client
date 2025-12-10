"""Integration tests for manufacturing order workflows.

These tests verify end-to-end manufacturing workflows against the real Katana API.
They test multi-tool scenarios such as:
- Search for producible items → Create MO for found item
- Create MO (preview) → Confirm MO

All tests require KATANA_API_KEY environment variable.

NOTE: These tests use preview mode by default to avoid creating real orders.
Tests that create actual orders are marked with @pytest.mark.creates_data.
"""

from datetime import UTC, datetime

import pytest
from katana_mcp.tools.foundation.items import (
    SearchItemsRequest,
    _search_items_impl,
)
from katana_mcp.tools.foundation.manufacturing_orders import (
    CreateManufacturingOrderRequest,
    _create_manufacturing_order_impl,
)


@pytest.mark.integration
@pytest.mark.asyncio
class TestManufacturingOrderPreviewWorkflow:
    """Test manufacturing order preview workflows (no actual data creation)."""

    async def test_create_manufacturing_order_preview(self, integration_context):
        """Test creating a manufacturing order in preview mode.

        Preview mode allows reviewing order details without actually
        creating the order in Katana.
        """
        request = CreateManufacturingOrderRequest(
            variant_id=1,  # Test variant ID
            planned_quantity=50,
            location_id=1,  # Test location ID
            additional_info="Integration test - preview only",
            confirm=False,  # Preview mode
        )

        result = await _create_manufacturing_order_impl(request, integration_context)

        # Verify preview response
        assert result.is_preview is True
        assert result.variant_id == 1
        assert result.planned_quantity == 50
        assert result.location_id == 1
        assert result.id is None  # No ID in preview mode

        # Preview should have next actions
        assert len(result.next_actions) > 0

        # Should have warning about missing deadline
        assert any("deadline" in w.lower() for w in result.warnings)

    async def test_create_manufacturing_order_with_deadline(self, integration_context):
        """Test MO preview with all fields including deadline."""
        deadline = datetime.now(UTC)

        request = CreateManufacturingOrderRequest(
            variant_id=1,
            planned_quantity=100,
            location_id=1,
            order_created_date=datetime.now(UTC),
            production_deadline_date=deadline,
            additional_info="Full fields test",
            confirm=False,
        )

        result = await _create_manufacturing_order_impl(request, integration_context)

        assert result.is_preview is True
        assert result.planned_quantity == 100

        # With deadline provided, should not have deadline warning
        assert not any("deadline" in w.lower() for w in result.warnings)

    async def test_search_producible_items_then_create_mo(self, integration_context):
        """Workflow: Search for producible items, then create MO.

        This tests the common workflow of:
        1. Search for items that can be manufactured
        2. Create a manufacturing order for one of them
        """
        # Step 1: Search for items (look for products which are typically producible)
        search_request = SearchItemsRequest(query="product", limit=10)

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
            pytest.skip("No items found to create MO")

        # Step 2: Create MO preview for first producible item
        # (in a real scenario, we'd check if the item is_producible)
        first_item = search_result.items[0]

        mo_request = CreateManufacturingOrderRequest(
            variant_id=first_item.id,
            planned_quantity=25,
            location_id=1,
            additional_info=f"Test MO for {first_item.sku}",
            confirm=False,
        )

        result = await _create_manufacturing_order_impl(mo_request, integration_context)

        assert result.is_preview is True
        assert result.variant_id == first_item.id
        assert result.planned_quantity == 25


@pytest.mark.integration
@pytest.mark.asyncio
class TestManufacturingOrderValidation:
    """Test manufacturing order input validation."""

    async def test_mo_requires_positive_quantity(self, integration_context):
        """Test that MO creation fails with zero or negative quantity."""
        with pytest.raises(ValueError):
            CreateManufacturingOrderRequest(
                variant_id=1,
                planned_quantity=0,  # Zero should fail
                location_id=1,
                confirm=False,
            )

        with pytest.raises(ValueError):
            CreateManufacturingOrderRequest(
                variant_id=1,
                planned_quantity=-10,  # Negative should fail
                location_id=1,
                confirm=False,
            )

    async def test_mo_preview_vs_confirm_behavior(self, integration_context):
        """Test difference between preview and confirm modes."""
        base_request_data = {
            "variant_id": 1,
            "planned_quantity": 10,
            "location_id": 1,
        }

        # Preview mode - should not create
        preview_request = CreateManufacturingOrderRequest(
            **base_request_data,
            confirm=False,
        )
        preview_result = await _create_manufacturing_order_impl(
            preview_request, integration_context
        )

        assert preview_result.is_preview is True
        assert preview_result.id is None  # No ID in preview

        # Note: We don't test confirm=True here as it would create real data


@pytest.mark.integration
@pytest.mark.asyncio
class TestManufacturingWorkflowEdgeCases:
    """Test edge cases in manufacturing order workflows."""

    async def test_large_quantity_mo_preview(self, integration_context):
        """Test MO preview with large quantity."""
        request = CreateManufacturingOrderRequest(
            variant_id=1,
            planned_quantity=100000,
            location_id=1,
            additional_info="Large batch test",
            confirm=False,
        )

        result = await _create_manufacturing_order_impl(request, integration_context)

        assert result.is_preview is True
        assert result.planned_quantity == 100000

    async def test_decimal_quantity_mo_preview(self, integration_context):
        """Test MO preview with decimal quantity."""
        request = CreateManufacturingOrderRequest(
            variant_id=1,
            planned_quantity=12.5,
            location_id=1,
            confirm=False,
        )

        result = await _create_manufacturing_order_impl(request, integration_context)

        assert result.is_preview is True
        assert result.planned_quantity == 12.5

    async def test_mo_with_past_deadline(self, integration_context):
        """Test MO preview with a past deadline (should still allow preview)."""
        past_deadline = datetime(2020, 1, 1, tzinfo=UTC)

        request = CreateManufacturingOrderRequest(
            variant_id=1,
            planned_quantity=10,
            location_id=1,
            production_deadline_date=past_deadline,
            confirm=False,
        )

        result = await _create_manufacturing_order_impl(request, integration_context)

        # Preview should succeed even with past deadline
        assert result.is_preview is True

    async def test_mo_with_long_additional_info(self, integration_context):
        """Test MO preview with long additional info text."""
        long_info = "This is a test note. " * 50  # ~1000 characters

        request = CreateManufacturingOrderRequest(
            variant_id=1,
            planned_quantity=10,
            location_id=1,
            additional_info=long_info,
            confirm=False,
        )

        result = await _create_manufacturing_order_impl(request, integration_context)

        assert result.is_preview is True
        assert result.additional_info == long_info


@pytest.mark.integration
@pytest.mark.asyncio
class TestManufacturingSearchIntegration:
    """Test manufacturing workflows that integrate with search."""

    async def test_search_and_create_multiple_mos(self, integration_context):
        """Workflow: Search for items and create MO previews for multiple items.

        Tests batch planning scenario where multiple MOs are created
        from search results.
        """
        # Search for items
        search_request = SearchItemsRequest(query="widget", limit=5)

        try:
            search_result = await _search_items_impl(
                search_request, integration_context
            )
        except Exception as e:
            error_msg = str(e).lower()
            if any(word in error_msg for word in ["connection", "auth", "timeout"]):
                pytest.skip(f"API unavailable: {e}")
            raise

        if len(search_result.items) < 2:
            pytest.skip("Not enough items found for batch MO test")

        # Create MO previews for first few items
        mo_results = []
        for item in search_result.items[:3]:
            mo_request = CreateManufacturingOrderRequest(
                variant_id=item.id,
                planned_quantity=10,
                location_id=1,
                additional_info=f"Batch test for {item.sku}",
                confirm=False,
            )

            result = await _create_manufacturing_order_impl(
                mo_request, integration_context
            )
            mo_results.append(result)

        # Verify all previews succeeded
        assert len(mo_results) >= 2
        for result in mo_results:
            assert result.is_preview is True
            assert result.planned_quantity == 10
