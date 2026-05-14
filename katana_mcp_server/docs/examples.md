# Katana MCP Server - Workflow Examples

This guide provides workflow examples for common manufacturing ERP tasks using the
Katana MCP Server.

## Quick Start

After connecting to the MCP server, use the `katana://help` resource for detailed
guidance on tools and workflows.

## Core Workflows

### 1. Inventory Management

#### Check Item Stock

```
# Search for items
search_items(query="widget", limit=10)

# Get detailed variant information
get_variant_details(variant_id=12345)
```

#### Typical Flow

1. **Search** - Use `search_items` to find products by name, SKU, or description
1. **Inspect** - Use `get_variant_details` for full inventory details including stock
   levels
1. **Resources** - Browse `katana://inventory/items` for inventory overview

### 2. Purchase Order Lifecycle

#### Create a Purchase Order (Preview/Confirm Pattern)

All create/modify operations use a two-step confirmation:

```
# Step 1: Preview the order (no changes made)
create_purchase_order(
    supplier_id=42,
    location_id=1,
    line_items=[{"variant_id": 123, "quantity": 100, "unit_cost": 25.50}],
    confirm=false  # Preview mode
)

# Step 2: Create the order (after reviewing preview)
create_purchase_order(
    supplier_id=42,
    location_id=1,
    line_items=[{"variant_id": 123, "quantity": 100, "unit_cost": 25.50}],
    confirm=true  # Creates order, prompts for confirmation
)
```

#### Receive a Purchase Order

```
# Preview receiving (shows what will happen)
receive_purchase_order(
    order_id=1234,
    line_items=[{"line_item_id": 5678, "quantity": 100}],
    confirm=false
)

# Confirm receiving
receive_purchase_order(
    order_id=1234,
    line_items=[{"line_item_id": 5678, "quantity": 100}],
    confirm=true
)
```

#### Verify Order Documents

Use document verification to cross-reference supplier documents with orders:

```
verify_order_document(
    order_id=1234,
    document_items=[
        {"sku": "WIDGET-001", "quantity": 100, "unit_price": 25.50},
        {"sku": "GADGET-002", "quantity": 50, "unit_price": 15.00}
    ]
)
```

Returns one of three results:

- **Full Match** - All items match perfectly
- **Partial Match** - Some discrepancies found (quantity, price, or missing items)
- **No Match** - No items could be matched

### 3. Manufacturing Order Lifecycle

#### Fulfill a Manufacturing Order

```
# Preview completion
fulfill_order(
    order_id=1234,
    order_type="manufacturing",
    confirm=false
)

# Complete the order (marks as DONE)
fulfill_order(
    order_id=1234,
    order_type="manufacturing",
    confirm=true
)
```

Manufacturing order fulfillment:

- Marks the order status as DONE
- Updates inventory based on bill of materials (BOM)
- Adds finished goods to stock
- Consumes raw materials

### 4. Sales Order Fulfillment

#### Fulfill a Sales Order

```
# Preview fulfillment
fulfill_order(
    order_id=5678,
    order_type="sales",
    confirm=false
)

# Create fulfillment record
fulfill_order(
    order_id=5678,
    order_type="sales",
    confirm=true
)
```

Sales order fulfillment:

- Creates a fulfillment record
- Reduces available inventory
- Marks items as shipped

## Response Format

Every tool returns an MCP `ToolResult`. `content` is a list of `ContentBlock`s — for
this server, always a single text block whose `text` field carries the response
serialized as JSON (programmatic consumers `json.loads(result.content[0].text)`).
`structured_content` is one of two shapes depending on what the tool *actually emitted*
(not its registration metadata):

- **Data-only response** (any tool returning `make_json_result(response)` — or an inline
  `ToolResult(...)` when the tool needs custom dump kwargs, like
  `get_manufacturing_order` threading its include/verbose flags through `model_dump`
  selectors, or the batch branches of UI-meta tools like `check_inventory` /
  `get_variant_details`) — `structured_content` is the response payload as a plain dict,
  so programmatic consumers can branch on response shape without re-parsing `content`.
- **UI-emitting response** (any tool returning `make_tool_result(response, ui=app)`) —
  `structured_content` carries the Prefab card envelope (a `PrefabApp` serialized dict)
  for MCP-Apps hosts to render. The response payload lives only in `content` on these
  responses.

Some tools (`check_inventory`, `get_variant_details`) are registered with
`meta={"ui": True}` but pick between the two shapes per-request: a single-item request
attaches the rich Prefab card; a batch request returns the payload dict. The
`structured_content` shape is what programmatic consumers should branch on.

Sketch of a data-only response (pseudo-JSON; `content` is actually a list of one text
block):

```text
ToolResult(
    content=[TextContent(text='{"order_id": 1234, "order_number": "PO-2024-001", ...}')],
    structured_content={"order_id": 1234, "order_number": "PO-2024-001", ...},
)
```

The `format: "markdown" | "json"` parameter was removed in #719; see `katana://help` for
the current contract.

## Resources

The server provides read-only resources for browsing cached reference data.
Transactional data (orders, stock movements) uses tools instead.

| Resource                   | Description                             |
| -------------------------- | --------------------------------------- |
| `katana://help`            | Help index and quick start              |
| `katana://help/workflows`  | Workflow documentation                  |
| `katana://help/tools`      | Tool reference                          |
| `katana://help/resources`  | Resource documentation                  |
| `katana://inventory/items` | Browse product/material/service catalog |
| `katana://suppliers`       | Supplier directory with contact info    |
| `katana://locations`       | Warehouses and facilities               |
| `katana://tax-rates`       | Configured tax rates                    |
| `katana://operators`       | Manufacturing operators                 |

## Safety Patterns

### Preview/Confirm Pattern

All operations that create or modify data use a two-step pattern:

1. **Preview** (`confirm=false`) - Shows what would happen without making changes
1. **Confirm** (`confirm=true`) - Executes the operation with user confirmation prompt

This prevents accidental modifications and allows reviewing changes before committing.

### Elicitation

When `confirm=true`, the server uses FastMCP's elicitation feature to prompt for
explicit user confirmation before executing destructive or irreversible operations.

## Error Handling

Tools return structured error information:

- **Validation errors** - Invalid input parameters
- **API errors** - Katana API failures with status codes
- **Not found errors** - Resources that don't exist

Errors include actionable `next_actions` suggestions when applicable.

## Token Efficiency

The server is designed to minimize token usage:

1. **Minimal Instructions** - Server instructions are brief; use `katana://help` for
   details
1. **Progressive Discovery** - Load help resources on-demand as needed
1. **JSON-only content** - Every tool returns its response as a JSON text block in
   `content` (`json.loads(result.content[0].text)` for programmatic consumers; LLM
   consumers read the JSON natively). Responses that emit Prefab UI carry the card
   envelope in `structured_content` for iframe-rendering hosts (see the Response Format
   section above for the per-shape contract). The `format: "markdown" | "json"`
   parameter was removed in #719.
