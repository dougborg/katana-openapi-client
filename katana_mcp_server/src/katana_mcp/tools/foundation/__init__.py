"""Foundation tools for Katana MCP Server.

Foundation tools are low-level operations that map closely to API endpoints.
They provide granular control and are the building blocks for workflow tools.

Organization:
- items.py: Search and manage items (variants, products, materials, services)
- bom.py: Product-level BOM (Bill of Materials) read + modify on a
  producible product variant
- inventory.py: Stock checking, low stock alerts, inventory operations
- customers.py: Search and look up customers
- purchase_orders.py: Create, receive, and verify purchase orders
- sales_orders.py: Create sales orders
- catalog.py: Create products and materials (dedicated catalog management)
- manufacturing_orders.py: Create manufacturing orders
- orders.py: Fulfill manufacturing orders and sales orders
- reference.py: Thin tool wrappers for reference-data resources
  (locations, suppliers, tax rates, operators, additional costs)
- cache_admin.py: Cache administration (rebuild_cache for typed cache)

Reporting / forecasting tools (top_selling_variants, sales_summary,
inventory_velocity) were removed in favor of Katana's own forecasting
and replenishment work — those features are part of Katana's roadmap
and surfacing our derived approximations would drift from their
authoritative numbers.
"""

from fastmcp import FastMCP

from .bom import register_tools as register_bom_tools
from .cache_admin import register_tools as register_cache_admin_tools
from .catalog import register_tools as register_catalog_tools
from .corrections import register_tools as register_corrections_tools
from .customers import register_tools as register_customers_tools
from .inventory import register_tools as register_inventory_tools
from .items import register_tools as register_items_tools
from .manufacturing_orders import register_tools as register_manufacturing_order_tools
from .orders import register_tools as register_order_tools
from .purchase_orders import register_tools as register_purchase_order_tools
from .reference import register_tools as register_reference_tools
from .sales_orders import register_tools as register_sales_order_tools
from .serial_numbers import register_tools as register_serial_number_tools
from .stock_transfers import register_tools as register_stock_transfer_tools


def register_all_foundation_tools(mcp: FastMCP) -> None:
    """Register all foundation tools from all modules.

    Args:
        mcp: FastMCP server instance to register tools with
    """
    register_items_tools(mcp)
    register_inventory_tools(mcp)
    register_customers_tools(mcp)
    register_purchase_order_tools(mcp)
    register_sales_order_tools(mcp)
    register_catalog_tools(mcp)
    register_manufacturing_order_tools(mcp)
    register_order_tools(mcp)
    register_stock_transfer_tools(mcp)
    register_serial_number_tools(mcp)
    register_reference_tools(mcp)
    register_cache_admin_tools(mcp)
    register_corrections_tools(mcp)
    register_bom_tools(mcp)


__all__ = [
    "register_all_foundation_tools",
]
