"""Tests for tool_result_utils — the make_tool_result contract for UI tools.

When a tool emits a Prefab UI via ``make_tool_result(response, ui=app)``,
fastmcp's ``ToolResult.__init__`` converts the ``PrefabApp`` into the Prefab
wire envelope and stuffs it into ``structuredContent``. An MCP Apps host
with the auto-registered ``ui://prefab/renderer.html`` resource ingests it
via ``ui/notifications/tool-result`` (SEP-1865, #422). content carries the
JSON dump of the response so the LLM can act on the data.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest
from katana_mcp.tools.tool_result_utils import (
    UI_META,
    make_tool_result,
    resolve_entity_name,
    resolve_factory_base_currency,
)
from prefab_ui.app import PrefabApp
from prefab_ui.components import Text
from pydantic import BaseModel


class _StubResponse(BaseModel):
    id: int
    label: str


def _make_response() -> _StubResponse:
    return _StubResponse(id=42, label="hello")


def test_make_tool_result_emits_prefab_envelope_as_structured_content():
    response = _make_response()
    with PrefabApp(state={"label": response.label}) as app:
        Text(content="{{ label }}")

    result = make_tool_result(response, ui=app)

    # fastmcp converts the PrefabApp to its wire envelope in ToolResult.__init__.
    # The envelope has "$prefab", "view", and "state" keys; the data lives
    # under .state. The host's auto-registered renderer iframe ingests this
    # via ui/notifications/tool-result.
    assert result.structured_content is not None
    assert "$prefab" in result.structured_content
    assert "view" in result.structured_content
    assert result.structured_content["state"]["label"] == "hello"


def test_make_tool_result_emits_response_json_as_content():
    """Per MCP Apps spec, ``content`` IS the model context (structuredContent
    is for UI binding only). The JSON dump gives the LLM the data without UI
    tree noise."""
    response = _make_response()
    with PrefabApp(state={"label": response.label}) as app:
        Text(content="{{ label }}")

    result = make_tool_result(response, ui=app)

    # content comes back as a list of TextContent blocks; assert the first
    # block parses as the response JSON.
    assert result.content
    first_content = result.content[0]
    from mcp.types import TextContent

    assert isinstance(first_content, TextContent)
    text = first_content.text
    assert json.loads(text) == {"id": 42, "label": "hello"}


def test_ui_meta_is_the_opt_in_marker_for_prefab_rendering():
    # UI_META is the opt-in marker for fastmcp's _maybe_apply_prefab_ui hook.
    # When fastmcp sees meta={"ui": True} on a tool, it expands it into the
    # full _meta.ui = {"resourceUri": "ui://prefab/renderer.html", "csp": ...}
    # shape required by MCP Apps and registers the renderer resource.
    assert UI_META == {"ui": True}


# ============================================================================
# resolve_entity_name — best-effort cache enrichment
# ============================================================================


@pytest.mark.asyncio
async def test_resolve_entity_name_returns_name_on_cache_hit():
    """Hit path: cache returns a row, function returns ``(name, None)``."""
    cache = AsyncMock()
    cache.get_by_id = AsyncMock(return_value={"id": 1, "name": "Acme Supply Co"})

    name, warning = await resolve_entity_name(
        cache, "supplier", 1, entity_label="Supplier"
    )

    assert name == "Acme Supply Co"
    assert warning is None


@pytest.mark.asyncio
async def test_resolve_entity_name_returns_advisory_warning_on_cache_miss():
    """Miss path: cache returns None, function returns ``(None, warning)`` —
    advisory only (no BLOCK prefix), explaining the live API will validate
    the ID on apply."""
    cache = AsyncMock()
    cache.get_by_id = AsyncMock(return_value=None)

    name, warning = await resolve_entity_name(
        cache, "supplier", 9999, entity_label="Supplier"
    )

    assert name is None
    assert warning is not None
    assert "9999" in warning
    assert "not found in the cache" in warning
    # Advisory warnings must NOT carry the BLOCK prefix — that prefix is
    # reserved for hard duplicate-create gates.
    assert not warning.startswith("BLOCK:")


@pytest.mark.asyncio
async def test_resolve_entity_name_swallows_cache_exceptions_so_apply_can_proceed():
    """Cache failure path (#620 Copilot review): a SQLite/IO error inside
    ``cache.get_by_id`` must NOT propagate. Otherwise an unhealthy cache
    aborts destructive apply paths (e.g. ``create_purchase_order``) before
    the live API call. The function returns the same ``(None, warning)``
    advisory shape as a miss, with a message explaining the cache was
    unavailable."""
    cache = AsyncMock()
    cache.get_by_id = AsyncMock(side_effect=RuntimeError("database is locked"))

    name, warning = await resolve_entity_name(
        cache, "supplier", 4001, entity_label="Supplier"
    )

    assert name is None
    assert warning is not None
    assert "4001" in warning
    assert "cache unavailable" in warning
    assert "RuntimeError" in warning
    assert not warning.startswith("BLOCK:")


# ============================================================================
# resolve_factory_base_currency — #751 Factory.base_currency_code plumbing
# ============================================================================


@pytest.mark.asyncio
async def test_resolve_factory_base_currency_returns_code_on_cache_hit():
    """Hit path: the cached ``CachedFactory`` row carries
    ``base_currency_code``; helper returns it verbatim. Verifies the
    singleton-id convention (``id=1``, synthesized by the sync pipeline).
    """
    cache = AsyncMock()

    class _StubFactory:
        base_currency_code = "EUR"

    cache.get_by_id = AsyncMock(return_value=_StubFactory())

    code = await resolve_factory_base_currency(cache)

    assert code == "EUR"
    # Lookup must use the singleton id=1 — not entity_id=0 or some other key.
    args, _kwargs = cache.get_by_id.call_args
    assert args[1] == 1


@pytest.mark.asyncio
async def test_resolve_factory_base_currency_tolerates_dict_shaped_row():
    """Some test fixtures stub the cache with dicts rather than SQLModel
    rows — match :func:`resolve_entity_name`'s dual-shape support so
    callers don't have to refactor their fixtures."""
    cache = AsyncMock()
    cache.get_by_id = AsyncMock(return_value={"id": 1, "base_currency_code": "JPY"})

    code = await resolve_factory_base_currency(cache)

    assert code == "JPY"


@pytest.mark.asyncio
async def test_resolve_factory_base_currency_returns_none_on_cache_miss():
    """Miss path (cold cache, factory record not yet synced): helper
    returns ``None`` so callers fall back to USD in :func:`_format_money`."""
    cache = AsyncMock()
    cache.get_by_id = AsyncMock(return_value=None)

    code = await resolve_factory_base_currency(cache)

    assert code is None


@pytest.mark.asyncio
async def test_resolve_factory_base_currency_swallows_cache_exceptions():
    """Cache failure path: same shape as :func:`resolve_entity_name` —
    swallow the exception and return ``None`` so the variant card render
    doesn't blow up on an unhealthy cache."""
    cache = AsyncMock()
    cache.get_by_id = AsyncMock(side_effect=RuntimeError("database is locked"))

    code = await resolve_factory_base_currency(cache)

    assert code is None


@pytest.mark.asyncio
async def test_resolve_factory_base_currency_returns_none_for_empty_code():
    """Defensive: a cached row with an empty-string ``base_currency_code``
    coalesces to ``None`` so downstream falls back to USD cleanly rather
    than passing ``""`` to Babel (which would render as ``1,500.00``
    sans symbol)."""
    cache = AsyncMock()

    class _EmptyFactory:
        base_currency_code = ""

    cache.get_by_id = AsyncMock(return_value=_EmptyFactory())

    code = await resolve_factory_base_currency(cache)

    assert code is None
