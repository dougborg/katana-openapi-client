"""Tests for MCP Apps (SEP-1865) UI integration.

When tools are registered with ``meta=UI_META`` (i.e. ``{"ui": True}``),
fastmcp's prefab synthesis pipeline does two things:

1. Stamps a per-tool ``_meta.ui.resourceUri`` of the form
   ``ui://prefab/tool/<hash>/renderer.html`` on the tool definition,
   where ``<hash>`` is a deterministic 12-char hex digest from the
   app name + tool name (see ``fastmcp.server.providers.addressing``).
2. Synthesizes a matching ``TextResource`` for each prefab tool on
   ``list_resources`` with ``mimeType: text/html;profile=mcp-app`` and
   the CSP prefab-ui needs (one resource per unique hash).

These tests guard the contract: every UI-marked tool surfaces the
expanded meta with a hashed URI, and the synthesized resource is present
in resources/list with the correct shape. Hosts advertising the
``io.modelcontextprotocol/ui`` capability use these signals to load the
renderer iframe and route ``ui/notifications/tool-result`` to it. See #422.
"""

from __future__ import annotations

import re

import pytest

# A sample of tools we register with meta=UI_META in foundation/*.py.
# Hard-coded rather than discovered so a regression that drops UI_META from
# a tool surfaces as a missing test, not a silent passing zero.
UI_TOOL_NAMES = {
    "search_items",
    "create_item",
    "get_item",
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
    "fulfill_order",
}

# Per-tool renderer URI shape from fastmcp's prefab synthesis pipeline.
# Hash is a 12-char hex digest derived from app_name + tool_name.
PREFAB_TOOL_URI_RE = re.compile(r"^ui://prefab/tool/[0-9a-f]{12}/renderer\.html$")
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


def _prefab_resources(resources):
    """Filter the resources list to the synthetic Prefab renderer entries."""
    return [r for r in resources if PREFAB_TOOL_URI_RE.match(str(r.uri))]


def test_prefab_renderer_resources_are_registered(server_resources, server_tools):
    """The synthesized Prefab renderers must surface in resources/list with the
    spec-required URI scheme + MIME type, so a UI-capable host can fetch them.

    fastmcp synthesizes one renderer per unique tool hash (i.e. per
    UI-marked tool). Every UI-marked tool we know about should have a
    matching synthesized resource whose URI equals the tool's own
    ``_meta.ui.resourceUri``. Duplicate URIs would indicate a hash collision
    or double-registration regression.
    """
    prefab_resources = _prefab_resources(server_resources)
    assert prefab_resources, (
        "No prefab renderer resources synthesized — fastmcp's prefab "
        "synthesis pipeline did not run, or no tools were registered with "
        "meta=UI_META."
    )

    seen_uris = {str(r.uri) for r in prefab_resources}
    assert len(seen_uris) == len(prefab_resources), (
        "Duplicate renderer URIs in resources/list — the synthesis pipeline "
        "should de-duplicate on hash."
    )

    for resource in prefab_resources:
        assert resource.mime_type == MCP_APP_MIME_TYPE

    for tool_name in sorted(UI_TOOL_NAMES & set(server_tools)):
        tool_uri = server_tools[tool_name].meta["ui"]["resourceUri"]
        assert tool_uri in seen_uris, (
            f"{tool_name}: tool advertises resourceUri={tool_uri!r}, but no "
            "matching resource in list_resources. The synthesis walk should "
            "produce one resource per prefab tool."
        )


def test_prefab_renderer_resources_carry_csp_meta(server_resources):
    """Each renderer resource carries the CSP prefab-ui needs to load fonts,
    icons etc. from cdn.jsdelivr.net. Without this, hosts enforce the spec's
    restrictive default CSP and the renderer fails to boot in the iframe."""
    prefab_resources = _prefab_resources(server_resources)
    assert prefab_resources, "No prefab renderer resources to inspect."

    # Spot-check the first resource — CSP is built from the same defaults
    # for all of them, so one is representative.
    resource = prefab_resources[0]
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
    the spec defines, stamping a per-tool ``resourceUri``. Hosts read this
    to decide which UI resource to load for the tool. If this fails, the
    tool registration likely lost its ``meta=UI_META`` kwarg."""
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
        "is >=3.2 (the per-tool synthesis lives there)."
    )
    resource_uri = ui_meta.get("resourceUri")
    assert isinstance(resource_uri, str) and PREFAB_TOOL_URI_RE.match(resource_uri), (
        f"{tool_name}: resourceUri = {resource_uri!r}; expected per-tool "
        f"shape {PREFAB_TOOL_URI_RE.pattern}."
    )
