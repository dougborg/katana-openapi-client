# Live-Spec Audit — 2026-04-28

Comparison of `docs/katana-openapi.yaml` (local) against the live OpenAPI document at
`https://api.katanamrp.com/v1/openapi.json` (refreshed via the updated
`scripts/extract_all_katana_docs.py`). This supersedes the parts of
`docs/audit-2026-04-28.md` that were based on the now-stale archived upstream spec; the
original audit is preserved as historical record but its field-level claims should be
treated as superseded by this document.

## Source of truth

- **Live spec**: 110 paths, 95 named schemas (almost all request DTOs: `Create*Dto`,
  `Update*Dto`, `*PatchDto`).
- **Local spec**: 107 paths, ~700 schemas (request bodies + reverse-engineered response
  object schemas).
- The live spec **has no response object schemas** — only request DTOs and filter-param
  enums. Our local response schemas (`SalesReturn`, `StockTransfer`, `Product`,
  `ManufacturingOrder`, etc.) remain the only source of those shapes and continue to be
  useful.
- OpenAPI version: live is **3.0**, local is **3.1**. Syntax differences
  (`nullable: true` vs `type: [string, null]`, `integer` vs `number`) are semantically
  equivalent and have been filtered out of the report below.

## Endpoint coverage

Mapping by `(path, method)` of operations with a request body:

| Bucket                    | Count | Notes                                                         |
| ------------------------- | ----- | ------------------------------------------------------------- |
| Shared (in both)          | 82    | Compared field-by-field                                       |
| Live-only                 | 4     | We don't expose these endpoints                               |
| Local-only with named DTO | 5     | All 5 paths exist in live, but live uses inline schemas there |

### Endpoints in live but not local

| Method   | Path                             | Live DTO                         | Action                                |
| -------- | -------------------------------- | -------------------------------- | ------------------------------------- |
| `POST`   | `/custom_field_definitions`      | `CreateCustomFieldDefinitionDto` | Add endpoint + DTO                    |
| `PATCH`  | `/custom_field_definitions/{id}` | `UpdateCustomFieldDefinitionDto` | Add endpoint + DTO                    |
| `POST`   | `/sales_orders/search`           | `SearchFilterDto`                | Add endpoint + DTO                    |
| `DELETE` | `/serial_numbers`                | `DeleteSerialNumberDto`          | Add request body to existing endpoint |

