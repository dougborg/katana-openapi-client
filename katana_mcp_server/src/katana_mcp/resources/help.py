"""Help resources for Katana MCP Server.

Provides on-demand detailed guidance for AI agents, implementing a progressive
discovery pattern to minimize initial token usage while keeping comprehensive
documentation available when needed.

Resources:
- katana://help - Main help index with brief descriptions
- katana://help/workflows - Detailed workflow examples with tool sequences
- katana://help/tools - Tool usage guide with examples
- katana://help/resources - Resource descriptions and usage
"""

from fastmcp import FastMCP

from katana_mcp.logging import get_logger

logger = get_logger(__name__)


# ============================================================================
# Help Content
# ============================================================================

HELP_INDEX = """
# Katana MCP Server Help

Manufacturing ERP tools for inventory, orders, and production management.

## Quick Navigation

| Resource | Description |
|----------|-------------|
| `katana://help/workflows` | Step-by-step workflow guides |
| `katana://help/tools` | Tool reference with examples |
| `katana://help/resources` | Available data resources |

## Core Capabilities

### Inventory & Catalog
- **search_items** - Find products, materials, services by name/SKU
- **get_variant_details** - Get full details for a specific item
- **check_inventory** - Check stock levels for a SKU
- **list_low_stock_items** - Find items needing reorder

### Purchase Orders
- **create_purchase_order** - Create PO with preview/confirm pattern
- **receive_purchase_order** - Receive items and update inventory
- **verify_order_document** - Verify supplier documents against POs

### Manufacturing & Sales
- **create_manufacturing_order** - Create production work orders
- **fulfill_order** - Complete manufacturing or sales orders
- **create_sales_order** - Create sales orders with preview/confirm

## Safety Pattern

All create/modify operations use a **two-step confirmation**:
1. Call with `confirm=false` to preview (no changes made)
2. Call with `confirm=true` to execute (prompts for confirmation)

## Common Workflows

1. **Reorder low stock**: check_inventory → create_purchase_order
2. **Receive delivery**: verify_order_document → receive_purchase_order
3. **Fulfill sales**: search_items → fulfill_order
4. **Create production**: search_items → create_manufacturing_order

Use `katana://help/workflows` for detailed step-by-step guides.
"""

HELP_WORKFLOWS = """
# Katana Workflow Guide

Detailed step-by-step guides for common manufacturing ERP workflows.

---

## Workflow 1: Check Stock and Reorder

**Goal:** Identify low stock items and create purchase orders to replenish.

### Steps

1. **Check current stock levels**
   ```json
   Tool: list_low_stock_items
   Request: {}
   ```
   Returns items below reorder threshold.

2. **Get supplier info for item**
   ```json
   Tool: get_variant_details
   Request: {"sku": "BOLT-M8"}
   ```
   Returns supplier_id and pricing info.

3. **Preview purchase order**
   ```json
   Tool: create_purchase_order
   Request: {
     "supplier_id": 4001,
     "location_id": 1,
     "order_number": "PO-2025-001",
     "items": [{"variant_id": 501, "quantity": 100, "price_per_unit": 0.15}],
     "confirm": false
   }
   ```
   Returns preview with total cost - no order created yet.

4. **Confirm and create order**
   ```json
   Tool: create_purchase_order
   Request: {...same as above..., "confirm": true}
   ```
   Creates actual PO after user confirmation.

---

## Workflow 2: Receive Purchase Order

**Goal:** Receive delivered items and update inventory.

### Steps

1. **Verify the delivery document**
   ```json
   Tool: verify_order_document
   Request: {
     "order_id": 1234,
     "document_items": [
       {"sku": "BOLT-M8", "quantity": 100, "unit_price": 0.15}
     ]
   }
   ```
   Returns match status and any discrepancies.

2. **Preview receipt**
   ```json
   Tool: receive_purchase_order
   Request: {
     "order_id": 1234,
     "items": [{"purchase_order_row_id": 501, "quantity": 100}],
     "confirm": false
   }
   ```
   Shows what will be received.

3. **Confirm receipt**
   ```json
   Tool: receive_purchase_order
   Request: {...same as above..., "confirm": true}
   ```
   Updates inventory after user confirmation.

---

## Workflow 3: Manufacturing Order Fulfillment

**Goal:** Complete a manufacturing order and add finished goods to inventory.

### Steps

1. **Check manufacturing order status**
   Access `katana://manufacturing-orders` resource to see active orders.

2. **Verify materials available**
   ```json
   Tool: check_inventory
   Request: {"sku": "WIDGET-001"}
   ```

3. **Complete the order**
   ```json
   Tool: fulfill_order
   Request: {
     "order_id": 345,
     "order_type": "manufacturing",
     "confirm": true
   }
   ```
   Marks order complete and updates finished goods inventory.

---

## Workflow 4: Sales Order Fulfillment

**Goal:** Fulfill a sales order and ship to customer.

### Steps

1. **Check order details**
   Access `katana://sales-orders` resource.

2. **Verify stock available**
   ```json
   Tool: check_inventory
   Request: {"sku": "WIDGET-001"}
   ```

3. **Fulfill the order**
   ```json
   Tool: fulfill_order
   Request: {
     "order_id": 789,
     "order_type": "sales",
     "confirm": true
   }
   ```
   Updates inventory and marks order as shipped.

---

## Workflow 5: Product Catalog Search

**Goal:** Find and inspect items in the catalog.

### Steps

1. **Search for items**
   ```json
   Tool: search_items
   Request: {"query": "widget", "limit": 10}
   ```
   Returns matching products, materials, services.

2. **Get full details**
   ```json
   Tool: get_variant_details
   Request: {"sku": "WIDGET-001"}
   ```
   Returns complete item info including BOM, suppliers, pricing.

3. **Check stock**
   ```json
   Tool: check_inventory
   Request: {"sku": "WIDGET-001"}
   ```
   Returns current stock levels and availability.
"""

