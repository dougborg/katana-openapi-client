# MCP v0.1.0 Implementation Plan

**Goal**: Build a small but complete MCP implementation that showcases ALL MCP features
while supporting actual workflows.

**Design Philosophy**: "Small set of all the MCP features so we can best see how
everything works together"

**Scope**:

- **10 Tools** - Cover all 7 workflows with elicitation pattern
- **6 Resources** - Inventory (items, movements, adjustments), Orders (sales, purchase,
  manufacturing)
- **3 Prompts** - Complete workflow automation
- **Full Documentation** - 3-level docs for every primitive

______________________________________________________________________

## User Workflows (Priority Order)

Based on actual usage patterns:

1. **Searching for and accessing info about items** (Products, Materials, Variants,
   Services)
1. **Creating new Items**
1. **Creating POs**
1. **Creating Work Orders**
1. **Completing Work Orders and Fulfilling Sales Orders**
1. **Verifying sales order confirmations, invoices and other documents against POs**
1. **Receiving POs**

______________________________________________________________________

## Implementation Architecture

### Tools (8-10 Total)

#### Inventory & Catalog (Workflow #1)

1. **`search_variants`** - Search across all item types (Products, Materials, Variants,
   Services)

   - Input: `query: str`, `limit: int = 20`,
     `item_type: Literal["all", "product", "material", "service"] = "all"`
   - Output: `SearchVariantsResponse` with `items: list[VariantSearchResult]`,
     `total_count: int`
   - Returns: Pydantic domain models (KatanaVariant, KatanaProduct, etc.)
   - Documentation: Comprehensive field descriptions, usage examples, common patterns

1. **`get_variant_details`** - Get detailed info for a specific SKU

   - Input: `sku: str`
   - Output: `VariantDetailsResponse` with full KatanaVariant + stock info + BOM info
   - Documentation: What data is available, when to use this vs search

1. **`check_inventory`** - Check stock levels for SKU

   - Input: `sku: str`
   - Output: `StockInfo` (keep existing - already good)
   - Documentation: Real-time vs cached data, stock calculation logic

#### Item Creation (Workflow #2)

4. **`create_product`** - Create new product with variants

   - Input: `CreateProductRequest` (Pydantic model with validation)
   - Output: `CreateProductResponse` with created KatanaProduct + warnings +
     next_actions
   - Documentation: Required fields, validation rules, variant creation, common patterns
   - Elicitation: Preview mode (confirm=false) shows what will be created

1. **`create_material`** - Create new material

   - Input: `CreateMaterialRequest`
   - Output: `CreateMaterialResponse` with created KatanaMaterial + warnings +
     next_actions
   - Documentation: Material vs product differences, when to use each

#### Purchase Orders (Workflows #3, #6, #7)

6. **`create_purchase_order`** - Create PO with line items

   - Input: `CreatePurchaseOrderRequest` (supplier_id, items, confirm)
   - Output: `CreatePurchaseOrderResponse` (order preview or created order)
   - Documentation: Validation rules, supplier selection, item selection
   - **Elicitation Pattern**: Two-step confirmation
     - Step 1: `confirm=false` → Returns preview with costs, warnings, next_actions
     - Step 2: `confirm=true` → Creates the actual PO
   - Example:
     ```python
     # Step 1: Preview
     preview = await create_purchase_order(
         CreatePurchaseOrderRequest(
             supplier_id=123,
             items=[OrderItem(sku="WIDGET-001", quantity=100)],
             confirm=False  # Preview mode
         )
     )
     # Returns: PurchaseOrderPreview with total_cost, lead_times, warnings

     # Step 2: Confirm
     order = await create_purchase_order(
         CreatePurchaseOrderRequest(
             supplier_id=123,
             items=[OrderItem(sku="WIDGET-001", quantity=100)],
             confirm=True  # Create mode
         )
     )
     # Returns: Created PurchaseOrder with order_number, status
     ```

