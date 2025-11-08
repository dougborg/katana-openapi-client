"""Manufacturing order management tools for Katana MCP Server.

Foundation tools for creating manufacturing orders to initiate production.

These tools provide:
- create_manufacturing_order: Create manufacturing orders with preview/confirm pattern
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Annotated, cast

from fastmcp import Context, FastMCP
from pydantic import BaseModel, Field

from katana_mcp.services import get_services
from katana_mcp.unpack import Unpack, unpack_pydantic_params
from katana_public_api_client.client_types import UNSET
from katana_public_api_client.models import (
    CreateManufacturingOrderRequest as APICreateManufacturingOrderRequest,
    ManufacturingOrder,
)

logger = logging.getLogger(__name__)

# ============================================================================
# Tool 1: create_manufacturing_order
# ============================================================================


class CreateManufacturingOrderRequest(BaseModel):
    """Request to create a manufacturing order."""

    variant_id: int = Field(..., description="Variant ID to manufacture")
    planned_quantity: float = Field(
        ..., description="Planned quantity to produce", gt=0
    )
    location_id: int = Field(..., description="Production location ID")
    order_created_date: datetime | None = Field(
        None, description="Order creation date (defaults to current time)"
    )
    production_deadline_date: datetime | None = Field(
        None, description="Production deadline date (optional)"
    )
    additional_info: str | None = Field(None, description="Additional notes (optional)")
    confirm: bool = Field(
        False, description="If false, returns preview. If true, creates order."
    )


class ManufacturingOrderResponse(BaseModel):
    """Response from creating a manufacturing order.

    Attributes:
        id: Manufacturing order ID (None in preview mode)
        order_no: Manufacturing order number
        variant_id: Variant ID to manufacture
        planned_quantity: Planned quantity to produce
        location_id: Production location ID
        status: Order status (e.g., "NOT_STARTED")
        order_created_date: Order creation timestamp
        production_deadline_date: Production deadline
        additional_info: Additional notes
        is_preview: True if preview mode, False if order created
        warnings: List of warnings (e.g., missing optional fields)
        next_actions: Suggested next steps
        message: Human-readable summary message
    """

    id: int | None = None
    order_no: str | None = None
    variant_id: int
    planned_quantity: float
    location_id: int
    status: str | None = None
    order_created_date: datetime | None = None
    production_deadline_date: datetime | None = None
    additional_info: str | None = None
    is_preview: bool
    warnings: list[str] = []
    next_actions: list[str] = []
    message: str


async def _create_manufacturing_order_impl(
    request: CreateManufacturingOrderRequest, context: Context
) -> ManufacturingOrderResponse:
    """Implementation of create_manufacturing_order tool.

    Args:
        request: Request with manufacturing order details
        context: Server context with KatanaClient

    Returns:
        Manufacturing order response with details

    Raises:
        ValueError: If validation fails
        Exception: If API call fails
    """
    logger.info(
        f"{'Previewing' if not request.confirm else 'Creating'} manufacturing order for variant {request.variant_id}"
    )

    # Preview mode - just return details without API call
    if not request.confirm:
        logger.info(
            f"Preview mode: MO for variant {request.variant_id}, quantity {request.planned_quantity}"
        )

        # Generate warnings for missing optional fields
        warnings = []
        if request.production_deadline_date is None:
            warnings.append(
                "No production_deadline_date specified - order will have no deadline"
            )
        if request.additional_info is None:
            warnings.append(
                "No additional_info specified - consider adding notes for context"
            )

        return ManufacturingOrderResponse(
            variant_id=request.variant_id,
            planned_quantity=request.planned_quantity,
            location_id=request.location_id,
            order_created_date=request.order_created_date,
            production_deadline_date=request.production_deadline_date,
            additional_info=request.additional_info,
            is_preview=True,
            warnings=warnings,
            next_actions=[
                "Review the order details",
                "Set confirm=true to create the manufacturing order",
            ],
            message=f"Preview: Manufacturing order for variant {request.variant_id}, quantity {request.planned_quantity}",
        )

    # Confirm mode - create the manufacturing order via API
    try:
        services = get_services(context)

        # Build API request
        api_request = APICreateManufacturingOrderRequest(
            variant_id=request.variant_id,
            planned_quantity=request.planned_quantity,
            location_id=request.location_id,
            order_created_date=request.order_created_date
            if request.order_created_date is not None
            else UNSET,
            production_deadline_date=request.production_deadline_date
            if request.production_deadline_date is not None
            else UNSET,
            additional_info=request.additional_info
            if request.additional_info is not None
            else UNSET,
        )

        # Call API
        from katana_public_api_client.api.manufacturing_order import (
            create_manufacturing_order as api_create_manufacturing_order,
        )

        response = await api_create_manufacturing_order.asyncio_detailed(
            client=services.client, body=api_request
        )

        if response.status_code == 200 and isinstance(
            response.parsed, ManufacturingOrder
        ):
            mo = response.parsed
            logger.info(f"Successfully created manufacturing order ID {mo.id}")

            # Extract values, handling UNSET with cast for type narrowing
            order_no: str | None = (
                cast(str, mo.order_no)
                if not isinstance(mo.order_no, type(UNSET))
                else None
            )
            variant_id: int = (
                cast(int, mo.variant_id)
                if not isinstance(mo.variant_id, type(UNSET))
                else request.variant_id
            )
            planned_quantity: float = (
                cast(float, mo.planned_quantity)
                if not isinstance(mo.planned_quantity, type(UNSET))
                else request.planned_quantity
            )
            location_id: int = (
                cast(int, mo.location_id)
                if not isinstance(mo.location_id, type(UNSET))
                else request.location_id
            )
            order_created_date: datetime | None = (
                cast(datetime, mo.order_created_date)
                if not isinstance(mo.order_created_date, type(UNSET))
                else None
            )
            production_deadline_date: datetime | None = (
                cast(datetime, mo.production_deadline_date)
                if not isinstance(mo.production_deadline_date, type(UNSET))
                else None
            )
            additional_info: str | None = (
                cast(str, mo.additional_info)
                if not isinstance(mo.additional_info, type(UNSET))
                else None
            )

            return ManufacturingOrderResponse(
                id=mo.id,
                order_no=order_no,
                variant_id=variant_id,
                planned_quantity=planned_quantity,
                location_id=location_id,
                status=mo.status.value
                if mo.status and not isinstance(mo.status, type(UNSET))
                else None,
                order_created_date=order_created_date,
                production_deadline_date=production_deadline_date,
                additional_info=additional_info,
                is_preview=False,
                next_actions=[
                    f"Manufacturing order created with ID {mo.id}",
                    "Use production tools to track and complete the order",
                ],
                message=f"Successfully created manufacturing order {order_no or mo.id} (ID: {mo.id})",
            )
        else:
            raise Exception(f"API returned unexpected status: {response.status_code}")

    except Exception as e:
        logger.error(f"Failed to create manufacturing order: {e}")
        raise


@unpack_pydantic_params
async def create_manufacturing_order(
    request: Annotated[CreateManufacturingOrderRequest, Unpack()], context: Context
) -> ManufacturingOrderResponse:
    """Create a manufacturing order with two-step confirmation.

    This tool supports a two-step confirmation process:
    1. Preview (confirm=false): Shows order details without creating
    2. Confirm (confirm=true): Creates the actual manufacturing order in Katana

    The tool creates manufacturing orders to initiate production of products
    or components. Manufacturing order recipe and operation rows are created
    automatically based on the product recipe and operations.

    Args:
        request: Request with manufacturing order details and confirm flag
        context: Server context with KatanaClient

    Returns:
        Manufacturing order response with ID (if created) and details

    Example:
        Preview:
            Request: {"variant_id": 2101, "planned_quantity": 50, "location_id": 1,
                     "production_deadline_date": "2024-01-25T17:00:00Z",
                     "additional_info": "Priority order", "confirm": false}
            Returns: Preview with order details

        Confirm:
            Request: Same as above but with "confirm": true
            Returns: Created MO with ID and status
    """
    return await _create_manufacturing_order_impl(request, context)


def register_tools(mcp: FastMCP) -> None:
    """Register all manufacturing order tools with the FastMCP instance.

    Registers manufacturing order creation tool:
    - create_manufacturing_order: Create manufacturing orders with preview/confirm

    Args:
        mcp: FastMCP server instance to register tools with
    """
    mcp.tool()(create_manufacturing_order)
