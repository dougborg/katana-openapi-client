"""Sales order management tools for Katana MCP Server.

Foundation tools for creating sales orders.

These tools provide:
- create_sales_order: Create sales orders with preview/confirm pattern
"""

from __future__ import annotations

import asyncio
import datetime as _datetime
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
    UI_META,
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
    ids: list[int] | None = Field(
        default=None, description="Filter by explicit list of sales order IDs"
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

    # Time-window filters (client-side — Katana does not expose
    # delivery_date_min/max as server-side filters, so the tool applies them
    # after fetch).
    delivered_after: str | None = Field(
        default=None,
        description=(
            "ISO-8601 datetime lower bound on delivery_date. Applied "
            "client-side — Katana does not expose a server-side filter "
            "for delivery_date, so this filters post-fetch. Combine with a "
            "created_at window to keep fetched rows bounded."
        ),
    )
    delivered_before: str | None = Field(
        default=None,
        description=(
            "ISO-8601 datetime upper bound on delivery_date. Applied "
            "client-side — see `delivered_after`."
        ),
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
    rows: list[SalesOrderRowInfo] | None = None


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


def _parse_iso_datetime(value: str, field_name: str) -> datetime:
    """Parse an ISO-8601 datetime string, raising ValueError on malformed input.

    Normalizes trailing ``Z`` / ``z`` (UTC shorthand) to ``+00:00`` before
    parsing — ``datetime.fromisoformat`` didn't accept ``Z`` before Python
    3.11. Raises ``ValueError`` with the field name on unparseable input so
    caller mistakes surface loudly instead of being silently dropped.
    """
    normalized = value
    if normalized.endswith(("Z", "z")):
        normalized = normalized[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(normalized)
    except ValueError as e:
        raise ValueError(
            f"Invalid ISO-8601 datetime for {field_name!r}: {value!r}"
        ) from e


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
    """List sales orders with filters (list-tool pattern v2)."""
    from katana_public_api_client.api.sales_order import get_all_sales_orders
    from katana_public_api_client.utils import unwrap_data

    services = get_services(context)

    # Pass through only the filters the caller actually set. `is not None`
    # (not truthy) so 0-valued customer_id/location_id still filter.
    production_status = request.production_status
    if production_status is None and request.needs_work_orders:
        production_status = "NONE"
    kwargs: dict[str, Any] = {
        "client": services.client,
        "limit": request.limit,
    }
    if request.order_no is not None:
        kwargs["order_no"] = request.order_no
    if request.ids is not None:
        kwargs["ids"] = request.ids
    if request.customer_id is not None:
        kwargs["customer_id"] = request.customer_id
    if request.location_id is not None:
        kwargs["location_id"] = request.location_id
    if request.status is not None:
        kwargs["status"] = request.status
    if production_status is not None:
        kwargs["production_status"] = production_status
    if request.invoicing_status is not None:
        kwargs["invoicing_status"] = request.invoicing_status
    if request.currency is not None:
        kwargs["currency"] = request.currency
    if request.include_deleted is not None:
        kwargs["include_deleted"] = request.include_deleted

    # Server-side date filters
    if request.created_after is not None:
        kwargs["created_at_min"] = _parse_iso_datetime(
            request.created_after, "created_after"
        )
    if request.created_before is not None:
        kwargs["created_at_max"] = _parse_iso_datetime(
            request.created_before, "created_before"
        )
    if request.updated_after is not None:
        kwargs["updated_at_min"] = _parse_iso_datetime(
            request.updated_after, "updated_after"
        )
    if request.updated_before is not None:
        kwargs["updated_at_max"] = _parse_iso_datetime(
            request.updated_before, "updated_before"
        )

    # Client-side date filters — parsed eagerly so bad input fails loudly
    # before we spend an API call.
    delivered_after_dt: datetime | None = None
    delivered_before_dt: datetime | None = None
    if request.delivered_after is not None:
        delivered_after_dt = _parse_iso_datetime(
            request.delivered_after, "delivered_after"
        )
    if request.delivered_before is not None:
        delivered_before_dt = _parse_iso_datetime(
            request.delivered_before, "delivered_before"
        )
    has_client_filter = (
        delivered_after_dt is not None or delivered_before_dt is not None
    )

    # Pagination strategy:
    # - If `page` is set, the caller is driving pagination manually; forward
    #   it so PaginationTransport disables auto-pagination and lets callers
    #   walk beyond the transport's max_pages ceiling.
    # - Otherwise, when `limit` fits in a single Katana page (<=250, the API's
    #   max page size) AND no client-side-only filter is active, pass page=1
    #   to short-circuit auto-pagination. When a client-side filter IS active,
    #   skip the short-circuit so the transport's auto-pagination can scan
    #   enough rows to find `limit` matching ones post-filter.
    if request.page is not None:
        kwargs["page"] = request.page
    elif 1 <= request.limit <= 250 and not has_client_filter:
        kwargs["page"] = 1

    response = await get_all_sales_orders.asyncio_detailed(**kwargs)
    attrs_list = unwrap_data(response, default=[])

    # Client-side delivery_date filter (Katana has no server-side param).
    if has_client_filter:

        def _in_delivery_window(so: Any) -> bool:
            delivery = unwrap_unset(so.delivery_date, None)
            if not isinstance(delivery, _datetime.datetime):
                return False
            if delivered_after_dt is not None and delivery < delivered_after_dt:
                return False
            return not (
                delivered_before_dt is not None and delivery > delivered_before_dt
            )

        attrs_list = [so for so in attrs_list if _in_delivery_window(so)]

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
        # When include_rows is set, expose row-level detail on each summary.
        # `sku` is left None in list context — resolving it would require a
        # variant cache lookup per row (up to 250 rows * N variants), which
        # defeats the "one call for 50 orders" goal. Callers that need SKUs
        # should use `get_sales_order` on a specific order.
        row_infos: list[SalesOrderRowInfo] | None = None
        if request.include_rows:
            row_infos = [
                SalesOrderRowInfo(
                    id=r.id,
                    variant_id=unwrap_unset(r.variant_id, None),
                    sku=None,
                    quantity=unwrap_unset(r.quantity, None),
                    price_per_unit=unwrap_unset(r.price_per_unit, None),
                    linked_manufacturing_order_id=unwrap_unset(
                        r.linked_manufacturing_order_id, None
                    ),
                )
                for r in rows
            ]
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
    """List sales orders with filters (list-tool pattern v2).

    Use this for discovery workflows — find recent orders, orders needing work
    orders, orders for a specific customer, etc. Returns summary info (order_no,
    status, production_status, totals, row count).

    **Common filters:**
    - `needs_work_orders=true` — orders with no MOs yet (production_status=NONE)
    - `status="NOT_SHIPPED"` — unshipped orders
    - `customer_id=N` — orders for a specific customer

    **Time windows:**
    - `created_after` / `created_before` — server-side bounds on `created_at`
    - `updated_after` / `updated_before` — server-side bounds on `updated_at`
    - `delivered_after` / `delivered_before` — client-side bounds on
      `delivery_date` (Katana has no server-side filter). When set, the tool
      skips the page=1 short-circuit so auto-pagination can scan enough rows
      to find `limit` matching results post-filter.

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
