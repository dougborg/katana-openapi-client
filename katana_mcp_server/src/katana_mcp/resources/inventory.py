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


__all__ = ["register_resources"]
