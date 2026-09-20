"""Verify sales-return filters against distinct temporary returns (#939)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import httpx
import pytest

from katana_public_api_client import KatanaClient
from katana_public_api_client.testing_artifacts import LiveTestArtifacts

pytestmark = [pytest.mark.integration, pytest.mark.live, pytest.mark.asyncio]


async def _create_sales_return(
    *,
    http: httpx.AsyncClient,
    live_artifacts: LiveTestArtifacts,
    customer_id: int,
    location_id: int,
    variant_id: int,
    suffix: str,
) -> tuple[dict, dict]:
    """Create a tracked order and return that fixture teardown deletes."""
    order_no = live_artifacts.tag(f"SALES-RETURN-SO-{suffix}")
    order_response = await http.post(
        "/sales_orders",
        json={
            "customer_id": customer_id,
            "order_no": order_no,
            "sales_order_rows": [
                {"variant_id": variant_id, "quantity": 1, "price_per_unit": 1}
            ],
        },
    )
    order_response.raise_for_status()
    order = order_response.json()
    live_artifacts.record(endpoint="/sales_orders", entity_id=order["id"], issue="#939")

    return_response = await http.post(
        "/sales_returns",
        json={
            "sales_order_id": order["id"],
            "return_location_id": location_id,
            "order_no": live_artifacts.tag(f"SALES-RETURN-{suffix}"),
        },
    )
    return_response.raise_for_status()
    sales_return = return_response.json()
    live_artifacts.record(
        endpoint="/sales_returns", entity_id=sales_return["id"], issue="#939"
    )
    return order, sales_return


async def _returned_ids(http: httpx.AsyncClient, **params: int | str) -> set[int]:
    response = await http.get(
        "/sales_returns", params={"limit": 100, "page": 1, **params}
    )
    response.raise_for_status()
    return {entry["id"] for entry in response.json()["data"]}


async def test_sales_return_filters_match_live_api(
    live_client: KatanaClient, live_artifacts: LiveTestArtifacts
) -> None:
    fixture_path = Path(
        os.environ.get(
            "KATANA_TEST_BATCH_FIXTURE",
            str(Path(__file__).parent / "fixtures" / "reusable_batch.json"),
        )
    )
    fixture = json.loads(fixture_path.read_text())
    http = live_client.get_async_httpx_client()
    assert fixture["factory_id"] == live_artifacts.factory_id
    assert fixture["base_url"].rstrip("/") == str(http.base_url).rstrip("/")

    factory = await http.get("/factory")
    factory.raise_for_status()
    location_id = factory.json()["default_sales_location_id"]
    customers = await http.get("/customers", params={"limit": 1, "page": 1})
    customers.raise_for_status()
    customer_id = customers.json()["data"][0]["id"]

    first_order, first_return = await _create_sales_return(
        http=http,
        live_artifacts=live_artifacts,
        customer_id=customer_id,
        location_id=location_id,
        variant_id=fixture["variant_id"],
        suffix="FIRST",
    )
    _, second_return = await _create_sales_return(
        http=http,
        live_artifacts=live_artifacts,
        customer_id=customer_id,
        location_id=location_id,
        variant_id=fixture["variant_id"],
        suffix="SECOND",
    )

    all_ids = await _returned_ids(http)
    assert {first_return["id"], second_return["id"]} <= all_ids
    for sales_return, return_date in [
        (first_return, "2026-09-18"),
        (second_return, "2026-09-19"),
    ]:
        dated = await http.patch(
            f"/sales_returns/{sales_return['id']}", json={"return_date": return_date}
        )
        dated.raise_for_status()
        assert dated.json()["return_date"].startswith(return_date)
    assert await _returned_ids(http, order_no=first_return["order_no"]) == {
        first_return["id"]
    }
    assert await _returned_ids(http, sales_order_no=first_order["order_no"]) == all_ids
    assert await _returned_ids(http, return_location_id=-1) == set()
    assert await _returned_ids(http, status="RETURNED_ALL") == set()
    assert await _returned_ids(http, refund_status="REFUNDED") == set()
    assert await _returned_ids(http, order_return_date_min="2026-09-19") == {
        second_return["id"]
    }

    # The API is lenient with unknown query keys. These portal/local names must
    # not be exposed as functional filters when they return the unfiltered set.
    assert (
        await _returned_ids(http, return_order_no=first_return["order_no"]) == all_ids
    )
    assert await _returned_ids(http, sales_order_id=first_order["id"]) == all_ids
    assert await _returned_ids(http, return_date_min="2026-09-19") == all_ids