HELP_TOOLS = """
# Katana Tool Reference

Detailed guide for all available MCP tools.

---

## Inventory & Catalog Tools

### search_items
Find products, materials, and services by name or SKU.

**Parameters:**
- `query` (required): Search term to match against name, SKU, or description
- `limit` (optional): Maximum results (default: 20, max: 100)
- `item_type` (optional): Filter by type - "product", "material", "service", or "all"

**Example:**
```json
{"query": "bolt", "limit": 10, "item_type": "material"}
```

**Returns:** List of matching items with ID, SKU, name, type, and basic info.

---

### get_variant_details
Get complete details for a specific item variant.

**Parameters:**
- `sku` (required): The SKU of the item to look up

**Example:**
```json
{"sku": "BOLT-M8"}
```

**Returns:** Full item details including inventory, BOM, suppliers, pricing.

---

### check_inventory
Check current stock levels for an item.

**Parameters:**
- `sku` (required): The SKU to check

**Example:**
```json
{"sku": "WIDGET-001"}
```

**Returns:** Stock levels (in_stock, available, allocated, on_order).

---

### list_low_stock_items
Find items that are below their reorder threshold.

**Parameters:** None required.

**Returns:** List of items needing reorder with current stock vs threshold.

---

## Purchase Order Tools

### create_purchase_order
Create a purchase order with preview/confirm pattern.

**Parameters:**
- `supplier_id` (required): Supplier ID
- `location_id` (required): Warehouse location for receipt
- `order_number` (required): PO number (e.g., "PO-2025-001")
- `items` (required): Array of line items with variant_id, quantity, price_per_unit
- `confirm` (required): false=preview, true=create

**Safety:** When confirm=true, prompts user for confirmation before creating.

---

### receive_purchase_order
Receive items from a purchase order.

**Parameters:**
- `order_id` (required): Purchase order ID
- `items` (required): Array of items with purchase_order_row_id and quantity
- `confirm` (required): false=preview, true=receive

**Safety:** When confirm=true, prompts user for confirmation.

---

### verify_order_document
Verify a supplier document (invoice, packing slip) against a PO.

**Parameters:**
- `order_id` (required): Purchase order ID to verify against
- `document_items` (required): Array of items from document with sku, quantity, unit_price

**Returns:** Match status, discrepancies, and suggested actions.

---

## Manufacturing & Sales Tools

### create_manufacturing_order
Create a manufacturing work order.

**Parameters:**
- `product_sku` (required): SKU of product to manufacture
- `quantity` (required): Quantity to produce
- `confirm` (required): false=preview, true=create

---

### create_sales_order
Create a sales order.

**Parameters:**
- `customer_id` (required): Customer ID
- `items` (required): Array of items with variant_id and quantity
- `confirm` (required): false=preview, true=create

---

### fulfill_order
Complete a manufacturing or sales order.

**Parameters:**
- `order_id` (required): Order ID to fulfill
- `order_type` (required): "manufacturing" or "sales"
- `confirm` (required): false=preview, true=fulfill
"""

