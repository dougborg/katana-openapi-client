"""Tests for ``JsonStringCoercionMiddleware``.

Covers the schema-classification helpers, the middleware's behavior on a
range of input shapes (decode/skip/passthrough), and integration with the
real registered MCP server (PO-881 regression).
"""

from __future__ import annotations

from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

import mcp.types as mt
import pytest
from fastmcp.server.middleware.middleware import MiddlewareContext
from katana_mcp.middleware.json_string_coercion import (
    JsonStringCoercionMiddleware,
    _accepts_string,
    _accepts_structured,
    _should_decode,
)

# ---------------------------------------------------------------------------
# Helper unit tests
# ---------------------------------------------------------------------------


class TestAcceptsString:
    def test_bare_string(self):
        assert _accepts_string({"type": "string"}) is True

    def test_bare_array(self):
        assert _accepts_string({"type": "array"}) is False

    def test_string_in_type_list(self):
        assert _accepts_string({"type": ["string", "null"]}) is True

    def test_array_only_in_type_list(self):
        assert _accepts_string({"type": ["array", "null"]}) is False

    def test_string_in_anyof(self):
        assert (
            _accepts_string({"anyOf": [{"type": "string"}, {"type": "null"}]}) is True
        )

    def test_no_string_in_anyof(self):
        assert (
            _accepts_string({"anyOf": [{"type": "array"}, {"type": "null"}]}) is False
        )

    def test_empty_schema(self):
        assert _accepts_string({}) is False


class TestAcceptsStructured:
    def test_array(self):
        assert _accepts_structured({"type": "array"}) is True

    def test_object(self):
        assert _accepts_structured({"type": "object"}) is True

    def test_ref(self):
        assert _accepts_structured({"$ref": "#/$defs/Foo"}) is True

    def test_string(self):
        assert _accepts_structured({"type": "string"}) is False

    def test_array_in_anyof(self):
        assert (
            _accepts_structured({"anyOf": [{"type": "array"}, {"type": "null"}]})
            is True
        )

    def test_ref_in_anyof(self):
        assert (
            _accepts_structured({"anyOf": [{"$ref": "#/$defs/Foo"}, {"type": "null"}]})
            is True
        )


class TestShouldDecode:
    def test_array_only(self):
        assert _should_decode({"type": "array"}) is True

    def test_string_only(self):
        assert _should_decode({"type": "string"}) is False

    def test_array_or_null(self):
        assert _should_decode({"type": ["array", "null"]}) is True

    def test_array_or_string_is_ambiguous(self):
        # Schema accepts both — pydantic will keep the string; don't decode.
        assert _should_decode({"type": ["array", "string"]}) is False

    def test_anyof_array_null(self):
        assert _should_decode({"anyOf": [{"type": "array"}, {"type": "null"}]}) is True

    def test_anyof_array_string_is_ambiguous(self):
        assert (
            _should_decode({"anyOf": [{"type": "array"}, {"type": "string"}]}) is False
        )

    def test_object_only(self):
        assert _should_decode({"type": "object"}) is True

    def test_ref_or_null(self):
        assert (
            _should_decode({"anyOf": [{"$ref": "#/$defs/X"}, {"type": "null"}]}) is True
        )

    def test_integer(self):
        # Scalars don't need JSON decoding.
        assert _should_decode({"type": "integer"}) is False


# ---------------------------------------------------------------------------
# Middleware behavior tests
# ---------------------------------------------------------------------------


def _make_context(
    tool_name: str,
    properties: dict[str, Any],
    args: dict[str, Any] | None,
    *,
    tool_found: bool = True,
) -> MiddlewareContext[mt.CallToolRequestParams]:
    """Build a MiddlewareContext whose mock fastmcp_context returns a tool
    with the given input-schema ``properties``."""
    tool: MagicMock | None
    if tool_found:
        tool = MagicMock()
        tool.parameters = {"properties": properties}
    else:
        tool = None

    fastmcp = MagicMock()
    fastmcp.get_tool = AsyncMock(return_value=tool)

    fastmcp_context = MagicMock()
    fastmcp_context.fastmcp = fastmcp

    msg = mt.CallToolRequestParams(name=tool_name, arguments=args)
    return MiddlewareContext(
        message=msg,
        fastmcp_context=fastmcp_context,
        method="tools/call",
    )


