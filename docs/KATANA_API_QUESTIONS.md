# Katana API Questions

Questions and inconsistencies discovered during P1-P4 OpenAPI spec alignment (Katana
spec dated 2026-01-20, 104 paths). Each was originally investigated against the live API
on 2026-02-07.

**Last swept:** 2026-05-12. Resolved entries are in the table at the bottom; each
remaining open entry has a "Last verified" line noting the date and method (spec-only vs
live-API).

______________________________________________________________________

## 1. Create/Update vs Response Schema Asymmetries

### 1.1 Material `serial_tracked` and `operations_in_sequence` not settable via API

**Status: CONFIRMED - not settable**

The Material GET response includes `serial_tracked` and `operations_in_sequence`, but
neither field appears in the Create or Update request schemas. By contrast, the Product
resource includes both fields in its Create and Update schemas.

**Investigation:** Attempted `PATCH /materials/{id}` with each field. Both returned 422
`additionalProperties` - the API actively rejects them on update. These are truly
read-only on materials, despite being writable on products.

**Conclusion:** Intentional API asymmetry between materials and products. Our spec is
correct as-is. This may be a product-line decision (materials inherit these properties
from the products they're consumed by), but it's worth confirming with Katana.

**Last verified:** 2026-05-07 (spec-only — `MaterialUpdateDto` in
`docs/upstream-specs/live-gateway.yaml` still excludes both fields; live-API
re-verification not re-run).

### 1.2 `MaterialConfig` schema requires `id` and `material_id` on CREATE

**Status: CONFIRMED — spec error; needs follow-up in our local spec**

`CreateMaterialRequest.configs` references the `MaterialConfig` schema, which has `id`
and `material_id` as required fields. These values don't exist yet when creating a new
material.

**Investigation (2026-02-07):** Created a material with configs containing only `name`
and `values` (no `id` or `material_id`). The API accepted it (200 OK) and returned the
created configs with server-generated identifier fields populated. (The original note
recorded `product_id` as the parent-ID field name on the response — possibly a typo,
possibly accurate if Katana's wire shape uses `product_id` even on a material's configs.
Worth confirming on the next live-API sweep tracked under #603.)

**Live spec (2026-05-07 cross-check):** `live-gateway.yaml` uses an inline
`ItemVariantConfigDto` (only `values` is required; `id` and `name` are optional).

**Status of fix in our local spec:** This entry's earlier conclusion claimed *"Our spec
already uses the simplified inline schema for create, which matches reality."* That's
not currently true: `docs/katana-openapi.yaml` `CreateMaterialRequest.configs` still
$refs the over-specified `MaterialConfig` schema. The reality and the upstream spec
agree on the simplified shape; our local spec hasn't been updated yet. **Action:**
follow-up spec PR to switch to the inline shape (or define a sibling
`MaterialConfigCreate` and ref it from `CreateMaterialRequest`).

**Last verified:** 2026-05-07 (spec-only).

### 1.3 Manufacturing Order cannot be linked to Sales Order via create/update

*Moved to the Resolved Issues table — `/manufacturing_order_make_to_order` is the
linking endpoint. Linking only happens at MO creation; there is no post-hoc link
endpoint by design.*

### 1.4 Purchase Order `status` in CREATE only accepts one value

*Moved to the Resolved Issues table — Katana now accepts `DRAFT` and `NOT_RECEIVED` on
`POST /purchase_orders`. The 2026-02-07 finding (only `NOT_RECEIVED`) is no longer
current; both `live-gateway.yaml` and our local `CreatePurchaseOrderInitialStatus` enum
list `[DRAFT, NOT_RECEIVED]` as of 2026-05-07.*

______________________________________________________________________

## 2. Field Naming Inconsistencies

### 2.1 Bin Location: `name` vs `bin_name`

**Status: INCONCLUSIVE - no data available**

The spec defines both `name` and `bin_name` for the `/bin_locations` resource (note: the
actual endpoint is `/bin_locations`, not `/storage_bins` as originally noted).

**Investigation:** `GET /bin_locations` returns 200 but with an empty list (no bin
locations configured in this account). The response is also a raw JSON array, not
wrapped in `{"data": [...]}` like other list endpoints.

**Conclusion:** Cannot verify field naming with no data. The raw-array response format
is another non-standard pattern worth noting. If bin locations are ever configured in
the test account, this should be re-investigated.

**Cross-reference:** The raw-array response shape (no `{"data": [...]}` wrapper) is now
tracked separately as #575
(`bug(client): /bin_locations returns bare array, not StorageBinListResponse wrapper`).
The `name` vs `bin_name` portion of this question remains open.

**Last verified:** 2026-05-07 (spec-only — no live data to test against).

### 2.2 `ProductOperationRow` uses `product_operation_row_id` instead of `id`

*Moved to the Resolved Issues table — confirmed real Katana inconsistency
(`product_operation_row_id` instead of the standard `id` field), our local spec mirrors
it, no follow-up needed.*

______________________________________________________________________

## 3. Read-Only Endpoints Missing Write Operations

**Status: CONFIRMED - write operations do not exist via API**

| Resource         | Endpoint            | GET | POST | PATCH | Result              |
| ---------------- | ------------------- | --- | ---- | ----- | ------------------- |
| Additional Costs | `/additional_costs` | 200 | 404  | -     | 3 items, read-only  |
| Factory          | `/factory`          | 200 | -    | 404   | Settings, read-only |
| Operators        | `/operators`        | 200 | -    | -     | Empty, not tested   |

**Investigation:**

- `/additional_costs`: Returns 3 system-defined items (`Shipping`, `Customs`, `Other`).
  `POST /additional_costs` returns 404. These appear to be system presets, not
  user-created.
- `/factory`: Returns factory settings (legal name, address, currency, default
  locations, inventory closing date). `PATCH /factory` returns 404. These are managed
  through the Katana UI only.
- `/operators`: Returns empty list (no operators configured). Cannot test POST without
  data to validate against.

**Conclusion:** These are intentionally read-only API endpoints. Additional costs are
system presets. Factory settings and operators are UI-managed. Our spec correctly
documents them as GET-only.

**MCP exposure update (2026-05-07):** PR #589 added `list_locations`, `list_suppliers`,
`list_tax_rates`, `list_operators`, and `list_additional_costs` MCP tools (read-only
wrappers around the existing `katana://...` resources). This doesn't change the API
surface — these endpoints remain GET-only on the Katana side; the new MCP tools just
make the read surface more discoverable to LLM agents.

**Last verified:** 2026-05-07 (spec-only — `live-gateway.yaml` shows only `get` for
`/factory`, `/operators`, and `/additional_costs`).

______________________________________________________________________

## 4. Nullable Field Semantics

*Section retired — only entry (§4.1 Variant `lead_time` / `minimum_order_quantity` null
semantics) was clarified during the original 2026-02-07 investigation; moved to the
Resolved Issues table.*

______________________________________________________________________

## 5. Non-Standard Patterns

### 5.1 `/demand_forecasts` doesn't follow any standard resource pattern

*Moved to the Resolved Issues table — confirmed Katana design choice (computation
endpoint, not CRUD resource); body requires `variant_id` + `location_id` + `periods` on
POST and DELETE; our spec mirrors it, no follow-up needed.*

______________________________________________________________________

## 6. PATCH Asymmetric Field-Wipe Behavior

### 6.1 `PATCH /purchase_orders/{id}` clears `additional_info` when omitted

**Status: CONFIRMED via wire-level reproduction on 2026-05-05**

`PATCH /purchase_orders/{id}` clears the PO's `additional_info` field to `""` whenever
the request body omits that field, while every other omitted field is correctly
preserved. This is asymmetric: the endpoint treats omitted `additional_info` as a
null-write but treats every other omitted field as a no-op.

**Reproduction (live API, account `factory.katanamrp.com`):**

1. Create PO 2708970 with `additional_info` populated. Confirmed via
   `GET /purchase_orders/2708970`:

   ```json
   {
     "id": 2708970,
     "additional_info": "CANARY-PATCH-ECHO: Test if explicitly echoing additional_info in PATCH body preserves it.",
     "order_no": "TEST-505-PATCH-ECHO-2026-05-05",
     "supplier_id": 1302070,
     "currency": "USD",
     "expected_arrival_date": "2026-05-19T15:24:10.163Z",
     "status": "NOT_RECEIVED"
   }
   ```

1. Send a minimal PATCH (single-field rename) with no `additional_info` key:

   ```http
   PATCH /purchase_orders/2708970
   Content-Type: application/json

   {"order_no": "TEST-505-MODIFY-NONSTATUS-2026-05-05-RENAMED"}
   ```

   Response: 200 OK.

1. Re-fetch immediately. Result:

   ```json
   {
     "id": 2708970,
     "additional_info": "",
     "order_no": "TEST-505-MODIFY-NONSTATUS-2026-05-05-RENAMED",
     "supplier_id": 1302070,
     "currency": "USD",
     "expected_arrival_date": "2026-05-19T15:24:10.163Z",
     "status": "NOT_RECEIVED"
   }
   ```

   `additional_info` is wiped to empty. Every other omitted field is preserved. The
   PATCH body verifiably did not include `additional_info`. (We separately verified the
   wire shape for a similar single-field rename PATCH by intercepting the httpx request
   — the body was exactly `{"order_no":"TEST-RENAMED"}` (27 bytes), no `additional_info`
   key in any form. The example above uses the longer
   `TEST-505-MODIFY-NONSTATUS-2026-05-05-RENAMED` value but the wire shape is the same —
   only the changed field is present in the body.)

1. Conversely, sending the same PATCH with `additional_info` echoed in the body
   preserves the value:

   ```http
   PATCH /purchase_orders/2708970
   Content-Type: application/json

   {
     "order_no": "TEST-505-MODIFY-NONSTATUS-2026-05-05-RENAMED",
     "additional_info": "<the existing value>"
   }
   ```

   Result: `additional_info` retained.

**Expected behavior:** Per RFC 7396 (JSON Merge Patch) and standard PATCH semantics,
omitted fields should be left unchanged. The asymmetry — every other omitted field is
left alone, only `additional_info` is treated as a null-write — strongly suggests an
unintended platform-side normalization rather than a deliberate API contract.

**Impact on integrators:** Any client that PATCHes a PO without echoing
`additional_info` will silently destroy user-entered notes (UPS tracking links, customer
references, supplier remarks, etc.). Several of our agent-driven workflows have hit this
in production — including the common case of correcting a single header field after the
fact.

**Workaround in our MCP wrapper (this repo):** Always include the existing
`additional_info` value in the PATCH body when the caller didn't change it. See
`_build_update_header_request` in
`katana_mcp_server/src/katana_mcp/tools/foundation/purchase_orders.py` (introduced in PR
#515).

### 6.2 Same wipe-on-PATCH affects every entity with `additional_info`

**Status: CONFIRMED platform-wide via live-API reproduction on 2026-05-05**

We followed up on §6.1 by testing every other Katana entity that exposes
`additional_info`. The same asymmetric wipe reproduces on every one we could test:

| Entity                 | PATCH endpoint                     | `additional_info` after omitted PATCH |
| ---------------------- | ---------------------------------- | ------------------------------------- |
| PurchaseOrder (§6.1)   | `PATCH /purchase_orders/{id}`      | wiped to `""`                         |
| **Material**           | `PATCH /materials/{id}`            | **wiped to `""`**                     |
| **Product**            | `PATCH /products/{id}`             | **wiped to `""`**                     |
| **ManufacturingOrder** | `PATCH /manufacturing_orders/{id}` | **wiped to `""`**                     |
| **StockAdjustment**    | `PATCH /stock_adjustments/{id}`    | **wiped to `""`**                     |

Each was verified by:

1. Creating a test record with `additional_info` populated.
1. Issuing a single-field PATCH on a different header field (rename / status change).
1. Re-fetching and observing `additional_info: ""` post-PATCH.
1. Cleaning up the test record.

Test records used (all deleted post-verification): Material 17042013, Product 17042018,
MO 16647058, StockAdjustment 2394711.

Two other candidates couldn't be tested in the original round and were noted as blocked.
Both blockers have since shipped — these are now testable, follow-up verification
pending:

- **SalesOrder** — was blocked by missing `PENDING` in `SalesOrderStatus`. Fixed in PR
  #524 (closed #516). Ready for re-test against the wipe-on-PATCH question.
- **StockTransfer** — was blocked by `create_stock_transfer` returning opaque 422 on the
  execute path (#499 / #517). The 422 opacity was fixed in PR #578 (rewrote
  `ValidationErrorDetail` to match Katana's Ajv-style wire shape). Ready for re-test.

A live-API re-run that extends the §6.2 wipe table to cover SO and ST should be paired
with the broader doc sweep tracked under #603.

**Conclusion:** This is a platform-wide PATCH-merge bug, not a one-off on PurchaseOrder.
Whatever is treating omitted `additional_info` as a null-write is doing so consistently
across at least 5 distinct PATCH endpoints, strongly suggesting a shared serialization
or normalization layer at Katana's side.

**Workaround in our MCP wrapper:** Same pattern as §6.1, applied to each affected
entity:

- `_build_update_header_request` in `katana_mcp_server/.../tools/foundation/items.py`
  (covers material/product/service)
- `_build_update_header_request` in
  `katana_mcp_server/.../tools/foundation/manufacturing_orders.py`
- `_update_stock_adjustment_impl` in
  `katana_mcp_server/.../tools/foundation/inventory.py` (pre-fetches the adjustment via
  `get_all_stock_adjustments(ids=[id])` only when the caller didn't supply
  `additional_info`)

All four echo the existing value when the caller doesn't change it. Idempotent — if
Katana fixes the asymmetry, the echo becomes a no-op write.

**Asks:**

1. Confirm whether the wipe is intentional across all five entities. If yes, document it
   on each PATCH endpoint (we'd update our spec accordingly).
1. If unintentional, fix the asymmetry at the shared layer (we suspect a single
   normalization step given how uniformly it reproduces) so omitted `additional_info` is
   treated as a no-op like every other omitted field.
1. If other entity types (`PATCH /sales_orders/{id}`,
   `PATCH /manufacturing_orders/{id}`, etc.) have the same behavior on their notes /
   free-text fields, please flag them — we haven't audited those yet and would prefer to
   fix all of them in one pass rather than discovering each one in production.

______________________________________________________________________

## 7. Stock Transfer & Stock Adjustment — Row Immutability + DELETE Behavior

### 7.1 Stock-transfer / stock-adjustment rows are immutable post-creation

**Status: CONFIRMED via 3-source spec agreement on 2026-05-07**

`PATCH /stock_transfers/{id}` and `PATCH /stock_adjustments/{id}` both accept *header
fields only* — neither schema includes a `stock_transfer_rows` / `stock_adjustment_rows`
property, and both declare `additionalProperties: false`. There are also no row-level
endpoints (`/stock_transfer_rows/{id}`, `/stock_adjustment_rows/{id}`) on any source we
have. Confirmed across:

- `docs/katana-openapi.yaml` (local)
- `docs/upstream-specs/live-gateway.yaml` (Katana's API gateway)
- `docs/upstream-specs/readme-portal.yaml` (Katana's public portal)

**Practical implication:** Once a stock transfer or stock adjustment is created, its
variant + quantity rows can't be edited. The only API-sanctioned correction paths are:

1. Post compensating `create_stock_adjustment` call(s) that reverse or amend the prior
   inventory delta. The shape depends on which entity got it wrong:

   - **Stock adjustment** is already location-scoped, so a single compensating
     adjustment at the same `location_id` undoes the original delta.
   - **Stock transfer** moves inventory between two locations, so reversing it requires
     **two** compensating adjustments — one at the source location to restore the
     outflow, one at the target location to remove the inflow. (Both adjustments should
     share matching `reason` text so the audit trail traces back to the same correction
     event.)

   The original record stays as the audit trail of what was *intended*; the compensating
   adjustment(s) record what was *fixed*. This is the path the MCP `correct_*` family
   deliberately does **not** cover for ST/SA — the reasoning is captured in #533 and the
   (in-flight) help-resource update tracked under #602.

1. `DELETE` the record and re-create with corrected rows — see open question §7.2.

**Why this is asymmetric with PO/SO/MO:** Purchase orders, sales orders, and
manufacturing orders all expose row-level PATCH endpoints (`/purchase_order_rows/{id}`,
`/sales_order_rows/{id}`, `/manufacturing_order_recipe_rows/{id}`), which is what makes
the reopen → modify → restore pattern work for them (`correct_manufacturing_order` /
`correct_sales_order` / `correct_purchase_order` shipped in PR #536, #546, #595). Stock
transfer and stock adjustment have no equivalent surface, so the same pattern can't
apply.

**Asks:**

1. Confirm whether row-level CRUD is intentionally absent from the API surface for
   stock_transfer and stock_adjustment, or if it's an oversight.
1. If a future DTO change will add `stock_transfer_rows` / `stock_adjustment_rows` to
   the PATCH body (or expose row-level endpoints), please flag it — our spec + tools
   would track that change.

### 7.2 DELETE behavior on already-applied stock_transfer / stock_adjustment is unverified

**Status: OPEN — needs live-API verification**

Both `DELETE /stock_transfers/{id}` and `DELETE /stock_adjustments/{id}` are documented
on every spec source, but the **response code disagrees across sources**:

- `docs/katana-openapi.yaml` (local) → `204`
- `docs/upstream-specs/readme-portal.yaml` (Katana's public portal) → `204`
- `docs/upstream-specs/live-gateway.yaml` (Katana's API gateway) → `200`

The two upstream sources disagree, so we don't actually know what the live API returns
on success. Worth resolving as part of the live-API check below — most likely `204`
(matching the public portal and what our spec already declares), with the gateway spec
out of sync, but worth confirming. (If it's `200`, the spec needs to declare a body
schema for the DELETE response, since `204` means no content.)

What's also unclear is the inventory-effect side of the delete:

1. **Stock transfers in `received` status** have already moved inventory from source →
   target location. Does DELETE reverse the inventory move, leave it in place, or
   422-refuse?
1. **Stock adjustments** apply their inventory delta on creation. Does DELETE reverse
   the delta?
1. **Audit-trail preservation:** Even if DELETE 204s, do the historical
   `inventory_movements` rows associated with the deleted record stay queryable, or are
   they removed too?

**Why it matters:** A `correct_stock_transfer` or `correct_stock_adjustment` tool
implemented via "delete + recreate with corrected rows" depends on these behaviors.
Without confirmation, we don't know if the workaround is safe to expose or whether it'd
silently corrupt inventory. If reversal is automatic, delete-and-recreate becomes a
viable correction pattern; if not, the compensating-adjustment pattern (§7.1) remains
the only safe option.

**Asks:**

1. Confirm the canonical DELETE success status code (`200` or `204`) so the spec sources
   can be reconciled.
1. Document the DELETE side-effects on each entity per status (where applicable):
   - Does DELETE on a `received` stock_transfer reverse the inventory move?
   - Does DELETE on any stock_adjustment reverse the inventory delta?
   - Are historical `inventory_movements` rows preserved or removed when their parent is
     deleted?
1. If reversal is *not* automatic, document that explicitly so we can warn operators in
   the MCP wrapper before they delete a record assuming the inventory effect will roll
   back.

______________________________________________________________________

## Resolved Issues (FYI)

Issues discovered and fixed during P1-P4 alignment, documented here for reference:

| Issue                                                                              | Resolution                                                                                                                                                               |
| ---------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| PurchaseOrderAccountingMetadata used camelCase field names                         | Fixed to snake_case to match actual API responses                                                                                                                        |
| StockAdjustment field renames (`adjustment_date` -> `stock_adjustment_date`, etc.) | Updated spec to match actual field names                                                                                                                                 |
| SalesOrderFulfillment schema overhaul                                              | ~8 fields removed, ~10 added to match actual API                                                                                                                         |
| SalesReturnRow field corrections                                                   | Updated to match actual response structure                                                                                                                               |
| 7 schemas incorrectly used UpdatableEntity                                         | Upgraded to DeletableEntity where DELETE endpoints exist                                                                                                                 |
| PriceList phantom fields (`currency`, `end_date`, etc.)                            | Removed fields not present in actual API responses                                                                                                                       |
| StockTransfer/StockAdjustment had status enums                                     | Removed - these resources use free-form status strings                                                                                                                   |
| §1.3 — MO ↔ SO linking via PATCH                                                   | API design: linking is one-way at MO creation via `POST /manufacturing_order_make_to_order`. No post-hoc link endpoint exists by design.                                 |
| §1.4 — PO CREATE `status` only accepted `NOT_RECEIVED` (2026-02-07)                | Katana now accepts both `DRAFT` and `NOT_RECEIVED` (verified spec-only against `live-gateway.yaml` and our local `CreatePurchaseOrderInitialStatus` enum on 2026-05-07). |
| §4.1 — Variant `lead_time` / `minimum_order_quantity` null semantics               | Clarified — `null` means "not set" (distinct from `0`). API correctly distinguishes.                                                                                     |
| §2.2 — `ProductOperationRow` PK is `product_operation_row_id` (not `id`)           | Confirmed real Katana inconsistency vs every other resource. Our local spec mirrors it; no spec change needed.                                                           |
| §5.1 — `/demand_forecasts` is a computation endpoint, not a CRUD resource          | POST and DELETE bodies both require `variant_id` + `location_id` + `periods` (not just an identifier). Mental model: it's a calculation API. Our spec mirrors it.        |
