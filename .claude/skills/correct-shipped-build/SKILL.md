---
name: correct-shipped-build
description: >-
  Resolve a shipped-order discrepancy — customer received different items than
  Katana recorded. Pull the customer-facing record, locate the linked Katana
  SO/MO, decide whether a BOM-driven split is needed (when an assembled good
  shipped as its component parts), then apply correct_manufacturing_order +
  correct_sales_order with operator-judgment gates between phases. Verify
  against the source of truth at the end.
argument-hint: "[order id from source-of-truth system]"
allowed-tools:
  - mcp__katana-erp__get_sales_order
  - mcp__katana-erp__get_manufacturing_order
  - mcp__katana-erp__get_manufacturing_order_recipe
  - mcp__katana-erp__list_sales_orders
  - mcp__katana-erp__correct_manufacturing_order
  - mcp__katana-erp__correct_sales_order
  - mcp__katana-erp__modify_manufacturing_order
  - mcp__katana-erp__modify_sales_order
  - mcp__katana-erp__check_inventory
  - mcp__katana-erp__create_stock_adjustment
---

# /correct-shipped-build — shipped-order discrepancy resolution

## PURPOSE

When a customer received different items than Katana recorded — wrong
ingredient on a finished good, wrong line item on a sales order, or a
finished good that shipped as its components — restore Katana to ground
truth without losing the original close-state metadata (`done_date`,
`picked_date`, per-production timestamps, fulfillment tracking).

## CRITICAL

- **Ground truth is the customer-facing record, not Katana.** Pull the
  Shopify / e-commerce / fulfillment-system order first; treat it as
  authoritative. Don't assume Katana's recorded fulfillment is right —
  this skill exists because it isn't.
- **Preview every correction before applying.** Both `correct_manufacturing_order`
  and `correct_sales_order` default to `preview=true` for a reason. The
  operator should read the planned action list and confirm before any
  mutations land.
- **Both MO and SO may need correction, in this order.** When a finished
  good's recipe was wrong (consumed the wrong ingredient), fix the MO
  first — that's the upstream truth. Then fix the SO if its line items
  also drifted. SO line items can reference variants the MO produced, so
  MO-first is the safer order.
- **Inventory side-effects belong to a separate decision.** If the
  finished good was disassembled mid-fulfillment — i.e. an assembled
  good was broken into its BOM components and shipped as parts — the
  MO/SO corrections alone don't reshuffle inventory. That's
  `split_via_bom`'s job. Don't conflate the two; decide explicitly
  whether a split is needed.

## STANDARD PATH

### Phase 1 — Pull the source-of-truth record

Ask the operator for the source-system order id (Shopify order, etc.).
Read the customer-facing record and write down what actually shipped:
SKUs, quantities, condition / assembly state. This is the **expected
state** every later phase compares against.

If you have a Chrome tab or other tool already open on the order, use it.
Otherwise the operator may need to open it manually and read off the
relevant fields.

### Phase 2 — Locate the linked Katana SO and MO

```
list_sales_orders(customer_id=..., delivered_after=..., delivered_before=...)
```

Filter by customer name + delivery date window to find the candidate SO.
Once you have the SO id:

```
get_sales_order(order_id=...)
```

Inspect:
- SO line items — what Katana thinks shipped
- `linked_manufacturing_order_id` on each row — the upstream MO, if any

If a row has a linked MO:

```
get_manufacturing_order(order_id=...)
```

Note the MO's `variant_id` (the finished good) and the status (`DONE` /
`PARTIALLY_COMPLETED`).

`get_manufacturing_order` defaults to `include_rows="blocking"`, which
hides recipe rows whose ingredients are in stock. To inspect the *full*
recipe before deciding what to correct, fetch the dedicated recipe view:

```
get_manufacturing_order_recipe(manufacturing_order_id=...)
```

This returns every recipe row regardless of ingredient-availability
status — that's what you want when figuring out which row consumed the
wrong variant.

### Phase 3 — Decide whether a split is needed

A **split** means: the finished good produced by the MO was disassembled
into its BOM components before shipment, and the customer received the
components instead of the assembled good.

Operator-judgment criteria:

- The customer-confirmed item list (phase 1) lists individual component
  SKUs instead of the assembled SKU.
- The MO produced a single assembled good, but the SO's line item now
  needs to reference component SKUs.
- The warehouse / fulfillment notes confirm the split.

If yes, plan to use `split_via_bom` in phase 6. If no, skip phase 6.

If `split_via_bom` is not yet shipped (issue #543 still open at the time
of writing), document the intended split — finished-good variant id,
location id, quantity, and the timing — and proceed without it. The
MO/SO corrections still land cleanly; the inventory reshuffling can be
applied as a follow-up when the tool ships.

### Phase 4 — Correct the MO (if the recipe was wrong)

If the MO consumed the wrong ingredient (e.g., the wrong variant of a
component, or an incorrect quantity per unit):

