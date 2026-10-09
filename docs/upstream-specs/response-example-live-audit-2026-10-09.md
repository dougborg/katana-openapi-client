# Live response-example audit — 2026-10-09

Validated the 83 portal-example errors across 41 operation/status pairs against test
factory `104008`, using `make_test_client()` exclusively. Requests used existing records
for read-only sampling and SDT-tagged disposable records for writes. All 42 recorded
parent resources were successfully deleted; children were covered by their parents. No
serial attachment probe executed, and no batch identities were created.

The [JSON evidence](response-example-live-audit-2026-10-09.json) contains each finding,
observed JSON types, request statuses, limitations, and cleanup totals. It omits tenant
payloads and credentials. Counts below are error occurrences: examples sometimes repeat
the same property in several rows.

## Results

| Result                                               | Error occurrences |
| ---------------------------------------------------- | ----------------: |
| Portal example disagrees with sampled live responses |                54 |
| Local schema rejects an observed live value/property |                16 |
| Unverified                                           |                13 |

A portal-example verdict describes the observed cases; it does not prove the entire
response contract for every tenant and state. A local-schema verdict can coexist with an
incorrect portal type: operation actual time/cost are nullable strings, while the portal
examples show numbers.

## Confirmed local gaps

- Manufacturing operation `total_actual_time` and `total_actual_cost` can be `null`
  before completion and strings after completion. This affects eight example errors
  across list, create, detail, and update responses. Preserve strings and add
  nullability.

- Outsourced recipe creation returns `planned_quantity_per_unit` as a string; the local
  create-response schema expects a number.

- Shipping-fee creation returns numeric `amount`; list, detail, and update responses
  return strings. Model the create response separately or support the observed
  difference explicitly.

- Stock-adjustment rows include `traceability` in list, create, and update responses.
  The local response schema forbids this property (five example errors).

- Stock-transfer `batch_transactions[].batch_id` can be `null` for unallocated stock
  once its status is `inTransit`; the local response schema expects an integer.

The disputed purchase-order `landed_cost` is numeric in the sampled live responses,
matching the local field schema. The portal examples use strings. Purchase-order
classification checks this leaf explicitly; unrelated failures in other union fields
must not decide this mismatch.

## Unverified cases

- Eight nullable legacy `batch_id` occurrences: no null legacy allocation was observed,
  including after receiving unallocated stock into a disposable batch-tracked product
  and completing fulfillment. Explicit null legacy allocations on sales and outsourced
  recipe rows returned 422 type errors. Outsourced receipt without batch traces returned
  `UNTRACED_BATCH_TRACKABLE_INGREDIENTS`. The stock-transfer case was subsequently
  confirmed after changing the owned transfer from `draft` to `inTransit`. These request
  rejections do not establish the response field’s nullability.
- Two accounting-metadata occurrences: `GET /purchase_order_accounting_metadata`
  returned an empty `data` array. There is no public write endpoint to create metadata
  for this probe. Prior archived evidence is not counted as fresh live validation.
- Two recipe-cost occurrences: create/update returned `null`, which the local schema
  allows. Their non-null JSON type remains unverified.
- One serial failure reason: automatic approval review rejected attaching a pre-existing
  out-of-stock serial to an owned row, because acceptance could modify its assignment
  without a verified rollback. The `NOT_IN_STOCK` enum case remains unverified.

## Individual findings

Array indices are shown as `*` because the probe samples every available element rather
than requiring the example’s literal index. “Portal” means the example conflicts with
observed live data; “Local” means an observed live value is rejected by the
corresponding schema; “Unverified” means the disputed case was not observed.

