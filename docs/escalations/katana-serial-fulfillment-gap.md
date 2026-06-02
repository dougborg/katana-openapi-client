# Public API gap: cannot fulfill a serial-tracked, make-to-order sales order

**Area:** Sales Order Fulfillments · Serial Numbers · Make-to-order\
**Severity:** Blocks all API-driven shipping of serial-tracked finished goods produced
via make-to-order\
**Public API base:** `https://api.katanamrp.com/v1`

> **Status:** Submitted to Katana 2026-06-02; this is the consolidated statement after a
> live investigation (test tenant + a browser network-trace of the UI close-out).\
> Internal tracking:
> [#784](https://github.com/dougborg/katana-openapi-client/issues/784),
> [#849](https://github.com/dougborg/katana-openapi-client/issues/849).

## Summary

A serial-tracked sales-order row whose serial was produced through a **make-to-order**
manufacturing order cannot have a delivered fulfillment recorded via the public REST
API. By production time the serial is already consumed onto its SO row, and
`POST /sales_order_fulfillments` only knows how to **assign a new** serial — so it
rejects the already-consumed one. The web UI does it through an internal endpoint
(`salesFulfillmentEvents/createMany`) that **confirms** the existing reservation; there
is no public equivalent. Driving that internal endpoint with a web-UI session token is
the only working path today, which is not a supportable integration.

The gap is specific to **make-to-order**. **Make-to-stock has a clean public path** (see
below), so integrators who can produce to stock are unblocked; build-to-order close-out
is not.

## What we're trying to do (make-to-order flow)

1. `POST /sales_orders` — order a serial-tracked product (qty 1).
1. `POST /manufacturing_order_make_to_order` — create the linked MO from the SO row.
1. `POST /serial_numbers` (`resource_type: ManufacturingOrder`) — mint the serial on the
   MO.
1. `POST /manufacturing_order_productions` (`serial_numbers: [<id>]`, `is_final: true`)
   — complete production.
1. **`POST /sales_order_fulfillments` — record delivery with that serial.** ←
   impossible.

Steps 1–4 all succeed. Step 5 cannot be made to succeed by any payload.

## The core gap — the catch-22

After step 4 the serial is bound to three resources, and the **SO row already carries
it** (`serial_numbers: [<id>]`, `linked_manufacturing_order_id: <mo>`):

```text
serial 904179 → Production           14472037
serial 904179 → ManufacturingOrder   17293071
serial 904179 → SalesOrderRow        111978788   ← already on the row we're fulfilling
```

Every minimal payload is rejected. Each request is
`{ "sales_order_id": 46366857, "status": "DELIVERED", "sales_order_fulfillment_rows": [ <row> ] }`
with the `<row>` (`SalesOrderFulfillmentRowRequest`) varied as below — there is no third
option:

| `sales_order_fulfillment_rows[]` item (+ top-level `status`)            | Response                                                                      |
| ----------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `{sales_order_row_id, quantity: 1}` (no serial)                         | `422` "sum of serial number quantity (current: 0) must match … (expected: 1)" |
| `{sales_order_row_id, quantity: 1, serial_numbers: [904179]}`           | `422` "given serial numbers have already been assigned"                       |
| …same row, but top-level `status: "PACKED"`                             | `422` "already assigned"                                                      |
| `{sales_order_row_id, quantity: 1, serial_numbers: []}`                 | `422` "current 0 … expected 1"                                                |
| `{sales_order_row_id, quantity: 0}`                                     | `422` schema — quantity must be `> 0`                                         |
| `serial_numbers: ["<name>"]` / `["<id-as-string>"]`                     | `422` schema — *must be number* (the field takes integer ids only)            |
| `serial_number_transactions: [{serial_number_id, quantity}]` on the row | `422` "Unexpected property" (not a fulfillment-row field)                     |

- **Provide the serial** → "already assigned" (production already assigned it to the MO,
  the production, and the SO row). It is not a representation problem: the integer id is
  the only schema-valid form, and it is rejected *semantically*.
- **Omit the serial** → "current 0" — the fulfillment does **not** read the serial off
  the row; it only counts serials declared in the request.

The request that *should* be simplest — "deliver row `111978788`, quantity 1, using the
serial already on it" — has **no public form**. The fulfillment endpoint's only serial
input is the *assign* path, which the make-to-order link has already foreclosed.

## Why — the serial-ledger lifecycle (UI-traced)

Tracing `GET /serial_numbers_stock` after each UI action — with the browser network
panel open to capture the UI-API calls — pins down which transition is missing. A
make-to-order order books its serial ledger in three steps, and **delivery does not add
a transaction — it stamps a reservation written back at serial-generation time**:

| UI action                                        | Serial-ledger effect (`quantity_change`)                                                |
| ------------------------------------------------ | --------------------------------------------------------------------------------------- |
| Generate the serial on the make-to-order MO      | `SalesOrderRow -1` written **undated** (a reservation)                                  |
| Build / complete the MO                          | `Production +1`, `ManufacturingOrder +1` (the `MO 0` placeholder becomes `+1`)          |
| Deliver (UI `salesFulfillmentEvents/createMany`) | the existing `SalesOrderRow -1` is **stamped** with the delivery timestamp — no new row |

Observed verbatim (serial `904176` on row `111966287`):

```text
after MO build:   SalesOrderRow -1 (date=null)     Production +1   ManufacturingOrder +1   net=+1
after delivery:   SalesOrderRow -1 (date=19:58:42)  Production +1   ManufacturingOrder +1   net=+1
```

So by delivery time the serial is already fully consumed onto its row and the ledger is
complete (`net=+1`, `in_stock=false`) **before** any fulfillment call. Delivery only
needs to *confirm* that reservation. The UI does exactly that via its internal endpoint
(captured from the browser, real values):

```http
POST https://sales-fulfillments.katanamrp.com/api/salesFulfillmentEvents/createMany
[
  { "salesOrderId": 46356252, "status": "delivered",
    "serialNumberTransactions": [
      { "salesOrderRowId": 111966287,
        "serialNumber":   "784-UI-429952/1-0001",   // name
        "serialNumberId": 904176 }                  // id — the UI sends BOTH
    ] }
]
```

The response row carries the serial as **traceability**, not an assignment:

```json
"rows": [ { "salesOrderRowId": 111966287, "quantity": 1,
            "traceability": [ { "serialNumberId": 904176, "quantity": "1" } ] } ]
```

`serialNumberTransactions` here is a **confirm-the-reservation** verb. The public
`POST /sales_order_fulfillments` only exposes `serial_numbers`, an
**assign-a-new-serial** operation. **There is no public verb to confirm/stamp the
existing make-to-order reservation** — that is the single missing primitive.

(Note the field-name collision: `serial_number_transactions` *also* exists on
`PATCH /sales_order_rows/{id}`, but there it is an **assign** verb — "put this serial on
the row." On a make-to-order row it returns `422` "row already has serial number with id
(…)", because the link already put the serial there. Same name, opposite semantics from
the UI's confirm verb.)

## Make-to-stock works cleanly (verified end-to-end)

Producing to stock first, then selling, has a fully working public path that preserves
the serial ledger — because the serial sits in free stock until the row transfer
consumes it (no make-to-order link pre-consuming it):

```http
1. POST /manufacturing_orders                       # standalone MO (NOT make_to_order)
2. POST /serial_numbers (ManufacturingOrder)         # mint on the MO
   POST /manufacturing_order_productions (serial)    # → serial enters stock
3. POST /sales_orders                                # order the same variant
4. PATCH /sales_order_rows/{id}
   { "serial_number_transactions": [ { "serial_number_id": <id>, "quantity": 1 } ] }
                                                      # ← transfer the in-stock serial onto the row
5. POST /sales_order_fulfillments                     # → 200, DELIVERED
   { "sales_order_id": <so>, "status": "DELIVERED",
     "sales_order_fulfillment_rows": [
       { "sales_order_row_id": <row>, "quantity": 1, "serial_numbers": [ <id> ] } ] }
```

Resulting trail is **identical to the UI's**
(`Production +1 / ManufacturingOrder +1 / SalesOrderRow -1`, `net=+1`,
`in_stock=false`). The only cost is the lost formal SO↔MO link (the MO is standalone,
not make-to-order).

## Everything else we tried (all rejected)

| Attempt                                                                          | Result                                                                                                                   |
| -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `PATCH /sales_orders/{id}` `{status: DELIVERED}`                                 | `200` but **no-op** — status stays `NOT_SHIPPED` (computed from fulfillments)                                            |
| `POST /serial_numbers` (`resource_type: SalesOrderRow`) to (re)assign the serial | `422` "SalesOrderRow … is linked, serial info must be updated on MO"                                                     |
| Mint the serial directly on the SO row (`resource_type: SalesOrderRow`)          | `422` "serial numbers not found" (serials can only be *minted* on an MO)                                                 |
| `PATCH /sales_order_rows/{id}` `serial_number_transactions` (the transfer)       | `422` "row already has serial number with id (…)" — the link already consumed it                                         |
| Produce **without** a serial, then mint afterward                                | mint immediately writes a `SalesOrderRow -1` with **no** `Production +1` (a different broken trail); fulfill still `422` |
| `POST /manufacturing_order_unlink` → then fulfill                                | unlink succeeds but the serial is still MO-bound → `422` "already assigned" (and unlinking tears down a legitimate link) |

## Deleting the serial bindings then fulfilling succeeds but corrupts the ledger — not a workaround

`DELETE /serial_numbers` ("unassign from a resource", returns `204`) *can* free the
serial from Production + ManufacturingOrder, after which
`POST /sales_order_fulfillments` then succeeds (`200`) and the SO shows `DELIVERED`.
**It is data corruption, not a fix.** It deletes the `+1` production transactions,
leaving a lone `SalesOrderRow -1` (net **-1**) — a unit shipped that the ledger says was
never produced:

```text
UI / make-to-stock (correct):  Production +1 | ManufacturingOrder +1 | SalesOrderRow -1   net +1
DELETE-then-fulfill (broken):                                          SalesOrderRow -1   net -1
```

(Aside: the `DELETE /serial_numbers` `ids` field is typed `string` in the published docs
but the live API requires **integer** ids — sending the documented type returns
"`/ids/0` must be number".)

## What we need (any one of these unblocks us)

The blocker, precisely: **a serial that has been consumed onto its own make-to-order SO
row cannot have a delivered fulfillment recorded against it via the public API.** Any
one of these resolves it, mirroring what already works for make-to-stock and the UI:

1. **Accept the already-consumed serial** on `POST /sales_order_fulfillments` when it is
   bound to the *same* row being fulfilled (treat "already on this row" as valid);
   **or**
1. **Auto-adopt the row's serial** — when a serial-tracked, make-to-order row omits
   `serial_numbers`, use the serial already on the row instead of returning "current 0";
   **or**
1. **Expose the confirm verb** — a public `serialNumberTransactions`-shaped body on
   `POST /sales_order_fulfillments` that stamps the existing reservation (what
   `salesFulfillmentEvents/createMany` does internally); **or**
1. **Don't auto-consume at production** — leave the serial in stock and let the
   fulfillment record the consumption, as make-to-stock already does.

## Minor adjacent findings (not blocking, FYI)

- `GET /manufacturing_orders` and `POST /manufacturing_order_make_to_order` return
  `production_deadline_date: null` for deadline-less MOs, but it is documented as a
  non-nullable `date-time`. Please mark it nullable.
- `POST /manufacturing_order_make_to_order` requires `createSubassemblies`, and there
  appears to be an undocumented camelCase bulk branch (`salesOrderIds`) alongside the
  documented snake_case single-row `sales_order_row_id`.

______________________________________________________________________

*All IDs above are from disposable test-tenant fixtures; the sequence reproduces from a
clean tenant. Probed against the public API on 2026-06-01 and 2026-06-02, with the UI
close-out captured via browser devtools on 2026-06-02.*