1. **`receive_purchase_order`** - Mark PO items as received

   - Input: `ReceivePurchaseOrderRequest` (order_id, items_received, confirm)
   - Output: `ReceivePurchaseOrderResponse` with updated stock levels + next_actions
   - Documentation: Partial receiving, quality checks, stock updates
   - Elicitation: Preview before finalizing receipt

1. **`verify_order_document`** - Compare document against open PO

   - Input: `VerifyOrderDocumentRequest` (order_id, document_items)
   - Output: `VerifyOrderDocumentResponse` with matches, discrepancies,
     suggested_actions
   - Documentation: What to check, how to handle discrepancies

#### Manufacturing Orders (Workflows #4, #5)

9. **`create_manufacturing_order`** - Create work order

   - Input: `CreateManufacturingOrderRequest` (product_sku, quantity, confirm)
   - Output: `CreateManufacturingOrderResponse` with order + material requirements +
     warnings
   - Documentation: BOM requirements, material availability checks
   - Elicitation: Preview with material availability before creating

1. **`fulfill_order`** - Complete work order or fulfill sales order

   - Input: `FulfillOrderRequest` (order_id, order_type: Literal\["manufacturing",
     "sales"\], confirm)
   - Output: `FulfillOrderResponse` with final status + inventory updates + next_actions
   - Documentation: Fulfillment criteria, inventory impacts, completion steps
   - Elicitation: Confirm before finalizing

______________________________________________________________________

### Resources (6 Total)

Resources provide read-only contextual data that AI can access to understand the current
state of your Katana system. Each resource stays under the 1MB size limit through
pagination when needed.

#### Inventory Resources

##### 1. Catalog Items (with Inventory)

- **URI**: `katana://inventory/items`
- **Type**: Dynamic resource (refreshes every 5 minutes)
- **Content**: Paginated list of all catalog items with current inventory
- **Purpose**: Complete catalog view for workflow #1 (searching/accessing items)
- **Size Management**:
  - Returns first 100 items by default (typical size: 50-100KB)
  - Includes pagination cursor for large catalogs
  - Use `katana://inventory/items?cursor={next_cursor}` for next page
  - Each variant: ~500-1000 bytes (includes inventory data)
- **Data**:
  ```json
  {
    "generated_at": "2025-01-15T10:30:00Z",
    "summary": {
      "total_items": 1234,
      "products": 150,
      "materials": 900,
      "services": 20,
      "variants": 164,
      "items_in_response": 100,
      "has_more": true
    },
    "items": [
      {
        "id": 456,
        "sku": "WIDGET-001",
        "name": "Premium Widget / Red / Large",
        "type": "product",
        "product_name": "Premium Widget",
        "is_sellable": true,
        "is_purchasable": false,
        "inventory": {
          "in_stock": 150,
          "available": 120,
          "allocated": 30,
          "in_production": 50,
          "on_order": 200,
          "stock_value": 4500.00
        },
        "bom": {
          "has_bom": true,
          "materials_count": 3
        },
        "pricing": {
          "sales_price": 45.00,
          "cost": 30.00
        }
      },
      {
        "id": 789,
        "sku": "BOLT-M8",
        "name": "M8 Hex Bolt",
        "type": "material",
        "is_purchasable": true,
        "inventory": {
          "in_stock": 5,
          "available": 5,
          "allocated": 0,
          "reorder_point": 50
        },
        "pricing": {
          "cost": 0.15
        },
        "low_stock": true
      }
    ],
    "pagination": {
      "cursor": "eyJpZCI6MTAwfQ==",
      "next_uri": "katana://inventory/items?cursor=eyJpZCI6MTAwfQ=="
    },
    "alerts": {
      "low_stock_count": 15,
      "out_of_stock_count": 3,
      "negative_stock_count": 0
    },
    "next_actions": [
      "Review 15 low stock items",
      "Create PO for out-of-stock materials",
      "Use search_variants tool for specific items"
    ]
  }
  ```
