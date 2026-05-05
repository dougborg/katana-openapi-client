"""Sales order management tools for Katana MCP Server.

Foundation tools covering the sales-order lifecycle: create, list, get
(read-mostly tools), plus the unified modify/delete pair.

Tools:
- create_sales_order: Create sales orders with preview/apply pattern
- list_sales_orders / get_sales_order: discovery + exhaustive read
- modify_sales_order: header + row CRUD + addresses + fulfillments +
  shipping-fee CRUD via typed sub-payload slots
- delete_sales_order: destructive sibling of modify_sales_order
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated, Any, Literal

from fastmcp import Context, FastMCP
from fastmcp.tools import ToolResult
from pydantic import BaseModel, ConfigDict, Field

from katana_mcp.cache import EntityType
from katana_mcp.logging import get_logger, observe_tool
from katana_mcp.services import get_services
from katana_mcp.tools._modification import (
    ConfirmableRequest,
    ModificationResponse,
    compute_field_diff,
    make_response_verifier,
    to_tool_result,
)
from katana_mcp.tools._modification_dispatch import (
    ActionSpec,
    has_any_subpayload,
    make_delete_apply,
    make_patch_apply,
    make_post_apply,
    plan_creates,
    plan_deletes,
    plan_updates,
    run_delete_plan,
    run_modify_plan,
    safe_fetch_for_diff,
    unset_dict,
)
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
    parse_request_dates,
    resolve_entity_name,
)
from katana_mcp.unpack import Unpack, unpack_pydantic_params
from katana_mcp.web_urls import katana_web_url

# Modify/delete API endpoints used by ``modify_sales_order`` /
# ``delete_sales_order``. Hoisted to module scope for declarative dependency
# tracking and consistency with the rest of the codebase.
from katana_public_api_client.api.sales_order import (
    delete_sales_order as api_delete_sales_order,
    get_sales_order as api_get_sales_order,
    update_sales_order as api_update_sales_order,
)
from katana_public_api_client.api.sales_order_address import (
    create_sales_order_address as api_create_so_address,
    delete_sales_order_address as api_delete_so_address,
    update_sales_order_address as api_update_so_address,
)
from katana_public_api_client.api.sales_order_fulfillment import (
    create_sales_order_fulfillment as api_create_so_fulfillment,
    delete_sales_order_fulfillment as api_delete_so_fulfillment,
    get_sales_order_fulfillment as api_get_so_fulfillment,
    update_sales_order_fulfillment as api_update_so_fulfillment,
)
from katana_public_api_client.api.sales_order_row import (
    create_sales_order_row as api_create_so_row,
    delete_sales_order_row as api_delete_so_row,
    get_sales_order_row as api_get_so_row,
    update_sales_order_row as api_update_so_row,
)
from katana_public_api_client.api.sales_orders import (
    create_sales_order_shipping_fee as api_create_so_shipping_fee,
    delete_sales_order_shipping_fee as api_delete_so_shipping_fee,
    get_sales_order_shipping_fee as api_get_so_shipping_fee,
    update_sales_order_shipping_fee as api_update_so_shipping_fee,
)
from katana_public_api_client.client_types import UNSET, Unset
from katana_public_api_client.domain.converters import to_unset, unwrap_unset
from katana_public_api_client.models import (
    AddressEntityType,
    CreateSalesOrderAddressRequest as APICreateSOAddressRequest,
    CreateSalesOrderFulfillmentRequest as APICreateSOFulfillmentRequest,
    CreateSalesOrderRequest as APICreateSalesOrderRequest,
    CreateSalesOrderRequestSalesOrderRowsItem,
    CreateSalesOrderRowRequest as APICreateSORowRequest,
    CreateSalesOrderShippingFeeRequest as APICreateSOShippingFeeRequest,
    CreateSalesOrderStatus,
    SalesOrder,
    SalesOrderAddress as APISalesOrderAddress,
    SalesOrderFulfillment,
    SalesOrderFulfillmentRowRequest,
    SalesOrderFulfillmentStatus,
    SalesOrderRow,
    SalesOrderShippingFee,
    UpdateSalesOrderAddressRequest as APIUpdateSOAddressRequest,
    UpdateSalesOrderFulfillmentRequest as APIUpdateSOFulfillmentRequest,
    UpdateSalesOrderRequest as APIUpdateSalesOrderRequest,
    UpdateSalesOrderRowRequest as APIUpdateSORowRequest,
    UpdateSalesOrderShippingFeeRequest as APIUpdateSOShippingFeeRequest,
    UpdateSalesOrderStatus,
)
from katana_public_api_client.utils import unwrap_as

logger = get_logger(__name__)


# ============================================================================
# Tool 1: create_sales_order
# ============================================================================


class SalesOrderItem(BaseModel):
    """Line item for a sales order."""

    model_config = ConfigDict(extra="forbid")

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

    model_config = ConfigDict(extra="forbid")

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

    model_config = ConfigDict(extra="forbid")

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
    preview: bool = Field(
        default=True,
        description="If true (default), returns preview. If false, creates order.",
    )


class SalesOrderResponse(BaseModel):
    """Response from creating a sales order."""

    id: int | None = None
    order_number: str
    customer_id: int
    customer_name: str | None = None
    location_id: int | None = None
    status: str | None = None
    total: float | None = None
    currency: str | None = None
    delivery_date: str | None = None
    item_count: int | None = None
    is_preview: bool
    warnings: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    message: str
    katana_url: str | None = None


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
        f"{'Previewing' if request.preview else 'Creating'} sales order {request.order_number}"
    )

    # Calculate preview total (estimate based on items with prices)
    total_estimate = sum(
        (item.price_per_unit or 0.0) * item.quantity - (item.total_discount or 0.0)
        for item in request.items
    )

    if request.preview:
        logger.info(
            f"Preview mode: SO {request.order_number} would have {len(request.items)} items"
        )

        services = get_services(context)
        customer_name, cust_warn = await resolve_entity_name(
            services.cache,
            EntityType.CUSTOMER,
            request.customer_id,
            entity_label="Customer",
        )
        warnings: list[str] = [cust_warn] if cust_warn else []
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
            customer_name=customer_name,
            location_id=request.location_id,
            status="PENDING",
            total=total_estimate if total_estimate > 0 else None,
            currency=request.currency,
            delivery_date=request.delivery_date.isoformat()
            if request.delivery_date
            else None,
            item_count=len(request.items),
            is_preview=True,
            warnings=warnings,
            next_actions=[
                "Review the order details",
                "Set preview=false to create the sales order",
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
            katana_url=katana_web_url("sales_order", so.id),
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

    Two-step flow: preview=true (default) to preview totals, preview=false to create.
    Requires customer_id, order_number, and at least one line item with
    variant_id and quantity. Supports optional pricing overrides, discounts,
    delivery dates, and billing/shipping addresses.
    """
    from katana_mcp.tools.prefab_ui import (
        build_order_created_ui,
        build_order_preview_ui,
    )

    response = await _create_sales_order_impl(request, context)

    order_dict = response.model_dump()
    if response.is_preview:
        ui = build_order_preview_ui(
            order_dict,
            "Sales Order",
            confirm_request=request,
            confirm_tool="create_sales_order",
        )
    else:
        ui = build_order_created_ui(order_dict, "Sales Order")

    return make_tool_result(response, ui=ui)


