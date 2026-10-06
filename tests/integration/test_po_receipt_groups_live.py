"""Live pin of Katana's purchase-order receipt-group semantics.

Katana records each ``POST /purchase_order_receive`` call as a receipt group
(``PurchaseOrderRow.group_id``). A partial quantity splits the row into a
received row in a new group plus an open remainder that keeps the original
id. ``PATCH /purchase_orders/{id}`` ``status: NOT_RECEIVED`` undoes every
receipt at once, returns rows and additional cost rows to
``default_group_id`` and merges rows that are identical apart from quantity;
it is refused on a PARTIALLY_RECEIVED PO. A RECEIVED PO refuses new rows.
These rules drive ``correct_purchase_order`` and the spec descriptions; this
file is the evidence.

Everything created here is SDT-tagged and deleted by ``live_artifacts``;
:func:`scratch_purchase_order` leaves every PO stockless, even on failure.
"""

from __future__ import annotations

import pytest
from po_live import (
    D1,
    D2,
    D3,
    POLive,
    open_rows,
    parse,
    received,
    scratch_purchase_order,
)

from katana_public_api_client import KatanaClient
from katana_public_api_client.testing_artifacts import LiveTestArtifacts

pytestmark = [pytest.mark.integration, pytest.mark.live, pytest.mark.asyncio]

ISSUE = "#1142"


@pytest.fixture
def live(live_client: KatanaClient, live_artifacts: LiveTestArtifacts) -> POLive:
    return POLive(live_client.get_async_httpx_client(), live_artifacts, ISSUE)


async def test_receipt_groups_follow_receive_calls_and_collapse_on_revert(
    live: POLive,
) -> None:
    (variant_id,) = await live.product("PO-GROUPS", ["PO-GROUPS-SKU"])
    rows = [
        {"variant_id": variant_id, "quantity": 10, "price_per_unit": 1.0},
        {"variant_id": variant_id, "quantity": 1, "price_per_unit": 1.0},
    ]
    async with scratch_purchase_order(live, "PO-GROUPS-PO", rows) as created:
        po_id = created["id"]
        default_group = created["default_group_id"]
        row_a = next(r for r in created["purchase_order_rows"] if r["quantity"] == 10)
        row_b = next(r for r in created["purchase_order_rows"] if r["quantity"] == 1)
        assert all(
            r["group_id"] == default_group for r in created["purchase_order_rows"]
        )

        # 1. A partial receipt splits the row and opens the first group; the
        #    open remainder keeps the original id.
        await live.receive([(row_a["id"], 9, D1)])
        po = await live.get_po(po_id)
        assert po["status"] == "PARTIALLY_RECEIVED"
        (received_a,) = received(po)
        assert received_a["quantity"] == 9
        assert parse(received_a["received_date"]) == D1
        assert received_a["id"] != row_a["id"]
        group_1 = received_a["group_id"]
        assert group_1 != default_group
        remnant_a = next(r for r in open_rows(po) if r["id"] == row_a["id"])
        assert remnant_a["quantity"] == 1

        # 2. A second call receives the rest into a second, distinct group.
        await live.receive([(remnant_a["id"], 1, D2), (row_b["id"], 1, D2)])
        po = await live.get_po(po_id)
        assert po["status"] == "RECEIVED"
        groups = {r["group_id"] for r in received(po)}
        assert len(groups) == 2 and default_group not in groups
        for row in received(po):
            expected = D1 if row["group_id"] == group_1 else D2
            assert parse(row["received_date"]) == expected

        # 3. A RECEIVED PO refuses new rows.
        denied = await live.http.post(
            "/purchase_order_rows",
            json={
                "purchase_order_id": po_id,
                "variant_id": variant_id,
                "quantity": 1,
                "price_per_unit": 1.0,
            },
        )
        assert denied.status_code == 422, denied.text
        assert "RECEIVED" in denied.text

        # 4. The revert clears every receipt, returns rows to the default
        #    group and merges the rows identical apart from quantity - here
        #    all three, ordered as 10 + 1, come back as one row of 11 that
        #    keeps the lowest id.
        assert (await live.set_status(po_id, "NOT_RECEIVED")).status_code == 200
        po = await live.get_po(po_id)
        assert po["status"] == "NOT_RECEIVED"
        assert not received(po)
        assert all(r["group_id"] == default_group for r in po["purchase_order_rows"])
        (merged,) = po["purchase_order_rows"]
        assert merged["quantity"] == 11
        assert merged["id"] == min(row_a["id"], row_b["id"])

        # 5. The revert is refused while the PO is PARTIALLY_RECEIVED.
        await live.receive([(merged["id"], 9, D1)])
        refused = await live.set_status(po_id, "NOT_RECEIVED")
        assert refused.status_code == 422, refused.text
        assert "PARTIALLY_RECEIVED" in refused.text


