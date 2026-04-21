"""Sales order management tools for Katana MCP Server.

Foundation tools for creating sales orders.

These tools provide:
- create_sales_order: Create sales orders with preview/confirm pattern
"""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from typing import Annotated, Any, Literal

from fastmcp import Context, FastMCP
from fastmcp.tools import ToolResult
from pydantic import BaseModel, Field

from katana_mcp.cache import EntityType
from katana_mcp.logging import get_logger, observe_tool
from katana_mcp.services import get_services
from katana_mcp.tools.schemas import ConfirmationResult, require_confirmation
from katana_mcp.tools.tool_result_utils import (
    enum_to_str,
    format_md_table,
    iso_or_none,
    make_tool_result,
    none_coro,
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

    # Confirm mode - use elicitation to get user confirmation before creating
    confirmation = await require_confirmation(
        context,
        f"Place sales order {request.order_number} for customer {request.customer_id} "
        f"with {len(request.items)} items?",
    )

    if confirmation != ConfirmationResult.CONFIRMED:
        logger.info(f"User did not confirm creation of SO {request.order_number}")
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
            message=f"Sales order creation {confirmation} by user",
            next_actions=["Review the order details and try again with confirm=true"],
        )

    # User confirmed - create the sales order via API
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

    Two-step flow: confirm=false to preview totals, confirm=true to create
    (prompts for confirmation). Requires customer_id, order_number, and at
    least one line item with variant_id and quantity. Supports optional pricing
    overrides, discounts, delivery dates, and billing/shipping addresses.
    """
    from katana_mcp.tools.prefab_ui import (
        build_order_created_ui,
        build_order_preview_ui,
    )

    response = await _create_sales_order_impl(request, context)

    next_actions_text = "\n".join(f"- {a}" for a in response.next_actions) or "None"

    order_dict = response.model_dump()
    if response.is_preview:
        ui = build_order_preview_ui(order_dict, "Sales Order")
    else:
        ui = build_order_created_ui(order_dict, "Sales Order")

    return make_tool_result(
        response,
        "sales_order_created",
        ui=ui,
        id=response.id or "N/A",
        order_number=response.order_number,
        customer_id=response.customer_id,
        status=response.status or ("PREVIEW" if response.is_preview else "N/A"),
        total=f"${response.total:,.2f}" if response.total is not None else "N/A",
        currency=response.currency or "N/A",
        message=response.message,
        next_actions_text=next_actions_text,
    )


# ============================================================================
# Tool 2: list_sales_orders
# ============================================================================


class ListSalesOrdersRequest(BaseModel):
    """Request to list/filter sales orders."""

    limit: int = Field(
        default=50,
        ge=1,
        description=(
            "Max orders to return (default 50, min 1). When `page` is set, "
            "acts as the page size for that request."
        ),
    )
    page: int | None = Field(
        default=None,
        description=(
            "Page number (1-based). When set, returns a single page and "
            "disables auto-pagination; `limit` becomes the page size for "
            "that request."
        ),
    )
    order_no: str | None = Field(default=None, description="Filter by exact order_no")
    customer_id: int | None = Field(default=None, description="Filter by customer ID")
    location_id: int | None = Field(default=None, description="Filter by location ID")
    status: str | None = Field(
        default=None, description="Filter by sales order status (e.g. NOT_SHIPPED)"
    )
    production_status: str | None = Field(
        default=None,
        description="Filter by production status (NONE, NOT_STARTED, IN_PROGRESS, BLOCKED, DONE, NOT_APPLICABLE)",
    )
    needs_work_orders: bool = Field(
        default=False,
        description="Convenience: filter to orders with production_status=NONE (no MOs created yet)",
    )


class PaginationMeta(BaseModel):
    """Pagination metadata extracted from Katana's `x-pagination` response header.

    Populated on `ListSalesOrdersResponse.pagination` only when the caller requested
    a specific page (i.e. passed `page=N`). When auto-pagination is used, this field
    is `None` because there is no single page to describe.
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


class ListSalesOrdersResponse(BaseModel):
    """Response containing a list of sales orders."""

    orders: list[SalesOrderSummary]
    total_count: int
    pagination: PaginationMeta | None = Field(
        default=None,
        description=(
            "Pagination cursor populated from the API's `x-pagination` header when "
            "the caller requested a specific page. `None` when auto-paginating."
        ),
    )