|   # | Operation                                         | Disputed field                                                         | Observed types           | Result     |
| --: | ------------------------------------------------- | ---------------------------------------------------------------------- | ------------------------ | ---------- |
|   1 | `GET /inventory`                                  | `/data/*/safety_stock_level`                                           | string                   | Portal     |
|   2 | `POST /inventory_reorder_points`                  | `/value`                                                               | string                   | Portal     |
|   3 | `POST /inventory_safety_stock_levels`             | `/value`                                                               | string                   | Portal     |
|   4 | `GET /manufacturing_order_operation_rows`         | `/data/*/planned_time_per_unit`                                        | string                   | Portal     |
|   5 | `GET /manufacturing_order_operation_rows`         | `/data/*/planned_time_parameter`                                       | string                   | Portal     |
|   6 | `GET /manufacturing_order_operation_rows`         | `/data/*/total_actual_time`                                            | null, string             | Local      |
|   7 | `GET /manufacturing_order_operation_rows`         | `/data/*/planned_cost_per_unit`                                        | string                   | Portal     |
|   8 | `GET /manufacturing_order_operation_rows`         | `/data/*/total_actual_cost`                                            | null, string             | Local      |
|   9 | `GET /manufacturing_order_operation_rows`         | `/data/*/cost_per_hour`                                                | string                   | Portal     |
|  10 | `GET /manufacturing_order_operation_rows`         | `/data/*/cost_parameter`                                               | string                   | Portal     |
|  11 | `POST /manufacturing_order_operation_rows`        | `/planned_time_per_unit`                                               | string                   | Portal     |
|  12 | `POST /manufacturing_order_operation_rows`        | `/planned_time_parameter`                                              | string                   | Portal     |
|  13 | `POST /manufacturing_order_operation_rows`        | `/total_actual_time`                                                   | null                     | Local      |
|  14 | `POST /manufacturing_order_operation_rows`        | `/planned_cost_per_unit`                                               | string                   | Portal     |
|  15 | `POST /manufacturing_order_operation_rows`        | `/total_actual_cost`                                                   | null                     | Local      |
|  16 | `POST /manufacturing_order_operation_rows`        | `/cost_per_hour`                                                       | string                   | Portal     |
|  17 | `POST /manufacturing_order_operation_rows`        | `/cost_parameter`                                                      | string                   | Portal     |
|  18 | `GET /manufacturing_order_operation_rows/{id}`    | `/planned_time_per_unit`                                               | string                   | Portal     |
|  19 | `GET /manufacturing_order_operation_rows/{id}`    | `/planned_time_parameter`                                              | string                   | Portal     |
|  20 | `GET /manufacturing_order_operation_rows/{id}`    | `/total_actual_time`                                                   | null, string             | Local      |
|  21 | `GET /manufacturing_order_operation_rows/{id}`    | `/planned_cost_per_unit`                                               | string                   | Portal     |
|  22 | `GET /manufacturing_order_operation_rows/{id}`    | `/total_actual_cost`                                                   | null, string             | Local      |
|  23 | `GET /manufacturing_order_operation_rows/{id}`    | `/cost_per_hour`                                                       | string                   | Portal     |
|  24 | `GET /manufacturing_order_operation_rows/{id}`    | `/cost_parameter`                                                      | string                   | Portal     |
|  25 | `PATCH /manufacturing_order_operation_rows/{id}`  | `/planned_time_per_unit`                                               | string                   | Portal     |
|  26 | `PATCH /manufacturing_order_operation_rows/{id}`  | `/planned_time_parameter`                                              | string                   | Portal     |
|  27 | `PATCH /manufacturing_order_operation_rows/{id}`  | `/total_actual_time`                                                   | null, string             | Local      |
|  28 | `PATCH /manufacturing_order_operation_rows/{id}`  | `/planned_cost_per_unit`                                               | string                   | Portal     |
|  29 | `PATCH /manufacturing_order_operation_rows/{id}`  | `/total_actual_cost`                                                   | null, string             | Local      |
|  30 | `PATCH /manufacturing_order_operation_rows/{id}`  | `/cost_per_hour`                                                       | string                   | Portal     |
|  31 | `PATCH /manufacturing_order_operation_rows/{id}`  | `/cost_parameter`                                                      | string                   | Portal     |
|  32 | `GET /manufacturing_order_recipe_rows`            | `/data/*/planned_quantity_per_unit`                                    | string                   | Portal     |
|  33 | `GET /manufacturing_order_recipe_rows`            | `/data/*/total_actual_quantity`                                        | null, string             | Portal     |
|  34 | `GET /manufacturing_order_recipe_rows`            | `/data/*/cost`                                                         | null, string             | Portal     |
|  35 | `POST /manufacturing_order_recipe_rows`           | `/planned_quantity_per_unit`                                           | string                   | Portal     |
|  36 | `POST /manufacturing_order_recipe_rows`           | `/total_actual_quantity`                                               | string                   | Portal     |
|  37 | `POST /manufacturing_order_recipe_rows`           | `/cost`                                                                | null                     | Unverified |
|  38 | `GET /manufacturing_order_recipe_rows/{id}`       | `/planned_quantity_per_unit`                                           | string                   | Portal     |
|  39 | `GET /manufacturing_order_recipe_rows/{id}`       | `/total_actual_quantity`                                               | string                   | Portal     |
|  40 | `GET /manufacturing_order_recipe_rows/{id}`       | `/cost`                                                                | null, string             | Portal     |
|  41 | `PATCH /manufacturing_order_recipe_rows/{id}`     | `/planned_quantity_per_unit`                                           | string                   | Portal     |
|  42 | `PATCH /manufacturing_order_recipe_rows/{id}`     | `/total_actual_quantity`                                               | string                   | Portal     |
|  43 | `PATCH /manufacturing_order_recipe_rows/{id}`     | `/cost`                                                                | null                     | Unverified |
|  44 | `GET /operators`                                  | `/`                                                                    | object                   | Portal     |
|  45 | `GET /outsourced_purchase_order_recipe_rows`      | `/data/*/batch_transactions/*/batch_id`                                | No matching field sample | Unverified |
|  46 | `POST /outsourced_purchase_order_recipe_rows`     | `/planned_quantity_per_unit`                                           | string                   | Local      |
|  47 | `GET /outsourced_purchase_order_recipe_rows/{id}` | `/batch_transactions/*/batch_id`                                       | No matching field sample | Unverified |
|  48 | `GET /purchase_order_accounting_metadata`         | `/data/*/purchase_order_id`                                            | No matching field sample | Unverified |
|  49 | `GET /purchase_order_accounting_metadata`         | `/data/*/purchase_order_id`                                            | No matching field sample | Unverified |
|  50 | `GET /purchase_orders`                            | `/data/*/purchase_order_rows/*/landed_cost`                            | number                   | Portal     |
|  51 | `POST /purchase_orders`                           | `/purchase_order_rows/*/landed_cost`                                   | number                   | Portal     |
|  52 | `GET /purchase_orders/{id}`                       | `/purchase_order_rows/*/landed_cost`                                   | number                   | Portal     |
|  53 | `GET /sales_order_fulfillments`                   | `/data/*/sales_order_fulfillment_rows/*/batch_transactions/*/batch_id` | No matching field sample | Unverified |
|  54 | `GET /sales_order_fulfillments/{id}`              | `/sales_order_fulfillment_rows/*/batch_transactions/*/batch_id`        | No matching field sample | Unverified |
|  55 | `GET /sales_order_rows`                           | `/data/*/price_per_unit`                                               | string                   | Portal     |
|  56 | `GET /sales_order_rows`                           | `/data/*/batch_transactions/*/batch_id`                                | No matching field sample | Unverified |
|  57 | `POST /sales_order_rows`                          | `/price_per_unit`                                                      | string                   | Portal     |
|  58 | `POST /sales_order_rows/search`                   | `/data/*/quantity`                                                     | number                   | Portal     |
|  59 | `POST /sales_order_rows/search`                   | `/data/*/total`                                                        | number                   | Portal     |
|  60 | `GET /sales_order_rows/{id}`                      | `/price_per_unit`                                                      | string                   | Portal     |
|  61 | `GET /sales_order_rows/{id}`                      | `/batch_transactions/*/batch_id`                                       | No matching field sample | Unverified |
|  62 | `PATCH /sales_order_rows/{id}`                    | `/price_per_unit`                                                      | string                   | Portal     |
|  63 | `GET /sales_order_shipping_fee`                   | `/data/*/amount`                                                       | string                   | Portal     |
|  64 | `GET /sales_order_shipping_fee`                   | `/data/*/amount`                                                       | string                   | Portal     |
|  65 | `POST /sales_order_shipping_fee`                  | `/amount`                                                              | number                   | Local      |
|  66 | `GET /sales_order_shipping_fee/{id}`              | `/amount`                                                              | string                   | Portal     |
|  67 | `PATCH /sales_order_shipping_fee/{id}`            | `/amount`                                                              | string                   | Portal     |
|  68 | `GET /sales_orders`                               | `/data/*/sales_order_rows/*/price_per_unit`                            | string                   | Portal     |
|  69 | `GET /sales_orders`                               | `/data/*/sales_order_rows/*/batch_transactions/*/batch_id`             | No matching field sample | Unverified |
|  70 | `POST /sales_orders`                              | `/sales_order_rows/*/price_per_unit`                                   | string                   | Portal     |
|  71 | `POST /sales_orders/search`                       | `/data/*/total`                                                        | number                   | Portal     |
|  72 | `POST /sales_orders/search`                       | `/data/*/location_id`                                                  | number                   | Portal     |
|  73 | `GET /sales_orders/{id}`                          | `/sales_order_rows/*/price_per_unit`                                   | string                   | Portal     |
|  74 | `GET /sales_orders/{id}`                          | `/sales_order_rows/*/batch_transactions/*/batch_id`                    | No matching field sample | Unverified |
|  75 | `GET /serial_numbers`                             | `/`                                                                    | object                   | Portal     |
|  76 | `POST /serial_numbers`                            | `/failed/*/reason`                                                     | No matching field sample | Unverified |
|  77 | `GET /serial_numbers_stock`                       | `/`                                                                    | object                   | Portal     |
|  78 | `GET /stock_adjustments`                          | `/data/*/stock_adjustment_rows/*/traceability`                         | array                    | Local      |
|  79 | `GET /stock_adjustments`                          | `/data/*/stock_adjustment_rows/*/traceability`                         | array                    | Local      |
|  80 | `POST /stock_adjustments`                         | `/stock_adjustment_rows/*/traceability`                                | array                    | Local      |
|  81 | `POST /stock_adjustments`                         | `/stock_adjustment_rows/*/traceability`                                | array                    | Local      |
|  82 | `PATCH /stock_adjustments/{id}`                   | `/stock_adjustment_rows/*/traceability`                                | array                    | Local      |
|  83 | `GET /stock_transfers`                            | `/data/*/stock_transfer_rows/*/batch_transactions/*/batch_id`          | null                     | Local      |

## Probe and validation

`uv run python -m scripts.probe_portal_response_mismatches --mutate` provides read-only
sampling plus ledger-controlled create/update probes. A supplemental stock-lifecycle
probe received unallocated stock, completed an operation and fulfillment, and
transferred owned stock, then reverted receipts before deleting the parents.
Supplemental request statuses are included in the JSON evidence.

The probe’s classification tests cover empty arrays, missing fields, null cases, enum
cases, and numeric drift. All seven pass. No shared-schema changes are made by this
audit.
