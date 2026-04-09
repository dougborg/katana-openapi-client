"""Tests for Prefab UI builder functions.

Verifies that all UI builders can be called without errors and produce
valid PrefabApp instances. This catches constructor signature mismatches
(e.g., positional vs keyword args) that would only surface at runtime.
"""

from __future__ import annotations

import pytest
from katana_mcp.tools.prefab_ui import (
    build_fulfill_preview_ui,
    build_fulfill_success_ui,
    build_inventory_check_ui,
    build_item_detail_ui,
    build_item_mutation_ui,
    build_low_stock_ui,
    build_order_created_ui,
    build_order_preview_ui,
    build_receipt_ui,
    build_search_results_ui,
    build_variant_details_ui,
    build_verification_ui,
)
from prefab_ui.app import PrefabApp


def _assert_valid_prefab(app: PrefabApp) -> None:
    """Assert that a PrefabApp serializes to valid JSON."""
    result = app.to_json()
    assert isinstance(result, dict)
    assert "$prefab" in result


class TestBuildSearchResultsUI:
    def test_with_items(self):
        items = [
            {
                "id": 1,
                "sku": "SKU-001",
                "name": "Widget",
                "item_type": "product",
                "is_sellable": True,
            },
            {
                "id": 2,
                "sku": "SKU-002",
                "name": "Bolt",
                "item_type": "material",
                "is_sellable": False,
            },
        ]
        app = build_search_results_ui(items, "widget", 2)
        _assert_valid_prefab(app)

    def test_empty_results(self):
        app = build_search_results_ui([], "nothing", 0)
        _assert_valid_prefab(app)


class TestBuildVariantDetailsUI:
    def test_full_variant(self):
        variant = {
            "id": 100,
            "sku": "SKU-001",
            "name": "Widget Pro",
            "type": "product",
            "sales_price": 29.99,
            "purchase_price": 15.00,
            "product_id": 10,
            "material_id": None,
            "lead_time": 7,
            "supplier_item_codes": ["SUP-001", "SUP-002"],
        }
        app = build_variant_details_ui(variant)
        _assert_valid_prefab(app)

    def test_minimal_variant(self):
        variant = {"id": 1, "sku": "X"}
        app = build_variant_details_ui(variant)
        _assert_valid_prefab(app)


class TestBuildItemDetailUI:
    def test_product(self):
        item = {
            "id": 1,
            "name": "Widget",
            "type": "product",
            "uom": "pcs",
            "category_name": "Finished Goods",
            "is_sellable": True,
            "is_producible": True,
        }
        app = build_item_detail_ui(item)
        _assert_valid_prefab(app)

    def test_minimal_item(self):
        app = build_item_detail_ui({"id": 1, "name": "X"})
        _assert_valid_prefab(app)


class TestBuildInventoryCheckUI:
    def test_with_stock(self):
        stock = {
            "sku": "SKU-001",
            "product_name": "Widget",
            "in_stock": 125,
            "available_stock": 100,
            "committed": 25,
            "expected": 50,
        }
        app = build_inventory_check_ui(stock)
        _assert_valid_prefab(app)

    def test_zero_stock(self):
        stock = {
            "sku": "SKU-002",
            "product_name": "",
            "in_stock": 0,
            "available_stock": 0,
            "committed": 0,
            "expected": 0,
        }
        app = build_inventory_check_ui(stock)
        _assert_valid_prefab(app)


class TestBuildLowStockUI:
    def test_with_items(self):
        items = [
            {
                "sku": "SKU-001",
                "product_name": "Widget",
                "current_stock": 3,
                "threshold": 10,
            },
        ]
        app = build_low_stock_ui(items, 10, 1)
        _assert_valid_prefab(app)

    def test_empty(self):
        app = build_low_stock_ui([], 10, 0)
        _assert_valid_prefab(app)


class TestBuildOrderPreviewUI:
    def test_purchase_order(self):
        order = {
            "order_number": "PO-001",
            "status": "PENDING",
            "supplier_id": 1,
            "location_id": 2,
            "total": 1500.0,
            "currency": "USD",
        }
        app = build_order_preview_ui(order, "Purchase")
        _assert_valid_prefab(app)

    def test_sales_order(self):
        order = {
            "order_number": "SO-001",
            "status": "PENDING",
            "customer_id": 1,
            "total": 500.0,
            "currency": "EUR",
        }
        app = build_order_preview_ui(order, "Sales")
        _assert_valid_prefab(app)


class TestBuildOrderCreatedUI:
    def test_created(self):
        order = {
            "order_number": "PO-001",
            "order_id": 123,
            "status": "OPEN",
            "total": 1500.0,
            "currency": "USD",
        }
        app = build_order_created_ui(order, "Purchase")
        _assert_valid_prefab(app)


class TestBuildFulfillPreviewUI:
    def test_preview(self):
        response = {
            "order_type": "sales",
            "order_number": "SO-001",
            "order_id": 123,
            "status": "IN_PROGRESS",
            "message": "Ready to fulfill",
        }
        app = build_fulfill_preview_ui(response)
        _assert_valid_prefab(app)


class TestBuildFulfillSuccessUI:
    def test_success(self):
        response = {
            "order_type": "sales",
            "order_number": "SO-001",
            "status": "DONE",
            "message": "Order fulfilled",
            "inventory_updates": "Stock reduced by 10",
        }
        app = build_fulfill_success_ui(response)
        _assert_valid_prefab(app)


class TestBuildVerificationUI:
    def test_match(self):
        response = {
            "overall_status": "match",
            "order_id": 123,
            "matches": [
                {"sku": "SKU-001", "quantity": 10, "unit_price": 5.0, "status": "match"}
            ],
            "discrepancies": [],
        }
        app = build_verification_ui(response)
        _assert_valid_prefab(app)

    def test_no_match(self):
        response = {
            "overall_status": "no_match",
            "order_id": 456,
            "matches": [],
            "discrepancies": [
                {"sku": "SKU-002", "type": "missing", "message": "Not on PO"}
            ],
        }
        app = build_verification_ui(response)
        _assert_valid_prefab(app)


class TestBuildItemMutationUI:
    @pytest.mark.parametrize("action", ["Created", "Updated", "Deleted"])
    def test_actions(self, action):
        item = {"id": 1, "name": "Widget", "type": "product", "sku": "SKU-001"}
        app = build_item_mutation_ui(item, action)
        _assert_valid_prefab(app)

    def test_minimal(self):
        app = build_item_mutation_ui({"id": 1}, "Created")
        _assert_valid_prefab(app)


class TestBuildReceiptUI:
    def test_preview(self):
        response = {
            "order_number": "PO-001",
            "order_id": 123,
            "is_preview": True,
            "message": "Preview of receipt",
            "items_received": 5,
        }
        app = build_receipt_ui(response)
        _assert_valid_prefab(app)

    def test_confirmed(self):
        response = {
            "order_number": "PO-001",
            "order_id": 123,
            "is_preview": False,
            "items_received": 5,
        }
        app = build_receipt_ui(response)
        _assert_valid_prefab(app)
