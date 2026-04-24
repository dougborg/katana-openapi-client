"""Utilities for creating ToolResult responses with template rendering.

This module provides helpers for converting Pydantic response models
to FastMCP ToolResult objects with:
- Human-readable markdown content (from templates) for non-Prefab clients
- Machine-readable structured content (from Pydantic model) for programmatic access
- Prefab UI (via structuredContent) for Claude Desktop and other Prefab-capable hosts

When a PrefabApp is provided, it takes priority as structured_content. Claude Desktop
renders the Prefab UI; other clients fall back to markdown content.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING, Any

from fastmcp.tools import ToolResult
from pydantic import BaseModel, Field

from katana_mcp.templates import format_template

if TYPE_CHECKING:
    from prefab_ui.app import PrefabApp


# Opt-in marker for Prefab UI rendering. Pass as ``meta=UI_META`` in
# ``mcp.tool(...)`` for every tool that returns a ``PrefabApp`` via
# ``make_tool_result``. Any tool missing this marker will ship markdown only —
# the UI will be built but silently discarded by the client.
UI_META: dict[str, Any] = {"ui": True}


def enum_to_str(value: Any) -> str | None:
    """Extract the string value from an enum, or return as-is.

    Handles the common case where an attrs model field may be a StrEnum,
    a plain string, or None. Pattern: `enum_to_str(status)` instead of
    `status.value if hasattr(status, "value") else status`.
    """
    if value is None:
        return None
    return value.value if hasattr(value, "value") else str(value)


def iso_or_none(dt: datetime | None) -> str | None:
    """Format a datetime as ISO 8601, or return None.

    Shorthand for `dt.isoformat() if dt else None`.
    """
    return dt.isoformat() if dt else None


def parse_iso_datetime(value: str, field_name: str) -> datetime:
    """Parse an ISO-8601 datetime string, raising ValueError with field context.

    Normalizes trailing ``Z`` / ``z`` (UTC shorthand) to ``+00:00`` before
    parsing — ``datetime.fromisoformat`` didn't accept ``Z`` before Python
    3.11. Raises ``ValueError`` with the field name when input is unparseable
    so caller mistakes surface loudly instead of being silently dropped.

    Callers with optional values should guard ``if value is not None:``
    before calling — this function requires a non-None string so the return
    type stays narrow (``datetime``, not ``datetime | None``).
    """
    normalized = value
    if normalized.endswith(("Z", "z")):
        normalized = normalized[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(normalized)
    except ValueError as e:
        msg = f"Invalid ISO-8601 datetime for {field_name!r}: {value!r}"
        raise ValueError(msg) from e


class PaginationMeta(BaseModel):
    """Pagination metadata extracted from Katana's ``x-pagination`` header.

    Populated on list-tool responses only when the caller requested a
    specific page (i.e. passed ``page=N``). When auto-pagination is used,
    this field is ``None`` because there is no single page to describe.
    """

    total_records: int | None = Field(
        default=None, description="Total records across all pages"
    )
    total_pages: int | None = Field(default=None, description="Total number of pages")
    page: int | None = Field(default=None, description="Current page number (1-based)")
    first_page: bool | None = Field(
        default=None, description="True if this is the first page"
    )
    last_page: bool | None = Field(
        default=None, description="True if this is the last page"
    )


def parse_pagination_header(raw: str | None) -> PaginationMeta | None:
    """Parse Katana's ``x-pagination`` response header into a PaginationMeta.

    Katana returns this as a JSON string with stringy values, e.g.:
    ``{"total_records":"2319","total_pages":"2319","offset":"0","page":"1",
    "first_page":"true","last_page":"false"}``.

    Returns ``None`` when the header is absent or the top-level JSON is
    invalid (non-JSON or not a JSON object). When the header is valid JSON
    but individual fields are missing or malformed, returns a
    ``PaginationMeta`` with those specific fields set to ``None`` rather
    than discarding the whole header.
    """
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except (ValueError, TypeError):
        return None
    if not isinstance(data, dict):
        return None

    def _as_int(val: Any) -> int | None:
        if val is None:
            return None
        try:
            return int(val)
        except (ValueError, TypeError):
            return None

    def _as_bool(val: Any) -> bool | None:
        if isinstance(val, bool):
            return val
        if isinstance(val, str):
            lowered = val.strip().lower()
            if lowered == "true":
                return True
            if lowered == "false":
                return False
        return None

    return PaginationMeta(
        total_records=_as_int(data.get("total_records")),
        total_pages=_as_int(data.get("total_pages")),
        page=_as_int(data.get("page")),
        first_page=_as_bool(data.get("first_page")),
        last_page=_as_bool(data.get("last_page")),
    )


async def none_coro() -> None:
    """Awaitable that resolves to None.

    Use as a placeholder in ``asyncio.gather`` when some slots have no real
    coroutine to await — e.g. enriching a list where some rows are already
    resolved. Avoids per-module re-definitions of the same helper.
    """
    return None


def format_md_table(
    headers: list[str],
    rows: list[list[Any]],
) -> str:
    """Format a simple markdown table from headers and row data.

    Each row cell is rendered via str(); use "—" or "" for missing values.
    Returns an empty string if `rows` is empty.

    Example:
        format_md_table(
            ["Name", "Qty"],
            [["Apple", 3], ["Banana", 5]],
        )
    """
    if not rows:
        return ""
    header_line = "| " + " | ".join(headers) + " |"
    sep_line = "|" + "|".join("---" for _ in headers) + "|"
    body_lines = ["| " + " | ".join(str(cell) for cell in row) + " |" for row in rows]
    return "\n".join([header_line, sep_line, *body_lines])


def make_tool_result(
    response: BaseModel,
    template_name: str,
    *,
    ui: PrefabApp | None = None,
    **template_vars: Any,
) -> ToolResult:
    """Create a ToolResult with markdown content and optional Prefab UI.

    When ``ui`` is provided, the PrefabApp is passed through ``structured_content``
    as-is — FastMCP's ``ToolResult.__init__`` detects it and converts to the wire
    envelope via ``_prefab_to_json``. Combined with ``meta={"ui": True}`` on the
    tool registration, this causes MCP-Apps-capable clients (Claude Desktop) to
    render the Prefab UI. Non-Prefab clients still see the markdown fallback.

    Without ``ui``, ``structured_content`` is the Pydantic response dict so
    programmatic callers can consume fields directly.

    **Contract for programmatic callers:** when ``ui`` is present, ``structured_content``
    is the Prefab wire envelope — it does **not** include the raw response dict
    under a stable key. The previous implementation spliced the Pydantic dump into
    ``structured_content["data"]``; that is gone. Callers who need the response as
    JSON should request it explicitly via the tool's ``format="json"`` parameter
    (introduced in #334), which returns a pure Pydantic JSON dump with no UI
    envelope — the right channel for programmatic access regardless of UI state.

    Args:
        response: Pydantic model response from the tool
        template_name: Name of the markdown template (without .md extension)
        ui: Optional PrefabApp for MCP-Apps rendering
        **template_vars: Variables for template rendering

    Returns:
        ToolResult with markdown content and structured_content
    """
    try:
        markdown = format_template(template_name, **template_vars)
    except (FileNotFoundError, KeyError) as e:
        markdown = (
            f"# Response\n\n```json\n{response.model_dump_json(indent=2)}\n```\n\n"
            f"Template error: {e}"
        )

    return ToolResult(
        content=markdown,
        structured_content=ui if ui is not None else response.model_dump(),
    )


def make_simple_result(
    message: str,
    structured_data: dict[str, Any] | None = None,
) -> ToolResult:
    """Create a simple ToolResult with a message.

    For simple responses where a full template isn't needed.

    Args:
        message: The message to display
        structured_data: Optional structured data dict

    Returns:
        ToolResult with message as content
    """
    return ToolResult(
        content=message,
        structured_content=structured_data or {},
    )
