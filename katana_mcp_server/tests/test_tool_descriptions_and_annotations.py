"""Regression tests pinning two cross-cutting properties of registered MCP tools:

1. Every tool whose request model has a ``preview`` field includes the
   preview→apply coaching block in its description (closes #544).
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
# Two rails:
#   - SendMessage rail (default) — Confirm fires a ``Apply: call`` chat hint
#     and the agent re-issues. Coaching: ``PREVIEW_APPLY_COACHING``.
#   - Direct-apply rail (``register_preview_tool(direct=True)``) — Confirm
#     fires ``tools/call`` directly and pushes the structured result back via
#     ``ui/update-model-context``. Coaching: ``PREVIEW_APPLY_DIRECT_COACHING``.
#
# ``rebuild_cache`` has a ``preview`` field but renders markdown text rather
# than a Prefab card, so it does not need coaching about button-driven
# Apply: messages.

# Tools currently using the direct-apply rail (per ADR-0016 spike).
DIRECT_APPLY_TOOLS = [
    # Order creates that route through per-entity build_<po|so|mo>_create_ui.
    "create_purchase_order",
    "create_sales_order",
    "create_manufacturing_order",
    # Modification tools — every tool that returns a ModificationResponse
    # via _modification.to_tool_result is on the direct-apply rail.
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
]

# Tools still using the SendMessage rail (default, per ADR-0015). Tracked
# for migration in #633.
SEND_MESSAGE_APPLY_TOOLS = [
    "receive_purchase_order",
    "create_stock_transfer",
    "fulfill_order",
]

PREVIEW_BUTTON_TOOLS = DIRECT_APPLY_TOOLS + SEND_MESSAGE_APPLY_TOOLS


@pytest.mark.parametrize("tool_name", PREVIEW_BUTTON_TOOLS)
def test_preview_button_tool_has_no_renarrate_coaching(
    registered_tools: dict[str, Any], tool_name: str
) -> None:
    """Every preview-button tool's description must include the
    "do not re-narrate" coaching (closes #544). Required for both rails.
    """
    tool = registered_tools[tool_name]
    description = tool.description or ""
    assert "Do NOT re-narrate" in description, (
        f"{tool_name}: missing 'Do NOT re-narrate' coaching — agent will "
        f"re-narrate the preview card and ask for confirmation in chat. "
        f"Wire via with_preview_coaching() in register_tools."
    )


@pytest.mark.parametrize("tool_name", SEND_MESSAGE_APPLY_TOOLS)
def test_send_message_apply_tool_has_apply_call_coaching(
    registered_tools: dict[str, Any], tool_name: str
) -> None:
    """SendMessage-rail tools must coach the agent to recognize the
    ``Apply: call <tool>(...)`` chat hint and re-issue.
    """
    tool = registered_tools[tool_name]
    description = tool.description or ""
    assert "Apply: call" in description, (
        f"{tool_name}: missing 'Apply: call' coaching — agent will not "
        f"recognize the Confirm-button SendMessage and re-issue the call. "
        f"Wire via with_preview_coaching() (direct=False) in register_tools."
    )


@pytest.mark.parametrize("tool_name", DIRECT_APPLY_TOOLS)
def test_direct_apply_tool_has_update_model_context_coaching(
    registered_tools: dict[str, Any], tool_name: str
) -> None:
    """Direct-apply-rail tools must coach the agent that the apply result
    arrives via ``ui/update-model-context``, not via re-issue.
    """
    tool = registered_tools[tool_name]
    description = tool.description or ""
    assert "ui/update-model-context" in description, (
        f"{tool_name}: missing 'ui/update-model-context' coaching — agent "
        f"won't know to expect the apply result via the iframe context push. "
        f"Wire via with_preview_coaching(direct=True) in register_tools."
    )
    assert "Do NOT re-issue" in description, (
        f"{tool_name}: missing 'Do NOT re-issue' coaching — agent may "
        f"incorrectly re-issue after the iframe already applied. "
        f"Wire via with_preview_coaching(direct=True) in register_tools."
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
        "sales_summary",
        "top_selling_variants",
        "inventory_velocity",
    }
    for name in read_only_tools:
        if name not in registered_tools:
            continue
        description = registered_tools[name].description or ""
        assert "Apply: call" not in description, (
            f"{name}: read-only tool unexpectedly carries the preview→apply "
            f"coaching. The coaching should only be on tools that emit a "
            f"Prefab preview card with Confirm/Cancel buttons."
        )
        assert "ui/update-model-context" not in description, (
            f"{name}: read-only tool unexpectedly carries the direct-apply "
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
