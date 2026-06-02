# Public API gap: cannot fulfill a serial-tracked, make-to-order sales order

**Area:** Sales Order Fulfillments · Serial Numbers · Make-to-order\
**Severity:** Blocks all API-driven shipping of serial-tracked finished goods produced
via make-to-order\
**Public API base:** `https://api.katanamrp.com/v1`

> Escalation prepared for the Katana API team. Internal tracking:
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
