"""Tests for Prefab UI builder functions.

Verifies that all UI builders can be called without errors and produce
valid PrefabApp instances. This catches constructor signature mismatches
(e.g., positional vs keyword args) that would only surface at runtime.
"""

from __future__ import annotations

import pytest
from katana_mcp.tools.prefab_ui import (
    build_batch_recipe_update_ui,
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
from pydantic import BaseModel


class _StubRequest(BaseModel):
    """Minimal Pydantic stub used by builder tests that don't care about the
    real request shape — only that the builder accepts a BaseModel and emits
    a valid envelope.
    """

    confirm: bool = False


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


class TestCallToolFromRequest:
    """Tests for the call_tool_from_request helper.

    The helper introspects a Pydantic request model and emits a CallTool
    action whose ``arguments`` template every field from iframe state.
    Used to wire the Confirm buttons in preview UIs back to their tool with
    ``confirm=True``, without an LLM round-trip.
    """

    def test_args_template_each_field(self):
        from katana_mcp.tools.foundation.purchase_orders import (
            CreatePurchaseOrderRequest,
        )
        from katana_mcp.tools.prefab_ui import call_tool_from_request

        action = call_tool_from_request(
            "create_purchase_order",
            CreatePurchaseOrderRequest,
            overrides={"confirm": True},
        )
        # Tool name is set
        assert action.tool == "create_purchase_order"
        # Every non-overridden field is templated from state.request
        for fname in CreatePurchaseOrderRequest.model_fields:
            if fname == "confirm":
                continue  # overridden — verified separately
            assert action.arguments[fname] == f"{{{{ request.{fname} }}}}"
        # Override wins over the templated value
        assert action.arguments["confirm"] is True

    def test_state_key_override(self):
        from katana_mcp.tools.foundation.orders import FulfillOrderRequest
        from katana_mcp.tools.prefab_ui import call_tool_from_request

        action = call_tool_from_request(
            "fulfill_order", FulfillOrderRequest, state_key="response"
        )
        assert action.arguments["order_id"] == "{{ response.order_id }}"


def _find_tool_call_actions(tree: object) -> list[dict]:
    """Walk a Prefab envelope dict/list recursively and return every node
    that looks like a ``toolCall`` action (i.e. a dict with ``action ==
    "toolCall"``). Used by the confirm-button regression tests so they can
    assert on the action's actual ``tool``/``arguments`` fields rather than
    on the stringified envelope (which is brittle to ordering/quoting).
    """
    found: list[dict] = []
    if isinstance(tree, dict):
        if tree.get("action") == "toolCall":
            found.append(tree)
        for v in tree.values():
            found.extend(_find_tool_call_actions(v))
    elif isinstance(tree, list):
        for item in tree:
            found.extend(_find_tool_call_actions(item))
    return found


class TestConfirmButtonsUseCallTool:
    """Tests asserting the Prefab confirm buttons emit CallTool actions
    (not SendMessage) so the iframe re-invokes the tool directly with
    ``confirm=True``, instead of round-tripping through the LLM.
    """

    def test_order_preview_confirm_action_emits_calltool(self):
        from katana_mcp.tools.foundation.purchase_orders import (
            CreatePurchaseOrderRequest,
            PurchaseOrderItem,
        )

        order_dict = {
            "id": 1,
            "order_number": "PO-1",
            "supplier_id": 2,
            "location_id": 3,
            "status": "NOT_RECEIVED",
            "entity_type": "regular",
            "is_preview": True,
            "warnings": [],
            "next_actions": [],
            "message": "Preview",
        }
        request = CreatePurchaseOrderRequest(
            supplier_id=2,
            location_id=3,
            order_number="PO-1",
            items=[PurchaseOrderItem(variant_id=10, quantity=1.0, price_per_unit=2.0)],
        )
        app = build_order_preview_ui(
            order_dict,
            "Purchase Order",
            confirm_request=request,
            confirm_tool="create_purchase_order",
        )
        envelope = app.to_json()

        # Walk the envelope's view tree looking for a toolCall action that
        # invokes create_purchase_order with confirm=True. If absent, the
        # migration regressed — the button reverted to SendMessage.
        actions = _find_tool_call_actions(envelope)
        matching = [
            a
            for a in actions
            if a.get("tool") == "create_purchase_order"
            and a.get("arguments", {}).get("confirm") is True
        ]
        assert len(matching) == 1, (
            f"Expected exactly one create_purchase_order toolCall with "
            f"confirm=True; found {len(matching)}. Total toolCall actions "
            f"in envelope: {len(actions)}."
        )


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

        confirm_buttons = _find_buttons_by_label(envelope, "Confirm & Create")
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

        confirm_buttons = _find_buttons_by_label(envelope, "Confirm & Create")
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
