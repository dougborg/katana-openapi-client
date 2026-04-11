"""Inventory resources for Katana MCP Server.

Provides cache-backed read-only access to the item catalog (products,
materials, services). Stock movements are exposed via the `get_inventory_movements`
tool, not as a resource.
"""

# NOTE: Do not use 'from __future__ import annotations' in this module
# FastMCP requires Context to be the actual class, not a string annotation

import json
import time
from datetime import UTC, datetime
from typing import Any

from fastmcp import Context, FastMCP

from katana_mcp.cache import EntityType
from katana_mcp.cache_sync import (
    ensure_materials_synced,
    ensure_products_synced,
    ensure_services_synced,
)
from katana_mcp.logging import get_logger
from katana_mcp.services import get_services

logger = get_logger(__name__)


def _filter_deleted(entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Filter out entities marked as deleted."""
    return [e for e in entities if not e.get("deleted_at")]


async def get_inventory_items(context: Context) -> str:
    """Complete catalog view for browsing products, materials, and services.

    **Resource URI:** `katana://inventory/items`

    **Purpose:** Browse the complete item catalog. Reads from the SQLite cache
    for fast access — cache is synced from the Katana API on-demand.

    **Contains:**
    - All products, materials, and services with id, name, type
    - Item capabilities (is_sellable, is_producible, is_purchasable)
    - Summary counts by type

    **Related Tools:**
    - `search_items` - Find specific items by name or SKU (FTS5 search)
    - `get_variant_details` - Get pricing and supplier codes by SKU
    - `check_inventory` - Get current stock levels for a SKU
    """
    start = time.monotonic()
    services = get_services(context)

    # Ensure cache is fresh for all three item types
    await ensure_products_synced(services)
    await ensure_materials_synced(services)
    await ensure_services_synced(services)

    # Read from cache
    products_raw = await services.cache.get_all(EntityType.PRODUCT)
    materials_raw = await services.cache.get_all(EntityType.MATERIAL)
    services_raw = await services.cache.get_all(EntityType.SERVICE)

    products = _filter_deleted(products_raw)
    materials = _filter_deleted(materials_raw)
    service_items = _filter_deleted(services_raw)

    items: list[dict[str, Any]] = []

    for p in products:
        items.append(
            {
                "id": p.get("id"),
                "name": p.get("name"),
                "type": "product",
                # Default None to False for products (conservative: unset means not flagged)
                "is_sellable": p.get("is_sellable") is True,
                "is_producible": p.get("is_producible") is True,
                "is_purchasable": p.get("is_purchasable") is True,
            }
        )

    for m in materials:
        items.append(
            {
                "id": m.get("id"),
                "name": m.get("name"),
                "type": "material",
                "is_sellable": False,
                "is_producible": False,
                "is_purchasable": True,
            }
        )

    for s in service_items:
        items.append(
            {
                "id": s.get("id"),
                "name": s.get("name"),
                "type": "service",
                # Services default to sellable when field is missing/None
                "is_sellable": s.get("is_sellable") is not False,
                "is_producible": False,
                "is_purchasable": False,
            }
        )

    duration_ms = round((time.monotonic() - start) * 1000, 2)
    logger.info(
        "inventory_items_resource",
        total=len(items),
        duration_ms=duration_ms,
    )

    return json.dumps(
        {
            "generated_at": datetime.now(UTC).isoformat(),
            "summary": {
                "total_items": len(items),
                "products": len(products),
                "materials": len(materials),
                "services": len(service_items),
            },
            "items": items,
            "next_actions": [
                "Use search_items tool to find specific items by name or SKU",
                "Use check_inventory tool to get detailed stock levels for a SKU",
                "Use list_low_stock_items tool to identify items needing reorder",
            ],
        }
    )


def register_resources(mcp: FastMCP) -> None:
    """Register inventory resources with the FastMCP instance."""
    mcp.resource(
        uri="katana://inventory/items",
        name="Inventory Items",
        description="Complete catalog of all products, materials, and services",
        mime_type="application/json",
    )(get_inventory_items)


__all__ = ["register_resources"]
