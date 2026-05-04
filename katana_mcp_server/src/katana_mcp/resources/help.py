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
- **get_item** / **modify_item** / **delete_item** - Full CRUD on items (products / materials / services). `modify_item` carries header + variant CRUD in one call via typed sub-payload slots.
- **get_variant_details** - Get full details for a specific item
- **check_inventory** - Check stock levels for one or more SKUs or variant IDs (pass a list for a summary table)
- **list_low_stock_items** - Find items needing reorder
- **create_stock_adjustment / list_stock_adjustments / update_stock_adjustment / delete_stock_adjustment** - Full CRUD for manual inventory adjustments

### Purchase Orders
- **create_purchase_order** - Create PO with preview/apply pattern
- **list_purchase_orders** - List POs with supplier/status/date filters
- **receive_purchase_order** - Receive items and update inventory
- **verify_order_document** - Verify supplier documents against POs (returns the full PO alongside match/discrepancy details)
- **get_purchase_order** - Look up a PO by number or ID — exhaustive detail (every PO/row field, additional cost rows, accounting metadata)
- **modify_purchase_order** - Unified modify: header, rows, additional-cost rows in one call (typed sub-payload slots, multi-action, preview/apply)
- **delete_purchase_order** - Delete a PO (Katana cascades child rows)

### Manufacturing & Sales
- **create_manufacturing_order** - Create production work orders
- **list_manufacturing_orders** - List MOs with status/location/date filters
- **get_manufacturing_order** - Look up an MO with full details
- **modify_manufacturing_order** - Unified modify: header, recipe rows, operation rows, production records (multi-action, preview/apply)
- **delete_manufacturing_order** - Delete an MO (Katana cascades child rows)
- **fulfill_order** - Complete manufacturing or sales orders
- **create_sales_order** - Create sales orders with preview/apply
- **list_sales_orders** - List SOs with customer/status/date filters
- **get_sales_order** - Look up an SO with full details
- **modify_sales_order** - Unified modify: header, rows, addresses, fulfillments, shipping fees (multi-action, preview/apply)
- **delete_sales_order** - Delete an SO (Katana cascades child rows)

### Stock Transfers
- **create_stock_transfer** - Move inventory between locations (preview/apply)
- **list_stock_transfers** - List transfers with status / location / date filters
- **modify_stock_transfer** - Unified modify: header body fields and/or status transition in one call (preview/apply). Hides Katana's two-endpoint split.
- **delete_stock_transfer** - Delete a transfer

### Cache Administration
- **rebuild_cache** - Force-rebuild the local typed cache for one or more transactional entity types (PO, SO, MO, stock adjustment, stock transfer). Truncates the cache table(s), clears the sync watermark, and re-fetches from Katana. Use when the cache has phantom rows (entities present locally but missing from Katana). Destructive; preview/apply.

## Safety Pattern

All create/modify operations use a **two-step preview/apply pattern**:
1. Call with `preview=true` (default) to preview (no changes made)
2. Call with `preview=false` to execute

Destructive tools advertise this via the standard MCP `destructiveHint`
tool annotation; hosts that respect the annotation prompt the user before
invoking. The server does not gate further.

## Unified-Modify Pattern

Five entities (PO, SO, MO, stock transfer, item) expose a unified
`modify_<entity>` tool that lets you do header / row / sub-resource CRUD
in a single call via typed sub-payload slots. Every modify tool follows
the same shape:

- **Typed sub-payload slots** — one optional field per kind of action
  the entity supports (e.g. `update_header`, `add_rows`, `update_rows`,
  `delete_row_ids`). Set any subset; combinations are valid.
- **Multi-action apply** — actions execute in canonical order
  (header → adds → updates → deletes → status). The Katana API is not
  transactional across endpoints; the dispatcher fail-fasts on the
  first error, leaving earlier successful actions applied.
- **Prior-state snapshot** — on an applied call, the response carries
  a `prior_state` snapshot of the pre-modification entity (best-effort:
  `prior_state` is `null` when the entity has no GET-by-id endpoint,
  e.g. stock transfer, or the diff-context fetch failed). Callers can
  compose a follow-up modify call to manually revert if needed. We
  don't auto-revert via inverse calls — those have their own failure
  modes; visible partial application beats silent inconsistency.
- **Post-action verification** — for actions where the API returns the
  mutated entity, the dispatcher confirms the requested fields match
  the response. Verification failures surface as
  `verified=False` with `actual_after` snapshot — they don't raise.