- **Documentation**:
  - Pagination: Use cursor for next page
  - Inventory fields: What each stock level means
  - Item types: Product vs Material vs Service differences
  - When to use this vs search_variants tool
  - Refresh rate: 5 minutes (may show stale data during high-frequency updates)

##### 2. Stock Movements

- **URI**: `katana://inventory/stock-movements`
- **Type**: Dynamic resource (refreshes every 5 minutes)
- **Content**: Recent inventory movements (transfers, allocations, receipts,
  adjustments)
- **Purpose**: Track inventory changes, audit trail, understand stock flow
- **Size Management**: Last 100 movements by default (~20-30KB), paginated for history
- **Data**:
  ```json
  {
    "generated_at": "2025-01-15T10:30:00Z",
    "summary": {
      "total_movements": 2456,
      "movements_in_response": 100,
      "date_range": {
        "from": "2025-01-14T10:30:00Z",
        "to": "2025-01-15T10:30:00Z"
      },
      "movement_types": {
        "receipt": 25,
        "transfer": 15,
        "allocation": 40,
        "adjustment": 10,
        "consumption": 10
      }
    },
    "movements": [
      {
        "id": 12345,
        "timestamp": "2025-01-15T09:45:00Z",
        "type": "receipt",
        "sku": "BOLT-M8",
        "quantity": 1000,
        "from_location": null,
        "to_location": "Warehouse A",
        "reference": {
          "type": "purchase_order",
          "id": 123,
          "number": "PO-2025-018"
        },
        "user": "john@example.com",
        "notes": "Received from supplier delivery"
      },
      {
        "id": 12344,
        "timestamp": "2025-01-15T09:30:00Z",
        "type": "allocation",
        "sku": "WIDGET-001",
        "quantity": -50,
        "from_location": "Warehouse A",
        "to_location": null,
        "reference": {
          "type": "sales_order",
          "id": 789,
          "number": "SO-2025-042"
        },
        "user": "system",
        "notes": "Allocated to sales order"
      },
      {
        "id": 12343,
        "timestamp": "2025-01-15T08:15:00Z",
        "type": "adjustment",
        "sku": "PLATE-STEEL",
        "quantity": -5,
        "from_location": "Warehouse A",
        "to_location": null,
        "reference": {
          "type": "stock_adjustment",
          "id": 456,
          "number": "ADJ-2025-012"
        },
        "user": "jane@example.com",
        "notes": "Damaged material - write off"
      }
    ],
    "pagination": {
      "cursor": "eyJ0aW1lc3RhbXAiOiIyMDI1LTAxLTE0VDEwOjMwOjAwWiJ9",
      "next_uri": "katana://inventory/stock-movements?cursor=eyJ0aW1lc3RhbXAiOiIyMDI1LTAxLTE0VDEwOjMwOjAwWiJ9"
    },
    "next_actions": [
      "Review recent adjustments for trends",
      "Check large movements for accuracy",
      "Audit negative adjustments"
    ]
  }
  ```
- **Documentation**:
  - Movement types: receipt, transfer, allocation, adjustment, consumption
  - Negative quantities: indicate stock reduction
  - Reference types: Links to source transaction (PO, SO, MO, adjustment)
  - Audit trail: Who, when, why for each movement
  - Time range filtering: Use query params for custom date ranges

##### 3. Stock Adjustments

