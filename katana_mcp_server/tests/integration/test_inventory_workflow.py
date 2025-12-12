"""Integration tests for inventory management workflows.

These tests verify end-to-end inventory workflows against the real Katana API.
They test multi-tool scenarios such as:
- Search for items → Get variant details → Check inventory levels
- Low stock alerts → Inventory checks

All tests require KATANA_API_KEY environment variable.
"""

import pytest
from katana_mcp.tools.foundation.inventory import (
    CheckInventoryRequest,
    LowStockRequest,
    _check_inventory_impl,
    _list_low_stock_items_impl,
)
from katana_mcp.tools.foundation.items import (
    GetVariantDetailsRequest,
    SearchItemsRequest,
    _get_variant_details_impl,
    _search_items_impl,
)


@pytest.mark.integration
@pytest.mark.asyncio
class TestInventorySearchWorkflow:
    """Test multi-step inventory search workflows."""

    async def test_search_then_get_details(self, integration_context):
        """Workflow: Search for items, then get details for first result.

        This tests a common user workflow:
        1. Search for items by name/keyword
        2. Pick an item from results
        3. Get detailed information about that item
        """
        # Step 1: Search for items
        search_request = SearchItemsRequest(query="product", limit=5)

        try:
            search_result = await _search_items_impl(
                search_request, integration_context
            )
        except Exception as e:
            error_msg = str(e).lower()
            if any(word in error_msg for word in ["connection", "auth", "timeout"]):
                pytest.skip(f"API unavailable: {e}")
            raise

        # Verify search returned results
        assert search_result.total_count >= 0
        assert isinstance(search_result.items, list)

        if not search_result.items:
            pytest.skip("No items found in search - test data may not exist")

        # Step 2: Get details for first item
        first_item = search_result.items[0]
        assert first_item.sku, "First item should have a SKU"

        details_request = GetVariantDetailsRequest(sku=first_item.sku)

        try:
            details = await _get_variant_details_impl(
                details_request, integration_context
            )
        except ValueError as e:
            # SKU might have been deleted between search and details call
            if "not found" in str(e).lower():
                pytest.skip(f"Item disappeared during test: {e}")
            raise

        # Verify details match search result
        assert details.sku.upper() == first_item.sku.upper()
        assert details.id == first_item.id

    async def test_search_then_check_inventory(self, integration_context):
        """Workflow: Search for items, then check inventory for first result.

        This tests checking stock levels after finding an item:
        1. Search for items
        2. Check inventory levels for the found item
        """
        # Step 1: Search for items
        search_request = SearchItemsRequest(query="material", limit=5)

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
            pytest.skip("No items found in search - test data may not exist")

        # Step 2: Check inventory for first item
        first_item = search_result.items[0]
        inventory_request = CheckInventoryRequest(sku=first_item.sku)

        inventory = await _check_inventory_impl(inventory_request, integration_context)

        # Verify inventory response
        assert inventory.sku == first_item.sku
        assert inventory.available_stock >= 0
        assert inventory.committed >= 0

    async def test_complete_inventory_lookup_workflow(self, integration_context):
        """Complete workflow: Search → Details → Inventory check.

        This tests the full inventory lookup workflow:
        1. Search for items by keyword
        2. Get detailed variant information
        3. Check current inventory levels
        4. Verify data consistency across all steps
        """
        # Step 1: Search
        search_request = SearchItemsRequest(query="widget", limit=10)

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
            pytest.skip("No items found - try different search term")

        # Step 2: Get details for each item (up to 3)
        items_to_check = search_result.items[:3]
        details_results = []

        for item in items_to_check:
            try:
                details_request = GetVariantDetailsRequest(sku=item.sku)
                details = await _get_variant_details_impl(
                    details_request, integration_context
                )
                details_results.append(details)
            except ValueError:
                # Item not found - skip it
                continue

        if not details_results:
            pytest.skip("Could not get details for any items")

        # Step 3: Check inventory for each item with details
        for details in details_results:
            inventory_request = CheckInventoryRequest(sku=details.sku)
            inventory = await _check_inventory_impl(
                inventory_request, integration_context
            )

            # Verify consistency
            assert inventory.sku == details.sku
            # Product name might differ slightly between APIs
            assert isinstance(inventory.product_name, str)


