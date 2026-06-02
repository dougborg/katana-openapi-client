# Public API gap: cannot fulfill a serial-tracked, make-to-order sales order

**Area:** Sales Order Fulfillments · Serial Numbers · Make-to-order\
**Severity:** Blocks all API-driven shipping of serial-tracked finished goods produced
via make-to-order\
**Public API base:** `https://api.katanamrp.com/v1`

> **Status:** Submitted to Katana 2026-06-02 (awaiting response). A second investigation
> (2026-06-02) narrowed the gap to **make-to-order specifically** and found that
> **make-to-stock has a clean public path** — see
> [Update — second investigation](#update--second-investigation-2026-06-02) below.\
> Internal tracking:
> [#784](https://github.com/dougborg/katana-openapi-client/issues/784),
> [#849](https://github.com/dougborg/katana-openapi-client/issues/849).

## Summary

There is no public-REST sequence that records a **delivered fulfillment** for a
serial-tracked sales-order row whose serial was produced through a **make-to-order**
manufacturing order. Every `POST /sales_order_fulfillments` payload is rejected. The
Katana web UI performs this routinely via
`POST https://sales-fulfillments.katanamrp.com/api/salesFulfillmentEvents/createMany`
using a `serialNumberTransactions` array — a **transfer** verb the public API does not
expose.

This is the normal lifecycle for any serialized finished good built to order, so it
blocks API-based close-out for that entire class of orders. The only working path today
is driving the internal `salesFulfillmentEvents` endpoint with a web UI session token,
which is not a supportable integration.

## What we're trying to do (standard make-to-order flow)

1. `POST /sales_orders` — order a serial-tracked product (qty 1).
1. `POST /manufacturing_order_make_to_order` — create the linked MO from the SO row.
1. `POST /serial_numbers` (`resource_type: ManufacturingOrder`) — mint the serial on the
   MO.
1. `POST /manufacturing_order_productions` (`serial_numbers: [<id>]`, `is_final: true`)
   — complete production.
1. **`POST /sales_order_fulfillments` — record delivery with that serial.** ←
   impossible.

Steps 1–4 all succeed. Step 5 cannot be made to succeed by any payload.

## The blocking call (verbatim)

At step 5 the serial is simultaneously bound to three resources (all created by steps
3–4):

```text
serial 903402 → Production           14429383
serial 903402 → ManufacturingOrder   17233151
serial 903402 → SalesOrderRow        111795735   ← already on the row we're fulfilling
```

Request:

```http
POST /sales_order_fulfillments
{
  "sales_order_id": 46242059,
  "status": "DELIVERED",
  "sales_order_fulfillment_rows": [
    { "sales_order_row_id": 111795735, "quantity": 1, "serial_numbers": [903402] }
  ]
}
```

Response:

```http
422 Unprocessable Entity
{ "error": { "statusCode": 422, "name": "UnprocessableEntityError",
             "message": "given serial numbers have already been assigned" } }
```

## The catch-22

`serial_numbers` accepts only integer SerialNumber IDs, and for this row the only
relevant serial is the one production already created. Every possible value is rejected:

| `serial_numbers` on the fulfillment row | Response                                                                                               |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| `[903402]` (the produced serial)        | `422` — "given serial numbers have already been assigned"                                              |
| omitted / `[]`                          | `422` — "sum of serial number quantity (current: 0) must match fulfillment row quantity (expected: 1)" |

- **Provide the serial** → rejected because production already assigned it (to the MO,
  the production, and the SO row).
- **Omit the serial** → rejected because the row requires one and the fulfillment does
  **not** auto-adopt the serial already attached to the SO row.

There is no third option.

## Everything else we tried (all rejected)

| Attempt                                                                    | Result                                                                                         |
| -------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| Fulfillment with **no rows**                                               | `422` — `sales_order_fulfillment_rows` required                                                |
| `PATCH /sales_orders/{id}` `{status: DELIVERED}`                           | `200` but **no-op** — status stays `NOT_SHIPPED` (it's computed from fulfillments)             |
| `POST /serial_numbers` (`resource_type: SalesOrderRow`) to move the serial | `422` — "SalesOrderRow … is linked, serial info must be updated on MO"                         |
| `POST /manufacturing_order_unlink` → then fulfill                          | unlink succeeds (`204`, row link cleared) but serial still MO-bound → `422` "already assigned" |
| unlink → `POST /serial_numbers` (SalesOrderRow) → fulfill                  | the add returns `200` but is a no-op (`resource_id: null`); fulfill still `422`                |
| Mint the serial directly on the SO row (`resource_type: SalesOrderRow`)    | `422` — "serial numbers not found" (serials can only be *minted* on a ManufacturingOrder)      |
| `serial_number_transactions` / `serialNumberTransactions` field on the row | `422` — "Unexpected property" (rejected as unknown)                                            |
| Produce **without** a serial, then fulfill with a freshly minted one       | produce ok; fresh serial is MO-bound → `422` "already assigned"                                |

## What the web UI does (and works)

```http
POST https://sales-fulfillments.katanamrp.com/api/salesFulfillmentEvents/createMany
[
  {
    "salesOrderId": <so>,
    "status": "delivered",
    "serialNumberTransactions": [
      { "salesOrderRowId": <row>, "serialNumber": "<name>", "serialNumberId": <id> }
    ]
  }
]
```

`serialNumberTransactions` is a **transfer** — it moves the serial's binding onto the
fulfillment atomically. The public `serial_numbers` field is an
**assign-unassigned-serials** operation, which is the wrong verb for an already-produced
serial.

## What we need (any one of these unblocks us)

1. **A public transfer verb** — e.g. accept a
   `serial_number_transactions`/`serialNumberTransactions`-shaped body on
   `POST /sales_order_fulfillments` that moves an already-assigned serial onto the
   fulfillment; **or**
1. **Auto-adopt the row's serial** — when a fulfillment row for a serial-tracked,
   make-to-order-linked SO row omits `serial_numbers`, use the serial already attached
   to that SO row; **or**
1. **Accept the already-assigned serial** on `POST /sales_order_fulfillments` when the
   serial is already bound to the *same* SO row being fulfilled (treat "already assigned
   to this row" as valid rather than an error).

## Update — second investigation (2026-06-02)

A deeper probe refined the picture. **The gap is specific to make-to-order.** The public
API *does* expose the transfer verb the UI uses — `serial_number_transactions` on
`PATCH /sales_order_rows/{id}` (`{serial_number_id, quantity}`, the same
`UpdateSerialNumberTransactionDto` shape as the UI's `serialNumberTransactions`). It
just cannot be applied in a make-to-order flow, because make-to-order auto-consumes the
serial onto the row at production time.

### Make-to-STOCK works cleanly (verified end-to-end)

Producing to stock first, then selling, has a fully working public path that preserves
the serial ledger:

```http
1. POST /manufacturing_orders                      # standalone MO (NOT make_to_order)
2. POST /serial_numbers (ManufacturingOrder)        # mint on the MO
   POST /manufacturing_order_productions (serial)   # → serial enters stock
3. POST /sales_orders                               # order the same variant
4. PATCH /sales_order_rows/{id}
   { "serial_number_transactions": [ { "serial_number_id": <id>, "quantity": 1 } ] }
                                                     # ← the transfer (in-stock serial → row)
5. POST /sales_order_fulfillments  { …, "serial_numbers": [ <id> ] }   # → 200, DELIVERED
```

Resulting serial trail (`GET /serial_numbers_stock`) is **identical to the UI's**:

```text
Production#…           qty_change=+1
ManufacturingOrder#…   qty_change=+1
SalesOrderRow#…        qty_change=-1      (net +1, in_stock=false)
```

So integrators who can produce-to-stock have a supportable public path today. The only
cost is the lost formal SO↔MO link (the MO is standalone, not make-to-order).

### Make-to-order is still blocked (representation ruled out)

On a make-to-order row whose serial was produced through the linked MO, every
representation of the fulfillment serial fails:

| `POST /sales_order_fulfillments` row payload                 | Result                                                             |
| ------------------------------------------------------------ | ------------------------------------------------------------------ |
| `serial_numbers: [<integer id>]`                             | `422` "given serial numbers have already been assigned" (semantic) |
| `serial_numbers: ["<name>"]`                                 | `422` schema — *must be number*                                    |
| `serial_numbers: ["<id-as-string>"]`                         | `422` schema — *must be number*                                    |
| `serial_number_transactions: [{serial_number_id, quantity}]` | `422` "Unexpected property" (not a fulfillment-row field)          |

And the row-level transfer that works for make-to-stock is rejected here:
`PATCH /sales_order_rows` `serial_number_transactions` → `422` "row already has serial
number with id (…)" — the make-to-order link already consumed it onto the row. Producing
*without* a serial and minting afterward doesn't help: minting on a make-to-order MO
immediately writes a `SalesOrderRow -1` with **no** `Production +1`, i.e. a different
broken trail.

### The make-to-order serial-ledger lifecycle (UI-traced, 2026-06-02)

Tracing `GET /serial_numbers_stock` after each UI action — with the browser network
panel open to capture the UI-API calls — pins down exactly which transition the public
API is missing. A serial-tracked make-to-order order books its serial ledger in three
steps, and **delivery does not add a transaction — it stamps a reservation already
written at serial-generation time**:

| UI action                                        | Serial-ledger effect (`quantity_change`)                                                |
| ------------------------------------------------ | --------------------------------------------------------------------------------------- |
| Generate the serial on the make-to-order MO      | `SalesOrderRow -1` written **undated** (a reservation)                                  |
| Build / complete the MO                          | `Production +1`, `ManufacturingOrder +1` (the `MO 0` placeholder becomes `+1`)          |
| Deliver (UI `salesFulfillmentEvents/createMany`) | the existing `SalesOrderRow -1` is **stamped** with the delivery timestamp — no new row |

Observed verbatim (serial `904176` on row `111966287`):

```text
after MO build:   SalesOrderRow -1 (date=null)   Production +1   ManufacturingOrder +1   net=+1
after delivery:   SalesOrderRow -1 (date=19:58:42) Production +1  ManufacturingOrder +1   net=+1
```

So by the time you deliver, the serial is already fully consumed onto its row; the
ledger is complete (`net=+1`, `in_stock=false`) **before** any fulfillment call. The
delivery step only needs to *confirm* that reservation.

The UI does this via its internal endpoint (captured from the browser, real values):

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

Response row carries the serial as **traceability**, not an assignment:

```json
"rows": [ { "salesOrderRowId": 111966287, "quantity": 1,
            "traceability": [ { "serialNumberId": 904176, "quantity": "1" } ] } ]
```

`serialNumberTransactions` is therefore a **confirm-the-reservation** verb. The public
`POST /sales_order_fulfillments` only exposes `serial_numbers` (an
**assign-a-new-serial** operation): passing the already-reserved serial → "already
assigned"; omitting it → "current 0" (nothing new to assign). **There is no public verb
to confirm/stamp the existing make-to-order reservation** — which is the single missing
primitive.

### The `DELETE /serial_numbers` path returns 200 but corrupts the ledger — do not use it

`DELETE /serial_numbers` ("unassign from a resource") *can* free the serial from
Production + ManufacturingOrder, after which `POST /sales_order_fulfillments` returns
`200` and the SO shows `DELIVERED`. **It is data corruption, not a workaround.** It
deletes the `+1` production transactions, leaving the serial with a lone
`SalesOrderRow -1` (net **-1**) — a unit shipped that the ledger says was never
produced. Side by side:

```text
UI / make-to-stock (correct):  Production +1 | MO +1 | SalesOrderRow -1   net +1
DELETE-then-fulfill (broken):                              SalesOrderRow -1   net -1
```

(Note: the `DELETE /serial_numbers` `ids` field is typed `string` in the published docs
but the live API requires **integer** ids — sending the documented type returns
"`/ids/0` must be number".)

### Narrowed ask

The blocker is precisely: **a serial that has been consumed onto its own make-to-order
SO row cannot have a delivered fulfillment recorded against it via the public API.** Any
one of these resolves it, mirroring what already works for make-to-stock:

1. Accept the already-consumed serial on `POST /sales_order_fulfillments` when it is
   bound to the *same* row being fulfilled; **or**
1. Auto-adopt the row's serial when `serial_numbers` is omitted for a serial-tracked,
   make-to-order row; **or**
1. Don't auto-consume the serial onto the row at production — leave it in stock and let
   `serial_number_transactions` / the fulfillment record the consumption (as in
   make-to-stock).

## Minor adjacent findings (not blocking, FYI)

- `GET /manufacturing_orders` and `POST /manufacturing_order_make_to_order` return
  `production_deadline_date: null` for deadline-less MOs, but it is documented as a
  non-nullable `date-time`. Please mark it nullable.
- `POST /manufacturing_order_make_to_order` requires `createSubassemblies`, and there
  appears to be an undocumented camelCase bulk branch (`salesOrderIds`) alongside the
  documented snake_case single-row `sales_order_row_id`.

______________________________________________________________________

*All IDs above are from disposable test-tenant fixtures, since deleted; the sequence
reproduces from a clean tenant. Probed against the public API on 2026-06-01.*
