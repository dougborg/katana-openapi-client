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
- **check_inventory** - Check stock levels for one or more SKUs or variant IDs (pass a list for a summary table)
- **list_low_stock_items** - Find items needing reorder
- **create_stock_adjustment / list_stock_adjustments / update_stock_adjustment / delete_stock_adjustment** - Full CRUD for manual inventory adjustments

### Purchase Orders
- **create_purchase_order** - Create PO with preview/confirm pattern
- **list_purchase_orders** - List POs with supplier/status/date filters
- **receive_purchase_order** - Receive items and update inventory
- **verify_order_document** - Verify supplier documents against POs (returns the full PO alongside match/discrepancy details)
- **get_purchase_order** - Look up a PO by number or ID — exhaustive detail (every PO/row field, additional cost rows, accounting metadata)
- **update_purchase_order** - Update header fields (incl. status, expected_arrival_date)
- **delete_purchase_order** - Delete a PO (preview/confirm)
- **add_purchase_order_row / update_purchase_order_row / delete_purchase_order_row** - Full row-level CRUD with per-field diff previews
- **add_purchase_order_additional_cost / update_purchase_order_additional_cost / delete_purchase_order_additional_cost** - Manage freight/duty/handling cost rows

### Manufacturing & Sales
- **create_manufacturing_order** - Create production work orders
- **list_manufacturing_orders** - List MOs with status/location/date filters
- **get_manufacturing_order** - Look up an MO with full details
- **fulfill_order** - Complete manufacturing or sales orders
- **create_sales_order** - Create sales orders with preview/confirm
- **list_sales_orders** - List SOs with customer/status/date filters

### Stock Transfers
- **create_stock_transfer** - Move inventory between locations (preview/confirm)
- **list_stock_transfers** - List transfers with status / location / date filters
- **update_stock_transfer** - Update transfer body fields
- **update_stock_transfer_status** - Transition status (DRAFT → IN_TRANSIT → RECEIVED)
- **delete_stock_transfer** - Delete a transfer

## Safety Pattern

All create/modify operations use a **two-step confirm pattern**:
1. Call with `confirm=false` to preview (no changes made)
2. Call with `confirm=true` to execute

Destructive tools advertise this via the standard MCP `destructiveHint`
tool annotation; hosts that respect the annotation prompt the user before
invoking. The server does not gate further.

## Output Format

Every list/get/search and reporting tool accepts a shared `format` parameter:

- `format="markdown"` (default) — human-readable markdown tables / sections.
- `format="json"` — structured JSON matching the tool's Pydantic response,
  for programmatic consumers that would otherwise have to re-parse markdown.

Default behavior is unchanged. Pass `format="json"` when chaining tool calls
or feeding output into downstream aggregation / filtering.

## Linking to Katana

`get_*` and `create_*` tools (and the rows on their `list_*` siblings)
return a `katana_url` field for the entity. Prefer that over composing
URLs by hand — Katana's path conventions are inconsistent
(`/salesorder/{id}` is singular, `/products/{id}` is plural) and easy to
get wrong silently.

Patterns (base: `factory.katanamrp.com`, override via `KATANA_WEB_BASE_URL`):

| Entity | Path |
|--------|------|
| Sales orders | `/salesorder/{id}` |
| Manufacturing orders | `/manufacturingorder/{id}` |
| Purchase orders | `/purchaseorder/{id}` |
| Products / materials | `/products/{id}` (variants link to parent item) |
| Customers | `/contacts/customers/{id}` |
| Stock transfers | `/stocktransfer/{id}` |
| Stock adjustments | `/stockadjustment/{id}` |

`katana_url` is `None` when the entity id isn't available — typically
create-tool previews (no id assigned until confirm=true). Update-tool
previews already know the id and return a populated `katana_url`.

## Common Workflows

1. **Reorder low stock**: check_inventory → create_purchase_order
2. **Receive delivery**: verify_order_document → receive_purchase_order
3. **Fulfill sales**: search_items → fulfill_order
4. **Create production**: search_items → create_manufacturing_order

Use `katana://help/workflows` for detailed step-by-step guides.

## Reporting & Analytics

Aggregation tools compute rollups in one MCP call instead of paginating
through hundreds of sales orders client-side. All read-only, no `confirm`.

- **top_selling_variants** — top-N variants by units or revenue over a
  date window. Filters: category, location.
- **sales_summary** — group sales by day/week/month, variant, customer,
  or category over a window.
- **inventory_velocity** — units sold (SO), units consumed by completed MOs,
  avg-daily, stock-on-hand, and days-of-cover for one SKU or a batch of SKUs.
  Use ``sku_or_variant_ids`` for cross-variant reports in a single call.
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
   Creates actual PO once invoked with confirm=true.

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
   Updates inventory once invoked with confirm=true.

