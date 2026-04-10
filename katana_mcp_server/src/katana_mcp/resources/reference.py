"""Reference data resources for Katana MCP Server.

Provides cache-backed read-only access to stable reference data: suppliers,
locations, tax rates, and operators. These are small, stable datasets that
the AI needs as context for creating orders and manufacturing assignments.

All resources read from the SQLite cache (with on-demand sync) rather than
calling the API directly — making them fast and suitable for frequent access.
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
    ensure_locations_synced,
    ensure_operators_synced,
    ensure_suppliers_synced,
    ensure_tax_rates_synced,
)
from katana_mcp.logging import get_logger
from katana_mcp.services import get_services

logger = get_logger(__name__)


def _filter_deleted(entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Filter out entities marked as deleted."""
    return [e for e in entities if not e.get("deleted_at")]


# ============================================================================
# Resource: katana://suppliers
# ============================================================================


async def get_suppliers(context: Context) -> str:
    """Browse all suppliers for creating purchase orders.

    **Resource URI:** `katana://suppliers`

    **Purpose:** Reference data for supplier lookup — use to find supplier_id
    when creating purchase orders.
    """
    start = time.monotonic()
    services = get_services(context)
    await ensure_suppliers_synced(services)
    raw = await services.cache.get_all(EntityType.SUPPLIER)
    suppliers = _filter_deleted(raw)

    items = [
        {
            "id": s.get("id"),
            "name": s.get("name"),
            "email": s.get("email"),
            "phone": s.get("phone"),
            "currency": s.get("currency"),
            "comment": s.get("comment"),
        }
        for s in suppliers
    ]

    duration_ms = round((time.monotonic() - start) * 1000, 2)
    logger.info("suppliers_resource", count=len(items), duration_ms=duration_ms)

    return json.dumps(
        {
            "generated_at": datetime.now(UTC).isoformat(),
            "summary": {"total_suppliers": len(items)},
            "suppliers": items,
            "next_actions": [
                "Use create_purchase_order with supplier_id to order materials",
            ],
        }
    )


# ============================================================================
# Resource: katana://locations
# ============================================================================


async def get_locations(context: Context) -> str:
    """Browse all warehouses and facilities (locations).

    **Resource URI:** `katana://locations`

    **Purpose:** Reference data for location lookup — use to find location_id
    when creating orders or checking inventory.
    """
    start = time.monotonic()
    services = get_services(context)
    await ensure_locations_synced(services)
    raw = await services.cache.get_all(EntityType.LOCATION)
    locations = _filter_deleted(raw)

    items = [
        {
            "id": loc.get("id"),
            "name": loc.get("name"),
            "address": loc.get("address"),
            "city": loc.get("city"),
            "country": loc.get("country"),
            "is_primary": loc.get("is_primary"),
        }
        for loc in locations
    ]

    duration_ms = round((time.monotonic() - start) * 1000, 2)
    logger.info("locations_resource", count=len(items), duration_ms=duration_ms)

    return json.dumps(
        {
            "generated_at": datetime.now(UTC).isoformat(),
            "summary": {"total_locations": len(items)},
            "locations": items,
            "next_actions": [
                "Use location_id when creating orders or checking inventory",
            ],
        }
    )


# ============================================================================
# Resource: katana://tax-rates
# ============================================================================


async def get_tax_rates(context: Context) -> str:
    """Browse all configured tax rates.

    **Resource URI:** `katana://tax-rates`

    **Purpose:** Reference data for tax rate lookup — use to find tax_rate_id
    when creating sales orders with tax calculations.
    """
    start = time.monotonic()
    services = get_services(context)
    await ensure_tax_rates_synced(services)
    raw = await services.cache.get_all(EntityType.TAX_RATE)
    tax_rates = _filter_deleted(raw)

    items = [
        {
            "id": tr.get("id"),
            "name": tr.get("name"),
            "rate": tr.get("rate"),
            "display_name": tr.get("display_name"),
            "is_default_sales": tr.get("is_default_sales"),
            "is_default_purchases": tr.get("is_default_purchases"),
        }
        for tr in tax_rates
    ]

    duration_ms = round((time.monotonic() - start) * 1000, 2)
    logger.info("tax_rates_resource", count=len(items), duration_ms=duration_ms)

    return json.dumps(
        {
            "generated_at": datetime.now(UTC).isoformat(),
            "summary": {"total_tax_rates": len(items)},
            "tax_rates": items,
            "next_actions": [
                "Reference tax_rate_id when creating sales orders",
            ],
        }
    )


# ============================================================================
# Resource: katana://operators
# ============================================================================


async def get_operators(context: Context) -> str:
    """Browse all manufacturing operators.

    **Resource URI:** `katana://operators`

    **Purpose:** Reference data for operator lookup — use to assign operators
    to manufacturing order operation rows.
    """
    start = time.monotonic()
    services = get_services(context)
    await ensure_operators_synced(services)
    raw = await services.cache.get_all(EntityType.OPERATOR)
    operators = _filter_deleted(raw)

    items = [
        {
            "id": op.get("id"),
            "name": op.get("name"),
        }
        for op in operators
    ]

    duration_ms = round((time.monotonic() - start) * 1000, 2)
    logger.info("operators_resource", count=len(items), duration_ms=duration_ms)

    return json.dumps(
        {
            "generated_at": datetime.now(UTC).isoformat(),
            "summary": {"total_operators": len(items)},
            "operators": items,
            "next_actions": [
                "Reference operator_id when assigning manufacturing operations",
            ],
        }
    )


# ============================================================================
# Registration
# ============================================================================


def register_resources(mcp: FastMCP) -> None:
    """Register all reference data resources with the FastMCP instance."""
    mcp.resource(
        uri="katana://suppliers",
        name="Suppliers",
        description="All suppliers with contact info — for creating purchase orders",
        mime_type="application/json",
    )(get_suppliers)

    mcp.resource(
        uri="katana://locations",
        name="Locations",
        description="All warehouses and facilities — for order and inventory lookups",
        mime_type="application/json",
    )(get_locations)

    mcp.resource(
        uri="katana://tax-rates",
        name="Tax Rates",
        description="Configured tax rates — for sales order tax calculations",
        mime_type="application/json",
    )(get_tax_rates)

    mcp.resource(
        uri="katana://operators",
        name="Operators",
        description="Manufacturing operators — for operation assignments",
        mime_type="application/json",
    )(get_operators)


__all__ = ["register_resources"]