# ============================================================================
# Tool 2: list_sales_orders
# ============================================================================


class ListSalesOrdersRequest(BaseModel):
    """Request to list/filter sales orders (list-tool pattern v2)."""

    model_config = ConfigDict(extra="forbid")

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
    katana_url: str | None = None


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
                katana_url=katana_web_url("sales_order", so.id),
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

    model_config = ConfigDict(extra="forbid")

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
    katana_url: str | None = None
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

    Accepts both attrs ``SalesOrderShippingFee`` and a raw dict: the
    generated ``SalesOrder._parse_shipping_fee`` silently falls through to
    a raw dict cast as the union type when ``SalesOrderShippingFee.from_dict``
    raises (a quirk of openapi-python-client's oneOf codegen). When that
    happens, parse the dict via ``from_dict`` here; if even that fails
    (malformed payload), return ``None`` so the SO assembly completes
    rather than crashing with an opaque ``AttributeError`` (#501).
    """
    if fee is None:
        return None
    if isinstance(fee, dict):
        from katana_public_api_client.models import SalesOrderShippingFee

        try:
            fee = SalesOrderShippingFee.from_dict(fee)
        except (TypeError, ValueError, KeyError, AttributeError):
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

    # One batched IN-clause SQLite read for all row variants, in parallel
    # with the address fetch — both depend only on the SO we just loaded.
    variant_ids = {
        v_id
        for v_id in (unwrap_unset(r.variant_id, None) for r in raw_rows)
        if v_id is not None
    }
    variants, addresses = await asyncio.gather(
        services.cache.get_many_by_ids(EntityType.VARIANT, variant_ids),
        _fetch_sales_order_addresses(services, so.id),
    )

    row_details: list[SalesOrderRowDetail] = []
    for r in raw_rows:
        v_id = unwrap_unset(r.variant_id, None)
        variant = variants.get(v_id) if v_id is not None else None
        row_details.append(
            SalesOrderRowDetail(
                id=r.id,
                variant_id=v_id,
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
        katana_url=katana_web_url("sales_order", so.id),
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


# ============================================================================
# Tool: modify_sales_order — unified modification surface
# ============================================================================


class SOOperation(StrEnum):
    """Operation names emitted on ActionSpecs by ``modify_sales_order`` /
    ``delete_sales_order`` plan builders.
    """

    UPDATE_HEADER = "update_header"
    DELETE = "delete"
    ADD_ROW = "add_row"
    UPDATE_ROW = "update_row"
    DELETE_ROW = "delete_row"
    ADD_ADDRESS = "add_address"
    UPDATE_ADDRESS = "update_address"
    DELETE_ADDRESS = "delete_address"
    ADD_FULFILLMENT = "add_fulfillment"
    UPDATE_FULFILLMENT = "update_fulfillment"
    DELETE_FULFILLMENT = "delete_fulfillment"
    ADD_SHIPPING_FEE = "add_shipping_fee"
    UPDATE_SHIPPING_FEE = "update_shipping_fee"
    DELETE_SHIPPING_FEE = "delete_shipping_fee"


# Tool-facing literals — values match the API StrEnum's ``.value`` directly,
# so ``EnumClass(literal)`` resolves the enum without a lookup table.
SalesOrderStatusLiteral = Literal["NOT_SHIPPED", "PENDING", "PACKED", "DELIVERED"]
FulfillmentStatusLiteral = Literal["DELIVERED", "PACKED"]
AddressEntityTypeLiteral = Literal["billing", "shipping"]


# ----------------------------------------------------------------------------
# Diff-context fetchers
# ----------------------------------------------------------------------------


async def _fetch_sales_order_attrs(services: Any, so_id: int) -> SalesOrder | None:
    return await safe_fetch_for_diff(
        api_get_sales_order, services, so_id, return_type=SalesOrder, label="SO"
    )


async def _fetch_so_row(services: Any, row_id: int) -> SalesOrderRow | None:
    return await safe_fetch_for_diff(
        api_get_so_row, services, row_id, return_type=SalesOrderRow, label="SO row"
    )


async def _fetch_so_fulfillment(
    services: Any, fulfillment_id: int
) -> SalesOrderFulfillment | None:
    return await safe_fetch_for_diff(
        api_get_so_fulfillment,
        services,
        fulfillment_id,
        return_type=SalesOrderFulfillment,
        label="SO fulfillment",
    )


async def _fetch_so_shipping_fee(
    services: Any, fee_id: int
) -> SalesOrderShippingFee | None:
    return await safe_fetch_for_diff(
        api_get_so_shipping_fee,
        services,
        fee_id,
        return_type=SalesOrderShippingFee,
        label="SO shipping fee",
    )


# Note: addresses do not have a get-by-id endpoint (only list-by-SO). Updates
# go through with ``unknown_prior=True`` since we can't cheaply fetch one row.


# ----------------------------------------------------------------------------
# Sub-payload models (typed slots on ModifySalesOrderRequest)
# ----------------------------------------------------------------------------


class SOHeaderPatch(BaseModel):
    """Header fields to patch on an SO. Status is included here — the Katana
    PATCH endpoint accepts it as a regular field."""

    model_config = ConfigDict(extra="forbid")

    order_no: str | None = Field(default=None, description="New SO number")
    customer_id: int | None = Field(default=None, description="New customer ID")
    location_id: int | None = Field(default=None, description="New location ID")
    status: SalesOrderStatusLiteral | None = Field(
        default=None,
        description="New status — NOT_SHIPPED / PENDING / PACKED / DELIVERED",
    )
    currency: str | None = Field(default=None, description="New currency code")
    conversion_rate: float | None = Field(
        default=None, description="New currency conversion rate"
    )
    conversion_date: str | None = Field(
        default=None, description="New conversion date (ISO-8601)"
    )
    order_created_date: datetime | None = Field(
        default=None, description="New order created date"
    )
    delivery_date: datetime | None = Field(
        default=None, description="New delivery date"
    )
    picked_date: datetime | None = Field(default=None, description="New picked date")
    additional_info: str | None = Field(
        default=None, description="New notes / additional info"
    )
    customer_ref: str | None = Field(default=None, description="New customer reference")
    tracking_number: str | None = Field(default=None, description="Tracking number")
    tracking_number_url: str | None = Field(default=None, description="Tracking URL")


class SORowAdd(BaseModel):
    """A new line item to add to the SO."""

    model_config = ConfigDict(extra="forbid")

    variant_id: int = Field(..., description="Variant ID")
    quantity: float = Field(..., description="Quantity", gt=0)
    price_per_unit: float | None = Field(default=None, description="Unit price")
    tax_rate_id: int | None = Field(default=None, description="Tax rate ID")
    location_id: int | None = Field(default=None, description="Location ID")
    total_discount: float | None = Field(default=None, description="Total discount")


class SORowUpdate(BaseModel):
    """Patch to an existing SO row."""

    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., description="Row ID to update")
    variant_id: int | None = Field(default=None, description="New variant ID")
    quantity: float | None = Field(default=None, description="New quantity", gt=0)
    price_per_unit: float | None = Field(default=None, description="New unit price")
    tax_rate_id: int | None = Field(default=None, description="New tax rate ID")
    location_id: int | None = Field(default=None, description="New location ID")
    total_discount: float | None = Field(default=None, description="New discount")


class SOAddressAdd(BaseModel):
    """A new address to attach to the SO."""

    model_config = ConfigDict(extra="forbid")

    entity_type: AddressEntityTypeLiteral = Field(
        ..., description="Address kind — billing or shipping"
    )
    first_name: str | None = Field(default=None)
    last_name: str | None = Field(default=None)
    company: str | None = Field(default=None)
    city: str | None = Field(default=None)
    state: str | None = Field(default=None)
    zip: str | None = Field(default=None)
    country: str | None = Field(default=None)
    phone: str | None = Field(default=None)


class SOAddressUpdate(BaseModel):
    """Patch to an existing SO address. Address get-by-id isn't exposed by
    the Katana API, so previews show every supplied field as
    ``is_unknown_prior=True`` — we can't read the prior values cheaply."""

    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., description="Address ID to update")
    first_name: str | None = Field(default=None)
    last_name: str | None = Field(default=None)
    company: str | None = Field(default=None)
    city: str | None = Field(default=None)
    state: str | None = Field(default=None)
    zip: str | None = Field(default=None)
    country: str | None = Field(default=None)
    phone: str | None = Field(default=None)


class SOFulfillmentRowInput(BaseModel):
    """A row inside a fulfillment — references an SO row + a quantity to fulfill."""

    model_config = ConfigDict(extra="forbid")

    sales_order_row_id: int = Field(..., description="SO row being fulfilled")
    quantity: float = Field(..., description="Quantity fulfilled", gt=0)


class SOFulfillmentAdd(BaseModel):
    """A new fulfillment for the SO."""

    model_config = ConfigDict(extra="forbid")

    status: FulfillmentStatusLiteral = Field(
        ..., description="Fulfillment status — DELIVERED or PACKED"
    )
    sales_order_fulfillment_rows: list[SOFulfillmentRowInput] = Field(
        ..., description="Rows being fulfilled (variant + quantity)", min_length=1
    )
    picked_date: datetime | None = Field(default=None)
    conversion_rate: float | None = Field(default=None)
    conversion_date: datetime | None = Field(default=None)
    tracking_number: str | None = Field(default=None)
    tracking_url: str | None = Field(default=None)
    tracking_carrier: str | None = Field(default=None)
    tracking_method: str | None = Field(default=None)


class SOFulfillmentUpdate(BaseModel):
    """Patch to an existing SO fulfillment."""

    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., description="Fulfillment ID to update")
    status: FulfillmentStatusLiteral | None = Field(default=None)
    picked_date: datetime | None = Field(default=None)
    packer_id: int | None = Field(default=None, description="New packer (operator)")
    conversion_rate: float | None = Field(default=None)
    conversion_date: datetime | None = Field(default=None)
    tracking_number: str | None = Field(default=None)
    tracking_url: str | None = Field(default=None)
    tracking_carrier: str | None = Field(default=None)
    tracking_method: str | None = Field(default=None)


