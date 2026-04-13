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
   Use `get_manufacturing_order` tool with the order_no or order_id.

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
   Use sales order tools to find order details.

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
- `query` (required): Search term to match against name or SKU
- `limit` (optional): Maximum results (default: 20)

**Example:**
```json
{"query": "bolt", "limit": 10}
```

**Returns:** List of matching items with ID, SKU, name, and sellable status.

---

### get_variant_details
Get complete details for a specific item variant.

**Parameters:**
- `sku` (required): The SKU of the item to look up

**Example:**
```json
{"sku": "BOLT-M8"}
```

**Returns:** Full variant details including pricing, barcodes, supplier codes,
configuration attributes, custom fields, and more.

---

### check_inventory
Check current stock levels for an item.

**Parameters:**
- `sku` (required): The SKU to check

**Example:**
```json
{"sku": "WIDGET-001"}
```

**Returns:** Stock levels (in_stock, available_stock, committed, expected).

---

### list_low_stock_items
Find items that are below their reorder threshold.

**Parameters:**
- `threshold` (optional): Stock threshold level (default: 10)
- `limit` (optional): Maximum items to return (default: 50)

**Returns:** List of items needing reorder with current stock vs threshold.

---

### get_inventory_movements
Get inventory movement history for a SKU — every stock change with dates and causes.

**Parameters:**
- `sku` (required): SKU to get movements for
- `limit` (optional): Maximum movements to return (default: 50)

**Returns:** Movement history with dates, quantity changes, balances, resource types, and order numbers.

---

### create_stock_adjustment
Create a stock adjustment to correct inventory levels.

**Parameters:**
- `location_id` (required): Location ID for the adjustment
- `rows` (required): List of `{sku, quantity, cost_per_unit?}` — positive to add, negative to remove
- `reason` (optional): Reason for adjustment
- `confirm` (optional, default false): Set false to preview, true to create

**Returns:** Adjustment ID and summary of changes.

---

### get_manufacturing_order
Look up manufacturing orders by order number or ID.

**Parameters:**
- `order_no` (optional): Order number (e.g., '#WEB20082 / 1')
- `order_id` (optional): Manufacturing order ID

**Returns:** Order details including status, quantities, costs, linked sales order, and timeline.

---

### create_item
Create a new item (product, material, or service).

**Parameters:**
- `type` (required): Item type - "product", "material", or "service"
- `name` (required): Item name
- `sku` (required): SKU for the item variant
- `uom` (optional): Unit of measure (default: "pcs")
- Plus optional fields: category_name, is_sellable, sales_price, purchase_price, etc.

---

### get_item / update_item / delete_item
CRUD operations for items by ID and type.

---

## Purchase Order Tools

### create_purchase_order
Create a purchase order with preview/confirm pattern.

**Parameters:**
- `supplier_id` (required): Supplier ID
- `location_id` (required): Warehouse location for receipt
- `order_number` (required): PO number (e.g., "PO-2025-001")
- `items` (required): Array of line items with variant_id, quantity, price_per_unit
- `confirm` (optional, default false): false=preview, true=create

**Safety:** When confirm=true, prompts user for confirmation before creating.

---

### receive_purchase_order
Receive items from a purchase order.

**Parameters:**
- `order_id` (required): Purchase order ID
- `items` (required): Array of items with purchase_order_row_id and quantity
- `confirm` (optional, default false): false=preview, true=receive

**Safety:** When confirm=true, prompts user for confirmation.

---

### verify_order_document
Verify a supplier document (invoice, packing slip) against a PO.

**Parameters:**
- `order_id` (required): Purchase order ID to verify against
- `document_items` (required): Array of items from document with sku, quantity, unit_price

**Returns:** Match status, discrepancies, and suggested actions.

---

### get_purchase_order
Look up a purchase order by order number or ID with all line items.

**Parameters:**
- `order_no` (optional): PO number (e.g., "PO-1022")
- `order_id` (optional): PO ID

**Returns:** Order details (status, supplier, total) plus rows with variant_id, quantity, price, arrival/received dates.

---

## Manufacturing & Sales Tools

### create_manufacturing_order
Create a manufacturing work order.

**Parameters:**
- `variant_id` (required): Variant ID of product to manufacture
- `planned_quantity` (required): Quantity to produce
- `location_id` (required): Production location ID
- `production_deadline_date` (optional): Production deadline
- `additional_info` (optional): Notes
- `confirm` (optional, default false): false=preview, true=create

---

### search_customers
Search customers by name or email.

**Parameters:**
- `query` (required): Search term
- `limit` (optional): Maximum results (default: 20)

**Returns:** List of customers with id, name, email, phone, currency.

---

### get_customer
Get full details for a customer by ID.

**Parameters:**
- `customer_id` (required): Customer ID

**Returns:** Full customer details (name, email, phone, currency, category, comment).

---

### get_manufacturing_order_recipe
List the ingredient rows for a manufacturing order.

