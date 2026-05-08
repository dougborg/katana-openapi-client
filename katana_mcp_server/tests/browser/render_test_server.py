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

from collections.abc import Callable
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
    build_inventory_check_ui,
    build_modification_preview_ui,
    build_modification_result_ui,
    build_search_results_ui,
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
                "location_name": "Brooklyn",
                "location_id": 2,
                "in_stock": 12,
                "committed": 2,
                "available": 10,
                "expected": 40,
            },
        ],
    }
    return build_inventory_check_ui(stock)


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


def _batch_recipe_update_app() -> PrefabApp:
    """build_batch_recipe_update_ui with 5 sub-ops — exercises rows='{{ rows }}'."""
    response = {
        "is_preview": True,
        "message": "5 sub-ops planned",
        "warnings": [],
        "results": [
            {
                "group_label": "Replace bolt with nut",
                "sub_op": "delete",
                "sku": f"SKU-OLD-{i}",
                "qty": 1,
                "status": "PENDING",
                "error": None,
            }
            for i in range(5)
        ],
    }
    return build_batch_recipe_update_ui(response)


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
    "inventory_check": _inventory_check_app,
    "verification": _verification_app,
    "batch_recipe_update": _batch_recipe_update_app,
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


if __name__ == "__main__":
    mcp.run(transport="http", port=8765)
