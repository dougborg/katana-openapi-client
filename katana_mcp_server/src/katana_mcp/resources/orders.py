"""Order resources for Katana MCP Server.

Provides read-only access to order data including sales orders, purchase orders,
and manufacturing orders.
"""

# NOTE: Do not use 'from __future__ import annotations' in this module
# FastMCP requires Context to be the actual class, not a string annotation

import time
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from fastmcp import Context, FastMCP
from pydantic import BaseModel, Field

from katana_mcp.logging import get_logger
from katana_mcp.services import get_services

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)


# ============================================================================
# Resource 1: katana://sales-orders
# ============================================================================


class SalesOrdersSummary(BaseModel):
    """Summary statistics for sales orders."""

    total_orders: int = Field(..., description="Total number of sales orders")
    orders_in_response: int = Field(
        ..., description="Number of orders in this response"
    )
    status_counts: dict[str, int] = Field(..., description="Count of orders by status")


class SalesOrdersResource(BaseModel):
    """Response structure for sales orders resource."""

    generated_at: str = Field(
        ..., description="ISO timestamp when resource was generated"
    )
    summary: SalesOrdersSummary = Field(..., description="Summary statistics")
    orders: list[dict] = Field(..., description="List of sales orders")
    next_actions: list[str] = Field(
        default_factory=list, description="Suggested next actions"
    )


async def _get_sales_orders_impl(context: Context) -> SalesOrdersResource:
    """Implementation of sales orders resource.

    Fetches open/pending sales orders from Katana.

    Args:
        context: FastMCP context for accessing the Katana client

    Returns:
        Structured sales orders data with summary and orders list

    Raises:
        Exception: If API calls fail
    """
    logger.info("sales_orders_resource_started")
    start_time = time.monotonic()

    try:
        services = get_services(context)

        # Import the generated API function
        from katana_public_api_client.api.sales_order import get_all_sales_orders

        # Fetch recent sales orders
        response = await get_all_sales_orders.asyncio_detailed(
            client=services.client, limit=50
        )

        # Parse response
        orders_data = response.parsed if response.parsed else []

        # Aggregate into orders list
        orders = []
        status_counts: dict[str, int] = {}

        for order in orders_data:
            status = (
                order.status.value
                if hasattr(order, "status") and order.status
                else "unknown"
            )
            status_counts[status] = status_counts.get(status, 0) + 1

            orders.append(
                {
                    "id": order.id if hasattr(order, "id") else None,
                    "order_number": order.order_no
                    if hasattr(order, "order_no")
                    else None,
                    "customer_id": order.customer_id
                    if hasattr(order, "customer_id")
                    else None,
                    "status": status,
                    "created_at": (
                        order.order_created_date.isoformat()
                        if hasattr(order, "order_created_date")
                        and order.order_created_date
                        else (
                            order.created_at.isoformat()
                            if hasattr(order, "created_at") and order.created_at
                            else None
                        )
                    ),
                    "delivery_date": (
                        order.delivery_date.isoformat()
                        if hasattr(order, "delivery_date") and order.delivery_date
                        else None
                    ),
                    "total": order.total if hasattr(order, "total") else None,
                    "currency": order.currency if hasattr(order, "currency") else None,
                    "source": order.source if hasattr(order, "source") else None,
                    "location_id": order.location_id
                    if hasattr(order, "location_id")
                    else None,
                    "notes": order.additional_info
                    if hasattr(order, "additional_info")
                    else None,
                }
            )

        # Sort by created date (most recent first)
        orders.sort(key=lambda o: o.get("created_at") or "", reverse=True)

        # Build summary
        summary = SalesOrdersSummary(
            total_orders=len(orders_data),
            orders_in_response=len(orders),
            status_counts=status_counts,
        )

        duration_ms = round((time.monotonic() - start_time) * 1000, 2)
        logger.info(
            "sales_orders_resource_completed",
            total_orders=summary.total_orders,
            duration_ms=duration_ms,
        )

        return SalesOrdersResource(
            generated_at=datetime.now(UTC).isoformat(),
            summary=summary,
            orders=orders,
            next_actions=[
                "Use fulfill_order tool to complete ready orders",
                "Check inventory for orders awaiting stock",
                "Review orders approaching delivery date",
            ],
        )

    except Exception as e:
        duration_ms = round((time.monotonic() - start_time) * 1000, 2)
        logger.error(
            "sales_orders_resource_failed",
            error=str(e),
            error_type=type(e).__name__,
            duration_ms=duration_ms,
            exc_info=True,
        )
        raise


