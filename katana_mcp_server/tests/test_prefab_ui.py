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

    preview: bool = True


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
