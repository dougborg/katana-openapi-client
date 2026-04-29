"""Order fulfillment tools for Katana MCP Server.

Foundation tools for fulfilling manufacturing orders and sales orders.

These tools provide:
- fulfill_order: Complete manufacturing orders or fulfill sales orders
"""

from __future__ import annotations

from typing import Annotated, Literal

from fastmcp import Context, FastMCP
from fastmcp.tools import ToolResult
from pydantic import BaseModel, Field

from katana_mcp.logging import get_logger, observe_tool
from katana_mcp.services import get_services
from katana_mcp.tools.tool_result_utils import UI_META, make_tool_result
from katana_mcp.unpack import Unpack, unpack_pydantic_params
from katana_public_api_client.domain.converters import unwrap_unset
from katana_public_api_client.models import (
    ManufacturingOrder,
    SalesOrder,
    UpdateManufacturingOrderRequest,
)
from katana_public_api_client.utils import unwrap_as

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
    """Convert FulfillOrderResponse to ToolResult with the appropriate Prefab UI."""
    from katana_mcp.tools.prefab_ui import (
        build_fulfill_preview_ui,
        build_fulfill_success_ui,
    )

    response_dict = response.model_dump()
    if response.is_preview:
        ui = build_fulfill_preview_ui(response_dict)
    else:
        ui = build_fulfill_success_ui(response_dict)

    return make_tool_result(response, ui=ui)


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

    # confirm=true — mark MO as DONE via API. Per spec, the host (driven by
    # destructiveHint annotation) confirmed with the user before invoking;
    # the server does not gate further.
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

    # confirm=true — sales orders can have multiple fulfillments, so we
    # don't prevent on status. Per spec, the host (driven by destructiveHint
    # annotation) confirmed with the user before invoking.

    # The live API requires ``sales_order_fulfillment_rows`` (the line
    # items being fulfilled — variants, quantities, batch transactions).
    # Our current ``FulfillOrderRequest`` tool surface doesn't model
    # rows. Fail fast with a clear, actionable message rather than send
    # an empty array (which would 422 against live Katana with a
    # confusing validation error and consume an API call). The
    # row-aware extension is tracked for follow-up.
    raise NotImplementedError(
        "fulfill_order(order_type='sales', confirm=true) is not yet "
        "supported. The live Katana API requires per-row fulfillment "
        "input on POST /sales_order_fulfillments "
        "(``sales_order_fulfillment_rows``: variants, quantities, batch "
        "transactions), which this tool's request shape does not yet "
        "expose. Until the tool is extended (either to fetch the order's "
        "rows automatically or to accept fulfillment rows as input), use "
        "the Katana UI or a row-aware client to mark sales orders as "
        "fulfilled."
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
    preview what would happen, confirm=true to execute.

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
        meta=UI_META,
    )(fulfill_order)
