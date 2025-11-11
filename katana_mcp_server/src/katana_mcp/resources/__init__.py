"""MCP Resources for Katana Manufacturing ERP.

Resources provide read-only views of Katana data that refresh on-demand.
Resources are organized by domain (inventory, orders) and provide structured
data with summaries, statistics, and actionable next steps.

Available Resources:
- katana://inventory/items - Complete catalog with stock levels
- katana://inventory/stock-movements - Recent inventory movements
- katana://inventory/stock-adjustments - Manual stock adjustments
- katana://sales-orders - Open/pending sales orders
- katana://purchase-orders - Open/pending purchase orders
- katana://manufacturing-orders - Active manufacturing orders
"""

from __future__ import annotations

from fastmcp import FastMCP


def register_all_resources(mcp: FastMCP) -> None:
    """Register all resources with the FastMCP server instance.

    This function is called during server initialization to register all
    resource handlers with the MCP server.

    Args:
        mcp: FastMCP server instance to register resources with
    """
    # Import and register inventory resources
    from .inventory import register_resources as register_inventory_resources

    register_inventory_resources(mcp)

    # Import and register order resources
    from .orders import register_resources as register_order_resources

    register_order_resources(mcp)


__all__ = ["register_all_resources"]