Destructive `delete_<entity>` tools are siblings of the modify tools —
keeping them separate makes the destructiveHint annotation honest.

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
URLs by hand — Katana's path conventions have one nested + plural
exception (`/contacts/customers/{id}`) on top of an otherwise-uniform
singular-noun pattern, and getting it wrong fails silently.

Patterns (base: `factory.katanamrp.com`, override via `KATANA_WEB_BASE_URL`):

| Entity | Path |
|--------|------|
| Sales orders | `/salesorder/{id}` |
| Manufacturing orders | `/manufacturingorder/{id}` |
| Purchase orders | `/purchaseorder/{id}` |
| Products | `/product/{id}` (variants link to parent item) |
| Materials | `/material/{id}` (variants link to parent item) |
| Customers | `/contacts/customers/{id}` |
| Stock transfers | `/stocktransfer/{id}` |
| Stock adjustments | `/stockadjustment/{id}` |

`katana_url` is `None` when the entity id isn't available — typically
create-tool previews (no id assigned until preview=false). Update-tool
previews already know the id and return a populated `katana_url`.

## Common Workflows

1. **Reorder low stock**: check_inventory → create_purchase_order
2. **Receive delivery**: verify_order_document → receive_purchase_order
3. **Fulfill sales**: search_items → fulfill_order
4. **Create production**: search_items → create_manufacturing_order

Use `katana://help/workflows` for detailed step-by-step guides.

## Reporting & Analytics

Aggregation tools compute rollups in one MCP call instead of paginating
through hundreds of sales orders client-side. All read-only, no `preview` flag.

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
     "preview": true
   }
   ```
   Returns preview with total cost - no order created yet.

4. **Confirm and create order**
   ```json
   Tool: create_purchase_order
   Request: {...same as above..., "preview": false}
   ```
   Creates actual PO once invoked with preview=false.

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
     "preview": true
   }
   ```
   Shows what will be received.

3. **Confirm receipt**
   ```json
   Tool: receive_purchase_order
   Request: {...same as above..., "preview": false}
   ```
   Updates inventory once invoked with preview=false.

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
     "preview": false
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
     "preview": false
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
- `preview` (optional, default true): Set true to preview, false to create

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
- `preview` (optional, default true): true = preview, false = apply (prompts)

**Safety:** At least one updatable field is required. Row-level edits are not supported
via this tool — create a new adjustment for that.

**Returns:** Updated adjustment summary plus a summary of the field changes applied.

---

### delete_stock_adjustment
Delete an existing stock adjustment by ID.

**Parameters:**
- `id` (required): Stock adjustment ID
- `preview` (optional, default true): true = preview, false = delete (prompts)

**Safety:** Deletion reverses the associated inventory movements; the preview returns
the adjustment number, location, and row count so the change is inspectable before
applying.

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
- `status` (optional): NOT_STARTED, BLOCKED, IN_PROGRESS, PARTIALLY_COMPLETED, DONE
- `location_id` (optional): Production location ID
- `variant_ids` (optional): List of variant IDs — MOs producing any of these
  variants. Resolve a SKU to its `variant_id` via `search_items` or
  `get_variant_details` first.
- `sales_order_ids` (optional): List of sales order IDs — MOs linked to any
  of these SOs (more precise than `is_linked_to_sales_order=true` when you
  already know the SO IDs)
- `ingredient_availability` (optional): PROCESSED, IN_STOCK, NOT_AVAILABLE,
  EXPECTED, NO_RECIPE, NOT_APPLICABLE — use NOT_AVAILABLE / EXPECTED to find
  MOs blocked on materials
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

### get_item
Look up an item by ID and type — exhaustive detail across the
polymorphic Product / Material / Service record, plus nested `variants`
(summary), `configs`, and `supplier`. Type-specific fields
(`is_producible` on products, etc.) stay `null` for the other types.

**Parameters:**
- `id` (required): Item ID
- `type` (required): "product" | "material" | "service"
- `format` (optional, default "markdown"): "markdown" | "json"

For per-variant detail (barcodes, supplier codes, custom fields), follow
up with `get_variant_details`.

---

### modify_item
Unified modification surface for an item — header + variant CRUD in one
call. The required `type` discriminator routes header updates to the
matching `/products/{id}` / `/materials/{id}` / `/services/{id}`
endpoint; variant sub-payloads route to the shared `/variant` family.

