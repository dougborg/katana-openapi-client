"""Verify allocation quantities using the single approved retained batch (#1053).

The product and batch are reusable, because the API has no batch-delete endpoint.
Only the temporary sales order is created here; the ledger fixture deletes it.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from katana_public_api_client import KatanaClient
from katana_public_api_client.models import (
    SalesOrderRowBatchTransactionUpdate,
    UpdateSalesOrderRowRequest,
)
from katana_public_api_client.testing_artifacts import LiveTestArtifacts

pytestmark = [pytest.mark.integration, pytest.mark.live, pytest.mark.asyncio]


async def test_sales_row_omitted_batch_quantity_resets_to_zero(
    live_client: KatanaClient, live_artifacts: LiveTestArtifacts
) -> None:
    path = Path(
        os.environ.get(
            "KATANA_TEST_BATCH_FIXTURE",
            str(Path(__file__).parent / "fixtures" / "reusable_batch.json"),
        )
    )
    fixture = json.loads(path.read_text())
    http = live_client.get_async_httpx_client()
    # Refuse all writes before resolving tenant-specific fixture IDs.
    assert fixture["factory_id"] == live_artifacts.factory_id
    assert fixture["base_url"].rstrip("/") == str(http.base_url).rstrip("/")
    product = await http.get(f"/products/{fixture['product_id']}")
    product.raise_for_status()
    assert product.json()["name"] == fixture["tag"]
    assert any(
        variant["id"] == fixture["variant_id"] for variant in product.json()["variants"]
    )
    customers = await http.get("/customers", params={"limit": 1, "page": 1})
    customers.raise_for_status()
    created = await http.post(
        "/sales_orders",
        json={
            "customer_id": customers.json()["data"][0]["id"],
            "order_no": live_artifacts.tag("BATCH-QUANTITY"),
            "sales_order_rows": [
                {
                    "variant_id": fixture["variant_id"],
                    "quantity": 1,
                    "price_per_unit": 1,
                }
            ],
        },
    )
    created.raise_for_status()
    order_id = created.json()["id"]
    live_artifacts.record(endpoint="/sales_orders", entity_id=order_id, issue="#1053")
    order = await http.get(f"/sales_orders/{order_id}")
    order.raise_for_status()
    row_id = order.json()["sales_order_rows"][0]["id"]
    for allocation, expected in [
        (SalesOrderRowBatchTransactionUpdate(batch_id=fixture["batch_id"]), 0),
        (
            SalesOrderRowBatchTransactionUpdate(
                batch_id=fixture["batch_id"], quantity=1
            ),
            1,
        ),
        (SalesOrderRowBatchTransactionUpdate(batch_id=fixture["batch_id"]), 0),
    ]:
        body = UpdateSalesOrderRowRequest(batch_transactions=[allocation])
        updated = await http.patch(f"/sales_order_rows/{row_id}", json=body.to_dict())
        updated.raise_for_status()
        assert updated.json()["batch_transactions"] == [
            {"batch_id": fixture["batch_id"], "quantity": expected}
        ]


async def test_production_ingredient_requires_batch_quantity(
    live_client: KatanaClient,
) -> None:
    # A nonexistent ingredient prevents writes. Its domain validator rejects
    # missing quantity before looking up the ingredient, even though the gateway
    # schema allows omission. A quantity-bearing control reaches the lookup.
    http = live_client.get_async_httpx_client()
    for allocation, message in [
        (
            {"batch_id": -1},
            "Traceability entries without a serial number must provide a positive quantity",
        ),
        ({"batch_id": -1, "quantity": 1}, "Production ingredient -1 not found"),
    ]:
        response = await http.patch(
            "/manufacturing_order_production_ingredients/-1",
            json={"batch_transactions": [allocation]},
        )
        assert response.status_code == 422
        assert message in response.text
