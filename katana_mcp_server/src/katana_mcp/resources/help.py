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
- **get_product_bom** / **manage_product_bom** - Read and edit a producible variant's BOM (Bill of Materials) — the master recipe future manufacturing orders are copied from. `manage_product_bom` supports add / update / delete BOM rows in one call (preview/apply). Distinct from `modify_manufacturing_order`'s recipe-row sub-payloads, which edit a single MO's snapshot.
- **check_inventory** - Check stock levels for one or more SKUs or variant IDs (pass a list for a summary table)
- **inventory_at** - Reconstruct historical balance: walks `inventory_movements` and returns per-location stock, value, and average cost as of an ISO-8601 `as_of` instant. Use for audit / point-in-time reconstruction; use `check_inventory` for current state.
- **get_inventory_movements** - Stream of every stock change with dates, causes, and valuation. Filterable by location, resource type, and `created_at`/`updated_at` windows.
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
- **correct_purchase_order** - Edit a closed (RECEIVED / PARTIALLY_RECEIVED) PO without losing its per-row `received_date` / batch-transaction metadata. Reverts to NOT_RECEIVED, edits rows keyed by row ID, then replays the original receipts via `/purchase_order_receive` to restore close-state. See "Closed-Record Corrections" below.

### Manufacturing & Sales
- **create_manufacturing_order** - Create production work orders
- **list_manufacturing_orders** - List MOs with status/location/date filters
- **get_manufacturing_order** - Look up an MO with full details
- **modify_manufacturing_order** - Unified modify: header, recipe rows, operation rows, production records (multi-action, preview/apply)
- **delete_manufacturing_order** - Delete an MO (Katana cascades child rows)
- **correct_manufacturing_order** - Edit a closed (DONE / PARTIALLY_COMPLETED) MO without losing its `done_date` / per-production timestamps. Reopens, swaps ingredients keyed by current variant, then re-closes preserving close-state. See "Closed-Record Corrections" below.
- **fulfill_order** - Complete manufacturing or sales orders
- **create_sales_order** - Create sales orders with preview/apply
- **list_sales_orders** - List SOs with customer/status/date filters
- **get_sales_order** - Look up an SO with full details
- **modify_sales_order** - Unified modify: header, rows, addresses, fulfillments, shipping fees (multi-action, preview/apply)
- **delete_sales_order** - Delete an SO (Katana cascades child rows)
- **correct_sales_order** - Edit a closed (DELIVERED) SO without losing its `picked_date` / fulfillment metadata. Reopens, edits lines keyed by current variant, then re-closes preserving close-state. See "Closed-Record Corrections" below.

### Stock Transfers
- **create_stock_transfer** - Move inventory between locations (preview/apply)
- **list_stock_transfers** - List transfers with status / location / date filters
- **modify_stock_transfer** - Unified modify: header body fields and/or status transition in one call (preview/apply). Hides Katana's two-endpoint split.
- **delete_stock_transfer** - Delete a transfer

### Bin Transfers & Storage Bins
- **create_bin_transfer** - Move inventory between bins within one location (preview/apply). Rows carry source/target bin + batch/serial traceability.
- **list_bin_transfers** - List bin transfers with status (CREATED/IN_TRANSIT/DONE) / location / date filters; `include_rows` for line items
- **modify_bin_transfer** - Unified modify: header fields, row CRUD (add/update/delete — rows are mutable, unlike stock transfers), and/or status transition (preview/apply)
- **delete_bin_transfer** - Delete a bin transfer
- **list_bin_inventory** - Per-bin stock levels at VARIANT / BATCH / SERIAL_NUMBER granularity (live read). `bin_location_id='null'` finds unassigned stock.
- **list_storage_bins** - List the named bins within each location. Use for bin ID lookups.
- **create_storage_bin** - Create a storage bin in a location (preview/apply)

### Serial Numbers
- **add_serial_numbers** - Attach serial numbers to a resource. Mint new ones (ManufacturingOrder, PurchaseOrderRow) or transfer existing strings between resources (SalesOrderRow, StockTransferRow, StockAdjustmentRow). Partial-failure capable. (preview/apply)
- **list_serial_numbers** - List serial numbers, optionally scoped by `resource_type` and/or `resource_id`. Diagnostic / lookup tool — use to verify which strings are attached to an MO before fulfillment.
- **delete_serial_numbers** - Detach serial numbers from a resource. Idempotent (Katana returns 204 even for invalid ids). (preview/apply, destructive)

### Customers
- **search_customers** - Fuzzy-search customers by name / email. Use for `customer_id` lookups on sales orders.
- **get_customer** - Full-detail customer record by id (contact fields, currency, default discount, addresses).
- **create_customer** - Create a new customer (preview/apply). Use for non-Shopify channels (eBay, Amazon, etc.) where buyers don't pre-exist. Cache write-through on apply — `search_customers` sees the new record immediately.

### Reference Data
- **list_locations** - List or fuzzy-search warehouses and facilities (id, name, address, primary flag). Use for `location_id` lookups on orders and inventory queries. Supports `query`, `limit`
- **list_suppliers** - List or fuzzy-search suppliers by name/code (id, name, email, phone, currency, code). Use for `supplier_id` / `default_supplier_id` on POs and materials. Supports `query`, `limit`
- **get_supplier** - Full-detail supplier record by id (contact info, address, payment terms). Pair with `list_suppliers(query=...)`.
- **list_tax_rates** - List or fuzzy-search configured tax rates (id, rate, defaults). Use for `tax_rate_id` on order line items. Supports `query`, `limit`
- **list_operators** - List or fuzzy-search manufacturing operators (id, name). Use for `operator_id` / `packer_id` on MO operations and SO fulfillments. Supports `query`, `limit`
- **list_additional_costs** - List or fuzzy-search the additional-cost catalog (freight, duties, handling). Use for `additional_cost_id` on `modify_purchase_order`. Supports `query`, `limit`

### Cache Administration
- **rebuild_cache** - Force-rebuild the local typed cache for one or more cached entity types. Covers transactional entities (PO, SO, MO, stock adjustment, stock transfer, bin transfer) and catalog entities (variant, product, material, service, customer, supplier, location, tax_rate, operator, factory, additional_cost). Truncates the cache table(s), clears the sync watermark, and re-fetches from Katana. Use when the cache has phantom rows (entities present locally but missing from Katana). Destructive; preview/apply.

## Safety Pattern

All create/modify operations use a **two-step preview/apply pattern**:
1. Call with `preview=true` (default) — returns a Prefab preview card with
   Confirm and Cancel buttons. **No changes made.**
2. Call with `preview=false` — executes the operation. Triggered either by
   the user clicking Confirm on the preview card, or by the agent
   re-issuing the call after a chat-based confirmation.

Destructive tools advertise this via the standard MCP `destructiveHint`
tool annotation; hosts that respect the annotation prompt the user before
invoking. The server does not gate further.

### Agent guidance for preview→apply

The same preview card serves two host families, and the agent's
end-of-turn behavior is different for each. The `content` channel of
every preview response carries the response JSON, so the data is always
available even if the card itself doesn't render.

**1. Hosts that do NOT render MCP Apps iframes** (Claude Code, plain CLI
clients). The Prefab card is invisible — the user can't click anything.
Summarize the planned change in chat from the `content` JSON (what's
changing, key field values), ask the user to confirm, and on yes
re-issue the call with `preview=False` yourself. Do **not** end your
turn waiting for a button click; there is none. Common signals that
this is the case: the user says they can't see the card, or you have no
prior evidence iframes have rendered in this session.

**2. Hosts that DO render iframes** (Claude Desktop, Claude.ai, Cowork).
The card has Confirm and Cancel buttons the user clicks. **Do not
re-narrate the card or ask for confirmation in chat** — the buttons
handle that. End your turn after the preview response.

*Unified direct-apply rail (ADR-0021, supersedes ADR-0015).* The
Confirm click fires the apply `tools/call` directly from the iframe
with the original args + `preview=False`, and the iframe pushes the
structured result back to the agent's model context via
`ui/update-model-context`. The agent sees the apply response on its
next turn without re-issuing — treat it as you would any tool-call
result (acknowledge completion, suggest next steps).

