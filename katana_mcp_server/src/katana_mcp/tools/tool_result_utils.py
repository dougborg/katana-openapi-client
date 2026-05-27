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
from typing import TYPE_CHECKING, Any, Self

from fastmcp.tools import ToolResult
from pydantic import BaseModel, Field, model_validator

from katana_mcp.logging import get_logger

if TYPE_CHECKING:
    from prefab_ui.app import PrefabApp

logger = get_logger(__name__)


class SoftDeletableResponse(BaseModel):
    """Mixin: derives ``is_deleted: bool`` from ``deleted_at`` after validation.

    Mirrors #526's ``is_archived`` convention so callers don't need to
    parse the timestamp/null shape. Subclasses get the field plumbing
    for free; the ``mode="after"`` validator fires on any construction
    path that runs validation — direct ``__init__``, ``model_validate``,
    ``model_validate_json`` — and sets ``is_deleted=True`` when
    ``deleted_at`` is non-null. ``model_construct`` bypasses validation
    in Pydantic v2 and will **not** derive ``is_deleted``; callers using
    that escape hatch must set the field explicitly.

    Read-side only — Katana exposes deletion via DELETE endpoints, not
    via a writable boolean on update bodies. See
    ``katana_mcp_server/docs/typed_cache/README.md`` "Archive / deleted
    state" for the asymmetry vs. ``is_archived``.
    """

    deleted_at: str | None = None
    is_deleted: bool = False

    @model_validator(mode="after")
    def _derive_is_deleted(self) -> Self:
        # Only derive when ``is_deleted`` wasn't explicitly provided —
        # ``not self.is_deleted`` can't distinguish the default ``False``
        # from an explicit ``is_deleted=False`` and would silently override
        # an explicit ``False`` on a round-tripped payload that also
        # carries a non-null ``deleted_at``. ``model_fields_set`` is the
        # pydantic-native signal for "was this field passed by the
        # caller?" — true only when explicitly provided at construction.
        if self.deleted_at is not None and "is_deleted" not in self.model_fields_set:
            self.is_deleted = True
        return self


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


# Marker prefix on a warning string that signals the preview should refuse to
# expose a Confirm button — the target resource is already in a downstream/final
# state (e.g. a sales-order row already linked to an MO, a PO already received).
# Prefab UI builders strip the prefix before rendering, so the user sees clean
# text; their presence tells the builder to omit the Confirm button.
BLOCK_WARNING_PREFIX = "BLOCK:"


async def resolve_factory_base_currency(catalog: Any) -> str | None:
    """Look up the tenant's ``Factory.base_currency_code`` from the typed cache.

    Katana's factory record is a singleton (``GET /factory``) — the typed
    cache stores it under ``CachedFactory.id == 1`` (synthesized by the
    sync pipeline since the wire shape carries no ``id``). This helper
    centralizes the lookup so callers can plumb the tenant's base
    currency through to UI builders without re-deriving the singleton
    convention each time.

    Returns ``None`` (rather than raising) when the cache is cold,
    unhealthy, or the record is missing — callers should treat it as
    "currency unknown" and fall back to a default (most card builders
    fall back to ``USD`` via :func:`_format_money`). The MCP layer's
    other resolvers (``resolve_entity_name``) follow the same
    best-effort shape; the live API stays the authority for correctness.

    Use this when formatting amounts denominated in the tenant's base
    currency: variant ``sales_price`` / ``purchase_price`` and any
    ``*_in_base_currency`` field on transactional responses. Transaction
    currency (``SalesOrder.currency``, ``PurchaseOrder.currency``) is
    per-record and should be read off the response directly — don't
    confuse the two.
    """
    from katana_public_api_client.models_pydantic._generated import CachedFactory

    try:
        row = await catalog.get_by_id(
            CachedFactory, 1, include_archived=True, include_deleted=True
        )
    except Exception as exc:
        logger.warning(
            "resolve_factory_base_currency: cache lookup failed",
            error=str(exc),
        )
        return None
    if row is None:
        return None
    if isinstance(row, dict):
        return row.get("base_currency_code") or None
    return getattr(row, "base_currency_code", None) or None