---

## Workflow 3: Manufacturing Order Fulfillment

**Goal:** Complete a manufacturing order and add finished goods to inventory.

### Steps

1. **Check manufacturing order status**
   Use `get_manufacturing_order` tool with the order_no or order_id.

2. **Verify materials available**
   ```json
   Tool: check_inventory
   Request: {"skus_or_variant_ids": ["WIDGET-001"]}
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
   Request: {"skus_or_variant_ids": ["WIDGET-001"]}
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
   Request: {"skus_or_variant_ids": ["WIDGET-001"]}
   ```
   Returns current stock levels and availability.

---

## Workflow 6: Sales Analytics & Velocity

**Goal:** Answer analytical questions ("top sellers", "sales by month", "how
fast is this SKU moving?") in a single tool call instead of paginating
through hundreds of orders.

### Steps

1. **Find top sellers for a category and period**
   ```json
   Tool: top_selling_variants
   Request: {
     "start_date": "2026-01-22",
     "end_date": "2026-04-22",
     "limit": 20,
     "category": "bikes",
     "order_by": "units"
   }
   ```
   Returns the top 20 SKUs in the `bikes` category by units sold over the
   last 90 days. Substitute `order_by="revenue"` to sort by dollar volume.

2. **Group sales by time or dimension**
   ```json
   Tool: sales_summary
   Request: {
     "start_date": "2026-01-01",
     "end_date": "2026-03-31",
     "group_by": "month"
   }
   ```
   Supports `group_by` of `day`, `week` (ISO weeks), `month`, `variant`,
   `customer`, or `category`.

3. **Check velocity and days-of-cover for a SKU**
   ```json
   Tool: inventory_velocity
   Request: {"sku_or_variant_id": "BIKE-MTB-01", "period_days": 90}
   ```
   Returns `{items: [{sku, variant_id, units_sold, units_consumed_by_mos,
   units_total, avg_daily, stock_on_hand, days_of_cover, ...}]}`. Use
   ``sku_or_variant_ids`` for a batch cross-variant report in one call.
   `days_of_cover` is `null` when average daily demand is 0 (no history).
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
- `format` (optional, default "markdown"): "markdown" | "json" — "json" returns the Pydantic response serialized

**Example:**
```json
{"query": "bolt", "limit": 10}
```

**Returns:** List of matching items with ID, SKU, name, and sellable status.

---

### get_variant_details
Get exhaustive details for one or more item variants. Every field Katana
exposes on the Variant record is surfaced — no follow-up lookups needed
for pricing, barcodes, supplier codes, config attributes, custom fields,
or timestamps (including `deleted_at`).

For multiple variants at once, pass `skus=[...]` or `variant_ids=[...]` —
batching N lookups in one call beats N separate invocations.

**Parameters (at least one of the first four is required):**
- `sku` (optional): Single SKU to look up (exact case-insensitive match)
- `variant_id` (optional): Single variant ID to look up directly
- `skus` (optional): Batch — list of SKUs to look up
- `variant_ids` (optional): Batch — list of variant IDs to look up
- `format` (optional, default "markdown"): "markdown" | "json" — "json" returns the Pydantic response serialized

**Examples:**
```json
{"sku": "BOLT-M8"}
{"variant_id": 12345}
{"skus": ["BOLT-M8", "NUT-M8"]}
{"variant_ids": [12345, 12346]}
```

**Returns:** Full variant details including pricing, barcodes,
`supplier_item_codes` (passed through verbatim from the catalog — entries
that match the variant's own SKU are meaningful and retained, because the
house SKU is often the QBP/vendor SKU for retail pass-throughs),
configuration attributes, custom fields, and lifecycle timestamps. Markdown
labels use the canonical Pydantic field names (e.g.
`**supplier_item_codes**: [SW7083, 10654627]`) with list-shaped fields
rendered in explicit bracket syntax so LLM consumers can't misread a value
as a differently-labeled field. List form returned when a batch is
requested.

---

### check_inventory
Check current stock levels for one or more SKUs or variant IDs — pass a list for a summary table, one item for a detailed card.

**Parameters:**
- `skus_or_variant_ids` (required, min 1): List of SKUs (strings) or variant IDs (integers) — mix freely. Pass one for a stock card, many for a summary table.
- `format` (optional, default "markdown"): "markdown" | "json"

**Examples:**
```json
{"skus_or_variant_ids": ["WIDGET-001"]}
{"skus_or_variant_ids": ["WIDGET-001", "WIDGET-002"]}
{"skus_or_variant_ids": ["WIDGET-001", 12345]}
```

**Returns:** Stock levels (in_stock, available_stock, committed, expected) per variant.

---

### list_low_stock_items
Find items that are below their reorder threshold.

**Parameters:**
- `threshold` (optional): Stock threshold level (default: 10)
- `limit` (optional): Maximum items to return (default: 50)
- `format` (optional, default "markdown"): "markdown" | "json" — "json" returns the Pydantic response serialized

**Returns:** List of items needing reorder with current stock vs threshold.

---

### get_inventory_movements
Get inventory movement history for a SKU — every stock change with dates, causes,
and valuation. Exhaustive: every field on Katana's `InventoryMovement` is surfaced
(identity, variant/location pointers, resource pointers, valuation fields,
timestamps, and rank) so no follow-up lookups are needed for standard fields.

**Parameters:**
- `sku` (required): SKU to get movements for
- `limit` (optional): Maximum movements to return (default: 50)
- `format` (optional, default "markdown"): "markdown" | "json" — "json" returns the Pydantic response serialized

**Returns:** Movement history with `id`, `variant_id`, `location_id`, `resource_type`,
`resource_id`, `caused_by_order_no`, `caused_by_resource_id`, `movement_date`,
`quantity_change`, `balance_after`, `value_per_unit`, `value_in_stock_after`,
`average_cost_after`, `rank`, `created_at`, `updated_at`. Markdown render uses
canonical Pydantic field names as column headers.

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

### list_stock_adjustments
List existing stock adjustments with filters, paging, and optional row detail. All filters
run as indexed SQL against the typed cache, so `variant_id` finds matches regardless of
how many adjustments precede them.

**Parameters:**
- `limit` (optional, default 50, min 1, max 250): Max adjustments to return — also the page size when `page` is set
- `page` (optional, min 1): Page number (1-based); when set, the response includes `pagination` metadata (total_records, total_pages) computed via SQL COUNT against the same filter predicate
- `location_id` (optional): Filter by location
- `ids` (optional): Restrict to a specific set of adjustment IDs
- `stock_adjustment_number` (optional): Exact match on the adjustment number
- `created_after` / `created_before` (optional): ISO-8601 datetime bounds on `created_at`
- `updated_after` / `updated_before` (optional): ISO-8601 datetime bounds on `updated_at` (useful for incremental sync)
- `include_deleted` (optional, default false): Include soft-deleted adjustments
- `variant_id` (optional): Only adjustments whose rows touch this variant — runs as an EXISTS subquery against the indexed FK on the rows table
- `reason` (optional): Case-insensitive substring match on the `reason` field (SQL ILIKE)
- `include_rows` (optional, default false): When true, populate row-level details on each summary
- `format` (optional, default "markdown"): "markdown" | "json" — "json" returns the Pydantic response serialized

**Returns:** Summary rows with `id`, `stock_adjustment_number`, `location_id`, dates,
`reason`, and row count (plus per-row detail when `include_rows=true`), plus optional
`pagination` metadata when `page` is set.

---

### update_stock_adjustment
Update header fields on an existing stock adjustment.

**Parameters:**
- `id` (required): Stock adjustment ID to update
- `stock_adjustment_number` (optional): New number
- `stock_adjustment_date` (optional): New adjustment date (ISO-8601)
- `location_id` (optional): New location
- `reason` (optional): New reason
- `additional_info` (optional): New additional_info
- `confirm` (optional, default false): false = preview, true = apply (prompts)

**Safety:** At least one updatable field is required. Row-level edits are not supported
via this tool — create a new adjustment for that.

**Returns:** Updated adjustment summary plus a summary of the field changes applied.

---

### delete_stock_adjustment
Delete an existing stock adjustment by ID.

**Parameters:**
- `id` (required): Stock adjustment ID
- `confirm` (optional, default false): false = preview, true = delete (prompts)

**Safety:** Deletion reverses the associated inventory movements; the preview returns
the adjustment number, location, and row count so the change is inspectable before
confirming.

---

### list_manufacturing_orders
List manufacturing orders with filters. All filters (including `production_deadline_*`)
run as indexed SQL against the typed cache.

**Paging:**
- `limit` (optional, default 50, min 1, max 250): Max rows to return
- `page` (optional, min 1): Page number (1-based); when set, the response includes
  `pagination` metadata (total_records, total_pages) computed via SQL COUNT against
  the same filter predicate

**Domain filters:**
- `ids` (optional): Explicit list of MO IDs
- `order_no` (optional): Exact order_no
- `status` (optional): NOT_STARTED, IN_PROGRESS, BLOCKED, DONE
- `location_id` (optional): Production location ID
- `is_linked_to_sales_order` (optional): True/False filter on SO linkage
- `include_deleted` (optional): Include soft-deleted MOs

**Time windows** (all run as indexed SQL date-range queries):
- `created_after` / `created_before`: ISO-8601 bounds on `created_at`
- `updated_after` / `updated_before`: ISO-8601 bounds on `updated_at`
- `production_deadline_after` / `production_deadline_before`: bounds on
  `production_deadline_date`

- `format` (optional, default "markdown"): "markdown" | "json" — "json" returns the Pydantic response serialized

**Returns:** Summary rows with id, order_no, status, ingredient_availability,
variant_id, planned/actual qty, location_id, order_created_date,
production_deadline_date, done_date, is_linked_to_sales_order, sales_order_id,
total_cost. The `ingredient_availability` column is the rolled-up MO-level
state (IN_STOCK / NOT_AVAILABLE / EXPECTED / …) — use it to pick which MOs
to drill into without fanning out to `get_manufacturing_order` for each. When
`page` is set, also returns `pagination` with total_records/total_pages/etc.
For per-row recipe detail on a specific MO, call `get_manufacturing_order_recipe`
or `get_manufacturing_order` (which now bundles blocking rows by default).

---

### get_manufacturing_order
Look up a manufacturing order by order number or ID. **Compact-by-default**
for procurement triage: returns the MO header + only blocking recipe rows,
metadata stripped, operation rows and production records omitted.

**Parameters:**
- `order_no` (optional): Order number (e.g., '#WEB20082 / 1')
- `order_id` (optional): Manufacturing order ID
- `format` (optional, default "markdown"): "markdown" | "json"
- `include_rows` (optional, default `"blocking"`): Recipe-row projection.
  - `"blocking"` — only rows with `ingredient_availability` in {NOT_AVAILABLE, EXPECTED}.
  - `"all"` — every recipe row.
  - `"none"` — omit `recipe_rows` entirely; skips the upstream API call.
- `include_operation_rows` (optional, default `false`): When `true`, fetch
  and include the operation-row collection.
- `include_productions` (optional, default `false`): When `true`, fetch and
  include the production-record collection.
- `verbose` (optional, default `false`): When `true`, restore stripped metadata
  (`created_at`/`updated_at`/`deleted_at` on every nested row) and empty
  `batch_transactions: []` placeholders. Use with `include_rows="all"`,
  `include_operation_rows=true`, `include_productions=true` to reproduce the
  legacy exhaustive payload.

**Returns:** Single-object response with every scalar MO field (status,
quantities, costs, timings, linked sales order fields). Recipe rows / operation
rows / production records are populated according to the include flags above.
Markdown labels use canonical Pydantic field names (e.g.
`**production_deadline_date**:`) so downstream consumers can't confuse section
headers with field names.

---

### list_blocking_ingredients
Roll up blocking-ingredient recipe rows across manufacturing orders.
Cache-backed: a single typed-cache join, no per-MO fan-out. Answers
"which SKUs is procurement blocked on, across the active queue?"

**Default scope:** NOT_STARTED + IN_PROGRESS MOs.
**Blocking definition:** recipe rows with `ingredient_availability` in
{NOT_AVAILABLE, EXPECTED}. IN_STOCK / PROCESSED / NOT_APPLICABLE / NO_RECIPE
are excluded by design — they don't represent actionable procurement work.

**Parameters:**
- `mo_status` (optional): MO statuses to scope to (defaults to active).
- `mo_ids` (optional): Restrict to specific MO IDs.
- `mo_order_nos` (optional): Restrict to specific order_no values.
- `location_id` (optional): Restrict to MOs at one production location.
- `production_deadline_after` / `production_deadline_before` (optional):
  ISO-8601 bounds on `production_deadline_date`.
- `group_by` (optional, default `"variant"`):
  - `"variant"` — one row per blocking SKU, sorted by affected_mo_count
    desc, then total_remaining_quantity desc. The procurement-priority view.
  - `"mo"` — one block per MO, sorted by deadline. Preserves per-row detail.
- `limit` (optional, default 100, max 500): Max aggregate rows.
- `format` (optional, default "markdown").

**Returns:** When `group_by="variant"`: rows with variant_id, sku,
affected_mo_count, affected_mo_order_nos (truncated to 5 in markdown),
total_planned_quantity (per-unit times MO planned_quantity, summed),
total_remaining_quantity, earliest_expected_date. When `group_by="mo"`: per-MO
sections with id, order_no, status, deadline, and the blocking recipe rows
nested. Top-level `total_blocking_rows` and `total_affected_mos` are always
populated.

**Cache freshness:** every list/rollup tool re-syncs from Katana via an
incremental `updated_at_min` delta on each invocation, so the rollup reflects
the API state at the moment of the call (including UI-driven edits and
soft-deletes). The cache is a read-shape optimization for filtering/joining,
not a freshness barrier.

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

**get_item** is exhaustive — it surfaces every field Katana exposes on the
polymorphic Product / Material / Service record, plus nested `variants`
(summary), `configs`, and `supplier`. Type-specific fields
(`is_producible` on products, etc.) stay `null` for the other types.
Parameters: `id` (required), `type` (required — "product" | "material" |
"service"), `format` (optional, "markdown" | "json"). For per-variant
detail (barcodes, supplier codes, custom fields), follow up with
`get_variant_details`.

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
- `format` (optional, default "markdown"): "markdown" | "json" — "json" returns the Pydantic response serialized

**Returns:** Match status, discrepancies, suggested actions, and the full
`purchase_order` in the same exhaustive shape as `get_purchase_order` —
so callers can trace every compared value back to a concrete PO field
without a follow-up lookup. Markdown output uses canonical Pydantic field
names as labels (`**matches**`, `**discrepancies**`, `**purchase_order**`)
to keep LLM consumers from misreading a prettified header as a different
field (#346 follow-on).

---

### list_purchase_orders
List purchase orders with filters. All filters run as indexed SQL against the typed
cache. Both `RegularPurchaseOrder` and `OutsourcedPurchaseOrder` live in one cache table
(`purchase_order`) keyed on `entity_type`; the outsourced-only `tracking_location_id`
field is hoisted onto the row so it's queryable across both subtypes.

**Paging:**
- `limit` (optional, default 50, min 1, max 250): Max rows to return
- `page` (optional, min 1): Page number (1-based); when set, the response includes
  `pagination` metadata (total_records, total_pages) computed via SQL COUNT against
  the same filter predicate

**Domain filters:**
- `ids` (optional): Explicit list of PO IDs
- `order_no` (optional): Exact order_no
- `entity_type` (optional): "regular" or "outsourced"
- `status` (optional): DRAFT, NOT_RECEIVED, PARTIALLY_RECEIVED, RECEIVED
- `billing_status` (optional): BILLED, NOT_BILLED, PARTIALLY_BILLED
- `currency` (optional): Currency code (e.g. "USD")
- `location_id` (optional): Receiving location ID
- `tracking_location_id` (optional): Tracking location ID (outsourced POs)
- `supplier_id` (optional): Supplier ID
- `include_deleted` (optional): Include soft-deleted POs

**Time windows** (all run as indexed SQL date-range queries):
- `created_after` / `created_before`: ISO-8601 bounds on `created_at`
- `updated_after` / `updated_before`: ISO-8601 bounds on `updated_at`
- `expected_arrival_after` / `expected_arrival_before`: bounds on `expected_arrival_date`

- `include_rows` (optional, default false): Populate per-PO line item detail
  (variant_id, quantity, price, arrival).
- `format` (optional, default "markdown"): "markdown" | "json" — "json" returns the Pydantic response serialized

**Returns:** Summary rows with id, order_no, status, billing_status,
entity_type, supplier_id, location_id, currency, created_date,
expected_arrival_date, total, row_count. When `page` is set, also returns
`pagination` with total_records/total_pages/etc.

---

### get_purchase_order
Look up a purchase order by order number or ID — exhaustive detail.
For multiple purchase orders at once, use `list_purchase_orders(ids=[...],
include_rows=True)` — it returns a summary table and supports all the
same filters in a single call.

**Parameters:**
- `order_no` (optional): PO number (e.g., "PO-1022")
- `order_id` (optional): PO ID
- `format` (optional, default "markdown"): "markdown" | "json" — "json" returns the Pydantic response serialized

**Returns:** Every field Katana exposes on the PO record — status, billing
status, supplier, location, totals (including `total_in_base_currency`),
timestamps, `last_document_status`, `tracking_location_id`,
`additional_info`, plus:
- `supplier` — the full embedded supplier record when Katana attaches one
  (every field on `Supplier`: name, email, phone, currency, comment,
  default_address_id, addresses, timestamps)
- `purchase_order_rows` — full line items (UOM, conversion rates,
  landed_cost, batch_transactions, every row field)
- `additional_cost_rows` — shipping, duties, handling (every field on
  `PurchaseOrderAdditionalCostRow`)
- `accounting_metadata` — bill IDs, integration type (every field on
  `PurchaseOrderAccountingMetadata`)

Two extra HTTP calls fetch the additional cost rows (by PO
`default_group_id`) and accounting metadata (by PO id) on top of the
PO-detail fetch; they run concurrently via `asyncio.gather` so the extra
wait is a single round-trip, not two. Markdown output uses canonical
Pydantic field names as labels (`**status**`, `**purchase_order_rows** (N):`,
`**additional_cost_rows**: []`) so LLM consumers can't misread a section
header as a different field (#346 follow-on). Use this whenever full
detail is needed; use `list_purchase_orders` for discovery.

---

### update_purchase_order
Update header fields on an existing PO. Status transitions are folded in
here as a regular field — there's no separate `update_purchase_order_status`
tool because Katana's API treats it as a normal PATCH field.

**Parameters:**
- `id` (required): Purchase order ID
- `order_no`, `supplier_id`, `currency`, `location_id`,
  `tracking_location_id`, `expected_arrival_date`, `order_created_date`,
  `additional_info` (optional): Header fields to overwrite
- `status` (optional): DRAFT / NOT_RECEIVED / PARTIALLY_RECEIVED / RECEIVED.
  To flip to RECEIVED with inventory updates use `receive_purchase_order`
  instead.
- `confirm` (optional, default false): false=preview with per-field diff,
  true=apply

**Returns:** A `ModificationResponse` with `is_preview`, the per-field
`changes` list (old/new for every supplied field), `katana_url`, and
`next_actions`.

---

### delete_purchase_order
Delete a purchase order. Destructive — the order record is removed.

**Parameters:**
- `id` (required): Purchase order ID
- `confirm` (optional, default false): false=preview, true=delete

---

### add_purchase_order_row
Add a new line item to an existing PO.

**Parameters:**
- `purchase_order_id` (required): Parent PO ID
- `variant_id`, `quantity`, `price_per_unit` (required): Core line item
- `tax_rate_id`, `tax_name`, `tax_rate`, `currency`, `purchase_uom`,
  `purchase_uom_conversion_rate`, `arrival_date` (optional)
- `confirm` (optional, default false)

---

### update_purchase_order_row
Update fields on an existing PO row. Accepts any subset of `quantity`,
`variant_id`, taxes, `price_per_unit`, UOM fields, `received_date`, and the
row-level `arrival_date` (separate from the PO header's arrival date — Katana
tracks per-row dates so different lines on the same PO can arrive on
different days).

**Parameters:**
- `id` (required): Row ID
- Any subset of: `quantity`, `variant_id`, `tax_rate_id`, `tax_name`,
  `tax_rate`, `price_per_unit`, `purchase_uom`,
  `purchase_uom_conversion_rate`, `received_date`, `arrival_date`
- `confirm` (optional, default false): false=preview with per-field diff,
  true=apply

---

### delete_purchase_order_row
Delete a PO row. Destructive.

**Parameters:**
- `id` (required): Row ID
- `confirm` (optional, default false)

---

### add_purchase_order_additional_cost
Add an additional-cost row (freight, duties, handling fees) to a PO. Katana
models additional-cost rows as members of a *cost group*; the PO carries a
`default_group_id` that the rows attach to. The tool accepts the parent PO
id (familiar) and resolves the group id internally — pass `group_id`
directly only if the PO has multiple groups and you need a non-default one.

**Parameters:**
- `purchase_order_id` *or* `group_id` (one is required): Parent linkage.
  Tool resolves `default_group_id` from the PO when only `purchase_order_id`
  is given.
- `additional_cost_id` (required): Catalog entry ID for the cost type
- `tax_rate_id` (required): Tax rate ID
- `price` (required): Cost amount
- `distribution_method` (optional): BY_VALUE distributes proportionally
  to row value; NON_DISTRIBUTED leaves it unallocated
- `confirm` (optional, default false)

---

### update_purchase_order_additional_cost
Update a PO additional-cost row. Per-field diff against the existing row.

**Parameters:**
- `id` (required): Cost row ID
- Any subset of: `additional_cost_id`, `tax_rate_id`, `price`,
  `distribution_method`
- `confirm` (optional, default false)

---

### delete_purchase_order_additional_cost
Delete a PO additional-cost row. Destructive.

**Parameters:**
- `id` (required): Cost row ID
- `confirm` (optional, default false)

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
- `format` (optional, default "markdown"): "markdown" | "json" — "json" returns the Pydantic response serialized

**Returns:** List of customers with id, name, email, phone, currency.

---

### get_customer
Get full details for a customer by ID.

**Parameters:**
- `customer_id` (required): Customer ID
- `format` (optional, default "markdown"): "markdown" | "json" — "json" returns the Pydantic response serialized

**Returns:** Full customer details (name, email, phone, currency, category, comment).

---

### get_manufacturing_order_recipe
List the ingredient (recipe) rows for a manufacturing order with exhaustive detail.
For recipe rows across multiple MOs, call `get_manufacturing_order` once per MO —
it returns recipe rows inline (there is no batch shape for this tool).

**Parameters:**
- `manufacturing_order_id` (required): MO ID
- `format` (optional, default "markdown"): "markdown" | "json" — "json" returns the Pydantic response serialized

**Returns:** Every field Katana exposes on each `ManufacturingOrderRecipeRow`
(notes, planned/actual/consumed/remaining quantities, ingredient availability
and expected date, batch transactions, cost, timestamps) plus the resolved
SKU. Markdown labels use canonical Pydantic field names.

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
List sales orders with filters. All filters run as indexed SQL against the typed cache.

**Paging:**
- `limit` (optional, default 50, min 1, max 250): Max rows to return. When
  `page` is set, acts as the page size.
- `page` (optional, min 1): Page number (1-based); when set, the response includes
  `pagination` metadata (total_records, total_pages) computed via SQL COUNT against
  the same filter predicate.

**Domain filters:**
- `order_no` (optional): Exact order number
- `ids` (optional): Explicit list of sales order IDs
- `customer_id` (optional): Filter to a customer
- `location_id` (optional): Filter to a location
- `status` (optional): Order status (e.g., "NOT_SHIPPED", "DELIVERED")
- `production_status` (optional): Production status
- `invoicing_status` (optional): e.g. "NOT_INVOICED", "INVOICED"
- `currency` (optional): Currency code (e.g. "USD")
- `include_deleted` (optional): When true, include soft-deleted SOs
- `needs_work_orders` (optional): Shortcut for `production_status="NONE"` —
  finds sales orders that haven't had manufacturing orders created yet

**Time windows** (all run as indexed SQL date-range queries):
- `created_after` / `created_before`: ISO-8601 bounds on `created_at`
- `updated_after` / `updated_before`: ISO-8601 bounds on `updated_at`
- `delivered_after` / `delivered_before`: ISO-8601 bounds on `delivery_date`

**Row detail:**
- `include_rows` (optional, default false): When true, populate per-order row
  details (id, variant_id, quantity, price_per_unit,
  linked_manufacturing_order_id) on each summary. `sku` is left None in list
  context — use `get_sales_order` for SKU-enriched rows on a specific order.

**Other:**
- `format` (optional, default "markdown"): "markdown" | "json" — "json" returns the Pydantic response serialized

**Returns:** Summary rows with order_no, status, production_status, row_count,
total, currency, created_at, delivery_date. When `page` is set, the response
also includes `pagination` with `total_records`, `total_pages`, current
`page`, `first_page`, and `last_page`. When `include_rows=true`, each summary
also carries a `rows` list.

---

### get_sales_order
Look up a single sales order by order number or ID with exhaustive detail.
For multiple sales orders at once, use `list_sales_orders(ids=[...],
include_rows=True)` — it returns a summary table and supports all the
same filters in a single call.

**Parameters:**
- `order_no` (optional): SO number (e.g., "#WEB20394")
- `order_id` (optional): SO ID
- `format` (optional, default "markdown"): "markdown" | "json" — "json" returns the Pydantic response serialized

**Returns:** Every field Katana exposes on the sales order record —
identifiers (id, order_no, customer_id, location_id, source), status flags
(status, production_status, invoicing_status, product_availability,
ingredient_availability), dates (order_created_date, delivery_date,
picked_date, product_expected_date, ingredient_expected_date), money (total,
total_in_base_currency, currency, conversion_rate, conversion_date), notes
(additional_info, customer_ref), tracking (tracking_number,
tracking_number_url), address pointers (billing_address_id,
shipping_address_id) plus the full resolved `addresses` list fetched from
/sales_order_addresses, `shipping_fee` block, `linked_manufacturing_order_id`,
ecommerce metadata (ecommerce_order_type/store_name/order_id), timestamps
(created_at, updated_at, deleted_at), and per-line `rows` with every
`SalesOrderRow` field (variant_id, SKU via variant cache, quantity, pricing,
discounts, tax, cogs, linked MO, batch/serial tracking, timestamps).

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

---

## Stock Transfer Tools

### create_stock_transfer
Create a stock transfer moving inventory between two locations.

**Parameters:**
- `source_location_id` (required): Source location ID
- `destination_location_id` (required): Destination location ID (target_location_id)
- `expected_arrival_date` (required): Expected arrival datetime (ISO-8601)
- `rows` (required): Line items `[{variant_id, quantity, batch_transactions?}]` —
  `batch_transactions` is `[{batch_id, quantity}]` for batch-tracked variants
- `order_no` (optional): Stock transfer number. When omitted, the tool generates a `ST-<unix-ts>` default before sending — Katana's API requires the field.
- `additional_info` (optional): Notes
- `confirm` (optional, default false): false=preview, true=create

**Safety:** When confirm=true, prompts user for confirmation before creating.

---

### list_stock_transfers
List stock transfers with filters. All filters (including `status`) run as indexed
SQL against the typed cache.

**Parameters:**
- `limit` (optional, default 50, min 1): Max rows to return
- `page` (optional): Page number (1-based); when set, the response includes
  `pagination` metadata (total_records, total_pages) computed via SQL COUNT
  against the same filter predicate
- `status` (optional): "DRAFT", "IN_TRANSIT", or "RECEIVED" (mapped to the
  Katana wire values "draft" / "inTransit" / "received" against the cache
  column)
- `source_location_id` (optional): Filter by source location ID
- `destination_location_id` (optional): Filter by destination (target) location ID
- `stock_transfer_number` (optional): Exact match on the transfer number
- `created_after` / `created_before` (optional): ISO-8601 datetime bounds on
  created_at — indexed SQL range filter
- `include_rows` (optional, default false): Populate per-transfer row details
- `format` (optional, default "markdown"): "markdown" | "json" — "json" returns the Pydantic response serialized

**Returns:** Summary rows (id, number, status, source/destination, row_count,
expected_arrival). `pagination` metadata is populated when `page` is set.

---

### update_stock_transfer
Update body fields on an existing stock transfer.

**Parameters:**
- `id` (required): Stock transfer ID
- `stock_transfer_number` (optional): New transfer number
- `transfer_date` (optional): New transfer datetime (ISO-8601)
- `expected_arrival_date` (optional): New expected arrival datetime (ISO-8601)
- `additional_info` (optional): Updated notes
- `confirm` (optional, default false): false=preview, true=apply

At least one updatable field must be provided. Use `update_stock_transfer_status`
to change the transfer's status — it's a separate endpoint.

---

### update_stock_transfer_status
Transition a stock transfer through the 3-state machine.

**Parameters:**
- `id` (required): Stock transfer ID
- `new_status` (required): "DRAFT", "IN_TRANSIT", or "RECEIVED" (mapped to
  the Katana wire values "draft" / "inTransit" / "received")
- `confirm` (optional, default false): false=preview, true=apply

**Typical flow:** DRAFT → IN_TRANSIT → RECEIVED. Katana rejects invalid
transitions (e.g. RECEIVED → IN_TRANSIT); the tool surfaces the API error
message as a ValueError.

---

### delete_stock_transfer
Delete a stock transfer.

**Parameters:**
- `id` (required): Stock transfer ID
- `confirm` (optional, default false): false=preview, true=delete

Destructive — removes the transfer record.

---

## Reporting & Analytics Tools

### top_selling_variants
Top-selling variants over a date window (single call; auto-paginates and
aggregates DELIVERED sales orders in memory).

**Parameters:**
- `start_date` (required): ISO-8601 date — window start (inclusive)
- `end_date` (required): ISO-8601 date — window end (inclusive)
- `limit` (optional, default 20, min 1): Max rows to return
- `category` (optional): Item category name to filter by (e.g. "bikes")
- `order_by` (optional, default "units"): "units" or "revenue"
- `location_id` (optional): Filter to a single location
- `format` (optional, default "markdown"): "markdown" | "json" — "json" returns the Pydantic response serialized

**Returns:** List of `{sku, variant_id, name, units, revenue, order_count}`
sorted by the `order_by` key descending.

---

### sales_summary
Grouped sales totals for DELIVERED orders in a window.

**Parameters:**
- `start_date` (required): ISO-8601 date — window start (inclusive)
- `end_date` (required): ISO-8601 date — window end (inclusive)
- `group_by` (required): one of `day`, `week`, `month`, `variant`,
  `customer`, `category`
- `format` (optional, default "markdown"): "markdown" | "json" — "json" returns the Pydantic response serialized

**Returns:** List of `{group, units, revenue, order_count}`. Time groups
(`day`/`week`/`month`) sort ascending; dimension groups sort by revenue
descending.

---

### inventory_velocity
Velocity stats and days-of-cover for one or more SKUs/variants. Includes both
sales-order demand and manufacturing-order ingredient consumption. Use
``sku_or_variant_ids`` for cross-variant batch reports in a single call.

**Parameters:**
- `sku_or_variant_id` (required for single): SKU (string) or variant_id (int)
- `sku_or_variant_ids` (required for batch): list of SKUs and/or variant IDs
  (max 100). Exactly one of `sku_or_variant_id` or `sku_or_variant_ids` must
  be provided.
- `period_days` (optional, default 90, max 365): Rolling window size
- `include_mo_consumption` (optional, default true): Include units consumed as
  ingredients on completed MOs. Set false for SO-only numbers (legacy behavior).
- `format` (optional, default "markdown"): "markdown" | "json" — "json" returns the Pydantic response serialized

**Returns:** `{items: [{sku, variant_id, units_sold, units_consumed_by_mos,
units_total, avg_daily, stock_on_hand, days_of_cover, period_days,
window_start, window_end}]}`. `days_of_cover` is `null` when `avg_daily` is 0
(no demand in window). Single-item calls return a rich card; batch calls return
a markdown table.
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
