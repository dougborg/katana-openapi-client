"""Manufacturing order management tools for Katana MCP Server.

Foundation tools for creating manufacturing orders to initiate production.

These tools provide:
- create_manufacturing_order: Create manufacturing orders with preview/confirm pattern
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastmcp import Context, FastMCP
from fastmcp.tools.tool import ToolResult
from pydantic import BaseModel, Field

from katana_mcp.logging import get_logger, observe_tool
from katana_mcp.services import get_services
from katana_mcp.tools.schemas import ConfirmationResult, require_confirmation
from katana_mcp.tools.tool_result_utils import make_tool_result
from katana_mcp.unpack import Unpack, unpack_pydantic_params
from katana_public_api_client.domain.converters import to_unset, unwrap_unset
from katana_public_api_client.models import (
    CreateManufacturingOrderRequest as APICreateManufacturingOrderRequest,
    ManufacturingOrder,
)
from katana_public_api_client.utils import unwrap_as

logger = get_logger(__name__)

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

    # Confirm mode - use elicitation to get user confirmation before creating
    confirmation = await require_confirmation(
        context,
        f"Create manufacturing order for variant {request.variant_id} with quantity {request.planned_quantity}?",
    )

    if confirmation != ConfirmationResult.CONFIRMED:
        logger.info(
            f"User did not confirm creation of manufacturing order for variant {request.variant_id}"
        )
        return ManufacturingOrderResponse(
            variant_id=request.variant_id,
            planned_quantity=request.planned_quantity,
            location_id=request.location_id,
            order_created_date=request.order_created_date,
            production_deadline_date=request.production_deadline_date,
            additional_info=request.additional_info,
            is_preview=True,
            message=f"Manufacturing order creation {confirmation} by user",
            next_actions=["Review the order details and try again with confirm=true"],
        )

    # User confirmed - create the manufacturing order via API
    try:
        services = get_services(context)

        # Build API request
        api_request = APICreateManufacturingOrderRequest(
            variant_id=request.variant_id,
            planned_quantity=request.planned_quantity,
            location_id=request.location_id,
            order_created_date=to_unset(request.order_created_date),
            production_deadline_date=to_unset(request.production_deadline_date),
            additional_info=to_unset(request.additional_info),
        )

        # Call API
        from katana_public_api_client.api.manufacturing_order import (
            create_manufacturing_order as api_create_manufacturing_order,
        )

        response = await api_create_manufacturing_order.asyncio_detailed(
            client=services.client, body=api_request
        )

        # unwrap_as() raises typed exceptions on error, returns typed ManufacturingOrder
        mo = unwrap_as(response, ManufacturingOrder)
        logger.info(f"Successfully created manufacturing order ID {mo.id}")

        # Extract values using unwrap_unset for clean UNSET handling
        order_no = unwrap_unset(mo.order_no, None)
        variant_id = unwrap_unset(mo.variant_id, request.variant_id)
        planned_quantity = unwrap_unset(mo.planned_quantity, request.planned_quantity)
        location_id = unwrap_unset(mo.location_id, request.location_id)
        order_created_date = unwrap_unset(mo.order_created_date, None)
        production_deadline_date = unwrap_unset(mo.production_deadline_date, None)
        additional_info = unwrap_unset(mo.additional_info, None)
        mo_status = unwrap_unset(mo.status, None)
        status = mo_status.value if mo_status else None

        return ManufacturingOrderResponse(
            id=mo.id,
            order_no=order_no,
            variant_id=variant_id,
            planned_quantity=planned_quantity,
            location_id=location_id,
            status=status,
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

    except Exception as e:
        logger.error(f"Failed to create manufacturing order: {e}")
        raise


@observe_tool
@unpack_pydantic_params
async def create_manufacturing_order(
    request: Annotated[CreateManufacturingOrderRequest, Unpack()], context: Context
) -> ToolResult:
    """Create a manufacturing order to produce items.

    Two-step flow: confirm=false to preview, confirm=true to create (prompts
    for confirmation). Requires variant_id of the product to manufacture,
    planned_quantity, and location_id. Recipe and operation rows are created
    automatically from the product's recipe. Use search_items to find variant IDs.
    """
    response = await _create_manufacturing_order_impl(request, context)

    next_actions_text = "\n".join(f"- {a}" for a in response.next_actions) or "None"

    return make_tool_result(
        response,
        "manufacturing_order_created",
        id=response.id or "N/A",
        order_no=response.order_no or "N/A",
        variant_id=response.variant_id,
        planned_quantity=response.planned_quantity,
        location_id=response.location_id,
        status=response.status or ("PREVIEW" if response.is_preview else "N/A"),
        message=response.message,
        next_actions_text=next_actions_text,
    )


def register_tools(mcp: FastMCP) -> None:
    """Register all manufacturing order tools with the FastMCP instance.

    Args:
        mcp: FastMCP server instance to register tools with
    """
    from mcp.types import ToolAnnotations

    mcp.tool(
        tags={"orders", "manufacturing", "write"},
        annotations=ToolAnnotations(
            readOnlyHint=False, destructiveHint=False, openWorldHint=True
        ),
    )(create_manufacturing_order)
