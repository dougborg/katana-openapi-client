"""Foundation tools for Katana MCP Server.

Foundation tools are low-level operations that map closely to API endpoints.
They provide granular control and are the building blocks for workflow tools.

Organization:
- items.py: Search and manage items (variants, products, materials, services)
- inventory.py: Stock checking, low stock alerts, inventory operations
"""

from fastmcp import FastMCP

from .inventory import register_tools as register_inventory_tools
from .items import register_tools as register_items_tools


def register_all_foundation_tools(mcp: FastMCP) -> None:
    """Register all foundation tools from all modules.

    Args:
        mcp: FastMCP server instance to register tools with
    """
    register_items_tools(mcp)
    register_inventory_tools(mcp)


__all__ = [
    "register_all_foundation_tools",
]
