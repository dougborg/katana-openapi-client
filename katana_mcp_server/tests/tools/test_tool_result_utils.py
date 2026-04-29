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

from katana_mcp.tools.tool_result_utils import UI_META, make_tool_result
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
    text = result.content[0].text  # type: ignore[union-attr]
    assert json.loads(text) == {"id": 42, "label": "hello"}


def test_ui_meta_is_the_opt_in_marker_for_prefab_rendering():
    # UI_META is the opt-in marker for fastmcp's _maybe_apply_prefab_ui hook.
    # When fastmcp sees meta={"ui": True} on a tool, it expands it into the
    # full _meta.ui = {"resourceUri": "ui://prefab/renderer.html", "csp": ...}
    # shape required by MCP Apps and registers the renderer resource.
    assert UI_META == {"ui": True}