@pytest.mark.asyncio
class TestMiddlewareBehavior:
    async def _run(
        self,
        ctx: MiddlewareContext[mt.CallToolRequestParams],
    ) -> dict[str, Any] | None:
        """Run the middleware and return the args the next handler saw."""
        captured: dict[str, dict[str, Any] | None] = {"args": None}

        async def call_next(c):
            captured["args"] = c.message.arguments
            return MagicMock()

        await JsonStringCoercionMiddleware().on_call_tool(ctx, call_next)
        return captured["args"]

    async def test_decodes_stringified_int_list(self):
        ctx = _make_context(
            "t",
            {"ids": {"type": "array", "items": {"type": "integer"}}},
            {"ids": "[1, 2, 3]"},
        )
        assert await self._run(ctx) == {"ids": [1, 2, 3]}

    async def test_decodes_stringified_list_of_objects(self):
        ctx = _make_context(
            "t",
            {"update_rows": {"type": "array", "items": {"type": "object"}}},
            {"update_rows": '[{"id": 1, "quantity": 2}]'},
        )
        assert await self._run(ctx) == {"update_rows": [{"id": 1, "quantity": 2}]}

    async def test_decodes_stringified_object(self):
        ctx = _make_context(
            "t",
            {"header": {"type": "object"}},
            {"header": '{"foo": "bar"}'},
        )
        assert await self._run(ctx) == {"header": {"foo": "bar"}}

    async def test_decodes_anyof_ref_or_null(self):
        # Mirrors `update_header: SomeModel | None` after pydantic schema gen.
        ctx = _make_context(
            "t",
            {"update_header": {"anyOf": [{"$ref": "#/$defs/Patch"}, {"type": "null"}]}},
            {"update_header": '{"x": 1}'},
        )
        assert await self._run(ctx) == {"update_header": {"x": 1}}

    async def test_protects_string_field(self):
        # A real string field whose value happens to start with `[` must be
        # preserved literally.
        ctx = _make_context(
            "t",
            {"description": {"type": "string"}},
            {"description": "[hello]"},
        )
        assert await self._run(ctx) == {"description": "[hello]"}

    async def test_native_list_passthrough(self):
        ctx = _make_context(
            "t",
            {"ids": {"type": "array"}},
            {"ids": [1, 2, 3]},
        )
        assert await self._run(ctx) == {"ids": [1, 2, 3]}

    async def test_native_dict_passthrough(self):
        ctx = _make_context(
            "t",
            {"header": {"type": "object"}},
            {"header": {"foo": "bar"}},
        )
        assert await self._run(ctx) == {"header": {"foo": "bar"}}

    async def test_non_json_looking_string_left_alone(self):
        # Doesn't start with `[` or `{` — middleware skips, pydantic raises.
        ctx = _make_context(
            "t",
            {"ids": {"type": "array"}},
            {"ids": "not-json"},
        )
        assert await self._run(ctx) == {"ids": "not-json"}

    async def test_malformed_json_left_alone(self):
        # Starts with `[` but unparseable — middleware skips, pydantic raises.
        ctx = _make_context(
            "t",
            {"ids": {"type": "array"}},
            {"ids": "[1, 2,"},
        )
        assert await self._run(ctx) == {"ids": "[1, 2,"}

    async def test_ambiguous_string_or_array_left_alone(self):
        # Schema accepts both; defer to pydantic (which keeps the string).
        ctx = _make_context(
            "t",
            {"x": {"type": ["string", "array"]}},
            {"x": "[1,2]"},
        )
        assert await self._run(ctx) == {"x": "[1,2]"}

    async def test_empty_args_passthrough(self):
        ctx = _make_context("t", {"ids": {"type": "array"}}, {})
        assert await self._run(ctx) == {}

    async def test_no_arguments_passthrough(self):
        ctx = _make_context("t", {"ids": {"type": "array"}}, None)
        assert await self._run(ctx) is None

    async def test_unknown_tool_passthrough(self):
        ctx = _make_context("missing", {}, {"x": "[1]"}, tool_found=False)
        assert await self._run(ctx) == {"x": "[1]"}

    async def test_mixed_decoded_and_native_args(self):
        ctx = _make_context(
            "t",
            {
                "id": {"type": "integer"},
                "ids": {"type": "array"},
                "name": {"type": "string"},
            },
            {"id": 42, "ids": "[1,2]", "name": "[literal]"},
        )
        assert await self._run(ctx) == {
            "id": 42,
            "ids": [1, 2],
            "name": "[literal]",
        }

    async def test_skips_schema_fetch_when_no_string_args(self):
        # Performance guard: when no arg value is a string, there's nothing
        # the middleware could ever decode, so it must short-circuit before
        # the (async) tool-schema lookup.
        ctx = _make_context(
            "t",
            {"ids": {"type": "array"}},
            {"ids": [1, 2, 3], "id": 42, "confirm": True},
        )
        result = await self._run(ctx)
        assert result == {"ids": [1, 2, 3], "id": 42, "confirm": True}
        # ``get_tool`` should never have been awaited. ``fastmcp_context`` is
        # a ``MagicMock`` at runtime; cast lets the test assert through the
        # mock chain without static-typing friction.
        get_tool = cast(
            AsyncMock, cast(MagicMock, ctx.fastmcp_context).fastmcp.get_tool
        )
        get_tool.assert_not_called()