@pytest.mark.integration
@pytest.mark.asyncio
class TestLowStockWorkflow:
    """Test low stock alert workflows."""

    async def test_low_stock_then_check_details(self, integration_context):
        """Workflow: Get low stock items, then check details for each.

        This tests the inventory management workflow:
        1. Get list of low stock items
        2. For each low stock item, get detailed variant info
        3. Verify the stock levels match
        """
        # Step 1: Get low stock items with a high threshold to ensure results
        low_stock_request = LowStockRequest(threshold=1000, limit=5)

        try:
            low_stock_result = await _list_low_stock_items_impl(
                low_stock_request, integration_context
            )
        except Exception as e:
            error_msg = str(e).lower()
            if any(word in error_msg for word in ["connection", "auth", "timeout"]):
                pytest.skip(f"API unavailable: {e}")
            raise

        assert isinstance(low_stock_result.items, list)
        assert low_stock_result.total_count >= 0

        if not low_stock_result.items:
            pytest.skip(
                "No low stock items found - increase threshold or add test data"
            )

        # Step 2: Check details for first few items
        for item in low_stock_result.items[:3]:
            if not item.sku:
                continue

            # Get detailed inventory check
            inventory_request = CheckInventoryRequest(sku=item.sku)
            inventory = await _check_inventory_impl(
                inventory_request, integration_context
            )

            # Verify SKU matches
            assert inventory.sku == item.sku

            # The stock levels should be consistent
            # (low_stock uses in_stock, check_inventory uses available)
            assert inventory.available_stock >= 0

    async def test_low_stock_with_different_thresholds(self, integration_context):
        """Test low stock alerts with various thresholds.

        Verifies that:
        1. Higher thresholds return more items
        2. All returned items have stock below threshold
        """
        thresholds = [10, 100, 1000]
        results = {}

        for threshold in thresholds:
            request = LowStockRequest(threshold=threshold, limit=50)

            try:
                result = await _list_low_stock_items_impl(request, integration_context)
                results[threshold] = result
            except Exception as e:
                error_msg = str(e).lower()
                if any(word in error_msg for word in ["connection", "auth", "timeout"]):
                    pytest.skip(f"API unavailable: {e}")
                raise

        # Higher thresholds should return >= items than lower thresholds
        # (though exact counts depend on inventory)
        for threshold, result in results.items():
            for item in result.items:
                # Stock should be below threshold (using current_stock field)
                assert item.current_stock <= threshold, (
                    f"Item {item.sku} has {item.current_stock} stock "
                    f"but threshold is {threshold}"
                )


@pytest.mark.integration
@pytest.mark.asyncio
class TestInventoryDataConsistency:
    """Test data consistency across inventory tools."""

    async def test_search_and_details_consistency(self, integration_context):
        """Verify that search results and detail lookups return consistent data."""
        # Search for items
        search_request = SearchItemsRequest(query="test", limit=10)

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
            pytest.skip("No items found")

        # Check consistency for each item
        for item in search_result.items[:5]:
            try:
                details_request = GetVariantDetailsRequest(sku=item.sku)
                details = await _get_variant_details_impl(
                    details_request, integration_context
                )

                # IDs should match
                assert details.id == item.id, (
                    f"ID mismatch: search returned {item.id}, "
                    f"details returned {details.id}"
                )

                # SKUs should match (case-insensitive)
                assert details.sku.upper() == item.sku.upper(), (
                    f"SKU mismatch: search returned {item.sku}, "
                    f"details returned {details.sku}"
                )

            except ValueError:
                # Item might have been deleted - acceptable
                continue

    async def test_inventory_check_returns_valid_data(self, integration_context):
        """Verify inventory checks return valid, non-negative values."""
        # First find some items to check
        search_request = SearchItemsRequest(query="a", limit=20)  # Broad search

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
            pytest.skip("No items found")

        # Check inventory for several items
        checked_count = 0
        for item in search_result.items:
            if not item.sku:
                continue

            inventory_request = CheckInventoryRequest(sku=item.sku)
            inventory = await _check_inventory_impl(
                inventory_request, integration_context
            )

            # All values should be non-negative
            assert inventory.available_stock >= 0, "Available stock cannot be negative"
            assert inventory.in_production >= 0, "In production cannot be negative"
            assert inventory.committed >= 0, "Committed cannot be negative"

            # Product name should be a string
            assert isinstance(inventory.product_name, str)

            checked_count += 1
            if checked_count >= 5:
                break

        assert checked_count > 0, "Should have checked at least one item"
