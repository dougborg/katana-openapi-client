# Katana API Questions

Questions for the Katana API team, with reproduction evidence and the current status of
our client workarounds. The log began with the 2026-02-07 P1-P4 spec investigation.

**Last reviewed:** 2026-09-21 against the local spec, the committed 2026-09-18 upstream
spec snapshots, current client/MCP code, and the live test-tenant findings from
2026-09-20 and the material-price / serial-mint probes from 2026-09-21. Entries
distinguish fresh test-tenant reproductions from historical observations that were not
rerun. Spec agreement does not establish live behavior or confirm that an API design is
intentional.

### Questions to prioritize with Katana

| Topic                                                                                                           | Question                                                                                 | Evidence                                                       |
| --------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| [BOM-row HTTP 500](#8-nonexistent-bom-row-update-returns-http-500)                                              | Can missing-row updates return a domain error or 404 instead of 500?                     | Test-tenant reproduction, 2026-09-20                           |
| [Notes cleared on PATCH](#6-patch-asymmetric-field-wipe-behavior)                                               | Is clearing omitted `additional_info` intentional?                                       | Five historical wipes; SO/ST preserve notes on 2026-09-20      |
| [Omitted batch quantity](#63-sales-order-row-batch-quantity-omission-resets-the-allocation-to-zero)             | Should an allocation with no quantity reset to zero, preserve the value, or be rejected? | Test-tenant reproduction, 2026-09-20                           |
| [Stock deletion effects](#72-delete-behavior-on-already-applied-stock_transfer--stock_adjustment-is-unverified) | Does deletion reverse inventory, and what happens to movement history?                   | Live inventory reads inconsistent; deletion effects unverified |
| [Custom-field availability](#15-custom-field-request-formats-and-account-availability)                          | How can integrations discover which resources support definition-keyed maps?             | Gateway checks and account-feature rejection, 2026-09-20       |
| [Sales-return filtering](#52-get-sales_returnssales_order_idn-silently-ignores-the-filter)                      | Which filter is canonical, and can the portal and gateway docs agree?                    | Controlled test-tenant comparison, 2026-09-20                  |
| [Material sales price](#16-material-creation-rejects-nested-sales-price)                                        | Can initial material selling prices be set atomically during creation?                   | Test-tenant create/PATCH comparison, 2026-09-21                |
| [Serial mint 404](#17-serial-mint-reports-an-existing-make-to-order-mo-as-missing)                              | Why does serial mint reject an MO recognized by both read endpoints?                     | Two test-tenant fixtures, 2026-09-21                           |

Local-only schema work is identified separately below. The remaining historical live
checks stay tracked in
[#603](https://github.com/dougborg/katana-openapi-client/issues/603).

______________________________________________________________________

## 1. Create/Update vs Response Schema Asymmetries

### 1.1 Material `serial_tracked` and `operations_in_sequence` not settable via API

**Status: HISTORICALLY REJECTED; still excluded by current request schemas**

The Material GET response includes `serial_tracked` and `operations_in_sequence`, but
neither field appears in the Create or Update request schemas. By contrast, the Product
resource includes both fields in its Create and Update schemas.

**Investigation:** Attempted `PATCH /materials/{id}` with each field. Both returned 422
`additionalProperties` - the API actively rejects them on update. These are truly
read-only on materials, despite being writable on products.

**Ask:** Confirm whether the asymmetry between materials and products is intentional,
and document how integrations should configure these material properties. The rejection
alone does not establish inheritance or the product rationale.

**Last verified:** 2026-09-20 (spec-only — both material create/update schemas still
exclude these fields in the local spec and committed gateway snapshot). Last live
reproduction: 2026-02-07; not rerun in this review.

### 1.2 Material configuration CREATE and UPDATE contracts

*Resolved in [PR #1068](https://github.com/dougborg/katana-openapi-client/pull/1068).
The verified contract and cleanup evidence are retained below under Resolved Issues.*

### 1.3 Manufacturing Order cannot be linked to Sales Order via create/update

*Moved to the Resolved Issues table — `/manufacturing_order_make_to_order` is the
documented linking endpoint, used at MO creation. No post-hoc linking endpoint is
documented.*

### 1.4 Purchase Order `status` in CREATE only accepts one value

*Moved to the Resolved Issues table — Katana now accepts `DRAFT` and `NOT_RECEIVED` on
`POST /purchase_orders`. The 2026-02-07 finding (only `NOT_RECEIVED`) is no longer
current; both `live-gateway.yaml` and our local `CreatePurchaseOrderInitialStatus` enum
list `[DRAFT, NOT_RECEIVED]` as of 2026-05-07.*

### 1.5 Custom-field request formats and account availability

**Status: FORMATS VERIFIED; account capability discovery needs clarification**

The 2026-09-20 probes distinguish two request formats:

- Seventeen BOM, contact, manufacturing, and purchasing create/update DTOs accept
  object/null at the gateway and reject legacy arrays.
- Variant create/update and service update accept legacy arrays and UUID-keyed scalar
  maps at the gateway. A nonempty valid map reaches a domain error on the test account:
  `The object custom fields format is not available for this account`.
- Empty-object creation and explicit-null updates succeeded on test-owned customers and
  suppliers. Those contacts were deleted afterward. This does not prove that nonempty
  maps can be persisted on every endpoint or account.

**Local status:** Request models and conversion handling were corrected in
[PR #1062](https://github.com/dougborg/katana-openapi-client/pull/1062), closing #1030.
MCP custom-field authoring remains tracked separately in #806. Definition discovery and
management landed in
[PR #1066](https://github.com/dougborg/katana-openapi-client/pull/1066).

**Search/read checks:** Both sales-order search endpoints accept
`filter: {"custom_fields.<uuid>": null}` and reject the camelCase `customFields` key
with 422. The test tenant has no definitions, so this verifies filter syntax, not
matching populated values. The bounded read audit in
[PR #1071](https://github.com/dougborg/katana-openapi-client/pull/1071) observed absent
custom fields on product/material lists and details, empty arrays on variants, and no
services to inspect. Those observations do not establish account-wide map support.

**Asks:** Document the format and null/empty-object behavior per resource; explain the
account feature requirements and how an integration can discover them before writing.

**Last verified:** 2026-09-20 (live test tenant; see
[`test_custom_field_formats_live.py`](../tests/integration/test_custom_field_formats_live.py)).

### 1.6 Material creation rejects nested sales price

**Status: VERIFIED; use a separate variant update**

On 2026-09-21, test factory `104008` rejected `POST /materials` with
`variants[0].sales_price` (422, `additionalProperties`, unexpected `sales_price`).
Creating the same sellable material without that field succeeded. A subsequent
`PATCH /variants/{id}` with `{"sales_price": 12.34}` succeeded and GET confirmed the
value. `POST /products` accepted the nested price. The gateway snapshot also excludes
`sales_price` from `CreateMaterialDto.variants`.

**Ask:** Is this asymmetry intentional? Can material creation accept its initial selling
price atomically, as product creation does? Until then, integrations need to report
partial success if the separate price update fails, preserving the new IDs so callers do
not repeat creation. Client/MCP correction is tracked in
[#1083](https://github.com/dougborg/katana-openapi-client/issues/1083).

The SDT material `18022413` and product `18022414` were deleted; the tenant-scoped
cleanup ledger has no pending records.

### 1.7 Serial mint reports an existing make-to-order MO as missing

**Status: LIVE BLOCKER; fulfillment re-verification could not run**

On 2026-09-21, two independent SDT fixtures in test factory `104008` created
serial-tracked products, sales orders, and linked make-to-order manufacturing orders.
`POST /serial_numbers` with `resource_type: ManufacturingOrder` returned 404
`manufacturing order <id> not found` for MOs `19209084` and `19209103`.

For the second fixture, `GET /manufacturing_orders/19209103` returned 200 with the
correct variant and SO-row link, and `GET /serial_numbers` for that MO returned 200 with
an empty list. Retrying the serial POST after those readbacks still returned 404. The
serial string was `SDT-ec58bea6-MTO` (within the documented length limit). All requests
were awaited; no sleeps or timing assumptions were added. This does not rule out longer
eventual consistency, but the normal resource read reports it ready.

A standalone-MO control reproduced the same failure: serial mint for MO `19209707`
returned 404, while its detail and resource-scoped serial list returned 200. Thus the
new mint failure is not limited to make-to-order linking. Its product and MO were also
deleted; no serials were minted in any of these probes.

**Ask:** Why does the serial-mint endpoint reject an MO that the resource and serial
list endpoints recognize? Is there a new prerequisite or an endpoint migration?

This blocks the fresh
[make-to-order fulfillment probe](escalations/katana-serial-fulfillment-gap.md) tracked
in [#784](https://github.com/dougborg/katana-openapi-client/issues/784). We did not
reach production or fulfillment, so the historical delivery gap remains unverified. No
serials were deleted as a workaround. All eight temporary parent resources were deleted
successfully through tenant-scoped ledgers.

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

**Local status:** The bare-array parser was fixed in
[PR #903](https://github.com/dougborg/katana-openapi-client/pull/903), closing #575
after a 2026-06-03 live check. That issue is resolved; it did not establish the field
names on populated responses. The local `StorageBin` schema describes `name` for lists
and `bin_name` for requests/detail, but still requires `bin_name`.

**Ask:** Confirm the canonical list/detail names and whether `bin_name` is always
present in a nonempty list response.

**Last verified:** 2026-09-20 (local schema and merged fix review). Populated-response
field naming remains unverified by the evidence in this log.

### 2.2 `ProductOperationRow` uses `product_operation_row_id` instead of `id`

*Moved to the Resolved Issues table — confirmed real Katana inconsistency
(`product_operation_row_id` instead of the standard `id` field), our local spec mirrors
it, no follow-up needed.*

______________________________________________________________________

## 3. Read-Only Endpoints Missing Write Operations

**Status: NO WRITE OPERATIONS DOCUMENTED; historical endpoint probes below**

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

**Ask:** Confirm whether these resources are intentionally read-only through the public
API. The observed additional-cost names do not prove that the catalog is fixed, and POST
on `/operators` was not tested. Current specs document only GET for all three.

**MCP exposure update (2026-05-07):** PR #589 added `list_locations`, `list_suppliers`,
`list_tax_rates`, `list_operators`, and `list_additional_costs` MCP tools (read-only
wrappers around the existing `katana://...` resources). This doesn't change the API
surface — these endpoints remain GET-only on the Katana side; the new MCP tools just
make the read surface more discoverable to LLM agents.

**Last verified:** 2026-09-20 (spec-only — local, gateway, and portal snapshots still
show only GET for these paths). The endpoint probes above date to 2026-02-07.

### 3.1 Batch fixture lifecycle has no documented DELETE endpoint

**Status: DOCUMENTATION GAP — deletion/retirement support needs clarification**

The published batch surface has no documented DELETE operation. For the #1053 live
tests, one reusable batch and its test product were explicitly approved for retention;
temporary orders are deleted through a tenant-scoped artifact ledger.

**Ask:** Is there a supported way to delete or retire an unused test batch, including
its inventory and audit-history implications? If retention is required, document that
lifecycle constraint so integrations can plan fixture cleanup.

**Last verified:** 2026-09-20 (spec review and test-fixture setup; no undocumented
deletion endpoint was attempted).

______________________________________________________________________

## 4. Nullable Field Semantics

*Section retired — only entry (§4.1 Variant `lead_time` / `minimum_order_quantity` null
semantics) was clarified during the original 2026-02-07 investigation; moved to the
Resolved Issues table.*

______________________________________________________________________

## 5. Non-Standard Patterns

### 5.1 `/demand_forecasts` doesn't follow any standard resource pattern

*Moved to the Resolved Issues table — modeled as a computation endpoint, rather than a
CRUD resource; body requires `variant_id` + `location_id` + `periods` on POST and
DELETE; our spec mirrors it, no follow-up needed.*

### 5.2 `GET /sales_returns?sales_order_id=N` silently ignores the filter

**Status: RECONFIRMED on the test tenant, 2026-09-20; client correction in
[PR #1070](https://github.com/dougborg/katana-openapi-client/pull/1070)**

The server accepts several unknown filter names with HTTP 200 and returns the unfiltered
collection. The historical 2026-05-14 production observation of an ignored
`sales_order_id` filter was reproduced with two distinct, owned SDT order/return pairs.
An empty result was not used as the sole evidence of filtering.

| Query key                            | Observed behavior                                        |
| ------------------------------------ | -------------------------------------------------------- |
| `order_no`                           | Filters by the **return order's** number                 |
| `return_location_id`                 | Filters by return location                               |
| `status`, `refund_status`            | Exclude the owned returns when the status does not match |
| `order_return_date_min`              | Separates returns with distinct return dates             |
| `sales_order_id`                     | Ignored; both owned returns remain                       |
| `sales_order_no`                     | Also ignored, despite appearing in the gateway snapshot  |
| `return_order_no`, `return_date_min` | Ignored legacy/portal names                              |

The gateway also declares the paired `order_return_date_max` bound; the client exposes
that canonical name rather than `return_date_max`. The committed regression directly
exercises the minimum-bound comparison.

**Client handling:** Replace `return_order_no` with `order_no` and `return_date_min/max`
with `order_return_date_min/max`. Remove the ineffective generated `sales_order_id`
parameter. Consumers needing the source-order relationship must fetch all pages and
filter each return's `sales_order_id` locally. A return order number is not a sales
order ID or sales order number. The MCP list/get/delete follow-up is tracked in #740.

**Ask:** Document a supported source-sales-order filter, if one exists, and reconcile
the portal and gateway query names. In particular, the gateway's `sales_order_no`
declaration does not match the observed behavior. Rejecting unknown filters would help
integrations detect misspellings instead of silently processing unrelated returns.

The investigation created twelve temporary resources in total (six returns and six sales
orders); all were ledgered and deleted, with no pending cleanup. The regression in
`tests/integration/test_sales_return_filters_live.py` reads all pages and checks its
owned IDs so unrelated tenant records cannot affect the result.

**Last verified:** 2026-09-20 (controlled live test-tenant comparisons; gateway and
portal snapshots reviewed separately).

______________________________________________________________________

## 6. PATCH Asymmetric Field-Wipe Behavior

### 6.1 `PATCH /purchase_orders/{id}` clears `additional_info` when omitted

**Status: CONFIRMED via wire-level reproduction on 2026-05-05**

`PATCH /purchase_orders/{id}` clears the PO's `additional_info` field to `""` whenever
the request body omits that field, while the other fields checked in the reproduction
are preserved. This is asymmetric: the omitted `additional_info` changes to an empty
string even when the caller only renames the order.

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

   `additional_info` is wiped to empty. The other fields shown are preserved. The PATCH
   body verifiably did not include `additional_info`. (We separately verified the wire
   shape for a similar single-field rename PATCH by intercepting the httpx request — the
   body was exactly `{"order_no":"TEST-RENAMED"}` (27 bytes), no `additional_info` key
   in any form. The example above uses the longer
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

**Expected behavior:** Preserve omitted `additional_info`, consistent with the other
fields checked in these probes, or explicitly document replacement behavior. These
requests use `application/json`; HTTP PATCH alone does not establish that the endpoint
implements JSON Merge Patch. The shared cause of the observed wipe is unconfirmed.

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

**Last verified:** 2026-05-05 (live wire-level reproduction). Reviewed 2026-09-20: the
MCP echo workaround remains in place through `patch_additional_info`; this review did
not rerun the upstream behavior.

### 6.2 Same wipe-on-PATCH affects five tested entity types

**Status: REPRODUCED ON FIVE ENTITY TYPES on 2026-05-05; broader coverage unverified**

We followed up on §6.1 by testing four other entities that expose `additional_info`. The
same asymmetric wipe reproduced on each:

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

**Fresh extension (2026-09-20):** Sales orders and stock transfers **preserve** nonempty
`additional_info` when a PATCH changes only `order_no` or `stock_transfer_number`,
respectively. Both the PATCH response and subsequent GET retained the notes. Temporary
SDT records were ledgered and deleted. This completes the two missing behavior probes
from #531; it does not establish that the five historical wipes above have been fixed.
The old production-tenant orphan cleanup in #531 was not attempted by these test-tenant
probes.

**Conclusion:** The May behavior is not universal across PATCH endpoints. A shared
serialization cause remains a hypothesis. The five historical cases were not rerun.

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

These paths share `patch_additional_info` in
[`tools/_modification.py`](../katana_mcp_server/src/katana_mcp/tools/_modification.py).
They echo the existing nonempty value when the caller doesn't change it. This prevents
the observed wipe but is not an atomic read-modify-write: a concurrent edit between the
read and PATCH could still be overwritten.

**Asks:**

1. Confirm whether the wipe is intentional across all five entities. If yes, document it
   on each PATCH endpoint (we'd update our spec accordingly).
1. If unintentional, fix the asymmetry so omitted `additional_info` is preserved. A
   shared implementation may explain the similar results, but its location and cause
   need investigation by Katana.
1. Explain the resource-specific difference: the September sales-order and
   stock-transfer probes preserve omitted notes, unlike the five May cases.

**Last verified:** 2026-09-20 for SO/ST preservation and workaround review; 2026-05-05
for the five historical wipes. The regression is
`tests/integration/test_stock_lifecycle_contract_live.py`.

### 6.3 Sales-order-row batch quantity omission resets the allocation to zero

**Status: REPRODUCED on the live test tenant, 2026-09-20**

For an existing allocation with quantity 1, this update succeeds and returns quantity 0:

```http
PATCH /v1/sales_order_rows/{test_row_id}
Content-Type: application/json

{"batch_transactions": [{"batch_id": 123}]}
```

Here `123` is an illustrative batch ID; the probe used the approved reusable fixture.
Explicitly setting quantity to 1 and then omitting it again reproduces the reset. The
temporary sales order was deleted after the test.

Omission is not interchangeable across endpoints: production-ingredient batch
allocations without quantity are rejected with
`Traceability entries without a serial number must provide a positive quantity`. That
check used a nonexistent ingredient plus a quantity-bearing lookup control.

**Local status:**
[PR #1058](https://github.com/dougborg/katana-openapi-client/pull/1058) closed #1053 by
modeling optional quantity specifically for sales-row updates and keeping it required
for production-ingredient batch allocations.

**Ask:** Document whether the sales-row allocation array is treated as replacement data
and whether an omitted quantity is intentionally defaulted to zero. Integrations need to
distinguish this from preserving the existing quantity or rejecting omission.

**Last verified:** 2026-09-20 (live test tenant;
[`test_batch_quantity_live.py`](../tests/integration/test_batch_quantity_live.py)).

______________________________________________________________________

## 7. Stock Transfer & Stock Adjustment — Row Immutability + DELETE Behavior

### 7.1 Stock-transfer / stock-adjustment rows are immutable post-creation

**Status: NO ROW-EDIT SURFACE in the three reviewed specs, 2026-09-20**

`PATCH /stock_transfers/{id}` and `PATCH /stock_adjustments/{id}` both accept *header
fields only* — neither schema includes a `stock_transfer_rows` / `stock_adjustment_rows`
property, and both declare `additionalProperties: false`. There are also no row-level
endpoints (`/stock_transfer_rows/{id}`, `/stock_adjustment_rows/{id}`) on any source we
have. Confirmed across:

- `docs/katana-openapi.yaml` (local)
- `docs/upstream-specs/live-gateway.yaml` (Katana's API gateway)
- `docs/upstream-specs/readme-portal.yaml` (Katana's public portal)

**Practical implication:** The documented API cannot edit existing variant/quantity
rows. Potential correction approaches need to account for the inventory already moved:

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
   help-resource follow-up tracked under #602, which remains open.

1. `DELETE` the record and re-create with corrected rows — a candidate only after the
   inventory and history effects in §7.2 are verified. The presence of a DELETE endpoint
   alone is insufficient evidence that this is a safe correction workflow.

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

**Last verified:** 2026-09-20 (spec-only — local spec and committed gateway/portal
snapshots agree; no live row-edit attempt in this review).

### 7.2 DELETE behavior on already-applied stock_transfer / stock_adjustment is unverified

**Status: OPEN — deletion effects remain unverified after bounded live probes**

Both `DELETE /stock_transfers/{id}` and `DELETE /stock_adjustments/{id}` are documented
on every spec source, but the **response code disagrees across sources**:

- `docs/katana-openapi.yaml` (local) → `204`
- `docs/upstream-specs/readme-portal.yaml` (Katana's public portal) → `204`
- `docs/upstream-specs/live-gateway.yaml` (Katana's API gateway) → `200`

The September cleanup ledger records successful deletion of all test-owned artifacts,
but does not retain HTTP statuses. It cannot settle this response-code discrepancy or
the inventory effects of deleting a reliably observed applied transaction.

**Live probe limit (2026-09-20):** A non-batch-tracked, non-serial-tracked temporary
variant had a +2 stock-adjustment movement visible in every one of eight request-driven
snapshots, while inventory remained zero. Another temporary variant did show the +2
balance. Because the setup state did not reliably converge, the probe stopped before
creating a further transfer. Immediate movement/history snapshots from earlier attempts
are not evidence of settled reversal or retention. All temporary products and parent
transactions were ledgered and cleaned up; no arbitrary sleeps were introduced.

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
Without confirmation, we cannot recommend delete-and-recreate as a verified correction
workflow. Automatic reversal would still require checking status transitions, retained
links/history, and failure recovery before implementing a multi-step correction.
Compensating adjustments also need before/after inventory checks.

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

**Last verified:** 2026-09-20 (successful cleanup and inconsistent setup reads;
committed spec comparison). Inventory reversal and settled audit-history effects remain
unverified. The team should clarify consistency and completion signals before
delete-and-recreate guidance is offered.

______________________________________________________________________

## 8. Nonexistent BOM-row update returns HTTP 500

**Status: REPRODUCED on the live test tenant, 2026-09-20**

Updating a nonexistent BOM row with an empty custom-field object returns an internal
server error:

```http
PATCH /v1/bom_rows/-1
Content-Type: application/json

{"custom_fields": {}}
```

```http
HTTP/1.1 500 Internal Server Error
```

```json
{
  "error": {
    "statusCode": 500,
    "message": "Internal Server Error",
    "code": "ERR_NON_2XX_3XX_RESPONSE"
  }
}
```

Sending `{"custom_fields": null}` produces the same status and error code. The target ID
is deliberately nonexistent; these probes did not modify an existing record.

**Controls:** An invalid array, `{"custom_fields": []}`, returns HTTP 422 with a
`/custom_fields` type error. Supplying an independently invalid quantity with the
object/null forms also produces gateway validation HTTP 422. This is consistent with the
500 occurring after schema validation; it does not identify the failing internal
operation.

**Expected behavior / ask:** Return a documented missing-row response (404 or an
appropriate domain validation error) instead of HTTP 500. Please confirm the canonical
status and fix the internal failure for both object and null input.

**Local test handling:** The custom-field format probe uses an independently invalid
quantity to stay at gateway validation and avoid the failing lookup. It still requires
the quantity type error and absence of custom-field errors; it does not count HTTP 500
as success or add retries/waits to hide the failure.

**Last verified:** 2026-09-20 (live test-tenant reproduction and gateway controls;
[`test_custom_field_formats_live.py`](../tests/integration/test_custom_field_formats_live.py)).

______________________________________________________________________

## Resolved Issues (FYI)

Historical local fixes and answered contract questions. A local fix does not imply that
an upstream behavior changed; related open questions are called out explicitly.

| Issue                                                                              | Resolution                                                                                                                                                                                                                                                                                                |
| ---------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| PurchaseOrderAccountingMetadata used camelCase field names                         | Fixed to snake_case to match actual API responses                                                                                                                                                                                                                                                         |
| StockAdjustment field renames (`adjustment_date` -> `stock_adjustment_date`, etc.) | Updated spec to match actual field names                                                                                                                                                                                                                                                                  |
| SalesOrderFulfillment schema overhaul                                              | ~8 fields removed, ~10 added to match actual API                                                                                                                                                                                                                                                          |
| SalesReturnRow field corrections                                                   | Updated to match actual response structure                                                                                                                                                                                                                                                                |
| 7 schemas incorrectly used UpdatableEntity                                         | Upgraded to DeletableEntity where DELETE endpoints exist                                                                                                                                                                                                                                                  |
| PriceList phantom fields (`currency`, `end_date`, etc.)                            | Removed fields not present in actual API responses                                                                                                                                                                                                                                                        |
| StockTransfer/StockAdjustment had status enums                                     | Current local spec uses a free-form status string on StockTransfer and no status field on StockAdjustment (reviewed 2026-09-20).                                                                                                                                                                          |
| §1.3 — MO ↔ SO linking via PATCH                                                   | Linking is documented at MO creation via `POST /manufacturing_order_make_to_order`. No post-hoc linking endpoint is documented.                                                                                                                                                                           |
| §1.4 — PO CREATE `status` only accepted `NOT_RECEIVED` (2026-02-07)                | Katana now accepts both `DRAFT` and `NOT_RECEIVED` (verified spec-only against `live-gateway.yaml` and our local `CreatePurchaseOrderInitialStatus` enum on 2026-05-07).                                                                                                                                  |
| §4.1 — Variant `lead_time` / `minimum_order_quantity` null semantics               | Clarified — `null` means "not set" (distinct from `0`). API correctly distinguishes.                                                                                                                                                                                                                      |
| §2.2 — `ProductOperationRow` PK is `product_operation_row_id` (not `id`)           | Our local spec mirrors this resource-specific identifier; still present on review, 2026-09-20.                                                                                                                                                                                                            |
| §5.1 — `/demand_forecasts` is a computation endpoint, not a CRUD resource          | POST and DELETE bodies both require `variant_id` + `location_id` + `periods` (not just an identifier). Mental model: it's a calculation API. Our spec mirrors it.                                                                                                                                         |
| §2.1 — `/bin_locations` bare-array parser (#575)                                   | Fixed in [PR #903](https://github.com/dougborg/katana-openapi-client/pull/903), with live verification on 2026-06-03. The populated-response naming question remains open.                                                                                                                                |
| Manufacturing request contracts (#830)                                             | [PR #1060](https://github.com/dougborg/katana-openapi-client/pull/1060): operation-row PATCH accepts a name-only update but rejects parent-MO changes; MO-header PATCH rejects `serial_numbers`; serial-number POST with only `resource_id` accepts a 204 no-op. Verified on the test tenant, 2026-09-20. |
| §1.5 — Missing custom-field request inputs (#1030)                                 | [PR #1062](https://github.com/dougborg/katana-openapi-client/pull/1062) models 17 object/null inputs and three map/legacy-array unions. Account capability and persistence semantics remain upstream questions.                                                                                           |
| §6.3 — Endpoint-specific batch quantity models (#1053)                             | [PR #1058](https://github.com/dougborg/katana-openapi-client/pull/1058) reflects the observed sales-row/production-ingredient difference. The omission default still needs upstream documentation.                                                                                                        |
| §1.2 — Material config create/update requirements                                  | [PR #1068](https://github.com/dougborg/katana-openapi-client/pull/1068) separates name/values create inputs from ID-or-name updates. Live response uses `product_id`; verified 2026-09-20.                                                                                                                |
| §6.2 — Missing SO/ST notes-preservation probes (#531)                              | Both preserve omitted notes in controlled PATCH/GET checks, 2026-09-20. Historical wipes on other entities remain open questions.                                                                                                                                                                         |

### Material configuration verification (#1068)

**Status: RESOLVED in the local client —
[PR #1068](https://github.com/dougborg/katana-openapi-client/pull/1068)**

The local `CreateMaterialRequest.configs` previously inherited response-only `id` and
`material_id` requirements through `MaterialConfig`. The create input now requires only
`name` and `values`, matching the gateway DTO and live behavior. Material responses
continue to use `ItemConfig`.

**Test-tenant verification (2026-09-20):**

- CREATE with `configs: [{name, values}]` succeeds without either identifier.
- The returned config has `id`, `name`, `values`, and **`product_id`**, including when
  its parent is a material. The old note's `product_id` spelling was accurate.
- A values-only config PATCH returns 422: `Config name or id has to be set`.
- PATCH with `{id, values}` succeeds without repeating the name. Updates identify each
  config by ID or name; the gateway's optional fields have this additional constraint.

Three temporary SDT materials were recorded in the tenant-aware ledger and deleted. The
live regression is in `tests/integration/test_material_config_contract_live.py`.

**Last verified:** 2026-09-20 (controlled live writes and cleanup, plus all three
regenerated clients).
