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
from katana_public_api_client.domain.converters import unwrap_unset
from katana_public_api_client.utils import unwrap_data

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

        # Parse response - extract data list from Response
        orders_data = unwrap_data(response, raise_on_error=False, default=[])

        # Aggregate into orders list
        orders = []
        status_counts: dict[str, int] = {}

        for order in orders_data:
            # Extract status - attrs models have all fields defined
            order_status = unwrap_unset(order.status, None)
            status = order_status.value if order_status else "unknown"
            status_counts[status] = status_counts.get(status, 0) + 1

            # Prefer order_created_date, fall back to created_at
            order_created_date = unwrap_unset(order.order_created_date, None)
            created_at = unwrap_unset(order.created_at, None)
            created_at_str = (
                order_created_date.isoformat()
                if order_created_date
                else (created_at.isoformat() if created_at else None)
            )
            delivery_date = unwrap_unset(order.delivery_date, None)

            orders.append(
                {
                    "id": order.id,
                    "order_number": order.order_no,
                    "customer_id": order.customer_id,
                    "status": status,
                    "created_at": created_at_str,
                    "delivery_date": delivery_date.isoformat()
                    if delivery_date
                    else None,
                    "total": unwrap_unset(order.total, None),
                    "currency": unwrap_unset(order.currency, None),
                    "source": unwrap_unset(order.source, None),
                    "location_id": order.location_id,
                    "notes": unwrap_unset(order.additional_info, None),
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

        # Parse response - extract data list from Response
        orders_data = unwrap_data(response, raise_on_error=False, default=[])

        orders = []
        status_counts: dict[str, int] = {}

        for order in orders_data:
            # Extract status - attrs models have all fields defined
            order_status = unwrap_unset(order.status, None)
            status = order_status.value if order_status else "unknown"
            status_counts[status] = status_counts.get(status, 0) + 1

            # Extract dates
            created_at = unwrap_unset(order.created_at, None)
            expected_delivery_date = unwrap_unset(order.expected_delivery_date, None)

            orders.append(
                {
                    "id": order.id,
                    "order_number": unwrap_unset(order.order_no, None),
                    "supplier_id": unwrap_unset(order.supplier_id, None),
                    "status": status,
                    "created_at": created_at.isoformat() if created_at else None,
                    "expected_delivery": expected_delivery_date.isoformat()
                    if expected_delivery_date
                    else None,
                    "total": unwrap_unset(order.total, None),
                    "currency": unwrap_unset(order.currency, None),
                    "location_id": unwrap_unset(order.location_id, None),
                    "notes": unwrap_unset(order.additional_info, None),
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

        # Parse response - extract data list from Response
        orders_data = unwrap_data(response, raise_on_error=False, default=[])

        orders = []
        status_counts: dict[str, int] = {}

        for order in orders_data:
            # Extract status - attrs models have all fields defined
            order_status = unwrap_unset(order.status, None)
            status = order_status.value if order_status else "unknown"
            status_counts[status] = status_counts.get(status, 0) + 1

            # Extract dates
            created_at = unwrap_unset(order.created_at, None)
            production_deadline_date = unwrap_unset(
                order.production_deadline_date, None
            )

            orders.append(
                {
                    "id": order.id,
                    "mo_number": unwrap_unset(order.mo_number, None),
                    "variant_id": unwrap_unset(order.variant_id, None),
                    "status": status,
                    "created_at": created_at.isoformat() if created_at else None,
                    "production_deadline": production_deadline_date.isoformat()
                    if production_deadline_date
                    else None,
                    "planned_quantity": unwrap_unset(order.planned_quantity, None),
                    "quantity_done": unwrap_unset(order.quantity_done, None),
                    "location_id": unwrap_unset(order.location_id, None),
                    "notes": unwrap_unset(order.additional_info, None),
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
