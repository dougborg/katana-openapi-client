"""Regression tests pinning two cross-cutting properties of registered MCP tools:

1. Every tool whose request model has a ``preview`` field includes the
   preview→apply coaching block in its description (closes #544). After
   ADR-0021 every preview tool uses the unified direct-apply rail.
2. ``destructiveHint`` annotations follow the policy fixed in ADR-0015
   (#316 housekeeping).

These tests boot the real ``katana_mcp.server.mcp`` instance once via a
module-level fixture; they're slower than the unit tests in
``test_prefab_ui.py`` but cover the registration sites end-to-end.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest


@pytest.fixture(scope="module")
def registered_tools() -> dict[str, Any]:
    """Boot the server once and return ``{tool_name: ToolInfo}``.

    Module-scoped so the (somewhat heavy) FastMCP setup runs only once
    across all parametrized cases.
    """
    from katana_mcp.server import mcp

    tools = asyncio.run(mcp.list_tools())
    return {t.name: t for t in tools}


# ----------------------------------------------------------------------
# Section 1: preview→apply coaching presence
# ----------------------------------------------------------------------

# Tools whose request model has a ``preview: bool`` field AND emit a Prefab
# preview card with Confirm/Cancel buttons. These must include the coaching
# block (``with_preview_coaching``) in their description so the agent
# recognizes the iframe round-trip.
#
# Per ADR-0021, all preview-button tools use the unified direct-apply rail:
# Confirm fires ``tools/call`` directly and pushes the structured result
# back via ``ui/update-model-context``; Cancel pushes an UpdateContext
# notification of the user's opt-out.
#
# ``rebuild_cache`` has a ``preview`` field but renders markdown text rather
# than a Prefab card, so it does not need coaching about button-driven
# Apply behavior.
PREVIEW_BUTTON_TOOLS = [
    # Order creates that route through per-entity build_<po|so|mo>_create_ui.
    "create_purchase_order",
    "create_sales_order",
    "create_manufacturing_order",
    # Modification tools — every tool that returns a ModificationResponse
    # via _modification.to_tool_result is on the apply rail.
    "modify_purchase_order",
    "delete_purchase_order",
    "modify_sales_order",
    "delete_sales_order",
    "modify_manufacturing_order",
    "delete_manufacturing_order",
    "modify_stock_transfer",
    "delete_stock_transfer",
    "modify_item",
    "delete_item",
    "correct_manufacturing_order",
    "correct_sales_order",
    "correct_purchase_order",
    # Stock adjustment family — moved to direct-apply when their Prefab
    # cards landed (closes part of #639).
    "create_stock_adjustment",
    "update_stock_adjustment",
    "delete_stock_adjustment",
    # Tools migrated from the SendMessage rail to the unified apply rail
    # by ADR-0021.
    "receive_purchase_order",
    "create_stock_transfer",
    "fulfill_order",
]


@pytest.mark.parametrize("tool_name", PREVIEW_BUTTON_TOOLS)
def test_preview_button_tool_has_no_renarrate_coaching(
    registered_tools: dict[str, Any], tool_name: str
) -> None:
    """Every preview-button tool's description must include the
    "do not re-narrate" coaching (closes #544). Required for all tools
    that emit a Prefab preview card.
    """
    tool = registered_tools[tool_name]
    description = tool.description or ""
    assert "Do NOT re-narrate" in description, (
        f"{tool_name}: missing 'Do NOT re-narrate' coaching — agent will "
        f"re-narrate the preview card and ask for confirmation in chat. "
        f"Wire via with_preview_coaching() in register_tools."
    )


@pytest.mark.parametrize("tool_name", PREVIEW_BUTTON_TOOLS)
def test_preview_button_tool_has_update_model_context_coaching(
    registered_tools: dict[str, Any], tool_name: str
) -> None:
    """Every preview-button tool must coach the agent that the apply
    result arrives via ``ui/update-model-context`` (post-ADR-0021 unified
    rail), not via agent re-issue.
    """
    tool = registered_tools[tool_name]
    description = tool.description or ""
    assert "ui/update-model-context" in description, (
        f"{tool_name}: missing 'ui/update-model-context' coaching — agent "
        f"won't know to expect the apply result via the iframe context push. "
        f"Wire via with_preview_coaching() in register_tools."
    )
    assert "Do NOT re-issue" in description, (
        f"{tool_name}: missing 'Do NOT re-issue' coaching — agent may "
        f"incorrectly re-issue after the iframe already applied. "
        f"Wire via with_preview_coaching() in register_tools."
    )


def test_read_only_tools_do_not_have_coaching(
    registered_tools: dict[str, Any],
) -> None:
    """Tools with no ``preview`` parameter must NOT carry the coaching —
    the description shouldn't lie about a flow the tool doesn't expose.
    """
    read_only_tools = {
        "search_items",
        "get_item",
        "get_variant_details",
        "check_inventory",
        "list_low_stock_items",
        "verify_order_document",
        "search_customers",
        "get_customer",
        "list_purchase_orders",
        "get_purchase_order",
        "list_sales_orders",
        "get_sales_order",
        "list_manufacturing_orders",
        "get_manufacturing_order",
        "get_manufacturing_order_recipe",
        "list_blocking_ingredients",
        "list_stock_adjustments",
        "list_stock_transfers",
        "get_inventory_movements",
    }
    for name in read_only_tools:
        if name not in registered_tools:
            continue
        description = registered_tools[name].description or ""
        assert "ui/update-model-context" not in description, (
            f"{name}: read-only tool unexpectedly carries the apply-rail "
            f"coaching. The coaching should only be on tools that emit a "
            f"Prefab preview card with Confirm/Cancel buttons."
        )


# ----------------------------------------------------------------------
# Section 2: destructiveHint policy (ADR-0015)
# ----------------------------------------------------------------------

# (tool_name, expected_destructiveHint). Tools that do not appear in this
# table are expected to be either read-only (destructiveHint=False) or
# documented as exceptions.
DESTRUCTIVE_HINT_POLICY = [
    # delete_* — irrecoverable
    ("delete_item", True),
    ("delete_manufacturing_order", True),
    ("delete_purchase_order", True),
    ("delete_sales_order", True),
    ("delete_stock_adjustment", True),
    ("delete_stock_transfer", True),
    # modify_* — overwrites
    ("modify_item", True),
    ("modify_manufacturing_order", True),
    ("modify_purchase_order", True),
    ("modify_sales_order", True),
    ("modify_stock_transfer", True),
    ("update_stock_adjustment", True),
    # create_* — additive, reversible via delete
    ("create_item", False),
    ("create_material", False),
    ("create_product", False),
    ("create_manufacturing_order", False),
    ("create_purchase_order", False),
    ("create_sales_order", False),
    ("create_stock_adjustment", False),
    ("create_stock_transfer", False),
    # Irreversible inventory effects
    ("fulfill_order", True),
    ("receive_purchase_order", True),
    # Closed-record corrections — overwrite shipped data
    ("correct_manufacturing_order", True),
    ("correct_sales_order", True),
    # Cache wipe — destructive locally even though no Katana writes
    ("rebuild_cache", True),
]


@pytest.mark.parametrize("tool_name, expected", DESTRUCTIVE_HINT_POLICY)
def test_destructive_hint_matches_policy(
    registered_tools: dict[str, Any],
    tool_name: str,
    expected: bool,
) -> None:
    """Pin the per-tool ``destructiveHint`` value to ADR-0015's policy
    table. Failures here mean the registration site drifted from the
    documented policy."""
    tool = registered_tools[tool_name]
    annotations = tool.annotations
    assert annotations is not None, f"{tool_name}: no ToolAnnotations set"
    actual = annotations.destructiveHint
    assert actual is expected, (
        f"{tool_name}: destructiveHint policy violation. "
        f"ADR-0015 requires {expected}, got {actual}. "
        f"Update the tool's registration to match policy or update the "
        f"policy table in this test (and the ADR) if the tool's role changed."
    )


# ----------------------------------------------------------------------
# Section 3: removed-tools regression guard
# ----------------------------------------------------------------------

# Tools that were intentionally removed in #757 (commit message:
# "drop derived reporting tools"). Pin their absence so an accidental
# re-registration — e.g. a sloppy revert of `foundation/__init__.py`
# or a sub-issue's import that re-pulls `reporting.py` from history —
# fails this test loudly instead of silently bringing back the derived
# analytics surface that Katana's own forecasting work supersedes.
REMOVED_TOOLS = [
    "inventory_velocity",
    "top_selling_variants",
    "sales_summary",
]


@pytest.mark.parametrize("tool_name", REMOVED_TOOLS)
def test_removed_reporting_tools_stay_unregistered(
    registered_tools: dict[str, Any],
    tool_name: str,
) -> None:
    """Pin the removal of the derived analytics tools (#757).

    These were dropped because Katana is shipping native forecasting
    and replenishment features; surfacing our derived approximations
    alongside their authoritative numbers would confuse anyone
    comparing the two. If you're re-adding one of these, update this
    list and document the reasoning in a follow-up ADR.
    """
    assert tool_name not in registered_tools, (
        f"{tool_name} was intentionally removed in #757 but is registered "
        f"again. If this is a deliberate restoration, update REMOVED_TOOLS "
        f"and add an ADR explaining why we're back in this space."
    )
