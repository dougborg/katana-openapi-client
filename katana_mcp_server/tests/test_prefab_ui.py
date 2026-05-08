"""Tests for Prefab UI builder functions.

Verifies that all UI builders can be called without errors and produce
valid PrefabApp instances. This catches constructor signature mismatches
(e.g., positional vs keyword args) that would only surface at runtime.
"""

from __future__ import annotations

import json
import re
from typing import Any

import pytest
from katana_mcp.tools.prefab_ui import (
    build_batch_recipe_update_ui,
    build_fulfill_preview_ui,
    build_fulfill_success_ui,
    build_inventory_check_ui,
    build_item_detail_ui,
    build_item_mutation_ui,
    build_low_stock_ui,
    build_modification_preview_ui,
    build_modification_result_ui,
    build_order_created_ui,
    build_order_preview_ui,
    build_receipt_ui,
    build_search_results_ui,
    build_variant_details_ui,
    build_verification_ui,
)
from prefab_ui.app import PrefabApp
from pydantic import BaseModel


class _StubRequest(BaseModel):
    """Minimal Pydantic stub used by builder tests that don't care about the
    real request shape — only that the builder accepts a BaseModel and emits
    a valid envelope.
    """

    preview: bool = True


def _walk_view_tree(node: object) -> list[dict[str, Any]]:
    """Yield every Component dict in a view tree (for test traversal)."""
    found: list[dict[str, Any]] = []

    def visit(o: object) -> None:
        if isinstance(o, dict):
            if "type" in o:
                found.append(o)
            for v in o.values():
                visit(v)
        elif isinstance(o, list):
            for v in o:
                visit(v)

    visit(node)
    return found


_MUSTACHE_RE = re.compile(r"^\s*\{\{\s*([^}\s]+)\s*\}\}\s*$")


def _assert_state_bindings_resolve(envelope: dict[str, Any]) -> None:
    """Every DataTable rendering rows by state-key reference must point to
    a slot that exists in ``state``, AND must use the mustache template
    form ``{{ key }}``. Bare strings crash the JS renderer with
    ``t.some is not a function`` — discovered via headless render tests.
    """
    state = envelope.get("state") or {}
    for component in _walk_view_tree(envelope.get("view")):
        if component.get("type") != "DataTable":
            continue
        rows = component.get("rows")
        if not isinstance(rows, str):
            continue
        m = _MUSTACHE_RE.match(rows)
        assert m is not None, (
            f"DataTable.rows={rows!r} is a bare string. State-bound rows "
            f"must use the mustache template form '{{{{ key }}}}' — bare "
            f"strings crash the JS renderer."
        )
        # The mustache content can be a path expression like "stock.by_location"
        # — only the first segment must exist in state.
        first_segment = m.group(1).split(".", 1)[0]
        assert first_segment in state, (
            f"DataTable.rows={rows!r} references missing state slot "
            f"{first_segment!r}. Available: {sorted(state)}"
        )


def _assert_valid_prefab(app: PrefabApp) -> None:
    """Assert that a PrefabApp serializes to valid JSON.

    Beyond the basic shape check, also rounds-trips through ``json.dumps``
    (catches non-serializable values that ``to_json`` may have skipped) and
    verifies that every state-bound DataTable references a present slot.
    """
    result = app.to_json()
    assert isinstance(result, dict)
    assert "$prefab" in result
    # Full JSON serialization roundtrip — catches anything ``to_json``
    # produced that pydantic_core wouldn't accept downstream.
    json.dumps(result)
    _assert_state_bindings_resolve(result)


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

    def test_with_items_renders_table_and_buttons(self):
        """Regression guard for #470 — the existing populated-results path
        must still render the DataTable, the drill-down Slot, and the
        "Check inventory" button. Pairs with
        ``test_empty_results_omits_table_and_buttons``.
        """
        items = [
            {"id": 1, "sku": "SKU-001", "name": "Widget", "is_sellable": True},
        ]
        app = build_search_results_ui(items, "widget", 1)
        envelope = app.to_json()
        assert _has_node_of_type(envelope, "DataTable"), (
            "Populated search results must render a DataTable."
        )
        assert _has_node_of_type(envelope, "Slot"), (
            "Populated search results must render the drill-down Slot."
        )
        check_inventory_buttons = _find_buttons_by_label(
            envelope, "Check inventory for search results"
        )
        assert len(check_inventory_buttons) == 1, (
            "Populated search results must render the 'Check inventory' button."
        )

    def test_empty_results(self):
        app = build_search_results_ui([], "nothing", 0)
        _assert_valid_prefab(app)

    def test_empty_results_omits_table_and_buttons(self):
        """#470 — when ``total_count == 0`` we render the header + badges
        + a Muted hint, but no DataTable, no Slot, and no "Check
        inventory" button (all of which would reference nonexistent
        results).
        """
        app = build_search_results_ui([], "00.4021.018.003", 0)
        envelope = app.to_json()

        assert not _has_node_of_type(envelope, "DataTable"), (
            "Empty search results must not render a DataTable."
        )
        assert not _has_node_of_type(envelope, "Slot"), (
            "Empty search results must not render the drill-down Slot."
        )
        check_inventory_buttons = _find_buttons_by_label(
            envelope, "Check inventory for search results"
        )
        assert len(check_inventory_buttons) == 0, (
            "Empty search results must not render the 'Check inventory' button."
        )

        # Empty-state hint must mention the query and surface the fallback
        # advice so a user pasting a full SKU knows to try a substring.
        # Assert on the Muted node's actual content rather than
        # ``str(envelope)`` — the header badge renders ``Query: ...``
        # unconditionally, so an envelope-wide substring check would pass
        # even if the Muted hint regressed.
        muted_contents = _collect_node_content(envelope, "Muted")
        hint = next(
            (c for c in muted_contents if c.startswith("No items match")),
            None,
        )
        assert hint is not None, (
            f"Empty-state must render a 'No items match' Muted hint; "
            f"got Muted contents: {muted_contents!r}"
        )
        assert '"00.4021.018.003"' in hint, (
            f"Empty-state hint must echo the original query; got {hint!r}"
        )
        assert "partial SKU" in hint, (
            f"Empty-state hint must suggest a partial-SKU/name fallback; got {hint!r}"
        )


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

    def test_includes_uom_when_set(self):
        """UoM should render in the reference section when the parent supplied it."""
        variant = {
            "id": 100,
            "sku": "SEAL-250",
            "name": "Tubeless Sealant",
            "uom": "ml",
            "sales_price": 12.99,
        }
        app = build_variant_details_ui(variant)
        _assert_valid_prefab(app)
        rendered = str(app.to_json())
        assert "UoM: ml" in rendered
        # Price should use uom suffix when uom isn't pcs/ea.
        assert "$12.99 / ml" in rendered

    def test_omits_uom_when_unset(self):
        """No UoM line and no /uom price suffix when parent didn't supply uom."""
        variant = {
            "id": 100,
            "sku": "SKU-001",
            "name": "Widget",
            "sales_price": 10.0,
        }
        app = build_variant_details_ui(variant)
        _assert_valid_prefab(app)
        rendered = str(app.to_json())
        assert "UoM:" not in rendered
        assert "$10.00" in rendered
        # No `/ <uom>` suffix on the bare price.
        assert "$10.00 /" not in rendered

    def test_includes_config_attributes_as_badges(self):
        """Config attributes should appear inline so the variant axes are visible."""
        variant = {
            "id": 100,
            "sku": "SHIRT-RED-L",
            "name": "T-Shirt",
            "config_attributes": [
                {"config_name": "Color", "config_value": "Red"},
                {"config_name": "Size", "config_value": "Large"},
            ],
        }
        app = build_variant_details_ui(variant)
        _assert_valid_prefab(app)
        rendered = str(app.to_json())
        assert "Color: Red" in rendered
        assert "Size: Large" in rendered

    def test_includes_default_supplier_name(self):
        """Supplier name (with id in parens) should appear in the reference section."""
        variant = {
            "id": 100,
            "sku": "SKU-001",
            "name": "Widget",
            "default_supplier_id": 42,
            "default_supplier_name": "Acme Industrial",
        }
        app = build_variant_details_ui(variant)
        _assert_valid_prefab(app)
        rendered = str(app.to_json())
        assert "Default Supplier: Acme Industrial (42)" in rendered

    def test_renders_when_parent_lookup_returns_nothing(self):
        """When parent enrichment finds nothing (uom/supplier/batch all None),
        the card still renders without crashing and skips the parent-derived rows.
        """
        variant = {
            "id": 100,
            "sku": "SKU-001",
            "name": "Orphan Variant",
            "sales_price": 5.0,
            "uom": None,
            "default_supplier_id": None,
            "default_supplier_name": None,
            "is_batch_tracked": None,
        }
        app = build_variant_details_ui(variant)
        _assert_valid_prefab(app)
        rendered = str(app.to_json())
        assert "UoM:" not in rendered
        assert "Default Supplier" not in rendered
        assert "Batch tracked" not in rendered
        # Identity still renders.
        assert "Orphan Variant" in rendered
        assert "SKU-001" in rendered


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

    def test_with_items_renders_table_and_restock_button(self):
        """Regression guard for the empty-state fix bundled with #470 —
        the populated path must still render the DataTable and the
        "Create Restock Orders" button.
        """
        items = [
            {
                "sku": "SKU-001",
                "product_name": "Widget",
                "current_stock": 3,
                "threshold": 10,
            },
        ]
        app = build_low_stock_ui(items, 10, 1)
        envelope = app.to_json()
        assert _has_node_of_type(envelope, "DataTable"), (
            "Populated low-stock report must render a DataTable."
        )
        restock_buttons = _find_buttons_by_label(envelope, "Create Restock Orders")
        assert len(restock_buttons) == 1, (
            "Populated low-stock report must render the 'Create Restock Orders' button."
        )

    def test_empty(self):
        app = build_low_stock_ui([], 10, 0)
        _assert_valid_prefab(app)

    def test_empty_omits_table_and_restock_button(self):
        """#470-adjacent — when ``total_count == 0`` (no items below the
        threshold) the report drops the empty DataTable and the
        "Create Restock Orders" button (both reference nonexistent rows)
        and renders an "all clear" Muted hint instead.
        """
        app = build_low_stock_ui([], 10, 0)
        envelope = app.to_json()

        assert not _has_node_of_type(envelope, "DataTable"), (
            "Empty low-stock report must not render a DataTable."
        )
        restock_buttons = _find_buttons_by_label(envelope, "Create Restock Orders")
        assert len(restock_buttons) == 0, (
            "Empty low-stock report must not render the 'Create Restock Orders' button."
        )

        # Assert on the Muted node's actual content rather than
        # ``str(envelope)`` — the header badge renders ``Threshold: 10``
        # unconditionally, so a substring check on the whole envelope
        # would pass even if the Muted hint regressed.
        muted_contents = _collect_node_content(envelope, "Muted")
        hint = next(
            (c for c in muted_contents if "threshold of" in c),
            None,
        )
        assert hint is not None, (
            f"Empty-state must render a 'threshold of …' Muted hint; "
            f"got Muted contents: {muted_contents!r}"
        )
        assert "threshold of 10" in hint, (
            f"Empty-state hint must echo the threshold value; got {hint!r}"
        )


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
        app = build_order_preview_ui(
            order,
            "Purchase Order",
            confirm_request=_StubRequest(),
            confirm_tool="create_purchase_order",
        )
        _assert_valid_prefab(app)

    def test_sales_order(self):
        order = {
            "order_number": "SO-001",
            "status": "PENDING",
            "customer_id": 1,
            "total": 500.0,
            "currency": "EUR",
        }
        app = build_order_preview_ui(
            order,
            "Sales Order",
            confirm_request=_StubRequest(),
            confirm_tool="create_sales_order",
        )
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
        app = build_order_created_ui(order, "Purchase Order")
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


