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
from katana_mcp.tools._modification import ActionResult, FieldChange
from katana_mcp.tools.prefab_ui import (
    build_modification_preview_ui,
    build_modification_result_ui,
)
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
    envelope, since we just need ``RESULT.actions`` to land in state.
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
    response = _twelve_action_response(
        is_preview=preview, succeeded=None if preview else True
    )
    return ToolResult(
        content="ok",
        structured_content=response,
    )


if __name__ == "__main__":
    mcp.run(transport="http", port=8765)
