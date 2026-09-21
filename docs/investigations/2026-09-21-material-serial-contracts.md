# Material creation and serial traceability: current contract review

Reviewed on 2026-09-21 for #1083 and #784, against client/MCP commit `f419e1ca`. Live
writes used only `make_test_client()` and factory `104008`, with SDT names and
tenant-scoped cleanup ledgers. Requests were awaited; no sleeps or timing retries were
added to the probes.

## Conclusions

- **#1083:** the material price workaround is necessary. Both header and nested
  `sales_price` are rejected on material creation. Embedded `product_id` and
  `material_id` are also rejected individually. Other supported material and variant
  properties can be supplied in the initial request; they do not generally need PATCH.
- **#784:** the June public-API fulfillment gap no longer reproduces for the tested
  make-to-order flow. Production generated a serial automatically. Delivery succeeded
  both with allocations omitted and with explicit unified `traceability`, on separate
  fixtures. Production provenance and the requested delivery timestamp were preserved.
- The manual serial-assignment 404 is real, but it is **not a prerequisite blocker** for
  the auto-generated-serial workflow. Our MCP's mandatory-serial guards and its
  categorical public-API-gap guidance need revision. The tool already supports explicit
  `traceability`; it does not need that parameter added again.

## Sources and scope

Fresh downloads, rather than just the committed September 18 snapshots:

- [Live gateway OpenAPI](https://api.katanamrp.com/v1/openapi.json): 125 paths.
- [Official documentation index](https://developer.katanamrp.com/llms.txt) and the
  portal's embedded OpenAPI: 119 paths. The portal schema was semantically unchanged;
  gateway changes since the committed snapshot were confined to two purchase-order
  recipe DTOs, outside these two issues.
- [Create a material](https://developer.katanamrp.com/reference/creatematerial),
  [update a material](https://developer.katanamrp.com/reference/updatematerial), and
  [create a variant](https://developer.katanamrp.com/reference/create-variant).
- [Assign serial numbers](https://developer.katanamrp.com/reference/createserialnumbers),
  [list serial assignments](https://developer.katanamrp.com/reference/getserialnumbers),
  [unassign serials](https://developer.katanamrp.com/reference/deleteserialnumbers), and
  [serial stock/history](https://developer.katanamrp.com/reference/getserialnumberstock).
- [Create an MO](https://developer.katanamrp.com/reference/createmanufacturingorder),
  [create a production](https://developer.katanamrp.com/reference/createmanufacturingorderproduction),
  [create a fulfillment](https://developer.katanamrp.com/reference/create-sales-order-fulfillment),
  sales-row and manufacturing object references, and purchase receiving documentation.
- Katana's current
  [serial tracking guide](https://support.katanamrp.com/en/articles/7439695-enabling-serial-number-tracking),
  [manufactured serial guide](https://support.katanamrp.com/en/articles/7470870-adding-serial-numbers-to-manufactured-products),
  [item defaults guide](https://support.katanamrp.com/en/articles/14461565-how-to-create-default-settings-for-items),
  and
  [official MCP overview](https://support.katanamrp.com/en/articles/15502865-katana-mcp-overview).

The official MCP is `https://mcp.katanamrp.com`, authenticated with Katana credentials;
its overview does not publish endpoint-level serial contracts. Its authenticated tool
schemas were not inspected. The configured `katana` connector here is our repository's
MCP, not proof of the official service's implementation. Its resource listing failed
with an `AnyFunction` import error, so this review inspected local tool schemas, source,
and help directly. Do not conflate these two MCP servers.

Neither current OpenAPI source nor the official index publishes a separate `/serials`
endpoint. `/serial_numbers` remains documented and is not marked deprecated there. The
deprecated inputs are the older allocation fields on business documents, such as
production/fulfillment `serial_numbers` and `batch_transactions`. The newer unified
`traceability` takes precedence when supplied.

## #1083: initial request versus follow-up update

The first investigation only live-tested nested `sales_price`; the parent-ID exclusions
were schema-derived. This review tested each exclusion separately and also created a
material with the supported fields together, then read back the material and variant.
Both rounds of price probes explicitly set `is_sellable: true`, including the rejected
header and nested price requests. The rejection was not caused by leaving selling
disabled.

| Input on `POST /materials`                                                                                                                                                 | Live result                                                                          |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| Header `name`, `uom`, `category_name`, `default_supplier_id`, `purchase_uom`, `purchase_uom_conversion_rate`, `batch_tracked`, `configs`, `additional_info`, `is_sellable` | 200; persisted in GET                                                                |
| Nested `sku`, `purchase_price`, both barcodes, `supplier_item_codes`, `config_attributes`, integer `lead_time`, fractional `minimum_order_quantity`                        | 200; persisted in GET; barcodes normalized to uppercase                              |
| Header `custom_field_collection_id: null`, nested `custom_fields: {}`                                                                                                      | Accepted; does not establish nonempty custom-field support or collection association |
| Nested `sales_price: 12.34`                                                                                                                                                | 422 `additionalProperties` at `/variants/0`                                          |
| Nested `product_id` or `material_id`, each using a test-owned parent ID                                                                                                    | Each 422 `additionalProperties` at `/variants/0`                                     |
| Header `sales_price: 12.34`                                                                                                                                                | 422 `additionalProperties`                                                           |
| Header `serial_tracked: false` or `operations_in_sequence: false`                                                                                                          | Each 422 `additionalProperties`                                                      |
| Nested `lead_time: 1000`                                                                                                                                                   | 422 domain error: integer 0–999 required                                             |
| Nested `lead_time: 1.5`                                                                                                                                                    | 500, despite the gateway's `number` type                                             |
| Nested `lead_time`, `minimum_order_quantity`, `purchase_price` all null                                                                                                    | 200; first two stayed null, purchase price normalized to zero                        |
| Nested registered barcode of length 41                                                                                                                                     | 422 `maxLength: 40`                                                                  |

Katana's product guides reserve serial tracking and manufacturing operations for
products; material tracking supports batches. Thus the material/product distinction has
a documented product rationale, not just an unexplained DTO omission. The standalone
variant creation endpoint requires a parent ID; embedding a variant inside a new
material does not accept those IDs.

Material `18022581`, variant `42143159`, confirmed the combined initial payload.
Price-only PATCH succeeded. A second material (`18022588`, variant `42143161`) showed
that a price-only PATCH response contains `config_attributes: []` even though the next
GET preserves `Size=Small`. This is an incomplete mutation response, **not evidence of
configuration deletion**. Avoid deriving an authoritative display name from that empty
PATCH response without retaining/readback-verifying the known configuration.

The new local material variant schema still needs narrow follow-ups: registered barcode
length is too permissive (120 versus 40), and purchase price/minimum order quantity do
not accept the verified null inputs. Do **not** widen local lead time to the gateway's
fractional/32-bit range: live domain validation contradicts that schema. Other numeric
limits and nonempty custom-field writes were not comprehensively boundary-tested here.

Failed domain creates were not atomic: the lead-time probes left five material parents
(`18022582`–`18022586`) despite 422/500 results, four with the fractional probe's exact
SDT name. They were discovered by a scoped read, ledgered, and deleted. This observation
does not by itself identify which layer generated the repeated parents. Failed POST
cleanup must discover such resources rather than assuming no response ID means no write.

## #784: verified current sequence

1. Create a serial-tracked, producible product, customer, and one-unit sales order.
1. Create its linked MO with `POST /manufacturing_order_make_to_order`.
1. Complete production without `serial_numbers` or `traceability`. In these fixtures,
   Katana generated a serial and returned it in production `traceability`. The sales row
   then contained that same serial allocation. This establishes automatic generation in
   this tenant/configuration, not every possible product setting.
1. Deliver using either of the following payloads. Both were verified separately:

```json
{
  "sales_order_id": 52169291,
  "status": "DELIVERED",
  "picked_date": "2026-09-21T19:17:27.220Z",
  "sales_order_fulfillment_rows": [
    {"sales_order_row_id": 124015026, "quantity": 1}
  ]
}
```

Or, for the second fixture's row:

```json
{
  "sales_order_row_id": 124015161,
  "quantity": 1,
  "traceability": [{"serial_number_id": 1047119, "quantity": "1"}]
}
```

| Probe                 | MO / production / serial            | Fulfillment | Result                                                                        |
| --------------------- | ----------------------------------- | ----------- | ----------------------------------------------------------------------------- |
| Omitted allocations   | `19210189` / `16327030` / `1047104` | `46064748`  | 200 DELIVERED; exact requested picked date; serial allocation carried forward |
| Explicit traceability | `19210205` / `16327053` / `1047119` | `46064801`  | 200 DELIVERED; exact requested picked date; same serial allocation            |

For both probes, before/after `/serial_numbers_stock` retained the original
`ManufacturingOrder` +1 transaction ID and production date. The undated sales-row -1
reservation became a dated -1 transaction at the requested picked date (its transaction
ID changed). No duplicate consumption or lost production provenance was observed. No
serial was unassigned/deleted to enable fulfillment, and no private UI API was used.

The separate manual-assignment checks still returned 404 on a valid MO, before and after
production. Assigning an unknown string to `Production` returned 422
`UnknownSerialNumber`. After auto-generation, the MO detail and production contained the
serial, while legacy resource-scoped `GET /serial_numbers` returned an empty list. The
assignment/list adapter needs its own upstream clarification; it cannot be used as the
sole authoritative view of current document traceability.

The documented allocation rules matter: omission and `[]` are different; `traceability`
overrides legacy fields; serial entries refer to existing IDs with quantity `"1"`.
Manufacturing output omits the bin axis, while ingredient allocations omit the serial
axis. The published input DTOs do not accept new serial strings inside `traceability`. A
microsecond timestamp with `+00:00` was rejected by production; millisecond UTC `Z`
timestamps succeeded. This review did not isolate offset versus precision as the cause.

## Remaining client/MCP work

- Keep #784 open for the MCP fix and regression coverage, not as proof of an unresolved
  general public-API delivery gap. Add a cleaned-up end-to-end test of the sequence
  above.
- `FulfillRowOverride.traceability` and manufacturing output allocations already exist.
  Use these paths; do not add another serial API wrapper or detach/reattach workaround.
- `_build_row_override_warnings` currently blocks omitted serial inputs even when the
  linked sales row already has valid allocations. It should distinguish a complete
  existing reservation from missing traceability before permitting omission.
- Manufacturing completion also unconditionally requires supplied IDs. Account for
  existing/generated serials with explicit caller intent and configuration checks; this
  probe alone does not justify silently generating serials for every product.
- Replace the obsolete categorical gap claims in `fulfill_order`'s docstring, warning
  text, `katana://help`, and close-out instructions. Show the supported explicit
  traceability path while distinguishing API capability from current MCP guards.
- Track the material null/barcode limits and incomplete PATCH response in
  [#1090](https://github.com/dougborg/katana-openapi-client/issues/1090), following
  #1083. Preserve its tested partial-success recovery behavior.
- Keep manual serial assignment/listing under the existing
  [#983](https://github.com/dougborg/katana-openapi-client/issues/983); upstream
  failed-create and cleanup questions stay in the team notes and
  [#603](https://github.com/dougborg/katana-openapi-client/issues/603).

## Cleanup and evidence limits

Every ledgered parent resource was deleted, including the five failed-create leftovers.
Deleting an individual production on a completed MO returned 422; deleting its parent MO
removed it, verified by GET 404 and a successful ledger recovery. No reusable batch
fixture was changed or added.

Three empty serial identities remain visible in serial stock/history: `1047071`,
`1047104`, and `1047119`, each `in_stock: false` with no transactions. Deleting parents
does not remove these identity rows. Disabling serial tracking on the last test product
before deletion also did not remove its identity from this read endpoint; attempting to
update the two already-deleted test products returned 404. These are residual test
identities, not retained inventory or reusable fixtures. Their cleanup contract needs
clarification; no unrelated serials were touched.

Evidence logs and fresh source downloads are under `/tmp/katana-current-research/` and
`/tmp/katana-research-*.log`. Persistent tenant ledgers for this review end in
`bd91c760`, `dd05bfdc`, `83a0e902`, `d5a49da6`, and `4d59fab5`; all parent deletion
records are complete. The raw probes bypassed MCP orchestration deliberately to isolate
API behavior. They establish the supported one-unit auto-generated MTO flow, not all
partial fulfillments, preexisting manually assigned serials, or account configurations.

## MCP regression follow-up (2026-09-21)

The #784 implementation was exercised through `_fulfill_order_impl` against the test
factory for both omitted and explicit sales allocations. Both ledgered tests passed:
automatic production returned the generated serial, the sales preview showed the same
serial, and delivery preserved the original manufacturing transaction ID/date while
stamping exactly one sales consumption at the requested picked date. Fixture teardown
deleted all tracked parents. Empty serial identities can remain as described above; this
test does not delete or unassign serials to enable delivery.

Manufacturing generation is an explicit `generate_serial_numbers=true` option. It
requires confirmed serial tracking and the caller's confirmation that automatic
generation is configured for the product/tenant; the public API exposes no separate
readable generation setting. Both allocation fields must be omitted, including no
explicit empty list. Unsupported API responses are surfaced without a second creation
attempt. Incomplete generated-serial readback reports the created production ID and
warns against repeating production.

Sales allocation omission now uses a complete reservation from the freshly fetched sales
row. Explicit unified traceability takes precedence; invalid, empty, duplicate, or
incomplete serial allocations remain blocked. Transaction audit history is not used as
current allocation state. Full-quantity fulfillment remains the supported MCP operation;
this does not establish partial-fulfillment behavior or resolve #983's
manual-assignment/listing discrepancies.

Coverage lives in `katana_mcp_server/tests/tools/test_mto_fulfillment.py` and
`tests/integration/test_mto_serial_fulfillment_live.py`. The latter runs with the
existing local/nightly live suite and requires automatic generation configured in the
test tenant.