- **URI**: `katana://inventory/stock-adjustments`
- **Type**: Dynamic resource (refreshes every 5 minutes)
- **Content**: Manual stock adjustments (corrections, damage, shrinkage, etc.)
- **Purpose**: Track inventory corrections, understand discrepancies, audit adjustments
- **Size Management**: Last 50 adjustments by default (~10-15KB), paginated for history
- **Data**:
  ```json
  {
    "generated_at": "2025-01-15T10:30:00Z",
    "summary": {
      "total_adjustments": 145,
      "adjustments_in_response": 50,
      "date_range": {
        "from": "2025-01-01T00:00:00Z",
        "to": "2025-01-15T10:30:00Z"
      },
      "adjustment_reasons": {
        "damage": 12,
        "shrinkage": 8,
        "found": 5,
        "count_correction": 15,
        "other": 10
      },
      "net_value_impact": -2500.00
    },
    "adjustments": [
      {
        "id": 456,
        "adjustment_number": "ADJ-2025-012",
        "created_at": "2025-01-15T08:15:00Z",
        "status": "completed",
        "created_by": "jane@example.com",
        "reason": "damage",
        "notes": "Water damage from roof leak - 5 plates unsalvageable",
        "items": [
          {
            "sku": "PLATE-STEEL",
            "name": "Steel Plate 1m x 2m",
            "quantity_before": 45,
            "quantity_after": 40,
            "adjustment": -5,
            "unit_cost": 50.00,
            "value_impact": -250.00,
            "location": "Warehouse A"
          }
        ],
        "total_value_impact": -250.00
      },
      {
        "id": 455,
        "adjustment_number": "ADJ-2025-011",
        "created_at": "2025-01-14T16:45:00Z",
        "status": "completed",
        "created_by": "john@example.com",
        "reason": "found",
        "notes": "Found 10 bolts in secondary storage during cleanup",
        "items": [
          {
            "sku": "BOLT-M8",
            "name": "M8 Hex Bolt",
            "quantity_before": 5,
            "quantity_after": 15,
            "adjustment": 10,
            "unit_cost": 0.15,
            "value_impact": 1.50,
            "location": "Warehouse B"
          }
        ],
        "total_value_impact": 1.50
      }
    ],
    "pagination": {
      "cursor": "eyJpZCI6NDU1fQ==",
      "next_uri": "katana://inventory/stock-adjustments?cursor=eyJpZCI6NDU1fQ=="
    },
    "next_actions": [
      "Investigate high shrinkage rates",
      "Review damage adjustments for prevention",
      "Audit large value-impact adjustments"
    ]
  }
  ```
- **Documentation**:
  - Adjustment reasons: Standard categories (damage, shrinkage, found, count_correction,
    other)
  - Value impact: Financial effect of adjustment (negative = loss, positive = gain)
  - Status: draft, completed, cancelled
  - Multi-item adjustments: Single adjustment can affect multiple SKUs
  - Audit requirements: Who, when, why, and value impact

#### Order Resources

##### 4. Open Sales Orders

- **URI**: `katana://sales-orders`
- **Type**: Dynamic resource (refreshes every 5 minutes)
- **Content**: All open/pending sales orders
- **Purpose**: Support workflow #5 (fulfilling sales orders), workflow #6 (verifying
  documents)
- **Size Management**: Paginated (50 orders per page, ~10-20KB per page)
- **Data**:
  ```json
  {
    "generated_at": "2025-01-15T10:30:00Z",
    "summary": {
      "total_open_orders": 45,
      "orders_in_response": 45,
      "total_value": 125000.00,
      "overdue_count": 3,
      "ready_to_ship_count": 12
    },
    "orders": [
      {
        "order_id": 789,
        "order_number": "SO-2025-042",
        "customer": {
          "id": 234,
          "name": "Acme Retail Inc"
        },
        "created_at": "2025-01-10T09:00:00Z",
        "due_date": "2025-01-20",
        "status": "in_progress",
        "fulfillment_status": "awaiting_manufacturing",
        "total_amount": 12500.00,
        "items_count": 8,
        "top_items": [
          {"sku": "WIDGET-001", "quantity": 50, "status": "in_production"},
          {"sku": "WIDGET-002", "quantity": 25, "status": "ready"}
        ],
        "days_until_due": 5,
        "is_overdue": false
      }
    ],
    "pagination": {
      "has_more": false
    },
    "next_actions": [
      "Ship 12 ready-to-ship orders",
      "Follow up on 3 overdue orders",
      "Check manufacturing status for awaiting orders"
    ]
  }
  ```
