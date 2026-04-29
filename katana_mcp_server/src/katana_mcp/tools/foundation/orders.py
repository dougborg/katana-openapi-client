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
        warnings.append(
            f"BLOCK: Manufacturing order {order_number} is already completed. "
            "No further action will mark it DONE again."
        )
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
    """Fulfill a sales order by creating a DELIVERED fulfillment record.

    The Katana API ``POST /sales_order_fulfillments`` requires per-row
    fulfillment input (``sales_order_fulfillment_rows``: each carrying a
    ``sales_order_row_id`` and a ``quantity``). The tool fetches the sales
    order's rows and ships the full quantity of each — the standard
    "deliver everything ordered" case. For partial fulfillments the user
    should use the Katana UI directly; the tool's MCP surface intentionally
    keeps the simple case simple.
    """
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
    so_rows = unwrap_unset(so.sales_order_rows, []) or []

    # Build a row summary list the preview UI can render — one entry per
    # SO row. variant_id + qty is what the user needs to recognise the
    # shipment; SKU resolution would require a per-row variant fetch and
    # isn't worth the latency cost on a preview.
    inventory_updates: list[str] = []
    for row in so_rows:
        rid = row.id
        vid = row.variant_id
        qty = row.quantity
        inventory_updates.append(
            f"Row {rid}: ship {qty} of variant {vid} (full ordered quantity)"
        )
    if not inventory_updates:
        inventory_updates.append("(no rows on this sales order)")

    warnings: list[str] = []
    if current_status in ("DELIVERED", "PARTIALLY_DELIVERED"):
        warnings.append(
            f"BLOCK: Sales order {order_number} status is {current_status}. "
            "Creating another fulfillment may double-ship items."
        )
    if not so_rows:
        warnings.append(f"BLOCK: Sales order {order_number} has no rows to fulfill.")

    if not request.confirm:
        has_block = any(w.startswith("BLOCK:") for w in warnings)
        next_actions = (
            ["Resolve the issue above (cancel and inspect via the Katana UI)"]
            if has_block
            else [
                "Review the row list above",
                "Set confirm=true to create a DELIVERED fulfillment for the full order",
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
            message=(
                f"Preview: Would fulfill sales order {order_number} "
                f"({len(so_rows)} row(s), currently {current_status})"
            ),
        )

    # Refuse on confirm if the order is already in a delivered state — the
    # preview's BLOCK warning would have suppressed the Confirm button in
    # the iframe, but we re-check here so direct/programmatic callers
    # (skipping the UI) get the same protection.
    if current_status in ("DELIVERED", "PARTIALLY_DELIVERED"):
        return FulfillOrderResponse(
            order_id=request.order_id,
            order_type="sales",
            order_number=order_number,
            status=current_status,
            is_preview=False,
            inventory_updates=[],
            warnings=warnings,
            next_actions=["No action taken — order already delivered"],
            message=(
                f"Sales order {order_number} is already {current_status}; refusing "
                "to create a duplicate fulfillment"
            ),
        )
    if not so_rows:
        raise ValueError(f"Sales order {order_number} has no rows to fulfill")

    from katana_public_api_client.api.sales_order_fulfillment import (
        create_sales_order_fulfillment as api_create_fulfillment,
    )
    from katana_public_api_client.models import (
        CreateSalesOrderFulfillmentRequest,
        SalesOrderFulfillment,
        SalesOrderFulfillmentRowRequest,
        SalesOrderFulfillmentStatus,
    )

    fulfill_rows = [
        SalesOrderFulfillmentRowRequest(
            sales_order_row_id=row.id,
            quantity=row.quantity,
        )
        for row in so_rows
    ]
    fulfill_request = CreateSalesOrderFulfillmentRequest(
        sales_order_id=request.order_id,
        status=SalesOrderFulfillmentStatus.DELIVERED,
        sales_order_fulfillment_rows=fulfill_rows,
    )
    fulfill_response = await api_create_fulfillment.asyncio_detailed(
        client=services.client, body=fulfill_request
    )
    fulfillment = unwrap_as(fulfill_response, SalesOrderFulfillment)

    logger.info(
        f"Created sales order fulfillment {fulfillment.id} for SO {order_number} "
        f"({len(fulfill_rows)} row(s) DELIVERED)"
    )
    return FulfillOrderResponse(
        order_id=request.order_id,
        order_type="sales",
        order_number=order_number,
        status="DELIVERED",
        is_preview=False,
        inventory_updates=[
            f"Created fulfillment {fulfillment.id} marking {len(fulfill_rows)} row(s) DELIVERED"
        ],
        warnings=warnings,
        next_actions=[
            f"Sales order {order_number} marked DELIVERED",
            "Inventory has been adjusted for shipped items",
        ],
        message=(
            f"Successfully fulfilled sales order {order_number} "
            f"({len(fulfill_rows)} row(s), fulfillment id={fulfillment.id})"
        ),
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
