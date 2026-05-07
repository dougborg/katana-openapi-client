"""Smoke test for the resources aggregator (``register_all_resources``)."""

from __future__ import annotations

from unittest.mock import MagicMock

from katana_mcp.resources import register_all_resources


def test_register_all_resources_registers_exactly_the_expected_uris():
    """``register_all_resources`` must delegate to inventory + help so that
    only those URIs end up registered on the server. Asserts equality (not
    subset) so a future bug that re-registers a deprecated resource fails
    loudly instead of slipping through.

    The five reference resources (``katana://suppliers`` /
    ``katana://locations`` / ``katana://tax-rates`` / ``katana://operators``
    / ``katana://additional-costs``) were removed because they dumped every
    cached row as a single-line JSON blob, flooding agent context. Their
    replacements are parameterized search tools (``list_suppliers(query=...)``
    etc.) registered via ``tools/foundation/reference.py``.
    """
    mcp = MagicMock()
    mcp.resource = MagicMock(return_value=lambda fn: fn)
    register_all_resources(mcp)
    registered = {call.kwargs["uri"] for call in mcp.resource.call_args_list}
    expected = {
        # inventory (1)
        "katana://inventory/items",
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


def test_dropped_reference_resources_are_not_registered():
    """The five bulk-list reference resources must stay deregistered.

    Agents rely on ``list_suppliers(query=...)`` etc. for filtered access.
    If a resource gets reintroduced (e.g., a careless revert), this test
    fails before the regression ships.
    """
    mcp = MagicMock()
    mcp.resource = MagicMock(return_value=lambda fn: fn)
    register_all_resources(mcp)
    registered = {call.kwargs["uri"] for call in mcp.resource.call_args_list}
    for dropped in (
        "katana://suppliers",
        "katana://locations",
        "katana://tax-rates",
        "katana://operators",
        "katana://additional-costs",
    ):
        assert dropped not in registered, (
            f"{dropped} reappeared — should have been replaced by parameterized tools."
        )
