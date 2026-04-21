"""Reporting and aggregation tools for Katana MCP Server.

Read-only aggregation tools that compute rollups client-side from paginated
sales-order data. These exist to replace multi-call analytical workflows
(e.g. "top 20 selling bikes over the last 90 days") with a single tool call.

Tools:
- top_selling_variants: top-N variants by units or revenue over a date window
- sales_summary: group sales in a window by day/week/month/variant/customer/category
- inventory_velocity: units_sold, avg_daily, stock_on_hand, days_of_cover for a SKU

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
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from datetime import UTC, date, datetime, timedelta
from typing import Annotated, Any, Literal

from fastmcp import Context, FastMCP
from fastmcp.tools import ToolResult
from pydantic import BaseModel, Field

from katana_mcp.logging import get_logger, observe_tool
from katana_mcp.services import get_services
from katana_mcp.tools.tool_result_utils import (
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


async def _resolve_variant_info(
    services: Any,
    variant_id: int,
    variant_cache: dict[int, dict[str, Any]],
    category_cache: dict[int, str | None],
) -> tuple[dict[str, Any] | None, str | None]:
    """Resolve variant dict and its item-category, caching both.

    Returns ``(variant_dict, category_name)``. Both may be None if lookups
    miss (cache-only path; we do not fall back to API to keep aggregation
    calls bounded — unknown variants are still counted in aggregates, just
    without SKU/name/category enrichment).
    """
    variant = variant_cache.get(variant_id)
    if variant is None:
        from katana_mcp.cache import EntityType

        variant = await services.cache.get_by_id(EntityType.VARIANT, variant_id)
        variant_cache[variant_id] = variant or {}

    if not variant:
        return None, None

    product_id = variant.get("product_id")
    if product_id is None:
        return variant, None

    category = category_cache.get(product_id)
    if category is not None or product_id in category_cache:
        return variant, category

    # Try product → then material → then service for category_name. The
    # variant dict alone doesn't tell us which one, so we try in order and
    # stop at the first hit.
    category = await _fetch_category_for_product(services, product_id)
    category_cache[product_id] = category
    return variant, category


async def _fetch_category_for_product(services: Any, product_id: int) -> str | None:
    """Look up the category_name for a given product/material/service ID.

    Tries product first, then material, then service. Returns None if none
    match or category is unset.
    """
    from katana_public_api_client.api.material import get_material
    from katana_public_api_client.api.product import get_product
    from katana_public_api_client.api.services import get_service
    from katana_public_api_client.models import ErrorResponse
    from katana_public_api_client.utils import unwrap

    for fetcher in (
        get_product.asyncio_detailed,
        get_material.asyncio_detailed,
        get_service.asyncio_detailed,
    ):
        try:
            response = await fetcher(id=product_id, client=services.client)
        except Exception:
            continue
        obj = unwrap(response, raise_on_error=False)
        if obj is None or isinstance(obj, ErrorResponse):
            continue
        cat = unwrap_unset(getattr(obj, "category_name", None), None)
        if cat is not None:
            return cat
        # Found a matching record but no category — stop here.
        return None
    return None


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
    category_cache: dict[int, str | None] = {}

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
    """Top-selling product variants over a date window.

    Aggregates DELIVERED sales orders in the window, rolls up units sold and
    revenue per variant, and returns the top-N sorted by ``order_by`` (default
    ``units``). Supports optional category and location filters.

    Use when an agent needs a single answer to "what sold best last quarter?"
    instead of paginating through orders client-side.
    """
    response = await _top_selling_variants_impl(request, context)

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

    start_date: date = Field(..., description="Start of window (inclusive)")
    end_date: date = Field(..., description="End of window (inclusive)")
    group_by: SalesGroupBy = Field(
        ...,
        description="Grouping key: day, week, month, variant, customer, or category",
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
    category_cache: dict[int, str | None] = {}

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
    """Group DELIVERED sales in a window by time or dimension.

    ``group_by`` supports ``day``, ``week`` (ISO week), ``month``, ``variant``
    (by SKU), ``customer`` (by customer ID), and ``category`` (by item
    category name). Returns one row per group with units, revenue, and order
    count.
    """
    response = await _sales_summary_impl(request, context)

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
    """Request for inventory-velocity stats for a SKU/variant."""

    sku_or_variant_id: str | int = Field(
        ..., description="SKU (string) or variant_id (int) to analyze"
    )
    period_days: int = Field(
        default=90,
        ge=1,
        le=365,
        description="Rolling-window size in days (default 90, max 365)",
    )


class VelocityStats(BaseModel):
    """Velocity response."""

    sku: str | None
    variant_id: int
    units_sold: float
    avg_daily: float
    stock_on_hand: float
    days_of_cover: float | None
    period_days: int
    window_start: str
    window_end: str


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


async def _inventory_velocity_impl(
    request: InventoryVelocityRequest, context: Context
) -> VelocityStats:
    """Compute inventory-velocity stats for one variant."""
    services = get_services(context)

    variant_id, sku = await _resolve_sku_or_variant_id(
        services, request.sku_or_variant_id
    )

    end_dt = datetime.now(tz=UTC)
    start_dt = end_dt - timedelta(days=request.period_days)
    window_start = start_dt.date()
    window_end = end_dt.date()

    logger.info(
        "inventory_velocity_started",
        variant_id=variant_id,
        sku=sku,
        period_days=request.period_days,
    )

    orders = await _fetch_delivered_sales_orders_in_window(
        services, window_start, window_end
    )

    units_sold = 0.0
    for so in orders:
        for row in _iter_rows(so):
            if unwrap_unset(row.variant_id, None) == variant_id:
                units_sold += float(unwrap_unset(row.quantity, 0) or 0)

    stock_on_hand = await _fetch_stock_on_hand(services, variant_id)

    avg_daily = units_sold / request.period_days if request.period_days > 0 else 0.0
    days_of_cover: float | None
    if avg_daily > 0:
        days_of_cover = round(stock_on_hand / avg_daily, 2)
    else:
        days_of_cover = None

    logger.info(
        "inventory_velocity_completed",
        variant_id=variant_id,
        units_sold=units_sold,
        stock_on_hand=stock_on_hand,
        avg_daily=avg_daily,
    )

    return VelocityStats(
        sku=sku,
        variant_id=variant_id,
        units_sold=round(units_sold, 4),
        avg_daily=round(avg_daily, 4),
        stock_on_hand=round(stock_on_hand, 4),
        days_of_cover=days_of_cover,
        period_days=request.period_days,
        window_start=window_start.isoformat(),
        window_end=window_end.isoformat(),
    )


@observe_tool
@unpack_pydantic_params
async def inventory_velocity(
    request: Annotated[InventoryVelocityRequest, Unpack()], context: Context
) -> ToolResult:
    """How fast is a SKU moving? Units sold, avg-daily, stock, and days of cover.

    Computes units sold in the trailing ``period_days`` (default 90) from
    DELIVERED sales orders, divides by the period to get average daily sales,
    and pairs it with current stock-on-hand to produce a ``days_of_cover``
    estimate. ``days_of_cover`` is ``None`` when average daily sales are 0
    (no sales history, can't project).
    """
    response = await _inventory_velocity_impl(request, context)

    cover = (
        f"{response.days_of_cover:.1f} days"
        if response.days_of_cover is not None
        else "∞ (no sales history)"
    )
    lines = [
        f"## Inventory Velocity: {response.sku or response.variant_id}",
        f"- **Variant ID**: {response.variant_id}",
        f"- **Window**: {response.window_start} to {response.window_end} "
        f"({response.period_days} days)",
        f"- **Units Sold**: {response.units_sold:g}",
        f"- **Average Daily**: {response.avg_daily:.2f}",
        f"- **Stock on Hand**: {response.stock_on_hand:g}",
        f"- **Days of Cover**: {cover}",
    ]

    return make_simple_result("\n".join(lines), structured_data=response.model_dump())


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