async def get_sales_orders(context: Context) -> dict:
    """Get sales orders resource.

    Provides view of recent sales orders with status and delivery information.

    **Resource URI:** `katana://sales-orders`

    **Purpose:** Monitor customer orders and fulfillment progress

    **Refresh Rate:** On-demand (no caching in v0.1.0)

    **Data Includes:**
    - Order numbers and customer IDs
    - Order status and delivery dates
    - Total amounts and currency
    - Source and location information
    - Notes and additional info

    **Use Cases:**
    - Monitor open sales orders
    - Track fulfillment status
    - Identify approaching deadlines
    - Review order details

    **Related Tools:**
    - `fulfill_order` - Complete and ship orders
    - `check_inventory` - Verify stock availability

    Args:
        context: FastMCP context providing access to Katana client

    Returns:
        Dictionary containing sales orders data with summary and orders list
    """
    response = await _get_sales_orders_impl(context)
    return response.model_dump()


# ============================================================================
# Resource 2: katana://purchase-orders
# ============================================================================


class PurchaseOrdersSummary(BaseModel):
    """Summary statistics for purchase orders."""

    total_orders: int = Field(..., description="Total number of purchase orders")
    orders_in_response: int = Field(
        ..., description="Number of orders in this response"
    )
    status_counts: dict[str, int] = Field(..., description="Count of orders by status")


class PurchaseOrdersResource(BaseModel):
    """Response structure for purchase orders resource."""

    generated_at: str = Field(
        ..., description="ISO timestamp when resource was generated"
    )
    summary: PurchaseOrdersSummary = Field(..., description="Summary statistics")
    orders: list[dict] = Field(..., description="List of purchase orders")
    next_actions: list[str] = Field(
        default_factory=list, description="Suggested next actions"
    )


async def _get_purchase_orders_impl(context: Context) -> PurchaseOrdersResource:
    """Implementation of purchase orders resource."""
    logger.info("purchase_orders_resource_started")
    start_time = time.monotonic()

    try:
        services = get_services(context)

        from katana_public_api_client.api.purchase_order import find_purchase_orders

        response = await find_purchase_orders.asyncio_detailed(
            client=services.client, limit=50
        )

        orders_data = response.parsed if response.parsed else []

        orders = []
        status_counts: dict[str, int] = {}

        for order in orders_data:
            status = (
                order.status.value
                if hasattr(order, "status") and order.status
                else "unknown"
            )
            status_counts[status] = status_counts.get(status, 0) + 1

            orders.append(
                {
                    "id": order.id if hasattr(order, "id") else None,
                    "order_number": order.order_no
                    if hasattr(order, "order_no")
                    else None,
                    "supplier_id": order.supplier_id
                    if hasattr(order, "supplier_id")
                    else None,
                    "status": status,
                    "created_at": (
                        order.created_at.isoformat()
                        if hasattr(order, "created_at") and order.created_at
                        else None
                    ),
                    "expected_delivery": (
                        order.expected_delivery_date.isoformat()
                        if hasattr(order, "expected_delivery_date")
                        and order.expected_delivery_date
                        else None
                    ),
                    "total": order.total if hasattr(order, "total") else None,
                    "currency": order.currency if hasattr(order, "currency") else None,
                    "location_id": order.location_id
                    if hasattr(order, "location_id")
                    else None,
                    "notes": order.additional_info
                    if hasattr(order, "additional_info")
                    else None,
                }
            )

        orders.sort(key=lambda o: o.get("created_at") or "", reverse=True)

        summary = PurchaseOrdersSummary(
            total_orders=len(orders_data),
            orders_in_response=len(orders),
            status_counts=status_counts,
        )

        duration_ms = round((time.monotonic() - start_time) * 1000, 2)
        logger.info(
            "purchase_orders_resource_completed",
            total_orders=summary.total_orders,
            duration_ms=duration_ms,
        )

        return PurchaseOrdersResource(
            generated_at=datetime.now(UTC).isoformat(),
            summary=summary,
            orders=orders,
            next_actions=[
                "Use receive_purchase_order tool to receive delivered orders",
                "Use verify_order_document tool to validate supplier documents",
                "Review orders approaching expected delivery date",
            ],
        )

    except Exception as e:
        duration_ms = round((time.monotonic() - start_time) * 1000, 2)
        logger.error(
            "purchase_orders_resource_failed",
            error=str(e),
            error_type=type(e).__name__,
            duration_ms=duration_ms,
            exc_info=True,
        )
        raise


async def get_purchase_orders(context: Context) -> dict:
    """Get purchase orders resource."""
    response = await _get_purchase_orders_impl(context)
    return response.model_dump()


# ============================================================================
# Resource 3: katana://manufacturing-orders
# ============================================================================


