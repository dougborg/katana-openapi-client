"""Order fulfillment tools for Katana MCP Server.

Foundation tools for fulfilling manufacturing orders and sales orders.

These tools provide:
- fulfill_order: Complete manufacturing orders or fulfill sales orders
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Literal

from fastmcp import Context, FastMCP
from fastmcp.tools import ToolResult
from pydantic import BaseModel, Field

from katana_mcp.logging import get_logger, observe_tool
from katana_mcp.services import get_services
from katana_mcp.tools.schemas import ConfirmationResult, require_confirmation
from katana_mcp.tools.tool_result_utils import make_tool_result
from katana_mcp.unpack import Unpack, unpack_pydantic_params
from katana_public_api_client.domain.converters import unwrap_unset
from katana_public_api_client.models import (
    CreateSalesOrderFulfillmentRequest,
    ManufacturingOrder,
    SalesOrder,
    UpdateManufacturingOrderRequest,
)
from katana_public_api_client.utils import is_success, unwrap, unwrap_as

logger = get_logger(__name__)

# ============================================================================
# Tool: fulfill_order
# ============================================================================


class FulfillOrderRequest(BaseModel):
    """Request to fulfill an order."""

    order_id: int = Field(..., description="Order ID to fulfill")
    order_type: Literal["manufacturing", "sales"] = Field(
        ..., description="Type of order (manufacturing or sales)"
    )
    confirm: bool = Field(
        False, description="If false, returns preview. If true, fulfills order."
    )


class FulfillOrderResponse(BaseModel):
    """Response from fulfilling an order."""

    order_id: int
    order_type: str
    order_number: str
    status: str
    is_preview: bool
    inventory_updates: list[str] = Field(
        default_factory=list, description="Inventory changes made or to be made"
    )
    warnings: list[str] = Field(default_factory=list, description="Warning messages")
    next_actions: list[str] = Field(
        default_factory=list, description="Suggested next steps"
    )
    message: str


def _fulfill_response_to_tool_result(response: FulfillOrderResponse) -> ToolResult:
    """Convert FulfillOrderResponse to ToolResult with markdown + Prefab UI."""
    from katana_mcp.tools.prefab_ui import (
        build_fulfill_preview_ui,
        build_fulfill_success_ui,
    )

    # Format lists for template
    inventory_updates_text = (
        "\n".join(f"- {update}" for update in response.inventory_updates)
        if response.inventory_updates
        else "No inventory updates"
    )

    next_steps_text = (
        "\n".join(f"- {action}" for action in response.next_actions)
        if response.next_actions
        else "No next steps"
    )

    response_dict = response.model_dump()
    if response.is_preview:
        ui = build_fulfill_preview_ui(response_dict)
    else:
        ui = build_fulfill_success_ui(response_dict)

    return make_tool_result(
        response,
        "order_fulfilled",
        ui=ui,
        order_type=response.order_type.title(),
        order_number=response.order_number,
        order_id=response.order_id,
        fulfilled_at=datetime.now(UTC).isoformat(),
        items_count="N/A",  # Not available in fulfill response
        total_value="N/A",  # Not available in fulfill response
        status=response.status,
        inventory_updates=inventory_updates_text,
        next_steps=next_steps_text,
    )


async def _fulfill_manufacturing_order(
    request: FulfillOrderRequest, context: Context
) -> FulfillOrderResponse:
    """Fulfill a manufacturing order by marking it as DONE."""
    from katana_public_api_client.api.manufacturing_order import (
        get_manufacturing_order as api_get_manufacturing_order,
    )

    services = get_services(context)
    mo_response = await api_get_manufacturing_order.asyncio_detailed(
        id=request.order_id, client=services.client
    )
    mo = unwrap_as(mo_response, ManufacturingOrder)
    order_number = unwrap_unset(mo.order_no, f"MO-{request.order_id}")
    current_status = mo.status.value if mo.status else "UNKNOWN"

    inventory_updates = [
        "Manufacturing order completion will update inventory based on BOM",
        "Finished goods will be added to stock",
        "Raw materials will be consumed from inventory",
    ]

    warnings: list[str] = []
    if current_status == "DONE":
        warnings.append(f"Manufacturing order {order_number} is already completed")
    elif current_status == "BLOCKED":
        warnings.append(
            f"Manufacturing order {order_number} is blocked - review before completing"
        )

    if not request.confirm:
        next_actions = (
            ["Order is already completed - no action needed"]
            if current_status == "DONE"
            else [
                "Review the manufacturing order details",
                "Verify all production steps are complete",
                "Set confirm=true to mark order as DONE",
            ]
        )
        return FulfillOrderResponse(
            order_id=request.order_id,
            order_type="manufacturing",
            order_number=order_number,
            status=current_status,
            is_preview=True,
            inventory_updates=inventory_updates,
            warnings=warnings,
            next_actions=next_actions,
            message=f"Preview: Would mark manufacturing order {order_number} as DONE (currently {current_status})",
        )

    if current_status == "DONE":
        return FulfillOrderResponse(
            order_id=request.order_id,
            order_type="manufacturing",
            order_number=order_number,
            status=current_status,
            is_preview=False,
            inventory_updates=[],
            warnings=warnings,
            next_actions=["Order is already completed"],
            message=f"Manufacturing order {order_number} is already completed",
        )

    confirmation = await require_confirmation(
        context,
        f"Mark manufacturing order {order_number} as DONE and update inventory?",
    )
    if confirmation != ConfirmationResult.CONFIRMED:
        return FulfillOrderResponse(
            order_id=request.order_id,
            order_type="manufacturing",
            order_number=order_number,
            status=current_status,
            is_preview=True,
            inventory_updates=inventory_updates,
            warnings=warnings,
            message=f"Manufacturing order fulfillment {confirmation} by user",
            next_actions=["Review the order details and try again with confirm=true"],
        )

    from katana_public_api_client.api.manufacturing_order import (
        update_manufacturing_order as api_update_manufacturing_order,
    )
    from katana_public_api_client.models.manufacturing_order_status import (
        ManufacturingOrderStatus,
    )

    update_req = UpdateManufacturingOrderRequest(
        status=ManufacturingOrderStatus.DONE,
    )
    update_response = await api_update_manufacturing_order.asyncio_detailed(
        id=request.order_id, client=services.client, body=update_req
    )
    updated_mo = unwrap_as(update_response, ManufacturingOrder)
    new_status = updated_mo.status.value if updated_mo.status else "UNKNOWN"

    logger.info(f"Successfully marked manufacturing order {order_number} as DONE")
    return FulfillOrderResponse(
        order_id=request.order_id,
        order_type="manufacturing",
        order_number=order_number,
        status=new_status,
        is_preview=False,
        inventory_updates=inventory_updates,
        warnings=warnings,
        next_actions=[
            f"Manufacturing order {order_number} completed",
            "Inventory has been updated",
            "Check stock levels for finished goods",
        ],
        message=f"Successfully marked manufacturing order {order_number} as DONE",
    )


async def _fulfill_sales_order(
    request: FulfillOrderRequest, context: Context
) -> FulfillOrderResponse:
    """Fulfill a sales order by creating a fulfillment record."""
    from katana_public_api_client.api.sales_order import (
        get_sales_order as api_get_sales_order,
    )

    services = get_services(context)
    so_response = await api_get_sales_order.asyncio_detailed(
        id=request.order_id, client=services.client
    )
    so = unwrap_as(so_response, SalesOrder)
    order_number = unwrap_unset(so.order_no, f"SO-{request.order_id}")
    current_status = so.status.value if so.status else "UNKNOWN"

    inventory_updates = [
        "Sales order fulfillment will reduce available inventory",
        "Items will be marked as shipped/fulfilled",
        "Stock levels will be updated accordingly",
    ]

    warnings: list[str] = []
    if current_status in ("DELIVERED", "PARTIALLY_DELIVERED"):
        warnings.append(f"Sales order {order_number} may already be delivered")

    if not request.confirm:
        next_actions = (
            [
                "Order may already be delivered - verify before creating additional fulfillment"
            ]
            if current_status in ("DELIVERED", "PARTIALLY_DELIVERED")
            else [
                "Review the sales order details",
                "Verify items are ready to ship",
                "Set confirm=true to create fulfillment",
            ]
        )
        return FulfillOrderResponse(
            order_id=request.order_id,
            order_type="sales",
            order_number=order_number,
            status=current_status,
            is_preview=True,
            inventory_updates=inventory_updates,
            warnings=warnings,
            next_actions=next_actions,
            message=f"Preview: Would fulfill sales order {order_number} (currently {current_status})",
        )

    # Sales orders can have multiple fulfillments, so we don't prevent
    # fulfillment based on status
    confirmation = await require_confirmation(
        context,
        f"Fulfill sales order {order_number} and update inventory?",
    )
    if confirmation != ConfirmationResult.CONFIRMED:
        return FulfillOrderResponse(
            order_id=request.order_id,
            order_type="sales",
            order_number=order_number,
            status=current_status,
            is_preview=True,
            inventory_updates=inventory_updates,
            warnings=warnings,
            message=f"Sales order fulfillment {confirmation} by user",
            next_actions=["Review the order details and try again with confirm=true"],
        )

    from katana_public_api_client.api.sales_order_fulfillment import (
        create_sales_order_fulfillment as api_create_sales_order_fulfillment,
    )

    fulfillment_body = CreateSalesOrderFulfillmentRequest(
        sales_order_id=request.order_id
    )
    fulfillment_response = await api_create_sales_order_fulfillment.asyncio_detailed(
        client=services.client, body=fulfillment_body
    )
    if not is_success(fulfillment_response):
        unwrap(fulfillment_response)

    logger.info(f"Successfully created fulfillment for sales order {order_number}")
    return FulfillOrderResponse(
        order_id=request.order_id,
        order_type="sales",
        order_number=order_number,
        status="FULFILLED",
        is_preview=False,
        inventory_updates=inventory_updates,
        warnings=warnings,
        next_actions=[
            f"Sales order {order_number} fulfilled",
            "Inventory has been updated",
            "Fulfillment record created",
        ],
        message=f"Successfully fulfilled sales order {order_number}",
    )


async def _fulfill_order_impl(
    request: FulfillOrderRequest, context: Context
) -> FulfillOrderResponse:
    """Dispatch to the appropriate fulfillment handler."""
    logger.info(
        f"{'Previewing' if not request.confirm else 'Fulfilling'} {request.order_type} order {request.order_id}"
    )
    try:
        if request.order_type == "manufacturing":
            return await _fulfill_manufacturing_order(request, context)
        return await _fulfill_sales_order(request, context)
    except Exception as e:
        logger.error(f"Failed to fulfill {request.order_type} order: {e}")
        raise


@observe_tool
@unpack_pydantic_params
async def fulfill_order(
    request: Annotated[FulfillOrderRequest, Unpack()], context: Context
) -> ToolResult:
    """Complete a manufacturing order (mark DONE) or fulfill a sales order (ship items).

    Destructive operation that updates inventory. Two-step flow: confirm=false to
    preview what would happen, confirm=true to execute (prompts for confirmation).

    Manufacturing: marks order DONE, adds finished goods, consumes raw materials.
    Sales: creates a fulfillment record, reduces available inventory.
    """
    response = await _fulfill_order_impl(request, context)
    return _fulfill_response_to_tool_result(response)


def register_tools(mcp: FastMCP) -> None:
    """Register all order fulfillment tools with the FastMCP instance.

    Args:
        mcp: FastMCP server instance to register tools with
    """
    from mcp.types import ToolAnnotations

    mcp.tool(
        tags={"orders", "write", "destructive"},
        annotations=ToolAnnotations(
            readOnlyHint=False, destructiveHint=True, openWorldHint=True
        ),
    )(fulfill_order)
