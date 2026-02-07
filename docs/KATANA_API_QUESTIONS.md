# Katana API Questions

Questions and inconsistencies discovered during P1-P4 OpenAPI spec alignment (Katana
spec dated 2026-01-20, 104 paths). Each was investigated against the live API on
2026-02-07.

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

### 1.2 `MaterialConfig` schema requires `id` and `material_id` on CREATE

**Status: CONFIRMED - spec error, API does not require them**

`CreateMaterialRequest.configs` references the `MaterialConfig` schema, which has `id`
and `material_id` as required fields. These values don't exist yet when creating a new
material.

**Investigation:** Created a material with configs containing only `name` and `values`
(no `id` or `material_id`). The API accepted it (200 OK) and returned the created
configs with server-generated `id` and `product_id` values.

**Conclusion:** Confirmed spec error. The Katana API spec's `MaterialConfig` schema
over-specifies the create case. Our spec already uses the simplified inline schema for
create, which matches reality.

### 1.3 Manufacturing Order cannot be linked to Sales Order via create/update

**Status: RESOLVED - use `/manufacturing_order_make_to_order`**

The Manufacturing Order response includes `sales_order_id`, `sales_order_row_id`, and
`sales_order_delivery_deadline`, but none of these fields appear in the Create or Update
request schemas.

**Investigation:**

- `PATCH /manufacturing_orders/{id}` with `sales_order_id` returns 422
  `additionalProperties` - the field is truly not settable via update.
- `POST /manufacturing_order_make_to_order` exists and accepts
  `{"sales_order_row_id": <id>, "create_subassemblies": <bool>}`. This is the linking
  mechanism - it creates a new MO already linked to a sales order row.
- `POST /manufacturing_order_unlink` exists and accepts `{"sales_order_row_id": <id>}`
  to break the link.
- There is no way to link an *existing* unlinked MO to a sales order. The flow is:
  create-linked (make_to_order) or create-unlinked (regular create), then optionally
  unlink.

**Conclusion:** The API design is intentional. Linking is one-way at creation time via
`/manufacturing_order_make_to_order`. Our spec already documents both endpoints
correctly. The original question about a missing "link" endpoint is answered: linking
only happens at MO creation, not post-hoc.

### 1.4 Purchase Order `status` in CREATE only accepts one value

**Status: CONFIRMED - only `NOT_RECEIVED` allowed, field is optional**

`CreatePurchaseOrderRequest` includes a `status` field, but the only valid value is
`NOT_RECEIVED`.

**Investigation:**

- `POST /purchase_orders` without a `status` field succeeds (200 OK), and the created PO
  has `status: "NOT_RECEIVED"` automatically.
- `POST /purchase_orders` with `status: "NOT_RECEIVED"` also succeeds identically.
- `POST /purchase_orders` with `status: "PARTIALLY_RECEIVED"` returns 422 with
  `allowedValues: ["NOT_RECEIVED"]`.

**Conclusion:** The field is optional and defaults to `NOT_RECEIVED`. Including it is
harmless but pointless. This appears to be a Katana API design choice (consistent schema
shape between create/update) rather than a bug. Our spec correctly documents the enum
constraint.

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

### 2.2 `ProductOperationRow` uses `product_operation_row_id` instead of `id`

**Status: CONFIRMED - intentionally different from other resources**

Every other resource in the API uses `id` as its primary key field.
`ProductOperationRow` uniquely uses `product_operation_row_id`.

**Investigation:** `GET /product_operation_rows` returns records with
`product_operation_row_id` as the identifier - no `id` field present. However, the
related `ManufacturingOrderOperationRow` (from `/manufacturing_order_operation_rows`)
does use a standard `id` field.

The `ProductOperationRow` fields are: `product_operation_row_id`, `product_id`,
`product_variant_id`, `operation_id`, `operation_name`, `type`, `resource_id`,
`resource_name`, `cost_per_hour`, `cost_parameter`, `planned_cost_per_unit`,
`planned_time_per_unit`, `planned_time_parameter`, `rank`, `group_boundary`,
`created_at`, `updated_at`. No `deleted_at` despite having `created_at`/`updated_at`.

**Conclusion:** This is confirmed as a real inconsistency in the Katana API - not a spec
error on our side. The product operation row is the only resource that uses a
non-standard primary key naming convention.

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

______________________________________________________________________

## 4. Nullable Field Semantics

### 4.1 Variant `lead_time` and `minimum_order_quantity` null semantics

**Status: CLARIFIED - null means "not set"**

**Investigation:**

- Out of 250 variants sampled, 249 had `lead_time: null` and all 250 had
  `minimum_order_quantity: null`. Only one variant had `lead_time: 10`.
- `PATCH /variants/{id}` with `lead_time: 0` succeeds - the response shows
  `lead_time: 0` (integer zero, distinct from null).
- `PATCH /variants/{id}` with `lead_time: null` succeeds - the response shows
  `lead_time: null`.

**Conclusion:** `null` means "not configured / no value set" rather than a meaningful
zero or "N/A". The API correctly distinguishes between `0` (explicit zero) and `null`
(not set). This is consistent with standard nullable semantics. No spec change needed.

______________________________________________________________________

## 5. Non-Standard Patterns

### 5.1 `/demand_forecasts` doesn't follow any standard resource pattern

**Status: CONFIRMED - intentionally different, more of a "calculation" than a resource**

**Investigation:**

- `GET /demand_forecasts` without params returns 400: "Required parameter variant_id is
  missing!" - mandatory query params confirmed.
- `GET /demand_forecasts?variant_id=X&location_id=Y` returns a single forecast object
  (not a list) with `variant_id`, `location_id`, `in_stock`, and `periods` array. No
  pagination headers. The response is a computed view, not a stored resource.
- `POST /demand_forecasts` requires `variant_id`, `location_id`, and `periods` in the
  request body.
- `DELETE /demand_forecasts` also requires `variant_id`, `location_id`, and `periods` in
  the request body (not just the resource identifier).

**Conclusion:** This endpoint is fundamentally a *computation endpoint*, not a CRUD
resource. It returns calculated demand forecast data for a specific variant+location
combination. The POST "creates" forecast overrides for specific periods, and DELETE
"clears" overrides for specific periods. This design makes sense when understood as a
calculation API rather than a REST resource. No spec change needed, but worth
documenting the different mental model.

______________________________________________________________________

## Resolved Issues (FYI)

Issues discovered and fixed during P1-P4 alignment, documented here for reference:

| Issue                                                                              | Resolution                                               |
| ---------------------------------------------------------------------------------- | -------------------------------------------------------- |
| PurchaseOrderAccountingMetadata used camelCase field names                         | Fixed to snake_case to match actual API responses        |
| StockAdjustment field renames (`adjustment_date` -> `stock_adjustment_date`, etc.) | Updated spec to match actual field names                 |
| SalesOrderFulfillment schema overhaul                                              | ~8 fields removed, ~10 added to match actual API         |
| SalesReturnRow field corrections                                                   | Updated to match actual response structure               |
| 7 schemas incorrectly used UpdatableEntity                                         | Upgraded to DeletableEntity where DELETE endpoints exist |
| PriceList phantom fields (`currency`, `end_date`, etc.)                            | Removed fields not present in actual API responses       |
| StockTransfer/StockAdjustment had status enums                                     | Removed - these resources use free-form status strings   |