class ManufacturingOrdersSummary(BaseModel):
    """Summary statistics for manufacturing orders."""

    total_orders: int = Field(..., description="Total number of manufacturing orders")
    orders_in_response: int = Field(
        ..., description="Number of orders in this response"
    )
    status_counts: dict[str, int] = Field(..., description="Count of orders by status")


class ManufacturingOrdersResource(BaseModel):
    """Response structure for manufacturing orders resource."""

    generated_at: str = Field(
        ..., description="ISO timestamp when resource was generated"
    )
    summary: ManufacturingOrdersSummary = Field(..., description="Summary statistics")
    orders: list[dict] = Field(..., description="List of manufacturing orders")
    next_actions: list[str] = Field(
        default_factory=list, description="Suggested next actions"
    )


async def _get_manufacturing_orders_impl(
    context: Context,
) -> ManufacturingOrdersResource:
    """Implementation of manufacturing orders resource."""
    logger.info("manufacturing_orders_resource_started")
    start_time = time.monotonic()

    try:
        services = get_services(context)

        from katana_public_api_client.api.manufacturing_order import (
            get_all_manufacturing_orders,
        )

        response = await get_all_manufacturing_orders.asyncio_detailed(
            client=services.client, limit=50
        )

        orders_data = response.parsed if response.parsed else []

        orders = []
        status_counts: dict[str, int] = {}

        for order in orders_data:
            status = (
                order.status.value
                if hasattr(order, "status") and order.status
                else "unknown"
            )
            status_counts[status] = status_counts.get(status, 0) + 1

            orders.append(
                {
                    "id": order.id if hasattr(order, "id") else None,
                    "mo_number": order.mo_number
                    if hasattr(order, "mo_number")
                    else None,
                    "variant_id": order.variant_id
                    if hasattr(order, "variant_id")
                    else None,
                    "status": status,
                    "created_at": (
                        order.created_at.isoformat()
                        if hasattr(order, "created_at") and order.created_at
                        else None
                    ),
                    "production_deadline": (
                        order.production_deadline_date.isoformat()
                        if hasattr(order, "production_deadline_date")
                        and order.production_deadline_date
                        else None
                    ),
                    "planned_quantity": (
                        order.planned_quantity
                        if hasattr(order, "planned_quantity")
                        else None
                    ),
                    "quantity_done": (
                        order.quantity_done if hasattr(order, "quantity_done") else None
                    ),
                    "location_id": order.location_id
                    if hasattr(order, "location_id")
                    else None,
                    "notes": order.additional_info
                    if hasattr(order, "additional_info")
                    else None,
                }
            )

        orders.sort(key=lambda o: o.get("created_at") or "", reverse=True)

        summary = ManufacturingOrdersSummary(
            total_orders=len(orders_data),
            orders_in_response=len(orders),
            status_counts=status_counts,
        )

        duration_ms = round((time.monotonic() - start_time) * 1000, 2)
        logger.info(
            "manufacturing_orders_resource_completed",
            total_orders=summary.total_orders,
            duration_ms=duration_ms,
        )

        return ManufacturingOrdersResource(
            generated_at=datetime.now(UTC).isoformat(),
            summary=summary,
            orders=orders,
            next_actions=[
                "Use fulfill_order tool to mark completed orders as done",
                "Check ingredient availability for pending orders",
                "Review orders approaching production deadline",
            ],
        )

    except Exception as e:
        duration_ms = round((time.monotonic() - start_time) * 1000, 2)
        logger.error(
            "manufacturing_orders_resource_failed",
            error=str(e),
            error_type=type(e).__name__,
            duration_ms=duration_ms,
            exc_info=True,
        )
        raise


async def get_manufacturing_orders(context: Context) -> dict:
    """Get manufacturing orders resource."""
    response = await _get_manufacturing_orders_impl(context)
    return response.model_dump()


def register_resources(mcp: FastMCP) -> None:
    """Register all order resources with the FastMCP instance.

    Args:
        mcp: FastMCP server instance to register resources with
    """
    # Register katana://sales-orders resource
    mcp.resource(
        uri="katana://sales-orders",
        name="Sales Orders",
        description="Recent sales orders with status and delivery information",
        mime_type="application/json",
    )(get_sales_orders)

    # Register katana://purchase-orders resource
    mcp.resource(
        uri="katana://purchase-orders",
        name="Purchase Orders",
        description="Recent purchase orders with status and delivery information",
        mime_type="application/json",
    )(get_purchase_orders)

    # Register katana://manufacturing-orders resource
    mcp.resource(
        uri="katana://manufacturing-orders",
        name="Manufacturing Orders",
        description="Active manufacturing orders with production status",
        mime_type="application/json",
    )(get_manufacturing_orders)


__all__ = ["register_resources"]
