"""Minimal FastMCP server exercising the Prefab card builders for browser tests.

Exposes a single tool, ``render_scenario``, that takes a scenario name and
returns a canned ``PrefabApp`` built by the real card builders. Browser tests
navigate the fastmcp ``apps_dev`` ``/launch`` URL with ``tool=render_scenario``
+ ``args={"name": "<scenario>"}`` and assert the rendered DOM.

Plus a stub ``modify_manufacturing_order`` that returns a canned apply
``ModificationResponse`` — used by the Confirm-button click-through tests
to exercise the live-tick path without hitting the real Katana API.
"""

from __future__ import annotations

import json
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

from fastmcp import FastMCP
from fastmcp.tools import ToolResult
from katana_mcp.tools._modification import (
    ActionResult,
    FieldChange,
    ModificationResponse,
)
from katana_mcp.tools.prefab_ui import (
    build_batch_recipe_update_ui,
    build_bom_modify_ui,
    build_customer_create_ui,
    build_inventory_at_ui,
    build_inventory_check_ui,
    build_item_detail_ui,
    build_item_modify_ui,
    build_mo_modify_ui,
    build_po_modify_ui,
    build_product_bom_ui,
    build_search_results_ui,
    build_so_create_ui,
    build_so_detail_ui,
    build_so_modify_ui,
    build_stock_adjustment_create_ui,
    build_stock_adjustment_delete_ui,
    build_stock_adjustment_update_ui,
    build_stock_transfer_modify_ui,
    build_variant_batch_ui,
    build_verification_ui,
)
from katana_mcp.tools.tool_result_utils import make_tool_result
from prefab_ui.app import PrefabApp
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Scenarios — each builds a PrefabApp via the real card builders.
# ---------------------------------------------------------------------------


class _StubRequest(BaseModel):
    """Matches what a modify_manufacturing_order request looks like for the
    Confirm-button payload (the iframe re-issues with these args).
    """

    id: int = 16467730
    preview: bool = True


def _trivial_text_app() -> PrefabApp:
    """Minimal hello-world card to isolate render-pipeline issues."""
    from prefab_ui.components import Card, CardContent, CardTitle, Text

    with PrefabApp(state={}, css_class="p-4") as app, Card():
        CardTitle(content="Trivial Test")
        with CardContent():
            Text(content="If you can read this the iframe is rendering.")
    return app


def _datatable_inline_app() -> PrefabApp:
    """DataTable with inline rows (no state binding) — isolation test."""
    from prefab_ui.components import (
        Card,
        CardContent,
        CardTitle,
        DataTable,
        DataTableColumn,
    )

    with PrefabApp(state={}, css_class="p-4") as app, Card():
        CardTitle(content="DataTable Inline Test")
        with CardContent():
            DataTable(
                columns=[
                    DataTableColumn(key="a", header="A"),
                    DataTableColumn(key="b", header="B"),
                ],
                rows=[
                    {"a": "1", "b": "one"},
                    {"a": "2", "b": "two"},
                ],
            )
    return app


def _datatable_state_app() -> PrefabApp:
    """DataTable with state-bound rows (bare string) — known broken."""
    from prefab_ui.components import (
        Card,
        CardContent,
        CardTitle,
        DataTable,
        DataTableColumn,
    )

    with (
        PrefabApp(
            state={"my_rows": [{"a": "1", "b": "one"}, {"a": "2", "b": "two"}]},
            css_class="p-4",
        ) as app,
        Card(),
    ):
        CardTitle(content="DataTable State Bare Test")
        with CardContent():
            DataTable(
                columns=[
                    DataTableColumn(key="a", header="A"),
                    DataTableColumn(key="b", header="B"),
                ],
                rows="my_rows",
            )
    return app


def _datatable_state_template_app() -> PrefabApp:
    """DataTable with state-bound rows using {{ template }} mustache form."""
    from prefab_ui.components import (
        Card,
        CardContent,
        CardTitle,
        DataTable,
        DataTableColumn,
    )

    with (
        PrefabApp(
            state={"my_rows": [{"a": "1", "b": "one"}, {"a": "2", "b": "two"}]},
            css_class="p-4",
        ) as app,
        Card(),
    ):
        CardTitle(content="DataTable State Template Test")
        with CardContent():
            DataTable(
                columns=[
                    DataTableColumn(key="a", header="A"),
                    DataTableColumn(key="b", header="B"),
                ],
                rows="{{ my_rows }}",
            )
    return app


# ---------------------------------------------------------------------------
# Audit scenarios: cover the other state-bound DataTable cards that share
# the bare-string-vs-mustache risk class. Verifies the mustache fix
# actually renders, not just passes the assertion.
# ---------------------------------------------------------------------------


def _search_results_app() -> PrefabApp:
    """build_search_results_ui with 50 items — exercises rows='{{ items }}'."""
    items = [
        {
            "id": 10000 + i,
            "sku": f"SKU-{i:04d}",
            "name": f"Test Item {i}",
            "item_type": "product" if i % 2 == 0 else "material",
            "is_archived": False,
            "is_sellable": True,
        }
        for i in range(50)
    ]
    return build_search_results_ui(items, query="Test", total_count=50)


def _inventory_check_app() -> PrefabApp:
    """build_inventory_check_ui with multi-location stock — exercises
    rows='{{ stock.by_location }}' (path expression)."""
    stock = {
        "sku": "SKU-WIDGET",
        "product_name": "Widget",
        "in_stock": 42,
        "available_stock": 35,
        "committed": 7,
        "expected": 100,
        "by_location": [
            {
                "location_name": "Main Warehouse",
                "location_id": 1,
                "in_stock": 30,
                "committed": 5,
                "available": 25,
                "expected": 60,
            },
            {
                "location_name": "East Warehouse",
                "location_id": 2,
                "in_stock": 12,
                "committed": 2,
                "available": 10,
                "expected": 40,
            },
        ],
    }
    return build_inventory_check_ui(stock)


def _inventory_at_single_app() -> PrefabApp:
    """build_inventory_at_ui with one variant across two locations —
    exercises the single-item layout (SKU/Item columns hidden, variant
    info in the header)."""
    items = [
        {
            "variant_id": 3001,
            "sku": "SKU-WIDGET",
            "display_name": "Widget",
            "by_location": [
                {
                    "location_id": 1,
                    "location_name": "Main Warehouse",
                    "balance_at": 100.0,
                    "value_in_stock_at": 5000.0,
                    "average_cost_at": 50.0,
                    "last_movement_date": "2026-03-15T12:00:00+00:00",
                    "last_movement_id": 9001,
                },
                {
                    "location_id": 2,
                    "location_name": "East Warehouse",
                    "balance_at": 40.0,
                    "value_in_stock_at": 2000.0,
                    "average_cost_at": 50.0,
                    "last_movement_date": "2026-03-10T08:30:00+00:00",
                    "last_movement_id": 9002,
                },
            ],
            "total_balance": 140.0,
            "total_value": 7000.0,
        },
    ]
    return build_inventory_at_ui(
        items=items, as_of="2026-04-01T00:00:00Z", location_id=None
    )


def _inventory_at_batch_app() -> PrefabApp:
    """build_inventory_at_ui with multiple variants — exercises batch
    layout (SKU/Item columns visible) plus a not_found entry and a
    variant with no movement history (empty by_location → placeholder row).
    """
    items = [
        {
            "variant_id": 3001,
            "sku": "SKU-A",
            "display_name": "Widget A",
            "by_location": [
                {
                    "location_id": 1,
                    "location_name": "Main",
                    "balance_at": 50.0,
                    "value_in_stock_at": 2500.0,
                    "average_cost_at": 50.0,
                    "last_movement_date": "2026-03-01T00:00:00+00:00",
                    "last_movement_id": 1,
                },
            ],
            "total_balance": 50.0,
            "total_value": 2500.0,
        },
        {
            "variant_id": 3002,
            "sku": "SKU-B",
            "display_name": "Widget B",
            "by_location": [
                {
                    "location_id": 1,
                    "location_name": "Main",
                    "balance_at": 25.0,
                    "value_in_stock_at": 1250.0,
                    "average_cost_at": 50.0,
                    "last_movement_date": "2026-02-15T00:00:00+00:00",
                    "last_movement_id": 2,
                },
                {
                    "location_id": 2,
                    "location_name": "Annex",
                    "balance_at": 10.0,
                    "value_in_stock_at": 500.0,
                    "average_cost_at": 50.0,
                    "last_movement_date": "2026-02-20T00:00:00+00:00",
                    "last_movement_id": 3,
                },
            ],
            "total_balance": 35.0,
            "total_value": 1750.0,
        },
        {
            # Empty by_location — placeholder row in the table.
            "variant_id": 3003,
            "sku": "SKU-C",
            "display_name": "Widget C",
            "by_location": [],
            "total_balance": 0.0,
            "total_value": 0.0,
        },
    ]
    return build_inventory_at_ui(
        items=items,
        as_of="2026-04-01T00:00:00Z",
        location_id=None,
        not_found=["GHOST-SKU"],
    )


def _verification_app() -> PrefabApp:
    """build_verification_ui with matches + discrepancies — exercises both
    rows='{{ matches }}' and rows='{{ discrepancies }}'."""
    response = {
        "order_id": 123,
        "overall_status": "partial_match",
        "matches": [
            {
                "sku": "SKU-A",
                "quantity": 5,
                "unit_price": 10.50,
                "status": "matched",
            },
            {
                "sku": "SKU-B",
                "quantity": 3,
                "unit_price": 7.25,
                "status": "matched",
            },
        ],
        "discrepancies": [
            {
                "sku": "SKU-C",
                "type": "qty_mismatch",
                "message": "Expected 5, received 3",
            },
        ],
    }
    return build_verification_ui(response)


