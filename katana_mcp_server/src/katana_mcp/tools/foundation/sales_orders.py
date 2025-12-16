"""Sales order management tools for Katana MCP Server.

Foundation tools for creating sales orders.

These tools provide:
- create_sales_order: Create sales orders with preview/confirm pattern
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Annotated, Literal

from fastmcp import Context, FastMCP
from pydantic import BaseModel, Field

from katana_mcp.logging import observe_tool
from katana_mcp.services import get_services
from katana_mcp.tools.schemas import ConfirmationSchema
from katana_mcp.unpack import Unpack, unpack_pydantic_params
from katana_public_api_client.client_types import UNSET
from katana_public_api_client.domain.converters import unwrap_unset
from katana_public_api_client.models import (
    CreateSalesOrderRequest as APICreateSalesOrderRequest,
    CreateSalesOrderRequestSalesOrderRowsItem,
    CreateSalesOrderRequestStatus,
    SalesOrder,
    SalesOrderAddress as APISalesOrderAddress,
    SalesOrderAddressEntityType,
)
from katana_public_api_client.utils import unwrap_as

logger = logging.getLogger(__name__)

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
    warnings: list[str] = []
    next_actions: list[str] = []
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
    elicit_result = await context.elicit(
        f"Create sales order {request.order_number} for customer {request.customer_id} "
        f"with {len(request.items)} items?",
        ConfirmationSchema,
    )

    # Check if user accepted
    if elicit_result.action != "accept":
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
            message="Sales order creation cancelled by user",
            next_actions=["Review the order details and try again with confirm=true"],
        )

    # Type narrowing: at this point we know action == "accept", so data exists
    if not elicit_result.data.confirm:
        logger.info(f"User declined to confirm creation of SO {request.order_number}")
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
            message="Sales order creation declined by user",
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
                price_per_unit=item.price_per_unit
                if item.price_per_unit is not None
                else UNSET,
                tax_rate_id=item.tax_rate_id if item.tax_rate_id is not None else UNSET,
                location_id=item.location_id if item.location_id is not None else UNSET,
                total_discount=item.total_discount
                if item.total_discount is not None
                else UNSET,
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
                    entity_type=SalesOrderAddressEntityType(addr.entity_type),
                    first_name=addr.first_name
                    if addr.first_name is not None
                    else UNSET,
                    last_name=addr.last_name if addr.last_name is not None else UNSET,
                    company=addr.company if addr.company is not None else UNSET,
                    phone=addr.phone if addr.phone is not None else UNSET,
                    line_1=addr.line_1 if addr.line_1 is not None else UNSET,
                    line_2=addr.line_2 if addr.line_2 is not None else UNSET,
                    city=addr.city if addr.city is not None else UNSET,
                    state=addr.state if addr.state is not None else UNSET,
                    zip_=addr.zip_code if addr.zip_code is not None else UNSET,
                    country=addr.country if addr.country is not None else UNSET,
                )
                addresses_list.append(api_addr)

        # Build API request
        api_request = APICreateSalesOrderRequest(
            order_no=request.order_number,
            customer_id=request.customer_id,
            sales_order_rows=so_rows,
            location_id=request.location_id
            if request.location_id is not None
            else UNSET,
            delivery_date=request.delivery_date
            if request.delivery_date is not None
            else UNSET,
            currency=request.currency if request.currency is not None else UNSET,
            addresses=addresses_list,
            additional_info=request.notes if request.notes is not None else UNSET,
            customer_ref=request.customer_ref
            if request.customer_ref is not None
            else UNSET,
            order_created_date=datetime.now(UTC),
            status=CreateSalesOrderRequestStatus.PENDING,
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
) -> SalesOrderResponse:
    """Create a sales order with two-step confirmation.

    This tool supports a two-step confirmation process:
    1. Preview (confirm=false): Shows order details and calculations without creating
    2. Confirm (confirm=true): Creates the actual sales order in Katana

    The tool creates sales orders for customer purchases and supports:
    - Multiple line items with different variants
    - Optional pricing overrides per line item
    - Optional tax rates and discounts
    - Billing and shipping addresses
    - Currency specification
    - Order notes and customer references

    Args:
        request: Request with sales order details and confirm flag
        context: Server context with KatanaClient

    Returns:
        Sales order response with ID (if created) and details

    Example:
        Preview:
            Request: {"customer_id": 1501, "order_number": "SO-2024-001",
                     "items": [{"variant_id": 2101, "quantity": 3, "price_per_unit": 599.99}],
                     "confirm": false}
            Returns: Preview with calculated total

        Confirm:
            Request: Same as above but with "confirm": true
            Returns: Created SO with ID and status
    """
    return await _create_sales_order_impl(request, context)


def register_tools(mcp: FastMCP) -> None:
    """Register all sales order tools with the FastMCP instance.

    Registers sales order creation tool:
    - create_sales_order: Create sales orders with preview/confirm

    Args:
        mcp: FastMCP server instance to register tools with
    """
    mcp.tool()(create_sales_order)