# ---------------------------------------------------------------------------
# Integration tests against the real registered MCP server
# ---------------------------------------------------------------------------


def test_middleware_is_registered():
    """``JsonStringCoercionMiddleware`` is wired into the MCP server."""
    from katana_mcp.server import mcp

    coercion = [
        m for m in mcp.middleware if isinstance(m, JsonStringCoercionMiddleware)
    ]
    assert len(coercion) == 1, (
        f"expected exactly one JsonStringCoercionMiddleware, got {len(coercion)}"
    )


def test_middleware_registered_before_caching():
    """Coercion must run before ResponseCachingMiddleware so cache keys
    reflect normalized args, not stringified ones."""
    from fastmcp.server.middleware.caching import ResponseCachingMiddleware
    from katana_mcp.server import mcp

    type_names = [type(m).__name__ for m in mcp.middleware]
    coercion_idx = next(
        i
        for i, m in enumerate(mcp.middleware)
        if isinstance(m, JsonStringCoercionMiddleware)
    )
    caching_idx = next(
        i
        for i, m in enumerate(mcp.middleware)
        if isinstance(m, ResponseCachingMiddleware)
    )
    assert coercion_idx < caching_idx, (
        f"JsonStringCoercionMiddleware (idx {coercion_idx}) must come before "
        f"ResponseCachingMiddleware (idx {caching_idx}); registration order: "
        f"{type_names}"
    )


@pytest.mark.asyncio
async def test_modify_purchase_order_schema_classifies_correctly():
    """PO-881 regression: the exact fields that failed must be schema-classified
    as "needs decoding" so they get coerced before pydantic validation.
    """
    from katana_mcp.server import mcp

    tool = await mcp.get_tool("modify_purchase_order")
    assert tool is not None, "modify_purchase_order must be registered"

    properties = tool.parameters.get("properties") or {}
    for field in ("update_rows", "delete_row_ids", "update_header"):
        assert field in properties, f"{field!r} missing from tool schema"
        assert _should_decode(properties[field]), (
            f"{field!r} schema {properties[field]!r} should be classified as "
            f"needing JSON-string decoding"
        )


@pytest.mark.asyncio
async def test_get_variant_details_schema_classifies_correctly():
    """The other tool the user reported failing earlier in their session."""
    from katana_mcp.server import mcp

    tool = await mcp.get_tool("get_variant_details")
    assert tool is not None, "get_variant_details must be registered"

    properties = tool.parameters.get("properties") or {}
    # ``variant_ids`` already uses CoercedIntListOpt for CSV support; the
    # middleware adds JSON-string support on top via the schema check.
    assert "variant_ids" in properties
    assert _should_decode(properties["variant_ids"]), (
        f"variant_ids schema {properties['variant_ids']!r} should need decoding"
    )