class TestBuildBatchRecipeUpdateUI:
    def test_preview_with_replacements(self):
        response = {
            "is_preview": True,
            "total_ops": 3,
            "success_count": 0,
            "failed_count": 0,
            "skipped_count": 0,
            "results": [
                {
                    "op_type": "delete",
                    "manufacturing_order_id": 9999,
                    "recipe_row_id": 5001,
                    "variant_id": 100,
                    "sku": "OLD-FORK",
                    "status": "pending",
                    "group_label": "OLD-FORK → [NEW-FORK, AIR-SHAFT]",
                },
                {
                    "op_type": "add",
                    "manufacturing_order_id": 9999,
                    "variant_id": 200,
                    "sku": "NEW-FORK",
                    "planned_quantity_per_unit": 1.0,
                    "status": "pending",
                    "group_label": "OLD-FORK → [NEW-FORK, AIR-SHAFT]",
                },
                {
                    "op_type": "add",
                    "manufacturing_order_id": 9999,
                    "variant_id": 201,
                    "sku": "AIR-SHAFT",
                    "planned_quantity_per_unit": 1.0,
                    "status": "pending",
                    "group_label": "OLD-FORK → [NEW-FORK, AIR-SHAFT]",
                },
            ],
            "warnings": [],
            "message": "Preview: 3 sub-operations planned",
        }
        app = build_batch_recipe_update_ui(response)
        _assert_valid_prefab(app)

    def test_executed_with_mixed_results(self):
        response = {
            "is_preview": False,
            "total_ops": 3,
            "success_count": 2,
            "failed_count": 1,
            "skipped_count": 0,
            "results": [
                {
                    "op_type": "delete",
                    "manufacturing_order_id": 9999,
                    "recipe_row_id": 5001,
                    "status": "success",
                    "group_label": "group1",
                },
                {
                    "op_type": "add",
                    "manufacturing_order_id": 9999,
                    "variant_id": 200,
                    "sku": "NEW-FORK",
                    "planned_quantity_per_unit": 1.0,
                    "status": "success",
                    "group_label": "group1",
                    "recipe_row_id": 9001,
                },
                {
                    "op_type": "add",
                    "manufacturing_order_id": 9999,
                    "variant_id": 201,
                    "sku": "BAD",
                    "planned_quantity_per_unit": 1.0,
                    "status": "failed",
                    "error": "422 validation error",
                    "group_label": "group1",
                },
            ],
            "warnings": [],
            "message": "Batch update completed: 2 succeeded, 1 failed",
        }
        app = build_batch_recipe_update_ui(response)
        _assert_valid_prefab(app)

    def test_empty_results(self):
        response = {
            "is_preview": True,
            "total_ops": 0,
            "success_count": 0,
            "failed_count": 0,
            "skipped_count": 0,
            "results": [],
            "warnings": [],
            "message": "Nothing to do",
        }
        app = build_batch_recipe_update_ui(response)
        _assert_valid_prefab(app)

    def test_with_warnings(self):
        response = {
            "is_preview": True,
            "total_ops": 1,
            "success_count": 0,
            "failed_count": 0,
            "skipped_count": 1,
            "results": [
                {
                    "op_type": "add",
                    "manufacturing_order_id": 9999,
                    "variant_id": 200,
                    "sku": "NEW-FORK",
                    "planned_quantity_per_unit": 1.0,
                    "status": "skipped",
                    "error": "Old variant not present in this MO",
                    "group_label": "OLD-FORK → [NEW-FORK]",
                },
            ],
            "warnings": ["MO 9999: old variant 100 not in recipe — skipping"],
            "message": "Preview with warnings",
        }
        app = build_batch_recipe_update_ui(response)
        _assert_valid_prefab(app)


def _confirm_button_on_click(envelope: dict, label: str) -> list[dict]:
    """Return the on_click action list for the Confirm button matching ``label``.

    All Confirm buttons in the new (post-#316) confirmation pattern fire
    a list of two actions: ``setState("pending", True)`` and
    ``sendMessage("Apply: call <tool>(<args>, preview=False)")``. The
    Cancel button mirrors this with ``cancelled`` and a ``"Cancel: ..."``
    SendMessage.
    """
    buttons = _find_buttons_by_label(envelope, label)
    assert len(buttons) == 1, (
        f"Expected exactly one Button with label {label!r}; found {len(buttons)}."
    )
    on_click = buttons[0].get("onClick") or buttons[0].get("on_click")
    assert isinstance(on_click, list), (
        f"Button {label!r}'s onClick should be a list of actions; got {on_click!r}"
    )
    return on_click