def _item_detail_app() -> PrefabApp:
    """build_item_detail_ui with 3 variants — exercises the variants
    DataTable's per-row ``onRowClick=CallTool(get_variant_details,
    arguments={"variant_id": "{{ id }}"})`` binding (#494).
    """
    item = {
        "id": 9001,
        "name": "Test Product",
        "type": "product",
        "uom": "pcs",
        "is_sellable": True,
        "is_producible": True,
        "variants": [
            {
                "id": 700001,
                "sku": "VAR-A",
                "sales_price": 10.00,
                "purchase_price": 4.00,
            },
            {
                "id": 700002,
                "sku": "VAR-B",
                "sales_price": 20.00,
                "purchase_price": 8.00,
            },
            {
                "id": 700003,
                "sku": "VAR-C",
                "sales_price": 30.00,
                "purchase_price": 12.00,
            },
        ],
    }
    return build_item_detail_ui(item)


def _product_bom_app() -> PrefabApp:
    """build_product_bom_ui with 3 ingredient rows — exercises the BOM
    rows DataTable's per-row drill into ``get_variant_details``.
    Pre-#810 ``get_product_bom`` returned ``make_json_result`` and the
    card rendered as "Waiting for content..." — this scenario pins the
    end-to-end render against a realistic response shape.
    """
    bom = {
        "product_variant_id": 700001,
        "product_id": 9001,
        "product_name": "Test Frame",
        "variant_sku": "FRAME-A",
        "variant_display_name": "Test Frame / Standard",
        "is_producible": True,
        "uom": "pcs",
        "katana_url": "https://factory.katanamrp.com/product/9001",
        "total_count": 3,
        "rows": [
            {
                "id": "11111111-1111-1111-1111-111111111111",
                "product_item_id": 9001,
                "product_variant_id": 700001,
                "ingredient_variant_id": 300,
                "sku": "FS90250",
                "display_name": "M5 chainring bolt",
                "quantity": 6.0,
                "notes": None,
                "rank": 1,
            },
            {
                "id": "22222222-2222-2222-2222-222222222222",
                "product_item_id": 9001,
                "product_variant_id": 700001,
                "ingredient_variant_id": 301,
                "sku": "FS90251",
                "display_name": "M6 hex screw",
                "quantity": 4.0,
                "notes": "Loctite blue",
                "rank": 2,
            },
            {
                "id": "33333333-3333-3333-3333-333333333333",
                "product_item_id": 9001,
                "product_variant_id": 700001,
                "ingredient_variant_id": 302,
                "sku": "OR12-NBR",
                "display_name": "O-ring NBR 12mm",
                "quantity": 2.0,
                "notes": None,
                "rank": 3,
            },
        ],
    }
    return build_product_bom_ui(bom)


def _product_bom_empty_app() -> PrefabApp:
    """build_product_bom_ui with no rows — exercises the empty-state
    Muted hint path (no DataTable rendered).
    """
    bom = {
        "product_variant_id": 700001,
        "product_id": 9001,
        "product_name": "Test Frame",
        "variant_sku": "FRAME-A",
        "variant_display_name": "Test Frame / Standard",
        "is_producible": True,
        "uom": "pcs",
        "katana_url": "https://factory.katanamrp.com/product/9001",
        "total_count": 0,
        "rows": [],
    }
    return build_product_bom_ui(bom)


def _variant_batch_app() -> PrefabApp:
    """build_variant_batch_ui with 3 found + 2 not-found inputs —
    exercises the batch summary DataTable and the not-found Alert.
    Pre-#810 sibling fix the batch path returned a bare dict
    ``structured_content`` and stalled on "Waiting for content...".
    """
    # Real ``VariantDetailsResponse.model_dump()`` uses ``id`` (not
    # ``variant_id``) for the primary key — mirror that here so the
    # fixture exercises the same shape ``get_variant_details``
    # actually emits, not a fictional one.
    payload = {
        "variants": [
            {
                "id": 700001,
                "sku": "VAR-A",
                "display_name": "Frame / Standard",
                "uom": "pcs",
                "sales_price": "100.00",
                "purchase_price": "40.00",
            },
            {
                "id": 700002,
                "sku": "VAR-B",
                "display_name": "Frame / Large",
                "uom": "pcs",
                "sales_price": "120.00",
                "purchase_price": "48.00",
            },
            {
                "id": 700003,
                "sku": "VAR-C",
                "display_name": "Frame / XL",
                "uom": "pcs",
                "sales_price": "140.00",
                "purchase_price": "56.00",
            },
        ],
        "not_found": [
            {"sku": "DOES-NOT-EXIST-1"},
            {"variant_id": 999999999},
        ],
    }
    return build_variant_batch_ui(payload)


def _so_detail_app() -> PrefabApp:
    """build_so_detail_ui — read-only sales-order detail card (#913).

    Exercises the static line-item DataTable (rows='{{ so.rows }}'), the
    resolved customer/location party lines, billing+shipping address blocks,
    storefront link, and the single View-in-Katana footer button.
    """
    so = {
        "id": 4242,
        "katana_url": "https://factory.katanamrp.com/salesorder/4242",
        "order_no": "SO-4242",
        "status": "PACKED",
        "customer_id": 10,
        "customer_name": "Bicycle Parts Co",
        "location_id": 3,
        "location_name": "Main Warehouse",
        "total": 1500.0,
        "currency": "USD",
        "delivery_date": "2026-07-01",
        "customer_ref": "PO-99",
        "order_created_date": "2026-06-01",
        "additional_info": "Rush order — ship by Friday",
        "tracking_number": "TRK-12345",
        "tracking_number_url": "https://track.example/TRK-12345",
        "ecommerce_order_type": "shopify",
        "ecommerce_store_name": "bikeparts.myshopify.com",
        "ecommerce_order_id": "555",
        "ecommerce_url": ("https://bikeparts.myshopify.com/admin/orders/555"),
        "addresses": [
            {
                "entity_type": "billing",
                "first_name": "Jane",
                "last_name": "Doe",
                "line_1": "1 Main St",
                "city": "Townsville",
                "country": "US",
            },
            {
                "entity_type": "shipping",
                "company": "Bicycle Parts Co",
                "line_1": "2 Dock Rd",
                "city": "Portcity",
                "state": "CA",
                "zip": "90210",
                "country": "US",
            },
        ],
        "rows": [
            {
                "variant_id": 700001,
                "sku": "FRAME-STD",
                "display_name": "Frame / Standard",
                "quantity": 2,
                "price_per_unit": 500.0,
                "total": 1000.0,
            },
            {
                "variant_id": 700002,
                "sku": "WHEEL-26",
                "display_name": "Wheel / 26in",
                "quantity": 5,
                "price_per_unit": 100.0,
                "total": 500.0,
            },
        ],
        "warnings": [],
    }
    return build_so_detail_ui(so)


def _batch_recipe_update_app() -> PrefabApp:
    """build_batch_recipe_update_ui with mixed sub-ops — exercises the
    per-row diff overlay (Qty / Batch / Serials columns) across all three
    op_types (add / delete / update) including batch-tracked + serial-
    tracked materials. See #557 for the design contract.
    """
    response = {
        "is_preview": True,
        "total_ops": 5,
        "success_count": 0,
        "failed_count": 0,
        "skipped_count": 0,
        "message": "5 sub-ops planned",
        "warnings": [],
        "results": [
            # Simple add — no batch / serial tracking.
            {
                "op_type": "add",
                "group_label": "Replace bolt with nut",
                "manufacturing_order_id": 9999,
                "variant_id": 200,
                "sku": "SKU-NEW-NUT",
                "display_name": "M6 nut / 1.0mm pitch / Stainless",
                "planned_quantity_per_unit": 2.0,
                "status": "pending",
            },
            # Delete with captured prior qty — exercises the "- N" shape.
            {
                "op_type": "delete",
                "group_label": "Replace bolt with nut",
                "manufacturing_order_id": 9999,
                "recipe_row_id": 5001,
                "variant_id": 100,
                "sku": "SKU-OLD-BOLT",
                "display_name": "M6 bolt / 25mm / Stainless",
                "before_planned_quantity_per_unit": 2.0,
                "status": "pending",
            },
            # Update with full diff — exercises the "before -> after" shape.
            {
                "op_type": "update",
                "group_label": "Resize gasket",
                "manufacturing_order_id": 9999,
                "recipe_row_id": 5002,
                "variant_id": 101,
                "sku": "SKU-GASKET",
                "display_name": "Rubber gasket / 30mm",
                "before_planned_quantity_per_unit": 1.0,
                "planned_quantity_per_unit": 4.0,
                "status": "pending",
            },
            # Batch-tracked add — exercises the Batch column.
            {
                "op_type": "add",
                "group_label": "Add batch-tracked ingredient",
                "manufacturing_order_id": 9999,
                "variant_id": 202,
                "sku": "SKU-BATCH-MAT",
                "display_name": "Premixed solvent / 1L",
                "planned_quantity_per_unit": 50.0,
                "batch_transactions": [
                    {"batch_id": 42, "quantity": 30.0},
                    {"batch_id": 51, "quantity": 20.0},
                ],
                "status": "pending",
            },
            # Serial-tracked add — exercises the Serials column.
            {
                "op_type": "add",
                "group_label": "Add serial-tracked ingredient",
                "manufacturing_order_id": 9999,
                "variant_id": 203,
                "sku": "SKU-SERIAL-MAT",
                "display_name": "Motor controller / rev B",
                "planned_quantity_per_unit": 2.0,
                "serial_numbers": ["SN-001", "SN-002"],
                "status": "pending",
            },
        ],
    }
    return build_batch_recipe_update_ui(response)


# ---------------------------------------------------------------------------
# Stock-adjustment scenarios — preview/result for create / update / delete.
# Adds direct-apply rail coverage for #639's stock_adjustment family.
# ---------------------------------------------------------------------------