- **Documentation**:
  - Order statuses: draft, in_progress, fulfilled, cancelled
  - Fulfillment statuses: awaiting_manufacturing, awaiting_stock, ready_to_ship, shipped
  - When to use this vs tools
  - Refresh frequency

##### 5. Open Purchase Orders

- **URI**: `katana://purchase-orders`
- **Type**: Dynamic resource (refreshes every 5 minutes)
- **Content**: All open/pending purchase orders
- **Purpose**: Support workflow #6 (verifying documents), workflow #7 (receiving POs)
- **Size Management**: Paginated (50 orders per page, ~10-20KB per page)
- **Data**:
  ```json
  {
    "generated_at": "2025-01-15T10:30:00Z",
    "summary": {
      "total_open_orders": 23,
      "orders_in_response": 23,
      "total_pending_value": 85000.00,
      "overdue_count": 2,
      "awaiting_receipt_count": 8
    },
    "orders": [
      {
        "order_id": 123,
        "order_number": "PO-2025-018",
        "supplier": {
          "id": 456,
          "name": "Industrial Supply Co"
        },
        "created_at": "2025-01-05T14:00:00Z",
        "expected_delivery": "2025-01-18",
        "status": "open",
        "receipt_status": "not_received",
        "total_amount": 8500.00,
        "items_count": 12,
        "top_items": [
          {"sku": "BOLT-M8", "quantity": 1000, "received": 0},
          {"sku": "PLATE-STEEL", "quantity": 50, "received": 0}
        ],
        "days_until_delivery": 3,
        "is_overdue": false
      }
    ],
    "pagination": {
      "has_more": false
    },
    "next_actions": [
      "Prepare to receive 8 awaiting-receipt POs",
      "Follow up on 2 overdue deliveries",
      "Review PO-2025-018 (delivery expected in 3 days)"
    ]
  }
  ```
- **Documentation**:
  - Order statuses: draft, open, received, cancelled
  - Receipt statuses: not_received, partially_received, fully_received
  - Partial receiving tracking
  - When to use this vs tools

##### 6. Open Work Orders (Manufacturing)

- **URI**: `katana://manufacturing-orders`
- **Type**: Dynamic resource (refreshes every 5 minutes)
- **Content**: All active manufacturing orders
- **Purpose**: Support workflow #4 (creating work orders), workflow #5 (completing work
  orders)
- **Size Management**: Paginated (50 orders per page, ~15-25KB per page)
- **Data**:
  ```json
  {
    "generated_at": "2025-01-15T10:30:00Z",
    "summary": {
      "total_open_orders": 18,
      "orders_in_response": 18,
      "in_progress_count": 12,
      "planned_count": 6,
      "blocked_count": 2
    },
    "orders": [
      {
        "order_id": 345,
        "order_number": "MO-2025-089",
        "product": {
          "sku": "WIDGET-001",
          "name": "Premium Widget / Red / Large"
        },
        "quantity": 100,
        "created_at": "2025-01-12T08:00:00Z",
        "due_date": "2025-01-19",
        "status": "in_progress",
        "completion_percentage": 60,
        "material_availability": {
          "all_available": false,
          "missing_materials": [
            {"sku": "BOLT-M8", "needed": 400, "available": 5, "shortage": 395}
          ]
        },
        "estimated_completion": "2025-01-18T16:00:00Z",
        "days_until_due": 4,
        "is_blocked": true,
        "blocking_reason": "Insufficient materials"
      }
    ],
    "pagination": {
      "has_more": false
    },
    "next_actions": [
      "Create PO for blocked MO materials",
      "Complete 8 in-progress orders nearing 100%",
      "Review planned orders for material availability"
    ]
  }
  ```
- **Documentation**:
  - Order statuses: planned, in_progress, completed, cancelled
  - Blocking reasons: material shortage, equipment unavailable, etc.
  - Completion tracking
  - Material availability interpretation
  - When to use this vs tools