class TestConfirmButtonEmitsApplyMessage:
    """The Confirm button on every preview card must fire two actions:

    1. ``setState("pending", True)`` — flips the card to a "Pending…"
       pill and grays out the buttons (no double-fire footgun).
    2. ``sendMessage("Apply: call <tool>(<inlined args>, preview=False)")``
       — prompts the agent to re-issue the apply call.

    The button does **not** fire ``CallTool`` directly. Per ADR-0015 and
    the spec finding behind #316, an iframe-initiated ``tools/call``
    returns its result to the iframe, not to the agent — so the only way
    for the agent to see the apply response is to make the call itself.
    """

    @staticmethod
    def _assert_apply_actions(on_click: list[dict], tool_name: str) -> dict:
        """Validate that on_click is exactly [SetState(pending, True),
        SendMessage(Apply: call <tool>(...))] and return the SendMessage."""
        set_states = [a for a in on_click if a.get("action") == "setState"]
        send_messages = [a for a in on_click if a.get("action") == "sendMessage"]
        assert any(
            a.get("key") == "pending" and a.get("value") is True for a in set_states
        ), f"Expected setState('pending', True) in on_click; got {on_click!r}"
        apply_msgs = [
            m
            for m in send_messages
            if isinstance(m.get("content"), str)
            and m["content"].startswith(f"Apply: call {tool_name}(")
        ]
        assert len(apply_msgs) == 1, (
            f"Expected exactly one SendMessage with 'Apply: call {tool_name}('; "
            f"got {[m.get('content') for m in send_messages]!r}"
        )
        return apply_msgs[0]

    def test_order_preview_confirm_emits_apply_send_message(self):
        from katana_mcp.tools.foundation.purchase_orders import (
            CreatePurchaseOrderRequest,
            PurchaseOrderItem,
        )

        request = CreatePurchaseOrderRequest(
            supplier_id=2,
            location_id=3,
            order_number="PO-1",
            items=[PurchaseOrderItem(variant_id=10, quantity=1.0, price_per_unit=2.0)],
        )
        app = build_order_preview_ui(
            {
                "id": 1,
                "order_number": "PO-1",
                "supplier_id": 2,
                "location_id": 3,
                "status": "NOT_RECEIVED",
                "warnings": [],
            },
            "Purchase Order",
            confirm_request=request,
            confirm_tool="create_purchase_order",
        )
        envelope = app.to_json()

        on_click = _confirm_button_on_click(envelope, "Confirm & Create Purchase Order")
        msg = self._assert_apply_actions(on_click, "create_purchase_order")
        # Args inlined into the SendMessage text so the agent re-issues
        # with the exact preview values; preview=False is overridden last
        # so the apply path is selected.
        assert "supplier_id=2" in msg["content"]
        assert "location_id=3" in msg["content"]
        assert "preview=False" in msg["content"]

    def test_fulfill_preview_confirm_emits_apply_send_message(self):
        app = build_fulfill_preview_ui(
            {
                "order_id": 9999,
                "order_type": "sales",
                "order_number": "SO-1",
                "status": "PARTIALLY_DELIVERED",
                "warnings": [],
            }
        )
        envelope = app.to_json()
        on_click = _confirm_button_on_click(envelope, "Confirm Fulfillment")
        msg = self._assert_apply_actions(on_click, "fulfill_order")
        assert "order_id=9999" in msg["content"]
        assert "order_type='sales'" in msg["content"]
        assert "preview=False" in msg["content"]

    def test_receipt_preview_confirm_emits_apply_send_message(self):
        from katana_mcp.tools.foundation.purchase_orders import (
            ReceiveItemRequest,
            ReceivePurchaseOrderRequest,
        )

        request = ReceivePurchaseOrderRequest(
            order_id=1234,
            items=[ReceiveItemRequest(purchase_order_row_id=10, quantity=5.0)],
        )
        app = build_receipt_ui(
            {
                "order_id": 1234,
                "order_number": "PO-1",
                "is_preview": True,
                "items_received": 5,
                "status": "NOT_RECEIVED",
                "warnings": [],
            },
            confirm_request=request,
            confirm_tool="receive_purchase_order",
        )
        envelope = app.to_json()
        on_click = _confirm_button_on_click(envelope, "Confirm Receipt")
        msg = self._assert_apply_actions(on_click, "receive_purchase_order")
        assert "order_id=1234" in msg["content"]
        assert "preview=False" in msg["content"]

    def test_batch_recipe_preview_confirm_emits_apply_send_message(self):
        request = _StubRequest()
        app = build_batch_recipe_update_ui(
            {
                "is_preview": True,
                "total_ops": 1,
                "success_count": 0,
                "failed_count": 0,
                "skipped_count": 0,
                "results": [
                    {
                        "op_type": "delete",
                        "manufacturing_order_id": 9999,
                        "recipe_row_id": 5001,
                        "status": "pending",
                    }
                ],
                "warnings": [],
                "message": "Preview",
            },
            confirm_request=request,
            confirm_tool="batch_update_recipes",
        )
        envelope = app.to_json()
        on_click = _confirm_button_on_click(envelope, "Execute batch")
        msg = self._assert_apply_actions(on_click, "batch_update_recipes")
        assert "preview=False" in msg["content"]