**Sub-payloads (all optional, any subset combinable):**
- `update_header` — patch header fields. Field set is type-specific:
  `is_producible` / `is_purchasable` / `is_auto_assembly` /
  `serial_tracked` / `operations_in_sequence` are PRODUCT-only;
  `default_supplier_id` / `batch_tracked` / `purchase_uom` /
  `purchase_uom_conversion_rate` are PRODUCT/MATERIAL only;
  `sales_price` / `default_cost` / `sku` are SERVICE-only. Misrouted
  fields fail fast with a clear error.
- `add_variants` — POST `/variant`. Parent `product_id` / `material_id`
  is injected automatically from the request's `type`. Not supported
  for SERVICE (services carry pricing on the header, not on variants).
- `update_variants` / `delete_variant_ids` — variant CRUD. Not supported
  for SERVICE.

**Parameters:**
- `id` (required): Item ID
- `type` (required): "product" | "material" | "service"
- Any subset of the sub-payloads above
- `preview` (optional, default true): true=preview, false=execute

---

### delete_item
Delete an item. Destructive — Katana cascades child variants server-side.

**Parameters:**
- `id` (required): Item ID
- `type` (required): "product" | "material" | "service"
- `preview` (optional, default true): true=preview, false=delete

---

## Purchase Order Tools

### create_purchase_order
Create a purchase order with preview/apply pattern.

**Parameters:**
- `supplier_id` (required): Supplier ID
- `location_id` (required): Warehouse location for receipt
- `order_number` (required): PO number (e.g., "PO-2025-001")
- `items` (required): Array of line items with variant_id, quantity, price_per_unit
- `preview` (optional, default true): true=preview, false=create

**Safety:** When preview=false, prompts user for confirmation before creating.

---

### receive_purchase_order
Receive items from a purchase order.

**Parameters:**
- `order_id` (required): Purchase order ID
- `items` (required): Array of items with purchase_order_row_id and quantity
- `preview` (optional, default true): true=preview, false=receive

**Safety:** When preview=false, prompts user for confirmation.

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

### modify_purchase_order
Unified modification surface for a PO — header, line rows, and
additional-cost rows in one call. Replaces the prior 8 separate
`update_purchase_order` / `add_purchase_order_row` etc. tools.

**Sub-payloads (all optional, any subset combinable):**
- `update_header` — patch header fields (`order_no`, `supplier_id`,
  `currency`, `location_id`, `tracking_location_id`,
  `expected_arrival_date`, `order_created_date`, `additional_info`,
  `status`). Status uses the PATCH endpoint; to flip to RECEIVED with
  inventory updates use `receive_purchase_order` instead.
- `add_rows` — list of new line items. Each row:
  `variant_id` (int, required), `quantity` (float, required, >0),
  `price_per_unit` (float, required), `tax_rate_id` (int — see
  `katana://tax-rates`), `tax_name`, `tax_rate`, `currency`,
  `purchase_uom`, `purchase_uom_conversion_rate`, `arrival_date`.
- `update_rows` — list of patches. Each entry: `id` (int, required) +
  any subset of `quantity`, `variant_id`, `tax_rate_id`, `tax_name`,
  `tax_rate`, `price_per_unit`, `purchase_uom`,
  `purchase_uom_conversion_rate`, `received_date`, `arrival_date`.
