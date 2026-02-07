# Katana API Questions

Questions and inconsistencies discovered during P1-P4 OpenAPI spec alignment (Katana
spec dated 2026-01-20, 104 paths). These are intended for discussion with the Katana API
team.

______________________________________________________________________

## 1. Create/Update vs Response Schema Asymmetries

### 1.1 Material `serial_tracked` and `operations_in_sequence` not settable via API

The Material GET response includes `serial_tracked` and `operations_in_sequence`, but
neither field appears in the Create or Update request schemas. By contrast, the Product
resource includes both fields in its Create and Update schemas.

- **Response schema:** `MaterialResponse` (~line 3714 in spec)
- **Create schema:** `CreateMaterialRequest` (~line 3515) - fields absent
- **Update schema:** `UpdateMaterialRequest` - fields absent
- **Compare:** `CreateProductRequest` and `UpdateProductRequest` include both fields

**Question:** Is there an intentional reason Materials cannot set these fields via API,
or is this a spec omission?

### 1.2 `MaterialConfig` schema requires `id` and `material_id` on CREATE

`CreateMaterialRequest.configs` references the `MaterialConfig` schema, which has `id`
and `material_id` as required fields. These values don't exist yet when creating a new
material.

By contrast, `UpdateMaterialRequest.configs` correctly uses an inline schema with only
`name` and `values`.

- **Likely spec error:** The Create schema should use the same simplified inline schema
  as Update.

**Question:** Can you confirm that `id` and `material_id` are not actually required when
creating material configs?

### 1.3 Manufacturing Order cannot be linked to Sales Order via create/update

The Manufacturing Order response includes `sales_order_id`, `sales_order_row_id`, and
`sales_order_delivery_deadline`, but none of these fields appear in the Create or Update
request schemas.

The endpoint `/manufacturing_order_unlink` exists to remove a link, but there is no
corresponding `/manufacturing_order_link` endpoint.

**Question:** How are Manufacturing Orders linked to Sales Orders via the API? Is there
an undocumented link endpoint, or is this only possible through the UI?

### 1.4 Purchase Order `status` in CREATE only accepts one value

`CreatePurchaseOrderRequest` includes a `status` field, but the only valid value is
`NOT_RECEIVED`. Since every new purchase order starts with this status, the field is
effectively meaningless on create.

**Question:** Is this intentional, or should the field be omitted from the create schema
(with the server defaulting to `NOT_RECEIVED`)?

______________________________________________________________________

## 2. Field Naming Inconsistencies

### 2.1 StorageBin: `name` vs `bin_name`

The StorageBin schema defines both `name` and `bin_name`. List endpoint examples use
`name`, while detail and update endpoints use `bin_name`. The `bin_name` field is the
required one.

**Question:** Are `name` and `bin_name` the same field with different names depending on
context, or are they genuinely separate fields? If separate, what is the semantic
difference?

### 2.2 `ProductOperationRow` uses `product_operation_row_id` instead of `id`

Every other resource in the API uses `id` as its primary key field.
`ProductOperationRow` uniquely uses `product_operation_row_id`. It also doesn't extend
any entity base type despite having `created_at` and `updated_at` fields.

**Question:** Is this intentional, or a legacy naming that could be aliased to `id` for
consistency?

______________________________________________________________________

## 3. Read-Only Endpoints Missing Write Operations

Several resources only have GET (list) endpoints with no documented create, update, or
delete operations:

| Resource         | Endpoint            | Question                            |
| ---------------- | ------------------- | ----------------------------------- |
| Additional Costs | `/additional_costs` | How are these created?              |
| Factory          | `/factory`          | How do you update factory settings? |
| Operators        | `/operators`        | How are operators created/managed?  |

**Question:** Are write operations for these resources UI-only, or are they undocumented
API endpoints?

______________________________________________________________________

## 4. Nullable Field Semantics

### 4.1 Variant `lead_time` and `minimum_order_quantity` null semantics

Both fields are defined as `[integer, null]` and `[number, null]` respectively, but the
meaning of `null` is ambiguous:

- `lead_time: null` - Does this mean "no data entered", "instant/zero lead time", or
  "N/A"?
- `minimum_order_quantity: null` - Does this mean "no minimum required" or "unknown"?

**Question:** What is the intended semantic meaning of `null` for these fields?

______________________________________________________________________

## 5. Non-Standard Patterns

### 5.1 `/demand_forecasts` doesn't follow any standard resource pattern

This endpoint deviates from every other resource in the API:

- No pagination support
- No standard CRUD pattern
- No entity inheritance (no `id`, `created_at`, etc.)
- GET requires `variant_id` + `location_id` as mandatory query parameters (not optional
  filters)
- POST returns 204 No Content (not the created/updated resource)
- DELETE accepts a request body (unusual for REST APIs)

**Question:** Is there a reason this resource follows a completely different pattern?
Are there plans to align it with the standard resource conventions?

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
