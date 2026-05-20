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
    build_inventory_at_ui,
    build_inventory_check_ui,
    build_item_detail_ui,
    build_modification_preview_ui,
    build_modification_result_ui,
    build_search_results_ui,
    build_stock_adjustment_create_ui,
    build_stock_adjustment_delete_ui,
    build_stock_adjustment_update_ui,
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


def _twelve_action_response(*, is_preview: bool, succeeded: bool | None) -> dict:
    """Build a 12-action mixed (6 add + 6 delete) response dict."""
    actions: list[dict] = []
    for i in range(6):
        action = ActionResult(
            index=i + 1,
            operation="add_recipe_row",
            target_id=None,
            changes=[
                FieldChange(
                    field="variant_id", old=None, new=40000000 + i, is_added=True
                ),
                FieldChange(
                    field="planned_quantity_per_unit", old=None, new=1, is_added=True
                ),
                FieldChange(
                    field="notes",
                    old=None,
                    new=f"AM swap {i}: example note with (parens)",
                    is_added=True,
                ),
            ],
            succeeded=succeeded,
            verified=True if succeeded else None,
        )
        actions.append(action.model_dump())
    for i in range(6):
        action = ActionResult(
            index=7 + i,
            operation="delete_recipe_row",
            target_id=97411400 + i,
            changes=[],
            succeeded=succeeded,
        )
        actions.append(action.model_dump())
    return {
        "entity_type": "manufacturing_order",
        "entity_id": 16467730,
        "is_preview": is_preview,
        "operation": "",
        "changes": [],
        "actions": actions,
        "prior_state": None,
        "warnings": [],
        "next_actions": [],
        "katana_url": "https://factory.katanamrp.com/manufacturingorder/16467730",
        "message": (
            "Preview: 12 action(s) planned" if is_preview else "Applied 12 action(s)"
        ),
    }


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


SCENARIOS: dict[str, Callable[[], PrefabApp]] = {
    # The bug-repro: 12 mixed actions on the preview card. Pre-fix this
    # rendered as a blank iframe; post-fix it renders one DataTable with 12
    # rows.
    "modify_mo_12_actions_preview": lambda: build_modification_preview_ui(
        _twelve_action_response(is_preview=True, succeeded=None),
        confirm_request=_StubRequest(),
        confirm_tool="modify_manufacturing_order",
    ),
    # Same 12-action plan after apply — every action APPLIED.
    "modify_mo_12_actions_applied": lambda: build_modification_result_ui(
        _twelve_action_response(is_preview=False, succeeded=True),
        tool_name="modify_manufacturing_order",
    ),
    # Single-action smoke.
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
    "modify_item_single_preview": lambda: build_modification_preview_ui(
        {
            "entity_type": "product",
            "entity_id": 1,
            "is_preview": True,
            "operation": "",
            "changes": [],
            "actions": [
                ActionResult(
                    operation="update_header",
                    target_id=1,
                    changes=[FieldChange(field="name", old="x", new="y")],
                    succeeded=None,
                ).model_dump()
            ],
            "prior_state": None,
            "warnings": [],
            "next_actions": [],
            "katana_url": None,
            "message": "Preview: 1 action(s) planned",
        },
        confirm_request=_StubRequest(),
        confirm_tool="modify_item",
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
    response_dict = _twelve_action_response(
        is_preview=preview, succeeded=None if preview else True
    )
    response = ModificationResponse.model_validate(response_dict)
    ui = build_modification_result_ui(
        response_dict, tool_name="modify_manufacturing_order"
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
