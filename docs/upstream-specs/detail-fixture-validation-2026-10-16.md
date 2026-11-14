# Detail fixture validation — 2026-10-16

The shared Python/TypeScript detail fixtures create tagged, tenant-verified resources
for the 14 detail paths previously skipped because their collections were empty.
Resources and their dependencies are temporary and recorded for cleanup before SDK
parsing or response validation. Bulk responses record all IDs before ledger persistence;
custom-field definition UUIDs are supported by both cleanup implementations.

## Confirmed wire differences

| Contract                      | Live evidence                                                                                     | Local correction                                                                                                     |
| ----------------------------- | ------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| Service category              | Creating a service without a category returns `category_name: null`.                              | Permit null in `Service.category_name`.                                                                              |
| Storage-bin name              | Both create and update reject a 41-character name with HTTP 422 and a 40-character limit message. | Add `maxLength: 40` to both request shapes.                                                                          |
| Return-row unassigned batches | A newly created return row returns the bare empty array `[]`.                                     | Accept an array as well as the previously documented `data` wrapper. Nonempty bare-array content remains unverified. |

These observations used `make_test_client()` and owned resources. Disabled webhook
fixtures point at `example.invalid`; no delivery is enabled. Return fixtures create an
owned fulfillment and an explicit return row. No batches or serial numbers are retained.

## Intermittent dependency errors

The October 16 nightly returned HTTP 422 claiming a just-created second sales order did
not exist when creating its return. The October 14 and 15 nightlies passed, and a local
rerun with the live timeout passed including cleanup. A separate owned-fixture probe
also encountered an invalid-variant response immediately after product creation.

The fixture recipes now read back product variants and sales orders before consuming
them as dependencies. The sales-return filter regression likewise verifies its order
through GET before creating the return. These checks improve dependency diagnostics;
they do not establish the root cause or guarantee consistency between API endpoints. No
mutation retries or failure suppression were added. Nightly failures remain visible
under the workflow changes in #1166.