class TestConfirmButtonDirectApplyRail:
    """Direct-apply rail (ADR-0016, supersedes ADR-0015 for opted-in tools):

    The Confirm button fires ``tools/call`` directly from the iframe with
    the original args + ``preview=False``, and on success pushes the
    structured result back to the agent's model context via
    ``ui/update-model-context``. The agent does NOT re-issue the call.

    Currently opted into by ``create_purchase_order``; rolling out to other
    write tools after Cowork verification.
    """

    @staticmethod
    def _confirm_action(envelope: dict, label: str) -> dict:
        """Return the inner ``toolCall`` action for the direct-apply rail.

        The direct rail's onClick is a list:
        ``[setState("pending", True), toolCall(...)]``. The leading
        ``setState`` is the in-flight click guard (so a double-click can't
        fire two applies); the toolCall is what we return for assertions.
        """
        buttons = _find_buttons_by_label(envelope, label)
        assert len(buttons) == 1, (
            f"Expected exactly one Button with label {label!r}; found {len(buttons)}."
        )
        on_click = buttons[0].get("onClick") or buttons[0].get("on_click")
        assert isinstance(on_click, list), (
            f"Direct-apply rail onClick should be a [SetState, CallTool] list; "
            f"got {type(on_click).__name__}: {on_click!r}"
        )
        # Click guard must come first: SetState(pending=True) before the
        # CallTool so the button binds locked the moment the click fires.
        assert on_click[0].get("action") == "setState", (
            f"First action must be the pending guard; got {on_click[0]!r}"
        )
        assert on_click[0].get("key") == "pending"
        assert on_click[0].get("value") is True, (
            f"pending guard must set pending=True; got {on_click[0]!r}"
        )
        tool_calls = [a for a in on_click if a.get("action") == "toolCall"]
        assert len(tool_calls) == 1, (
            f"Expected exactly one toolCall in onClick; got {tool_calls!r}"
        )
        return tool_calls[0]

    def test_po_preview_direct_apply_fires_call_tool(self):
        from katana_mcp.tools.foundation.purchase_orders import (
            CreatePurchaseOrderRequest,
            PurchaseOrderItem,
        )

        request = CreatePurchaseOrderRequest(
            supplier_id=2,
            location_id=3,
            order_number="PO-1",
            items=[PurchaseOrderItem(variant_id=10, quantity=1.0, price_per_unit=2.0)],
        )
        app = build_order_preview_ui(
            {
                "id": 1,
                "order_number": "PO-1",
                "supplier_id": 2,
                "location_id": 3,
                "status": "NOT_RECEIVED",
                "warnings": [],
            },
            "Purchase Order",
            confirm_request=request,
            confirm_tool="create_purchase_order",
            direct_apply=True,
        )
        envelope = app.to_json()
        on_click = self._confirm_action(envelope, "Confirm & Create Purchase Order")

        # The direct rail fires CallTool with the apply args (preview=False).
        assert on_click.get("tool") == "create_purchase_order"
        args = on_click.get("arguments") or {}
        assert args.get("preview") is False, (
            f"Direct rail must override preview=False; got {args!r}"
        )
        assert args.get("supplier_id") == 2
        assert args.get("location_id") == 3
        assert args.get("order_number") == "PO-1"

    def test_po_preview_direct_apply_pushes_result_via_update_context(self):
        """on_success chain must include UpdateContext(content=$result).

        This is the load-bearing primitive: the iframe pushes the apply
        result into the agent's context for its next turn, replacing the
        SendMessage round-trip.
        """
        from katana_mcp.tools.foundation.purchase_orders import (
            CreatePurchaseOrderRequest,
            PurchaseOrderItem,
        )

        request = CreatePurchaseOrderRequest(
            supplier_id=2,
            location_id=3,
            order_number="PO-1",
            items=[PurchaseOrderItem(variant_id=10, quantity=1.0, price_per_unit=2.0)],
        )
        app = build_order_preview_ui(
            {
                "id": 1,
                "order_number": "PO-1",
                "supplier_id": 2,
                "location_id": 3,
                "status": "NOT_RECEIVED",
                "warnings": [],
            },
            "Purchase Order",
            confirm_request=request,
            confirm_tool="create_purchase_order",
            direct_apply=True,
        )
        envelope = app.to_json()
        on_click = self._confirm_action(envelope, "Confirm & Create Purchase Order")

        on_success = on_click.get("onSuccess")
        assert isinstance(on_success, list), (
            f"Expected onSuccess to be a list; got {on_success!r}"
        )
        update_contexts = [a for a in on_success if a.get("action") == "updateContext"]
        assert len(update_contexts) == 1, (
            f"Expected exactly one updateContext action; got {update_contexts!r}"
        )
        assert update_contexts[0].get("content") == "{{ $result }}", (
            f"updateContext.content must carry $result reactive ref so the "
            f"agent receives the structured apply response on its next turn; "
            f"got {update_contexts[0]!r}"
        )

        # State morph: applied=True so the iframe flips to a result view in
        # place. result=$result so any inline Rx refs to state.result work.
        set_states = [a for a in on_success if a.get("action") == "setState"]
        keys = {s.get("key") for s in set_states}
        assert "applied" in keys and "result" in keys, (
            f"Expected applied/result state morph; got keys {keys!r}"
        )

    def test_po_preview_direct_apply_handles_error(self):
        """on_error chain must include UpdateContext with the error reason
        plus a toast and an 'error' state morph.
        """
        from katana_mcp.tools.foundation.purchase_orders import (
            CreatePurchaseOrderRequest,
            PurchaseOrderItem,
        )

        request = CreatePurchaseOrderRequest(
            supplier_id=2,
            location_id=3,
            order_number="PO-1",
            items=[PurchaseOrderItem(variant_id=10, quantity=1.0, price_per_unit=2.0)],
        )
        app = build_order_preview_ui(
            {
                "id": 1,
                "order_number": "PO-1",
                "supplier_id": 2,
                "location_id": 3,
                "status": "NOT_RECEIVED",
                "warnings": [],
            },
            "Purchase Order",
            confirm_request=request,
            confirm_tool="create_purchase_order",
            direct_apply=True,
        )
        envelope = app.to_json()
        on_click = self._confirm_action(envelope, "Confirm & Create Purchase Order")

        on_error = on_click.get("onError")
        assert isinstance(on_error, list), (
            f"Expected onError to be a list; got {on_error!r}"
        )
        update_contexts = [a for a in on_error if a.get("action") == "updateContext"]
        assert len(update_contexts) == 1, (
            f"Expected exactly one updateContext on error; got {update_contexts!r}"
        )
        assert "$error" in update_contexts[0].get("content", ""), (
            f"updateContext on error must include the error reason; "
            f"got {update_contexts[0]!r}"
        )
        toasts = [a for a in on_error if a.get("action") == "showToast"]
        assert len(toasts) == 1, f"Expected one error toast; got {toasts!r}"

    def test_po_preview_direct_apply_double_click_is_guarded(self):
        """Confirm button binds ``pending`` so a double-click cannot fire
        two applies. Ensures (1) on_click sets pending=True before
        CallTool, (2) on_success/on_error clear pending=False, and (3) the
        button's disabled expression includes ``pending`` (so the second
        click is dropped while the first is in flight).

        Without this guard a fast double-click on ``create_purchase_order``
        would fire two CallTool requests in parallel and create duplicate
        POs in Katana — there's no idempotency on the API side.
        """
        from katana_mcp.tools.foundation.purchase_orders import (
            CreatePurchaseOrderRequest,
            PurchaseOrderItem,
        )

        request = CreatePurchaseOrderRequest(
            supplier_id=2,
            location_id=3,
            order_number="PO-1",
            items=[PurchaseOrderItem(variant_id=10, quantity=1.0, price_per_unit=2.0)],
        )
        app = build_order_preview_ui(
            {
                "id": 1,
                "order_number": "PO-1",
                "supplier_id": 2,
                "location_id": 3,
                "status": "NOT_RECEIVED",
                "warnings": [],
            },
            "Purchase Order",
            confirm_request=request,
            confirm_tool="create_purchase_order",
            direct_apply=True,
        )
        envelope = app.to_json()

        buttons = _find_buttons_by_label(envelope, "Confirm & Create Purchase Order")
        on_click = buttons[0].get("onClick") or buttons[0].get("on_click")
        # Click chain: [SetState(pending, True), CallTool(...)].
        assert on_click[0].get("action") == "setState"
        assert on_click[0].get("key") == "pending"
        assert on_click[0].get("value") is True

        # Inner CallTool clears pending in both on_success and on_error.
        tool_call = next(a for a in on_click if a.get("action") == "toolCall")
        for chain_name in ("onSuccess", "onError"):
            chain = tool_call.get(chain_name) or []
            pending_clears = [
                a
                for a in chain
                if a.get("action") == "setState"
                and a.get("key") == "pending"
                and a.get("value") is False
            ]
            assert len(pending_clears) == 1, (
                f"{chain_name} must clear pending=False so the buttons unlock "
                f"after the call resolves; got {chain!r}"
            )

        # The button's `disabled` field carries the reactive lockout
        # expression. Assert against that specific field — searching the
        # whole button payload would false-positive because the guard
        # names also appear inside `onClick` actions (e.g.,
        # `setState(key="applied")` in on_success).
        disabled = buttons[0].get("disabled")
        assert isinstance(disabled, str), (
            f"Expected disabled to be a reactive template string; got "
            f"{disabled!r}. Lockout-contract pin lives there."
        )
        # Both the click guard (pending) and the morph guards (applied,
        # error, cancelled) must be in the disabled expression so the
        # button locks the moment any of those states flips.
        for guard in ("pending", "applied", "error", "cancelled"):
            assert guard in disabled, (
                f"Confirm button's `disabled` expression must reference "
                f"state '{guard}' so the button locks when it flips; "
                f"got disabled={disabled!r}"
            )


class TestCancelButtonEmitsCancelMessage:
    """The Cancel button must fire ``setState("cancelled", True)`` plus a
    ``sendMessage("Cancel: do not apply ...")`` so the agent recognizes the
    user's opt-out and moves on. Mirrors the Confirm-button contract above.
    """

    def _assert_cancel_actions(self, on_click: list[dict]) -> None:
        set_states = [a for a in on_click if a.get("action") == "setState"]
        send_messages = [a for a in on_click if a.get("action") == "sendMessage"]
        assert any(
            a.get("key") == "cancelled" and a.get("value") is True for a in set_states
        ), f"Expected setState('cancelled', True) in on_click; got {on_click!r}"
        cancel_msgs = [
            m
            for m in send_messages
            if isinstance(m.get("content"), str)
            and m["content"].startswith("Cancel: do not apply ")
        ]
        assert len(cancel_msgs) == 1, (
            f"Expected exactly one Cancel SendMessage; "
            f"got {[m.get('content') for m in send_messages]!r}"
        )

    def test_order_preview_cancel(self):
        from katana_mcp.tools.foundation.purchase_orders import (
            CreatePurchaseOrderRequest,
            PurchaseOrderItem,
        )

        request = CreatePurchaseOrderRequest(
            supplier_id=2,
            location_id=3,
            order_number="PO-CANCEL-1",
            items=[PurchaseOrderItem(variant_id=10, quantity=1.0, price_per_unit=2.0)],
        )
        app = build_order_preview_ui(
            {"order_number": "PO-CANCEL-1", "warnings": []},
            "Purchase Order",
            confirm_request=request,
            confirm_tool="create_purchase_order",
        )
        on_click = _confirm_button_on_click(app.to_json(), "Cancel")
        self._assert_cancel_actions(on_click)

    def test_fulfill_preview_cancel(self):
        app = build_fulfill_preview_ui(
            {
                "order_id": 9999,
                "order_type": "sales",
                "order_number": "SO-CANCEL-1",
                "status": "IN_PROGRESS",
                "warnings": [],
            }
        )
        on_click = _confirm_button_on_click(app.to_json(), "Cancel")
        self._assert_cancel_actions(on_click)


