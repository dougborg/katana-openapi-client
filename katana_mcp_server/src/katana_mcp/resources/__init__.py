"""MCP Resources for Katana Manufacturing ERP.

Resources provide read-only views of stable reference data that the AI reads
to understand system state. They are backed by the SQLite cache for fast access.

Available Resources:
- katana://inventory/items - Complete catalog (products, materials, services)
- katana://suppliers - Suppliers with contact info
- katana://locations - Warehouses and facilities
- katana://tax-rates - Tax rate configurations
- katana://operators - Manufacturing operators
- katana://help - Main help index (progressive discovery)
- katana://help/workflows - Detailed workflow guides
- katana://help/tools - Tool reference documentation
- katana://help/resources - Resource descriptions

Note: Transactional data (sales orders, purchase orders, manufacturing orders,
stock movements) is NOT exposed as resources — use the corresponding tools
instead (e.g., get_manufacturing_order, get_inventory_movements).
"""

from __future__ import annotations

from fastmcp import FastMCP


def register_all_resources(mcp: FastMCP) -> None:
    """Register all resources with the FastMCP server instance."""
    from .inventory import register_resources as register_inventory_resources

    register_inventory_resources(mcp)

    from .reference import register_resources as register_reference_resources

    register_reference_resources(mcp)

    from .help import register_resources as register_help_resources

    register_help_resources(mcp)


__all__ = ["register_all_resources"]