class SOShippingFeeAdd(BaseModel):
    """A new shipping fee to attach to the SO."""

    model_config = ConfigDict(extra="forbid")

    amount: str = Field(..., description="Fee amount (decimal string)")
    description: str | None = Field(default=None)
    tax_rate_id: int | None = Field(default=None)


class SOShippingFeeUpdate(BaseModel):
    """Patch to an existing SO shipping fee.

    Note: Katana's API requires ``amount`` even on PATCH — it's a replace
    semantic on the fee's amount, not a partial update. The other fields
    are genuinely optional.
    """

    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., description="Shipping fee ID to update")
    amount: str = Field(..., description="Fee amount (required by API)")
    description: str | None = Field(default=None)
    tax_rate_id: int | None = Field(default=None)


class ModifySalesOrderRequest(ConfirmableRequest):
    """Unified modification request for a sales order.

    Sub-payload slots span header + rows + addresses + fulfillments +
    shipping fees. Multiple slots can be combined; actions execute in
    canonical order. To remove the SO entirely, use ``delete_sales_order``.
    """

    id: int = Field(..., description="Sales order ID")
    update_header: SOHeaderPatch | None = Field(
        default=None,
        description=(
            "Header-level patch. Fields: order_no, customer_id, location_id, "
            "status (NOT_SHIPPED/PENDING/PACKED/DELIVERED), currency, "
            "conversion_rate, conversion_date, order_created_date, "
            "delivery_date, picked_date, additional_info, customer_ref, "
            "tracking_number, tracking_number_url."
        ),
    )
    add_rows: list[SORowAdd] | None = Field(
        default=None,
        description=(
            "New line items. Each row: variant_id (int, required), quantity "
            "(float, required, >0), price_per_unit, tax_rate_id (see "
            "katana://tax-rates), location_id, total_discount."
        ),
    )
    update_rows: list[SORowUpdate] | None = Field(
        default=None,
        description=(
            "Patches to existing line items. Each entry: id (int, required) + "
            "any subset of variant_id, quantity, price_per_unit, tax_rate_id, "
            "location_id, total_discount."
        ),
    )
    delete_row_ids: list[int] | None = Field(
        default=None,
        description="Row IDs to delete from the SO.",
    )
    add_addresses: list[SOAddressAdd] | None = Field(
        default=None,
        description=(
            "New addresses. Each: entity_type (billing | shipping, required), "
            "first_name, last_name, company, city, state, zip, country, phone."
        ),
    )
    update_addresses: list[SOAddressUpdate] | None = Field(
        default=None,
        description=(
            "Patches to existing addresses. Each entry: id (int, required) + "
            "any subset of first_name, last_name, company, city, state, zip, "
            "country, phone. Katana doesn't expose address get-by-id, so "
            "previews mark every supplied field as is_unknown_prior=True."
        ),
    )
    delete_address_ids: list[int] | None = Field(
        default=None,
        description="Address IDs to delete from the SO.",
    )
    add_fulfillments: list[SOFulfillmentAdd] | None = Field(
        default=None,
        description=(
            "New fulfillments. Each: status (DELIVERED | PACKED, required), "
            "sales_order_fulfillment_rows (list of {sales_order_row_id, "
            "quantity}, required, min_length=1), picked_date, "
            "conversion_rate, conversion_date, tracking_number, tracking_url, "
            "tracking_carrier, tracking_method."
        ),
    )
    update_fulfillments: list[SOFulfillmentUpdate] | None = Field(
        default=None,
        description=(
            "Patches to existing fulfillments. Each entry: id (int, "
            "required) + any subset of status, picked_date, packer_id "
            "(operator — see katana://operators), conversion_rate, "
            "conversion_date, tracking_number, tracking_url, "
            "tracking_carrier, tracking_method."
        ),
    )
    delete_fulfillment_ids: list[int] | None = Field(
        default=None,
        description="Fulfillment IDs to delete from the SO.",
    )
    add_shipping_fees: list[SOShippingFeeAdd] | None = Field(
        default=None,
        description=(
            "New shipping fees. Each: amount (decimal string, required), "
            "description, tax_rate_id (see katana://tax-rates)."
        ),
    )
    update_shipping_fees: list[SOShippingFeeUpdate] | None = Field(
        default=None,
        description=(
            "Patches to existing shipping fees. Each entry: id (int, "
            "required), amount (decimal string, required — Katana semantics "
            "are replace, not partial), description, tax_rate_id."
        ),
    )
    delete_shipping_fee_ids: list[int] | None = Field(
        default=None,
        description="Shipping fee IDs to delete from the SO.",
    )


