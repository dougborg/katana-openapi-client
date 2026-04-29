"""Sales order management tools for Katana MCP Server.

Foundation tools for creating sales orders.

These tools provide:
- create_sales_order: Create sales orders with preview/confirm pattern
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Annotated, Any, Literal

from fastmcp import Context, FastMCP
from fastmcp.tools import ToolResult
from pydantic import BaseModel, Field

from katana_mcp.cache import EntityType
from katana_mcp.logging import get_logger, observe_tool
from katana_mcp.services import get_services
from katana_mcp.tools.list_coercion import CoercedIntListOpt
from katana_mcp.tools.tool_result_utils import (
    UI_META,
    PaginationMeta,
    apply_date_window_filters,
    coerce_enum,
    enum_to_str,
    format_md_table,
    iso_or_none,
    make_tool_result,
    none_coro,
    parse_request_dates,
)
from katana_mcp.unpack import Unpack, unpack_pydantic_params
from katana_public_api_client.client_types import UNSET, Unset
from katana_public_api_client.domain.converters import to_unset, unwrap_unset
from katana_public_api_client.models import (
    AddressEntityType,
    CreateSalesOrderRequest as APICreateSalesOrderRequest,
    CreateSalesOrderRequestSalesOrderRowsItem,
    CreateSalesOrderStatus,
    SalesOrder,
    SalesOrderAddress as APISalesOrderAddress,
)
from katana_public_api_client.utils import unwrap_as

logger = get_logger(__name__)


# ============================================================================
# Tool 1: create_sales_order
# ============================================================================


class SalesOrderItem(BaseModel):
    """Line item for a sales order."""

    variant_id: int = Field(..., description="Variant ID to sell")
    quantity: float = Field(..., description="Quantity to sell", gt=0)
    price_per_unit: float | None = Field(
        default=None,
        description="Override price per unit (uses default if not specified)",
    )
    tax_rate_id: int | None = Field(default=None, description="Tax rate ID (optional)")
    location_id: int | None = Field(
        default=None, description="Location to pick from (optional)"
    )
    total_discount: float | None = Field(
        default=None, description="Discount for this line item (optional)"
    )


class SalesOrderAddress(BaseModel):
    """Billing or shipping address for a sales order."""

    entity_type: Literal["billing", "shipping"] = Field(
        ..., description="Type of address - billing or shipping"
    )
    first_name: str | None = Field(default=None, description="First name of contact")
    last_name: str | None = Field(default=None, description="Last name of contact")
    company: str | None = Field(default=None, description="Company name")
    phone: str | None = Field(default=None, description="Phone number")
    line_1: str | None = Field(default=None, description="Primary address line")
    line_2: str | None = Field(default=None, description="Secondary address line")
    city: str | None = Field(default=None, description="City")
    state: str | None = Field(default=None, description="State or province")
    zip_code: str | None = Field(default=None, description="Postal/ZIP code")
    country: str | None = Field(
        default=None, description="Country code (e.g., US, CA, GB)"
    )


class CreateSalesOrderRequest(BaseModel):
    """Request to create a sales order."""

    customer_id: int = Field(..., description="Customer ID placing the order")
    order_number: str = Field(..., description="Unique sales order number")
    items: list[SalesOrderItem] = Field(..., description="Line items", min_length=1)
    location_id: int | None = Field(
        default=None, description="Primary fulfillment location ID (optional)"
    )
    delivery_date: datetime | None = Field(
        default=None, description="Requested delivery date (optional)"
    )
    currency: str | None = Field(
        default=None,
        description="Currency code (defaults to company base currency)",
    )
    addresses: list[SalesOrderAddress] | None = Field(
        default=None, description="Billing and/or shipping addresses (optional)"
    )
    notes: str | None = Field(default=None, description="Additional notes (optional)")
    customer_ref: str | None = Field(
        default=None, description="Customer's reference number (optional)"
    )
    confirm: bool = Field(
        default=False,
        description="If false, returns preview. If true, creates order.",
    )


class SalesOrderResponse(BaseModel):
    """Response from creating a sales order."""

    id: int | None = None
    order_number: str
    customer_id: int
    location_id: int | None = None
    status: str | None = None
    total: float | None = None
    currency: str | None = None
    delivery_date: str | None = None
    is_preview: bool
    warnings: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    message: str


async def _create_sales_order_impl(
    request: CreateSalesOrderRequest, context: Context
) -> SalesOrderResponse:
    """Implementation of create_sales_order tool.

    Args:
        request: Request with sales order details
        context: Server context with KatanaClient

    Returns:
        Sales order response with details

    Raises:
        ValueError: If validation fails
        Exception: If API call fails
    """
    logger.info(
        f"{'Previewing' if not request.confirm else 'Creating'} sales order {request.order_number}"
    )

    # Calculate preview total (estimate based on items with prices)
    total_estimate = sum(
        (item.price_per_unit or 0.0) * item.quantity - (item.total_discount or 0.0)
        for item in request.items
    )

    # Preview mode - just return calculations without API call
    if not request.confirm:
        logger.info(
            f"Preview mode: SO {request.order_number} would have {len(request.items)} items"
        )

        # Generate warnings for missing optional fields
        warnings = []
        if request.location_id is None:
            warnings.append(
                "No location_id specified - order will use default location"
            )
        if request.delivery_date is None:
            warnings.append(
                "No delivery_date specified - order will have no delivery deadline"
            )

        return SalesOrderResponse(
            order_number=request.order_number,
            customer_id=request.customer_id,
            location_id=request.location_id,
            status="PENDING",
            total=total_estimate if total_estimate > 0 else None,
            currency=request.currency,
            delivery_date=request.delivery_date.isoformat()
            if request.delivery_date
            else None,
            is_preview=True,
            warnings=warnings,
            next_actions=[
                "Review the order details",
                "Set confirm=true to create the sales order",
            ],
            message=f"Preview: Sales order {request.order_number} with {len(request.items)} items"
            + (f" totaling {total_estimate:.2f}" if total_estimate > 0 else ""),
        )

    try:
        services = get_services(context)

        # Build sales order rows
        so_rows = []
        for item in request.items:
            row = CreateSalesOrderRequestSalesOrderRowsItem(
                variant_id=item.variant_id,
                quantity=item.quantity,
                price_per_unit=to_unset(item.price_per_unit),
                tax_rate_id=to_unset(item.tax_rate_id),
                location_id=to_unset(item.location_id),
                total_discount=to_unset(item.total_discount),
            )
            so_rows.append(row)

        # Build addresses if provided
        addresses_list: list[APISalesOrderAddress] | Unset = UNSET
        if request.addresses:
            addresses_list = []
            for addr in request.addresses:
                api_addr = APISalesOrderAddress(
                    id=0,  # Will be assigned by API
                    sales_order_id=0,  # Will be assigned by API
                    entity_type=AddressEntityType(addr.entity_type),
                    first_name=to_unset(addr.first_name),
                    last_name=to_unset(addr.last_name),
                    company=to_unset(addr.company),
                    phone=to_unset(addr.phone),
                    line_1=to_unset(addr.line_1),
                    line_2=to_unset(addr.line_2),
                    city=to_unset(addr.city),
                    state=to_unset(addr.state),
                    zip_=to_unset(addr.zip_code),
                    country=to_unset(addr.country),
                )
                addresses_list.append(api_addr)

        # Build API request
        api_request = APICreateSalesOrderRequest(
            order_no=request.order_number,
            customer_id=request.customer_id,
            sales_order_rows=so_rows,
            location_id=to_unset(request.location_id),
            delivery_date=to_unset(request.delivery_date),
            currency=to_unset(request.currency),
            addresses=addresses_list,
            additional_info=to_unset(request.notes),
            customer_ref=to_unset(request.customer_ref),
            order_created_date=datetime.now(UTC),
            status=CreateSalesOrderStatus.PENDING,
        )

        # Call API
        from katana_public_api_client.api.sales_order import (
            create_sales_order as api_create_sales_order,
        )

        response = await api_create_sales_order.asyncio_detailed(
            client=services.client, body=api_request
        )

        # unwrap_as() raises typed exceptions on error, returns typed SalesOrder
        so = unwrap_as(response, SalesOrder)
        logger.info(f"Successfully created sales order ID {so.id}")

        # Extract values using unwrap_unset for clean UNSET handling
        currency = unwrap_unset(so.currency, None)
        total = unwrap_unset(so.total, None)

        return SalesOrderResponse(
            id=so.id,
            order_number=so.order_no,
            customer_id=so.customer_id,
            location_id=so.location_id,
            status=so.status.value if so.status else "UNKNOWN",
            total=total,
            currency=currency,
            is_preview=False,
            next_actions=[
                f"Sales order created with ID {so.id}",
                "Use fulfill_order to ship items when ready",
            ],
            message=f"Successfully created sales order {so.order_no} (ID: {so.id})",
        )

    except Exception as e:
        logger.error(f"Failed to create sales order: {e}")
        raise


@observe_tool
@unpack_pydantic_params
async def create_sales_order(
    request: Annotated[CreateSalesOrderRequest, Unpack()], context: Context
) -> ToolResult:
    """Create a sales order for a customer purchase.

    Two-step flow: confirm=false to preview totals, confirm=true to create.
    Requires customer_id, order_number, and at least one line item with
    variant_id and quantity. Supports optional pricing overrides, discounts,
    delivery dates, and billing/shipping addresses.
    """
    from katana_mcp.tools.prefab_ui import (
        build_order_created_ui,
        build_order_preview_ui,
        call_tool_from_request,
    )

    response = await _create_sales_order_impl(request, context)

    order_dict = response.model_dump()
    if response.is_preview:
        ui = build_order_preview_ui(
            order_dict,
            "Sales Order",
            request=request.model_dump(),
            confirm_action=call_tool_from_request(
                "create_sales_order",
                CreateSalesOrderRequest,
                overrides={"confirm": True},
            ),
        )
    else:
        ui = build_order_created_ui(order_dict, "Sales Order")

    return make_tool_result(response, ui=ui)


# ============================================================================
# Tool 2: list_sales_orders
# ============================================================================


class ListSalesOrdersRequest(BaseModel):
    """Request to list/filter sales orders (list-tool pattern v2)."""

    # Paging
    limit: int = Field(
        default=50,
        ge=1,
        le=250,
        description=(
            "Max orders to return (default 50, min 1, max 250 — Katana's "
            "per-page ceiling). When `page` is set, acts as the page size "
            "for that request."
        ),
    )
    page: int | None = Field(
        default=None,
        ge=1,
        description=(
            "Page number (1-based). When set, returns a single page and "
            "disables auto-pagination; `limit` becomes the page size for "
            "that request."
        ),
    )

    # Domain filters
    order_no: str | None = Field(default=None, description="Filter by exact order_no")
    ids: CoercedIntListOpt = Field(
        default=None,
        description=(
            "Filter by explicit list of sales order IDs. "
            "JSON array of integers, e.g. [101, 202, 303]."
        ),
    )
    customer_id: int | None = Field(default=None, description="Filter by customer ID")
    location_id: int | None = Field(default=None, description="Filter by location ID")
    status: str | None = Field(
        default=None, description="Filter by sales order status (e.g. NOT_SHIPPED)"
    )
    production_status: str | None = Field(
        default=None,
        description="Filter by production status (NONE, NOT_STARTED, IN_PROGRESS, BLOCKED, DONE, NOT_APPLICABLE)",
    )
    invoicing_status: str | None = Field(
        default=None,
        description="Filter by invoicing status (e.g. NOT_INVOICED, INVOICED)",
    )
    currency: str | None = Field(
        default=None, description="Filter by currency code (e.g. 'USD')"
    )
    include_deleted: bool | None = Field(
        default=None,
        description="When true, include soft-deleted sales orders in the results.",
    )
    needs_work_orders: bool = Field(
        default=False,
        description="Convenience: filter to orders with production_status=NONE (no MOs created yet)",
    )

    # Time-window filters (server-side on Katana)
    created_after: str | None = Field(
        default=None, description="ISO-8601 datetime lower bound on created_at."
    )
    created_before: str | None = Field(
        default=None, description="ISO-8601 datetime upper bound on created_at."
    )
    updated_after: str | None = Field(
        default=None, description="ISO-8601 datetime lower bound on updated_at."
    )
    updated_before: str | None = Field(
        default=None, description="ISO-8601 datetime upper bound on updated_at."
    )

    # Time-window filters on delivery_date (applied as indexed SQL range
    # queries against the local cache post-#342).
    delivered_after: str | None = Field(
        default=None,
        description="ISO-8601 datetime lower bound on delivery_date.",
    )
    delivered_before: str | None = Field(
        default=None,
        description="ISO-8601 datetime upper bound on delivery_date.",
    )

    # Row inclusion
    include_rows: bool = Field(
        default=False,
        description=(
            "When true, populate row-level detail (id, variant_id, quantity, "
            "price_per_unit, linked_manufacturing_order_id) on each summary "
            "via the `rows` field. `sku` is not resolved in list context — "
            "use `get_sales_order` for SKU-enriched rows on a single order."
        ),
    )

    # Output formatting
    format: Literal["markdown", "json"] = Field(
        default="markdown",
        description=(
            "Output format: 'markdown' (default) for human-readable tables; "
            "'json' for structured data consumable by downstream tools/aggregations."
        ),
    )


class SalesOrderRowInfo(BaseModel):
    """Summary of a sales order line item."""

    id: int
    variant_id: int | None
    sku: str | None
    quantity: float | None
    price_per_unit: float | None
    linked_manufacturing_order_id: int | None


class SalesOrderSummary(BaseModel):
    """Summary row for a sales order in a list."""

    id: int
    order_no: str | None
    customer_id: int | None
    location_id: int | None
    status: str | None
    production_status: str | None
    invoicing_status: str | None
    created_at: str | None
    delivery_date: str | None
    total: float | None
    currency: str | None
    row_count: int
    rows: list[SalesOrderRowInfo] | None = None


class ListSalesOrdersResponse(BaseModel):
    """Response containing a list of sales orders."""

    orders: list[SalesOrderSummary]
    total_count: int
    pagination: PaginationMeta | None = Field(
        default=None,
        description=(
            "Pagination metadata — populated when the caller requests a "
            "specific `page`; `None` otherwise."
        ),
    )


_SALES_ORDER_DATE_FIELDS = (
    "created_after",
    "created_before",
    "updated_after",
    "updated_before",
    "delivered_after",
    "delivered_before",
)


def _apply_sales_order_filters(
    stmt: Any,
    request: ListSalesOrdersRequest,
    parsed_dates: dict[str, datetime | None],
) -> Any:
    """Translate request filters into WHERE clauses on a ``SalesOrder`` query.

    Shared by the data SELECT and the COUNT SELECT so pagination totals
    reflect exactly the same filter set as the data rows. ``parsed_dates``
    must come from :func:`parse_request_dates` — keeping parsing out of
    this function lets the paginated path avoid re-parsing on the COUNT
    query.
    """
    from katana_public_api_client.models_pydantic._generated import (
        CachedSalesOrder,
        SalesOrderProductionStatus,
        SalesOrderStatus,
    )

    production_status = request.production_status
    if production_status is None and request.needs_work_orders:
        production_status = "NONE"

    if request.order_no is not None:
        stmt = stmt.where(CachedSalesOrder.order_no == request.order_no)
    if request.ids is not None:
        stmt = stmt.where(CachedSalesOrder.id.in_(request.ids))
    if request.customer_id is not None:
        stmt = stmt.where(CachedSalesOrder.customer_id == request.customer_id)
    if request.location_id is not None:
        stmt = stmt.where(CachedSalesOrder.location_id == request.location_id)
    if request.status is not None:
        stmt = stmt.where(
            CachedSalesOrder.status
            == coerce_enum(request.status, SalesOrderStatus, "status")
        )
    if production_status is not None:
        stmt = stmt.where(
            CachedSalesOrder.production_status
            == coerce_enum(
                production_status, SalesOrderProductionStatus, "production_status"
            )
        )
    if request.invoicing_status is not None:
        stmt = stmt.where(CachedSalesOrder.invoicing_status == request.invoicing_status)
    if request.currency is not None:
        stmt = stmt.where(CachedSalesOrder.currency == request.currency)
    if not request.include_deleted:
        stmt = stmt.where(CachedSalesOrder.deleted_at.is_(None))

    return apply_date_window_filters(
        stmt,
        parsed_dates,
        ge_pairs={
            "created_after": CachedSalesOrder.created_at,
            "updated_after": CachedSalesOrder.updated_at,
            "delivered_after": CachedSalesOrder.delivery_date,
        },
        le_pairs={
            "created_before": CachedSalesOrder.created_at,
            "updated_before": CachedSalesOrder.updated_at,
            "delivered_before": CachedSalesOrder.delivery_date,
        },
    )


async def _list_sales_orders_impl(
    request: ListSalesOrdersRequest, context: Context
) -> ListSalesOrdersResponse:
    """List sales orders with filters via the typed cache.

    ``ensure_sales_orders_synced`` runs an incremental ``updated_at_min``
    delta (debounced — see :data:`_SYNC_DEBOUNCE`); the query then
    translates request filters into indexed SQL and returns results
    directly. See ADR-0018.
    """
    from sqlalchemy.orm import selectinload
    from sqlmodel import func, select

    from katana_mcp.typed_cache import ensure_sales_orders_synced
    from katana_public_api_client.models_pydantic._generated import (
        CachedSalesOrder,
        CachedSalesOrderRow,
    )

    services = get_services(context)

    await ensure_sales_orders_synced(services.client, services.typed_cache)

    parsed_dates = parse_request_dates(request, _SALES_ORDER_DATE_FIELDS)

    # When ``include_rows`` is set, ``selectinload`` eager-loads the
    # children, so ``len(so.sales_order_rows)`` is free at materialization
    # time and we skip the correlated COUNT subquery entirely.
    if request.include_rows:
        stmt = select(CachedSalesOrder).options(
            selectinload(CachedSalesOrder.sales_order_rows)
        )
    else:
        row_count_subq = (
            select(func.count(CachedSalesOrderRow.id))
            .where(CachedSalesOrderRow.sales_order_id == CachedSalesOrder.id)
            .correlate(CachedSalesOrder)
            .scalar_subquery()
            .label("row_count")
        )
        stmt = select(CachedSalesOrder, row_count_subq)
    stmt = _apply_sales_order_filters(stmt, request, parsed_dates)
    stmt = stmt.order_by(CachedSalesOrder.created_at.desc(), CachedSalesOrder.id.desc())
    if request.page is not None:
        stmt = stmt.offset((request.page - 1) * request.limit).limit(request.limit)
    else:
        stmt = stmt.limit(request.limit)

    async with services.typed_cache.session() as session:
        data_result = await session.exec(stmt)
        if request.include_rows:
            cached_orders = list(data_result.all())
            orders_with_counts: list[tuple[CachedSalesOrder, int]] = [
                (so, len(so.sales_order_rows)) for so in cached_orders
            ]
        else:
            orders_with_counts = data_result.all()

        pagination: PaginationMeta | None = None
        if request.page is not None:
            # Re-apply the same filter predicate to the COUNT so totals
            # never disagree with the data set.
            count_stmt = _apply_sales_order_filters(
                select(func.count()).select_from(CachedSalesOrder),
                request,
                parsed_dates,
            )
            total_records = (await session.exec(count_stmt)).one()
            total_pages = (total_records + request.limit - 1) // request.limit
            pagination = PaginationMeta(
                total_records=total_records,
                total_pages=total_pages,
                page=request.page,
                first_page=request.page == 1,
                last_page=request.page >= total_pages,
            )

    # ``sku`` stays None — resolving it would require a variant lookup
    # per row and defeat the single-query win.
    orders: list[SalesOrderSummary] = []
    for so, row_count in orders_with_counts:
        row_infos: list[SalesOrderRowInfo] | None = None
        if request.include_rows:
            row_infos = [
                SalesOrderRowInfo(
                    id=r.id,
                    variant_id=r.variant_id,
                    sku=None,
                    quantity=r.quantity,
                    price_per_unit=r.price_per_unit,
                    linked_manufacturing_order_id=r.linked_manufacturing_order_id,
                )
                for r in so.sales_order_rows
            ]
        orders.append(
            SalesOrderSummary(
                id=so.id,
                order_no=so.order_no,
                customer_id=so.customer_id,
                location_id=so.location_id,
                status=enum_to_str(so.status),
                production_status=enum_to_str(so.production_status),
                invoicing_status=so.invoicing_status,
                created_at=iso_or_none(so.created_at),
                delivery_date=iso_or_none(so.delivery_date),
                total=so.total,
                currency=so.currency,
                row_count=row_count,
                rows=row_infos,
            )
        )

    return ListSalesOrdersResponse(
        orders=orders, total_count=len(orders), pagination=pagination
    )


@observe_tool
@unpack_pydantic_params
async def list_sales_orders(
    request: Annotated[ListSalesOrdersRequest, Unpack()], context: Context
) -> ToolResult:
    """List sales orders with filters — pass `ids=[1,2,3]` to fetch a specific batch by ID (cache-backed, indexed SQL).

    Use this for discovery workflows — find recent orders, orders needing work
    orders, orders for a specific customer, etc. Returns summary info (order_no,
    status, production_status, totals, row count).

    **Common filters:**
    - `needs_work_orders=true` — orders with no MOs yet (production_status=NONE)
    - `status="NOT_SHIPPED"` — unshipped orders
    - `customer_id=N` — orders for a specific customer

    **Time windows** — all applied as indexed SQL range queries against
    the local cache (post-#342 cache-back):
    - `created_after` / `created_before` — bounds on `created_at`
    - `updated_after` / `updated_before` — bounds on `updated_at`
    - `delivered_after` / `delivered_before` — bounds on `delivery_date`

    **Row detail:**
    - `include_rows=true` — populate per-order row details (id, variant_id,
      quantity, price_per_unit, linked_manufacturing_order_id). `sku` is left
      None in list context; use `get_sales_order` for SKU-enriched rows on a
      specific order.
    """
    from katana_mcp.tools.tool_result_utils import make_simple_result

    response = await _list_sales_orders_impl(request, context)

    if request.format == "json":
        return ToolResult(
            content=response.model_dump_json(indent=2),
            structured_content=response.model_dump(),
        )

    if not response.orders:
        md = "No sales orders match the given filters."
    else:
        table = format_md_table(
            headers=["Order #", "Status", "Production", "Rows", "Total", "Created"],
            rows=[
                [
                    o.order_no or o.id,
                    o.status or "—",
                    o.production_status or "—",
                    o.row_count,
                    f"{o.total:.2f} {o.currency or ''}" if o.total is not None else "—",
                    o.created_at or "—",
                ]
                for o in response.orders
            ],
        )
        md = f"## Sales Orders ({response.total_count})\n\n{table}"

    if response.pagination is not None:
        p = response.pagination
        if p.page is not None and p.total_pages is not None:
            summary = f"\n\nPage {p.page} of {p.total_pages}"
            if p.total_records is not None:
                summary += f" (total: {p.total_records} records)"
            md += summary

    return make_simple_result(md, structured_data=response.model_dump())


# ============================================================================
# Tool 3: get_sales_order
# ============================================================================


class GetSalesOrderRequest(BaseModel):
    """Request to look up a single sales order with line items."""

    order_no: str | None = Field(default=None, description="Sales order number")
    order_id: int | None = Field(default=None, description="Sales order ID")
    format: Literal["markdown", "json"] = Field(
        default="markdown",
        description=(
            "Output format: 'markdown' (default) for human-readable tables; "
            "'json' for structured data consumable by downstream tools/aggregations."
        ),
    )


class SalesOrderRowDetail(BaseModel):
    """Full sales order row — every field on ``SalesOrderRow`` surfaced.

    Used inside ``GetSalesOrderResponse.rows`` where we want the exhaustive
    row-level detail. ``SalesOrderRowInfo`` (used by list_sales_orders) stays
    summary-shaped so the list tool remains compact.
    """

    id: int
    variant_id: int | None = None
    sku: str | None = None
    quantity: float | None = None
    sales_order_id: int | None = None
    tax_rate_id: int | None = None
    tax_rate: float | None = None
    location_id: int | None = None
    product_availability: str | None = None
    product_expected_date: str | None = None
    price_per_unit: float | None = None
    price_per_unit_in_base_currency: float | None = None
    total: float | None = None
    total_in_base_currency: float | None = None
    total_discount: str | None = None
    cogs_value: float | None = None
    linked_manufacturing_order_id: int | None = None
    conversion_rate: float | None = None
    conversion_date: str | None = None
    serial_numbers: list[int] = Field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None
    deleted_at: str | None = None


class SalesOrderAddressInfo(BaseModel):
    """Full sales order address — one entry in ``GetSalesOrderResponse.addresses``.

    Mirrors every field on the ``SalesOrderAddress`` attrs model. The attrs
    field ``zip_`` is a Python keyword workaround; the wire format (and this
    Pydantic field) is ``zip``.
    """

    id: int
    sales_order_id: int | None = None
    entity_type: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    company: str | None = None
    phone: str | None = None
    line_1: str | None = None
    line_2: str | None = None
    city: str | None = None
    state: str | None = None
    zip: str | None = None
    country: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    deleted_at: str | None = None


class SalesOrderShippingFeeInfo(BaseModel):
    """Shipping fee block — mirrors the ``SalesOrderShippingFee`` attrs model."""

    id: int
    sales_order_id: int | None = None
    amount: str | None = None
    tax_rate_id: int | None = None
    description: str | None = None


class GetSalesOrderResponse(BaseModel):
    """Full sales order details. Exhaustive — every field Katana exposes on
    ``SalesOrder`` is surfaced (including nested rows, addresses, and
    shipping fee) so callers don't need follow-up lookups for standard fields.
    """

    # Identifiers / header
    id: int
    order_no: str | None = None
    customer_id: int | None = None
    location_id: int | None = None
    source: str | None = None
    order_created_date: str | None = None

    # Status / workflow
    status: str | None = None
    production_status: str | None = None
    invoicing_status: str | None = None
    product_availability: str | None = None
    product_expected_date: str | None = None
    ingredient_availability: str | None = None
    ingredient_expected_date: str | None = None

    # Dates
    delivery_date: str | None = None
    picked_date: str | None = None

    # Money
    currency: str | None = None
    total: float | None = None
    total_in_base_currency: float | None = None
    conversion_rate: float | None = None
    conversion_date: str | None = None

    # Notes / reference
    additional_info: str | None = None
    customer_ref: str | None = None

    # Tracking
    tracking_number: str | None = None
    tracking_number_url: str | None = None

    # Addresses — both the ID pointers on the SO and the full resolved list
    billing_address_id: int | None = None
    shipping_address_id: int | None = None
    addresses: list[SalesOrderAddressInfo] = Field(default_factory=list)

    # Linked resources
    linked_manufacturing_order_id: int | None = None
    shipping_fee: SalesOrderShippingFeeInfo | None = None

    # Ecommerce metadata
    ecommerce_order_type: str | None = None
    ecommerce_store_name: str | None = None
    ecommerce_order_id: str | None = None

    # Timestamps
    created_at: str | None = None
    updated_at: str | None = None
    deleted_at: str | None = None

    # Line items — exhaustive per-row detail
    rows: list[SalesOrderRowDetail] = Field(default_factory=list)


def _shipping_fee_from_attrs(fee: Any) -> SalesOrderShippingFeeInfo | None:
    """Build a SalesOrderShippingFeeInfo from a populated attrs fee or None.

    Callers must pre-unwrap the attrs field (via ``unwrap_unset(obj.shipping_fee,
    None)``) so this helper only receives ``None`` or a populated object —
    passing the raw UNSET sentinel would AttributeError on ``.id``.
    """
    if fee is None:
        return None
    return SalesOrderShippingFeeInfo(
        id=fee.id,
        sales_order_id=fee.sales_order_id,
        amount=unwrap_unset(fee.amount, None),
        tax_rate_id=unwrap_unset(fee.tax_rate_id, None),
        description=unwrap_unset(fee.description, None),
    )


async def _fetch_sales_order_addresses(
    services: Any, sales_order_id: int
) -> list[SalesOrderAddressInfo]:
    """Fetch all addresses for a sales order via /sales_order_addresses.

    SOs aren't cached today (per #342 they're transactional), so this is a
    fetch-on-demand call alongside the SO lookup. Returns the full list of
    addresses linked to ``sales_order_id``.
    """
    from katana_public_api_client.api.sales_order_address import (
        get_all_sales_order_addresses,
    )
    from katana_public_api_client.utils import unwrap_data

    response = await get_all_sales_order_addresses.asyncio_detailed(
        client=services.client,
        sales_order_ids=[sales_order_id],
        limit=250,
    )
    rows = unwrap_data(response, default=[])
    result: list[SalesOrderAddressInfo] = []
    for row in rows:
        row_dict = row.to_dict() if hasattr(row, "to_dict") else row
        # The attrs model uses ``zip_`` as a Python keyword workaround; the
        # API wire format is ``zip``. ``to_dict()`` emits the wire name.
        result.append(
            SalesOrderAddressInfo(
                id=row_dict.get("id", 0),
                sales_order_id=row_dict.get("sales_order_id"),
                entity_type=row_dict.get("entity_type"),
                first_name=row_dict.get("first_name"),
                last_name=row_dict.get("last_name"),
                company=row_dict.get("company"),
                phone=row_dict.get("phone"),
                line_1=row_dict.get("line_1"),
                line_2=row_dict.get("line_2"),
                city=row_dict.get("city"),
                state=row_dict.get("state"),
                zip=row_dict.get("zip"),
                country=row_dict.get("country"),
                # to_dict() has already serialized these to ISO strings;
                # iso_or_none expects datetime and would AttributeError.
                created_at=row_dict.get("created_at"),
                updated_at=row_dict.get("updated_at"),
                deleted_at=row_dict.get("deleted_at"),
            )
        )
    return result


async def _get_sales_order_impl(
    request: GetSalesOrderRequest, context: Context
) -> GetSalesOrderResponse:
    """Look up a single sales order by order_no or order_id with line items.

    Exhaustive response — every field Katana exposes on ``SalesOrder`` (plus
    nested rows, addresses, and shipping fee) is surfaced so callers don't
    need follow-up lookups for standard fields. SO is not cached today (#342
    covers the cache migration), so this keeps the same SO lookup path the
    prior impl used and adds a fetch-on-demand for addresses.
    """
    from katana_public_api_client.api.sales_order import (
        get_all_sales_orders,
        get_sales_order as api_get_sales_order,
    )
    from katana_public_api_client.models import SalesOrder
    from katana_public_api_client.utils import unwrap_as, unwrap_data

    if not request.order_no and not request.order_id:
        raise ValueError("Either order_no or order_id must be provided")

    services = get_services(context)

    if request.order_id:
        response = await api_get_sales_order.asyncio_detailed(
            id=request.order_id, client=services.client
        )
        so = unwrap_as(response, SalesOrder)
    else:
        if not request.order_no:
            raise ValueError("order_no is required when order_id is not provided")
        list_response = await get_all_sales_orders.asyncio_detailed(
            client=services.client, order_no=request.order_no, limit=1
        )
        orders = unwrap_data(list_response, default=[])
        if not orders:
            raise ValueError(f"Sales order '{request.order_no}' not found")
        so = orders[0]

    raw_rows = unwrap_unset(so.sales_order_rows, [])

    # Parallelize variant lookups across all rows (N+1 fix) AND the address
    # fetch — both depend only on the SO we just loaded.
    variant_ids = [unwrap_unset(r.variant_id, None) for r in raw_rows]
    variants, addresses = await asyncio.gather(
        asyncio.gather(
            *(
                services.cache.get_by_id(EntityType.VARIANT, v_id)
                if v_id is not None
                else none_coro()
                for v_id in variant_ids
            )
        ),
        _fetch_sales_order_addresses(services, so.id),
    )

    row_details: list[SalesOrderRowDetail] = []
    for r, variant in zip(raw_rows, variants, strict=True):
        row_details.append(
            SalesOrderRowDetail(
                id=r.id,
                variant_id=unwrap_unset(r.variant_id, None),
                sku=variant.get("sku") if variant else None,
                quantity=unwrap_unset(r.quantity, None),
                sales_order_id=unwrap_unset(r.sales_order_id, None),
                tax_rate_id=unwrap_unset(r.tax_rate_id, None),
                tax_rate=unwrap_unset(r.tax_rate, None),
                location_id=unwrap_unset(r.location_id, None),
                product_availability=enum_to_str(
                    unwrap_unset(r.product_availability, None)
                ),
                product_expected_date=iso_or_none(
                    unwrap_unset(r.product_expected_date, None)
                ),
                price_per_unit=unwrap_unset(r.price_per_unit, None),
                price_per_unit_in_base_currency=unwrap_unset(
                    r.price_per_unit_in_base_currency, None
                ),
                total=unwrap_unset(r.total, None),
                total_in_base_currency=unwrap_unset(r.total_in_base_currency, None),
                total_discount=unwrap_unset(r.total_discount, None),
                cogs_value=unwrap_unset(r.cogs_value, None),
                linked_manufacturing_order_id=unwrap_unset(
                    r.linked_manufacturing_order_id, None
                ),
                conversion_rate=unwrap_unset(r.conversion_rate, None),
                conversion_date=iso_or_none(unwrap_unset(r.conversion_date, None)),
                serial_numbers=unwrap_unset(r.serial_numbers, []),
                created_at=iso_or_none(unwrap_unset(r.created_at, None)),
                updated_at=iso_or_none(unwrap_unset(r.updated_at, None)),
                deleted_at=iso_or_none(unwrap_unset(r.deleted_at, None)),
            )
        )

    return GetSalesOrderResponse(
        id=so.id,
        order_no=unwrap_unset(so.order_no, None),
        customer_id=unwrap_unset(so.customer_id, None),
        location_id=unwrap_unset(so.location_id, None),
        source=unwrap_unset(so.source, None),
        order_created_date=iso_or_none(unwrap_unset(so.order_created_date, None)),
        status=enum_to_str(unwrap_unset(so.status, None)),
        production_status=enum_to_str(unwrap_unset(so.production_status, None)),
        invoicing_status=unwrap_unset(so.invoicing_status, None),
        product_availability=enum_to_str(unwrap_unset(so.product_availability, None)),
        product_expected_date=iso_or_none(unwrap_unset(so.product_expected_date, None)),
        ingredient_availability=enum_to_str(
            unwrap_unset(so.ingredient_availability, None)
        ),
        ingredient_expected_date=iso_or_none(
            unwrap_unset(so.ingredient_expected_date, None)
        ),
        delivery_date=iso_or_none(unwrap_unset(so.delivery_date, None)),
        picked_date=iso_or_none(unwrap_unset(so.picked_date, None)),
        currency=unwrap_unset(so.currency, None),
        total=unwrap_unset(so.total, None),
        total_in_base_currency=unwrap_unset(so.total_in_base_currency, None),
        conversion_rate=unwrap_unset(so.conversion_rate, None),
        conversion_date=iso_or_none(unwrap_unset(so.conversion_date, None)),
        additional_info=unwrap_unset(so.additional_info, None),
        customer_ref=unwrap_unset(so.customer_ref, None),
        tracking_number=unwrap_unset(so.tracking_number, None),
        tracking_number_url=unwrap_unset(so.tracking_number_url, None),
        billing_address_id=unwrap_unset(so.billing_address_id, None),
        shipping_address_id=unwrap_unset(so.shipping_address_id, None),
        addresses=addresses,
        linked_manufacturing_order_id=unwrap_unset(
            so.linked_manufacturing_order_id, None
        ),
        shipping_fee=_shipping_fee_from_attrs(unwrap_unset(so.shipping_fee, None)),
        ecommerce_order_type=unwrap_unset(so.ecommerce_order_type, None),
        ecommerce_store_name=unwrap_unset(so.ecommerce_store_name, None),
        ecommerce_order_id=unwrap_unset(so.ecommerce_order_id, None),
        created_at=iso_or_none(unwrap_unset(so.created_at, None)),
        updated_at=iso_or_none(unwrap_unset(so.updated_at, None)),
        deleted_at=iso_or_none(unwrap_unset(so.deleted_at, None)),
        rows=row_details,
    )


# Scalar fields rendered in order at the top of the markdown response.
# Labels use canonical Pydantic names so LLM consumers can't confuse a
# rendered section header with the field name (see #346 follow-on).
_GET_SO_SCALAR_FIELDS: tuple[str, ...] = (
    "id",
    "order_no",
    "customer_id",
    "location_id",
    "source",
    "status",
    "production_status",
    "invoicing_status",
    "product_availability",
    "product_expected_date",
    "ingredient_availability",
    "ingredient_expected_date",
    "order_created_date",
    "delivery_date",
    "picked_date",
    "currency",
    "total",
    "total_in_base_currency",
    "conversion_rate",
    "conversion_date",
    "customer_ref",
    "additional_info",
    "tracking_number",
    "tracking_number_url",
    "billing_address_id",
    "shipping_address_id",
    "linked_manufacturing_order_id",
    "ecommerce_order_type",
    "ecommerce_store_name",
    "ecommerce_order_id",
    "created_at",
    "updated_at",
    "deleted_at",
)

# Per-address fields rendered (in order) under an ``addresses`` block.
_ADDRESS_FIELDS: tuple[str, ...] = (
    "sales_order_id",
    "entity_type",
    "first_name",
    "last_name",
    "company",
    "phone",
    "line_1",
    "line_2",
    "city",
    "state",
    "zip",
    "country",
    "created_at",
    "updated_at",
    "deleted_at",
)

# Per-row fields rendered under a ``rows`` block. ``id`` + ``variant_id`` /
# ``sku`` are emitted first as the row header; the rest are indented beneath.
_ROW_HEADER_FIELDS: tuple[str, ...] = ("variant_id", "sku")
_ROW_BODY_FIELDS: tuple[str, ...] = (
    "sales_order_id",
    "quantity",
    "price_per_unit",
    "price_per_unit_in_base_currency",
    "total",
    "total_in_base_currency",
    "total_discount",
    "tax_rate_id",
    "tax_rate",
    "location_id",
    "product_availability",
    "product_expected_date",
    "cogs_value",
    "linked_manufacturing_order_id",
    "conversion_rate",
    "conversion_date",
    "serial_numbers",
    "created_at",
    "updated_at",
    "deleted_at",
)


def _render_address_md(addr: SalesOrderAddressInfo) -> str:
    """Render one address as an indented multi-line block with canonical labels."""
    lines = [f"  - **id**: {addr.id}"]
    for fname in _ADDRESS_FIELDS:
        val = getattr(addr, fname)
        if val is None or val == "":
            continue
        lines.append(f"    **{fname}**: {val}")
    return "\n".join(lines)


def _render_row_md(row: SalesOrderRowDetail) -> str:
    """Render one sales order row as an indented multi-line block with canonical labels."""
    lines = [f"  - **id**: {row.id}"]
    for fname in _ROW_HEADER_FIELDS + _ROW_BODY_FIELDS:
        val = getattr(row, fname)
        # Empty serial_numbers list is noise — skip it. Non-empty lists render
        # with explicit [...] syntax so an LLM reading the output can tell
        # the field is a list.
        if val is None or val == "" or (isinstance(val, list) and not val):
            continue
        lines.append(f"    **{fname}**: {val}")
    return "\n".join(lines)


@observe_tool
@unpack_pydantic_params
async def get_sales_order(
    request: Annotated[GetSalesOrderRequest, Unpack()], context: Context
) -> ToolResult:
    """Look up a sales order by number or ID with all line items.

    For multiple sales orders at once, use ``list_sales_orders(ids=[...])`` —
    it returns a summary table and supports all the same filters.

    Returns every field Katana exposes on the sales order record — identity,
    status/workflow flags, dates, totals, tracking, ecommerce metadata,
    timestamps — plus the full list of associated billing/shipping addresses
    (fetched on-demand via /sales_order_addresses, since SOs aren't cached)
    and exhaustive per-row detail (variant, SKU via variant cache, pricing,
    linked manufacturing order, batch tracking, serial numbers). Use with
    `list_sales_orders` for discovery; this is the single-call path to the rest.
    """
    from katana_mcp.tools.tool_result_utils import make_simple_result

    response = await _get_sales_order_impl(request, context)

    if request.format == "json":
        return ToolResult(
            content=response.model_dump_json(indent=2),
            structured_content=response.model_dump(),
        )

    # Labels use canonical Pydantic field names so LLM consumers can't
    # confuse a section header with the field name (see #346 follow-on).
    header = f"## Sales Order {response.order_no or response.id}"
    md_lines: list[str] = [header]
    for fname in _GET_SO_SCALAR_FIELDS:
        val = getattr(response, fname)
        if val is None or val == "":
            continue
        md_lines.append(f"**{fname}**: {val}")

    # shipping_fee is a nested object — render its canonical fields inline.
    if response.shipping_fee is not None:
        md_lines.append("")
        md_lines.append("**shipping_fee**:")
        fee = response.shipping_fee
        md_lines.append(f"  **id**: {fee.id}")
        for fname in ("sales_order_id", "amount", "tax_rate_id", "description"):
            fval = getattr(fee, fname)
            if fval is None or fval == "":
                continue
            md_lines.append(f"  **{fname}**: {fval}")

    # Addresses — explicit [] when empty, count + per-address blocks when populated.
    md_lines.append("")
    if response.addresses:
        md_lines.append(f"**addresses** ({len(response.addresses)}):")
        for addr in response.addresses:
            md_lines.append(_render_address_md(addr))
    else:
        md_lines.append("**addresses**: []")

    # Rows — same shape as addresses (explicit [] / count + per-row blocks).
    md_lines.append("")
    if response.rows:
        md_lines.append(f"**rows** ({len(response.rows)}):")
        for row in response.rows:
            md_lines.append(_render_row_md(row))
    else:
        md_lines.append("**rows**: []")

    return make_simple_result(
        "\n".join(md_lines), structured_data=response.model_dump()
    )


def register_tools(mcp: FastMCP) -> None:
    """Register all sales order tools with the FastMCP instance.

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

    mcp.tool(
        tags={"orders", "sales", "write"},
        annotations=ToolAnnotations(
            readOnlyHint=False, destructiveHint=False, openWorldHint=True
        ),
        meta=UI_META,
    )(create_sales_order)
    mcp.tool(
        tags={"orders", "sales", "read"},
        annotations=_read,
    )(list_sales_orders)
    mcp.tool(
        tags={"orders", "sales", "read"},
        annotations=_read,
    )(get_sales_order)