- `delete_row_ids` — list of row IDs to delete.
- `add_additional_costs` — list of new freight / duty / handling rows.
  Each row: `additional_cost_id` (int, required — see
  `katana://additional-costs` for catalog IDs), `tax_rate_id` (int,
  required — see `katana://tax-rates`), `price` (float, required),
  `distribution_method` (`BY_VALUE` | `NON_DISTRIBUTED` — controls how
  the cost spreads across line items; `BY_VALUE` is what produces
  `landed_cost` on each row), `group_id` (int, optional — defaults to
  the PO's `default_group_id`).
- `update_additional_costs` — list of patches to existing cost rows.
  Each entry: `id` (int, required) + any subset of `additional_cost_id`,
  `tax_rate_id`, `price`, `distribution_method`.
- `delete_additional_cost_ids` — list of cost row IDs to delete.

**Derived fields (rejected on update):** `landed_cost`,
`total_in_base_currency`, `total`, `conversion_rate`, and
`conversion_date` on PO rows are computed by Katana from supplier price,
exchange rates, and distributed additional costs. Trying to set them via
`update_rows` returns "At least 1 field is required" because every other
patched field is also derived. To distribute landed cost across rows,
use `add_additional_costs` with `distribution_method=BY_VALUE` — Katana
recomputes per-row `landed_cost` automatically.

**Parameters:**
- `id` (required): Purchase order ID
- Any subset of the sub-payloads above
- `preview` (optional, default true): true=preview with per-action diff,
  false=execute the action plan in canonical order (header → row adds →
  row updates → row deletes → cost adds → cost updates → cost deletes);
  fail-fast on first error

**Returns:** A `ModificationResponse` with `is_preview`, an `actions` list
(one entry per planned API call with `operation`, `target_id`, `changes`,
`succeeded`, `verified`, `actual_after`), `prior_state` snapshot, and
`katana_url`.

---

### delete_purchase_order
Delete a purchase order. Destructive — Katana cascades child rows server-side.

**Parameters:**
- `id` (required): Purchase order ID
- `preview` (optional, default true): true=preview, false=delete

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
- `preview` (optional, default true): true=preview, false=create

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

### modify_manufacturing_order
Unified modification surface for an MO — header, recipe rows
(ingredients), operation rows (production steps), and production records
(completion logs) in one call. Replaces the prior recipe-row CRUD tools.

**Sub-payloads (all optional, any subset combinable):**
- `update_header` — patch header fields (`order_no`, `variant_id`,
  `location_id`, `status`, `planned_quantity`, `actual_quantity`, dates,
  `additional_info`). Status uses the PATCH endpoint
  (NOT_STARTED / IN_PROGRESS / DONE / BLOCKED / PARTIALLY_COMPLETED).
- `add_recipe_rows` / `update_recipe_rows` / `delete_recipe_row_ids` —
  ingredient CRUD. Each `add_recipe_rows` entry carries `variant_id` +
  `planned_quantity_per_unit` + optional notes.
- `add_operation_rows` / `update_operation_rows` /
  `delete_operation_row_ids` — production step CRUD. Operation rows
  carry status (NOT_STARTED / IN_PROGRESS / PAUSED / BLOCKED /
  COMPLETED) and type (fixed / perUnit / process / setup).
- `add_productions` / `update_productions` / `delete_production_ids` —
  completion-log entries.

**Parameters:**
- `id` (required): Manufacturing order ID
- Any subset of the sub-payloads above
- `preview` (optional, default true): true=preview, false=execute the
  action plan in canonical order; fail-fast on first error

**Returns:** A `ModificationResponse` carrying per-action results and a
`prior_state` snapshot. To swap a variant across many MOs at once, run
multiple `modify_manufacturing_order` calls — there is no batch shape
in the unified surface.

---

### delete_manufacturing_order
Delete a manufacturing order. Destructive — Katana cascades child recipe
rows / operation rows / production records server-side.

**Parameters:**
- `id` (required): Manufacturing order ID
- `preview` (optional, default true): true=preview, false=delete

---

### create_sales_order
Create a sales order.

**Parameters:**
- `customer_id` (required): Customer ID (use `search_customers` to find)
- `order_number` (required): Unique sales order number
- `items` (required): Array of items with variant_id, quantity, and optional price_per_unit
- `preview` (optional, default true): true=preview, false=create

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

### modify_sales_order
Unified modification surface for an SO — header, rows, addresses,
fulfillments, and shipping fees in one call.

**Sub-payloads (all optional, any subset combinable):**
- `update_header` — patch header fields (incl. status:
  NOT_SHIPPED / PENDING / PACKED / DELIVERED).
- `add_rows` / `update_rows` / `delete_row_ids` — line item CRUD.
- `add_addresses` / `update_addresses` / `delete_address_ids` — billing
  / shipping addresses. Note: Katana doesn't expose a per-address GET,
  so address-update previews show every supplied field as
  `(prior unknown) → new`.
- `add_fulfillments` / `update_fulfillments` /
  `delete_fulfillment_ids` — fulfillments (each carries its own status
  + tracking).
- `add_shipping_fees` / `update_shipping_fees` /
  `delete_shipping_fee_ids` — shipping/freight charges.

**Parameters:**
- `id` (required): Sales order ID
- Any subset of the sub-payloads above
- `preview` (optional, default true): true=preview, false=execute

---

### delete_sales_order
Delete a sales order. Destructive — Katana cascades child rows /
addresses / fulfillments / shipping fees server-side.

**Parameters:**
- `id` (required): Sales order ID
- `preview` (optional, default true): true=preview, false=delete

---

### create_product / create_material
Dedicated catalog tools for creating products or materials with a single variant.

---

### fulfill_order
Complete a manufacturing or sales order.

**Parameters:**
- `order_id` (required): Order ID to fulfill
- `order_type` (required): "manufacturing" or "sales"
- `preview` (optional, default true): true=preview, false=fulfill

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
- `preview` (optional, default true): true=preview, false=create

**Safety:** When preview=false, prompts user for confirmation before creating.

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

### modify_stock_transfer
Unified modification surface for a stock transfer — header body fields
and/or status transition in one call. Hides the fact that Katana exposes
these as two separate PATCH endpoints
(`/stock_transfers/{id}` and `/stock_transfers/{id}/status`).

**Sub-payloads (all optional, any subset combinable):**
- `update_header` — patch body fields (`stock_transfer_number`,
  `transfer_date`, `expected_arrival_date`, `additional_info`).
- `update_status` — `new_status: "DRAFT" | "IN_TRANSIT" | "RECEIVED"`
  (mapped to the Katana wire values `draft` / `inTransit` / `received`).
  Typical flow: DRAFT → IN_TRANSIT → RECEIVED. Katana rejects invalid
  transitions (e.g. RECEIVED → IN_TRANSIT); the action's error surfaces
  in the response.

**Parameters:**
- `id` (required): Stock transfer ID
- Any subset of the sub-payloads above
- `preview` (optional, default true): true=preview, false=execute the
  action plan in canonical order (header first, then status); fail-fast
  on first error

Stock-transfer rows are immutable post-creation — Katana doesn't expose
row-CRUD endpoints. Note: Katana doesn't expose a GET-by-id endpoint for
stock transfers either, so previews show every supplied field as
`(prior unknown) → new`.

---

### delete_stock_transfer
Delete a stock transfer. Destructive — the transfer record is removed.

**Parameters:**
- `id` (required): Stock transfer ID
- `preview` (optional, default true): true=preview, false=delete

---

## Cache Administration Tools

### rebuild_cache
Force-rebuild the local typed cache for one or more transactional entity types.
The steady-state sync path upserts via `session.merge` and never deletes — soft-
deletes from Katana are folded in correctly because the tombstone surfaces in
the next `updated_at_min` delta, but rows that left Katana without a tombstone
in our watermarked window (hard deletes, partial syncs, state predating cache
initialization) persist locally as phantoms. Rebuild is the manual escape hatch.

For each requested entity type, the rebuild:
1. Acquires the per-entity sync locks (parent + every related spec).
2. Deletes every row in the cache table(s).
3. Deletes the matching `sync_state` watermark row(s).
4. Re-fetches everything from Katana under the still-held locks. Concurrent
   `list_*` calls block on the same locks until the re-pull completes and
   never observe the empty intermediate state.

**Parameters:**
- `entity_types` (required, min length 1): list of entity types to rebuild.
  Allowed values: `purchase_order`, `sales_order`, `manufacturing_order`,
  `stock_adjustment`, `stock_transfer`.
- `preview` (optional, default true): true = report current row counts and
  last-synced timestamps without modifying anything; false = perform the
  destructive rebuild.
- `format` (optional, default "markdown"): "markdown" | "json".

**Returns:** `RebuildCacheResponse` with `is_preview` and a `results` list
carrying per-entity `parent_rows_before/after`, `child_rows_before/after`,
`last_synced_before` (ISO-8601 or `null` if never synced), and the list of
`sync_state_keys_cleared` (empty list in preview mode).

**Caveats:**
- Destructive: cache rows are gone between truncate and re-pull, but
  concurrent `list_*` calls block on the sync lock until the re-pull
  completes — they observe the rebuilt cache, not the empty intermediate.
- Not transactional across entity types: each entity is rebuilt sequentially.
  If the resync for entity B fails after entity A succeeded, A is
  already rebuilt.
- Bandwidth cost equals one full cold-start sync per entity type
  (paginated via the auto-pagination transport).

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

### katana://additional-costs
Configured additional-cost catalog (freight, duties, handling fees) for
purchase orders.

**Contains:**
- id, name
- Summary count

**Use when:** Looking up `additional_cost_id` for
`modify_purchase_order(add_additional_costs=[...])`. Pair with
`katana://tax-rates` for the matching `tax_rate_id`.

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
