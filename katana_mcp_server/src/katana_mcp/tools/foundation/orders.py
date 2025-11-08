"""Order fulfillment tools for Katana MCP Server.

Foundation tools for fulfilling manufacturing orders and sales orders.

These tools provide:
- fulfill_order: Complete manufacturing orders or fulfill sales orders
"""

from __future__ import annotations

import logging
from typing import Annotated, Literal, cast

from fastmcp import Context, FastMCP
from pydantic import BaseModel, Field

from katana_mcp.services import get_services
from katana_mcp.unpack import Unpack, unpack_pydantic_params
from katana_public_api_client.client_types import UNSET
from katana_public_api_client.models import (
    CreateSalesOrderFulfillmentBody,
    ManufacturingOrder,
    SalesOrder,
    UpdateManufacturingOrderRequest,
)

logger = logging.getLogger(__name__)

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


async def _fulfill_order_impl(
    request: FulfillOrderRequest, context: Context
) -> FulfillOrderResponse:
    """Implementation of fulfill_order tool.

    Fulfills manufacturing orders by marking them as DONE, or fulfills sales
    orders by creating a sales order fulfillment.

    Manufacturing orders:
    - Fetches the order to get current status
    - Preview mode: Shows what would happen (status change to DONE)
    - Confirm mode: Updates order status to DONE via PATCH /manufacturing_orders/{id}

    Sales orders:
    - Fetches the order to get current status
    - Preview mode: Shows what would happen (create fulfillment)
    - Confirm mode: Creates fulfillment via POST /sales_order_fulfillments

    Args:
        request: Request with order ID, type, and confirm flag
        context: Server context with KatanaClient

    Returns:
        FulfillOrderResponse with details of fulfillment

    Raises:
        ValueError: If validation fails
        Exception: If API call fails
    """
    logger.info(
        f"{'Previewing' if not request.confirm else 'Fulfilling'} {request.order_type} order {request.order_id}"
    )

    services = get_services(context)

    try:
        if request.order_type == "manufacturing":
            # Fetch manufacturing order
            from katana_public_api_client.api.manufacturing_order import (
                get_manufacturing_order as api_get_manufacturing_order,
            )

            mo_response = await api_get_manufacturing_order.asyncio_detailed(
                id=request.order_id, client=services.client
            )

            if mo_response.status_code != 200 or not isinstance(
                mo_response.parsed, ManufacturingOrder
            ):
                raise Exception(
                    f"Failed to fetch manufacturing order {request.order_id}: {mo_response.status_code}"
                )

            mo = mo_response.parsed

            # Extract order number safely
            order_number = (
                cast(str, mo.order_no)
                if not isinstance(mo.order_no, type(UNSET))
                else f"MO-{request.order_id}"
            )

            # Extract current status
            current_status = mo.status.value if mo.status else "UNKNOWN"

            # Build inventory update messages
            inventory_updates = [
                "Manufacturing order completion will update inventory based on BOM",
                "Finished goods will be added to stock",
                "Raw materials will be consumed from inventory",
            ]

            # Check current status and provide warnings
            warnings = []
            if current_status == "DONE":
                warnings.append(
                    f"Manufacturing order {order_number} is already completed"
                )
            elif current_status == "BLOCKED":
                warnings.append(
                    f"Manufacturing order {order_number} is blocked - review before completing"
                )

            # Preview mode - return what would happen
            if not request.confirm:
                logger.info(
                    f"Preview mode: Would complete manufacturing order {order_number}"
                )

                next_actions = [
                    "Review the manufacturing order details",
                    "Verify all production steps are complete",
                    "Set confirm=true to mark order as DONE",
                ]

                if current_status == "DONE":
                    next_actions = ["Order is already completed - no action needed"]

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

            # Confirm mode - actually update the order
            if current_status == "DONE":
                logger.info(f"Manufacturing order {order_number} is already completed")
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

            # Update order status to DONE
            from katana_public_api_client.api.manufacturing_order import (
                update_manufacturing_order as api_update_manufacturing_order,
            )

            update_request = UpdateManufacturingOrderRequest()
            # Set status via additional_properties since status field is not in the model
            update_request.additional_properties["status"] = "DONE"

            update_response = await api_update_manufacturing_order.asyncio_detailed(
                id=request.order_id, client=services.client, body=update_request
            )

            if update_response.status_code == 200 and isinstance(
                update_response.parsed, ManufacturingOrder
            ):
                updated_mo = update_response.parsed
                new_status = updated_mo.status.value if updated_mo.status else "UNKNOWN"

                logger.info(
                    f"Successfully marked manufacturing order {order_number} as DONE"
                )

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
            else:
                raise Exception(
                    f"API returned unexpected status: {update_response.status_code}"
                )

        else:  # sales order
            # Fetch sales order
            from katana_public_api_client.api.sales_order import (
                get_sales_order as api_get_sales_order,
            )

            so_response = await api_get_sales_order.asyncio_detailed(
                id=request.order_id, client=services.client
            )

            if so_response.status_code != 200 or not isinstance(
                so_response.parsed, SalesOrder
            ):
                raise Exception(
                    f"Failed to fetch sales order {request.order_id}: {so_response.status_code}"
                )

            so = so_response.parsed

            # Extract order number safely
            order_number = (
                cast(str, so.order_no)
                if not isinstance(so.order_no, type(UNSET))
                else f"SO-{request.order_id}"
            )

            # Extract current status
            current_status = so.status.value if so.status else "UNKNOWN"

            # Build inventory update messages
            inventory_updates = [
                "Sales order fulfillment will reduce available inventory",
                "Items will be marked as shipped/fulfilled",
                "Stock levels will be updated accordingly",
            ]

            # Check current status and provide warnings
            warnings = []
            if current_status in ["DELIVERED", "PARTIALLY_DELIVERED"]:
                warnings.append(f"Sales order {order_number} may already be delivered")

            # Preview mode - return what would happen
            if not request.confirm:
                logger.info(f"Preview mode: Would fulfill sales order {order_number}")

                next_actions = [
                    "Review the sales order details",
                    "Verify items are ready to ship",
                    "Set confirm=true to create fulfillment",
                ]

                if current_status in ["DELIVERED", "PARTIALLY_DELIVERED"]:
                    next_actions = [
                        "Order may already be delivered - verify before creating additional fulfillment"
                    ]

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

            # Confirm mode - create fulfillment
            # Note: Sales orders in Katana can have multiple fulfillments, so we don't
            # prevent fulfillment based on status

            # Create sales order fulfillment
            from katana_public_api_client.api.sales_order_fulfillment import (
                create_sales_order_fulfillment as api_create_sales_order_fulfillment,
            )

            fulfillment_body = CreateSalesOrderFulfillmentBody(
                sales_order_id=request.order_id
            )

            fulfillment_response = (
                await api_create_sales_order_fulfillment.asyncio_detailed(
                    client=services.client, body=fulfillment_body
                )
            )

            if fulfillment_response.status_code == 201:
                logger.info(
                    f"Successfully created fulfillment for sales order {order_number}"
                )

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
            else:
                raise Exception(
                    f"API returned unexpected status: {fulfillment_response.status_code}"
                )

    except Exception as e:
        logger.error(f"Failed to fulfill {request.order_type} order: {e}")
        raise