HELP_RESOURCES = """
# Katana Resources Reference

Available data resources for browsing system state.

---

## Inventory Resources

### katana://inventory/items
Complete catalog with stock levels.

**Contains:**
- All products, materials, services
- Item type and capabilities
- Summary statistics
- Total counts

**Use when:** Browsing catalog, checking item types, getting overview.

---

### katana://inventory/stock-movements
Recent inventory movements (transfers, adjustments).

**Contains:**
- Stock transfers between locations
- Manual stock adjustments
- Movement timestamps and users
- Source/destination locations

**Use when:** Auditing inventory changes, tracking movements.

---

### katana://inventory/stock-adjustments
Manual stock adjustments (corrections, damage, shrinkage).

**Contains:**
- Adjustment reasons and values
- Financial impact
- Before/after quantities
- User who made adjustment

**Use when:** Investigating discrepancies, audit trail.

---

## Order Resources

### katana://sales-orders
Open/pending sales orders.

**Contains:**
- Customer and order info
- Due dates and status
- Item counts and totals
- Fulfillment status

**Use when:** Checking orders to fulfill, customer status.

---

### katana://purchase-orders
Open/pending purchase orders.

**Contains:**
- Supplier and order info
- Expected delivery dates
- Receipt status
- Item totals

**Use when:** Checking expected deliveries, receiving status.

---

### katana://manufacturing-orders
Active manufacturing work orders.

**Contains:**
- Product and quantity info
- Completion percentage
- Material availability
- Blocking status

**Use when:** Checking production status, material needs.

---

## Help Resources

### katana://help
This help index (you are here).

### katana://help/workflows
Step-by-step workflow guides.

### katana://help/tools
Complete tool reference.

### katana://help/resources
Resource descriptions (this page).
"""


# ============================================================================
# Resource Functions
# ============================================================================


async def get_help_index() -> str:
    """Get main help index.

    **Resource URI:** `katana://help`

    Provides navigation to detailed help sections and overview of capabilities.
    Use this as a starting point to understand what the Katana MCP server can do.

    Returns:
        Markdown help content with navigation and capability overview.
    """
    logger.info("help_index_accessed")
    return HELP_INDEX


async def get_help_workflows() -> str:
    """Get detailed workflow guides.

    **Resource URI:** `katana://help/workflows`

    Step-by-step guides for common manufacturing ERP workflows including:
    - Check stock and reorder
    - Receive purchase orders
    - Manufacturing order fulfillment
    - Sales order fulfillment
    - Product catalog search

    Returns:
        Markdown content with detailed workflow examples.
    """
    logger.info("help_workflows_accessed")
    return HELP_WORKFLOWS


async def get_help_tools() -> str:
    """Get tool reference documentation.

    **Resource URI:** `katana://help/tools`

    Complete reference for all MCP tools including parameters,
    examples, and expected return values.

    Returns:
        Markdown content with tool documentation.
    """
    logger.info("help_tools_accessed")
    return HELP_TOOLS


async def get_help_resources() -> str:
    """Get resources documentation.

    **Resource URI:** `katana://help/resources`

    Descriptions of all available data resources and when to use them.

    Returns:
        Markdown content with resource documentation.
    """
    logger.info("help_resources_accessed")
    return HELP_RESOURCES


# ============================================================================
# Registration
# ============================================================================


def register_resources(mcp: FastMCP) -> None:
    """Register all help resources with the FastMCP instance.

    Args:
        mcp: FastMCP server instance to register resources with
    """
    # Register katana://help resource
    mcp.resource(
        uri="katana://help",
        name="Help Index",
        description="Main help index with navigation and capability overview",
    )(get_help_index)

    # Register katana://help/workflows resource
    mcp.resource(
        uri="katana://help/workflows",
        name="Workflow Guide",
        description="Step-by-step workflow guides for common tasks",
    )(get_help_workflows)

    # Register katana://help/tools resource
    mcp.resource(
        uri="katana://help/tools",
        name="Tool Reference",
        description="Complete tool documentation with examples",
    )(get_help_tools)

    # Register katana://help/resources resource
    mcp.resource(
        uri="katana://help/resources",
        name="Resources Guide",
        description="Available data resources and usage",
    )(get_help_resources)

    logger.info(
        "help_resources_registered",
        resources=[
            "katana://help",
            "katana://help/workflows",
            "katana://help/tools",
            "katana://help/resources",
        ],
    )
