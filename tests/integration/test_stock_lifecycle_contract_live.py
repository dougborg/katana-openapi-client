"""Verify current #531 omitted-note behavior for owned records."""

from __future__ import annotations

import json
import os
from pathlib import Path

import httpx
import pytest

from katana_public_api_client import KatanaClient
from katana_public_api_client.testing_artifacts import LiveTestArtifacts

pytestmark = [pytest.mark.integration, pytest.mark.live, pytest.mark.asyncio]


def _fixture() -> dict:
    path = Path(
        os.environ.get(
            "KATANA_TEST_BATCH_FIXTURE",
            str(Path(__file__).parent / "fixtures" / "reusable_batch.json"),
        )
    )
    return json.loads(path.read_text())


async def _transfer(http: httpx.AsyncClient, *, stock_transfer_number: str) -> dict:
    response = await http.get(
        "/stock_transfers",
        params={
            "stock_transfer_number": stock_transfer_number,
            "limit": 100,
            "page": 1,
        },
    )
    response.raise_for_status()
    rows = response.json()["data"]
    assert len(rows) == 1
    return rows[0]


async def test_omitted_additional_info_is_preserved_on_sales_order_and_transfer(
    live_client: KatanaClient, live_artifacts: LiveTestArtifacts
) -> None:
    """The gateway preserves notes when its header update omits the field (#531)."""
    fixture = _fixture()
    http = live_client.get_async_httpx_client()
    assert fixture["factory_id"] == live_artifacts.factory_id
    assert fixture["base_url"].rstrip("/") == str(http.base_url).rstrip("/")

    customers = await http.get("/customers", params={"limit": 1, "page": 1})
    customers.raise_for_status()
    sales_order_number = live_artifacts.tag("PATCH-WIPE-SO")
    sales_order = await http.post(
        "/sales_orders",
        json={
            "customer_id": customers.json()["data"][0]["id"],
            "order_no": sales_order_number,
            "additional_info": live_artifacts.tag("SO-NOTE"),
            "sales_order_rows": [
                {
                    "variant_id": fixture["variant_id"],
                    "quantity": 1,
                    "price_per_unit": 1,
                }
            ],
        },
    )
    sales_order.raise_for_status()
    sales_order_id = sales_order.json()["id"]
    live_artifacts.record(
        endpoint="/sales_orders", entity_id=sales_order_id, issue="#531"
    )

    updated_sales_order = await http.patch(
        f"/sales_orders/{sales_order_id}",
        json={"order_no": live_artifacts.tag("PATCH-WIPE-SO-UPDATED")},
    )
    updated_sales_order.raise_for_status()
    sales_order_note = sales_order.json()["additional_info"]
    assert updated_sales_order.json()["additional_info"] == sales_order_note
    fetched_sales_order = await http.get(f"/sales_orders/{sales_order_id}")
    fetched_sales_order.raise_for_status()
    assert fetched_sales_order.json()["additional_info"] == sales_order_note

    locations = await http.get("/locations", params={"limit": 100, "page": 1})
    locations.raise_for_status()
    location_ids = [location["id"] for location in locations.json()["data"]]
    assert len(location_ids) >= 2
    transfer_number = live_artifacts.tag("PATCH-WIPE-ST")
    transfer = await http.post(
        "/stock_transfers",
        json={
            "stock_transfer_number": transfer_number,
            "source_location_id": location_ids[0],
            "target_location_id": location_ids[1],
            "additional_info": live_artifacts.tag("ST-NOTE"),
            "stock_transfer_rows": [
                {"variant_id": fixture["variant_id"], "quantity": "1.0000000000"}
            ],
        },
    )
    transfer.raise_for_status()
    transfer_id = transfer.json()["id"]
    live_artifacts.record(
        endpoint="/stock_transfers", entity_id=transfer_id, issue="#531"
    )
    assert (await _transfer(http, stock_transfer_number=transfer_number))[
        "additional_info"
    ]

    updated_transfer_number = live_artifacts.tag("PATCH-WIPE-ST-UPDATED")
    updated_transfer = await http.patch(
        f"/stock_transfers/{transfer_id}",
        json={"stock_transfer_number": updated_transfer_number},
    )
    updated_transfer.raise_for_status()
    transfer_note = transfer.json()["additional_info"]
    assert updated_transfer.json()["additional_info"] == transfer_note
    assert (await _transfer(http, stock_transfer_number=updated_transfer_number))[
        "additional_info"
    ] == transfer_note