async def resolve_entity_name(
    catalog: Any,
    cached_cls: Any,
    entity_id: int,
    *,
    entity_label: str,
) -> tuple[str | None, str | None]:
    """Look up a cached entity by ID and return ``(name, advisory_warning)``.

    Args:
        catalog: ``CatalogQueries`` adapter (typically
            ``services.typed_cache.catalog``).
        cached_cls: ``Cached*`` SQLModel class (e.g., ``CachedSupplier``,
            ``CachedLocation``, ``CachedCustomer``).
        entity_id: Primary-key ID of the entity to look up.
        entity_label: Human-readable label for warnings ("Supplier",
            "Location", ...).

    On hit returns ``(name_or_None, None)``. On miss returns
    ``(None, "<entity_label> with id=N was not found in the cache...")`` —
    an advisory warning **without** the BLOCK prefix because cache lag
    is legitimate (an entity created moments ago in Katana may not yet
    be cached locally). The live API is the authority and will reject
    a genuinely bad ID; this warning just lets the user know we couldn't
    pretty-print the name. Hard duplicate-create gates (already linked,
    already received, source==destination) are the caller's responsibility
    and use ``BLOCK_WARNING_PREFIX`` explicitly.

    Cache *failures* (SQLite errors, locked DB, corruption, etc.) are
    swallowed and converted into the same advisory shape: ``(None, warning)``
    with a message explaining the cache was unhealthy. This keeps name
    resolution best-effort so callers — particularly destructive apply
    paths — can still proceed to the live API even when the cache is
    unavailable. The exception is logged at WARNING for stderr-side
    visibility.

    The lookup passes ``include_archived=True`` / ``include_deleted=True``
    so soft-state entities still resolve to their cached display name —
    this keeps the warning text accurate ("Supplier 'Acme Corp' was
    soft-deleted") even though the apply path lets the live API decide
    whether to accept the request.
    """
    try:
        row = await catalog.get_by_id(
            cached_cls,
            entity_id,
            include_archived=True,
            include_deleted=True,
        )
    except Exception as exc:
        logger.warning(
            "resolve_entity_name: cache lookup failed",
            entity_label=entity_label,
            entity_id=entity_id,
            error=str(exc),
        )
        warning = (
            f"{entity_label} with id={entity_id} could not be looked up "
            f"(cache unavailable: {type(exc).__name__}); the live API "
            f"validates the {entity_label.lower()}."
        )
        return None, warning
    if row is None:
        warning = (
            f"{entity_label} with id={entity_id} was not found in the cache "
            f"(possible cache lag); the live API validates the "
            f"{entity_label.lower()}."
        )
        return None, warning
    # Tolerate both ``Cached*`` rows (attribute access) and dict-shaped
    # legacy fixtures still present in some tests.
    if isinstance(row, dict):
        return row.get("name") or None, None
    return getattr(row, "name", None) or None, None


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


def float_or_none(value: Any) -> float | None:
    """Coerce a wire-format decimal string or number to ``float | None``.

    Returns ``None`` for ``None`` or empty string. Propagates ``ValueError``
    (unparseable string) or ``TypeError`` (non-string, non-numeric input) —
    a malformed wire payload should surface, not silently degrade.
    """
    if value is None or value == "":
        return None
    return float(value)


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


def make_json_result(response: BaseModel) -> ToolResult:
    """Create a ToolResult for a tool with no Prefab UI.

    Use this for tools whose response is purely data — no rich card layer.
    Sibling of ``make_tool_result(response, ui=...)`` (which handles the
    UI-emitting case). Historical context: these tools used to maintain a
    parallel hand-written markdown ``content`` channel plus a
    ``format: Literal["markdown", "json"]`` parameter; both were dropped
    in #567 in favor of JSON content matching the MCP-Apps reference
    servers and structurally eliminating the drift surface (#565).

    ``content`` carries the response as ``indent=2`` JSON for LLM context
    and eyeball-debug. ``structured_content`` carries the same payload as
    a plain dict so programmatic consumers can branch on response shape
    without re-parsing the content text.

    **Shape contrast with ``make_tool_result``**: ``make_tool_result``
    emits the response as compact JSON content (no indent) and puts the
    ``PrefabApp`` envelope in ``structured_content`` for UI-Apps hosts to
    render. The two helpers differ in both the ``content`` formatting
    and the ``structured_content`` payload type, so don't assume the
    helpers are interchangeable when migrating between UI and non-UI
    tools.
    """
    return ToolResult(
        content=response.model_dump_json(indent=2),
        structured_content=response.model_dump(mode="json"),
    )