class TestPreviewCardSeedsPendingState:
    """Every preview card must seed ``pending=False`` and ``cancelled=False``
    in iframe state so the conditional rendering for the "Pending…" /
    "Cancelled" pills (and the buttons' ``disabled="pending or cancelled"``)
    starts in the un-pressed default.
    """

    @staticmethod
    def _assert_seeds_state(envelope: dict, builder: str) -> None:
        state = envelope.get("state") or envelope.get("$prefab", {}).get("state") or {}
        assert state.get("pending") is False, (
            f"{builder}: state.pending must seed to False; got {state!r}"
        )
        assert state.get("cancelled") is False, (
            f"{builder}: state.cancelled must seed to False; got {state!r}"
        )

    def test_order_preview(self):
        from katana_mcp.tools.foundation.purchase_orders import (
            CreatePurchaseOrderRequest,
            PurchaseOrderItem,
        )

        request = CreatePurchaseOrderRequest(
            supplier_id=2,
            location_id=3,
            order_number="PO-STATE-1",
            items=[PurchaseOrderItem(variant_id=10, quantity=1.0, price_per_unit=2.0)],
        )
        app = build_order_preview_ui(
            {"order_number": "PO-STATE-1", "warnings": []},
            "Purchase Order",
            confirm_request=request,
            confirm_tool="create_purchase_order",
        )
        self._assert_seeds_state(app.to_json(), "build_order_preview_ui")

    def test_fulfill_preview(self):
        app = build_fulfill_preview_ui(
            {
                "order_id": 9999,
                "order_type": "sales",
                "order_number": "SO-STATE-1",
                "status": "IN_PROGRESS",
                "warnings": [],
            }
        )
        self._assert_seeds_state(app.to_json(), "build_fulfill_preview_ui")

    def test_receipt_preview(self):
        from katana_mcp.tools.foundation.purchase_orders import (
            ReceiveItemRequest,
            ReceivePurchaseOrderRequest,
        )

        request = ReceivePurchaseOrderRequest(
            order_id=1234,
            items=[ReceiveItemRequest(purchase_order_row_id=10, quantity=1.0)],
        )
        app = build_receipt_ui(
            {
                "order_id": 1234,
                "order_number": "PO-STATE-2",
                "is_preview": True,
                "items_received": 1,
                "status": "NOT_RECEIVED",
                "warnings": [],
            },
            confirm_request=request,
            confirm_tool="receive_purchase_order",
        )
        self._assert_seeds_state(app.to_json(), "build_receipt_ui")

    def test_batch_recipe_preview(self):
        request = _StubRequest()
        app = build_batch_recipe_update_ui(
            {
                "is_preview": True,
                "total_ops": 1,
                "success_count": 0,
                "failed_count": 0,
                "skipped_count": 0,
                "results": [
                    {
                        "op_type": "delete",
                        "manufacturing_order_id": 1,
                        "recipe_row_id": 1,
                        "status": "pending",
                    }
                ],
                "warnings": [],
                "message": "preview",
            },
            confirm_request=request,
            confirm_tool="batch_update_recipes",
        )
        self._assert_seeds_state(app.to_json(), "build_batch_recipe_update_ui")


class TestBuildApplyActionXorInvariant:
    """``_build_apply_action`` requires both ``confirm_tool`` and
    ``confirm_request`` to be set together (or both ``None``); a
    single-arg call is a programmer error.
    """

    @pytest.mark.parametrize(
        "tool, request_obj",
        [
            ("create_purchase_order", None),
            (None, _StubRequest()),
        ],
    )
    def test_partial_inputs_raise_value_error(self, tool, request_obj):
        from katana_mcp.tools.prefab_ui import _build_apply_action

        with pytest.raises(ValueError, match="must be set together"):
            _build_apply_action(tool, request_obj)

    def test_both_none_returns_none(self):
        from katana_mcp.tools.prefab_ui import _build_apply_action

        assert _build_apply_action(None, None) is None

    def test_apply_message_inlines_args_and_overrides_preview(self):
        """The ``Apply: call ...`` SendMessage must inline every request
        field as a literal value and force ``preview=False`` regardless
        of the request's preview value (the user already saw the preview).
        """
        from katana_mcp.tools.foundation.orders import FulfillOrderRequest
        from katana_mcp.tools.prefab_ui import _build_apply_action

        request = FulfillOrderRequest(order_id=42, order_type="sales", preview=True)
        actions = _build_apply_action("fulfill_order", request)
        assert actions is not None
        send_messages = [a for a in actions if hasattr(a, "content")]
        assert len(send_messages) == 1
        text = send_messages[0].content
        assert text.startswith("Apply: call fulfill_order(")
        assert "order_id=42" in text
        assert "order_type='sales'" in text
        # preview is forced to False even though request.preview was True
        assert "preview=False" in text
        assert "preview=True" not in text
        # And ``preview=False`` is the trailing arg regardless of where the
        # field appears in args.items() iteration order — agents read a
        # stable suffix.
        assert text.rstrip(")").endswith(", preview=False"), (
            f"`preview=False` must be the trailing arg; got: {text!r}"
        )

    def test_preview_field_required_in_request(self):
        """A request model without a ``preview`` field is a programmer
        error — the SendMessage would prompt the agent to call the tool
        with an unrecognized argument that fails validation downstream.
        Fail loudly at UI-build time instead.
        """
        from katana_mcp.tools.prefab_ui import _build_apply_action
        from pydantic import BaseModel as _BaseModel

        class _NoPreview(_BaseModel):
            order_id: int = 1

        with pytest.raises(ValueError, match="requires a request model with a"):
            _build_apply_action("some_tool", _NoPreview())


class TestBuildApplyResultUIs:
    """Tests for the generic apply-result builders introduced alongside
    the ADR-0015 rail change. These supplement (not replace) the existing
    per-entity success cards."""

    def test_apply_success_renders_summary_lines(self):
        from katana_mcp.tools.prefab_ui import build_apply_success_ui

        app = build_apply_success_ui(
            title="Sales order #WEB20387 fulfilled",
            summary_lines=[
                "Item: Carbon Rocker v2 (RGRD24LG5AXSTBK) qty 1",
                "Inventory: -1 of variant 33331882",
            ],
            katana_url="https://factory.katanamrp.com/salesorder/43264353",
        )
        envelope = app.to_json()
        # Title appears verbatim somewhere in the rendered card
        text_nodes: list[str] = []

        def collect(o: object) -> None:
            if isinstance(o, dict):
                if isinstance(o.get("content"), str):
                    text_nodes.append(o["content"])
                for v in o.values():
                    collect(v)
            elif isinstance(o, list):
                for v in o:
                    collect(v)

        collect(envelope)
        joined = "\n".join(text_nodes)
        assert "Sales order #WEB20387 fulfilled" in joined
        assert "Carbon Rocker v2" in joined
        assert "Inventory: -1 of variant 33331882" in joined

    def test_apply_error_surfaces_actual_error_message(self):
        """Closes #545 — the actual error string is not swallowed."""
        from katana_mcp.tools.prefab_ui import build_apply_error_ui

        app = build_apply_error_ui(
            operation="Fulfilling sales order #WEB20387",
            error_message="Katana API 422: row 108462734 already shipped",
            hint="Check the SO's current production_status before retrying.",
        )
        envelope = app.to_json()
        text_nodes: list[str] = []

        def collect(o: object) -> None:
            if isinstance(o, dict):
                if isinstance(o.get("content"), str):
                    text_nodes.append(o["content"])
                for v in o.values():
                    collect(v)
            elif isinstance(o, list):
                for v in o:
                    collect(v)

        collect(envelope)
        joined = "\n".join(text_nodes)
        assert "Fulfilling sales order #WEB20387 failed" in joined
        # The actual error string must be visible — the whole point of
        # this builder vs. the static-string toast/SendMessage from the
        # old preview→apply codepath.
        assert "Katana API 422: row 108462734 already shipped" in joined
        assert "Check the SO's current production_status" in joined