class DeleteSalesOrderRequest(ConfirmableRequest):
    """Delete a sales order. Destructive — Katana cascades child rows /
    addresses / fulfillments / shipping fees server-side.
    """

    id: int = Field(..., description="Sales order ID to delete")


# ----------------------------------------------------------------------------
# API request builders — pure data shaping per sub-payload kind.
# ----------------------------------------------------------------------------


def _build_update_header_request(patch: SOHeaderPatch) -> APIUpdateSalesOrderRequest:
    return APIUpdateSalesOrderRequest(
        **unset_dict(patch, transforms={"status": UpdateSalesOrderStatus})
    )


def _build_create_row_request(so_id: int, row: SORowAdd) -> APICreateSORowRequest:
    return APICreateSORowRequest(sales_order_id=so_id, **unset_dict(row))


def _build_update_row_request(patch: SORowUpdate) -> APIUpdateSORowRequest:
    return APIUpdateSORowRequest(**unset_dict(patch, exclude=("id",)))


def _build_create_address_request(
    so_id: int, addr: SOAddressAdd
) -> APICreateSOAddressRequest:
    return APICreateSOAddressRequest(
        sales_order_id=so_id,
        **unset_dict(
            addr,
            field_map={"zip": "zip_"},
            transforms={"entity_type": AddressEntityType},
        ),
    )