def _customer_create_response(*, is_preview: bool, with_addresses: bool) -> dict:
    """Build a canned CreateCustomerResponse dict for the customer card.

    ``with_addresses`` toggles billing+shipping snapshots to exercise the
    address-block rendering and the "same as billing" de-dup path.
    """
    base: dict = {
        "id": None if is_preview else 8001,
        "katana_url": (
            None
            if is_preview
            else "https://factory.katanamrp.com/contacts/customers/8001"
        ),
        "name": "Gourmet Bistro Group",
        "first_name": "Elena",
        "last_name": "Rodriguez",
        "company": "Gourmet Bistro Group Inc",
        "email": "procurement@gourmetbistro.com",
        "phone": "+1-555-0125",
        "comment": "Premium restaurant chain — priority orders",
        "currency": "USD",
        "reference_id": "GBG-2024-003",
        "category": "Fine Dining",
        "discount_rate": 7.5,
        "addresses": [],
        "is_preview": is_preview,
        "warnings": [],
        "next_actions": [],
        "message": (
            "Preview: customer ready to create"
            if is_preview
            else "Successfully created customer (ID: 8001)"
        ),
    }
    if with_addresses:
        billing = {
            "entity_type": "billing",
            "first_name": "Elena",
            "last_name": "Rodriguez",
            "company": "Gourmet Bistro Group Inc",
            "phone": "+1-555-0125",
            "line_1": "123 Market St",
            "line_2": "Suite 4",
            "city": "Springfield",
            "state": "IL",
            "zip": "62701",
            "country": "US",
        }
        # Shipping byte-equal to billing exercises the "same as billing"
        # de-dup branch in ``_render_customer_entity_view``.
        shipping = dict(billing)
        shipping["entity_type"] = "shipping"
        base["addresses"] = [billing, shipping]
    return base


def _so_create_response_with_shipping_fees(
    *, is_preview: bool, fee_outcomes: list[dict] | None = None
) -> dict:
    """Build a canned SalesOrderResponse dict for the SO-with-fees card.

    Used by the #818 browser scenarios to pin the inline-shipping-fees
    rendering on the create_sales_order card across the preview /
    all-success-apply / partial-failure states.
    """
    base: dict = {
        "id": None if is_preview else 9001,
        "order_number": "SO-FEES-001",
        "customer_id": 1501,
        "customer_name": "Buyer Co",
        "location_id": 1,
        # ``status`` mirrors the real tool's two paths: preview emits
        # ``PENDING`` (hardcoded — no SO exists yet), apply reads
        # ``so.status.value`` from the just-created SO (which Katana
        # stamps ``NOT_SHIPPED`` for a freshly-created order). The
        # ternary reads in the same order as the impl for parity.
        "status": "PENDING" if is_preview else "NOT_SHIPPED",
        "total": 100.0,
        "currency": "USD",
        "delivery_date": "2026-06-01",
        "item_count": 2,
        "is_preview": is_preview,
        "shipping_fee_outcomes": fee_outcomes or [],
        "warnings": [],
        "next_actions": [],
        "message": (
            "Preview: Sales order SO-FEES-001 with 2 items totaling 100.00"
            if is_preview
            else "Successfully created sales order SO-FEES-001 (ID: 9001)"
        ),
        "katana_url": (
            None if is_preview else "https://factory.katanamrp.com/salesorder/9001"
        ),
    }
    return base


def _stock_adjustment_response(*, is_preview: bool, n_rows: int = 3) -> dict:
    """Build a canned StockAdjustmentResponse dict with N rows."""
    rows = [
        {
            "sku": f"SKU-{1000 + i}",
            "display_name": f"Test Item {i}",
            "quantity": float(i + 1) if i % 2 == 0 else -float(i + 1),
            "cost_per_unit": 10.50 if i == 0 else None,
        }
        for i in range(n_rows)
    ]
    return {
        "id": None if is_preview else 9876,
        "is_preview": is_preview,
        "location_id": 1,
        "message": (
            "Preview — call again with preview=false to create"
            if is_preview
            else "Stock adjustment created successfully"
        ),
        "rows": rows,
        "rows_summary": "\n".join(
            f"- {r['sku']} ({r['display_name']}): {r['quantity']:+.1f}" for r in rows
        ),
        "reason": "Found one in stock",
        "katana_url": (
            None if is_preview else "https://factory.katanamrp.com/stockadjustment/9876"
        ),
    }


def _stock_adjustment_update_response(*, is_preview: bool) -> dict:
    """Build a canned UpdateStockAdjustmentResponse dict with field changes."""
    return {
        "id": 9876,
        "is_preview": is_preview,
        "stock_adjustment_number": "SA-FY26-Q2-001",
        "stock_adjustment_date": "2026-05-08T12:00:00+00:00",
        "location_id": 1,
        "reason": "Updated reason",
        "additional_info": None,
        "changes_summary": "stock_adjustment_number, reason",
        "message": (
            "Preview — call again with preview=false to update stock adjustment 9876"
            if is_preview
            else "Stock adjustment 9876 updated successfully"
        ),
        "katana_url": "https://factory.katanamrp.com/stockadjustment/9876",
    }


def _stock_adjustment_delete_response(*, is_preview: bool) -> dict:
    """Build a canned DeleteStockAdjustmentResponse dict."""
    return {
        "id": 9876,
        "is_preview": is_preview,
        "stock_adjustment_number": "SA-FY26-Q2-001",
        "location_id": 1,
        "row_count": 3,
        "message": (
            "Preview — call again with preview=false to delete stock adjustment "
            "SA-FY26-Q2-001 (3 rows)"
            if is_preview
            else "Stock adjustment SA-FY26-Q2-001 (id=9876) deleted; "
            "associated inventory movements reversed"
        ),
    }


def _bom_modify_response(*, is_preview: bool, succeeded: bool | None) -> dict:
    """Build a canned BOM modify response with adds + updates + deletes.

    Mirrors the production shape for the #811 BOM modify card: 5+ mixed
    actions (1 add + 1 update + 2 delete + 3 existing-untouched), the
    pre-action snapshot threaded as ``prior_state``, and
    ``resolved_ingredients`` in ``extras`` so ``build_bom_modify_ui``
    can render the added row's SKU + display name.
    """
    existing_rows = [
        {
            "id": "11111111-1111-1111-1111-111111111111",
            "product_item_id": 100,
            "product_variant_id": 200,
            "ingredient_variant_id": 401,
            "sku": "BLT-M5-10",
            "display_name": "M5 chainring bolt",
            "quantity": 6.0,
            "notes": None,
            "rank": 10000,
        },
        {
            "id": "22222222-2222-2222-2222-222222222222",
            "product_item_id": 100,
            "product_variant_id": 200,
            "ingredient_variant_id": 402,
            "sku": "BLT-M6-12",
            "display_name": "M6 hex screw",
            "quantity": 4.0,
            "notes": "optional",
            "rank": 20000,
        },
        {
            "id": "33333333-3333-3333-3333-333333333333",
            "product_item_id": 100,
            "product_variant_id": 200,
            "ingredient_variant_id": 403,
            "sku": "FRM-AL-140",
            "display_name": "Aluminum 140 frame raw",
            "quantity": 1.0,
            "notes": None,
            "rank": 30000,
        },
        {
            "id": "44444444-4444-4444-4444-444444444444",
            "product_item_id": 100,
            "product_variant_id": 200,
            "ingredient_variant_id": 404,
            "sku": "PNT-MTB",
            "display_name": "Matte black paint",
            "quantity": 2.0,
            "notes": None,
            "rank": 40000,
        },
        {
            "id": "55555555-5555-5555-5555-555555555555",
            "product_item_id": 100,
            "product_variant_id": 200,
            "ingredient_variant_id": 405,
            "sku": "DCL-MAYHEM",
            "display_name": "Mayhem decal sheet",
            "quantity": 1.0,
            "notes": None,
            "rank": 50000,
        },
    ]
    actions = [
        # Add: new chain pin ingredient.
        ActionResult(
            index=1,
            operation="add_bom_row",
            target_id=None,
            changes=[
                FieldChange(
                    field="ingredient_variant_id",
                    old=None,
                    new=301,
                    is_added=True,
                ),
                FieldChange(field="quantity", old=None, new=2.0, is_added=True),
            ],
            succeeded=succeeded,
        ).model_dump(),
        # Update: bump chainring bolt quantity from 6 → 8.
        ActionResult(
            index=2,
            operation="update_bom_row",
            target_id="11111111-1111-1111-1111-111111111111",
            changes=[
                FieldChange(
                    field="quantity",
                    old=None,
                    new=8.0,
                    is_unknown_prior=True,
                ),
            ],
            succeeded=succeeded,
            verified=True if succeeded else None,
        ).model_dump(),
        # Delete: drop the paint row.
        ActionResult(
            index=3,
            operation="delete_bom_row",
            target_id="44444444-4444-4444-4444-444444444444",
            changes=[],
            succeeded=succeeded,
        ).model_dump(),
        # Delete: drop the decal row.
        ActionResult(
            index=4,
            operation="delete_bom_row",
            target_id="55555555-5555-5555-5555-555555555555",
            changes=[],
            succeeded=succeeded,
        ).model_dump(),
    ]
    return {
        "entity_type": "product_bom",
        "entity_id": 200,
        "is_preview": is_preview,
        "operation": "",
        "changes": [],
        "actions": actions,
        "prior_state": {
            "product_variant_id": 200,
            "product_id": 100,
            "product_name": "Mayhem 140 Frame",
            "variant_sku": "MA14025RTLG",
            "variant_display_name": "Mayhem 140 Frame / Large",
            "is_producible": True,
            "uom": "pcs",
            "katana_url": "https://factory.katanamrp.com/product/100",
            "total_count": 5,
            "rows": existing_rows,
        },
        "extras": {
            "resolved_ingredients": {
                301: {"sku": "FS90250", "display_name": "M5 chain pin"},
                401: {"sku": "BLT-M5-10", "display_name": "M5 chainring bolt"},
                402: {"sku": "BLT-M6-12", "display_name": "M6 hex screw"},
                403: {"sku": "FRM-AL-140", "display_name": "Aluminum 140 frame raw"},
                404: {"sku": "PNT-MTB", "display_name": "Matte black paint"},
                405: {"sku": "DCL-MAYHEM", "display_name": "Mayhem decal sheet"},
            },
        },
        "warnings": [],
        "next_actions": [],
        "katana_url": None,
        "message": (
            "Preview: 4 action(s) planned" if is_preview else "Applied 4 action(s)"
        ),
    }