def _find_buttons_by_label(tree: object, label: str) -> list[dict]:
    """Walk a Prefab envelope and return every Button node whose label
    matches ``label`` exactly. Used by BLOCK-warning regression tests to
    assert the Confirm button is/isn't rendered.
    """
    found: list[dict] = []
    if isinstance(tree, dict):
        if tree.get("type") == "Button" and tree.get("label") == label:
            found.append(tree)
        for v in tree.values():
            found.extend(_find_buttons_by_label(v, label))
    elif isinstance(tree, list):
        for item in tree:
            found.extend(_find_buttons_by_label(item, label))
    return found


def _has_node_of_type(tree: object, node_type: str) -> bool:
    """Return ``True`` if any node anywhere in the Prefab envelope has
    ``type == node_type``. Used by empty-state tests (#470) to assert
    that DataTable / Slot are or aren't rendered.
    """
    if isinstance(tree, dict):
        if tree.get("type") == node_type:
            return True
        return any(_has_node_of_type(v, node_type) for v in tree.values())
    if isinstance(tree, list):
        return any(_has_node_of_type(item, node_type) for item in tree)
    return False


def _collect_node_content(tree: object, node_type: str) -> list[str]:
    """Walk a Prefab envelope and return every ``content`` string from
    nodes whose ``type`` equals ``node_type``. Used by empty-state tests
    to assert on the actual hint text rendered by ``Muted`` (rather than
    on ``str(envelope)``, which also matches header badges and would
    pass even if the hint regressed).
    """
    found: list[str] = []
    if isinstance(tree, dict):
        if tree.get("type") == node_type and isinstance(tree.get("content"), str):
            found.append(tree["content"])
        for v in tree.values():
            found.extend(_collect_node_content(v, node_type))
    elif isinstance(tree, list):
        for item in tree:
            found.extend(_collect_node_content(item, node_type))
    return found


class TestBlockWarningSuppressesConfirm:
    """Tests asserting that a ``BLOCK:``-prefixed warning string in a
    response causes the corresponding preview UI to render *without* the
    Confirm button — preventing the user from clicking through on a state
    the server has flagged as unsafe (e.g. duplicate-create, already-done).
    """

    def test_order_preview_with_block_warning_omits_confirm_button(self):
        order = {
            "order_number": "MO-1",
            "status": "PREVIEW",
            "variant_id": 100,
            "planned_quantity": 5,
            "warnings": [
                "BLOCK: sales_order_row 99 already linked to MO 88",
            ],
        }
        app = build_order_preview_ui(
            order,
            "Manufacturing Order",
            confirm_request=_StubRequest(),
            confirm_tool="create_manufacturing_order",
        )
        envelope = app.to_json()

        confirm_buttons = _find_buttons_by_label(
            envelope, "Confirm & Create Manufacturing Order"
        )
        cancel_buttons = _find_buttons_by_label(envelope, "Cancel")
        assert len(confirm_buttons) == 0, (
            "Confirm button must be suppressed when a BLOCK: warning is "
            f"present; found {len(confirm_buttons)}."
        )
        assert len(cancel_buttons) == 1, (
            "Cancel button must remain so the user can dismiss the preview."
        )

    def test_order_preview_without_block_warning_shows_confirm_button(self):
        order = {
            "order_number": "MO-1",
            "status": "PREVIEW",
            "variant_id": 100,
            "planned_quantity": 5,
            "warnings": ["No production_deadline_date specified"],  # not BLOCK:
        }
        app = build_order_preview_ui(
            order,
            "Manufacturing Order",
            confirm_request=_StubRequest(),
            confirm_tool="create_manufacturing_order",
        )
        envelope = app.to_json()

        confirm_buttons = _find_buttons_by_label(
            envelope, "Confirm & Create Manufacturing Order"
        )
        assert len(confirm_buttons) == 1, (
            "Confirm button must be present when no BLOCK: warning is set."
        )

    def test_fulfill_preview_with_block_warning_omits_confirm_button(self):
        response = {
            "order_type": "sales",
            "order_number": "SO-1",
            "order_id": 42,
            "status": "DELIVERED",
            "warnings": [
                "BLOCK: Sales order SO-1 is already DELIVERED.",
            ],
        }
        app = build_fulfill_preview_ui(response)
        envelope = app.to_json()

        confirm_buttons = _find_buttons_by_label(envelope, "Confirm Fulfillment")
        assert len(confirm_buttons) == 0, (
            "Confirm Fulfillment button must be suppressed on BLOCK warning."
        )

    def test_receipt_ui_with_block_warning_omits_confirm_button(self):
        from katana_mcp.tools.foundation.purchase_orders import (
            ReceiveItemRequest,
            ReceivePurchaseOrderRequest,
        )

        response = {
            "order_number": "PO-1",
            "order_id": 1,
            "is_preview": True,
            "items_received": 5,
            "status": "RECEIVED",
            "warnings": [
                "BLOCK: Purchase order PO-1 is already RECEIVED.",
            ],
        }
        request = ReceivePurchaseOrderRequest(
            order_id=1,
            items=[ReceiveItemRequest(purchase_order_row_id=10, quantity=1.0)],
        )
        app = build_receipt_ui(
            response,
            confirm_request=request,
            confirm_tool="receive_purchase_order",
        )
        envelope = app.to_json()

        confirm_buttons = _find_buttons_by_label(envelope, "Confirm Receipt")
        assert len(confirm_buttons) == 0, (
            "Confirm Receipt button must be suppressed on BLOCK warning."
        )

    def test_block_prefix_is_stripped_from_rendered_badge_labels(self):
        """The literal ``BLOCK:`` prefix must not appear in any Badge label —
        builders strip it so the warning reads naturally to the user.

        (The full warning string still passes through the iframe ``state``
        dict so client-side templates can read it; we only care about the
        rendered Badge text.)
        """
        order = {
            "order_number": "MO-1",
            "warnings": ["BLOCK: this is the diagnostic message"],
        }
        app = build_order_preview_ui(
            order,
            "Manufacturing Order",
            confirm_request=_StubRequest(),
            confirm_tool="create_manufacturing_order",
        )

        def collect_badge_labels(tree: object, out: list[str]) -> None:
            if isinstance(tree, dict):
                if tree.get("type") == "Badge":
                    label = tree.get("label")
                    if isinstance(label, str):
                        out.append(label)
                for v in tree.values():
                    collect_badge_labels(v, out)
            elif isinstance(tree, list):
                for item in tree:
                    collect_badge_labels(item, out)

        labels: list[str] = []
        collect_badge_labels(app.to_json(), labels)

        diagnostic_label = next(
            (lbl for lbl in labels if "diagnostic message" in lbl), None
        )
        assert diagnostic_label is not None, (
            "Diagnostic message must be rendered as a Badge label."
        )
        assert not diagnostic_label.startswith("BLOCK:"), (
            f"Badge label still has literal BLOCK: prefix: {diagnostic_label!r}"
        )


class _ModifyStubRequest(BaseModel):
    """Stub for ``ConfirmableRequest`` used by modification-card tests.

    Mirrors the load-bearing fields ``_build_apply_action_direct`` reads
    (``id``, ``preview``) without pulling a real entity request shape into
    these unit tests.
    """

    id: int = 1
    preview: bool = True


def _modification_preview_response(
    *,
    actions: list[dict] | None = None,
    legacy_changes: list[dict] | None = None,
    warnings: list[str] | None = None,
    katana_url: str | None = None,
) -> dict:
    """Build a minimal preview-shaped ``ModificationResponse`` dict."""
    return {
        "entity_type": "product",
        "entity_id": 17058420,
        "is_preview": True,
        "operation": "" if actions is not None else "update",
        "changes": legacy_changes or [],
        "actions": actions or [],
        "prior_state": None,
        "warnings": warnings or [],
        "next_actions": ["Review the planned actions", "Set preview=false to apply"],
        "katana_url": katana_url,
        "message": "Preview: 2 action(s) planned",
    }


