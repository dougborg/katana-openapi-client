"""Reporting and aggregation tools for Katana MCP Server.

Read-only aggregation tools that compute rollups client-side from paginated
sales-order data — and, for inventory velocity, from completed-MO recipe
rows joined out of the typed cache. These exist to replace multi-call
analytical workflows (e.g. "top 20 selling bikes over the last 90 days")
with a single tool call.

Tools:
- top_selling_variants: top-N variants by units or revenue over a date window
- sales_summary: group sales in a window by day/week/month/variant/customer/category
- inventory_velocity: units_sold, avg_daily, stock_on_hand, days_of_cover.
  Accepts either a single ``sku_or_variant_id`` or a batch of up to 100 via
  ``sku_or_variant_ids`` (one row per item). When ``include_mo_consumption``
  is true (default), units consumed as ingredients on completed manufacturing
  orders within the window are added to the velocity figure on top of the
  delivered-SO units, sourced from the ``manufacturing_order_recipe_row``
  cache table.

**Implementation notes:**

- All three tools call ``get_all_sales_orders.asyncio_detailed()`` with
  ``status="DELIVERED"``. The transport's PaginationTransport auto-paginates
  and materializes the full result set in memory — no streaming iterator
  exists today. For very large windows (100k+ SOs) this may be slow; accept
  the cost and flag to the user if they hit it.
- Date filtering is applied server-side via ``created_at_min`` /
  ``created_at_max`` (Katana's supported params on /sales_orders). The window
  semantics are "order was created within [start, end]".
- Variant → category lookup is cached per tool call in a local dict to avoid
  N+1 API calls across many sales-order rows.
- ``inventory_velocity``'s MO-consumption path filters cached MOs to
  ``status=DONE`` with ``done_date`` inside the window before joining recipe
  rows — so partially completed or in-progress MOs don't contribute.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import Iterable
from datetime import UTC, date, datetime, timedelta
from typing import Annotated, Any, Literal

from fastmcp import Context, FastMCP
from fastmcp.tools import ToolResult
from pydantic import BaseModel, ConfigDict, Field

from katana_mcp.cache import EntityType
from katana_mcp.logging import get_logger, observe_tool
from katana_mcp.services import get_services
from katana_mcp.tools.decorators import cache_read
from katana_mcp.tools.list_coercion import CoercedStrIntListOpt
from katana_mcp.tools.tool_result_utils import (
    apply_date_window_filters,
    format_md_table,
    make_simple_result,
)
from katana_mcp.unpack import Unpack, unpack_pydantic_params
from katana_public_api_client.api.inventory import get_all_inventory_point
from katana_public_api_client.api.sales_order import get_all_sales_orders
from katana_public_api_client.domain.converters import unwrap_unset
from katana_public_api_client.utils import unwrap_data

logger = get_logger(__name__)


# ============================================================================
# Shared helpers
# ============================================================================


def _to_datetime(d: date | str) -> datetime:
    """Normalize a ``date`` or ISO-8601 string to a UTC ``datetime``.

    For bare dates we anchor at 00:00 UTC; callers generally pass ``date``
    objects, but Pydantic may hand us a string when the JSON caller sends one.
    """
    if isinstance(d, datetime):
        if d.tzinfo is None:
            return d.replace(tzinfo=UTC)
        return d
    if isinstance(d, date):
        return datetime(d.year, d.month, d.day, tzinfo=UTC)
    # string
    parsed = datetime.fromisoformat(str(d).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed


def _end_of_day(d: date | str) -> datetime:
    """End-of-day UTC for an inclusive upper bound."""
    base = _to_datetime(d)
    # If caller passed a plain date we want inclusive end-of-day; if they
    # passed a datetime we honor the exact timestamp.
    if isinstance(d, datetime) or (isinstance(d, str) and "T" in str(d)):
        return base
    return base + timedelta(days=1) - timedelta(microseconds=1)


async def _fetch_delivered_sales_orders_in_window(
    services: Any,
    start: date | str,
    end: date | str,
    *,
    location_id: int | None = None,
) -> list[Any]:
    """Fetch all DELIVERED sales orders whose ``created_at`` falls in the window.

    Auto-paginates via PaginationTransport. Applies a client-side fallback
    filter in case the server's ``created_at_min`` / ``created_at_max`` are
    not honored on every deployment.
    """
    start_dt = _to_datetime(start)
    end_dt = _end_of_day(end)

    kwargs: dict[str, Any] = {
        "client": services.client,
        "status": "DELIVERED",
        "limit": 250,  # max page size; auto-pagination walks all pages
        "created_at_min": start_dt,
        "created_at_max": end_dt,
    }
    if location_id is not None:
        kwargs["location_id"] = location_id

    response = await get_all_sales_orders.asyncio_detailed(**kwargs)
    attrs_list = unwrap_data(response, default=[])

    # Client-side safety filter — drop rows outside the window in case the
    # server-side filter was ignored by this tenant / endpoint.
    filtered: list[Any] = []
    for so in attrs_list:
        created_at = unwrap_unset(so.created_at, None)
        if created_at is None:
            # No timestamp — we can't verify, include by default.
            filtered.append(so)
            continue
        if isinstance(created_at, datetime):
            ts = created_at if created_at.tzinfo else created_at.replace(tzinfo=UTC)
            if start_dt <= ts <= end_dt:
                filtered.append(so)
        else:
            filtered.append(so)

    return filtered


# Map the variant's normalized "type" string (set by cache_sync._variant_to_cache_dict
# from VariantType) to the (cache entity type, FK field name on the variant dict).
# Services appear to share the product_id FK namespace in Katana's schema.
_PARENT_BY_VARIANT_TYPE: dict[str, tuple[EntityType, str]] = {
    "product": (EntityType.PRODUCT, "product_id"),
    "material": (EntityType.MATERIAL, "material_id"),
    "service": (EntityType.SERVICE, "product_id"),
}

# Cap concurrent ``/inventory`` requests for ``inventory_velocity`` batches.
# Transport-layer rate limiting handles 429s, but a semaphore prevents 100+
# simultaneous requests from saturating the HTTP connection pool.
_STOCK_FETCH_CONCURRENCY = 10


async def _resolve_variant_info(
    services: Any,
    variant_id: int,
    variant_cache: dict[int, dict[str, Any]],
    category_cache: dict[tuple[EntityType, int], str | None],
) -> tuple[dict[str, Any] | None, str | None]:
    """Resolve variant dict and its item-category from the local cache.

    Returns ``(variant_dict, category_name)``. Both may be None if lookups
    miss (cache-only path; we do not fall back to API to keep aggregation
    calls bounded — unknown variants are still counted in aggregates, just
    without SKU/name/category enrichment).

    The variant's ``type`` field tells us which of product/material/service
    owns the parent, so we do one targeted cache lookup instead of probing
    all three tables.
    """
    variant = variant_cache.get(variant_id)
    if variant is None:
        variant = await services.cache.get_by_id(EntityType.VARIANT, variant_id)
        variant_cache[variant_id] = variant or {}

    if not variant:
        return None, None

    mapping = _PARENT_BY_VARIANT_TYPE.get(variant.get("type") or "")
    if mapping is None:
        return variant, None
    parent_entity_type, fk_field = mapping
    parent_id = variant.get(fk_field)
    if parent_id is None:
        return variant, None

    cache_key = (parent_entity_type, parent_id)
    if cache_key in category_cache:
        return variant, category_cache[cache_key]

    parent = await services.cache.get_by_id(parent_entity_type, parent_id)
    category = parent.get("category_name") if parent else None
    category_cache[cache_key] = category or None
    return variant, category or None


def _iter_rows(so: Any) -> Iterable[Any]:
    """Yield sales-order rows, handling the UNSET sentinel."""
    return unwrap_unset(so.sales_order_rows, [])


def _row_revenue(row: Any) -> float:
    """Revenue contribution for a single sales-order row."""
    qty = unwrap_unset(row.quantity, 0) or 0
    price = unwrap_unset(row.price_per_unit, 0) or 0
    total_discount = unwrap_unset(getattr(row, "total_discount", None), 0) or 0
    return float(qty) * float(price) - float(total_discount)


# ============================================================================
# Tool 1: top_selling_variants
# ============================================================================


class TopSellingVariantsRequest(BaseModel):
    """Request for top-selling variants over a date window."""

    model_config = ConfigDict(extra="forbid")

    start_date: date = Field(
        ..., description="Start of the window (inclusive, ISO-8601 date)"
    )
    end_date: date = Field(
        ..., description="End of the window (inclusive, ISO-8601 date)"
    )
    limit: int = Field(
        default=20,
        ge=1,
        description="Maximum number of variants to return (default 20, min 1)",
    )
    category: str | None = Field(
        default=None,
        description="Optional item category name to filter by (e.g. 'bikes')",
    )
    order_by: Literal["units", "revenue"] = Field(
        default="units",
        description="Sort key: 'units' (quantity sold) or 'revenue' (dollar volume)",
    )
    location_id: int | None = Field(
        default=None, description="Optional location ID to filter by"
    )
    format: Literal["markdown", "json"] = Field(
        default="markdown",
        description=(
            "Output format: 'markdown' (default) for human-readable tables; "
            "'json' for structured data consumable by downstream tools/aggregations."
        ),
    )


class VariantSalesRow(BaseModel):
    """Per-variant sales aggregate row."""

    sku: str | None
    variant_id: int
    name: str | None
    units: float
    revenue: float
    order_count: int


class TopSellingVariantsResponse(BaseModel):
    """Response for top_selling_variants."""

    rows: list[VariantSalesRow]
    total_variants: int
    window_start: str
    window_end: str


@cache_read(
    EntityType.VARIANT, EntityType.PRODUCT, EntityType.MATERIAL, EntityType.SERVICE
)
async def _top_selling_variants_impl(
    request: TopSellingVariantsRequest, context: Context
) -> TopSellingVariantsResponse:
    """Compute top-selling variants from DELIVERED sales orders in the window."""
    services = get_services(context)

    logger.info(
        "top_selling_variants_started",
        start_date=str(request.start_date),
        end_date=str(request.end_date),
        limit=request.limit,
        category=request.category,
        order_by=request.order_by,
        location_id=request.location_id,
    )

    orders = await _fetch_delivered_sales_orders_in_window(
        services,
        request.start_date,
        request.end_date,
        location_id=request.location_id,
    )

    # variant_id -> {units, revenue, order_ids}
    agg: dict[int, dict[str, Any]] = defaultdict(
        lambda: {"units": 0.0, "revenue": 0.0, "order_ids": set()}
    )
    variant_cache: dict[int, dict[str, Any]] = {}
    category_cache: dict[tuple[EntityType, int], str | None] = {}

    for so in orders:
        so_id = so.id
        for row in _iter_rows(so):
            variant_id = unwrap_unset(row.variant_id, None)
            if variant_id is None:
                continue
            qty = float(unwrap_unset(row.quantity, 0) or 0)
            revenue = _row_revenue(row)
            bucket = agg[variant_id]
            bucket["units"] += qty
            bucket["revenue"] += revenue
            bucket["order_ids"].add(so_id)

    # Resolve variant info (SKU, name, category) for each aggregated variant
    rows: list[VariantSalesRow] = []
    for variant_id, bucket in agg.items():
        variant, category = await _resolve_variant_info(
            services, variant_id, variant_cache, category_cache
        )
        # Filter by category; case-insensitive match
        if request.category is not None and (
            category is None or category.lower() != request.category.lower()
        ):
            continue
        rows.append(
            VariantSalesRow(
                sku=(variant or {}).get("sku"),
                variant_id=variant_id,
                name=(variant or {}).get("display_name") or (variant or {}).get("sku"),
                units=round(bucket["units"], 4),
                revenue=round(bucket["revenue"], 2),
                order_count=len(bucket["order_ids"]),
            )
        )

    sort_key = (
        (lambda r: r.units) if request.order_by == "units" else (lambda r: r.revenue)
    )
    rows.sort(key=sort_key, reverse=True)
    limited = rows[: request.limit]

    logger.info(
        "top_selling_variants_completed",
        orders_scanned=len(orders),
        variants_aggregated=len(agg),
        rows_returned=len(limited),
    )

    return TopSellingVariantsResponse(
        rows=limited,
        total_variants=len(rows),
        window_start=str(request.start_date),
        window_end=str(request.end_date),
    )


@observe_tool
@unpack_pydantic_params
async def top_selling_variants(
    request: Annotated[TopSellingVariantsRequest, Unpack()], context: Context
) -> ToolResult:
    """Top-selling product variants over a date window — returns multiple ranked rows.

    Aggregates DELIVERED sales orders in the window, rolls up units sold and
    revenue per variant, and returns the top-N sorted by ``order_by`` (default
    ``units``). Supports optional category and location filters.

    Use when an agent needs a single answer to "what sold best last quarter?"
    instead of paginating through orders client-side.
    """
    response = await _top_selling_variants_impl(request, context)

    if request.format == "json":
        return ToolResult(
            content=response.model_dump_json(indent=2),
            structured_content=response.model_dump(),
        )

    if not response.rows:
        md = (
            f"No DELIVERED sales in window "
            f"{response.window_start} - {response.window_end}."
        )
    else:
        table = format_md_table(
            headers=["SKU", "Variant", "Name", "Units", "Revenue", "Orders"],
            rows=[
                [
                    r.sku or "-",
                    r.variant_id,
                    r.name or "-",
                    f"{r.units:g}",
                    f"{r.revenue:,.2f}",
                    r.order_count,
                ]
                for r in response.rows
            ],
        )
        md = (
            f"## Top Selling Variants "
            f"({response.window_start} - {response.window_end})\n\n"
            f"{table}\n\n"
            f"_{response.total_variants} variant(s) matched; "
            f"showing top {len(response.rows)}._"
        )

    return make_simple_result(md, structured_data=response.model_dump())


# ============================================================================
# Tool 2: sales_summary
# ============================================================================


SalesGroupBy = Literal["day", "week", "month", "variant", "customer", "category"]


class SalesSummaryRequest(BaseModel):
    """Request for grouped sales summary."""

    model_config = ConfigDict(extra="forbid")

    start_date: date = Field(..., description="Start of window (inclusive)")
    end_date: date = Field(..., description="End of window (inclusive)")
    group_by: SalesGroupBy = Field(
        ...,
        description="Grouping key: day, week, month, variant, customer, or category",
    )
    format: Literal["markdown", "json"] = Field(
        default="markdown",
        description=(
            "Output format: 'markdown' (default) for human-readable tables; "
            "'json' for structured data consumable by downstream tools/aggregations."
        ),
    )


class SummaryRow(BaseModel):
    """Grouped sales aggregate row."""

    group: str
    units: float
    revenue: float
    order_count: int


class SalesSummaryResponse(BaseModel):
    """Response for sales_summary."""

    rows: list[SummaryRow]
    group_by: SalesGroupBy
    window_start: str
    window_end: str


def _group_key_time(so_created: datetime, group_by: SalesGroupBy) -> str:
    """Compute a time-based group key (day/week/month) from ``created_at``."""
    if group_by == "day":
        return so_created.date().isoformat()
    if group_by == "week":
        iso = so_created.date().isocalendar()
        return f"{iso.year}-W{iso.week:02d}"
    # month
    return f"{so_created.year:04d}-{so_created.month:02d}"


@cache_read(
    EntityType.VARIANT, EntityType.PRODUCT, EntityType.MATERIAL, EntityType.SERVICE
)
async def _sales_summary_impl(
    request: SalesSummaryRequest, context: Context
) -> SalesSummaryResponse:
    """Compute grouped sales summary for DELIVERED orders in the window."""
    services = get_services(context)

    logger.info(
        "sales_summary_started",
        start_date=str(request.start_date),
        end_date=str(request.end_date),
        group_by=request.group_by,
    )

    orders = await _fetch_delivered_sales_orders_in_window(
        services, request.start_date, request.end_date
    )

    agg: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"units": 0.0, "revenue": 0.0, "order_ids": set()}
    )
    variant_cache: dict[int, dict[str, Any]] = {}
    category_cache: dict[tuple[EntityType, int], str | None] = {}

    for so in orders:
        so_id = so.id
        created = unwrap_unset(so.created_at, None)
        if created is not None and not isinstance(created, datetime):
            created = None
        if created is not None and created.tzinfo is None:
            created = created.replace(tzinfo=UTC)

        # customer grouping works at SO level (aggregate over all rows)
        if request.group_by == "customer":
            key = str(unwrap_unset(so.customer_id, "unknown"))
            bucket = agg[key]
            for row in _iter_rows(so):
                bucket["units"] += float(unwrap_unset(row.quantity, 0) or 0)
                bucket["revenue"] += _row_revenue(row)
            bucket["order_ids"].add(so_id)
            continue

        if request.group_by in ("day", "week", "month"):
            if created is None:
                key = "unknown"
            else:
                key = _group_key_time(created, request.group_by)
            bucket = agg[key]
            for row in _iter_rows(so):
                bucket["units"] += float(unwrap_unset(row.quantity, 0) or 0)
                bucket["revenue"] += _row_revenue(row)
            bucket["order_ids"].add(so_id)
            continue

        # variant / category: aggregate per row
        for row in _iter_rows(so):
            variant_id = unwrap_unset(row.variant_id, None)
            if variant_id is None:
                continue
            qty = float(unwrap_unset(row.quantity, 0) or 0)
            revenue = _row_revenue(row)

            if request.group_by == "variant":
                variant, _ = await _resolve_variant_info(
                    services, variant_id, variant_cache, category_cache
                )
                key = (variant or {}).get("sku") or f"variant:{variant_id}"
            else:  # category
                _, category = await _resolve_variant_info(
                    services, variant_id, variant_cache, category_cache
                )
                key = category or "uncategorized"

            bucket = agg[key]
            bucket["units"] += qty
            bucket["revenue"] += revenue
            bucket["order_ids"].add(so_id)

    rows = [
        SummaryRow(
            group=group,
            units=round(b["units"], 4),
            revenue=round(b["revenue"], 2),
            order_count=len(b["order_ids"]),
        )
        for group, b in agg.items()
    ]
    # For time groups, sort by key ascending; for others sort by revenue desc.
    if request.group_by in ("day", "week", "month"):
        rows.sort(key=lambda r: r.group)
    else:
        rows.sort(key=lambda r: r.revenue, reverse=True)

    logger.info(
        "sales_summary_completed",
        orders_scanned=len(orders),
        groups=len(rows),
    )

    return SalesSummaryResponse(
        rows=rows,
        group_by=request.group_by,
        window_start=str(request.start_date),
        window_end=str(request.end_date),
    )


@observe_tool
@unpack_pydantic_params
async def sales_summary(
    request: Annotated[SalesSummaryRequest, Unpack()], context: Context
) -> ToolResult:
    """Group DELIVERED sales in a window by time or dimension — returns one row per group.

    ``group_by`` supports ``day``, ``week`` (ISO week), ``month``, ``variant``
    (by SKU), ``customer`` (by customer ID), and ``category`` (by item
    category name). Returns one row per group with units, revenue, and order
    count.
    """
    response = await _sales_summary_impl(request, context)

    if request.format == "json":
        return ToolResult(
            content=response.model_dump_json(indent=2),
            structured_content=response.model_dump(),
        )

    if not response.rows:
        md = (
            f"No DELIVERED sales in window "
            f"{response.window_start} - {response.window_end}."
        )
    else:
        table = format_md_table(
            headers=[response.group_by.title(), "Units", "Revenue", "Orders"],
            rows=[
                [
                    r.group,
                    f"{r.units:g}",
                    f"{r.revenue:,.2f}",
                    r.order_count,
                ]
                for r in response.rows
            ],
        )
        md = (
            f"## Sales Summary by {response.group_by} "
            f"({response.window_start} - {response.window_end})\n\n{table}"
        )

    return make_simple_result(md, structured_data=response.model_dump())


# ============================================================================
# Tool 3: inventory_velocity
# ============================================================================


class InventoryVelocityRequest(BaseModel):
    """Request for inventory-velocity stats for one or more SKUs/variants.

    Exactly one of ``sku_or_variant_id`` (single-item shape) or
    ``sku_or_variant_ids`` (batch shape) must be provided.
    """

    model_config = ConfigDict(extra="forbid")

    sku_or_variant_id: str | int | None = Field(
        default=None,
        description=("SKU (string) or variant_id (int) to analyze. Single-item shape."),
    )
    sku_or_variant_ids: CoercedStrIntListOpt = Field(
        default=None,
        description=(
            "Batch shape: JSON array of SKUs (strings) and/or variant IDs (integers), "
            'e.g. ["WS74001", "WS74002"] or [12345, 67890] (1-100 items). '
            "Returns one row per item in a markdown table. "
            "Use this for cross-variant reports."
        ),
        min_length=1,
        max_length=100,
    )
    period_days: int = Field(
        default=90,
        ge=1,
        le=365,
        description="Rolling-window size in days (default 90, max 365)",
    )
    include_mo_consumption: bool = Field(
        default=True,
        description=(
            "When true (default), units consumed as ingredients on completed "
            "MOs in the window are added to the velocity figure. "
            "Set false to match the legacy SO-only behavior."
        ),
    )
    format: Literal["markdown", "json"] = Field(
        default="markdown",
        description=(
            "Output format: 'markdown' (default) for human-readable tables; "
            "'json' for structured data consumable by downstream tools/aggregations."
        ),
    )

    @property
    def resolved_inputs(self) -> list[str | int]:
        """Return the canonical list of SKU/ID inputs to analyze."""
        if self.sku_or_variant_ids is not None:
            return list(self.sku_or_variant_ids)
        if self.sku_or_variant_id is not None:
            return [self.sku_or_variant_id]
        return []

    @property
    def is_batch(self) -> bool:
        """True when the batch shape was used."""
        return self.sku_or_variant_ids is not None

    def model_post_init(self, _context: Any) -> None:
        """Validate that exactly one shape is provided."""
        has_single = self.sku_or_variant_id is not None
        has_batch = self.sku_or_variant_ids is not None
        if not has_single and not has_batch:
            raise ValueError(
                "Provide either 'sku_or_variant_id' (single) or "
                "'sku_or_variant_ids' (batch)."
            )
        if has_single and has_batch:
            raise ValueError(
                "Provide only one of 'sku_or_variant_id' or 'sku_or_variant_ids', "
                "not both."
            )


class VelocityStats(BaseModel):
    """Per-variant velocity statistics."""

    sku: str | None
    variant_id: int
    units_sold: float
    units_consumed_by_mos: float
    units_total: float
    avg_daily: float
    stock_on_hand: float
    days_of_cover: float | None
    period_days: int
    window_start: str
    window_end: str


class InventoryVelocityResponse(BaseModel):
    """Response wrapper — one ``VelocityStats`` row per requested variant."""

    items: list[VelocityStats]


async def _resolve_sku_or_variant_id(
    services: Any, sku_or_id: str | int
) -> tuple[int, str | None]:
    """Return (variant_id, sku) for either an integer ID or a SKU string."""
    if isinstance(sku_or_id, int):
        from katana_mcp.cache import EntityType

        variant = await services.cache.get_by_id(EntityType.VARIANT, sku_or_id)
        sku = (variant or {}).get("sku")
        return sku_or_id, sku

    sku_str = str(sku_or_id).strip()
    if not sku_str:
        raise ValueError("sku_or_variant_id cannot be empty")
    # Try to parse as integer first — some callers pass the id as a string
    if sku_str.isdigit():
        from katana_mcp.cache import EntityType

        vid = int(sku_str)
        variant = await services.cache.get_by_id(EntityType.VARIANT, vid)
        sku = (variant or {}).get("sku")
        return vid, sku

    variant = await services.cache.get_by_sku(sku=sku_str)
    if not variant:
        raise ValueError(f"SKU '{sku_str}' not found in variant cache")
    return variant["id"], sku_str


async def _fetch_stock_on_hand(services: Any, variant_id: int) -> float:
    """Sum quantity_in_stock across all locations for a variant."""
    response = await get_all_inventory_point.asyncio_detailed(
        client=services.client, variant_id=variant_id
    )
    items = unwrap_data(response, default=[])
    total = 0.0
    for inv in items:
        total += float(unwrap_unset(inv.quantity_in_stock, "0") or 0)
    return total


async def _fetch_completed_mo_recipe_rows_in_window(
    services: Any,
    window_start_naive: datetime,
    window_end_naive: datetime,
) -> list[Any]:
    """Return recipe rows from completed MOs whose done_date falls in the window.

    A single ``SELECT ... JOIN ... WHERE`` statement filters recipe rows by
    joining ``CachedManufacturingOrderRecipeRow`` to its parent
    ``CachedManufacturingOrder`` and applying ``status=done``, the
    ``done_date`` window, and the soft-delete guard against the parent. The
    JOIN avoids a separate ID-collection round-trip and sidesteps SQLite's
    bound-parameter limit (≈ 999) when many MOs match the window.

    Both tables are tz-naive in SQLite (offsets stripped on insert), so the
    window datetimes must also be naive UTC — callers are responsible for
    stripping tzinfo before passing.
    """
    from sqlmodel import select

    from katana_mcp.typed_cache import ensure_manufacturing_orders_synced
    from katana_public_api_client.models_pydantic._generated import (
        CachedManufacturingOrder,
        CachedManufacturingOrderRecipeRow,
        ManufacturingOrderStatus,
    )

    # MO sync fans out to recipe rows via ``EntitySpec.related_specs`` —
    # both watermarks advance in parallel under disjoint per-entity locks.
    await ensure_manufacturing_orders_synced(services.client, services.typed_cache)

    async with services.typed_cache.session() as session:
        # Filter both sides of the join for soft-delete: a recipe row could
        # be tombstoned even while its parent MO is still live, so each table's
        # ``deleted_at`` guard is independently necessary to keep tombstoned
        # consumption out of velocity totals.
        row_stmt = (
            select(CachedManufacturingOrderRecipeRow)
            .join(
                CachedManufacturingOrder,
                CachedManufacturingOrder.id
                == CachedManufacturingOrderRecipeRow.manufacturing_order_id,
            )
            .where(CachedManufacturingOrder.status == ManufacturingOrderStatus.done)
            .where(CachedManufacturingOrder.done_date.is_not(None))
            .where(CachedManufacturingOrder.deleted_at.is_(None))
            .where(CachedManufacturingOrderRecipeRow.deleted_at.is_(None))
        )
        row_stmt = apply_date_window_filters(
            row_stmt,
            {
                "window_start": window_start_naive,
                "window_end": window_end_naive,
            },
            ge_pairs={"window_start": CachedManufacturingOrder.done_date},
            le_pairs={"window_end": CachedManufacturingOrder.done_date},
        )
        return list((await session.exec(row_stmt)).all())


async def _inventory_velocity_impl(
    request: InventoryVelocityRequest, context: Context
) -> InventoryVelocityResponse:
    """Compute inventory-velocity stats for one or more variants."""
    services = get_services(context)

    inputs = request.resolved_inputs

    # Inclusive window [window_start, window_end] covers exactly period_days
    # calendar days. Subtract period_days - 1 so a 7-day window ending today
    # starts 6 days ago, not 7.
    window_end = datetime.now(tz=UTC).date()
    window_start = window_end - timedelta(days=request.period_days - 1)
    # Naive UTC versions for cache comparisons (SQLite stores tz-stripped
    # datetimes). The end-of-day upper bound runs to 23:59:59.999999 so an MO
    # whose ``done_date`` carries microseconds (e.g. ``23:59:59.500000``) is
    # included by the inclusive ``<=`` filter — without the microsecond pad,
    # any sub-second-precision timestamp on the last day of the window would
    # be silently dropped.
    window_end_dt = datetime(
        window_end.year,
        window_end.month,
        window_end.day,
        23,
        59,
        59,
        999_999,
    )
    window_start_dt = datetime(window_start.year, window_start.month, window_start.day)

    logger.info(
        "inventory_velocity_started",
        inputs=inputs,
        period_days=request.period_days,
        include_mo_consumption=request.include_mo_consumption,
    )

    # Resolve all variant IDs up front (sequential; each is a cache lookup).
    resolved: list[tuple[int, str | None]] = []
    for inp in inputs:
        variant_id, sku = await _resolve_sku_or_variant_id(services, inp)
        resolved.append((variant_id, sku))

    # Fetch sales orders (and optionally MO recipe rows) in parallel.
    fetch_tasks: list[Any] = [
        _fetch_delivered_sales_orders_in_window(services, window_start, window_end),
    ]
    if request.include_mo_consumption:
        fetch_tasks.append(
            _fetch_completed_mo_recipe_rows_in_window(
                services, window_start_dt, window_end_dt
            )
        )

    fetch_results = await asyncio.gather(*fetch_tasks)
    sales_orders = fetch_results[0]
    recipe_rows: list[Any] = fetch_results[1] if request.include_mo_consumption else []

    # Stock-on-hand must be fetched per variant (separate API call each).
    # Cap concurrency so a 100-variant batch doesn't burst 100 simultaneous
    # ``/inventory`` requests at the connection pool — transport-layer
    # rate limiting handles 429s, but a semaphore prevents the burst
    # entirely.
    stock_fetch_semaphore = asyncio.Semaphore(_STOCK_FETCH_CONCURRENCY)

    async def _fetch_stock_limited(variant_id: int) -> float:
        async with stock_fetch_semaphore:
            return await _fetch_stock_on_hand(services, variant_id)

    stock_values = await asyncio.gather(
        *(_fetch_stock_limited(variant_id) for variant_id, _ in resolved)
    )

    # Pre-aggregate demand per variant in a single pass over each row source,
    # so the per-variant loop below is O(variant_count) instead of
    # O(variant_count * total_rows).
    units_sold_by_variant: dict[int, float] = defaultdict(float)
    for so in sales_orders:
        for row in _iter_rows(so):
            row_variant_id = unwrap_unset(row.variant_id, None)
            if row_variant_id is not None:
                units_sold_by_variant[row_variant_id] += float(
                    unwrap_unset(row.quantity, 0) or 0
                )

    units_consumed_by_variant: dict[int, float] = defaultdict(float)
    if request.include_mo_consumption:
        for rr in recipe_rows:
            units_consumed_by_variant[rr.variant_id] += float(
                rr.total_actual_quantity or 0
            )

    items: list[VelocityStats] = []
    for (variant_id, sku), stock_on_hand in zip(resolved, stock_values, strict=True):
        units_sold = units_sold_by_variant.get(variant_id, 0.0)
        units_consumed_by_mos = units_consumed_by_variant.get(variant_id, 0.0)
        units_total = units_sold + units_consumed_by_mos
        avg_daily = (
            units_total / request.period_days if request.period_days > 0 else 0.0
        )
        days_of_cover: float | None
        if avg_daily > 0:
            days_of_cover = round(stock_on_hand / avg_daily, 2)
        else:
            days_of_cover = None

        items.append(
            VelocityStats(
                sku=sku,
                variant_id=variant_id,
                units_sold=round(units_sold, 4),
                units_consumed_by_mos=round(units_consumed_by_mos, 4),
                units_total=round(units_total, 4),
                avg_daily=round(avg_daily, 4),
                stock_on_hand=round(stock_on_hand, 4),
                days_of_cover=days_of_cover,
                period_days=request.period_days,
                window_start=window_start.isoformat(),
                window_end=window_end.isoformat(),
            )
        )

    logger.info(
        "inventory_velocity_completed",
        variant_count=len(items),
    )

    return InventoryVelocityResponse(items=items)


def _format_velocity_card(stats: VelocityStats) -> str:
    """Render a single variant's velocity as a rich markdown card."""
    cover = (
        f"{stats.days_of_cover:.1f} days"
        if stats.days_of_cover is not None
        else "N/A (no demand history in window)"
    )
    lines = [
        f"## Inventory Velocity: {stats.sku or stats.variant_id}",
        f"- **Variant ID**: {stats.variant_id}",
        f"- **Window**: {stats.window_start} to {stats.window_end} "
        f"({stats.period_days} days)",
        f"- **Units Sold (SO)**: {stats.units_sold:g}",
        f"- **Units Consumed (MO)**: {stats.units_consumed_by_mos:g}",
        f"- **Total Demand**: {stats.units_total:g}",
        f"- **Average Daily**: {stats.avg_daily:.2f}",
        f"- **Stock on Hand**: {stats.stock_on_hand:g}",
        f"- **Days of Cover**: {cover}",
    ]
    return "\n".join(lines)


