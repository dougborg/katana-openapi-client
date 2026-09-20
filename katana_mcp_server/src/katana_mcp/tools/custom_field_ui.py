"""Confirmation card for custom-field definition changes."""

from typing import Any

from prefab_ui.app import PrefabApp
from prefab_ui.components import (
    Alert,
    AlertDescription,
    AlertTitle,
    Card,
    CardContent,
    Column,
    Text,
)
from prefab_ui.components.control_flow import If
from pydantic import BaseModel

from katana_mcp.tools.prefab_ui import (
    _build_apply_action,
    _build_cancel_action,
    _init_create_card_state,
    _render_preview_footer,
    _render_preview_header,
)


def build_definition_mutation_ui(
    *, response: dict[str, Any], request: BaseModel, tool: str
) -> PrefabApp:
    """Show the planned changes and preserve full data for the model."""
    definition = response.get("definition") or response["payload"]
    title = f"Custom Field {response['operation'].title()}"
    state = _init_create_card_state(response=response)
    state["response"] = response
    apply_action = (
        _build_apply_action(confirm_tool=tool, confirm_request=request)
        if response["is_preview"]
        else None
    )
    with PrefabApp(state=state) as app, Card():
        _render_preview_header(
            title_prefix=title,
            entity="custom_field_definition",
            order_number=definition.get("label", "Custom field"),
            status=None,
            applied_title_suffix="Applied",
            applied_state_label="APPLIED",
        )
        with CardContent(), Column(gap=2):
            for change in response["changes"]:
                Text(content=change)
            options = response["payload"].get("options")
            if options:
                for choice in options["choices"]:
                    status = "retired" if choice.get("deleted") else "active"
                    Text(content=f"{choice['label']} ({status})")
            with If("error"), Alert(variant="destructive"):
                AlertTitle(content="Apply failed")
                AlertDescription(content="{{ error }}")
        _render_preview_footer(
            title_prefix=title,
            block_warnings=[],
            confirm_label=f"Confirm & {response['operation'].title()}",
            apply_action=apply_action,
            cancel_action=_build_cancel_action(
                operation_label="the custom-field change"
            ),
            applied_verb="applied",
        )
    return app
