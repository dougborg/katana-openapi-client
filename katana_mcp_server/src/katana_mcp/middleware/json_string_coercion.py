"""Coerce JSON-stringified tool arguments back into native JSON values.

Some MCP harnesses (and some smaller LLMs) JSON-stringify nested argument
values before sending the ``tools/call`` request, producing payloads like
``{"update_rows": "[{...}]"}`` instead of ``{"update_rows": [{...}]}``.
The MCP/JSON-RPC 2.0 spec calls for native JSON values, so FastMCP rejects
the string with a pydantic ``Input should be a valid list
[type=list_type, input_type=str]`` error before tool logic ever runs.

This middleware closes the gap at the FastMCP boundary: it inspects the
called tool's input JSON schema, finds top-level args whose schema declares
a structured type (``array``/``object``/``$ref``) but never accepts
``string``, and ``json.loads()``-decodes any value at those keys that is a
string starting with ``[`` or ``{`` (the only shapes the bug we're fixing
produces — stringified arrays and objects). Strings on schema-declared
string fields are never touched, so a ``description: str`` carrying
``"[hello]"`` keeps its literal value. Strings that don't start with
``[``/``{`` (bare ``"null"``, ``"42"``, etc.) are passed through unchanged
so pydantic emits its normal type-error message rather than us guessing.

Decisions baked in:

- **Schema-aware, not blind.** Without the schema check, a string field
  whose value happens to start with ``[`` would be mis-parsed. The
  middleware never decodes strings on fields where the schema also
  accepts ``string`` (including ambiguous ``type: ["string", "array"]``
  and ``anyOf`` unions containing a string branch).
- **Top-level only.** Every tool in this server registers as
  ``request: Annotated[Model, Unpack()]``, which flattens the model's
  fields into the tool's input schema as top-level properties. The
  observed harness stringification is also one level deep
  (`update_rows` is a string; nested rows inside it are normal). No
  recursion is needed for the cases we're fixing today.
- **Fail-soft.** If JSON parsing fails, the value is left untouched so
  pydantic produces its normal type-error message — we don't mask
  malformed input.
- **No mutation of shared state.** A coerced args dict is built and
  attached to a copied ``MiddlewareContext``; the original message is
  not mutated.
"""

from __future__ import annotations

import json
from typing import Any, override

import mcp.types as mt
from fastmcp.server.middleware.middleware import (
    CallNext,
    Middleware,
    MiddlewareContext,
)
from fastmcp.tools.base import ToolResult

from katana_mcp.logging import get_logger

logger = get_logger(__name__)


def _accepts_string(prop_schema: dict[str, Any]) -> bool:
    """True if the schema's accepted type set includes ``string`` at any branch."""
    t = prop_schema.get("type")
    if t == "string":
        return True
    if isinstance(t, list) and "string" in t:
        return True
    for branch in prop_schema.get("anyOf", []) or []:
        if isinstance(branch, dict) and _accepts_string(branch):
            return True
    for branch in prop_schema.get("oneOf", []) or []:
        if isinstance(branch, dict) and _accepts_string(branch):
            return True
    return False


def _accepts_structured(prop_schema: dict[str, Any]) -> bool:
    """True if the schema's accepted type set includes ``array``, ``object``,
    or a ``$ref`` (refs in pydantic-emitted schemas always point at
    object/model schemas)."""
    if "$ref" in prop_schema:
        return True
    t = prop_schema.get("type")
    if t in ("array", "object"):
        return True
    if isinstance(t, list) and any(x in t for x in ("array", "object")):
        return True
    for branch in prop_schema.get("anyOf", []) or []:
        if isinstance(branch, dict) and _accepts_structured(branch):
            return True
    for branch in prop_schema.get("oneOf", []) or []:
        if isinstance(branch, dict) and _accepts_structured(branch):
            return True
    return False


def _should_decode(prop_schema: dict[str, Any]) -> bool:
    """Decode iff the schema expects structured input AND never accepts a string.

    Ambiguous schemas (``type: ["string", "array"]`` etc.) are left alone:
    pydantic will accept the string branch, which is the safer default.
    """
    return _accepts_structured(prop_schema) and not _accepts_string(prop_schema)


class JsonStringCoercionMiddleware(Middleware):
    """Pre-decode JSON-stringified args at the FastMCP boundary.

    See module docstring for rationale and decisions.
    """

    @override
    async def on_call_tool(
        self,
        context: MiddlewareContext[mt.CallToolRequestParams],
        call_next: CallNext[mt.CallToolRequestParams, ToolResult],
    ) -> ToolResult:
        params = context.message
        args = params.arguments
        if not args or context.fastmcp_context is None:
            return await call_next(context)

        # Cheap pre-check — if no value is a string, there's nothing to
        # decode and we can skip the (async) tool-schema lookup entirely.
        if not any(isinstance(v, str) for v in args.values()):
            return await call_next(context)

        tool = await context.fastmcp_context.fastmcp.get_tool(params.name)
        if tool is None:
            return await call_next(context)

        properties = tool.parameters.get("properties") or {}
        if not properties:
            return await call_next(context)

        coerced: dict[str, Any] = dict(args)
        decoded_keys: list[str] = []
        for key, value in args.items():
            if not isinstance(value, str):
                continue
            prop_schema = properties.get(key)
            if not isinstance(prop_schema, dict) or not _should_decode(prop_schema):
                continue
            stripped = value.strip()
            if not stripped or stripped[0] not in "[{":
                continue
            try:
                coerced[key] = json.loads(stripped)
            except (json.JSONDecodeError, ValueError):
                continue
            decoded_keys.append(key)

        if not decoded_keys:
            return await call_next(context)

        logger.debug(
            "json_string_coercion_applied",
            tool=params.name,
            keys=decoded_keys,
        )
        new_message = params.model_copy(update={"arguments": coerced})
        return await call_next(context.copy(message=new_message))