def _parse_pagination_header(raw: str | None) -> PaginationMeta | None:
    """Parse Katana's `x-pagination` response header into a PaginationMeta.

    Katana returns this as a JSON string with all fields as strings, e.g.:
    `{"total_records":"2319","total_pages":"2319","offset":"0","page":"1",
      "first_page":"true","last_page":"false"}`.

    Returns `None` when the header is absent or the top-level JSON is invalid
    (non-JSON or not a JSON object). When the header is valid JSON but
    individual fields are missing or malformed, returns a `PaginationMeta`
    with those specific fields set to `None` rather than discarding the
    whole header.
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


async def _list_sales_orders_impl(
    request: ListSalesOrdersRequest, context: Context
) -> ListSalesOrdersResponse:
    """List sales orders with filters."""
    from katana_public_api_client.api.sales_order import get_all_sales_orders
    from katana_public_api_client.utils import unwrap_data

    services = get_services(context)

    # Pass through only the filters the caller actually set. `is not None`
    # (not truthy) so 0-valued customer_id/location_id still filter.
    production_status = request.production_status
    if production_status is None and request.needs_work_orders:
        production_status = "NONE"
    filters = {
        "order_no": request.order_no,
        "customer_id": request.customer_id,
        "location_id": request.location_id,
        "status": request.status,
        "production_status": production_status,
    }
    kwargs: dict[str, Any] = {
        "client": services.client,
        "limit": request.limit,
        **{k: v for k, v in filters.items() if v is not None},
    }
    # Pagination strategy:
    # - If `page` is set, the caller is driving pagination manually; forward
    #   it so PaginationTransport disables auto-pagination (see: "ANY explicit
    #   `page` parameter in URL disables auto-pagination") and lets callers
    #   walk beyond the transport's max_pages ceiling.
    # - Otherwise, when `limit` fits in a single Katana page (<=250, the API's
    #   max page size), pass page=1 to short-circuit auto-pagination and
    #   avoid fetching thousands of rows when the caller asked for a small
    #   cap (see #329). Lower bound is defence-in-depth with `ge=1` on Field.
    if request.page is not None:
        kwargs["page"] = request.page
    elif 1 <= request.limit <= 250:
        kwargs["page"] = 1

    response = await get_all_sales_orders.asyncio_detailed(**kwargs)
    attrs_list = unwrap_data(response, default=[])
    # Safety net: cap to request.limit post-pagination so we never return more
    # than the caller asked for, regardless of how the transport behaved.
    attrs_list = attrs_list[: request.limit]

    # Surface pagination metadata from the `x-pagination` response header only
    # when the caller is driving paging manually. During auto-pagination the
    # header describes just the final fetched page, which would be misleading.
    pagination: PaginationMeta | None = None
    if request.page is not None:
        headers = getattr(response, "headers", None)
        if headers is not None:
            pagination = _parse_pagination_header(headers.get("x-pagination"))

    orders: list[SalesOrderSummary] = []
    for so in attrs_list:
        rows = unwrap_unset(so.sales_order_rows, [])
        orders.append(
            SalesOrderSummary(
                id=so.id,
                order_no=unwrap_unset(so.order_no, None),
                customer_id=unwrap_unset(so.customer_id, None),
                location_id=unwrap_unset(so.location_id, None),
                status=enum_to_str(unwrap_unset(so.status, None)),
                production_status=enum_to_str(unwrap_unset(so.production_status, None)),
                invoicing_status=enum_to_str(unwrap_unset(so.invoicing_status, None)),
                created_at=iso_or_none(unwrap_unset(so.created_at, None)),
                delivery_date=iso_or_none(unwrap_unset(so.delivery_date, None)),
                total=unwrap_unset(so.total, None),
                currency=unwrap_unset(so.currency, None),
                row_count=len(rows),
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
    """List sales orders with filters.

    Use this for discovery workflows — find recent orders, orders needing work
    orders, orders for a specific customer, etc. Returns summary info (order_no,
    status, production_status, totals, row count).

    **Common filters:**
    - `needs_work_orders=true` — orders with no MOs yet (production_status=NONE)
    - `status="NOT_SHIPPED"` — unshipped orders
    - `customer_id=N` — orders for a specific customer

    For full line-item details on a specific order, use `get_sales_order` next.
    """
    from katana_mcp.tools.tool_result_utils import make_simple_result

    response = await _list_sales_orders_impl(request, context)

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


class GetSalesOrderResponse(BaseModel):
    """Full sales order details."""

    id: int
    order_no: str | None
    customer_id: int | None
    location_id: int | None
    status: str | None
    production_status: str | None
    created_at: str | None
    delivery_date: str | None
    total: float | None
    currency: str | None
    additional_info: str | None
    rows: list[SalesOrderRowInfo]


async def _get_sales_order_impl(
    request: GetSalesOrderRequest, context: Context
) -> GetSalesOrderResponse:
    """Look up a single sales order by order_no or order_id with line items."""
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

    # Parallelize variant lookups across all rows (N+1 fix)
    variant_ids = [unwrap_unset(r.variant_id, None) for r in raw_rows]
    variants = await asyncio.gather(
        *(
            services.cache.get_by_id(EntityType.VARIANT, v_id)
            if v_id is not None
            else none_coro()
            for v_id in variant_ids
        )
    )

    row_infos: list[SalesOrderRowInfo] = []
    for r, variant in zip(raw_rows, variants, strict=True):
        row_infos.append(
            SalesOrderRowInfo(
                id=r.id,
                variant_id=unwrap_unset(r.variant_id, None),
                sku=variant.get("sku") if variant else None,
                quantity=unwrap_unset(r.quantity, None),
                price_per_unit=unwrap_unset(r.price_per_unit, None),
                linked_manufacturing_order_id=unwrap_unset(
                    r.linked_manufacturing_order_id, None
                ),
            )
        )

    return GetSalesOrderResponse(
        id=so.id,
        order_no=unwrap_unset(so.order_no, None),
        customer_id=unwrap_unset(so.customer_id, None),
        location_id=unwrap_unset(so.location_id, None),
        status=enum_to_str(unwrap_unset(so.status, None)),
        production_status=enum_to_str(unwrap_unset(so.production_status, None)),
        created_at=iso_or_none(unwrap_unset(so.created_at, None)),
        delivery_date=iso_or_none(unwrap_unset(so.delivery_date, None)),
        total=unwrap_unset(so.total, None),
        currency=unwrap_unset(so.currency, None),
        additional_info=unwrap_unset(so.additional_info, None),
        rows=row_infos,
    )


@observe_tool
@unpack_pydantic_params
async def get_sales_order(
    request: Annotated[GetSalesOrderRequest, Unpack()], context: Context
) -> ToolResult:
    """Look up a sales order by number or ID with all line items.

    Returns order details (status, production_status, customer, delivery date)
    plus rows with variant_id, SKU, quantity, price, and per-row production
    status. Use with `list_sales_orders` for discovery workflows.
    """
    from katana_mcp.tools.tool_result_utils import make_simple_result

    response = await _get_sales_order_impl(request, context)

    lines = [
        f"## Sales Order {response.order_no or response.id}",
        f"- **Status**: {response.status}",
        f"- **Production**: {response.production_status}",
    ]
    if response.customer_id is not None:
        lines.append(f"- **Customer ID**: {response.customer_id}")
    if response.location_id is not None:
        lines.append(f"- **Location ID**: {response.location_id}")
    if response.total is not None:
        lines.append(f"- **Total**: {response.total} {response.currency or ''}")
    if response.delivery_date:
        lines.append(f"- **Delivery**: {response.delivery_date}")
    if response.additional_info:
        lines.append(f"- **Notes**: {response.additional_info}")

    if response.rows:
        lines.append("")
        lines.append("### Line Items")
        lines.append(
            format_md_table(
                headers=["Row ID", "SKU", "Variant", "Qty", "Price", "Linked MO"],
                rows=[
                    [
                        r.id,
                        r.sku or "—",
                        r.variant_id or "—",
                        r.quantity,
                        r.price_per_unit or "—",
                        r.linked_manufacturing_order_id or "—",
                    ]
                    for r in response.rows
                ],
            )
        )

    return make_simple_result("\n".join(lines), structured_data=response.model_dump())


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
    )(create_sales_order)
    mcp.tool(
        tags={"orders", "sales", "read"},
        annotations=_read,
    )(list_sales_orders)
    mcp.tool(
        tags={"orders", "sales", "read"},
        annotations=_read,
    )(get_sales_order)
