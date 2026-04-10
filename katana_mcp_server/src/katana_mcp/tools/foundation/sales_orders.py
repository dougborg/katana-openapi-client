"""Sales order management tools for Katana MCP Server.

Foundation tools for creating sales orders.

These tools provide:
- create_sales_order: Create sales orders with preview/confirm pattern
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Literal

from fastmcp import Context, FastMCP
from fastmcp.tools.tool import ToolResult
from pydantic import BaseModel, Field

from katana_mcp.logging import get_logger, observe_tool
from katana_mcp.services import get_services
from katana_mcp.tools.schemas import ConfirmationResult, require_confirmation
from katana_mcp.tools.tool_result_utils import make_tool_result
from katana_mcp.unpack import Unpack, unpack_pydantic_params
from katana_public_api_client.client_types import UNSET
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
        None, description="Override price per unit (uses default if not specified)"
    )
    tax_rate_id: int | None = Field(None, description="Tax rate ID (optional)")
    location_id: int | None = Field(
        None, description="Location to pick from (optional)"
    )
    total_discount: float | None = Field(
        None, description="Discount for this line item (optional)"
    )


class SalesOrderAddress(BaseModel):
    """Billing or shipping address for a sales order."""

    entity_type: Literal["billing", "shipping"] = Field(
        ..., description="Type of address - billing or shipping"
    )
    first_name: str | None = Field(None, description="First name of contact")
    last_name: str | None = Field(None, description="Last name of contact")
    company: str | None = Field(None, description="Company name")
    phone: str | None = Field(None, description="Phone number")
    line_1: str | None = Field(None, description="Primary address line")
    line_2: str | None = Field(None, description="Secondary address line")
    city: str | None = Field(None, description="City")
    state: str | None = Field(None, description="State or province")
    zip_code: str | None = Field(None, description="Postal/ZIP code")
    country: str | None = Field(None, description="Country code (e.g., US, CA, GB)")


class CreateSalesOrderRequest(BaseModel):
    """Request to create a sales order."""

    customer_id: int = Field(..., description="Customer ID placing the order")
    order_number: str = Field(..., description="Unique sales order number")
    items: list[SalesOrderItem] = Field(..., description="Line items", min_length=1)
    location_id: int | None = Field(
        None, description="Primary fulfillment location ID (optional)"
    )
    delivery_date: datetime | None = Field(
        None, description="Requested delivery date (optional)"
    )
    currency: str | None = Field(
        None, description="Currency code (defaults to company base currency)"
    )
    addresses: list[SalesOrderAddress] | None = Field(
        None, description="Billing and/or shipping addresses (optional)"
    )
    notes: str | None = Field(None, description="Additional notes (optional)")
    customer_ref: str | None = Field(
        None, description="Customer's reference number (optional)"
    )
    confirm: bool = Field(
        False, description="If false, returns preview. If true, creates order."
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
        f"Create sales order {request.order_number} for customer {request.customer_id} "
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
        addresses_list: list[APISalesOrderAddress] | type[UNSET] = UNSET
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
        total=f"${response.total:,.2f}" if response.total else "N/A",
        currency=response.currency or "N/A",
        message=response.message,
        next_actions_text=next_actions_text,
    )


# ============================================================================
# Tool 2: list_sales_orders
# ============================================================================


class ListSalesOrdersRequest(BaseModel):
    """Request to list/filter sales orders."""

    limit: int = Field(default=50, description="Max orders to return (default 50)")
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


async def _list_sales_orders_impl(
    request: ListSalesOrdersRequest, context: Context
) -> ListSalesOrdersResponse:
    """List sales orders with filters."""
    from katana_public_api_client.api.sales_order import get_all_sales_orders
    from katana_public_api_client.utils import unwrap_data

    services = get_services(context)

    kwargs: dict = {
        "client": services.client,
        "limit": request.limit,
    }
    if request.order_no:
        kwargs["order_no"] = request.order_no
    if request.customer_id:
        kwargs["customer_id"] = request.customer_id
    if request.location_id:
        kwargs["location_id"] = request.location_id
    if request.status:
        kwargs["status"] = request.status
    if request.production_status:
        kwargs["production_status"] = request.production_status
    elif request.needs_work_orders:
        kwargs["production_status"] = "NONE"

    response = await get_all_sales_orders.asyncio_detailed(**kwargs)
    attrs_list = unwrap_data(response, default=[])

    orders: list[SalesOrderSummary] = []
    for so in attrs_list:
        rows = unwrap_unset(so.sales_order_rows, []) or []
        created_at = unwrap_unset(so.created_at, None)
        delivery_date = unwrap_unset(so.delivery_date, None)
        status = unwrap_unset(so.status, None)
        production_status = unwrap_unset(so.production_status, None)
        invoicing_status = unwrap_unset(so.invoicing_status, None)
        orders.append(
            SalesOrderSummary(
                id=so.id,
                order_no=unwrap_unset(so.order_no, None),
                customer_id=unwrap_unset(so.customer_id, None),
                location_id=unwrap_unset(so.location_id, None),
                status=status.value if hasattr(status, "value") else status,
                production_status=production_status.value
                if hasattr(production_status, "value")
                else production_status,
                invoicing_status=invoicing_status.value
                if hasattr(invoicing_status, "value")
                else invoicing_status,
                created_at=created_at.isoformat() if created_at else None,
                delivery_date=delivery_date.isoformat() if delivery_date else None,
                total=unwrap_unset(so.total, None),
                currency=unwrap_unset(so.currency, None),
                row_count=len(rows),
            )
        )

    return ListSalesOrdersResponse(orders=orders, total_count=len(orders))


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
        lines = [
            f"## Sales Orders ({response.total_count})",
            "",
            "| Order # | Status | Production | Rows | Total | Created |",
            "|---------|--------|------------|------|-------|---------|",
        ]
        for o in response.orders:
            total_str = f"{o.total:.2f} {o.currency or ''}" if o.total else "—"
            lines.append(
                f"| {o.order_no or o.id} | {o.status or '—'} "
                f"| {o.production_status or '—'} | {o.row_count} "
                f"| {total_str} | {o.created_at or '—'} |"
            )
        md = "\n".join(lines)

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
    from katana_public_api_client.utils import unwrap, unwrap_data

    if not request.order_no and not request.order_id:
        raise ValueError("Either order_no or order_id must be provided")

    services = get_services(context)

    if request.order_id:
        response = await api_get_sales_order.asyncio_detailed(
            id=request.order_id, client=services.client
        )
        so = unwrap(response)
        if so is None:
            raise ValueError(f"Sales order ID {request.order_id} not found")
    else:
        response = await get_all_sales_orders.asyncio_detailed(
            client=services.client, order_no=request.order_no, limit=1
        )
        orders = unwrap_data(response, default=[])
        if not orders:
            raise ValueError(f"Sales order '{request.order_no}' not found")
        so = orders[0]

    raw_rows = unwrap_unset(so.sales_order_rows, []) or []
    row_infos: list[SalesOrderRowInfo] = []
    for r in raw_rows:
        variant_id = unwrap_unset(r.variant_id, None)
        sku: str | None = None
        if variant_id is not None:
            variant = await services.cache.get_by_id("variant", variant_id)
            if variant:
                sku = variant.get("sku")
        row_infos.append(
            SalesOrderRowInfo(
                id=r.id,
                variant_id=variant_id,
                sku=sku,
                quantity=unwrap_unset(r.quantity, None),
                price_per_unit=unwrap_unset(r.price_per_unit, None),
                linked_manufacturing_order_id=unwrap_unset(
                    r.linked_manufacturing_order_id, None
                ),
            )
        )

    created_at = unwrap_unset(so.created_at, None)
    delivery_date = unwrap_unset(so.delivery_date, None)
    status = unwrap_unset(so.status, None)
    production_status = unwrap_unset(so.production_status, None)

    return GetSalesOrderResponse(
        id=so.id,
        order_no=unwrap_unset(so.order_no, None),
        customer_id=unwrap_unset(so.customer_id, None),
        location_id=unwrap_unset(so.location_id, None),
        status=status.value if hasattr(status, "value") else status,
        production_status=production_status.value
        if hasattr(production_status, "value")
        else production_status,
        created_at=created_at.isoformat() if created_at else None,
        delivery_date=delivery_date.isoformat() if delivery_date else None,
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
        lines.append("| Row ID | SKU | Variant | Qty | Price | Linked MO |")
        lines.append("|--------|-----|---------|-----|-------|-----------|")
        for r in response.rows:
            lines.append(
                f"| {r.id} | {r.sku or '—'} | {r.variant_id or '—'} "
                f"| {r.quantity} | {r.price_per_unit or '—'} "
                f"| {r.linked_manufacturing_order_id or '—'} |"
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
