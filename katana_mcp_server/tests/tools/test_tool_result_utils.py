"""Tests for tool_result_utils — specifically the make_tool_result contract
around structured_content.

make_tool_result is load-bearing for every tool. structured_content must be
the Pydantic model dump regardless of whether ``ui`` is provided — it's the
data Claude (the model) and programmatic callers consume.

The previous implementation passed ``PrefabApp`` instances through to
``ToolResult(structured_content=...)``, which triggered fastmcp's
``_prefab_to_json`` auto-detection and produced a ``$prefab`` v0.2 wire
envelope no MCP client renders. Claude Desktop displayed the envelope as
raw JSON. The fix: ``ui`` is now ignored; ``structured_content`` is always
``response.model_dump()``. Proper interactive UI rendering via the official
MCP Apps spec is tracked in #422.
"""

from __future__ import annotations

from katana_mcp.tools.tool_result_utils import UI_META, make_tool_result
from prefab_ui.app import PrefabApp
from prefab_ui.components import Text
from pydantic import BaseModel


class _StubResponse(BaseModel):
    id: int
    label: str


def _make_response() -> _StubResponse:
    return _StubResponse(id=42, label="hello")


def test_make_tool_result_without_ui_sets_pydantic_dump_as_structured_content():
    response = _make_response()
    result = make_tool_result(response, template_name="nonexistent_template_fallback")

    assert result.structured_content == {"id": 42, "label": "hello"}


def test_make_tool_result_ignores_ui_and_keeps_pydantic_dump_as_structured_content():
    response = _make_response()
    with PrefabApp(state={"label": response.label}) as app:
        Text(content="{{ label }}")

    result = make_tool_result(
        response,
        template_name="nonexistent_template_fallback",
        ui=app,
    )

    # structured_content must be the Pydantic dump — never the Prefab wire
    # envelope (see #422). Exact-equality covers the regression.
    assert result.structured_content == {"id": 42, "label": "hello"}


def test_ui_meta_is_the_opt_in_marker_for_prefab_rendering():
    # Keep UI_META's shape stable — tools pass it by reference to mcp.tool(meta=...).
    # The marker itself is harmless for now; #422 will replace it with
    # ``{"ui": {"resourceUri": "ui://..."}}`` per the MCP Apps spec.
    assert UI_META == {"ui": True}
