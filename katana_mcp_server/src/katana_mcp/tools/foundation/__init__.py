"""Foundation tools for Katana MCP Server.

Foundation tools are low-level operations that map closely to API endpoints.
They provide granular control and are the building blocks for workflow tools.

Organization:
- items.py: Search and manage items (variants, products, materials, services)
- inventory.py: Stock checking, low stock alerts, inventory operations
- purchase_orders.py: Create, receive, and verify purchase orders
- catalog.py: Create products and materials (dedicated catalog management)
- manufacturing_orders.py: Create manufacturing orders
- orders.py: Fulfill manufacturing orders and sales orders
"""

from fastmcp import FastMCP

from .catalog import register_tools as register_catalog_tools
from .inventory import register_tools as register_inventory_tools
from .items import register_tools as register_items_tools
from .manufacturing_orders import register_tools as register_manufacturing_order_tools
from .orders import register_tools as register_order_tools
from .purchase_orders import register_tools as register_purchase_order_tools


def register_all_foundation_tools(mcp: FastMCP) -> None:
    """Register all foundation tools from all modules.

    Args:
        mcp: FastMCP server instance to register tools with
    """
    register_items_tools(mcp)
    register_inventory_tools(mcp)
    register_purchase_order_tools(mcp)
    register_catalog_tools(mcp)
    register_manufacturing_order_tools(mcp)
    register_order_tools(mcp)


__all__ = [
    "register_all_foundation_tools",
]
