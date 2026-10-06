"""Shared helpers for the live purchase-order receipt tests.

Every scratch PO goes through :func:`scratch_purchase_order`, whose exit
always leaves the PO stockless (finishing any open receipt first, since
Katana refuses the revert while PARTIALLY_RECEIVED). That runs even when an
assertion fails, so ``live_artifacts`` can always delete what it recorded.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

import httpx

from katana_public_api_client.testing_artifacts import LiveTestArtifacts

D1 = datetime(2026, 9, 11, 21, 20, tzinfo=UTC)
D2 = datetime(2026, 9, 14, 21, 58, tzinfo=UTC)
D3 = datetime(2026, 9, 20, 9, 0, tzinfo=UTC)


def iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def parse(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class POLive:
    """Thin raw-HTTP access to one tenant, recording what it creates."""

    def __init__(
        self, http: httpx.AsyncClient, artifacts: LiveTestArtifacts, issue: str
    ) -> None:
        self.http = http
        self.artifacts = artifacts
        self.issue = issue

    async def create(self, endpoint: str, body: dict[str, Any]) -> dict[str, Any]:
        response = await self.http.post(endpoint, json=body)
        response.raise_for_status()
        data = response.json()
        self.artifacts.record(endpoint=endpoint, entity_id=data["id"], issue=self.issue)
        return data

    async def location_id(self) -> int:
        response = await self.http.get("/locations")
        return response.raise_for_status().json()["data"][0]["id"]

    async def product(self, name: str, skus: list[str], **extra: Any) -> list[int]:
        product = await self.create(
            "/products",
            {
                "name": self.artifacts.tag(name),
                "uom": "pcs",
                "is_producible": False,
                "is_purchasable": True,
                "variants": [{"sku": self.artifacts.tag(s)} for s in skus],
                **extra,
            },
        )
        return [v["id"] for v in product["variants"]]

    async def supplier(self, name: str) -> int:
        supplier = await self.create("/suppliers", {"name": self.artifacts.tag(name)})
        return supplier["id"]

    async def get_po(self, po_id: int) -> dict[str, Any]:
        response = await self.http.get(f"/purchase_orders/{po_id}")
        return response.raise_for_status().json()

    async def receive(self, items: list[tuple[int, float, datetime]]) -> None:
        response = await self.http.post(
            "/purchase_order_receive",
            json=[
                {"purchase_order_row_id": i, "quantity": q, "received_date": iso(d)}
                for i, q, d in items
            ],
        )
        assert response.status_code == 204, response.text

    async def set_status(self, po_id: int, status: str) -> httpx.Response:
        return await self.http.patch(
            f"/purchase_orders/{po_id}", json={"status": status}
        )

    async def cost_rows(self, group_id: int) -> list[dict[str, Any]]:
        response = await self.http.get(
            "/po_additional_cost_rows", params={"group_id": group_id}
        )
        return [
            r
            for r in response.raise_for_status().json()["data"]
            if r["group_id"] == group_id
        ]

    async def leave_stockless(self, po_id: int) -> None:
        po = await self.get_po(po_id)
        if po["status"] == "PARTIALLY_RECEIVED":
            await self.receive(
                [
                    (r["id"], r["quantity"], D3)
                    for r in po["purchase_order_rows"]
                    if not r.get("received_date")
                ]
            )
            po = await self.get_po(po_id)
        if po["status"] == "RECEIVED":
            reverted = await self.set_status(po_id, "NOT_RECEIVED")
            assert reverted.status_code == 200, reverted.text


def received(po: dict[str, Any]) -> list[dict[str, Any]]:
    return [r for r in po["purchase_order_rows"] if r.get("received_date")]


def open_rows(po: dict[str, Any]) -> list[dict[str, Any]]:
    return [r for r in po["purchase_order_rows"] if not r.get("received_date")]


@asynccontextmanager
async def scratch_purchase_order(
    live: POLive, name: str, rows: list[dict[str, Any]]
) -> AsyncIterator[dict[str, Any]]:
    """Create a tagged NOT_RECEIVED PO and always leave it stockless."""
    po = await live.create(
        "/purchase_orders",
        {
            "order_no": live.artifacts.tag(name),
            "supplier_id": await live.supplier(f"{name}-SUP"),
            "location_id": await live.location_id(),
            "status": "NOT_RECEIVED",
            "purchase_order_rows": rows,
        },
    )
    try:
        yield po
    finally:
        await live.leave_stockless(po["id"])
