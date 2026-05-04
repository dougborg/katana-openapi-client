"""Workflow prompt templates for Katana MCP Server.

These prompts guide LLMs through multi-step manufacturing ERP workflows
by providing the correct tool sequence and decision points.
"""

from fastmcp import FastMCP


async def reorder_low_stock(threshold: int = 10) -> str:
    """Identify low-stock items and create purchase orders to replenish inventory.

    Guides you through checking stock levels, finding supplier information,
    and creating purchase orders for items that need restocking.
    """
    return f"""\
Check inventory for items below {threshold} units and create purchase orders to restock:

1. Call **list_low_stock_items** with threshold={threshold} to find items needing reorder
2. For each low-stock item, call **get_variant_details** with the SKU to find:
   - The variant_id (needed for purchase order line items)
   - Supplier item codes and pricing info
3. Group items by supplier
4. For each supplier group, call **create_purchase_order** with preview=true (default) to preview:
   - Set supplier_id, location_id, order_number
   - Include line items with variant_id, quantity, price_per_unit
5. Review the preview totals with the user
6. Call **create_purchase_order** with preview=false to create each order
"""


async def receive_delivery(order_id: int) -> str:
    """Verify a supplier delivery against a purchase order and receive the items.

    Guides you through validating a delivery document, checking for discrepancies,
    and receiving items into inventory.
    """
    return f"""\
Verify and receive delivery for purchase order {order_id}:

1. Call **verify_order_document** with order_id={order_id} and the document_items
   (SKU, quantity, unit_price from the supplier's packing slip or invoice)
2. Review the verification results:
   - If "match": all items verified, safe to receive
   - If "partial_match": review discrepancies with user before proceeding
   - If "no_match": investigate before receiving
3. Call **receive_purchase_order** with preview=true (default) to preview the receipt
4. Review the preview with the user
5. Call **receive_purchase_order** with preview=false to receive items and update inventory
"""


async def fulfill_sales_order(order_id: int) -> str:
    """Check stock availability and fulfill a sales order.

    Guides you through verifying inventory levels and creating a
    fulfillment to ship items to the customer.
    """
    return f"""\
Fulfill sales order {order_id}:

1. Call **fulfill_order** with order_id={order_id}, order_type="sales", preview=true
   (default) to preview the fulfillment and check current order status
2. If the order has items that need stock verification, call **check_inventory**
   for each SKU to confirm availability
3. Review the fulfillment preview and stock levels with the user
4. Call **fulfill_order** with order_id={order_id}, order_type="sales", preview=false
   to create the fulfillment, reduce inventory, and mark items as shipped
"""


def register_prompts(mcp: FastMCP) -> None:
    """Register all workflow prompts with the FastMCP instance.

    Args:
        mcp: FastMCP server instance to register prompts with
    """
    mcp.prompt()(reorder_low_stock)
    mcp.prompt()(receive_delivery)
    mcp.prompt()(fulfill_sales_order)