def _build_update_address_request(
    patch: SOAddressUpdate,
) -> APIUpdateSOAddressRequest:
    return APIUpdateSOAddressRequest(
        **unset_dict(patch, exclude=("id",), field_map={"zip": "zip_"})
    )


def _build_create_fulfillment_request(
    so_id: int, fulfillment: SOFulfillmentAdd
) -> APICreateSOFulfillmentRequest:
    rows = [
        SalesOrderFulfillmentRowRequest(
            sales_order_row_id=r.sales_order_row_id, quantity=r.quantity
        )
        for r in fulfillment.sales_order_fulfillment_rows
    ]
    return APICreateSOFulfillmentRequest(
        sales_order_id=so_id,
        sales_order_fulfillment_rows=rows,
        **unset_dict(
            fulfillment,
            exclude=("sales_order_fulfillment_rows",),
            transforms={"status": SalesOrderFulfillmentStatus},
        ),
    )


def _build_update_fulfillment_request(
    patch: SOFulfillmentUpdate,
) -> APIUpdateSOFulfillmentRequest:
    return APIUpdateSOFulfillmentRequest(
        **unset_dict(
            patch,
            exclude=("id",),
            transforms={"status": SalesOrderFulfillmentStatus},
        )
    )


def _build_create_shipping_fee_request(
    so_id: int, fee: SOShippingFeeAdd
) -> APICreateSOShippingFeeRequest:
    return APICreateSOShippingFeeRequest(sales_order_id=so_id, **unset_dict(fee))


