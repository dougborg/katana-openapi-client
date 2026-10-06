"""Live checks that ``correct_purchase_order`` restores receipts exactly (#1142).

Each test builds a scratch PO, receives it in parcels, runs the MCP tool's
implementation against the test tenant and compares the rebuilt PO with the
original: same rows (variant, quantity, price, received date), one group per
original parcel, cost rows on the rebuilt groups, and only the requested
edit applied. Everything is SDT-tagged and deleted by ``live_artifacts``;
:func:`scratch_purchase_order` leaves every PO stockless, even on failure.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from katana_mcp.services.dependencies import Services
from katana_mcp.tools._modification import ModificationResponse
from katana_mcp.tools.foundation.corrections import (
    CorrectPurchaseOrderRequest,
    PORowCorrection,
    _correct_purchase_order_impl,
)
from katana_mcp.typed_cache import TypedCacheEngine
from po_live import (
    D1,
    D2,
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


@pytest_asyncio.fixture
async def correct(live_client: KatanaClient) -> AsyncIterator[Any]:
    cache = TypedCacheEngine(in_memory=True)
    await cache.open()
    context = MagicMock()
    context.request_context.lifespan_context = Services(
        client=live_client, typed_cache=cache
    )

    async def run(po_id: int, *changes: PORowCorrection) -> ModificationResponse:
        response = await _correct_purchase_order_impl(
            CorrectPurchaseOrderRequest(
                id=po_id, row_changes=list(changes), preview=False
            ),
            context,
        )
        assert all(a.succeeded for a in response.actions), [
            (a.operation, a.error) for a in response.actions
        ]
        return response

    try:
        yield run
    finally:
        await cache.close()


def _rows(po: dict[str, Any]) -> list[tuple[int, float, float, datetime | None]]:
    return sorted(
        (
            r["variant_id"],
            r["quantity"],
            r["price_per_unit"],
            parse(r["received_date"]) if r.get("received_date") else None,
        )
        for r in po["purchase_order_rows"]
    )


def _groups_by_date(po: dict[str, Any]) -> dict[datetime, set[int]]:
    out: dict[datetime, set[int]] = {}
    for r in received(po):
        out.setdefault(parse(r["received_date"]), set()).add(r["group_id"])
    return out


async def _two_parcel_po(
    live: POLive, name: str
) -> tuple[list[dict[str, Any]], int, int]:
    """Row specs for 10 of A and 1 of B, plus the two variant ids."""
    variant_a, variant_b = await live.product(name, [f"{name}-A", f"{name}-B"])
    rows = [
        {"variant_id": variant_a, "quantity": 10, "price_per_unit": 1.0},
        {"variant_id": variant_b, "quantity": 1, "price_per_unit": 1.0},
    ]
    return rows, variant_a, variant_b


async def _receive_two_parcels(
    live: POLive, po: dict[str, Any], variant_a: int, variant_b: int
) -> None:
    """9 of A on D1; the last A and the B on D2."""
    row_a = next(r for r in po["purchase_order_rows"] if r["variant_id"] == variant_a)
    row_b = next(r for r in po["purchase_order_rows"] if r["variant_id"] == variant_b)
    await live.receive([(row_a["id"], 9, D1)])
    await live.receive([(row_a["id"], 1, D2), (row_b["id"], 1, D2)])


async def test_correct_purchase_order_rebuilds_receipt_groups(
    live: POLive, correct: Any
) -> None:
    rows, variant_a, variant_b = await _two_parcel_po(live, "PO-CORR")
    async with scratch_purchase_order(live, "PO-CORR-PO", rows) as created:
        po_id = created["id"]
        await _receive_two_parcels(live, created, variant_a, variant_b)
        before = await live.get_po(po_id)
        assert before["status"] == "RECEIVED"
        row_b = next(r for r in received(before) if r["variant_id"] == variant_b)

        await correct(po_id, PORowCorrection(row_id=row_b["id"], price_per_unit=2.5))

        after = await live.get_po(po_id)
        assert after["status"] == "RECEIVED"
        assert _rows(after) == [
            (v, q, 2.5 if v == variant_b else p, d) for v, q, p, d in _rows(before)
        ]
        groups = _groups_by_date(after)
        assert set(groups) == {D1, D2}
        assert all(len(g) == 1 for g in groups.values())
        assert groups[D1] != groups[D2]


async def test_correct_purchase_order_variant_change_on_split_row(
    live: POLive, correct: Any
) -> None:
    """Re-varianting the D1 half of a split row must leave the D2 half on
    the original variant (the revert merges the two halves)."""
    rows, variant_a, variant_b = await _two_parcel_po(live, "PO-CORR-VAR")
    async with scratch_purchase_order(live, "PO-CORR-VAR-PO", rows) as created:
        po_id = created["id"]
        await _receive_two_parcels(live, created, variant_a, variant_b)
        before = await live.get_po(po_id)
        d1_row = next(r for r in received(before) if parse(r["received_date"]) == D1)

        await correct(
            po_id,
            PORowCorrection(row_id=d1_row["id"], new_variant_id=variant_b, quantity=8),
        )

        after = await live.get_po(po_id)
        assert after["status"] == "RECEIVED"
        assert _rows(after) == sorted(
            [(variant_b, 8, 1.0, D1), (variant_a, 1, 1.0, D2), (variant_b, 1, 1.0, D2)]
        )
        assert set(_groups_by_date(after)) == {D1, D2}


async def test_correct_purchase_order_moves_cost_rows_to_rebuilt_groups(
    live: POLive, correct: Any
) -> None:
    rows, variant_a, variant_b = await _two_parcel_po(live, "PO-CORR-COST")
    async with scratch_purchase_order(live, "PO-CORR-COST-PO", rows) as created:
        po_id = created["id"]
        await _receive_two_parcels(live, created, variant_a, variant_b)
        before = await live.get_po(po_id)
        (d2_group,) = _groups_by_date(before)[D2]
        costs = (await live.http.get("/additional_costs")).raise_for_status().json()
        taxes = (await live.http.get("/tax_rates")).raise_for_status().json()
        cost = await live.create(
            "/po_additional_cost_rows",
            {
                "additional_cost_id": costs["data"][0]["id"],
                "group_id": d2_group,
                "tax_rate_id": taxes["data"][0]["id"],
                "price": 12.5,
                "distribution_method": "BY_VALUE",
            },
        )
        landed = await live.get_po(po_id)
        landed_before = sorted(
            (r["variant_id"], parse(r["received_date"]), r["landed_cost"])
            for r in landed["purchase_order_rows"]
        )
        row_b = next(r for r in received(before) if r["variant_id"] == variant_b)

        await correct(po_id, PORowCorrection(row_id=row_b["id"], price_per_unit=2.0))

        after = await live.get_po(po_id)
        (new_d2_group,) = _groups_by_date(after)[D2]
        moved = await live.cost_rows(new_d2_group)
        for copy in moved:
            live.artifacts.record(
                endpoint="/po_additional_cost_rows",
                entity_id=copy["id"],
                issue=ISSUE,
            )
        assert [(c["price"], c["additional_cost_id"]) for c in moved] == [
            (12.5, costs["data"][0]["id"])
        ]
        gone = await live.http.get(f"/po_additional_cost_rows/{cost['id']}")
        assert gone.status_code == 404 or gone.json().get("deleted_at")
        # Katana recalculates landed cost asynchronously (seconds of lag, seen
        # live), so wait for the D1 row to settle. The cost belongs to the D2
        # receipt only, so the D1 row must end with no landed cost, as before.
        d1_before = [x for x in landed_before if x[1] == D1]
        d1_after: list[tuple[int, datetime, float]] = []
        for _ in range(15):
            settled = await live.get_po(po_id)
            d1_after = [
                (r["variant_id"], parse(r["received_date"]), r["landed_cost"])
                for r in received(settled)
                if parse(r["received_date"]) == D1
            ]
            if d1_after == d1_before:
                break
            await asyncio.sleep(2)
        assert d1_after == d1_before


async def test_correct_purchase_order_handles_partially_received(
    live: POLive, correct: Any
) -> None:
    """Katana refuses the revert on a PARTIALLY_RECEIVED PO, so the tool
    receives the open rows first, reverts, rebuilds, replays the original
    receipt and leaves the rest open again. The price edit lands on the
    received split row only."""
    rows, variant_a, variant_b = await _two_parcel_po(live, "PO-CORR-PART")
    async with scratch_purchase_order(live, "PO-CORR-PART-PO", rows) as created:
        po_id = created["id"]
        row_a = next(
            r for r in created["purchase_order_rows"] if r["variant_id"] == variant_a
        )
        await live.receive([(row_a["id"], 9, D1)])
        before = await live.get_po(po_id)
        assert before["status"] == "PARTIALLY_RECEIVED"
        (received_a,) = received(before)

        response = await correct(
            po_id, PORowCorrection(row_id=received_a["id"], price_per_unit=2.5)
        )

        assert [a.operation for a in response.actions][:2] == [
            "receive",
            "update_header",
        ]
        after = await live.get_po(po_id)
        assert after["status"] == "PARTIALLY_RECEIVED"
        assert _rows(after) == sorted(
            [
                (variant_a, 9, 2.5, D1),
                (variant_a, 1, 1.0, None),
                (variant_b, 1, 1.0, None),
            ]
        )
        assert len(open_rows(after)) == 2