def _item_modify_response(*, is_preview: bool, succeeded: bool | None) -> dict:
    """Build a canned item modify response with a header change + variant CRUD.

    Mirrors the production shape for the #726 item modify card: a header
    ``uom`` change plus 1 variant add + 1 variant update + 1 variant delete
    against a 2-variant product, with the pre-action snapshot threaded as
    ``prior_state`` (raw ``Product.to_dict()`` shape) and the supplier name
    pre-resolved (``_resolve_prior_supplier_name``). Pins the dual diff
    surface — header scalar diff + variant diff table — end to end.
    """
    actions = [
        ActionResult(
            index=1,
            operation="update_header",
            target_id=500,
            changes=[FieldChange(field="uom", old="pcs", new="set")],
            succeeded=succeeded,
            verified=True if succeeded else None,
        ).model_dump(),
        ActionResult(
            index=2,
            operation="add_variant",
            target_id=None,
            changes=[
                FieldChange(field="sku", old=None, new="WHL-CARB-DISC", is_added=True),
                FieldChange(field="sales_price", old=None, new=1300.0, is_added=True),
            ],
            succeeded=succeeded,
        ).model_dump(),
        ActionResult(
            index=3,
            operation="update_variant",
            target_id=9001,
            changes=[FieldChange(field="sales_price", old=1200.0, new=1250.0)],
            succeeded=succeeded,
            verified=True if succeeded else None,
        ).model_dump(),
        ActionResult(
            index=4,
            operation="delete_variant",
            target_id=9002,
            changes=[],
            succeeded=succeeded,
        ).model_dump(),
    ]
    return {
        "entity_type": "product",
        "entity_id": 500,
        "is_preview": is_preview,
        "operation": "",
        "changes": [],
        "actions": actions,
        "prior_state": {
            "id": 500,
            "name": "Carbon Wheelset",
            "uom": "pcs",
            "category_name": "Wheels",
            "additional_info": "Hand-built",
            "is_sellable": True,
            "is_producible": True,
            "batch_tracked": False,
            "serial_tracked": False,
            "archived_at": None,
            "default_supplier_id": 77,
            "default_supplier_name": "Acme Carbon Co",
            "lead_time": 14,
            "minimum_order_quantity": 2,
            "variants": [
                {
                    "id": 9001,
                    "sku": "WHL-CARB-700C",
                    "sales_price": 1200.0,
                    "purchase_price": 800.0,
                },
                {
                    "id": 9002,
                    "sku": "WHL-CARB-650B",
                    "sales_price": 1150.0,
                    "purchase_price": 760.0,
                },
            ],
        },
        "extras": {},
        "warnings": [],
        "next_actions": [],
        "katana_url": "https://factory.katanamrp.com/product/500",
        "message": (
            "Preview: 4 action(s) planned" if is_preview else "Applied 4 action(s)"
        ),
    }


def _po_modify_rows_response(*, is_preview: bool, succeeded: bool | None) -> dict:
    """Build a canned PO modify response with line-item row CRUD.

    Mirrors the production shape for the PO row-table content-drop fix (#722
    follow-up): a header change + (1 add + 1 update + 1 delete) on the line
    items, with the raw ``purchase_order_rows`` snapshot as ``prior_state`` and
    the resolved-variant map in ``extras`` so the row table renders SKU + name.
    """
    actions = [
        ActionResult(
            index=1,
            operation="update_header",
            target_id=9001,
            changes=[FieldChange(field="status", old="NOT_RECEIVED", new="RECEIVED")],
            succeeded=succeeded,
            verified=True if succeeded else None,
        ).model_dump(),
        ActionResult(
            index=2,
            operation="add_row",
            target_id=None,
            changes=[
                FieldChange(field="variant_id", old=None, new=403, is_added=True),
                FieldChange(field="quantity", old=None, new=20.0, is_added=True),
                FieldChange(field="price_per_unit", old=None, new=2.5, is_added=True),
            ],
            succeeded=succeeded,
        ).model_dump(),
        ActionResult(
            index=3,
            operation="update_row",
            target_id=7001,
            changes=[FieldChange(field="quantity", old=10.0, new=15.0)],
            succeeded=succeeded,
            verified=True if succeeded else None,
        ).model_dump(),
        ActionResult(
            index=4,
            operation="delete_row",
            target_id=7002,
            changes=[],
            succeeded=succeeded,
        ).model_dump(),
    ]
    return {
        "entity_type": "purchase_order",
        "entity_id": 9001,
        "is_preview": is_preview,
        "operation": "",
        "changes": [],
        "actions": actions,
        "prior_state": {
            "id": 9001,
            "order_no": "PO-2026-001",
            "supplier_id": 100,
            "supplier": {"id": 100, "name": "Acme Supply Co"},
            "location_id": 1,
            "status": "NOT_RECEIVED",
            "entity_type": "regular",
            "total": 1250.0,
            "currency": "USD",
            "additional_info": "Net-30",
            "purchase_order_rows": [
                {
                    "id": 7001,
                    "variant_id": 401,
                    "quantity": 10.0,
                    "price_per_unit": 25.0,
                },
                {
                    "id": 7002,
                    "variant_id": 402,
                    "quantity": 5.0,
                    "price_per_unit": 40.0,
                },
            ],
        },
        "extras": {
            "resolved_variants": {
                401: {"sku": "BOLT-M5", "display_name": "M5 bolt"},
                402: {"sku": "NUT-M5", "display_name": "M5 nut"},
                403: {"sku": "WASHER-M5", "display_name": "M5 washer"},
            }
        },
        "warnings": [],
        "next_actions": [],
        "katana_url": "https://factory.katanamrp.com/purchaseorder/9001",
        "message": (
            "Preview: 4 action(s) planned" if is_preview else "Applied 4 action(s)"
        ),
    }


def _mo_modify_response(*, is_preview: bool, succeeded: bool | None) -> dict:
    """Build a canned MO modify response exercising all three collection diff
    tables (#721 Phase 4): a header change + recipe add + operation status
    update + production add, with the collections attached to ``prior_state``
    and the added recipe variant resolved in ``extras``.
    """
    actions = [
        ActionResult(
            index=1,
            operation="update_header",
            target_id=500,
            changes=[FieldChange(field="planned_quantity", old=10, new=20)],
            succeeded=succeeded,
            verified=True if succeeded else None,
        ).model_dump(),
        ActionResult(
            index=2,
            operation="add_recipe_row",
            target_id=None,
            changes=[
                FieldChange(field="variant_id", old=None, new=403, is_added=True),
                FieldChange(
                    field="planned_quantity_per_unit", old=None, new=2.0, is_added=True
                ),
            ],
            succeeded=succeeded,
        ).model_dump(),
        ActionResult(
            index=3,
            operation="update_operation_row",
            target_id=21,
            changes=[FieldChange(field="status", old="NOT_STARTED", new="COMPLETED")],
            succeeded=succeeded,
            verified=True if succeeded else None,
        ).model_dump(),
        ActionResult(
            index=4,
            operation="add_production",
            target_id=None,
            changes=[
                FieldChange(
                    field="completed_quantity", old=None, new=3.0, is_added=True
                )
            ],
            succeeded=succeeded,
        ).model_dump(),
    ]
    return {
        "entity_type": "manufacturing_order",
        "entity_id": 500,
        "is_preview": is_preview,
        "order_no": "MO-2026-001",
        "status": "NOT_STARTED",
        "operation": "",
        "changes": [],
        "actions": actions,
        "prior_state": {
            "order_no": "MO-2026-001",
            "status": "NOT_STARTED",
            "variant_id": 9,
            "sku": "WIDGET-A",
            "planned_quantity": 10,
            "location_id": 1,
            "location_name": "Main Factory",
            "recipe_rows": [
                {
                    "id": 11,
                    "variant_id": 402,
                    "sku": "BOLT",
                    "display_name": "M5 bolt",
                    "planned_quantity_per_unit": 4.0,
                },
            ],
            "operation_rows": [
                {"id": 21, "operation_name": "Cut", "status": "NOT_STARTED"},
            ],
            "productions": [
                {"id": 31, "quantity": 5.0, "production_date": "2026-05-01T00:00:00Z"},
            ],
        },
        "extras": {
            "resolved_variants": {403: {"sku": "WASHER", "display_name": "M5 washer"}}
        },
        "warnings": [],
        "next_actions": [],
        "katana_url": "https://factory.katanamrp.com/manufacturingorder/500",
        "message": (
            "Preview: 4 action(s) planned" if is_preview else "Applied 4 action(s)"
        ),
    }


def _stock_transfer_modify_response(
    *, is_preview: bool, succeeded: bool | None
) -> dict:
    """Build a canned stock-transfer modify response (#721 Phase 5).

    Header-only — stock transfers have no GET endpoint, so ``prior_state`` is
    ``None`` and every change is flagged ``is_unknown_prior`` (renders
    ``(prior unknown) → new``). Exercises a header patch (transfer number +
    expected-arrival date) plus a status transition.
    """
    actions = [
        ActionResult(
            index=1,
            operation="update_header",
            target_id=42,
            changes=[
                FieldChange(
                    field="stock_transfer_number",
                    old=None,
                    new="ST-002",
                    is_unknown_prior=True,
                ),
                FieldChange(
                    field="expected_arrival_date",
                    old=None,
                    new="2026-06-10T00:00:00Z",
                    is_unknown_prior=True,
                ),
            ],
            succeeded=succeeded,
            verified=True if succeeded else None,
        ).model_dump(),
        ActionResult(
            index=2,
            operation="update_status",
            target_id=42,
            changes=[
                FieldChange(
                    field="new_status",
                    old=None,
                    new="IN_TRANSIT",
                    is_unknown_prior=True,
                )
            ],
            succeeded=succeeded,
        ).model_dump(),
    ]
    return {
        "entity_type": "stock_transfer",
        "entity_id": 42,
        "is_preview": is_preview,
        "operation": "",
        "changes": [],
        "actions": actions,
        "prior_state": None,
        "warnings": [],
        "next_actions": [],
        "katana_url": "https://factory.katanamrp.com/stocktransfer/42",
        "message": (
            "Preview: 2 action(s) planned for stock transfer 42"
            if is_preview
            else "Applied 2 action(s)"
        ),
    }