class TestBuildModificationPreviewUI:
    """Preview card for ``modify_*`` / ``delete_*`` / ``correct_*`` tools.

    The card must render a per-action diff DataTable and a Confirm button
    on the direct-apply rail (Confirm fires ``tools/call`` directly + the
    iframe pushes the result via ``ui/update-model-context``).
    """

    def test_basic_two_action_preview_renders_envelope(self):
        response = _modification_preview_response(
            actions=[
                {
                    "operation": "update_header",
                    "target_id": 17058420,
                    "changes": [
                        {
                            "field": "name",
                            "old": "Old Name",
                            "new": "New Name",
                            "is_added": False,
                            "is_unchanged": False,
                            "is_unknown_prior": False,
                        }
                    ],
                    "succeeded": None,
                    "error": None,
                    "verified": None,
                    "actual_after": None,
                },
                {
                    "operation": "update_variant",
                    "target_id": 40371805,
                    "changes": [
                        {
                            "field": "internal_barcode",
                            "old": None,
                            "new": "LD0739",
                            "is_added": False,
                            "is_unchanged": False,
                            "is_unknown_prior": True,
                        }
                    ],
                    "succeeded": None,
                    "error": None,
                    "verified": None,
                    "actual_after": None,
                },
            ],
        )
        app = build_modification_preview_ui(
            response,
            confirm_request=_ModifyStubRequest(id=17058420, preview=True),
            confirm_tool="modify_item",
        )
        _assert_valid_prefab(app)

    def test_confirm_button_uses_direct_apply_call_tool(self):
        """Confirm wires CallTool(modify_item, ..., preview=False)."""
        response = _modification_preview_response(
            actions=[
                {
                    "operation": "update_header",
                    "target_id": 1,
                    "changes": [
                        {
                            "field": "name",
                            "old": "x",
                            "new": "y",
                            "is_added": False,
                            "is_unchanged": False,
                            "is_unknown_prior": False,
                        }
                    ],
                    "succeeded": None,
                    "error": None,
                    "verified": None,
                    "actual_after": None,
                }
            ],
        )
        app = build_modification_preview_ui(
            response,
            confirm_request=_ModifyStubRequest(id=1, preview=True),
            confirm_tool="modify_item",
        )
        envelope = app.to_json()

        # Find the CallTool action — it's nested under a Button's onClick.
        def find_call_tool(tree: object) -> dict | None:
            if isinstance(tree, dict):
                if tree.get("action") == "toolCall":
                    return tree
                for v in tree.values():
                    found = find_call_tool(v)
                    if found is not None:
                        return found
            elif isinstance(tree, list):
                for v in tree:
                    found = find_call_tool(v)
                    if found is not None:
                        return found
            return None

        call_tool = find_call_tool(envelope)
        assert call_tool is not None, "Confirm button must wire a CallTool action"
        assert call_tool["tool"] == "modify_item"
        assert call_tool["arguments"]["preview"] is False, (
            "CallTool arguments must flip preview=False so the direct-apply "
            "fires the apply branch."
        )

    def test_block_warning_suppresses_confirm_button(self):
        """A ``BLOCK:``-prefixed warning must drop the Confirm button (only
        Cancel remains), matching the shape used by the other preview cards.
        """
        response = _modification_preview_response(
            actions=[
                {
                    "operation": "delete",
                    "target_id": 1,
                    "changes": [],
                    "succeeded": None,
                    "error": None,
                    "verified": None,
                    "actual_after": None,
                }
            ],
            warnings=["BLOCK: cannot proceed — already deleted"],
        )
        app = build_modification_preview_ui(
            response,
            confirm_request=_ModifyStubRequest(),
            confirm_tool="delete_item",
        )
        envelope = app.to_json()
        confirm = _find_buttons_by_label(envelope, "Confirm Changes")
        confirm_n = _find_buttons_by_label(envelope, "Confirm 1 action(s)")
        assert len(confirm) + len(confirm_n) == 0, (
            "Confirm button must be suppressed when a BLOCK: warning is set."
        )
        cancel = _find_buttons_by_label(envelope, "Cancel")
        assert len(cancel) == 1, "Cancel button must remain on BLOCK warning."

    def test_legacy_single_action_shape_renders_diff_table(self):
        """Tools that still emit the legacy single-action shape (top-level
        ``operation`` + ``changes``, empty ``actions``) must still get a
        diff table rendered."""
        response = _modification_preview_response(
            actions=[],
            legacy_changes=[
                {
                    "field": "status",
                    "old": "DRAFT",
                    "new": "RECEIVED",
                    "is_added": False,
                    "is_unchanged": False,
                    "is_unknown_prior": False,
                }
            ],
        )
        app = build_modification_preview_ui(
            response,
            confirm_request=_ModifyStubRequest(),
            confirm_tool="modify_purchase_order",
        )
        envelope = app.to_json()
        assert _has_node_of_type(envelope, "DataTable"), (
            "Legacy single-action shape must still render a diff DataTable."
        )

    def test_title_verb_derives_from_tool_name(self):
        """``modify_item`` → "Modify", ``delete_item`` → "Delete",
        ``correct_purchase_order`` → "Correct" — closes Copilot review
        finding that the title was hard-coded as "Modify".
        """
        response = _modification_preview_response(
            actions=[
                {
                    "operation": "delete",
                    "target_id": 1,
                    "changes": [],
                    "succeeded": None,
                    "error": None,
                    "verified": None,
                    "actual_after": None,
                }
            ],
        )
        app = build_modification_preview_ui(
            response,
            confirm_request=_ModifyStubRequest(),
            confirm_tool="delete_item",
        )
        envelope = app.to_json()
        titles: list[str] = []

        def collect_titles(o: object) -> None:
            if isinstance(o, dict):
                if o.get("type") == "CardTitle" and isinstance(o.get("content"), str):
                    titles.append(o["content"])
                for v in o.values():
                    collect_titles(v)
            elif isinstance(o, list):
                for v in o:
                    collect_titles(v)

        collect_titles(envelope)
        assert any(t.startswith("Delete ") for t in titles), (
            f"delete_item card title must start with 'Delete'; got {titles!r}"
        )

    def test_title_action_count_suffix_uses_n_actions(self):
        """The action-count suffix must be present whenever there's at
        least one planned action, including the legacy single-action
        shape (where ``actions`` is empty but ``changes`` is populated).
        Closes Copilot review finding.
        """
        response = _modification_preview_response(
            actions=[],
            legacy_changes=[
                {
                    "field": "status",
                    "old": "DRAFT",
                    "new": "RECEIVED",
                    "is_added": False,
                    "is_unchanged": False,
                    "is_unknown_prior": False,
                }
            ],
        )
        app = build_modification_preview_ui(
            response,
            confirm_request=_ModifyStubRequest(),
            confirm_tool="modify_purchase_order",
        )
        envelope = app.to_json()
        titles: list[str] = []

        def collect_titles(o: object) -> None:
            if isinstance(o, dict):
                if o.get("type") == "CardTitle" and isinstance(o.get("content"), str):
                    titles.append(o["content"])
                for v in o.values():
                    collect_titles(v)
            elif isinstance(o, list):
                for v in o:
                    collect_titles(v)

        collect_titles(envelope)
        assert any("1 action(s)" in t for t in titles), (
            f"Legacy single-action title must include the count suffix; got {titles!r}"
        )

    def test_twelve_action_mixed_plan_renders_single_state_bound_table(self):
        """Reproduces #629: 12-action mixed plans (6 adds + 6 deletes)
        previously emitted N separate state-bound DataTables, blowing the
        renderer. The fix is one DataTable bound to ``state.plan_actions``.
        """
        actions = []
        for i in range(6):
            actions.append(
                {
                    "operation": "add_recipe_row",
                    "target_id": None,
                    "changes": [
                        {
                            "field": "variant_id",
                            "old": None,
                            "new": 40000000 + i,
                            "is_added": True,
                            "is_unchanged": False,
                            "is_unknown_prior": False,
                        },
                        {
                            "field": "planned_quantity_per_unit",
                            "old": None,
                            "new": 1,
                            "is_added": True,
                            "is_unchanged": False,
                            "is_unknown_prior": False,
                        },
                        {
                            "field": "notes",
                            "old": None,
                            "new": f"AM swap {i}: notes with (parens) and #{i}",
                            "is_added": True,
                            "is_unchanged": False,
                            "is_unknown_prior": False,
                        },
                    ],
                    "succeeded": None,
                    "error": None,
                    "verified": None,
                    "actual_after": None,
                }
            )
        for i in range(6):
            actions.append(
                {
                    "operation": "delete_recipe_row",
                    "target_id": 97411400 + i,
                    "changes": [],
                    "succeeded": None,
                    "error": None,
                    "verified": None,
                    "actual_after": None,
                }
            )
        response = _modification_preview_response(actions=actions)
        app = build_modification_preview_ui(
            response,
            confirm_request=_ModifyStubRequest(id=16467730, preview=True),
            confirm_tool="modify_manufacturing_order",
        )
        envelope = app.to_json()

        # Sanity: full envelope serializes and bindings resolve.
        _assert_valid_prefab(app)

        # Exactly one DataTable, bound to plan_actions via mustache template.
        # Bare-string state references crash the JS renderer with
        # "t.some is not a function" — discovered via headless apps_dev tests.
        tables = [
            n
            for n in _walk_view_tree(envelope.get("view"))
            if n.get("type") == "DataTable"
        ]
        assert len(tables) == 1, f"expected 1 DataTable, got {len(tables)}"
        assert tables[0]["rows"] == "{{ plan_actions }}"

        # plan_actions has 12 rows, all PLANNED.
        plan_rows = envelope["state"]["plan_actions"]
        assert len(plan_rows) == 12
        assert [r["index"] for r in plan_rows] == list(range(1, 13))
        assert all(r["status_label"] == "PLANNED" for r in plan_rows)

        # Adds have target_label "—", deletes have "#<id>".
        for r in plan_rows[:6]:
            assert r["target_label"] == "—"
            assert "field(s) set" in r["summary"]
        for r in plan_rows[6:]:
            assert r["target_label"].startswith("#")
            assert r["summary"] == "deleted"

    def test_apply_button_pushes_result_actions_into_state(self):
        """The Confirm button's CallTool on_success chain must SetState
        ``plan_actions`` to ``$result.actions`` so each row's status_label
        ticks live from PLANNED → APPLIED/FAILED on apply.
        """
        response = _modification_preview_response(
            actions=[
                {
                    "operation": "update_header",
                    "target_id": 1,
                    "changes": [],
                    "succeeded": None,
                    "error": None,
                    "verified": None,
                    "actual_after": None,
                }
            ],
        )
        app = build_modification_preview_ui(
            response,
            confirm_request=_ModifyStubRequest(),
            confirm_tool="modify_item",
        )
        envelope = app.to_json()

        # Find the CallTool action and inspect its on_success chain.
        # toolCall actions are nested under Button.on_click (not Component
        # children), so search the full envelope tree.
        def find_action(o: object, action_name: str) -> dict[str, Any] | None:
            if isinstance(o, dict):
                if o.get("action") == action_name:
                    return o
                for v in o.values():
                    found = find_action(v, action_name)
                    if found is not None:
                        return found
            elif isinstance(o, list):
                for v in o:
                    found = find_action(v, action_name)
                    if found is not None:
                        return found
            return None

        call_tool = find_action(envelope, "toolCall")
        assert call_tool is not None
        # The wire field is camelCase via Pydantic alias="onSuccess".
        on_success = call_tool.get("onSuccess") or call_tool.get("on_success") or []
        # Must include a setState targeting plan_actions with $result.actions.
        plan_action_set = next(
            (
                a
                for a in on_success
                if isinstance(a, dict)
                and a.get("action") == "setState"
                and a.get("key") == "plan_actions"
            ),
            None,
        )
        assert plan_action_set is not None, (
            f"on_success must SetState('plan_actions', RESULT.actions) for "
            f"live-tick; got {on_success!r}"
        )
        # The value should be an Rx reference resolving to $result.actions.
        # Rx serializes via str() to "{{ key }}".
        value = plan_action_set.get("value")
        assert isinstance(value, str) and "$result.actions" in value, (
            f"plan_actions value must reference $result.actions; got {value!r}"
        )