def _build_update_shipping_fee_request(
    patch: SOShippingFeeUpdate,
) -> APIUpdateSOShippingFeeRequest:
    return APIUpdateSOShippingFeeRequest(**unset_dict(patch, exclude=("id",)))


# ----------------------------------------------------------------------------
# Implementations
# ----------------------------------------------------------------------------


async def _modify_sales_order_impl(
    request: ModifySalesOrderRequest, context: Context
) -> ModificationResponse:
    """Build the action plan from the request's sub-payloads and either
    preview or execute based on ``preview``."""
    services = get_services(context)

    if not has_any_subpayload(request):
        raise ValueError(
            "At least one sub-payload must be set: update_header, "
            "add/update/delete_rows, add/update/delete_addresses, "
            "add/update/delete_fulfillments, or "
            "add/update/delete_shipping_fees. To remove the SO entirely, "
            "use delete_sales_order."
        )

    existing_so = await _fetch_sales_order_attrs(services, request.id)

    plan: list[ActionSpec] = []

    # Header — single optional patch.
    if request.update_header is not None:
        diff = compute_field_diff(
            existing_so, request.update_header, unknown_prior=existing_so is None
        )
        plan.append(
            ActionSpec(
                operation=SOOperation.UPDATE_HEADER,
                target_id=request.id,
                diff=diff,
                apply=make_patch_apply(
                    api_update_sales_order,
                    services,
                    request.id,
                    _build_update_header_request(request.update_header),
                    return_type=SalesOrder,
                ),
                verify=make_response_verifier(diff),
            )
        )

    # Rows.
    plan.extend(
        plan_creates(
            request.add_rows,
            SOOperation.ADD_ROW,
            lambda row: _build_create_row_request(request.id, row),
            lambda body: make_post_apply(
                api_create_so_row, services, body, return_type=SalesOrderRow
            ),
        )
    )
    plan.extend(
        await plan_updates(
            request.update_rows,
            SOOperation.UPDATE_ROW,
            lambda rid: _fetch_so_row(services, rid),
            _build_update_row_request,
            lambda rid, body: make_patch_apply(
                api_update_so_row, services, rid, body, return_type=SalesOrderRow
            ),
        )
    )
    plan.extend(
        plan_deletes(
            request.delete_row_ids,
            SOOperation.DELETE_ROW,
            lambda rid: make_delete_apply(api_delete_so_row, services, rid),
        )
    )

    # Addresses. Updates have no get-by-id endpoint, so fetcher is None
    # (every diff marks ``is_unknown_prior=True``).
    plan.extend(
        plan_creates(
            request.add_addresses,
            SOOperation.ADD_ADDRESS,
            lambda addr: _build_create_address_request(request.id, addr),
            lambda body: make_post_apply(
                api_create_so_address, services, body, return_type=APISalesOrderAddress
            ),
        )
    )
    plan.extend(
        await plan_updates(
            request.update_addresses,
            SOOperation.UPDATE_ADDRESS,
            None,  # no get-by-id endpoint
            _build_update_address_request,
            lambda aid, body: make_patch_apply(
                api_update_so_address,
                services,
                aid,
                body,
                return_type=APISalesOrderAddress,
            ),
        )
    )
    plan.extend(
        plan_deletes(
            request.delete_address_ids,
            SOOperation.DELETE_ADDRESS,
            lambda aid: make_delete_apply(api_delete_so_address, services, aid),
        )
    )

    # Fulfillments.
    plan.extend(
        plan_creates(
            request.add_fulfillments,
            SOOperation.ADD_FULFILLMENT,
            lambda fulfillment: _build_create_fulfillment_request(
                request.id, fulfillment
            ),
            lambda body: make_post_apply(
                api_create_so_fulfillment,
                services,
                body,
                return_type=SalesOrderFulfillment,
            ),
        )
    )
    plan.extend(
        await plan_updates(
            request.update_fulfillments,
            SOOperation.UPDATE_FULFILLMENT,
            lambda fid: _fetch_so_fulfillment(services, fid),
            _build_update_fulfillment_request,
            lambda fid, body: make_patch_apply(
                api_update_so_fulfillment,
                services,
                fid,
                body,
                return_type=SalesOrderFulfillment,
            ),
        )
    )
    plan.extend(
        plan_deletes(
            request.delete_fulfillment_ids,
            SOOperation.DELETE_FULFILLMENT,
            lambda fid: make_delete_apply(api_delete_so_fulfillment, services, fid),
        )
    )

    # Shipping fees.
    plan.extend(
        plan_creates(
            request.add_shipping_fees,
            SOOperation.ADD_SHIPPING_FEE,
            lambda fee: _build_create_shipping_fee_request(request.id, fee),
            lambda body: make_post_apply(
                api_create_so_shipping_fee,
                services,
                body,
                return_type=SalesOrderShippingFee,
            ),
        )
    )
    plan.extend(
        await plan_updates(
            request.update_shipping_fees,
            SOOperation.UPDATE_SHIPPING_FEE,
            lambda fid: _fetch_so_shipping_fee(services, fid),
            _build_update_shipping_fee_request,
            lambda fid, body: make_patch_apply(
                api_update_so_shipping_fee,
                services,
                fid,
                body,
                return_type=SalesOrderShippingFee,
            ),
        )
    )
    plan.extend(
        plan_deletes(
            request.delete_shipping_fee_ids,
            SOOperation.DELETE_SHIPPING_FEE,
            lambda fid: make_delete_apply(api_delete_so_shipping_fee, services, fid),
        )
    )

    return await run_modify_plan(
        request=request,
        entity_type="sales_order",
        entity_label=f"sales order {request.id}",
        tool_name="modify_sales_order",
        web_url_kind="sales_order",
        existing=existing_so,
        plan=plan,
    )


