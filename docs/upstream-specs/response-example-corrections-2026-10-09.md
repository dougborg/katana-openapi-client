# Live-verified response example repairs — 2026-10-09

The original downloaded portal examples still produce 62 validation errors. The
[correction registry](response-example-corrections.yaml) repairs 61 fields across 26
operations, leaving two accounting-metadata errors unresolved. The extra repaired field
was exposed only after fixing a response wrapper.

The [fresh live evidence](response-example-corrections-live-2026-10-09.json) records 86
requests through `make_test_client()`, with zero schema errors in successful response
bodies. All 14 disposable parent resources were deleted. The evidence contains field
types and paths, not raw tenant payloads.

## Repairs

- Decimal strings replace numeric examples for inventory thresholds, manufacturing
  time/cost/quantity fields, and sales-row prices.
- Numeric values replace string examples for purchase-row landed costs and search
  quantities/totals.
- Operators and serial collections receive their observed `data` wrapper, retaining
  every original example record.
- Missing inventory safety-stock and sales-search location fields are added using the
  observed JSON types.
- Manufacturing operation POST/PATCH actual time/cost and recipe POST/PATCH cost
  examples use the observed `null` precompletion values. Non-null values for those
  operation/state combinations remain unverified.
- Wrapping serial-stock examples exposed a string ID. A supplemental read returned 56
  numeric IDs, and its full response passed schema validation. The example ID is
  corrected to an integer.

Illustrative literals remain public documentation values. The corrections establish the
sampled JSON representation, rather than claiming the literal example values were
returned by the tenant or that every lifecycle state was exercised.

## Remaining limitation

`GET /purchase_order_accounting_metadata` returned an empty `data` array on both reads.
The API has no public endpoint for creating accounting metadata. The two examples omit
the locally required `purchase_order_id` and use `purchaseOrderId`; an actual metadata
record is needed to establish the live contract. These examples remain unchanged and
both failures remain visible. Populating a test purchase order through its accounting
integration will allow this verification to finish.

## Validation behavior

`poe validate-response-examples` reports the raw upstream count, applied corrections,
and remaining failures, and exits nonzero while the two unresolved cases remain.
`poe validate-response-examples --raw-upstream` retains the original 62-error report.
Downloaded upstream snapshots and client schemas are unchanged by these repairs.

Corrections fail if an upstream example changes, if its live evidence is absent or
incompatible, or if a wrapper repair would discard records. New uncorrected drift
continues to fail schema validation.

## Checks

- `poe agent-check`: passed formatting, Ruff, and ty.
- Targeted Pyright and YAML lint: passed.
- `poe test`: 4,841 passed, with 15 existing skips.
- Corrected example validation: two unresolved metadata errors; exits 1.
- Raw upstream example validation: 62 errors; exits 1.
- `git diff --check`: passed.

## Follow-up: recurring SDK wire validation (#1157)

The spec-derived live SDK suite subsequently exercised all 88 GET operations and shared
write scenarios for eight core entities. The first Python run reported 77 passed, 14
skipped (detail reads without tenant fixtures), and five failures. Those failures
exposed four additional response contracts:

- `GET /suppliers`: `email`, `phone`, `comment`, and `default_address_id` can be null,
  including on a newly created SDT supplier.
- `GET /manufacturing_order_production_ingredients`: `quantity` and `cost` can be
  decimal strings.
- `GET /negative_stock`: `category` can be null.
- `GET /custom_fields_collections`: the test tenant returns a bare array. The response
  now accepts both that shape and the existing documented wrapper; the generated Python
  parser preserves an empty array as a list rather than silently constructing an empty
  wrapper.

The shared spec and all generated clients were updated from this live evidence. The
write scenarios use test-only credentials, SDT tags, factory verification, and
persistent cleanup ledgers. No tenant payloads or credentials are stored in this report.
Empty collections do not establish the shape of non-empty records, and skipped detail
reads remain explicit coverage gaps.