______________________________________________________________________

### Prompts (3 Total)

#### 1. Create and Receive Purchase Order

- **Name**: `create_and_receive_po`
- **Purpose**: Complete workflow for PO lifecycle (workflows #3 + #7)
- **Template**:
  ```
  I need to order materials and receive them when they arrive.

  Supplier: {{supplier_name}}
  Items needed:
  {{#items}}
  - {{sku}}: {{quantity}} units
  {{/items}}

  Expected delivery: {{expected_delivery_date}}

  Please:
  1. Search for the supplier by name
  2. Create a purchase order (preview first)
  3. Confirm the PO if it looks correct
  4. [Later] Help me receive the items when they arrive
  ```
- **Arguments**: `supplier_name`, `items` (array of {sku, quantity}),
  `expected_delivery_date`
- **Documentation**: When to use, what happens at each step, how to handle errors

#### 2. Verify Document and Create PO

- **Name**: `verify_and_create_po`
- **Purpose**: Check invoice/confirmation against existing POs, create new PO if needed
  (workflow #6)
- **Template**:
  ```
  I received a {{document_type}} from {{supplier_name}} with the following items:

  {{#items}}
  - {{sku}}: {{quantity}} units @ ${{unit_price}}
  {{/items}}

  Total: ${{total_amount}}

  Please:
  1. Check if we have an open PO for this supplier
  2. Verify the items and amounts match any existing PO
  3. Report any discrepancies
  4. If no matching PO exists, ask if I want to create one
  ```
- **Arguments**: `document_type` (invoice/confirmation), `supplier_name`, `items`,
  `total_amount`
- **Documentation**: Verification logic, what constitutes a "match", handling partial
  matches

#### 3. Complete Work Order or Fulfill Sales Order

- **Name**: `fulfill_order`
- **Purpose**: Complete a manufacturing work order or fulfill a sales order (workflow
  #5)
- **Template**:
  ```
  I need to {{#if order_type == "manufacturing"}}complete{{else}}fulfill{{/if}} {{order_type}} order {{order_number}}.

  {{#if order_type == "manufacturing"}}
  The production run is complete and items are ready to add to inventory.
  {{else}}
  The customer order has been shipped and should be marked as fulfilled.
  {{/if}}

  Please:
  1. Retrieve the order details
  2. Show me what will happen when I {{#if order_type == "manufacturing"}}complete{{else}}fulfill{{/if}} it (inventory updates, etc.)
  3. Ask for confirmation before finalizing
  4. {{#if order_type == "manufacturing"}}Complete{{else}}Fulfill{{/if}} the order
  5. Show me the updated inventory levels
  ```
- **Arguments**: `order_type` (manufacturing/sales), `order_number`
- **Documentation**: Completion/fulfillment criteria, inventory impacts, status changes

______________________________________________________________________

## Documentation Strategy

Every MCP primitive includes **three levels of documentation**:

### 1. Tool/Resource/Prompt Description

- **What**: One-sentence summary
- **Example**: "Search for products, materials, and services by name or SKU"

### 2. Field Descriptions

- **What**: Pydantic Field(..., description="...") for every parameter
- **Example**:
  ```python
  query: str = Field(..., description="Search query to match against SKU, name, or description")
  limit: int = Field(20, description="Maximum results to return (1-100)", ge=1, le=100)
  ```

### 3. Extended Documentation

- **What**: Detailed docstring with:

  - Purpose and use cases
  - Parameter details and validation rules
  - Return value structure
  - Common patterns and examples
  - Error handling guidance
  - Related tools/resources/prompts
  - Next actions suggestions

- **Example**:

  ```python
  async def search_variants(
      request: SearchVariantsRequest,
      context: Context
  ) -> SearchVariantsResponse:
      """Search for variants across all catalog item types.

      Purpose:
          Find products, materials, and services by name, SKU, or description.
          Returns Pydantic domain models with full type safety.

      Use Cases:
          - "Find all widgets" → Search by name
          - "Look up SKU WIDGET-001" → Exact SKU match
          - "Show me all materials" → Filter by type

      Parameters:
          - query: Matches against SKU (exact), name (fuzzy), description (fuzzy)
          - limit: Caps results (default 20, max 100)
          - item_type: Filter by product/material/service or search all

      Returns:
          SearchVariantsResponse with:
          - items: List of domain models (KatanaVariant/KatanaProduct/KatanaMaterial)
          - total_count: Total matches (may exceed limit)
          - next_actions: Suggested follow-up actions

      Common Patterns:
          1. Broad search → Narrow with filters
             search("widget") → 50 results
             search("widget", item_type="product") → 12 results

          2. Exact SKU lookup → Get details
             search("WIDGET-001") → [one result]
             get_variant_details("WIDGET-001") → full info

      Related Resources:
          - katana://dashboard/inventory - See inventory overview first
          - katana://variant/{sku} - Get detailed info after search

      Related Prompts:
          - create_and_receive_po - Create PO after finding items

      Error Handling:
          - Empty results → Check spelling, try broader query
          - Too many results → Add item_type filter or more specific query
          - Network errors → Automatic retry with exponential backoff

      Next Actions:
          After getting results, you might:
          - Call get_variant_details(sku) for detailed info
          - Call check_inventory(sku) for stock levels
          - Call create_purchase_order if stock is low
      """
  ```

______________________________________________________________________

## Elicitation Pattern

**Pattern**: Two-Step Confirmation for Destructive/Critical Operations

**Implementation**: All creation/modification tools support `confirm` parameter

**Example - Create Purchase Order**:

```python
class CreatePurchaseOrderRequest(BaseModel):
    """Request to create a purchase order."""
    supplier_id: int = Field(..., description="Supplier ID", gt=0)
    items: list[OrderItem] = Field(..., min_items=1, description="Line items")
    expected_delivery: date | None = Field(None, description="Expected delivery date")
    notes: str | None = Field(None, description="Order notes")
    confirm: bool = Field(
        False,
        description="Set to true to confirm order creation. False returns preview."
    )

class PurchaseOrderPreview(BaseModel):
    """Preview of PO before creation."""
    supplier_name: str
    items: list[OrderItem]
    subtotal: float
    tax: float
    total: float
    estimated_lead_time_days: int
    warnings: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(
        default=["Review totals", "Verify supplier", "Set confirm=true to create"]
    )

class PurchaseOrderCreated(BaseModel):
    """Created purchase order details."""
    order_id: int
    order_number: str
    status: str
    total_amount: float
    created_at: datetime
    next_actions: list[str] = Field(
        default=["Share PO with supplier", "Schedule follow-up", "Track delivery"]
    )

CreatePurchaseOrderResponse = PurchaseOrderPreview | PurchaseOrderCreated

async def create_purchase_order(
    request: CreatePurchaseOrderRequest,
    context: Context
) -> CreatePurchaseOrderResponse:
    """Create a purchase order with two-step confirmation.

    Step 1: Call with confirm=False (default)
        - Validates inputs
        - Calculates totals
        - Checks supplier info
        - Returns preview without creating anything

    Step 2: Call with confirm=True
        - Creates the actual PO in Katana
        - Returns created order details

    This pattern prevents accidental PO creation and gives you a chance
    to review costs, quantities, and supplier details first.
    """
    if not request.confirm:
        # Preview mode - don't create anything
        return await _generate_po_preview(request, context)
    else:
        # Confirm mode - create the PO
        return await _create_po_confirmed(request, context)
```

**Usage in Prompts**:

```
Please:
1. Create a purchase order (preview first)  ← Calls with confirm=false
2. Confirm the PO if it looks correct        ← Calls with confirm=true
```

**Apply To**:

- `create_purchase_order` (workflow #3)
- `create_manufacturing_order` (workflow #4)
- `fulfill_order` (workflow #5)
- `receive_purchase_order` (workflow #7)
- `create_product` (workflow #2)
- `create_material` (workflow #2)

______________________________________________________________________

## Implementation Phases

### Phase 1: Enhanced Tools with Documentation (Week 1)

- Implement 10 tools with:
  - Pydantic request/response models
  - Comprehensive docstrings
  - Field-level descriptions
  - Elicitation pattern where applicable
  - Next actions suggestions
- Update existing tools (check_inventory, search_variants) to new pattern
- Add logging with structured context

**Deliverable**: All tools working with full documentation

### Phase 2: Resources Implementation (Week 1)

- Implement 6 resources:
  - **Inventory**: `katana://inventory/items`, `katana://inventory/stock-movements`,
    `katana://inventory/stock-adjustments`
  - **Orders**: `katana://sales-orders`, `katana://purchase-orders`,
    `katana://manufacturing-orders`
- Add caching (5 minute TTL)
- Add pagination support (cursor-based)
- Add size validation (\<1MB per response)
- Document refresh rates and usage

**Deliverable**: Resources available and documented

### Phase 3: Prompts Implementation (Week 2)

- Create 3 workflow prompts:
  - `create_and_receive_po`
  - `verify_and_create_po`
  - `fulfill_and_close_order`
- Test with real scenarios
- Document parameters and examples

**Deliverable**: Prompts working and tested

### Phase 4: Integration Testing (Week 2)

- Test complete workflows end-to-end
- Verify elicitation pattern UX
- Validate resource size constraints
- Test error handling and recovery
- Performance testing (response times)

**Deliverable**: Fully tested MCP v0.1.0

### Phase 5: Documentation Polish (Week 2)

- Update MCP_ARCHITECTURE_DESIGN.md with final implementation
- Create user guide for each workflow
- Add examples and tutorials
- Document common patterns and anti-patterns

**Deliverable**: Complete documentation

______________________________________________________________________

## Success Metrics

### Functional Requirements

- ✅ 10 tools implemented
- ✅ 6 resources available (3 inventory + 3 orders)
- ✅ 3 prompts working
- ✅ Elicitation pattern in use
- ✅ All 7 workflows supported

### Quality Requirements

- ✅ 100% type coverage (mypy strict)
- ✅ 90%+ test coverage
- ✅ All tools have comprehensive docstrings
- ✅ All fields have descriptions
- ✅ Resources stay under 1MB
- ✅ Response times \<500ms P99

### Documentation Requirements

- ✅ Every tool documented at 3 levels
- ✅ Every resource has usage guide
- ✅ Every prompt has examples
- ✅ Workflow guides for all 7 patterns
- ✅ Error handling documented

______________________________________________________________________

## Issue Structure

### Recommendation: Create New Epic

**Close existing issues** #35-46 (outdated after architecture review)

**Create new epic**: "MCP v0.1.0 - Small Complete Implementation"

**New issues** (aligned with phases):

1. **#83**: Phase 1 - Enhanced Tools (10 tools with full documentation)
1. **#84**: Phase 2 - Resources (3 resources with caching)
1. **#85**: Phase 3 - Prompts (3 workflow prompts)
1. **#86**: Phase 4 - Integration Testing
1. **#87**: Phase 5 - Documentation Polish

**Dependencies**:

- #83 blocks #84, #85 (need tools first)
- #84, #85 block #86 (need all primitives for integration testing)
- #86 blocks #87 (verify before documenting)

**Parallel work possible**:

- #84 and #85 can run in parallel after #83

______________________________________________________________________

## Next Steps

1. **Review this plan** - Confirm alignment with vision
1. **Create issue structure** - Epic + 5 issues
1. **Begin Phase 1** - Start with enhanced tools
1. **Iterate** - Adjust based on learnings

**Questions for you**:

- Does this scope feel right? (8-10 tools, 3 resources, 3 prompts)
- Should we add/remove any tools for your workflows?
- Any specific documentation needs beyond what's outlined?