def _so_failed_delete_response(*, is_preview: bool = False) -> dict:
    """Build a canned SO delete response where the apply fails.

    Mirrors the failure shape Katana returns when the SO is already
    gone (404) or in a state that blocks the cascade. Pre-fix #858
    finding B the FAILED chrome rendered without the actual error text
    — delete actions carry no field changes (so the header-changes
    block was empty) and the sub-entity failure summary filters out
    top-level ``delete`` (so that block was empty too). Post-fix the
    dedicated header-op Alert surfaces the :attr:`ActionResult.error`.

    ``is_preview`` flips between the pre-Confirm preview shape (delete
    pending) and the post-Confirm apply result (delete FAILED).
    """
    delete_succeeded = None if is_preview else False
    actions = [
        ActionResult(
            index=1,
            operation="delete",
            target_id=42,
            changes=[],
            succeeded=delete_succeeded,
            error=None
            if is_preview
            else "404 Not Found: sales order 42 does not exist",
            status_label="" if is_preview else "FAILED",
        ).model_dump(),
    ]
    return {
        "entity_type": "sales_order",
        "entity_id": 42,
        "is_preview": is_preview,
        "operation": "",
        "changes": [],
        "actions": actions,
        "prior_state": {
            "id": 42,
            "order_no": "SO-2026-001",
            "customer_id": 1501,
            "customer_name": "Sarah Johnson",
            "location_id": 1,
            "status": "NOT_SHIPPED",
            "currency": "USD",
            "total": 1250.0,
        },
        "warnings": [],
        "next_actions": [],
        "katana_url": "https://factory.katanamrp.com/salesorder/42",
        "message": "Preview: 1 action(s) planned" if is_preview else "Delete failed",
    }


def _so_modify_partial_failure_response(*, is_preview: bool = False) -> dict:
    """Build a canned SO modify response with a partial-failure plan.

    Mirrors the production shape for the #723 SO modify card:

    - Header change (status: NOT_SHIPPED → PACKED) — applies cleanly.
    - One shipping_fee add — applies cleanly.
    - One row delete — FAILS (404 — stale row id) on apply.

    ``is_preview`` flips the response between the pre-Confirm preview
    (every action ``succeeded=None``) and the post-Confirm apply result
    (header + shipping_fee succeeded, delete_row failed). The same
    actions are returned in both cases so the morph test can assert
    that the Confirm-time apply call produces the partial-failure
    chrome (Alert + per-action FAILED Badge + card-level
    PARTIAL FAILURE state) on top of the preview tree.

    On the applied path the card-level state badge reads PARTIAL
    FAILURE, the state-driven sub-entity failed-action Alert shows
    the failed row's error + retry coaching, and the Python-painted
    action rows in the Line items + Shipping fees sections carry
    per-action APPLIED / FAILED Badges.
    """
    # On preview every action is pending (``succeeded=None``); on apply
    # the header + shipping_fee succeed and the row delete fails. The
    # failure path is what makes this the "interesting" morph fixture.
    header_succeeded = None if is_preview else True
    fee_succeeded = None if is_preview else True
    row_succeeded = None if is_preview else False
    actions = [
        ActionResult(
            index=1,
            operation="update_header",
            target_id=42,
            changes=[
                FieldChange(field="status", old="NOT_SHIPPED", new="PACKED"),
            ],
            succeeded=header_succeeded,
        ).model_dump(),
        ActionResult(
            index=2,
            operation="add_shipping_fee",
            target_id=None,
            changes=[
                FieldChange(
                    field="description",
                    old=None,
                    new="Express ground",
                    is_added=True,
                ),
                FieldChange(field="amount", old=None, new="12.99", is_added=True),
            ],
            succeeded=fee_succeeded,
            status_label="" if is_preview else "APPLIED",
        ).model_dump(),
        ActionResult(
            index=3,
            operation="delete_row",
            target_id=9999,
            changes=[],
            succeeded=row_succeeded,
            error=None
            if is_preview
            else "404 Not Found: row 9999 does not exist on SO 42",
            status_label="" if is_preview else "FAILED",
        ).model_dump(),
    ]
    if is_preview:
        message = "Preview: 3 action(s) planned"
    else:
        message = "Applied 2 of 3 action(s); 1 failure"
    return {
        "entity_type": "sales_order",
        "entity_id": 42,
        "is_preview": is_preview,
        "operation": "",
        "changes": [],
        "actions": actions,
        "prior_state": {
            "id": 42,
            "order_no": "SO-2026-001",
            "customer_id": 1501,
            "customer_name": "Sarah Johnson",
            "location_id": 1,
            "status": "NOT_SHIPPED",
            "currency": "USD",
            "total": 1250.0,
            "additional_info": "Customer requested expedited delivery",
            "delivery_date": "2026-05-08T14:30:00Z",
        },
        "warnings": [],
        "next_actions": [],
        "katana_url": "https://factory.katanamrp.com/salesorder/42",
        "message": message,
    }


def _so_modify_fail_fast_not_run_response(*, is_preview: bool = False) -> dict:
    """Build a canned SO modify response exercising the fail-fast NOT-RUN
    tail (#858 finding B).

    The plan has 4 row adds — the first succeeds, the second fails, and
    the third + fourth NEVER RUN (fail-fast halts after the second).
    The apply path mirrors what ``_modify_sales_order_impl`` produces:
    ``response.actions`` holds the 2 executed entries; the unattempted
    tail rides on ``response.extras["not_run_actions"]`` as NOT-RUN
    action dicts. :func:`build_so_modify_ui` merges the two so the
    morphed Line items section renders all 4 rows (APPLIED + FAILED +
    NOT RUN + NOT RUN) instead of silently dropping the leftover plan.

    On preview, every action is pending (``succeeded=None``) and the
    extras dict is empty — the preview already shows the full 4-row
    plan via the regular ``actions`` list. The morph between preview
    and apply is the load-bearing assertion: pre-fix the apply morph
    would HIDE the NOT-RUN rows; post-fix they remain visible.
    """
    succeeded_states = [
        # Action 1: succeeds.
        None if is_preview else True,
        # Action 2: fails — execute_plan stops here on apply.
        None if is_preview else False,
        # Actions 3-4: never attempted on apply.
        None,
        None,
    ]
    error_states = [
        None,
        None if is_preview else "422 Unprocessable: variant 999 archived",
        None,
        None,
    ]
    actions_full = [
        ActionResult(
            index=i + 1,
            operation="add_row",
            target_id=None,
            changes=[
                FieldChange(
                    field="variant_id",
                    old=None,
                    new=100 + i,
                    is_added=True,
                ),
                FieldChange(
                    field="quantity",
                    old=None,
                    new=f"{i + 1}.0",
                    is_added=True,
                ),
            ],
            succeeded=succeeded_states[i],
            error=error_states[i],
        ).model_dump()
        for i in range(4)
    ]
    # On apply, ``response.actions`` is truncated to the 2 executed
    # entries (fail-fast) and the unattempted tail rides on extras as
    # NOT-RUN dicts (matches what ``_modify_sales_order_impl`` produces
    # post-#858-fix).
    if is_preview:
        actions = actions_full
        extras: dict[str, Any] = {}
        message = "Preview: 4 action(s) planned"
    else:
        actions = actions_full[:2]
        extras = {
            "not_run_actions": [
                {
                    "operation": "add_row",
                    "target_id": None,
                    "succeeded": None,
                    "error": None,
                    "status_label": "NOT RUN",
                    "changes": [
                        {
                            "field": "variant_id",
                            "old": None,
                            "new": 100 + i,
                            "is_added": True,
                        },
                        {
                            "field": "quantity",
                            "old": None,
                            "new": f"{i + 1}.0",
                            "is_added": True,
                        },
                    ],
                }
                for i in (2, 3)
            ]
        }
        message = "Applied 1 of 4 action(s); 1 failure; 2 not run"
    return {
        "entity_type": "sales_order",
        "entity_id": 42,
        "is_preview": is_preview,
        "operation": "",
        "changes": [],
        "actions": actions,
        "prior_state": {
            "id": 42,
            "order_no": "SO-2026-001",
            "customer_id": 1501,
            "customer_name": "Sarah Johnson",
            "location_id": 1,
            "status": "NOT_SHIPPED",
            "currency": "USD",
            "total": 1250.0,
            "additional_info": "Customer requested expedited delivery",
            "delivery_date": "2026-05-08T14:30:00Z",
        },
        "warnings": [],
        "next_actions": [],
        "katana_url": "https://factory.katanamrp.com/salesorder/42",
        "message": message,
        "extras": extras,
    }


def _so_modify_header_failed_with_changes_response(*, is_preview: bool = False) -> dict:
    """Build a canned SO modify response exercising the failed
    ``update_header`` WITH field changes morph path (#858 finding C).

    A single ``update_header`` action changes ``status`` from
    NOT_SHIPPED → DELIVERED; on apply the Katana API rejects the
    transition (e.g. invalid state machine move). Pre-fix, the build-
    time ``_render_failed_changes_block`` (read at preview time when
    ``succeeded=None``) painted "no failures" into the view tree and
    NEVER updated on the morph — the operator saw APPLIED chrome
    despite the failure.

    Post-fix, :func:`_so_header_op_failure_alert_text` is the single
    source of truth: it includes failed ``update_header`` actions WITH
    changes too, so the state-driven Alert pops in after the morph
    with the error text. The build-time
    ``_render_failed_changes_block`` was removed from the SO entity
    view to avoid double-render.
    """
    succeeded = None if is_preview else False
    error = None if is_preview else "422 Unprocessable: invalid status transition"
    actions = [
        ActionResult(
            index=1,
            operation="update_header",
            target_id=42,
            changes=[
                FieldChange(field="status", old="PACKED", new="DELIVERED"),
            ],
            succeeded=succeeded,
            error=error,
        ).model_dump(),
    ]
    if is_preview:
        message = "Preview: 1 action(s) planned"
    else:
        message = "Failed: 1 action(s); 1 failure"
    return {
        "entity_type": "sales_order",
        "entity_id": 42,
        "is_preview": is_preview,
        "operation": "",
        "changes": [],
        "actions": actions,
        "prior_state": {
            "id": 42,
            "order_no": "SO-2026-001",
            "customer_id": 1501,
            "customer_name": "Sarah Johnson",
            "location_id": 1,
            "status": "PACKED",
            "currency": "USD",
            "total": 1250.0,
            "additional_info": "Customer requested expedited delivery",
            "delivery_date": "2026-05-08T14:30:00Z",
        },
        "warnings": [],
        "next_actions": [],
        "katana_url": "https://factory.katanamrp.com/salesorder/42",
        "message": message,
    }