async def test_revert_merges_only_identical_rows_and_detaches_cost_rows(
    live: POLive,
) -> None:
    """Rows of one variant stay apart when their price or arrival date
    differs; a cost row on a receipt group moves to the default group."""
    (variant_id,) = await live.product("PO-MERGE", ["PO-MERGE-SKU"])
    rows = [
        {"variant_id": variant_id, "quantity": 9, "price_per_unit": 5.0},
        {"variant_id": variant_id, "quantity": 2, "price_per_unit": 5.0},
        {"variant_id": variant_id, "quantity": 3, "price_per_unit": 7.0},
        {
            "variant_id": variant_id,
            "quantity": 4,
            "price_per_unit": 5.0,
            "arrival_date": "2026-11-30T00:00:00Z",
        },
    ]
    async with scratch_purchase_order(live, "PO-MERGE-PO", rows) as created:
        po_id = created["id"]
        default_group = created["default_group_id"]
        ids = {
            (r["quantity"], r["price_per_unit"]): r["id"]
            for r in created["purchase_order_rows"]
        }
        await live.receive([(ids[(9, 5)], 9, D1)])
        await live.receive([(ids[(2, 5)], 2, D2), (ids[(3, 7)], 3, D2)])
        await live.receive([(ids[(4, 5)], 4, D3)])
        po = await live.get_po(po_id)
        assert po["status"] == "RECEIVED"
        d2_group = next(
            r["group_id"] for r in po["purchase_order_rows"] if r["id"] == ids[(2, 5)]
        )
        costs = (await live.http.get("/additional_costs")).raise_for_status().json()
        tax_rates = (await live.http.get("/tax_rates")).raise_for_status().json()
        cost = await live.http.post(
            "/po_additional_cost_rows",
            json={
                "additional_cost_id": costs["data"][0]["id"],
                "group_id": d2_group,
                "tax_rate_id": tax_rates["data"][0]["id"],
                "price": 12.5,
                "distribution_method": "BY_VALUE",
            },
        )
        assert cost.status_code == 200, cost.text
        cost_id = cost.json()["id"]

        assert (await live.set_status(po_id, "NOT_RECEIVED")).status_code == 200
        po = await live.get_po(po_id)
        after = sorted(
            (r["id"], r["quantity"], r["price_per_unit"])
            for r in po["purchase_order_rows"]
        )
        # 9 + 2 at the same price and arrival merge into the lower id; the
        # 7.00 row and the later-arriving row stay separate.
        assert after == sorted(
            [
                (min(ids[(9, 5)], ids[(2, 5)]), 11, 5),
                (ids[(3, 7)], 3, 7),
                (ids[(4, 5)], 4, 5),
            ]
        )
        moved = (await live.http.get(f"/po_additional_cost_rows/{cost_id}")).json()
        assert moved["group_id"] == default_group


async def test_one_receive_call_is_one_group_whatever_the_row_dates(
    live: POLive,
) -> None:
    """Rows in one call keep their own dates and share one group. A first
    call that receives the whole order keeps the rows in the default group;
    later calls get new groups."""
    variant_a, variant_b, variant_c = await live.product(
        "PO-DATES", ["PO-DATES-A", "PO-DATES-B", "PO-DATES-C"]
    )
    rows = [
        {"variant_id": v, "quantity": 1, "price_per_unit": 1.0}
        for v in (variant_a, variant_b, variant_c)
    ]
    async with scratch_purchase_order(live, "PO-DATES-PO", rows) as created:
        po_id = created["id"]
        default_group = created["default_group_id"]
        by_variant = {r["variant_id"]: r["id"] for r in created["purchase_order_rows"]}

        await live.receive(
            [(by_variant[variant_a], 1, D1), (by_variant[variant_b], 1, D2)]
        )
        po = await live.get_po(po_id)
        got = {r["variant_id"]: r for r in received(po)}
        assert parse(got[variant_a]["received_date"]) == D1
        assert parse(got[variant_b]["received_date"]) == D2
        assert got[variant_a]["group_id"] == got[variant_b]["group_id"] != default_group

        await live.receive([(by_variant[variant_c], 1, D3)])
        assert (await live.set_status(po_id, "NOT_RECEIVED")).status_code == 200

        await live.receive(
            [
                (by_variant[v], 1, d)
                for v, d in ((variant_a, D1), (variant_b, D2), (variant_c, D3))
            ]
        )
        po = await live.get_po(po_id)
        assert po["status"] == "RECEIVED"
        assert {r["group_id"] for r in po["purchase_order_rows"]} == {default_group}


async def test_batch_tracked_row_can_be_received_without_batches(
    live: POLive,
) -> None:
    (variant_id,) = await live.product("PO-BATCH", ["PO-BATCH-SKU"], batch_tracked=True)
    rows = [{"variant_id": variant_id, "quantity": 3, "price_per_unit": 1.0}]
    async with scratch_purchase_order(live, "PO-BATCH-PO", rows) as created:
        await live.receive([(created["purchase_order_rows"][0]["id"], 3, D1)])
        po = await live.get_po(created["id"])
        assert po["status"] == "RECEIVED"
        (row,) = po["purchase_order_rows"]
        assert row["batch_transactions"] == [{"batch_id": None, "quantity": 3}]