**Parameters:**
- `manufacturing_order_id` (required): MO ID

**Returns:** List of recipe rows with row ID, variant ID, SKU, planned qty/unit, availability.

---

### add_manufacturing_order_recipe_row
Add a new ingredient to a manufacturing order's recipe.

**Parameters:**
- `manufacturing_order_id` (required): MO ID
- `sku` (optional): SKU of ingredient (resolved via cache)
- `variant_id` (optional): Variant ID directly (use when SKU isn't in cache)
- `planned_quantity_per_unit` (required): Qty needed per manufactured unit
- `notes` (optional): Notes
- `confirm` (optional, default false): false=preview, true=add

Provide either `sku` or `variant_id`.

---

### delete_manufacturing_order_recipe_row
Remove an ingredient from a manufacturing order's recipe.

**Parameters:**
- `recipe_row_id` (required): Recipe row ID (from get_manufacturing_order_recipe)
- `confirm` (optional, default false): false=preview, true=delete

---

### batch_update_manufacturing_order_recipes
Batch-update recipe rows across one or more MOs with ONE confirmation.

**Use modes (mixable):**
- `replacements`: "replace variant X with [Y, Z] across these MOs" — ideal
  for swapping a component across many MOs in one shot.
- `changes`: explicit per-MO row deletes and additions (escape hatch).

**Parameters:**
- `replacements` (optional): list of `{manufacturing_order_ids, old_sku or
  old_variant_id, new_components, strict}`
- `changes` (optional): list of `{manufacturing_order_id, remove_row_ids,
  add_variants}`
- `continue_on_error` (optional, default true): run all ops even if some fail
- `confirm` (optional, default false): false=preview, true=execute (single batch confirmation)

**Returns:** All sub-operations with individual status (success/failed/skipped),
grouped by replacement. Old rows are deleted first, then new rows added in
reverse order so they appear adjacent in Katana's natural sort order.

---

### create_sales_order
Create a sales order.

**Parameters:**
- `customer_id` (required): Customer ID (use `search_customers` to find)
- `order_number` (required): Unique sales order number
- `items` (required): Array of items with variant_id, quantity, and optional price_per_unit
- `confirm` (optional, default false): false=preview, true=create

---

### list_sales_orders
List sales orders with filters.

**Parameters:**
- `order_no` (optional): Exact order number
- `customer_id` (optional): Filter to a customer
- `location_id` (optional): Filter to a location
- `status` (optional): Order status (e.g., "PENDING", "DELIVERED")
- `production_status` (optional): Production status
- `needs_work_orders` (optional): Shortcut for `production_status="NONE"` —
  finds sales orders that haven't had manufacturing orders created yet
- `limit` (optional, default 50): Max rows to return

**Returns:** Summary rows with order_no, status, production_status, row_count,
total, currency, created_at, delivery_date.

---

### get_sales_order
Look up a single sales order by order number or ID with full line items.

**Parameters:**
- `order_no` (optional): SO number (e.g., "#WEB20394")
- `order_id` (optional): SO ID

**Returns:** Order header (status, customer, location, total, delivery_date)
plus `rows` with variant_id, SKU, quantity, price_per_unit, and any linked
manufacturing_order_id. SKU is enriched via the variant cache.

---

### create_product / create_material
Dedicated catalog tools for creating products or materials with a single variant.

---

### fulfill_order
Complete a manufacturing or sales order.

**Parameters:**
- `order_id` (required): Order ID to fulfill
- `order_type` (required): "manufacturing" or "sales"
- `confirm` (optional, default false): false=preview, true=fulfill
"""

HELP_RESOURCES = """
# Katana Resources Reference

Resources provide read-only **reference data** from the cache — small, stable
data you need as context. For transactional data (orders, movements), use the
corresponding tools (e.g., `get_manufacturing_order`, `get_inventory_movements`).

---

## Inventory Resources

### katana://inventory/items
Complete catalog of products, materials, and services.

**Contains:**
- All products, materials, services
- Item type and capabilities (is_sellable, is_producible, is_purchasable)
- Summary counts by type

**Use when:** Browsing the catalog, checking item types, getting an overview.

---

## Reference Data Resources

### katana://suppliers
All suppliers with contact info.

**Contains:**
- id, name, email, phone, currency, comment
- Summary count

**Use when:** Looking up `supplier_id` for `create_purchase_order`.

---

### katana://locations
All warehouses and facilities.

**Contains:**
- id, name, address, city, country, is_primary
- Summary count

**Use when:** Looking up `location_id` for orders or inventory checks.

---

### katana://tax-rates
All configured tax rates.

**Contains:**
- id, name, rate, display_name, default flags
- Summary count

**Use when:** Looking up `tax_rate_id` for sales order line items.

---

### katana://operators
All manufacturing operators.

**Contains:**
- id, name
- Summary count

**Use when:** Assigning operators to manufacturing order operations.

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
