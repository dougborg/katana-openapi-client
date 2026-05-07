"""MCP Resources for Katana Manufacturing ERP.

Resources provide read-only views of stable reference data that the AI reads
to understand system state. They are backed by the SQLite cache for fast access.

Available Resources:
- katana://inventory/items - Complete catalog (products, materials, services)
- katana://help - Main help index (progressive discovery)
- katana://help/workflows - Detailed workflow guides
- katana://help/tools - Tool reference documentation
- katana://help/resources - Resource descriptions

Note: Transactional data (sales orders, purchase orders, manufacturing orders,
stock movements) is NOT exposed as resources — use the corresponding tools
instead (e.g., get_manufacturing_order, get_inventory_movements).

Reference data (suppliers, locations, tax rates, operators, additional costs)
is also tools-only — see ``tools/foundation/reference.py``. Bulk-list
resources for those entities used to dump every row as a single-line JSON
blob, which floods agent context. Parameterized tools (with FTS-backed
``query`` and bounded ``limit``) replaced them.
"""

from __future__ import annotations

from fastmcp import FastMCP


def register_all_resources(mcp: FastMCP) -> None:
    """Register all resources with the FastMCP server instance."""
    from .inventory import register_resources as register_inventory_resources

    register_inventory_resources(mcp)

    from .help import register_resources as register_help_resources

    register_help_resources(mcp)


__all__ = ["register_all_resources"]