def _so_correct_fail_fast_header_skipped_response(*, is_preview: bool = False) -> dict:
    """Build a canned ``correct_sales_order`` response exercising the
    header-step NOT-RUN morph path (#858 round-8).

    Plan: delete fulfillment (phase 1, succeeds) → revert SO header
    (phase 2, succeeds) → edit SO row (phase 3, FAILS). Phase 4
    (re-create fulfillment) and phase 5 (close SO via update_header)
    never run. The close-phase ``update_header`` is the load-bearing
    NOT-RUN entry: pre-round-8 it had no rendering surface (sub-entity
    row lists only bucket sub-entity ops; the header field map filters
    NOT-RUN out per round 7), so the operator couldn't tell the SO
    close step was skipped. Post-round-8 the state-driven
    ``applied_header_skipped_*`` Alert surfaces the skipped step.
    """
    actions_executed: list[dict[str, Any]] = []
    if not is_preview:
        actions_executed = [
            ActionResult(
                index=1,
                operation="delete_fulfillment",
                target_id=77,
                changes=[],
                succeeded=True,
                error=None,
            ).model_dump(),
            ActionResult(
                index=2,
                operation="update_header",
                target_id=99,
                changes=[FieldChange(field="status", new="PENDING")],
                succeeded=True,
                error=None,
            ).model_dump(),
            ActionResult(
                index=3,
                operation="update_row",
                target_id=10,
                changes=[FieldChange(field="variant_id", old=500, new=501)],
                succeeded=False,
                error="Katana refused the row edit",
            ).model_dump(),
        ]
    else:
        # Preview: every action is pending (succeeded=None), no extras.
        actions_executed = [
            ActionResult(
                index=1,
                operation="delete_fulfillment",
                target_id=77,
                changes=[],
                succeeded=None,
                error=None,
            ).model_dump(),
            ActionResult(
                index=2,
                operation="update_header",
                target_id=99,
                changes=[FieldChange(field="status", new="PENDING")],
                succeeded=None,
                error=None,
            ).model_dump(),
            ActionResult(
                index=3,
                operation="update_row",
                target_id=10,
                changes=[FieldChange(field="variant_id", old=500, new=501)],
                succeeded=None,
                error=None,
            ).model_dump(),
            ActionResult(
                index=4,
                operation="add_fulfillment",
                target_id=None,
                changes=[],
                succeeded=None,
                error=None,
            ).model_dump(),
            ActionResult(
                index=5,
                operation="update_header",
                target_id=99,
                changes=[FieldChange(field="status", new="DELIVERED")],
                succeeded=None,
                error=None,
            ).model_dump(),
        ]

    extras: dict[str, Any] = {}
    if not is_preview:
        extras = {
            "not_run_actions": [
                {
                    "operation": "add_fulfillment",
                    "target_id": None,
                    "succeeded": None,
                    "error": None,
                    "status_label": "NOT RUN",
                    "changes": [],
                },
                {
                    "operation": "update_header",
                    "target_id": 99,
                    "succeeded": None,
                    "error": None,
                    "status_label": "NOT RUN",
                    "changes": [
                        {
                            "field": "status",
                            "old": None,
                            "new": "DELIVERED",
                        }
                    ],
                },
            ]
        }

    if is_preview:
        message = "Preview: 5 action(s) planned"
    else:
        message = "Applied 2 of 3 action(s); 1 failure; 2 not run"
    return {
        "entity_type": "sales_order",
        "entity_id": 99,
        "is_preview": is_preview,
        "operation": "",
        "changes": [],
        "actions": actions_executed,
        "prior_state": {
            "id": 99,
            "order_no": "SO-2026-002",
            "customer_id": 1501,
            "customer_name": "Sarah Johnson",
            "location_id": 1,
            "status": "DELIVERED",
            "currency": "USD",
            "total": 1250.0,
            "additional_info": "Customer requested expedited delivery",
            "delivery_date": "2026-05-08T14:30:00Z",
        },
        "warnings": [],
        "next_actions": [],
        "katana_url": "https://factory.katanamrp.com/salesorder/99",
        "message": message,
        "extras": extras,
    }