class TestBuildModificationResultUI:
    """Result card for an applied (non-preview) ModificationResponse."""

    def _response(self, actions: list[dict]) -> dict:
        return {
            "entity_type": "purchase_order",
            "entity_id": 99,
            "is_preview": False,
            "operation": "",
            "changes": [],
            "actions": actions,
            "prior_state": None,
            "warnings": [],
            "next_actions": [],
            "katana_url": "https://factory.katanamrp.com/purchaseorder/99",
            "message": "Applied 2 action(s)",
        }

    def test_all_succeeded_renders_applied_status(self):
        response = self._response(
            [
                {
                    "operation": "update_header",
                    "target_id": 99,
                    "changes": [
                        {
                            "field": "status",
                            "old": "DRAFT",
                            "new": "OPEN",
                            "is_added": False,
                            "is_unchanged": False,
                            "is_unknown_prior": False,
                        }
                    ],
                    "succeeded": True,
                    "error": None,
                    "verified": True,
                    "actual_after": None,
                }
            ]
        )
        app = build_modification_result_ui(response)
        envelope = app.to_json()
        labels: list[str] = []

        def collect_badges(o: object) -> None:
            if isinstance(o, dict):
                if o.get("type") == "Badge" and isinstance(o.get("label"), str):
                    labels.append(o["label"])
                for v in o.values():
                    collect_badges(v)
            elif isinstance(o, list):
                for v in o:
                    collect_badges(v)

        collect_badges(envelope)
        assert "APPLIED" in labels, (
            f"Top-level status badge must read APPLIED on full success; got {labels!r}"
        )

    def test_partial_failure_marks_overall_partial_failure(self):
        response = self._response(
            [
                {
                    "operation": "update_header",
                    "target_id": 99,
                    "changes": [],
                    "succeeded": True,
                    "error": None,
                    "verified": None,
                    "actual_after": None,
                },
                {
                    "operation": "update_row",
                    "target_id": 1234,
                    "changes": [],
                    "succeeded": False,
                    "error": "422 row already shipped",
                    "verified": None,
                    "actual_after": None,
                },
            ]
        )
        app = build_modification_result_ui(response)
        envelope = app.to_json()
        labels: list[str] = []

        def collect_badges(o: object) -> None:
            if isinstance(o, dict):
                if o.get("type") == "Badge" and isinstance(o.get("label"), str):
                    labels.append(o["label"])
                for v in o.values():
                    collect_badges(v)
            elif isinstance(o, list):
                for v in o:
                    collect_badges(v)

        collect_badges(envelope)
        assert "PARTIAL FAILURE" in labels, (
            f"Mixed succeed/fail must surface PARTIAL FAILURE; got {labels!r}"
        )
        # Per-action FAILED status must surface in the row data (status_label
        # column of the plan_actions DataTable). After the live-tick redesign
        # (#629), per-action status lives in the table cells, not in Badges.
        plan_rows = envelope["state"]["plan_actions"]
        statuses = [r["status_label"] for r in plan_rows]
        assert "APPLIED" in statuses, f"expected APPLIED in {statuses!r}"
        assert "FAILED" in statuses, f"expected FAILED in {statuses!r}"

    def test_view_in_katana_button_present_when_url_set(self):
        response = self._response(
            [
                {
                    "operation": "update_header",
                    "target_id": 99,
                    "changes": [],
                    "succeeded": True,
                    "error": None,
                    "verified": None,
                    "actual_after": None,
                }
            ]
        )
        app = build_modification_result_ui(response)
        envelope = app.to_json()
        assert len(_find_buttons_by_label(envelope, "View in Katana")) == 1

    def test_no_katana_url_drops_view_button(self):
        response = self._response(
            [
                {
                    "operation": "delete",
                    "target_id": 99,
                    "changes": [],
                    "succeeded": True,
                    "error": None,
                    "verified": None,
                    "actual_after": None,
                }
            ]
        )
        response["katana_url"] = None  # delete nulls it
        app = build_modification_result_ui(response)
        envelope = app.to_json()
        assert len(_find_buttons_by_label(envelope, "View in Katana")) == 0

    def test_title_verb_derives_from_tool_name(self):
        """Result-card title verb mirrors the preview-card behavior —
        ``delete_purchase_order`` reads "Purchase Order Delete" rather
        than the misleading "Purchase Order Modification".
        """
        response = self._response(
            [
                {
                    "operation": "delete",
                    "target_id": 99,
                    "changes": [],
                    "succeeded": True,
                    "error": None,
                    "verified": None,
                    "actual_after": None,
                }
            ]
        )
        app = build_modification_result_ui(response, tool_name="delete_purchase_order")
        envelope = app.to_json()
        titles: list[str] = []

        def collect_titles(o: object) -> None:
            if isinstance(o, dict):
                if o.get("type") == "CardTitle" and isinstance(o.get("content"), str):
                    titles.append(o["content"])
                for v in o.values():
                    collect_titles(v)
            elif isinstance(o, list):
                for v in o:
                    collect_titles(v)

        collect_titles(envelope)
        assert any(t.endswith("Delete") for t in titles), (
            f"delete_* result title must end with 'Delete'; got {titles!r}"
        )