@observe_tool
@unpack_pydantic_params
async def modify_sales_order(
    request: Annotated[ModifySalesOrderRequest, Unpack()], context: Context
) -> ToolResult:
    """Modify a sales order — unified surface across header, rows, addresses,
    fulfillments, and shipping fees.

    Sub-payloads (any subset, all optional):

    - ``update_header`` — patch header fields (incl. status)
    - ``add_rows`` / ``update_rows`` / ``delete_row_ids`` — line item CRUD
    - ``add_addresses`` / ``update_addresses`` / ``delete_address_ids`` —
      billing/shipping addresses
    - ``add_fulfillments`` / ``update_fulfillments`` / ``delete_fulfillment_ids`` —
      fulfillments (each carries its own status + tracking)
    - ``add_shipping_fees`` / ``update_shipping_fees`` /
      ``delete_shipping_fee_ids`` — shipping/freight charges

    To remove an SO entirely, use the sibling ``delete_sales_order`` tool.

    Two-step flow: ``preview=true`` (default) returns a per-action preview;
    ``preview=false`` executes the plan in canonical order. Fail-fast on
    error; per-action ``verified`` reflects post-execution re-fetch
    confirmation (when supported by the resource).

    The response carries a ``prior_state`` snapshot of the pre-modification
    SO. Note: address updates can't be diffed pre-execution because Katana
    doesn't expose a per-address GET; their previews show every supplied
    field as ``(prior unknown) → new``.
    """
    response = await _modify_sales_order_impl(request, context)
    return to_tool_result(response)