The Cancel button pushes an `UpdateContext` notification of the form

    User cancelled <description> preview.

into the agent's context, where `<description>` is a noun phrase that
already carries its own determiner — e.g. `the stock adjustment`,
`that purchase order`, `the receipt for PO-123`, `those purchase order
changes`. Acknowledge briefly without re-issuing. The user can ask
again later if they want to retry.

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

## Closed-Record Corrections

Three specialized tools — `correct_manufacturing_order`,
`correct_sales_order`, and `correct_purchase_order` — exist for the case
where you need to edit a record that has *already* reached a terminal
status (DONE for an MO, DELIVERED for an SO, RECEIVED /
PARTIALLY_RECEIVED for a PO) without losing the original close-state
metadata.

The standard `modify_<entity>` tool can technically do this, but the
operator has to discover and sequence several mechanical quirks each time:

- `done_date` can only be set once an MO is `DONE`; combined `status:
  DONE + done_date` PATCH calls fail because validation runs *before* the
  status change applies.
- Reverting a DONE MO auto-reverses its productions, so the original
  per-production `quantity`, `production_date`, and serial numbers must be
  re-played on the way back.
- Re-fulfilling a DELIVERED SO requires deleting fulfillments first
  (the delete returns an empty 200 body — `unwrap()` correctly flags it
  as `APIError`; callers should use `is_success`), then patching the
  status, editing lines, and re-creating fulfillments with the original
  `picked_date` / tracking metadata.
