"""Inventory resources for Katana MCP Server.

Provides read-only access to inventory data including items, stock movements,
and stock adjustments.
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
# Resource 1: katana://inventory/items
# ============================================================================


class InventoryItemsSummary(BaseModel):
    """Summary statistics for inventory items."""

    total_items: int = Field(..., description="Total number of items across all types")
    products: int = Field(..., description="Number of finished products")
    materials: int = Field(..., description="Number of raw materials/components")
    services: int = Field(..., description="Number of services")
    items_in_response: int = Field(..., description="Number of items in this response")
    low_stock_count: int | None = Field(
        None, description="Number of items below reorder threshold (if available)"
    )


class InventoryItemsResource(BaseModel):
    """Response structure for inventory items resource."""

    generated_at: str = Field(
        ..., description="ISO timestamp when resource was generated"
    )
    summary: InventoryItemsSummary = Field(..., description="Summary statistics")
    items: list[dict] = Field(..., description="List of inventory items with details")
    next_actions: list[str] = Field(
        default_factory=list, description="Suggested next actions"
    )


async def _get_inventory_items_impl(context: Context) -> InventoryItemsResource:
    """Implementation of inventory items resource.

    Fetches all products, materials, and services from Katana and aggregates
    them into a unified inventory view with stock levels and type information.

    Args:
        context: FastMCP context for accessing the Katana client

    Returns:
        Structured inventory data with summary and items list

    Raises:
        Exception: If API calls fail
    """
    logger.info("inventory_items_resource_started")
    start_time = time.monotonic()

    try:
        services = get_services(context)

        # Fetch all item types
        # TODO: Consider parallelizing with asyncio.gather() for better performance
        products_response = await services.client.products.list(limit=100)
        materials_response = await services.client.materials.list(limit=100)
        services_response = await services.client.services.list(limit=100)

        # Parse responses - handle both list and paginated response objects
        products = (
            products_response
            if isinstance(products_response, list)
            else getattr(products_response, "items", [])
        )
        materials = (
            materials_response
            if isinstance(materials_response, list)
            else getattr(materials_response, "items", [])
        )
        services_items = (
            services_response
            if isinstance(services_response, list)
            else getattr(services_response, "items", [])
        )

        # Aggregate into unified item list
        items = []

        # Add products
        for product in products:
            items.append(
                {
                    "id": product.id if hasattr(product, "id") else None,
                    "name": product.name if hasattr(product, "name") else "Unknown",
                    "type": "product",
                    "is_sellable": getattr(product, "is_sellable", False),
                    "is_producible": getattr(product, "is_producible", False),
                    "is_purchasable": getattr(product, "is_purchasable", False),
                }
            )

        # Add materials
        for material in materials:
            items.append(
                {
                    "id": material.id if hasattr(material, "id") else None,
                    "name": material.name if hasattr(material, "name") else "Unknown",
                    "type": "material",
                    "is_sellable": False,
                    "is_producible": False,
                    "is_purchasable": True,
                }
            )

        # Add services
        for service in services_items:
            items.append(
                {
                    "id": service.id if hasattr(service, "id") else None,
                    "name": service.name if hasattr(service, "name") else "Unknown",
                    "type": "service",
                    "is_sellable": getattr(service, "is_sellable", True),
                    "is_producible": False,
                    "is_purchasable": False,
                }
            )

        # Build summary
        summary = InventoryItemsSummary(
            total_items=len(products) + len(materials) + len(services_items),
            products=len(products),
            materials=len(materials),
            services=len(services_items),
            items_in_response=len(items),
        )

        duration_ms = round((time.monotonic() - start_time) * 1000, 2)
        logger.info(
            "inventory_items_resource_completed",
            total_items=summary.total_items,
            duration_ms=duration_ms,
        )

        return InventoryItemsResource(
            generated_at=datetime.now(UTC).isoformat(),
            summary=summary,
            items=items,
            next_actions=[
                "Use search_items tool to find specific items by name or SKU",
                "Use check_inventory tool to get detailed stock levels for a specific SKU",
                "Use list_low_stock_items tool to identify items needing reorder",
            ],
        )

    except Exception as e:
        duration_ms = round((time.monotonic() - start_time) * 1000, 2)
        logger.error(
            "inventory_items_resource_failed",
            error=str(e),
            error_type=type(e).__name__,
            duration_ms=duration_ms,
            exc_info=True,
        )
        raise


async def get_inventory_items(context: Context) -> dict:
    """Get inventory items resource.

    Provides complete catalog view with current inventory levels for all products,
    materials, and services in the Katana system.

    **Resource URI:** `katana://inventory/items`

    **Purpose:** Complete catalog view for searching and accessing items

    **Refresh Rate:** On-demand (no caching in v0.1.0)

    **Data Includes:**
    - All products, materials, and services
    - Item type and capabilities (sellable, producible, purchasable)
    - Summary statistics by type
    - Total item counts

    **Use Cases:**
    - Browse complete catalog
    - Find items by type
    - Get overview of inventory
    - Identify total item counts

    **Related Tools:**
    - `search_items` - Search for specific items by name or SKU
    - `check_inventory` - Get detailed stock info for a specific SKU
    - `list_low_stock_items` - Find items needing reorder

    **Example Response:**
    ```json
    {
      "generated_at": "2024-01-15T10:30:00Z",
      "summary": {
        "total_items": 150,
        "products": 50,
        "materials": 95,
        "services": 5,
        "items_in_response": 150
      },
      "items": [
        {
          "id": 123,
          "name": "Widget Pro",
          "type": "product",
          "is_sellable": true,
          "is_producible": true,
          "is_purchasable": false
        }
      ],
      "next_actions": [...]
    }
    ```

    Args:
        context: FastMCP context providing access to Katana client

    Returns:
        Dictionary containing inventory items data with summary and items list
    """
    response = await _get_inventory_items_impl(context)
    return response.model_dump()


# ============================================================================
# Resource 2: katana://inventory/stock-movements
# ============================================================================


class StockMovementsSummary(BaseModel):
    """Summary statistics for stock movements."""

    total_movements: int = Field(..., description="Total number of movements")
    movements_in_response: int = Field(
        ..., description="Number of movements in this response"
    )
    movement_types: dict[str, int] = Field(
        ..., description="Count of movements by type (transfer, adjustment)"
    )


class StockMovementsResource(BaseModel):
    """Response structure for stock movements resource."""

    generated_at: str = Field(
        ..., description="ISO timestamp when resource was generated"
    )
    summary: StockMovementsSummary = Field(..., description="Summary statistics")
    movements: list[dict] = Field(
        ..., description="List of recent stock movements (transfers and adjustments)"
    )
    next_actions: list[str] = Field(
        default_factory=list, description="Suggested next actions"
    )


async def _get_stock_movements_impl(context: Context) -> StockMovementsResource:
    """Implementation of stock movements resource.

    Fetches recent stock transfers and adjustments from Katana and aggregates
    them into a unified view of inventory movements.

    Args:
        context: FastMCP context for accessing the Katana client

    Returns:
        Structured stock movements data with summary and movements list

    Raises:
        Exception: If API calls fail
    """
    logger.info("stock_movements_resource_started")
    start_time = time.monotonic()

    try:
        services = get_services(context)

        # Import the generated API functions
        from katana_public_api_client.api.stock_adjustment import (
            get_all_stock_adjustments,
        )
        from katana_public_api_client.api.stock_transfer import (
            get_all_stock_transfers,
        )

        # Fetch recent stock transfers and adjustments
        # TODO: Consider parallelizing with asyncio.gather() for better performance
        transfers_response = await get_all_stock_transfers.asyncio_detailed(
            client=services.client, limit=50
        )
        adjustments_response = await get_all_stock_adjustments.asyncio_detailed(
            client=services.client, limit=50
        )

        # Parse responses - extract data from Response objects
        transfers = transfers_response.parsed if transfers_response.parsed else []
        adjustments = adjustments_response.parsed if adjustments_response.parsed else []

        # Aggregate into unified movements list
        movements = []

        # Add transfers
        for transfer in transfers:
            movements.append(
                {
                    "id": transfer.id if hasattr(transfer, "id") else None,
                    "timestamp": (
                        transfer.transfer_date.isoformat()
                        if hasattr(transfer, "transfer_date") and transfer.transfer_date
                        else (
                            transfer.updated_at.isoformat()
                            if hasattr(transfer, "updated_at") and transfer.updated_at
                            else None
                        )
                    ),
                    "type": "transfer",
                    "number": (
                        transfer.stock_transfer_number
                        if hasattr(transfer, "stock_transfer_number")
                        else None
                    ),
                    "source_location_id": (
                        transfer.source_location_id
                        if hasattr(transfer, "source_location_id")
                        else None
                    ),
                    "target_location_id": (
                        transfer.target_location_id
                        if hasattr(transfer, "target_location_id")
                        else None
                    ),
                    "status": (
                        transfer.status.value
                        if hasattr(transfer, "status") and transfer.status
                        else None
                    ),
                    "notes": (
                        transfer.additional_info
                        if hasattr(transfer, "additional_info")
                        else None
                    ),
                }
            )

        # Add adjustments
        for adjustment in adjustments:
            movements.append(
                {
                    "id": adjustment.id if hasattr(adjustment, "id") else None,
                    "timestamp": (
                        adjustment.adjustment_date.isoformat()
                        if hasattr(adjustment, "adjustment_date")
                        and adjustment.adjustment_date
                        else (
                            adjustment.updated_at.isoformat()
                            if hasattr(adjustment, "updated_at")
                            and adjustment.updated_at
                            else None
                        )
                    ),
                    "type": "adjustment",
                    "number": (
                        adjustment.stock_adjustment_number
                        if hasattr(adjustment, "stock_adjustment_number")
                        else None
                    ),
                    "location_id": (
                        adjustment.location_id
                        if hasattr(adjustment, "location_id")
                        else None
                    ),
                    "reference_no": (
                        adjustment.reference_no
                        if hasattr(adjustment, "reference_no")
                        else None
                    ),
                    "status": (
                        adjustment.status.value
                        if hasattr(adjustment, "status") and adjustment.status
                        else None
                    ),
                    "notes": (
                        adjustment.additional_info
                        if hasattr(adjustment, "additional_info")
                        else None
                    ),
                }
            )

        # Sort by timestamp (most recent first)
        movements.sort(key=lambda m: m.get("timestamp") or "", reverse=True)

        # Count movement types
        movement_types = {"transfer": len(transfers), "adjustment": len(adjustments)}

        # Build summary
        summary = StockMovementsSummary(
            total_movements=len(transfers) + len(adjustments),
            movements_in_response=len(movements),
            movement_types=movement_types,
        )

        duration_ms = round((time.monotonic() - start_time) * 1000, 2)
        logger.info(
            "stock_movements_resource_completed",
            total_movements=summary.total_movements,
            duration_ms=duration_ms,
        )

        return StockMovementsResource(
            generated_at=datetime.now(UTC).isoformat(),
            summary=summary,
            movements=movements,
            next_actions=[
                "Review recent adjustments for accuracy",
                "Check transfer statuses for pending movements",
                "Audit patterns in stock movements",
            ],
        )

    except Exception as e:
        duration_ms = round((time.monotonic() - start_time) * 1000, 2)
        logger.error(
            "stock_movements_resource_failed",
            error=str(e),
            error_type=type(e).__name__,
            duration_ms=duration_ms,
            exc_info=True,
        )
        raise


async def get_stock_movements(context: Context) -> dict:
    """Get stock movements resource.

    Provides unified view of recent inventory movements including stock transfers
    between locations and manual stock adjustments.

    **Resource URI:** `katana://inventory/stock-movements`

    **Purpose:** Track inventory changes and audit trail

    **Refresh Rate:** On-demand (no caching in v0.1.0)

    **Data Includes:**
    - Recent stock transfers between locations
    - Manual stock adjustments
    - Movement timestamps and statuses
    - Location information
    - Reference numbers and notes

    **Use Cases:**
    - Monitor recent inventory activity
    - Audit stock changes
    - Track transfer status
    - Investigate discrepancies

    **Related Tools:**
    - `check_inventory` - Get current stock levels
    - `create_purchase_order` - Order more stock

    Args:
        context: FastMCP context providing access to Katana client

    Returns:
        Dictionary containing stock movements data with summary and movements list
    """
    response = await _get_stock_movements_impl(context)
    return response.model_dump()


def register_resources(mcp: FastMCP) -> None:
    """Register all inventory resources with the FastMCP instance.

    Args:
        mcp: FastMCP server instance to register resources with
    """
    # Register katana://inventory/items resource
    mcp.resource(
        uri="katana://inventory/items",
        name="Inventory Items",
        description="Complete catalog of all products, materials, and services",
        mime_type="application/json",
    )(get_inventory_items)

    # Register katana://inventory/stock-movements resource
    mcp.resource(
        uri="katana://inventory/stock-movements",
        name="Stock Movements",
        description="Recent inventory movements (transfers and adjustments)",
        mime_type="application/json",
    )(get_stock_movements)


__all__ = ["register_resources"]
