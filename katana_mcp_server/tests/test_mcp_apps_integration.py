"""Tests for MCP Apps (SEP-1865) UI integration.

When tools are registered with ``meta=UI_META`` (i.e. ``{"ui": True}``),
fastmcp's ``_maybe_apply_prefab_ui`` hook does two things:

1. Lazily registers the bundled Prefab renderer at ``ui://prefab/renderer.html``
   as a resource with ``mimeType: text/html;profile=mcp-app`` and the CSP
   prefab-ui needs.
2. Expands the marker into the spec-compliant
   ``_meta.ui = {"resourceUri": "ui://prefab/renderer.html", "csp": {...}}``
   shape on the tool definition.

These tests guard the contract: every UI-marked tool should surface the
expanded meta, and the renderer resource should be present in resources/list
exactly once with the correct shape. Hosts advertising the
``io.modelcontextprotocol/ui`` capability use these signals to load the
renderer iframe and route ``ui/notifications/tool-result`` to it. See #422.
"""

from __future__ import annotations

import pytest

# A sample of tools we register with meta=UI_META in foundation/*.py.
# Hard-coded rather than discovered so a regression that drops UI_META from
# a tool surfaces as a missing test, not a silent passing zero.
UI_TOOL_NAMES = {
    "search_items",
    "create_item",
    "get_item",
    "update_item",
    "delete_item",
    "get_variant_details",
    "create_product",
    "create_material",
    "check_inventory",
    "list_low_stock_items",
    "create_sales_order",
    "create_purchase_order",
    "receive_purchase_order",
    "verify_order_document",
    "create_manufacturing_order",
    "batch_update_manufacturing_order_recipes",
    "fulfill_order",
}

PREFAB_RENDERER_URI = "ui://prefab/renderer.html"
MCP_APP_MIME_TYPE = "text/html;profile=mcp-app"


@pytest.fixture(scope="module")
def server_tools():
    """Resolve the registered tools from the configured mcp instance."""
    import asyncio

    from katana_mcp.server import mcp

    return asyncio.run(_collect_tools(mcp))


@pytest.fixture(scope="module")
def server_resources():
    """Resolve the registered resources from the configured mcp instance.

    Returned as a list (not a dict) so duplicate registrations of the same
    URI surface as duplicate entries — a dict comprehension would silently
    coalesce them and let a regression past us.
    """
    import asyncio

    from katana_mcp.server import mcp

    return asyncio.run(_collect_resources(mcp))


async def _collect_tools(mcp):
    return {t.name: t for t in await mcp.list_tools()}


async def _collect_resources(mcp):
    return list(await mcp.list_resources())


def test_prefab_renderer_resource_is_registered(server_resources):
    """The bundled Prefab renderer must surface in resources/list with the
    spec-required URI scheme + MIME type, so a UI-capable host can fetch it.

    Asserts exactly-once registration so a future bug that double-registers
    (e.g., calling _ensure_prefab_renderer outside its idempotency check)
    is caught here.
    """
    matching = [r for r in server_resources if str(r.uri) == PREFAB_RENDERER_URI]
    assert len(matching) == 1, (
        f"Expected exactly one {PREFAB_RENDERER_URI} resource; found "
        f"{len(matching)}. fastmcp's _ensure_prefab_renderer should "
        "register it once, idempotently."
    )

    resource = matching[0]
    assert resource.mime_type == MCP_APP_MIME_TYPE


def test_prefab_renderer_resource_carries_csp_meta(server_resources):
    """The renderer resource carries the CSP prefab-ui needs to load fonts,
    icons etc. from cdn.jsdelivr.net. Without this, hosts enforce the spec's
    restrictive default CSP and the renderer fails to boot in the iframe."""
    resource = next(r for r in server_resources if str(r.uri) == PREFAB_RENDERER_URI)
    assert resource.meta is not None
    ui_meta = resource.meta.get("ui")
    assert isinstance(ui_meta, dict)
    csp = ui_meta.get("csp")
    assert isinstance(csp, dict)
    assert csp.get("resourceDomains"), (
        "Renderer needs at least one resource_domain (cdn.jsdelivr.net) so "
        "the iframe CSP allows prefab's static assets to load."
    )


@pytest.mark.parametrize("tool_name", sorted(UI_TOOL_NAMES))
def test_ui_marked_tools_expose_resource_uri(server_tools, tool_name):
    """fastmcp expands ``meta={'ui': True}`` to the full ``_meta.ui`` shape
    the spec defines. Hosts read ``_meta.ui.resourceUri`` to decide which
    UI resource to load for this tool. If this fails, the tool registration
    likely lost its ``meta=UI_META`` kwarg."""
    assert tool_name in server_tools, (
        f"Tool {tool_name!r} not registered. The UI_TOOL_NAMES list in this "
        "test file should be kept in sync with foundation/*.py registrations."
    )
    tool = server_tools[tool_name]
    assert tool.meta is not None, (
        f"{tool_name} has no meta. Register with meta=UI_META in foundation/*.py."
    )

    ui_meta = tool.meta.get("ui")
    assert isinstance(ui_meta, dict), (
        f"{tool_name}: meta['ui'] = {ui_meta!r}; expected fastmcp to expand "
        "True → {'resourceUri': ..., 'csp': ...}. Check fastmcp version "
        "is >=3.0 (the auto-expansion lives there)."
    )
    assert ui_meta.get("resourceUri") == PREFAB_RENDERER_URI