SCENARIOS: dict[str, Callable[[], PrefabApp]] = {
    # Trivial sanity card — minimal Prefab tree with no DataTable. Used to
    # isolate whether the iframe pipeline works at all vs. a card-specific
    # rendering bug.
    "trivial_text": _trivial_text_app,
    "datatable_inline": _datatable_inline_app,
    "datatable_state": _datatable_state_app,
    "datatable_state_template": _datatable_state_template_app,
    # Audit coverage: post-mustache-fix render checks for every other
    # state-bound DataTable card.
    "search_results": _search_results_app,
    "item_detail": _item_detail_app,
    "product_bom": _product_bom_app,
    "product_bom_empty": _product_bom_empty_app,
    "variant_batch": _variant_batch_app,
    "so_detail": _so_detail_app,
    "inventory_check": _inventory_check_app,
    "inventory_at_single": _inventory_at_single_app,
    "inventory_at_batch": _inventory_at_batch_app,
    "verification": _verification_app,
    "batch_recipe_update": _batch_recipe_update_app,
    # Stock-adjustment family (preview + result for each of create/update/delete).
    "stock_adjustment_create_preview": lambda: build_stock_adjustment_create_ui(
        _stock_adjustment_response(is_preview=True),
        confirm_request=_StubRequest(),
        confirm_tool="create_stock_adjustment",
    ),
    "stock_adjustment_create_applied": lambda: build_stock_adjustment_create_ui(
        _stock_adjustment_response(is_preview=False),
        confirm_request=_StubRequest(),
        confirm_tool="create_stock_adjustment",
    ),
    "stock_adjustment_update_preview": lambda: build_stock_adjustment_update_ui(
        _stock_adjustment_update_response(is_preview=True),
        confirm_request=_StubRequest(),
        confirm_tool="update_stock_adjustment",
    ),
    "stock_adjustment_update_applied": lambda: build_stock_adjustment_update_ui(
        _stock_adjustment_update_response(is_preview=False),
        confirm_request=_StubRequest(),
        confirm_tool="update_stock_adjustment",
    ),
    "stock_adjustment_delete_preview": lambda: build_stock_adjustment_delete_ui(
        _stock_adjustment_delete_response(is_preview=True),
        confirm_request=_StubRequest(),
        confirm_tool="delete_stock_adjustment",
    ),
    "stock_adjustment_delete_applied": lambda: build_stock_adjustment_delete_ui(
        _stock_adjustment_delete_response(is_preview=False),
        confirm_request=_StubRequest(),
        confirm_tool="delete_stock_adjustment",
    ),
    # Customer create card (#817) — preview + applied + addresses variants.
    "customer_create_preview": lambda: build_customer_create_ui(
        _customer_create_response(is_preview=True, with_addresses=False),
        confirm_request=_StubRequest(),
        confirm_tool="create_customer",
    ),
    "customer_create_preview_with_addresses": lambda: build_customer_create_ui(
        _customer_create_response(is_preview=True, with_addresses=True),
        confirm_request=_StubRequest(),
        confirm_tool="create_customer",
    ),
    "customer_create_applied": lambda: build_customer_create_ui(
        _customer_create_response(is_preview=False, with_addresses=True),
        confirm_request=_StubRequest(),
        confirm_tool="create_customer",
    ),
    # Block-warning gate: the Confirm button must hide and the warnings
    # badge must surface when ``warnings`` carries a ``BLOCK:`` prefix.
    # Pins the gate against future regressions (no business-rule warning
    # populates this on the customer create path today; locked in now).
    "customer_create_block_warning": lambda: build_customer_create_ui(
        {
            **_customer_create_response(is_preview=True, with_addresses=False),
            "warnings": [
                "BLOCK: a customer named 'Gourmet Bistro Group' already exists"
            ],
        },
        confirm_request=_StubRequest(),
        confirm_tool="create_customer",
    ),
    # Minimal customer (only ``name``) — pins the empty-Tier-3-body
    # fallback ("No additional contact details provided.").
    "customer_create_minimal": lambda: build_customer_create_ui(
        {
            "id": None,
            "katana_url": None,
            "name": "Minimal Co",
            "is_preview": True,
            "addresses": [],
            "warnings": [],
            "next_actions": [],
            "message": "Preview: customer Minimal Co ready to create",
        },
        confirm_request=_StubRequest(),
        confirm_tool="create_customer",
    ),
    # SO create card with inline shipping fees (#818) — preview / all-success
    # apply / partial-failure apply. Pins the per-fee row rendering, the
    # APPLIED / FAILED status pills, and the destructive Alert on partial
    # failure so a future regression (e.g. the rows-binding shape from #629)
    # can't silently break the surface.
    "so_create_with_fees_preview": lambda: build_so_create_ui(
        _so_create_response_with_shipping_fees(
            is_preview=True,
            fee_outcomes=[
                {
                    "description": "Standard shipping",
                    "amount": "8.95",
                    "tax_rate_id": 301,
                    "succeeded": None,
                    "created_id": None,
                    "error": None,
                },
                {
                    "description": "Handling",
                    "amount": "2.50",
                    "tax_rate_id": None,
                    "succeeded": None,
                    "created_id": None,
                    "error": None,
                },
            ],
        ),
        confirm_request=_StubRequest(),
        confirm_tool="create_sales_order",
    ),
    "so_create_with_fees_applied_all_success": lambda: build_so_create_ui(
        _so_create_response_with_shipping_fees(
            is_preview=False,
            fee_outcomes=[
                {
                    "description": "Standard shipping",
                    "amount": "8.95",
                    "tax_rate_id": 301,
                    "succeeded": True,
                    "created_id": 5001,
                    "error": None,
                },
                {
                    "description": "Handling",
                    "amount": "2.50",
                    "tax_rate_id": None,
                    "succeeded": True,
                    "created_id": 5002,
                    "error": None,
                },
            ],
        ),
        confirm_request=_StubRequest(),
        confirm_tool="create_sales_order",
    ),
    "so_create_with_fees_applied_partial_failure": lambda: build_so_create_ui(
        {
            **_so_create_response_with_shipping_fees(
                is_preview=False,
                fee_outcomes=[
                    {
                        "description": "Standard shipping",
                        "amount": "8.95",
                        "tax_rate_id": None,
                        "succeeded": True,
                        "created_id": 5001,
                        "error": None,
                    },
                    {
                        "description": "Handling",
                        "amount": "2.50",
                        "tax_rate_id": 9999,
                        "succeeded": False,
                        "created_id": None,
                        "error": "422: invalid tax rate id",
                    },
                ],
            ),
            "warnings": [
                "1 of 2 shipping fee(s) failed to create on SO 9001 — "
                "the sales order itself is preserved. Retry the failed fees "
                "via `modify_sales_order(id=9001, add_shipping_fees=[...])`."
            ],
        },
        confirm_request=_StubRequest(),
        confirm_tool="create_sales_order",
    ),
    # #726 — item modify card: header scalar diff + variant diff table (add +
    # update + delete). Pins the dual diff surface + the resolved supplier name
    # + the per-variant status pills end-to-end in a real browser render.
    "item_modify_mixed_preview": lambda: build_item_modify_ui(
        _item_modify_response(is_preview=True, succeeded=None),
        confirm_request=_StubRequest(),
        confirm_tool="modify_item",
    ),
    "item_modify_mixed_applied": lambda: build_item_modify_ui(
        _item_modify_response(is_preview=False, succeeded=True),
        confirm_request=_StubRequest(),
        confirm_tool="modify_item",
    ),
    # #722 follow-up — PO modify card line-item diff table: a header change +
    # (1 add + 1 update + 1 delete) on the rows. Pins the content-drop fix —
    # row CRUD now renders with resolved SKU/name + per-row status — end to end.
    "po_modify_rows_preview": lambda: build_po_modify_ui(
        _po_modify_rows_response(is_preview=True, succeeded=None),
        confirm_request=_StubRequest(),
        confirm_tool="modify_purchase_order",
    ),
    "po_modify_rows_applied": lambda: build_po_modify_ui(
        _po_modify_rows_response(is_preview=False, succeeded=True),
        confirm_request=_StubRequest(),
        confirm_tool="modify_purchase_order",
    ),
    # #721 Phase 4 — MO modify card with all three collection diff tables
    # (recipe / operation / production) + a header diff. Pins the multi-table
    # render + resolved recipe SKU + operation status diff end to end.
    "mo_modify_preview": lambda: build_mo_modify_ui(
        _mo_modify_response(is_preview=True, succeeded=None),
        confirm_request=_StubRequest(),
        confirm_tool="modify_manufacturing_order",
    ),
    "mo_modify_applied": lambda: build_mo_modify_ui(
        _mo_modify_response(is_preview=False, succeeded=True),
        confirm_request=_StubRequest(),
        confirm_tool="modify_manufacturing_order",
    ),
    # #721 Phase 5 — stock-transfer modify card. Header-only (rows are
    # immutable post-create), so no DataTable; every diff reads
    # "(prior unknown) → new" since stock transfers have no GET endpoint.
    "stock_transfer_modify_preview": lambda: build_stock_transfer_modify_ui(
        _stock_transfer_modify_response(is_preview=True, succeeded=None),
        confirm_request=_StubRequest(),
        confirm_tool="modify_stock_transfer",
    ),
    "stock_transfer_modify_applied": lambda: build_stock_transfer_modify_ui(
        _stock_transfer_modify_response(is_preview=False, succeeded=True),
        confirm_request=_StubRequest(),
        confirm_tool="modify_stock_transfer",
    ),
    # #811 — BOM modify card with adds + updates + deletes against a
    # realistic 5-row existing recipe. Pins the row-content + status-pill
    # contract end-to-end in a real browser render.
    "bom_modify_mixed_preview": lambda: build_bom_modify_ui(
        _bom_modify_response(is_preview=True, succeeded=None),
        confirm_request=_StubRequest(),
        confirm_tool="manage_product_bom",
    ),
    "bom_modify_mixed_applied": lambda: build_bom_modify_ui(
        _bom_modify_response(is_preview=False, succeeded=True),
        confirm_request=_StubRequest(),
        confirm_tool="manage_product_bom",
    ),
    # #723 — SO modify card with a partial-failure applied state. Pins
    # the card-level PARTIAL FAILURE badge, the state-driven sub-entity
    # failed-action Alert, the per-action APPLIED / FAILED Badges in
    # the Line items + Shipping fees sections, and the failed-row
    # ``✗ `` gutter in a real browser render.
    "so_modify_partial_failure_applied": lambda: build_so_modify_ui(
        _so_modify_partial_failure_response(),
        confirm_request=_StubRequest(),
        confirm_tool="modify_sales_order",
    ),
    # #723 / #858 — preview side of the same partial-failure plan. Used
    # by the click-through morph test: the iframe renders this preview
    # tree, the user clicks Confirm, the apply call returns the applied
    # response (via the ``modify_sales_order`` stub tool below), and the
    # on_success SetState chain flips the state slots so the sub-entity
    # failed-action Alert pops in. Catches slot-name-typo regressions
    # the standalone-applied test cannot.
    "so_modify_partial_failure_preview": lambda: build_so_modify_ui(
        _so_modify_partial_failure_response(is_preview=True),
        confirm_request=_StubRequest(id=42),
        confirm_tool="modify_sales_order",
    ),
    # #858 finding B — failed top-level delete renders FAILED chrome WITH
    # the dedicated header-op Alert surfacing the ActionResult.error text.
    # Pre-fix this rendered with no visible error message.
    "so_delete_failed_applied": lambda: build_so_modify_ui(
        _so_failed_delete_response(is_preview=False),
        confirm_request=_StubRequest(id=42),
        confirm_tool="delete_sales_order",
    ),
    "so_delete_failed_preview": lambda: build_so_modify_ui(
        _so_failed_delete_response(is_preview=True),
        confirm_request=_StubRequest(id=42),
        confirm_tool="delete_sales_order",
    ),
    # #858 finding B (NOT-RUN morph) — fail-fast leaves the unattempted
    # plan tail visible as NOT-RUN rows on the morphed card instead of
    # silently dropping them. Pre-fix: 4-row plan that fails on row 2
    # morphed to a card showing only 2 rows.
    "so_modify_fail_fast_not_run_applied": lambda: build_so_modify_ui(
        _so_modify_fail_fast_not_run_response(is_preview=False),
        confirm_request=_StubRequest(id=42),
        confirm_tool="modify_sales_order_fail_fast",
    ),
    "so_modify_fail_fast_not_run_preview": lambda: build_so_modify_ui(
        _so_modify_fail_fast_not_run_response(is_preview=True),
        confirm_request=_StubRequest(id=42),
        confirm_tool="modify_sales_order_fail_fast",
    ),
    # #858 Copilot follow-up (comment 3312071378) — same NOT-RUN morph
    # contract, but for ``correct_sales_order``. ``build_so_modify_ui``
    # handles both tools and merges ``extras["not_run_actions"]`` the
    # same way; this scenario pins that ``_correct_sales_order_impl``'s
    # failure path populates those extras correctly so the morphed card
    # surfaces the unattempted restore / recreate / close phases.
    "so_correct_fail_fast_not_run_applied": lambda: build_so_modify_ui(
        _so_modify_fail_fast_not_run_response(is_preview=False),
        confirm_request=_StubRequest(id=42),
        confirm_tool="correct_sales_order",
    ),
    "so_correct_fail_fast_not_run_preview": lambda: build_so_modify_ui(
        _so_modify_fail_fast_not_run_response(is_preview=True),
        confirm_request=_StubRequest(id=42),
        confirm_tool="correct_sales_order",
    ),
    # #858 round-8 — fail-fast ``correct_sales_order`` whose close-phase
    # ``update_header`` lands in the NOT-RUN tail. Surfaces the
    # ``applied_header_skipped_*`` Alert that owns the rendering surface
    # for skipped header steps (sub-entity row lists only bucket sub-
    # entity ops; the header field map filters NOT-RUN out per round 7).
    "so_correct_fail_fast_header_skipped_applied": lambda: build_so_modify_ui(
        _so_correct_fail_fast_header_skipped_response(is_preview=False),
        confirm_request=_StubRequest(id=99),
        confirm_tool="correct_sales_order",
    ),
    "so_correct_fail_fast_header_skipped_preview": lambda: build_so_modify_ui(
        _so_correct_fail_fast_header_skipped_response(is_preview=True),
        confirm_request=_StubRequest(id=99),
        confirm_tool="correct_sales_order",
    ),
    # #858 finding C — failed update_header WITH field changes morphs
    # to a card with the state-driven header-op Alert visible (was
    # invisible pre-fix because the build-time ``_render_failed_changes_block``
    # painted preview-time content into the view tree).
    "so_modify_header_failed_with_changes_applied": lambda: build_so_modify_ui(
        _so_modify_header_failed_with_changes_response(is_preview=False),
        confirm_request=_StubRequest(id=42),
        confirm_tool="modify_sales_order_header_fail",
    ),
    "so_modify_header_failed_with_changes_preview": lambda: build_so_modify_ui(
        _so_modify_header_failed_with_changes_response(is_preview=True),
        confirm_request=_StubRequest(id=42),
        confirm_tool="modify_sales_order_header_fail",
    ),
}