- A RECEIVED / PARTIALLY_RECEIVED PO has rows whose `quantity` /
  `variant_id` / `price_per_unit` are immutable while `received_date` is
  non-null. The reopen path is PATCH `/purchase_orders/{id}` with status
  → NOT_RECEIVED (which clears each row's `received_date`); the restore
  path is `POST /purchase_order_receive` with the captured per-row
  quantity / `received_date` / batch_transactions, which auto-promotes
  status back to RECEIVED.

The correction tools encode the proven sequence once. Each takes the edits
keyed by the *current* variant on the row (not the row ID), so the operator
expresses intent at the level they think about it ("swap SP73000 for
SP73001 on this MO"). Both follow the standard preview/apply pattern.

Use the regular `modify_<entity>` tool when:
- The record is still open (no close-state to preserve).
- The edits don't fit the variant-keyed (MO/SO) or row-id-keyed (PO)
  shape — e.g. you need to add a row, delete a row, or change something
  other than variant/quantity/price.
- The same variant appears on multiple rows on the same MO/SO and you want
  to disambiguate with the explicit row ID.

**Note**: `correct_purchase_order` keys edits by row ID (not variant ID
like the MO/SO siblings). The receive endpoint may split a partially-
received row into two physical rows post-receipt — both rows can carry
the same `variant_id`, so variant-keyed lookup would be ambiguous. Look
up current row IDs via `get_purchase_order` before calling
`correct_purchase_order`.

**No `correct_stock_transfer`** — stock transfers don't fit the pattern:
no completion timestamp on the model and rows are immutable, so the
close-state pattern adds no value. For corrections:
`create_stock_adjustment` at the destination location for quantity
discrepancies; `delete_stock_transfer` + `create_stock_transfer` for
wrong variants; `modify_stock_transfer` for header metadata (works on
RECEIVED transfers as-is).

## Output Format

**Always read `content` for the response payload.** It carries the tool's
JSON response on every tool. Programmatic consumers can `json.loads(...)`
the content text directly; LLM consumers read the JSON natively without a
markdown rendering layer in between.

`structured_content` carries different shapes depending on the tool:

- **Plain tools** (most read-only `list_*` / `get_*` / `search_*`) —
  `structured_content` is the same response dict as `content`. Either
  surface works for programmatic consumers.

- **UI tools** (the `meta={"ui": True}` set — `get_variant_details`,
  `check_inventory` single-item, modification previews, etc.) —
  `structured_content` carries a Prefab card envelope rendered by
  MCP-Apps hosts. The response payload lives *only* in `content` on
  these tools; programmatic consumers must read `content` (don't expect
  response-shaped JSON in `structured_content`).

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

"""

HELP_TOOLS = """
# Katana Tool Reference

Detailed guide for all available MCP tools.

---

## Inventory & Catalog Tools

### search_items
Find products, materials, and services by name or SKU.

By default, archived items are filtered out. To find an archived item (so
you can unarchive it via `modify_item`), pass `include_archived=true`.

**Parameters:**
- `query` (required): Search term to match against name or SKU
- `limit` (optional): Maximum results (default: 20)
- `include_archived` (optional, default false): When true, archived items
  are included in results. Each row carries an `is_archived` flag so the
  UI / caller can distinguish active vs archived rows.

**Examples:**

Active-only search:
```json
{"query": "bolt", "limit": 10}
```

Include archived rows:
```json
{"query": "old style", "include_archived": true}
```

**Returns:** List of matching items, each with two ids — `id` (the **variant
id**, for `get_variant_details` / `check_inventory` / order / PO / MO line
items) and `parent_id` (the **item id**, for `get_item` / `modify_item` /
`delete_item`) — plus SKU, name, sellable status, and archived state. The two
differ (a service/product/material item id is not its variant id); pass
`parent_id`, not `id`, to the item CRUD tools or they 404.

**Archive workflow:** Katana doesn't expose dedicated archive/unarchive
endpoints. Instead, archive state is a writable boolean on the item header
that you toggle via `modify_item`. Send this body to archive:

```json
{"update_header": {"is_archived": true}}
```

Or to unarchive:

```json
{"update_header": {"is_archived": false}}
```

See `modify_item` below for the full request shape.

---

### get_variant_details
Get exhaustive details for one or more item variants. Every field Katana
exposes on the Variant record is surfaced — no follow-up lookups needed
for pricing, barcodes, supplier codes, config attributes, custom fields,
or timestamps (including `deleted_at`).

For multiple variants at once, pass `{"skus": [...]}` or
`{"variant_ids": [...]}` — batching N lookups in one call beats N separate
invocations.

**Parameters (at least one of the first four is required):**
- `sku` (optional): Single SKU to look up (exact case-insensitive match)
- `variant_id` (optional): Single variant ID to look up directly
- `skus` (optional): Batch — list of SKUs to look up
- `variant_ids` (optional): Batch — list of variant IDs to look up
- `include_archived` (optional, default `false`): Include variants whose
  parent product/material is archived. On a duplicate SKU the live row
  always wins via the `get_by_sku` tiebreaker; set `true` only when
  inspecting an archived-only variant directly.
- `include_deleted` (optional, default `false`): Include soft-deleted
  variants. Same default rationale — `true` is for cleanup workflows.

**Examples:**
```json
{"sku": "BOLT-M8"}
{"variant_id": 12345}
{"skus": ["BOLT-M8", "NUT-M8"]}
{"variant_ids": [12345, 12346]}
{"sku": "ARCHIVED-SKU", "include_archived": true}
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

**Partial results on batch misses:** Singular requests
(`{"sku": "..."}` / `{"variant_id": ...}`) raise an error if the variant
isn't found. Batch requests (`{"skus": [...]}` / `{"variant_ids": [...]}`,
or any mixed form) never short-circuit — the response carries every variant
that resolved plus a `not_found` list of the missing identifiers. Response
shape: `{"variants": [...], "not_found": [{"sku": ...}, ...]}`. This makes
batching safe for receiving-flow lookups where one bad SKU on a packing
slip shouldn't lose the rest of the batch.

---

### check_inventory
Check current stock levels for one or more SKUs or variant IDs — pass a list for a summary table, one item for a detailed card.

**Parameters:**
- `skus_or_variant_ids` (required, min 1): List of SKUs (strings) or variant IDs (integers) — mix freely. Pass one for a stock card, many for a summary table.
- `location_id` (optional): Filter to a single warehouse/facility.
- `include_archived` (optional, default `false`): Include variants whose
  parent is archived, and surface archived per-location inventory rows
  (threaded through to `/inventory`). On a duplicate SKU the live row
  always wins; `true` is for cleanup workflows. Per-row `is_archived`
  surfaces on each `LocationStock`.
- `include_deleted` (optional, default `false`): Include soft-deleted
  variants when resolving the SKU. Same live-wins-on-duplicates default.

**Examples:**
```json
{"skus_or_variant_ids": ["WIDGET-001"]}
{"skus_or_variant_ids": ["WIDGET-001", "WIDGET-002"]}
{"skus_or_variant_ids": ["WIDGET-001", 12345]}
{"skus_or_variant_ids": ["ARCHIVED-SKU"], "include_archived": true}
```

**Returns:** Stock levels (in_stock, available_stock, committed, expected) per variant. Each per-location row carries `is_archived`; the top-level item carries `is_archived` derived from the variant's parent archive state.

---

### list_low_stock_items
Find items that are below their reorder threshold.

**Parameters:**
- `threshold` (optional): Stock threshold level (default: 10)
- `limit` (optional): Maximum items to return (default: 50)
- `include_archived` (optional, default `false`): Include archived
  inventory rows. Archived rows are filtered by default so they can't
  carry phantom signals into reorder planning; pass `true` for cleanup
  workflows. Each row reports two distinct archive signals:
  `is_archived` (variant's parent product/material is archived) and
  `has_archived_inventory` (at least one per-warehouse inventory row
  contributing to `current_stock` is archived).

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
- `location_id` (optional): Filter to a single warehouse/facility
- `resource_type` (optional): Filter by what caused the movement. One of
  `SalesOrderRow`, `ManufacturingOrder`, `ManufacturingOrderRecipeRow`,
  `ProductionIngredient`, `PurchaseOrderRow`, `PurchaseOrderRecipeRow`,
  `StockAdjustmentRow`, `StockTransferRow`, `SystemGenerated`
- `created_at_min` / `created_at_max` (optional, ISO-8601): Audit-trail window
  on when the movement record was first written
- `updated_at_min` / `updated_at_max` (optional, ISO-8601): When the record was
  last modified — useful for incremental sync
- `include_archived` / `include_deleted` (optional, default `false`):
  See `get_variant_details` for the soft-state defaults. The live row
  always wins on duplicate SKUs via the `get_by_sku` tiebreaker; flags
  are for cleanup workflows that need to inspect an archived/deleted
  variant's movement history directly.

**Returns:** Movement history with `id`, `variant_id`, `location_id`, `resource_type`,
`resource_id`, `caused_by_order_no`, `caused_by_resource_id`, `movement_date`,
`quantity_change`, `balance_after`, `value_per_unit`, `value_in_stock_after`,
`average_cost_after`, `rank`, `created_at`, `updated_at`. Markdown render uses
canonical Pydantic field names as column headers.

For point-in-time balance reconstruction (e.g., "what was on hand on 2026-03-15"),
prefer `inventory_at` — it walks movements and returns the resolved snapshot.

---

### inventory_at
Reconstruct inventory balance at a specific point in time by walking movement history.
The Katana `/inventory` endpoint is snapshot-only; this tool walks the
`/inventory_movements` ledger, filters to `movement_date <= as_of`, and per location
picks the most recent matching row — reading its `balance_after`,
`value_in_stock_after`, and `average_cost_after` as the as-of snapshot.

**Parameters:**
- `skus_or_variant_ids` (required, min 1, max 100): List of SKUs (strings) or variant
  IDs (integers) — mix freely. Output order matches input order.
- `as_of` (required, ISO-8601): The instant to reconstruct. Movements after this
  point are ignored.
- `location_id` (optional): Filter to a single warehouse/facility — only movements
  at that location are considered.
- `include_archived` / `include_deleted` (optional, default `false`):
  See `get_variant_details` for the soft-state defaults. Live wins on
  duplicates; flags for cleanup workflows only.

**Returns:** `{as_of, items, not_found}`. Each item carries `variant_id`, `sku`,
`display_name`, per-location rows (`location_id`, `location_name`, `balance_at`,
`value_in_stock_at`, `average_cost_at`, `last_movement_date`, `last_movement_id`),
and the totals across locations. Variants with no movements before `as_of` return
an empty `by_location` list — they had no stock at that moment.

**When to use which:**
- `check_inventory` → current state (single direct call, fastest).
- `inventory_at` → historical state (walks movements; for audits & reconstruction).
- `get_inventory_movements` → the raw delta stream (every change in order).

---

### create_stock_adjustment
Create a stock adjustment to correct inventory levels.

**Parameters:**
- `location_id` (required): Location ID for the adjustment
- `rows` (required): List of `{sku, quantity, cost_per_unit?, batch_transactions?}`
  - `quantity`: positive to add, negative to remove
  - `batch_transactions`: `list[{batch_id, quantity}]` — required for
    batch-tracked materials. Sum of allocated quantities should equal
    the row's `quantity`. Leave None for non-batch-tracked items.
- `reason` (optional): Reason for adjustment
- `additional_info` (optional): Internal notes
- `stock_adjustment_number` (optional): Adjustment number. Leave None to
  let the tool generate a `SA-<timestamp>` default. Supply only when
  importing from an external system or you need a specific number.
- `stock_adjustment_date` (optional, ISO 8601): When the adjustment
  occurred. Leave None to stamp the current call time. Supply for
  back-fills (e.g. recording a physical count from yesterday).
- `preview` (optional, default true): Set true to preview, false to create
- `include_archived` (optional, default `false`): Include variants whose
  parent is archived when resolving row SKUs. Default `false` fails fast
  with "SKU not found" rather than letting Katana reject downstream; set
  `true` for cleanup workflows that need to adjust stock on an archived
  item.
- `include_deleted` (optional, default `false`): Include soft-deleted
  variants when resolving row SKUs. Live wins on duplicates regardless.

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

**Returns:** When `group_by="variant"`: rows with variant_id, sku,
affected_mo_count, affected_mo_order_nos, total_planned_quantity
(per-unit times MO planned_quantity, summed), total_remaining_quantity,
earliest_expected_date. When `group_by="mo"`: per-MO entries with id,
order_no, status, deadline, and the blocking recipe rows nested.
Top-level `total_blocking_rows` and `total_affected_mos` are always
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
- `type` (required): Item type — "product", "material", or "service"
- `name` (required): Item name
- `sku` (required): SKU for the item variant
- `uom` (optional, default "pcs"): Unit of measure
- `category_name` (optional): Category for grouping
- `is_sellable` (optional, default true): Whether the item can be sold
- `sales_price` / `purchase_price` (optional): Variant pricing
- `is_producible` / `is_purchasable` (optional, products/materials only)
- `default_supplier_id` / `additional_info` (optional)

**Variant-level fields** (apply to product / material — ignored for service):
- `supplier_item_codes` (optional, `list[str]`): Supplier MPNs / cross-references.
  Use a list — Katana stores multiple codes per variant.
- `internal_barcode` / `registered_barcode` (optional): Barcodes (UPC/EAN goes in
  `registered_barcode`).
- `lead_time` (optional, int days), `minimum_order_quantity` (optional, float).
- `config_attributes` (optional, `list[{config_name, config_value}]`): Pin one
  value per parent config to define this variant. Only meaningful for
  multi-variant items — leave None for single-variant.

PREFER `create_product` for finished goods or `create_material` for raw materials —
those tools have simpler dedicated parameters. Use `create_item` for services or
when type is determined dynamically.

---

### get_item
Look up an item by ID and type — exhaustive detail across the
polymorphic Product / Material / Service record, plus nested `variants`
(summary), `configs`, and `supplier`. Type-specific fields
(`is_producible` on products, etc.) stay `null` for the other types.

**Parameters:**
- `id` (required): Item id — `search_items`' `parent_id`, NOT the variant
  `id`. They differ; the variant id 404s here.
- `type` (required): "product" | "material" | "service"

For per-variant detail (barcodes, supplier codes, custom fields), follow
up with `get_variant_details` (which takes the variant `id`).

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
  `purchase_uom_conversion_rate` / `configs` are PRODUCT/MATERIAL only;
  `sales_price` / `default_cost` / `sku` are SERVICE-only.
  `is_archived` is shared across all three types — set true to archive,
  false to unarchive. Misrouted fields fail fast with a clear error.
- `update_header.configs` — replace the full set of variant-defining
  attributes (e.g. `Size`, `Color`). Each entry: `name` (str) and
  `values` (list[str]). Optional `id` (int) is honored for MATERIAL only
  to match an existing config; PRODUCT updates always match by `name`.
  Katana overwrites the full list at apply time — omit a config and it
  gets deleted, so always send every config you want to keep.
- `add_variants[].config_attributes` /
  `update_variants[].config_attributes` — pin one value per parent
  config on each variant entry (e.g. `[{config_name: "Size",
  config_value: "M"}, ...]`). Names must match a config on the parent;
  `update_variants[].config_attributes` overwrites the variant's
  existing list at apply time.
- `add_variants` — POST `/variant`. Parent `product_id` / `material_id`
  is injected automatically from the request's `type`. Not supported
  for SERVICE (services carry pricing on the header, not on variants).
- `update_variants` / `delete_variant_ids` — variant CRUD. Not supported
  for SERVICE.

**Parameters:**
- `id` (required): Item id — `search_items`' `parent_id`, NOT the variant
  `id`. They differ; passing the variant id routes to
  `/products|materials|services/{id}` and 404s (most visibly for services,
  whose only modify path is `update_header`).
- `type` (required): "product" | "material" | "service"
- Any subset of the sub-payloads above
- `preview` (optional, default true): true=preview, false=execute

**Archive / unarchive examples:**

Archive a product (preview):
```json
{"id": 12345, "type": "product", "update_header": {"is_archived": true}}
```

Unarchive a material (apply):
```json
{
  "id": 67890,
  "type": "material",
  "update_header": {"is_archived": false},
  "preview": false
}
```

To find an archived item before unarchiving it, call `search_items` with
`include_archived=true`.

---

### delete_item
Delete an item. Destructive — Katana cascades child variants server-side.

**Parameters:**
- `id` (required): Item id — `search_items`' `parent_id`, NOT the variant `id`.
- `type` (required): "product" | "material" | "service"
- `preview` (optional, default true): true=preview, false=delete

---

### get_product_bom
List the BOM (Bill of Materials) rows for a producible product variant —
the master recipe future manufacturing orders are copied from. Distinct
from `get_manufacturing_order_recipe`, which reads a single MO's recipe
snapshot.

BOM rows are **variant-scoped** — a producible product with multiple
variants has a separate recipe per variant. Pass the specific
`product_variant_id`. For multi-variant products, call once per variant.

**Parameters:**
- `product_variant_id` (required): Variant ID whose BOM rows to fetch

**Returns:** Each row carries every field on the underlying `BomRow`
(id (UUID string), product_item_id, product_variant_id,
ingredient_variant_id, quantity, notes, rank) plus the resolved
ingredient SKU and Katana-UI display_name (looked up from the typed
cache). Empty `rows` is a clean response, not an error — variants
without a recipe and unknown variant IDs both surface as
`total_count: 0`. Pair with `get_variant_details` first to confirm
`is_producible`.

---

### manage_product_bom
Add / update / delete BOM rows on a producible product variant
(preview/apply). Edits the master recipe; existing MOs are unaffected,
but future MOs created from this variant pick up the new recipe.

For per-MO recipe edits (a one-off change to one work order), use
`modify_manufacturing_order` instead — its `add_recipe_rows` /
`update_recipe_rows` / `delete_recipe_row_ids` sub-payloads target a
specific MO's snapshot.

**Parameters:**
- `id` (required): Parent product variant ID (BOM rows are
  variant-scoped, not product-scoped)
- `add_bom_rows` (optional): list of new rows, each
  `{ingredient_variant_id, quantity?, notes?}`. The tool resolves the
  parent `product_item_id` automatically from the typed cache.
- `update_bom_rows` (optional): patches to existing rows. Each:
  `{id (UUID), ingredient_variant_id?, quantity?, notes?}`. Look up
  the row id with `get_product_bom`. `rank` is server-managed and not
  patchable.
- `delete_bom_row_ids` (optional): UUIDs of rows to remove
- `preview` (optional, default true): true=preview, false=execute

**Behavior notes:**
- Actions execute in canonical order (adds → updates → deletes).
  Fail-fast on the first error — later actions are not attempted.
- Update diffs are marked `is_unknown_prior=true` because BOM rows have
  no individual GET-by-id endpoint. Call `get_product_bom` after
  applying to see the post-state.
- Errors when the parent variant isn't in the catalog cache (call
  `search_items` or `get_variant_details` first), or when the variant
  has neither a product nor material parent.

---

## Purchase Order Tools

### create_purchase_order
Create a purchase order with preview/apply pattern.

**Parameters:**
- `supplier_id` (required): Supplier ID
- `location_id` (required): Warehouse location for receipt
- `order_number` (required): PO number (e.g., "PO-2025-001")
- `items` (required): Array of line items with variant_id, quantity,
  price_per_unit (plus optional tax_rate_id, purchase_uom,
  purchase_uom_conversion_rate, arrival_date)
- `notes` (optional): Internal notes (additional_info on the wire)
- `currency` (optional): Currency code (e.g., USD, EUR)
- `status` (optional): "DRAFT" (default) or "NOT_RECEIVED". DRAFT is an unsent
  draft to review before committing the order; NOT_RECEIVED is an already-placed
  order awaiting receipt. Move between them later with `modify_purchase_order`.
- `entity_type` (optional): "regular" (default) or "outsourced". Outsourced
  orders track subcontractor manufacturing. **When `entity_type="outsourced"`,
  `tracking_location_id` is required** — Katana will reject the create call
  without it.
- `order_created_date` (optional, ISO 8601): When the order was placed.
  Leave None to let Katana stamp the current server time. Supply for
  back-fills (importing historical orders) or to reflect actual placement
  when different from the call time.
- `expected_arrival_date` (optional, ISO 8601): Order-level expected
  arrival; row-level `arrival_date` overrides per line.
- `tracking_location_id` (optional, int): Location ID for tracking
  outsourced orders. Required when `entity_type="outsourced"`.
- `preview` (optional, default true): true=preview, false=create

**Safety:** When preview=false, prompts user for confirmation before creating.

---

### receive_purchase_order
Receive items from a purchase order.

**Parameters:**
- `order_id` (required): Purchase order ID
- `items` (required): Array of items. Each item:
  - `purchase_order_row_id` (int, required)
  - `quantity` (float, required, >0)
  - `received_date` (ISO 8601 string, optional) — when the items were
    actually received. Defaults to call time, which is wrong for back-dated
    receives (e.g., re-receiving an old shipment after a variant correction).
  - `batch_transactions` (array, optional) — required for batch-tracked
    materials. Each entry: `batch_id` (int) + `quantity` (float). Summed
    quantity across batch_transactions should equal the row-level quantity.
- `preview` (optional, default true): true=preview, false=receive

**Safety:** When preview=false, prompts user for confirmation.

**Landed costs:** `receive_purchase_order` does not set customs / freight /
duties. After receiving, apportion them with
`modify_purchase_order(add_additional_costs=[{additional_cost_id, price,
tax_rate_id, distribution_method, group_id?}])`. Look up `additional_cost_id`
via `list_additional_costs`. Omit `group_id` and the dispatcher applies the
cost to the PO's `default_group_id`; pass a specific `group_id` to target one cost
group. This is MCP-native — it does not require the Katana UI.

---

### verify_order_document
Verify a supplier document (invoice, packing slip) against a PO.

**Parameters:**
- `order_id` (required): Purchase order ID to verify against
- `document_items` (required): Array of items from document with sku, quantity, unit_price

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
  inventory updates use `receive_purchase_order` instead. When the
  caller doesn't change `additional_info` and a snapshot is available,
  the wrapper echoes the existing value in the PATCH body — Katana's
  PATCH endpoint asymmetrically wipes that field when it's omitted,
  so the echo compensates so notes survive header edits (best-effort:
  skipped if the pre-edit GET fails, the existing value is empty, or
  the caller supplied an explicit override). See
  `docs/KATANA_API_QUESTIONS.md` section 6.1.
  **Date cascade** — updating `expected_arrival_date` on the header
  cascades server-side onto the row-level `arrival_date` of line items.
  If you need specific rows to keep different dates, include them in
  `update_rows` in the SAME modify call. Conversely, updating a single
  row's `arrival_date` bumps the header to the latest row date if
  applicable, but does not affect other rows. This came up during a
  2026-05-12 PO reconciliation; the pattern likely applies to other
  date fields with row/header duality.
- `add_rows` — list of new line items. Each row:
  `variant_id` (int, required), `quantity` (float, required, >0),
  `price_per_unit` (float, required), `tax_rate_id` (int — see
  `list_tax_rates`), `tax_name`, `tax_rate`, `currency`,
  `purchase_uom`, `purchase_uom_conversion_rate`, `arrival_date`.
- `update_rows` — list of patches. Each entry: `id` (int, required) +
  any subset of `quantity`, `variant_id`, `tax_rate_id`, `tax_name`,
  `tax_rate`, `price_per_unit`, `purchase_uom`,
  `purchase_uom_conversion_rate`, `received_date`, `arrival_date`.
- `delete_row_ids` — list of row IDs to delete.
- `add_additional_costs` — list of new freight / duty / handling rows.
  Each row: `additional_cost_id` (int, required — see
  `list_additional_costs` for catalog IDs), `tax_rate_id` (int,
  required — see `list_tax_rates`), `price` (float, required),
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

**Returns:** List of customers with id, name, email, phone, currency.

---

### get_customer
Get full details for a customer by ID.

**Parameters:**
- `customer_id` (required): Customer ID

**Returns:** Full customer details (name, email, phone, currency, category, comment).

---

### create_customer
Create a new customer record. Two-step preview/apply flow with a card-rendered
preview. Use for non-Shopify channels (eBay, Amazon, Etsy, direct-website)
where buyers don't pre-exist in Katana — Shopify-synced workflows usually see
the customer arrive on their own.

**Parameters:**
- `name` (required): Display name shown in Katana and on documents
- `first_name`, `last_name` (optional): For individual contacts
- `company` (optional): Company name for business accounts
- `email`, `phone` (optional): Contact details
- `currency` (optional): ISO 4217 code (USD, EUR, GBP, ...)
- `comment` (optional): Internal notes (not shown to the customer)
- `reference_id` (optional): External reference (e.g., the customer's ID in
  another system)
- `category` (optional): Free-form segmentation label
- `discount_rate` (optional): Default percentage discount on orders (0-100)
- `addresses` (optional): List of `{entity_type: "billing"|"shipping",
  first_name, last_name, company, phone, line_1, line_2, city, state, zip,
  country}` items
- `preview` (default `true`): If true, returns a preview card; if false,
  creates the customer

**Returns:** Created customer summary (id, name, contact fields, currency,
addresses snapshot, katana_url) plus next-action coaching. On apply, the
new record writes through to the typed cache so a follow-up
`search_customers` returns it immediately — no `rebuild_cache` needed.

---

### get_manufacturing_order_recipe
List the ingredient (recipe) rows for a manufacturing order with exhaustive detail.
For recipe rows across multiple MOs, call `get_manufacturing_order` once per MO —
it returns recipe rows inline (there is no batch shape for this tool).

**Parameters:**
- `manufacturing_order_id` (required): MO ID

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
  `planned_quantity_per_unit` + optional notes. Both add and update
  accept `batch_transactions` (list of `{batch_id, quantity}`) for
  batch-tracked ingredients — required so the MO consumes from the
  right batch records.
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

### correct_manufacturing_order
Edit a closed MO (status DONE or PARTIALLY_COMPLETED) without losing its
original close-state. Reopens the MO, swaps recipe-row ingredients keyed
by current variant, then re-closes preserving the original status,
`done_date`, and per-production `quantity` / `production_date` / serial
numbers.

For an MO that hasn't shipped yet, use `modify_manufacturing_order`
directly — there's no close-state to preserve.

**Parameters:**
- `id` (required): Manufacturing order ID
- `ingredient_changes` (required, min_length=1): list of recipe-row edits.
  Each entry: `old_variant_id` (variant currently on the row, required),
  `new_variant_id` (optional — None to keep variant), and/or
  `planned_quantity_per_unit` (optional, >0 — None to keep quantity). At
  least one of `new_variant_id` / `planned_quantity_per_unit` must be set.
- `preview` (optional, default true): true=preview, false=execute

**Sequence executed (in order):**
1. PATCH MO status → IN_PROGRESS (Katana auto-reverses productions)
2. PATCH each recipe row per `ingredient_changes`
3. POST one production per snapshot (replays `completed_quantity` and
   `serial_numbers`)
4. PATCH each new production's `production_date` to its snapshot value
5. PATCH MO status → DONE

**Errors when:**
- The MO isn't in DONE / PARTIALLY_COMPLETED status (use `modify_manufacturing_order`).
- An `old_variant_id` doesn't match any current recipe row, or matches
  multiple rows (use `modify_manufacturing_order` with the explicit row ID).
- An `ingredient_changes` entry has neither `new_variant_id` nor
  `planned_quantity_per_unit` set.

**Returns:** A `ModificationResponse` with one `ActionResult` per phase
step. Fail-fast halt at any phase boundary leaves the MO in an
intermediate (open) state with the captured close-state in `prior_state`
for manual recovery.

---

### create_sales_order
Create a sales order with preview/apply pattern.

**Required:**
- `customer_id`: Customer ID (use `search_customers` to find)
- `order_number`: Unique sales order number
- `items`: Array of items, each with `variant_id`, `quantity`, plus
  optional `price_per_unit`, `tax_rate_id`, `location_id`,
  `total_discount`, and `attributes` (`list[{key, value}]` for product
  customization metadata like engraving text, monogram, gift-wrap notes)

**Optional header fields:**
- `location_id`: Primary fulfillment location ID
- `delivery_date` (ISO 8601): Requested delivery date
- `order_created_date` (ISO 8601): When the order was placed. Leave None
  to let Katana stamp the current server time. Supply for back-fills or
  to reflect the actual placement date when different from call time.
- `currency`: Currency code (defaults to company base currency)
- `addresses`: List of billing/shipping addresses
- `notes`: Internal notes (additional_info on the wire)
- `customer_ref`: Customer's reference number

**Initial status & picking** (#907):
- `status` (optional): Initial SO status. Katana's `POST /sales_orders`
  accepts only `NOT_SHIPPED` or `PENDING`; omit to default to `PENDING`.
  Pass `NOT_SHIPPED` to skip the transient `PENDING` state when
  back-filling an already-confirmed order — this avoids the forced
  PENDING→NOT_SHIPPED transition that otherwise strands the SO in PENDING
  and silently blocks `fulfill_order`. `PACKED`/`DELIVERED` are rejected
  here (BLOCK) — reach them by shipping the order via
  `fulfill_order(order_type='sales')`.
- `picked_date` (ISO 8601, optional): When items were picked. Wire-level,
  Katana's `POST /sales_orders` rejects `picked_date`, so the apply path
  sets it via a follow-up `PATCH /sales_orders/{id}` after the SO exists.
  Best-effort: the SO is durable; a failed patch surfaces a warning and a
  retry hint pointing at `modify_sales_order(id=<so_id>,
  update_header={'picked_date': ...})`.

**Shipping / tracking:**
- `tracking_number`, `tracking_number_url`: Set if a carrier label is
  already known at creation time; otherwise patch in via
  `modify_sales_order.update_header.tracking_number`.
- `shipping_fees` (optional, list): Inline shipping fees to attach to the
  new SO. Each entry: `amount` (decimal string, required, e.g. "8.95"),
  `description` (label like "Standard shipping"), `tax_rate_id` (see
  `list_tax_rates`). Eliminates the create-then-modify two-step that
  every ecommerce-order workflow hits (#818).
  - **Wire-level**: Katana's `POST /sales_orders` doesn't accept fees
    inline, so the apply path creates the SO first and then fires
    `POST /sales_order_shipping_fee` per fee.
  - **Best-effort semantics**: SO success is durable. If any fee fails,
    the response carries a warning and per-fee outcomes; the SO remains
    intact. Retry failed fees via
    `modify_sales_order(id=<so_id>, add_shipping_fees=[...])`.

**Ecommerce cross-references** (set when the SO came from a native ecommerce
integration). All three are **create-only** — they cannot be changed via
`modify_sales_order`:
- `ecommerce_order_type`: case-sensitive platform id. Deep-linkable values:
  `shopify`, `wooCommerce`, `bigCommerce` (camelCase). Other strings are
  accepted but don't render a storefront link.
- `ecommerce_store_name`: storefront hostname for Shopify/WooCommerce
  (e.g. 'acme.myshopify.com'); the bare store slug for BigCommerce.
- `ecommerce_order_id`: original platform order id (e.g. '19433769').

**Custom fields:**
- `custom_fields`: `list[{field_name, field_value}]`. Names must already
  exist on the SO custom-field collection (configured via Katana's UI).
  Sending an unknown name yields a 422.

**`preview`** (optional, default true): true=preview, false=create.

**Returns:** `SalesOrderResponse` with the standard SO fields plus
`shipping_fee_outcomes` (per-fee status rows when `shipping_fees` was
supplied — `succeeded=None` on preview; `succeeded=True/False` on apply
with `created_id` on success or `error` on failure).

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

On UI-capable hosts this renders a read-only detail card (status, total,
line items, resolved customer/location names, addresses, storefront link)
with a single "View in Katana" action.

**Returns:** Every field Katana exposes on the sales order record —
identifiers (id, order_no, customer_id, customer_name, location_id,
location_name, source), status flags
(status, production_status, invoicing_status, product_availability,
ingredient_availability), dates (order_created_date, delivery_date,
picked_date, product_expected_date, ingredient_expected_date), money (total,
total_in_base_currency, currency, conversion_rate, conversion_date), notes
(additional_info, customer_ref), tracking (tracking_number,
tracking_number_url), address pointers (billing_address_id,
shipping_address_id) plus the full resolved `addresses` list fetched from
/sales_order_addresses, `shipping_fee` block, `linked_manufacturing_order_id`,
ecommerce metadata (ecommerce_order_type/store_name/order_id, plus a derived
`ecommerce_url` "Open in {platform}" storefront deep-link for Shopify/
WooCommerce/BigCommerce orders), timestamps
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

### correct_sales_order
Edit a closed SO (status DELIVERED) without losing its original
close-state. Reopens the SO, edits line items keyed by current variant,
then re-closes preserving the original status, `picked_date`, and per-
fulfillment metadata (status / `picked_date` / tracking_*).

For an SO that hasn't shipped yet, use `modify_sales_order` directly —
there's no close-state to preserve.

**Parameters:**
- `id` (required): Sales order ID
- `line_changes` (required, min_length=1): list of line-item edits. Each
  entry: `old_variant_id` (variant currently on the row, required),
  `new_variant_id` (optional), `quantity` (optional, >0), `price_per_unit`
  (optional). At least one of the latter three must be set.
- `preview` (optional, default true): true=preview, false=execute

**Sequence executed (in order):**
1. DELETE each existing fulfillment (Katana returns empty 200 — handled)
2. PATCH SO status → PENDING
3. PATCH each row per `line_changes`
4. POST one fulfillment per snapshot (replays status + `picked_date` +
   tracking_* + row references)
5. PATCH SO status → DELIVERED

**Errors when:**
- The SO isn't in DELIVERED status.
- An `old_variant_id` doesn't match any current row, or matches multiple
  rows on this SO.
- A `line_changes` entry sets none of `new_variant_id` / `quantity` /
  `price_per_unit`.

**Constraints:**
- Only updates rows in place; doesn't add or delete rows. Row IDs must stay
  stable so the re-created fulfillments can reference them by the original
  `sales_order_row_id`. If you need to add or remove a line, use
  `modify_sales_order`.
- A new `quantity` must be >= the original fulfillment quantity for that
  row, or Katana will reject the re-fulfillment step.

**Returns:** A `ModificationResponse` with one `ActionResult` per phase
step. Fail-fast halt leaves the SO in an intermediate (open) state with
the captured close-state in `prior_state`.

---

### correct_purchase_order
Edit a closed PO (status RECEIVED or PARTIALLY_RECEIVED) without losing
its original receipt metadata. Reverts to NOT_RECEIVED (clearing each
row's `received_date` so per-row fields become editable again), edits
rows keyed by row ID, then re-receives via `POST /purchase_order_receive`
to restore the captured per-row `quantity` / `received_date` /
`batch_transactions`. The receive endpoint promotes status back to
RECEIVED automatically once every row is fully received.

For a PO that hasn't been received yet, use `modify_purchase_order`
directly — there's no close-state to preserve.

**Parameters:**
- `id` (required): Purchase order ID
- `row_changes` (required, min_length=1): list of row edits. Each entry:
  `row_id` (existing row ID — find via `get_purchase_order`, required),
  `new_variant_id` (optional), `quantity` (optional, >0), `price_per_unit`
  (optional, >=0). At least one of the latter three must be set.
- `preview` (optional, default true): true=preview, false=execute

**Sequence executed (in order):**
1. PATCH PO status → NOT_RECEIVED (clears each row's `received_date`)
2. PATCH each row per `row_changes` (Katana now allows
   variant_id / quantity / price_per_unit edits since `received_date` is null)
3. POST `/purchase_order_receive` once per captured receipt, replaying
   `quantity` + `received_date` + `batch_transactions`. The endpoint
   auto-promotes status back to RECEIVED.

**Errors when:**
- The PO isn't in RECEIVED / PARTIALLY_RECEIVED status (use `modify_purchase_order`).
- A `row_id` doesn't match any current row on the PO.
- A `row_changes` entry sets none of `new_variant_id` / `quantity` /
  `price_per_unit`.
- A `quantity` drops below the originally-received quantity for that row
  (the receipt replay would fail and leave the PO mid-flow).

**Constraints:**
- Only updates rows in place; doesn't add or delete rows. Row IDs must
  stay stable so the re-receive POST can reference them by the original
  `purchase_order_row_id`. To add or remove a line, use `modify_purchase_order`
  (after the correction lands), or delete + recreate the PO.
- Edits are keyed by row ID, **not** by variant ID. The receive endpoint
  may split partially-received rows post-receipt — both halves can share
  the same variant — so variant-keyed lookup would be ambiguous on a
  PARTIALLY_RECEIVED PO.
- A PARTIALLY_RECEIVED PO's unreceived remnant rows stay open after the
  correction lands; re-issue `receive_purchase_order` for those when the
  rest of the shipment arrives.

**Returns:** A `ModificationResponse` with one `ActionResult` per phase
step (revert + edits + per-row re-receives). Fail-fast halt leaves the PO
in an intermediate (open) state — typically NOT_RECEIVED with edits
applied but receipts not replayed — with the captured close-state in
`prior_state` for manual recovery via `receive_purchase_order`.

---

### create_product / create_material
Dedicated catalog tools for creating products (finished goods) or materials
(raw inputs) with a single variant. Header fields plus variant-level fields
(barcodes, supplier codes, lead time, MOQ, config attributes) all flow through
in one call — no follow-up `modify_item` round-trip needed.

**Header parameters (both):**
- `name` (required), `sku` (required), `uom` (optional, default "pcs")
- `category_name`, `is_sellable`, `sales_price`, `purchase_price`,
  `default_supplier_id`, `additional_info` (all optional)

**`create_product` only:**
- `is_producible` (default false), `is_purchasable` (default true)

**Variant-level fields (both — forwarded to the item's single variant):**
- `supplier_item_codes` (optional, `list[str]`): Supplier MPNs / cross-references
- `internal_barcode` / `registered_barcode` (optional): Barcodes; UPC/EAN goes in
  `registered_barcode`
- `lead_time` (optional, int days), `minimum_order_quantity` (optional, float)
- `config_attributes` (optional, `list[{config_name, config_value}]`): Pin
  one value per parent config to define this variant. Only meaningful for
  multi-variant items — leave None for single-variant.

To edit any of the above on an existing item, use `modify_item` with
`update_variants` / `update_header`.

---

### fulfill_order
Complete a manufacturing or sales order.

**Parameters:**
- `order_id` (required): Order ID to fulfill
- `order_type` (required): "manufacturing" or "sales"
- `preview` (optional, default true): true=preview, false=fulfill
- `rows` (optional, sales orders only): Per-row overrides
  `[{sales_order_row_id, serial_numbers?}]`. `serial_numbers` is a list of
  pre-existing `SerialNumber` IDs to attach to that row; the count must
  equal the row's ordered quantity. **Required** when the row's variant is
  serial-tracked — without it, the tool emits a `BLOCK:` warning at preview
  and refuses on direct apply (Katana would 422 the request).
  **Caveat (serial minted on a linked MO):** the public-API write paths
  cannot *transfer* a serial that is currently attached to the row's linked
  manufacturing order — `POST /sales_order_fulfillments` returns "serial
  numbers have already been assigned" and `add_serial_numbers(SalesOrderRow)`
  returns "is linked, serial info must be updated on MO". That common
  close-out case (finished good came off an MO with the serial already
  minted) has no MCP-native path today; fulfill it from the Katana UI
  ("Deliver all"), which performs the MO→SO transfer atomically.
- `serial_numbers` (optional, manufacturing orders only): List of pre-existing
  `SerialNumber` IDs to attach to the produced units when marking the MO
  DONE. Length must equal `actual_quantity`. **Required** when the MO's
  finished-good variant is serial-tracked — without it, the tool emits a
  `BLOCK:` warning at preview and refuses on direct apply (Katana would 422
  the request).
- `completed_at` (optional, ISO-8601): Backdated completion timestamp. MO →
  production POST `completed_date` (Katana propagates to `MO.done_date`);
  SO → fulfillment `picked_date`. Omit to let Katana stamp server-time.
  **There is no separate `picked_date` / `delivery_date` parameter** — set
  the SO picked date (or MO done date) through `completed_at`; it is the
  single backdating knob for both order types.
- `acknowledge_inventory_ordering` (optional, default false): Override flag
  for the inventory-ordering guard. The guard fires when `completed_at` is
  supplied and a linked entity's timestamp is known — Katana's
  timestamp-ordered movement engine requires MO `done_date` to land
  **strictly before** SO `picked_date`. The BLOCK message suggests a
  1-minute offset in the safe direction (MO `done_date` 1 minute before
  the linked SO `picked_date`, or SO `picked_date` 1 minute after the
  linked MO `done_date`) as a safe default — any strictly-ordered value
  works; 1 minute is the recommendation, not a Katana-enforced floor.
  Setting `acknowledge_inventory_ordering=true` demotes the BLOCK to a
  non-BLOCK warning so the apply proceeds (the caller has accepted the
  consequence of a transient negative balance on the persistent
  `inventory_movements` ledger). Use only after explicit ledger
  verification.

**Returns:** Standard fulfillment envelope (`order_id`, `order_type`,
`order_number`, `status`, `is_preview`, `inventory_updates`, `warnings`,
`next_actions`, `message`) plus the Tier 2 metrics + Tier 3 per-row
breakdown introduced in #553 + the post-#card-ux reference block:
- `fulfilled_rows`: Per-row breakdown — list of `{row_id, variant_id, sku,
  display_name, quantity, serial_numbers, batch_summary, price_per_unit,
  row_total, currency}`. For manufacturing orders this is always a single
  synthesized row (the MO's finished good) with `row_id=None`; for sales
  orders it's one entry per SO row.
- `rows_count`: Count of fulfilled rows — equals SO row count for sales,
  always `1` for manufacturing.
- `total_quantity`: Sum of quantities across `fulfilled_rows`.
- `total_value`: Sum of `row_total` across rows in the order's currency.
  `None` when no row carries a price (manufacturing orders track cost,
  not price).
- `currency`: ISO 4217 currency code (sales orders only; `None` for MOs).
- `katana_url`: Deep link to the order in the Katana web UI (drives the
  Tier 4 "View in Katana" action on the success card).
- `customer_id` / `customer_name` *(sales orders only)*: Customer placing
  the SO. `customer_name` is resolved through the typed cache and drives
  the Tier-3 `Customer:` party-line on the card. `None` on manufacturing
  orders (MOs have no customer).
- `shipping_address` / `billing_address` *(sales orders only)*:
  `SalesOrderAddress.to_dict()` dicts fetched from
  `/sales_order_addresses`. `billing_address` is `None` when it duplicates
  shipping (the card hides the second block in that case).
- `picked_date`: ISO-8601 timestamp surfaced as the `Picked` (sales) or
  `Completed` (manufacturing) Metric. On the success path the impl
  prefers the server-stamped value (`fulfillment.picked_date` for SOs,
  `MO.done_date` for MOs) over the caller-supplied `completed_at`.
  `None` when no timestamp is known (preview without `completed_at` and
  server hasn't stamped yet).

---

## Stock Transfer Tools

### create_stock_transfer
Create a stock transfer moving inventory between two locations.

**Parameters:**
- `source_location_id` (required): Source location ID
- `destination_location_id` (required): Destination location ID (target_location_id)
- `expected_arrival_date` (required): Expected arrival datetime (ISO-8601)
- `transfer_date` (optional, ISO 8601): Date items leave the source.
  Distinct from `expected_arrival_date` (when they arrive). Leave None
  to let Katana stamp it server-side; supply for back-fills or to
  record an actual ship-out date.
- `order_created_date` (optional, ISO 8601): When the transfer record
  was created. Leave None for server-stamping; supply for back-fills.
- `rows` (required): Line items `[{variant_id, quantity, batch_transactions?}]` —
  `batch_transactions` is `[{batch_id, quantity}]` for batch-tracked variants
- `order_no` (optional): Stock transfer number. When omitted, the tool
  generates a `ST-<unix-ts>` default before sending — Katana's API
  requires the field.
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
- `ids` (optional): Filter by explicit list of stock transfer IDs
- `status` (optional): "DRAFT", "IN_TRANSIT", or "RECEIVED" (mapped to the
  Katana wire values "draft" / "inTransit" / "received" against the cache
  column)
- `source_location_id` (optional): Filter by source location ID
- `destination_location_id` (optional): Filter by destination (target) location ID
- `stock_transfer_number` (optional): Exact match on the transfer number
- `include_deleted` (optional, default `false`): When `true`, surface
  soft-deleted transfers. Mirrors the peer list-tool default (#539, #484).
- `created_after` / `created_before` (optional): ISO-8601 datetime bounds on
  created_at — indexed SQL range filter
- `updated_after` / `updated_before` (optional): ISO-8601 datetime bounds on
  updated_at — indexed SQL range filter (peer parity with PO/SO/MO lists)
- `include_rows` (optional, default false): Populate per-transfer row details

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

## Bin Transfer & Storage Bin Tools

Bin transfers move stock **between storage bins within a single location**
(contrast stock transfers, which move between locations). The status flow
is CREATED → IN_TRANSIT → DONE. Unlike stock transfers, bin transfer rows
are fully mutable post-creation and a GET-by-id endpoint exists, so
previews show real `before → after` diffs.

### create_bin_transfer
Create a bin transfer within one location.

**Parameters:**
- `location_id` (required): Location the transfer occurs within — bins on
  both sides must belong to it
- `rows` (required): Line items
  `[{variant_id, quantity, source_bin_location_id?, target_bin_location_id?, traceability?}]` —
  `traceability` is `[{batch_id? | serial_number_id?, quantity}]` for
  tracked variants. A `null` source means unassigned (un-binned) stock; a
  `null` target moves stock to the location's unassigned pool.
- `bin_transfer_number` (optional): When omitted, Katana assigns one
  server-side
- `additional_info` (optional): Notes
- `created_date` (optional, ISO 8601): Leave None for server-stamping;
  supply for back-fills
- `preview` (optional, default true): true=preview, false=create

**Safety:** When preview=false, prompts user for confirmation before creating.

---

### list_bin_transfers
List bin transfers with filters. All filters run as indexed SQL against the
typed cache. (The endpoint has no `updated_at_min` support, so each sync is
a full fetch — fine for this low-volume entity.)

**Parameters:**
- `limit` (optional, default 50, min 1): Max rows to return
- `page` (optional): Page number (1-based); when set, the response includes
  `pagination` metadata computed via SQL COUNT
- `ids` (optional): Filter by explicit list of bin transfer IDs
- `status` (optional): "CREATED", "IN_TRANSIT", or "DONE" (tool literals
  equal the Katana wire values)
- `location_id` (optional): Filter by location ID
- `bin_transfer_number` (optional): Exact match on the transfer number
- `include_deleted` (optional, default `false`): When `true`, surface
  soft-deleted transfers
- `created_after` / `created_before`, `updated_after` / `updated_before`
  (optional): ISO-8601 datetime bounds — indexed SQL range filters
- `include_rows` (optional, default false): Populate per-transfer row
  details (variant, quantity, source/target bin, traceability)

---

### modify_bin_transfer
Unified modification surface — header fields, row-level CRUD, and status
transition in one call.

**Sub-payloads (all optional, any subset combinable):**
- `update_header` — patch body fields (`bin_transfer_number`,
  `location_id`, `additional_info`, `created_date`, `departed_at`,
  `arrived_at`).
- `add_rows` / `update_rows` / `delete_row_ids` — line item CRUD. Bin
  transfer rows are mutable post-creation (`POST/PATCH/DELETE
  /bin_transfer_rows`), unlike stock-transfer rows. `update_rows` entries
  carry `id` plus any subset of `variant_id`, `quantity`,
  `source_bin_location_id`, `target_bin_location_id`, `traceability`
  (full replacement list). Omitted fields are left unchanged — a bin
  assignment can be reassigned but not cleared back to unassigned via
  `update_rows`; delete and re-add the row to un-bin it.
- `update_status` — `new_status: "CREATED" | "IN_TRANSIT" | "DONE"`.
  Katana rejects invalid transitions; the action's error surfaces in the
  response.

**Parameters:**
- `id` (required): Bin transfer ID
- Any subset of the sub-payloads above
- `preview` (optional, default true): true=preview, false=execute the
  action plan in canonical order (header → row adds → row updates → row
  deletes → status — status last so a DONE transition sees the final row
  set); fail-fast on first error

---

### delete_bin_transfer
Delete a bin transfer. Destructive — the transfer record (and its rows)
is removed. The preview carries a `prior_state` snapshot including rows.

**Parameters:**
- `id` (required): Bin transfer ID
- `preview` (optional, default true): true=preview, false=delete

---

### list_bin_inventory
Per-bin stock levels — which bins hold which stock. Live read against
`GET /bin_inventory` (not cached: rows carry no id/updated_at).

**Parameters:**
- `granularity` (optional, default "VARIANT"): "VARIANT" aggregates per
  variant+bin; "BATCH" / "SERIAL_NUMBER" break rows out per batch / serial
- `location_id` / `variant_id` (optional): Scope filters
- `bin_location_id` / `batch_id` / `serial_number_id` (optional): Integer
  ID as a string, or the literal string `'null'` to match rows without
  that attribution (e.g. `bin_location_id='null'` finds un-binned stock)
- `limit` (optional, default 50) / `page` (optional)

**Returns:** Rows of (location_id, variant_id, bin_location_id, batch_id,
serial_number_id, quantity_in_stock / committed / expected). A `null`
bin_location_id means unassigned stock.

---

### list_storage_bins
List storage bins (bin locations) — the named bins within each location.
Live read against `GET /bin_locations`. Use for bin ID lookups on
`create_bin_transfer` / `modify_bin_transfer` rows and
`list_bin_inventory` filters.

**Parameters:**
- `location_id` (optional): Filter by location
- `bin_name` (optional): Exact match on bin name
- `include_deleted` (optional, default false)
- `limit` (optional, default 50) / `page` (optional)

---

### create_storage_bin
Create a storage bin within a location.

**Parameters:**
- `bin_name` (required): Name of the new bin (e.g. "A-01-02")
- `location_id` (required): Location the bin belongs to
- `preview` (optional, default true): true=preview, false=create

---

## Reference Data Tools

Parameterized search tools backed by the local cache (FTS5 with difflib
fallback). Each `list_*` tool accepts `query` (optional fuzzy search) and
`limit` (default 50, max 250). Outputs are bounded — passing `limit`
keeps even large reference catalogs from flooding agent context.

### list_locations
List or fuzzy-search warehouses and facilities by name. Returns id, name,
the is_primary flag, and a nested `address` object (line_1, line_2, city,
state, zip, country) when one is on file. Use the `id` value when creating
orders or filtering inventory queries.

**Parameters:**
- `query` (optional): Fuzzy match by name.
- `limit` (optional, default 50, max 250): Cap on rows returned.

**Returns:** `ListLocationsResponse` with `locations: [{id, name,
address: {line_1, line_2, city, state, zip, country} | null,
is_primary}]`, `total_count`, `query`.

---

### list_suppliers
List or fuzzy-search suppliers by name or code. Returns id, name, email,
phone, currency, and code. Use the `id` value when creating purchase
orders or setting a default supplier on a material. Use `get_supplier`
for the full-detail record.

**Parameters:**
- `query` (optional): Fuzzy match by name or code.
- `limit` (optional, default 50, max 250).

**Returns:** `ListSuppliersResponse` with `suppliers: [{id, name, email,
phone, currency, code}]`, `total_count`, `query`.

---

### get_supplier
Full-detail supplier record by id. Returns every cached field — contact
info, address, currency, payment terms, comment, and timestamps.

**Parameters:**
- `supplier_id` (required): Supplier id.

**Returns:** `GetSupplierResponse` with id, name, email, phone, currency,
code, comment, default_payment_terms, address fields (line_1, line_2,
city, state, zip, country), created_at, updated_at, deleted_at.

---

### list_tax_rates
List or fuzzy-search configured tax rates by name. Returns id, name, rate,
display name, and default-for-sales / default-for-purchases flags. Use
the `id` value when creating sales orders or purchase-order line items
with explicit tax assignments.

**Parameters:**
- `query` (optional): Fuzzy match by name.
- `limit` (optional, default 50, max 250).

**Returns:** `ListTaxRatesResponse` with `tax_rates: [{id, name, rate,
display_name, is_default_sales, is_default_purchases}]`, `total_count`,
`query`.

---

### list_operators
List or fuzzy-search manufacturing operators by name. Returns id and name.
Use the `id` value when assigning operators to manufacturing-order
operation rows or naming the packer on a sales order.

**Parameters:**
- `query` (optional): Fuzzy match by name.
- `limit` (optional, default 50, max 250).

**Returns:** `ListOperatorsResponse` with `operators: [{id, name}]`,
`total_count`, `query`.

---

### list_additional_costs
List or fuzzy-search the additional-cost catalog (freight, duties,
handling fees, etc.) by name. Returns id and name. Use the `id` value
when calling `modify_purchase_order` with `add_additional_costs=[...]`.
Pair with `list_tax_rates` for the matching `tax_rate_id`.

**Parameters:**
- `query` (optional): Fuzzy match by name.
- `limit` (optional, default 50, max 250).

**Returns:** `ListAdditionalCostsResponse` with `additional_costs: [{id,
name}]`, `total_count`, `query`.

---

## Cache Administration Tools

### rebuild_cache
Force-rebuild the local typed cache for one or more cached entity types.
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
  Allowed values cover transactional entities (`purchase_order`, `sales_order`,
  `manufacturing_order`, `stock_adjustment`, `stock_transfer`) and catalog
  entities (`variant`, `product`, `material`, `service`, `customer`,
  `supplier`, `location`, `tax_rate`, `operator`, `factory`,
  `additional_cost`).
- `preview` (optional, default true): true = report current row counts and
  last-synced timestamps without modifying anything; false = perform the
  destructive rebuild.

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

> **Note:** Reference data (suppliers, locations, tax rates, operators,
> additional costs) is exposed only as parameterized tools, not resources.
> Use `list_suppliers(query=...)`, `list_locations(query=...)`,
> `list_tax_rates(query=...)`, `list_operators(query=...)`,
> `list_additional_costs(query=...)`, and `get_supplier(supplier_id)`.
> The previous bulk-list resources (`katana://suppliers` etc.) were
> removed because they dumped every row as a single-line JSON blob, which
> floods agent context — searchable tools with bounded `limit` solve the
> same lookup needs without the size problem.

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