def _format_velocity_table(response: InventoryVelocityResponse) -> str:
    """Render a batch velocity response as a markdown table."""
    headers = [
        "SKU",
        "Variant ID",
        "Units Sold (SO)",
        "Units Consumed (MO)",
        "Total",
        "Avg/day",
        "Stock",
        "Days Cover",
    ]
    rows = []
    for s in response.items:
        cover = f"{s.days_of_cover:.1f}" if s.days_of_cover is not None else "N/A"
        rows.append(
            [
                s.sku or "",
                str(s.variant_id),
                f"{s.units_sold:g}",
                f"{s.units_consumed_by_mos:g}",
                f"{s.units_total:g}",
                f"{s.avg_daily:.2f}",
                f"{s.stock_on_hand:g}",
                cover,
            ]
        )
    first = response.items[0] if response.items else None
    title = (
        f"## Inventory Velocity Report "
        f"({first.window_start} to {first.window_end}, {first.period_days} days)"
        if first
        else "## Inventory Velocity Report"
    )
    return f"{title}\n\n{format_md_table(headers, rows)}"


@observe_tool
@unpack_pydantic_params
async def inventory_velocity(
    request: Annotated[InventoryVelocityRequest, Unpack()], context: Context
) -> ToolResult:
    """Velocity stats for one or more SKUs: units sold/consumed, avg-daily, days of cover.

    Computes demand in the trailing ``period_days`` (default 90) from DELIVERED
    sales orders **and** completed manufacturing-order ingredient consumption,
    divides by the period to get average daily demand, and pairs it with
    current stock-on-hand to produce a ``days_of_cover`` estimate.

    Use ``sku_or_variant_id`` for a single-variant rich card, or
    ``sku_or_variant_ids`` for a cross-variant batch table.
    Set ``include_mo_consumption=false`` to use only SO-side numbers (legacy
    behaviour). ``days_of_cover`` is ``None`` when average daily demand is 0.
    """
    response = await _inventory_velocity_impl(request, context)

    if request.format == "json":
        return ToolResult(
            content=response.model_dump_json(indent=2),
            structured_content=response.model_dump(),
        )

    if request.is_batch or len(response.items) > 1:
        md = _format_velocity_table(response)
    else:
        md = _format_velocity_card(response.items[0]) if response.items else ""

    return make_simple_result(md, structured_data=response.model_dump())


# ============================================================================
# Registration
# ============================================================================


def register_tools(mcp: FastMCP) -> None:
    """Register reporting tools with the FastMCP instance.

    Args:
        mcp: FastMCP server instance to register tools with
    """
    from mcp.types import ToolAnnotations

    _read = ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    )

    mcp.tool(tags={"reporting", "sales", "read"}, annotations=_read)(
        top_selling_variants
    )
    mcp.tool(tags={"reporting", "sales", "read"}, annotations=_read)(sales_summary)
    mcp.tool(tags={"reporting", "inventory", "read"}, annotations=_read)(
        inventory_velocity
    )