# ---------------------------------------------------------------------------
# FastMCP server
# ---------------------------------------------------------------------------


mcp: FastMCP = FastMCP(name="katana-render-test")


@mcp.tool(meta={"ui": True})
async def render_scenario(name: str) -> PrefabApp:
    """Render a named card-builder scenario for browser tests."""
    builder = SCENARIOS.get(name)
    if builder is None:
        raise ValueError(f"Unknown scenario {name!r}. Available: {sorted(SCENARIOS)}")
    return builder()


@mcp.tool(meta={"ui": True})
async def modify_manufacturing_order(
    id: int,
    preview: bool = True,
    update_header: Any = None,
    add_recipe_rows: Any = None,
    update_recipe_rows: Any = None,
    delete_recipe_row_ids: Any = None,
    add_operation_rows: Any = None,
    update_operation_rows: Any = None,
    delete_operation_row_ids: Any = None,
    add_productions: Any = None,
    update_productions: Any = None,
    delete_production_ids: Any = None,
) -> ToolResult:
    """Stub for the click-through test — when the Confirm button on the
    preview card fires, the iframe calls this with ``preview=False`` and we
    return a canned apply response so the live-tick SetState fires.

    Sub-payload args mirror :class:`ModifyManufacturingOrderRequest` so
    FastMCP's signature validator accepts the full Confirm-button payload.
    All values are ignored — the stub always returns the same canned
    envelope.

    Uses ``make_tool_result`` (same helper real modification tools use) so
    the wire shape matches production exactly: ``content`` carries the
    response JSON, ``structured_content`` carries the apply result card's
    Prefab envelope. This pins the contract that ``RESULT.actions`` in
    the on_success Rx expression resolves the same way against the stub
    as it does against the real tool.
    """
    del (
        id,
        update_header,
        add_recipe_rows,
        update_recipe_rows,
        delete_recipe_row_ids,
        add_operation_rows,
        update_operation_rows,
        delete_operation_row_ids,
        add_productions,
        update_productions,
        delete_production_ids,
    )  # unused — canned response
    response_dict = _mo_modify_response(
        is_preview=preview, succeeded=None if preview else True
    )
    response = ModificationResponse.model_validate(response_dict)
    ui = build_mo_modify_ui(
        response_dict,
        confirm_request=_StubRequest(),
        confirm_tool="modify_manufacturing_order",
    )
    return make_tool_result(response, ui=ui)


@mcp.tool(meta={"ui": True})
async def modify_sales_order(
    id: int,
    preview: bool = True,
    update_header: Any = None,
    add_rows: Any = None,
    update_rows: Any = None,
    delete_row_ids: Any = None,
    add_addresses: Any = None,
    update_addresses: Any = None,
    delete_address_ids: Any = None,
    add_fulfillments: Any = None,
    update_fulfillments: Any = None,
    delete_fulfillment_ids: Any = None,
    add_shipping_fees: Any = None,
    update_shipping_fees: Any = None,
    delete_shipping_fee_ids: Any = None,
) -> ToolResult:
    """Stub for the SO modify click-through test — when the Confirm button
    on the preview card fires, the iframe calls this with ``preview=False``
    and we return the canned partial-failure apply response so the
    on_success SetState chain in :func:`build_so_modify_ui` fires.

    Sub-payload args mirror :class:`ModifySalesOrderRequest` so FastMCP's
    signature validator accepts the full Confirm-button payload. All
    values are ignored — the stub always returns the same canned envelope.

    Uses ``make_tool_result`` (same helper the real ``modify_sales_order``
    tool uses) so the wire shape matches production exactly: ``content``
    carries the response JSON, ``structured_content`` carries the apply
    result card's Prefab envelope (which is what ``$result.state.*``
    resolves against in the on_success chain).
    """
    del (
        id,
        update_header,
        add_rows,
        update_rows,
        delete_row_ids,
        add_addresses,
        update_addresses,
        delete_address_ids,
        add_fulfillments,
        update_fulfillments,
        delete_fulfillment_ids,
        add_shipping_fees,
        update_shipping_fees,
        delete_shipping_fee_ids,
    )  # unused — canned response
    response_dict = _so_modify_partial_failure_response(is_preview=preview)
    response = ModificationResponse.model_validate(response_dict)
    ui = build_so_modify_ui(
        response_dict,
        confirm_request=_StubRequest(id=42),
        confirm_tool="modify_sales_order",
    )
    return make_tool_result(response, ui=ui)


@mcp.tool(meta={"ui": True})
async def delete_sales_order(
    id: int,
    preview: bool = True,
) -> ToolResult:
    """Stub for the SO delete click-through test (#858 finding B) —
    Confirm on the preview card fires this with ``preview=False`` and
    the stub returns the failed-delete apply response so the
    state-driven header-op Alert pops in via the on_success chain.

    Wire shape matches the real ``delete_sales_order`` tool exactly so
    the morph contract pins the same behavior production does.
    """
    del id  # unused — canned response
    response_dict = _so_failed_delete_response(is_preview=preview)
    response = ModificationResponse.model_validate(response_dict)
    ui = build_so_modify_ui(
        response_dict,
        confirm_request=_StubRequest(id=42),
        confirm_tool="delete_sales_order",
    )
    return make_tool_result(response, ui=ui)


@mcp.tool(meta={"ui": True})
async def modify_sales_order_fail_fast(
    id: int,
    preview: bool = True,
) -> ToolResult:
    """Stub for the #858 finding B (NOT-RUN) click-through test —
    distinct ``confirm_tool`` so the click-through test can target a
    different canned response than the ``modify_sales_order`` partial-
    failure stub above. Confirm on the preview re-issues this with
    ``preview=False``; the canned apply response carries 2 executed
    actions + 2 NOT-RUN entries on ``extras["not_run_actions"]``, which
    :func:`build_so_modify_ui` merges into the Line items section so
    all 4 rows remain visible on the morphed card.
    """
    del id  # unused — canned response
    response_dict = _so_modify_fail_fast_not_run_response(is_preview=preview)
    response = ModificationResponse.model_validate(response_dict)
    ui = build_so_modify_ui(
        response_dict,
        confirm_request=_StubRequest(id=42),
        confirm_tool="modify_sales_order_fail_fast",
    )
    return make_tool_result(response, ui=ui)


@mcp.tool(meta={"ui": True})
async def modify_sales_order_header_fail(
    id: int,
    preview: bool = True,
) -> ToolResult:
    """Stub for the #858 finding C click-through test — failed
    ``update_header`` WITH field changes. Confirm re-issues with
    ``preview=False``; the canned apply response has ``succeeded=False``
    on the update_header action with a field change in ``changes``.

    The morph-target assertion is that the state-driven
    ``applied_header_failed_*`` Alert pops in (gated by
    ``If(Rx("applied_header_failed_count") > 0)``) with the 422 error
    text — pre-fix the build-time ``_render_failed_changes_block``
    painted preview-time content into the view tree and stayed at
    "no failures" on the morph.
    """
    del id  # unused — canned response
    response_dict = _so_modify_header_failed_with_changes_response(is_preview=preview)
    response = ModificationResponse.model_validate(response_dict)
    ui = build_so_modify_ui(
        response_dict,
        confirm_request=_StubRequest(id=42),
        confirm_tool="modify_sales_order_header_fail",
    )
    return make_tool_result(response, ui=ui)


class _EchoVariantDetails(BaseModel):
    """Echoes back the arguments the host actually passed to
    ``get_variant_details`` — used by the #494 row-click tests to verify
    DataTable per-row ``{{ field }}`` substitution resolved against the
    clicked row's data (not null, not the literal Mustache string).
    """

    received_sku: str | None = None
    received_variant_id: int | None = None


# Fixed cross-process path so the browser-test subprocess and the
# pytest process agree on where the stub writes its received args.
# Cleared before each row-click test and read back after the click.
GET_VARIANT_DETAILS_RECORD_PATH = (
    Path(tempfile.gettempdir()) / "katana_test_get_variant_details_received.json"
)


@mcp.tool(meta={"ui": True})
async def get_variant_details(
    sku: str | None = None,
    variant_id: int | None = None,
) -> ToolResult:
    """Echo stub for #494 row-click binding tests.

    The two row-click drill-downs that exercise per-row binding:

    - ``build_search_results_ui``: ``arguments={"sku": "{{ sku }}"}``
    - ``build_item_detail_ui`` variants table: ``arguments={"variant_id":
      "{{ id }}"}``

    A correctly-substituting host calls this with the clicked row's
    actual value. A broken host calls it with ``None`` (silent drop), the
    literal string ``"{{ sku }}"``, or fires ``on_error``. The stub
    records whichever value the host actually delivered to a cross-process
    file at :data:`GET_VARIANT_DETAILS_RECORD_PATH` so the browser test
    can read it back after the click — the response card itself can't
    be used as the assertion target because the Slot/RESULT envelope
    mismatch (separately filed) prevents the response from rendering in
    the ``detail`` slot.
    """
    received = {"received_sku": sku, "received_variant_id": variant_id}
    GET_VARIANT_DETAILS_RECORD_PATH.write_text(json.dumps(received))
    response = _EchoVariantDetails(received_sku=sku, received_variant_id=variant_id)
    from prefab_ui.components import Card, CardContent, CardTitle, Text

    with PrefabApp(state={}, css_class="p-4") as ui, Card():
        CardTitle(content="Echoed Variant Details")
        with CardContent():
            Text(content=f"received_sku={sku!r}")
            Text(content=f"received_variant_id={variant_id!r}")
    return make_tool_result(response, ui=ui)


if __name__ == "__main__":
    mcp.run(transport="http", port=8765)
