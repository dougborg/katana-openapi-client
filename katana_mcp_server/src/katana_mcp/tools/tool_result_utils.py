"""Utilities for creating ToolResult responses for UI-emitting tools.

This module provides ``make_tool_result``, the canonical helper for
converting a Pydantic response + Prefab UI tree into a FastMCP ToolResult.
Tools registered with ``meta=UI_META`` are linked to the auto-registered
``ui://prefab/renderer.html`` resource by fastmcp's ``_expand_prefab_ui_meta``;
the bundled renderer ingests the Prefab wire envelope from
``ui/notifications/tool-result`` notifications and renders the component
tree in a sandboxed iframe (MCP Apps SEP-1865, see #422).
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from fastmcp.tools import ToolResult
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from prefab_ui.app import PrefabApp


# Opt-in marker for Prefab UI rendering. Pass as ``meta=UI_META`` in
# ``mcp.tool(...)`` for every tool that emits a ``PrefabApp`` via
# ``make_tool_result(ui=...)``. fastmcp's ``_maybe_apply_prefab_ui`` hook
# (``fastmcp/server/providers/local_provider/decorators/tools.py``) expands
# this marker into the full ``_meta.ui = {"resourceUri":
# "ui://prefab/renderer.html", "csp": {...}}`` shape required by MCP Apps,
# and lazily registers the Prefab renderer as a ``ui://`` resource the first
# time it sees the marker. Tools missing this marker still return their JSON
# ``content`` payload, but no Prefab UI metadata is attached, so hosts will
# not render the UI and will treat the response as content-only.
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


def naive_utc(dt: datetime | None) -> datetime | None:
    """Normalize a datetime to naive UTC for comparison against the typed cache.

    Cache-backed list tools compare filter datetimes against SQLModel
    ``DateTime`` columns — SQLite's default ``DateTime`` doesn't preserve
    tzinfo, so stored values are naive UTC. Tz-aware inputs are converted to
    UTC and the tzinfo is stripped so SQLAlchemy comparisons don't raise
    ``TypeError: can't compare offset-naive and offset-aware datetimes``.
    Naive inputs are passed through unchanged (assumed UTC already).
    """
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(UTC).replace(tzinfo=None)
    return dt


def parse_request_dates(
    request: BaseModel,
    field_names: Iterable[str],
) -> dict[str, datetime | None]:
    """Parse ISO-8601 date filter fields from a request into naive UTC.

    Cache-backed list tools call their ``_apply_<entity>_filters`` helper
    twice on the paginated path (once for the data SELECT, once for the
    COUNT SELECT); parsing the filter strings once up front avoids doing
    the work twice. Unset fields map to ``None`` in the result.
    """
    result: dict[str, datetime | None] = {}
    for name in field_names:
        raw = getattr(request, name, None)
        result[name] = (
            naive_utc(parse_iso_datetime(raw, name)) if raw is not None else None
        )
    return result


def apply_date_window_filters(
    stmt: Any,
    parsed_dates: dict[str, datetime | None],
    *,
    ge_pairs: dict[str, Any],
    le_pairs: dict[str, Any],
) -> Any:
    """Attach ``>=`` / ``<=`` WHERE clauses for a set of date-range filters.

    ``ge_pairs`` maps ``request_field_name -> sql_column`` for lower bounds
    (``created_after`` → ``CachedX.created_at``, etc.); ``le_pairs`` does
    the same for upper bounds. ``parsed_dates`` is the dict produced by
    :func:`parse_request_dates`; missing keys (i.e. unset filters) are
    skipped without error.
    """
    for name, col in ge_pairs.items():
        dt = parsed_dates.get(name)
        if dt is not None:
            stmt = stmt.where(col >= dt)
    for name, col in le_pairs.items():
        dt = parsed_dates.get(name)
        if dt is not None:
            stmt = stmt.where(col <= dt)
    return stmt


def coerce_enum(value: Any, enum_cls: type[Enum], field_name: str) -> Enum:
    """Coerce a request-level value (str or peer enum) into ``enum_cls``.

    Cache-backed list tools accept caller-side enums like
    ``GetAllManufacturingOrdersStatus`` but query against the cache
    column's own enum (``ManufacturingOrderStatus``). The two share string
    values; this helper round-trips through ``.value`` to translate while
    raising a ``ValueError`` with the valid choices on bad input rather
    than silently returning an empty result set.
    """
    raw = value.value if hasattr(value, "value") else value
    try:
        return enum_cls(raw)
    except ValueError as e:
        valid = ", ".join(s.value for s in enum_cls)
        msg = f"Invalid {field_name} {value!r}. Valid: {valid}"
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


def make_tool_result(response: BaseModel, *, ui: PrefabApp) -> ToolResult:
    """Create a ToolResult for a UI-emitting tool.

    Per MCP Apps spec (SEP-1865): ``content`` IS the model context the LLM
    reads; ``structuredContent`` is for UI binding and is *not* added to
    model context. content carries the response as JSON so the LLM has the
    data the user sees in the iframe; structured_content carries the
    ``PrefabApp``. fastmcp's ``ToolResult.__init__`` converts the PrefabApp
    to the wire envelope, and the host (which has fetched
    ``ui://prefab/renderer.html`` via the tool's ``_meta.ui.resourceUri``)
    routes the envelope to its iframe via ``ui/notifications/tool-result``.

    This matches the data-heavy reference servers in
    ``modelcontextprotocol/ext-apps/examples`` (customer-segmentation,
    system-monitor, etc.) — none use formatted markdown for ``content``.
    """
    return ToolResult(
        content=response.model_dump_json(),
        structured_content=ui,
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
