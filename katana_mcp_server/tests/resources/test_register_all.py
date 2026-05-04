"""Smoke test for the resources aggregator (``register_all_resources``)."""

from __future__ import annotations

from unittest.mock import MagicMock

from katana_mcp.resources import register_all_resources


def test_register_all_resources_registers_exactly_the_expected_uris():
    """``register_all_resources`` must delegate to inventory + reference +
    help so that all 10 resource URIs end up registered on the server,
    and **only** those URIs. Asserts equality (not subset) so a future
    bug that re-registers a deprecated resource (e.g. one of the order
    resources removed during the tools-vs-resources split) fails loudly
    instead of slipping through.
    """
    mcp = MagicMock()
    mcp.resource = MagicMock(return_value=lambda fn: fn)
    register_all_resources(mcp)
    registered = {call.kwargs["uri"] for call in mcp.resource.call_args_list}
    expected = {
        # inventory (1)
        "katana://inventory/items",
        # reference (5)
        "katana://suppliers",
        "katana://locations",
        "katana://tax-rates",
        "katana://additional-costs",
        "katana://operators",
        # help (4)
        "katana://help",
        "katana://help/workflows",
        "katana://help/tools",
        "katana://help/resources",
    }
    assert registered == expected, (
        f"Registration set drifted.\n"
        f"  Missing: {sorted(expected - registered)}\n"
        f"  Unexpected: {sorted(registered - expected)}"
    )