Note: live also exposes `GET /custom_field_definitions` and
`GET /custom_field_definitions/{id}` and `DELETE /custom_field_definitions/{id}` (no
request body so they didn't appear in the shared/only-live tally) — we should add these
too.

### Endpoints local-only with named DTO (live has them with inline schemas)

| Method | Path                             | Local DTO                             | Live shape                                |
| ------ | -------------------------------- | ------------------------------------- | ----------------------------------------- |
| `POST` | `/inventory_reorder_points`      | `CreateInventoryReorderPointRequest`  | inline `{location_id, variant_id, value}` |
| `POST` | `/inventory_safety_stock_levels` | `InventorySafetyStockLevel`           | inline `{location_id, variant_id, value}` |
| `POST` | `/purchase_order_receive`        | `PurchaseOrderReceiveRequest`         | empty body                                |
| `POST` | `/unlink_variant_bin_locations`  | `UnlinkVariantBinLocationListRequest` | `type: array`                             |
| `POST` | `/variant_bin_locations`         | `VariantDefaultStorageBinLink`        | `type: array`                             |

These are not drift in the path — verify the local request shape matches the inline live
shape and we're done.

## Field-level drift on shared endpoints

34 of 82 shared endpoints have real (non-syntax) drift. Grouped by category and impact:

### Category 1 — Wrong `required` fields (15 endpoints, HIGH impact)

These cause API calls to fail or our spec to over-restrict callers:

| Endpoint                                   | Live required                                                                          | Local required                                                 | Direction                                                                           |
| ------------------------------------------ | -------------------------------------------------------------------------------------- | -------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| `POST /manufacturing_orders`               | `[location_id, order_no, planned_quantity, variant_id]`                                | `[location_id, planned_quantity, variant_id]`                  | Local under-requires `order_no` (live API will 422)                                 |
| `POST /manufacturing_order_operation_rows` | `[manufacturing_order_id, status]`                                                     | `[manufacturing_order_id, operation_id]`                       | Wrong required set entirely — local requires `operation_id`; live requires `status` |
| `POST /manufacturing_order_productions`    | `[completed_quantity, manufacturing_order_id]`                                         | `[completed_date, completed_quantity, manufacturing_order_id]` | Local over-requires `completed_date`                                                |
| `POST /sales_order_fulfillments`           | `[sales_order_fulfillment_rows, sales_order_id, status]`                               | `[sales_order_id]`                                             | Local under-requires `[status, sales_order_fulfillment_rows]`                       |
| `POST /serial_numbers`                     | `[resource_id]`                                                                        | `[resource_id, resource_type, serial_numbers]`                 | Local over-requires `[resource_type, serial_numbers]`                               |
| `POST /stock_adjustments`                  | `[location_id, stock_adjustment_number, stock_adjustment_rows]`                        | `[location_id, stock_adjustment_rows]`                         | Local under-requires `stock_adjustment_number`                                      |
| `POST /stock_transfers`                    | `[source_location_id, stock_transfer_number, stock_transfer_rows, target_location_id]` | `[source_location_id, target_location_id]`                     | Local under-requires `[stock_transfer_number, stock_transfer_rows]`                 |
| `POST /stocktake_rows`                     | `[stocktake_id]`                                                                       | `[stocktake_id, stocktake_rows]`                               | Local over-requires `stocktake_rows`                                                |
| `POST /sales_order_addresses`              | `[entity_type, sales_order_id]`                                                        | `[city, country, entity_type, line_1, sales_order_id]`         | Local over-requires 3 address fields                                                |
| `POST /supplier_addresses`                 | `[supplier_id]`                                                                        | `[line_1, supplier_id]`                                        | Local over-requires `line_1`                                                        |
| `POST /variants`                           | `[]`                                                                                   | `[sku]`                                                        | Local over-requires `sku`                                                           |
| `PATCH /bin_locations/{id}`                | `[bin_name]`                                                                           | `[]`                                                           | Local under-requires `bin_name`                                                     |
| `PATCH /price_list_customers/{id}`         | `[customer_id]`                                                                        | `[]`                                                           | Local under-requires `customer_id`                                                  |
| `PATCH /sales_order_shipping_fee/{id}`     | `[amount]`                                                                             | `[]`                                                           | Local under-requires `amount`                                                       |
| `PATCH /stock_transfers/{id}/status`       | `[]`                                                                                   | `[status]`                                                     | Local over-requires `status`                                                        |
| `PATCH /webhooks/{id}`                     | `[]`                                                                                   | `[subscribed_events, url]`                                     | Local over-requires                                                                 |

### Category 2 — Fields missing from local (10 endpoints, real callers can't pass valid data)

| Endpoint                                | Missing fields                                                                  |
| --------------------------------------- | ------------------------------------------------------------------------------- |
| `POST /sales_returns`                   | `tracking_number`, `tracking_number_url`, `tracking_carrier`, `tracking_method` |
| `PATCH /sales_returns/{id}`             | same 4 tracking fields                                                          |
| `POST /sales_orders`                    | `custom_fields`                                                                 |
| `PATCH /sales_orders/{id}`              | `custom_fields`                                                                 |
| `PATCH /services/{id}`                  | `custom_fields`                                                                 |
| `POST /webhooks`                        | `enabled`                                                                       |
| `POST /purchase_order_rows`             | `currency`, `tax_name`, `tax_rate`                                              |
| `PATCH /purchase_order_rows/{id}`       | `tax_name`, `tax_rate`                                                          |
| `POST /manufacturing_order_productions` | `batch_transaction`                                                             |
| `PATCH /price_list_rows/{id}`           | `variant_id`                                                                    |

### Category 3 — Enum/type drift on request fields (12 endpoints)

| Endpoint                                         | Field               | Live                                                                                          | Local                                                                                                     |
| ------------------------------------------------ | ------------------- | --------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `PATCH /stock_transfers/{id}/status`             | `status`            | `[draft, received, inTransit]`                                                                | `[pending, in_transit, completed, cancelled]` (M-1, completely wrong)                                     |
| `POST /manufacturing_orders`                     | `status`            | `[NOT_STARTED]` (only)                                                                        | full `ManufacturingOrderStatus` (4 values) — live restricts at create-time                                |
| `PATCH /manufacturing_orders/{id}`               | `status`            | `[NOT_STARTED, BLOCKED, IN_PROGRESS, PARTIALLY_COMPLETED, DONE]`                              | local `ManufacturingOrderStatus` missing `PARTIALLY_COMPLETED`                                            |
| `POST /manufacturing_order_operation_rows`       | `status`            | `[NOT_STARTED]` (only)                                                                        | plain `string`                                                                                            |
| `POST /manufacturing_order_operation_rows`       | `type`              | `[process, setup, perUnit, fixed]`                                                            | plain `string`                                                                                            |
| `PATCH /manufacturing_order_operation_rows/{id}` | `status`            | `[NOT_STARTED, BLOCKED, IN_PROGRESS, PAUSED, COMPLETED]`                                      | plain `string`                                                                                            |
| `PATCH /manufacturing_order_operation_rows/{id}` | `type`              | `[process, setup, perUnit, fixed]`                                                            | plain `string`                                                                                            |
| `PATCH /product_operation_rows/{id}`             | `type`              | same enum                                                                                     | plain `string`                                                                                            |
| `PATCH /price_list_rows/{id}`                    | `adjustment_method` | `[fixed, percentage, markup]`                                                                 | plain `string`                                                                                            |
| `POST /sales_order_fulfillments`                 | `status`            | `[PACKED, DELIVERED]`                                                                         | plain `string`                                                                                            |
| `PATCH /sales_order_fulfillments/{id}`           | `status`            | `[PACKED, DELIVERED]`                                                                         | plain `string`                                                                                            |
| `POST /sales_order_shipping_fee`                 | `amount`            | `string`                                                                                      | `number` (live takes string)                                                                              |
| `PATCH /sales_order_shipping_fee/{id}`           | `amount`            | `string`                                                                                      | `integer` (live takes string)                                                                             |
| `POST /serial_numbers`                           | `resource_type`     | `[ManufacturingOrder, PurchaseOrderRow, SalesOrderRow, StockAdjustmentRow, StockTransferRow]` | `CreateSerialNumberResourceType` includes `Production` (extra value not allowed in live's request schema) |
| `POST /sales_return_rows`                        | `quantity`          | untyped                                                                                       | `string` (verify live's intent — likely accepts both)                                                     |
| `PATCH /sales_return_rows/{id}`                  | `quantity`          | untyped                                                                                       | `string`                                                                                                  |

### Category 4 — Suspect local-only fields (likely we invented them)

| Endpoint                                         | Field(s)                              | Verdict                                                               |
| ------------------------------------------------ | ------------------------------------- | --------------------------------------------------------------------- |
| `POST /products`                                 | `lead_time`, `minimum_order_quantity` | Probably belong on `CreateVariantRequest`, not `CreateProductRequest` |
| `PATCH /variants/{id}`                           | `material_id`, `product_id`           | Set at create-time, immutable — should not be in PATCH body           |
| `PATCH /manufacturing_order_operation_rows/{id}` | `manufacturing_order_id`              | You can't reassign an operation row to a different MO via PATCH       |
| `POST /purchase_order_rows`                      | `group_id`                            | Suspect — verify against live behavior                                |
| `PATCH /purchase_order_rows/{id}`                | `group_id`                            | Same                                                                  |
| `PATCH /bin_locations/{id}`                      | `location_id`                         | Suspect — bin's location is set at create                             |

## Suggested phasing

The drift is too broad for one PR. Suggested order:

### Phase A — already evidenced, ship now (issue #412 closing fixes)

1. M-1: `StockTransferStatus` enum `[draft, received, inTransit]` (replaces wrong values
   \+ fixes `UpdateStockTransferStatusRequest.required`)
1. M-2: `SalesReturnRefundStatus.REFUNDED_ALL` → `REFUNDED`
1. Closing comment for M-4 (no change), L-2 (no change)

### Phase B — drop-in safe enum tightening (next, low risk)

Apply `$ref` enum constraints where local field is plain `string`:

- `manufacturing_order_operation_row_request.status` + `.type`
- `update_manufacturing_order_operation_row_request.status` + `.type`
- `update_product_operation_row_request.type`
- `update_price_list_row_request.adjustment_method`
- `create_sales_order_fulfillment_request.status` +
  `update_sales_order_fulfillment_request.status`
- `update_manufacturing_order_request.status` (add `PARTIALLY_COMPLETED` to enum)
- `create_manufacturing_order_request.status` (restrict to `[NOT_STARTED]` only or
  define create-time enum)

### Phase C — required-field corrections (medium risk; some are over-relaxing, some are over-restricting)

The 16 endpoints listed in Category 1. Probably one PR per related cluster:

- Cluster: addresses (`POST /sales_order_addresses`, `POST /supplier_addresses`)
- Cluster: stock transfers/adjustments (`POST /stock_transfers`,
  `POST /stock_adjustments`)
- Cluster: manufacturing orders (`POST /manufacturing_orders`,
  `POST /manufacturing_order_operation_rows`, `POST /manufacturing_order_productions`)
- Cluster: webhooks (`POST /webhooks`, `PATCH /webhooks/{id}`)
- Cluster: misc (variants, price lists, bin locations, etc.)

### Phase D — missing fields

The 10 endpoints in Category 2. Add fields to local DTOs.

### Phase E — invented-field cleanup

The 6 entries in Category 4. Remove or move to correct schema.

### Phase F — missing endpoints

- `/custom_field_definitions` (POST/PATCH/GET/DELETE) — full CRUD missing
- `/sales_orders/search` (POST) — search endpoint missing
- `DELETE /serial_numbers` — endpoint exists but missing request body

### Phase G — verify local-only-with-named-DTO endpoints

The 5 endpoints where local has named DTO and live has inline — verify shapes match,
possibly inline our schemas to match live (or keep named).

## Mechanics for each fix PR

Per `CLAUDE.md`:

1. Edit `docs/katana-openapi.yaml`
1. `uv run poe regenerate-client`
1. `uv run poe generate-pydantic`
1. `cd packages/katana-client && npm run generate`
1. `uv run poe check`
1. Commit spec change + regen output together.

Some fixes are breaking changes on the public client surface (e.g., dropping
`material_id`/`product_id` from `UpdateVariantRequest`). Those need `feat(client)!:` or
`fix(client)!:` per the harness's commit convention.