```
correct_manufacturing_order(
    id=...,
    ingredient_changes=[
        {
            old_variant_id: <variant currently on the recipe row>,
            new_variant_id: <variant that was actually consumed>,
            planned_quantity_per_unit: <if changed; otherwise omit>,
        },
        ...
    ],
    preview=true,
)
```

Review the planned action sequence — revert → recipe edit → recreate
production → re-close with backdated done_date / production_date.
Confirm the captured close-state matches reality. Then re-call with
`preview=false`.

The tool requires the MO to be in `DONE` or `PARTIALLY_COMPLETED`
status. If it's still `IN_PROGRESS`, use `modify_manufacturing_order`
directly — there's no close-state to preserve.

### Phase 5 — Correct the SO (if line items were wrong)

If the SO's line items don't match what the customer received:

```
correct_sales_order(
    id=...,
    line_changes=[
        {
            old_variant_id: <variant currently on the row>,
            new_variant_id: <variant actually shipped>,
            quantity: <if changed; must be ≥ already-fulfilled qty>,
            price_per_unit: <if changed>,
        },
        ...
    ],
    preview=true,
)
```

Preview surfaces the planned action sequence — delete fulfillments →
revert → row edits → re-add fulfillments with original `picked_date` →
re-close. Confirm and re-call with `preview=false`.

`correct_sales_order` only updates rows in place. If you need to **add
or remove** a line item entirely, use `modify_sales_order` directly —
the close-state restore would otherwise lose the row-id mapping the
fulfillments depend on.

### Phase 6 — Apply the BOM-driven split (if decided in phase 3)

> **Status: deferred.** The `split_via_bom` tool isn't shipped yet
> (issue #543). It's intentionally **not** listed in this skill's
> `allowed-tools` so the skill can load and run today; when the tool
> ships, add `mcp__katana-erp__split_via_bom` to the allowlist and
> remove this status callout.

When `split_via_bom` ships, the call shape will be:

```
split_via_bom(
    variant_id=<finished good>,
    location_id=<where the inventory transformation happened>,
    quantity=<how many were split>,
    stock_adjustment_date=<just before the customer's delivery date>,
    preview=true,
)
```

It generates a single mixed-sign stock adjustment: `-quantity` of the
finished good, `+(quantity × planned_quantity_per_unit)` of each BOM
ingredient, cost-balanced to net zero.

**Until then:** file a follow-up issue documenting the intended split
parameters (finished-good variant id, location id, quantity, timing)
and skip this phase. The MO/SO corrections still leave the records in
the right shape; only the inventory reshuffling is deferred.

### Phase 7 — Verify

Re-fetch the corrected records:

```
get_manufacturing_order(order_id=...)
get_sales_order(order_id=...)
```

Confirm the close-state restored cleanly: status back to its original
value, dates backdated to the originals, no new "today" timestamps
sneaking in.

Sanity-check inventory on the affected SKUs:

```
check_inventory(skus_or_variant_ids=[...])
```

Expected vs. actual stock levels should reconcile against the customer-
confirmed shipment. Negative availability is a red flag — it means the
correction over-corrected somewhere.

### Phase 8 — Summarize

Report to the operator:

- **Source-system order id** — what was being corrected.
- **Katana SO and MO ids** — links to the corrected records.
- **Changes applied** — MO recipe rows swapped (with variants), SO line
  items updated, split applied (yes/no, with parameters).
- **Inventory delta** — affected SKUs and the qty change at each.
- **Verification** — the inventory-check result and any flagged
  anomalies.
- **Deferred work** — if `split_via_bom` wasn't available, the
  follow-up issue or manual adjustment that's still needed.

## EDGE CASES

- **No linked MO on the SO** — the SO is for a purchased finished good,
  not a manufactured one. Skip phase 4 entirely; only the SO needs
  correction.
- **MO is `IN_PROGRESS`** — `correct_manufacturing_order` will refuse.
  The MO hasn't shipped yet, so there's no close-state to preserve. Use
  `modify_manufacturing_order` directly.
- **Same variant appears on multiple recipe rows / SO rows** — the
  correction tools refuse on ambiguity. Use `modify_manufacturing_order`
  / `modify_sales_order` with the explicit row id, or split the
  correction into two passes that disambiguate by other means.
- **New row quantity below the already-fulfilled quantity** —
  `correct_sales_order` preflight refuses. Either keep the original
  quantity, or fix the fulfillment record manually first.
- **Inventory goes negative after corrections** — the corrections
  over-shot. Likely cause: the MO/SO drift was only a partial
  representation of what shipped, and the rest needs a stock adjustment
  or a parallel correction on a sibling SO. Don't paper over with a
  goodwill stock adjustment without understanding the root cause.
- **Customer received a superset (got extras)** — corrections alone
  won't capture this. Either confirm a picking-error / goodwill add-on
  with the warehouse, or treat the extras as a separate incident.

## RELATED

- PR #536 — `correct_manufacturing_order`, `correct_sales_order`
- Issue #543 — `split_via_bom` (BOM-driven inventory split, pending)
- Issue #523 — Closed-record corrections umbrella
- Issue #532 — `correct_purchase_order` (separate workflow; not used here)
