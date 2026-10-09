# Response schema fixes — 2026-10-09

The [original live audit](response-example-live-audit-2026-10-09.md) identified 16
local-schema failures among 83 portal-example errors. Those failures are now addressed,
together with additional gaps found by validating complete responses rather than only
the original disputed fields.

The [verification evidence](response-schema-resolution-2026-10-09.json) records 84
requests through the test-only client, with **zero schema errors in their successful
response bodies**. Failed null-allocation requests are included as controls; a request
rejected with 422 is not counted as evidence about a successful response shape. All 14
disposable parent resources in the final response probe were deleted. Earlier
schema-development probes were also ledger-cleaned.

## Corrections

| Response                                    | Corrected contract                                                                                                                                                                                                                     |
| ------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Manufacturing operation row                 | Actual time/cost are nullable decimal strings. Resource ID/name, active operator ID, and group boundary may also be null.                                                                                                              |
| Manufacturing recipe row                    | Notes may be null. Existing nullable string quantity/cost fields are preserved.                                                                                                                                                        |
| Manufacturing order                         | Unlinked sales-order IDs and precompletion material, subassembly, and operation costs may be null.                                                                                                                                     |
| Outsourced purchase recipe row              | Planned quantity is a string on creation and a number on reads. Both representations are preserved in the existing model.                                                                                                              |
| Shipping fee                                | Amount is a number on creation and a string on reads/updates. Requests still send strings. The existing model supports both response representations.                                                                                  |
| Sales order                                 | An absent shipping fee can be represented by an empty object, as well as null. The Python client/cache preserve their existing normalization of this absent-fee shape to `None`; the MCP consumer also accepts the empty-object model. |
| Stock adjustment row                        | Responses include traceability allocations with nullable IDs, string quantities, and nullable deletion timestamps. Traceability is stored as JSON in generated cache tables.                                                           |
| Stock transfer row                          | Batch IDs may be null for unallocated stock after departure.                                                                                                                                                                           |
| Sales and outsourced recipe batch responses | Documented nullable batch IDs are supported in responses. Legacy allocation requests still reject null IDs.                                                                                                                            |
| Purchase order row                          | Purchase unit and purchase-unit conversion rate may be null.                                                                                                                                                                           |
| Catalog and location                        | An uncategorized inventory item can have a null category; a location can have a null legal name.                                                                                                                                       |
| Serial attachment                           | The published `NOT_IN_STOCK` failure reason is supported. Live matching-variant attachment verified the successful response envelope; that failure reason remains unobserved.                                                          |

All Python attrs, Pydantic/cache, and TypeScript clients were regenerated from the
shared spec. Regression tests exercise schema validation, generated parsers, Pydantic
conversion, JSON cache persistence, the empty shipping-fee consumer, and strict request
allocation rules.

## Authorized serial probe

After the original audit, the user explicitly authorized probing existing test serials.
A matching active variant returned 200 with one successful attachment and an empty
failed array; its response passed the updated schema. The owned order and customer were
deleted, and the serial's original out-of-stock flag remained unchanged afterward.

The wrong-variant and transfer-row controls returned 422. They did not reproduce a
per-item `NOT_IN_STOCK` failure. All eight parent resources created across the
authorized serial probes were successfully deleted. The enum addition is grounded in the
published response example, rather than a claim that the live API emitted that code.

## Remaining portal examples

`poe validate-response-examples` still reports **62 upstream example mismatches**. The
latest live probe classified 54 as disagreeing with observed live responses and eight as
lacking the disputed sample (including empty accounting metadata and non-null values
unavailable in the tested states). These are not hidden with overrides or error
suppressions. The upstream snapshots are left intact.

Examples of retained differences are portal numbers where the API returns decimal
strings, raw-list examples where the API returns a `data` wrapper, camelCase accounting
identifiers, string totals in search examples, and a search example missing its required
location. Broadening the local response schemas to accept these examples would weaken
the live contract without supporting evidence.

This verification establishes the sampled operations and states, rather than every
possible tenant feature or lifecycle state. The original per-error report remains
historical evidence; its finding numbers do not change when the schema is corrected.

## Validation

- `poe check`: passed, including 4,831 unit tests and 59 browser tests.
- `poe test-schema`: 2,440 passed; existing skips are reported separately. Missing
  property descriptions in the imported rerank and receipt schemas were corrected.
- TypeScript lint and type checking: passed; all 225 tests passed.
- `poe regenerate-all`: all three clients regenerated.
- No new audit overrides, skips, or error suppressions were introduced.