# ============================================================================
# Tool: delete_sales_order
# ============================================================================


async def _delete_sales_order_impl(
    request: DeleteSalesOrderRequest, context: Context
) -> ModificationResponse:
    """One-action plan that removes the SO. Katana cascades child rows,
    addresses, fulfillments, and shipping fees server-side."""
    return await run_delete_plan(
        request=request,
        services=get_services(context),
        entity_type="sales_order",
        entity_label=f"sales order {request.id}",
        web_url_kind="sales_order",
        fetcher=_fetch_sales_order_attrs,
        delete_endpoint=api_delete_sales_order,
        operation=SOOperation.DELETE,
    )


@observe_tool
@unpack_pydantic_params
async def delete_sales_order(
    request: Annotated[DeleteSalesOrderRequest, Unpack()], context: Context
) -> ToolResult:
    """Delete a sales order. Destructive — Katana cascades the delete to
    child rows / addresses / fulfillments / shipping fees server-side.

    The response carries a ``prior_state`` snapshot for manual revert.
    """
    response = await _delete_sales_order_impl(request, context)
    return to_tool_result(response)


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

    _write = ToolAnnotations(
        readOnlyHint=False, destructiveHint=False, openWorldHint=True
    )
    _update = ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    )
    _destructive = ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=True,
        openWorldHint=True,
    )

    mcp.tool(tags={"orders", "sales", "write"}, annotations=_write, meta=UI_META)(
        create_sales_order
    )
    mcp.tool(tags={"orders", "sales", "read"}, annotations=_read)(list_sales_orders)
    mcp.tool(tags={"orders", "sales", "read"}, annotations=_read)(get_sales_order)
    mcp.tool(tags={"orders", "sales", "write"}, annotations=_update)(modify_sales_order)
    mcp.tool(
        tags={"orders", "sales", "write", "destructive"},
        annotations=_destructive,
    )(delete_sales_order)