@unpack_pydantic_params
async def fulfill_order(
    request: Annotated[FulfillOrderRequest, Unpack()], context: Context
) -> FulfillOrderResponse:
    """Fulfill a manufacturing order or sales order with two-step confirmation.

    This tool supports a two-step confirmation process:
    1. Preview (confirm=false): Shows what would happen without making changes
    2. Confirm (confirm=true): Actually fulfills the order

    Manufacturing Orders:
    - Marks the order as DONE via PATCH /manufacturing_orders/{id}
    - Updates inventory based on bill of materials (BOM)
    - Adds finished goods to stock
    - Consumes raw materials from inventory

    Sales Orders:
    - Creates a fulfillment via POST /sales_order_fulfillments
    - Reduces available inventory
    - Marks items as shipped/fulfilled
    - Creates fulfillment record

    The tool handles different order statuses appropriately and provides
    warnings for edge cases (already completed, cancelled, blocked, etc.).

    Args:
        request: Request with order ID, type, and confirm flag
        context: Server context with KatanaClient

    Returns:
        FulfillOrderResponse with details of fulfillment

    Example:
        Preview Manufacturing Order:
            Request: {"order_id": 1234, "order_type": "manufacturing", "confirm": false}
            Returns: Preview showing order would be marked as DONE

        Confirm Manufacturing Order:
            Request: {"order_id": 1234, "order_type": "manufacturing", "confirm": true}
            Returns: Success message with updated status

        Preview Sales Order:
            Request: {"order_id": 5678, "order_type": "sales", "confirm": false}
            Returns: Preview showing fulfillment would be created

        Confirm Sales Order:
            Request: {"order_id": 5678, "order_type": "sales", "confirm": true}
            Returns: Success message with fulfillment details
    """
    return await _fulfill_order_impl(request, context)


def register_tools(mcp: FastMCP) -> None:
    """Register all order fulfillment tools with the FastMCP instance.

    Registers the fulfill_order tool for completing manufacturing orders
    and fulfilling sales orders.

    Args:
        mcp: FastMCP server instance to register tools with
    """
    mcp.tool()(fulfill_order)
