"""MCP production → MTO delivery, with tenant-aware cleanup (#784).

Requires automatic serial generation configured in the test tenant. Parent
resources are deleted; Katana can retain empty out-of-stock serial identities
(see #983). No serial is unassigned as a fulfillment workaround.
"""

from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import MagicMock

import httpx
import pytest
from katana_mcp.services.dependencies import Services
from katana_mcp.tools.foundation.orders import FulfillOrderRequest, _fulfill_order_impl
from katana_mcp.typed_cache import TypedCacheEngine

from katana_public_api_client import KatanaClient
from katana_public_api_client.testing_artifacts import LiveTestArtifacts

pytestmark = [pytest.mark.integration, pytest.mark.live, pytest.mark.asyncio]


async def _create(
    client: KatanaClient,
    artifacts: LiveTestArtifacts,
    endpoint: str,
    body: dict[str, Any],
) -> dict[str, Any]:
    response = await client.get_async_httpx_client().post(endpoint, json=body)
    response.raise_for_status()
    data = response.json()
    artifacts.record(
        endpoint="/manufacturing_orders"
        if endpoint == "/manufacturing_order_make_to_order"
        else endpoint,
        entity_id=data["id"],
        issue="#784",
    )
    return data


async def _serial_history(client: KatanaClient, serial_id: int) -> list[dict[str, Any]]:
    response = await client.get_async_httpx_client().get("/serial_numbers_stock")
    response.raise_for_status()
    serial = next(item for item in response.json()["data"] if item["id"] == serial_id)
    return serial["transactions"]


@pytest.mark.parametrize("explicit", [False, True])
async def test_mto_generation_and_delivery_preserve_provenance(
    live_client: KatanaClient, live_artifacts: LiveTestArtifacts, explicit: bool
) -> None:
    product = await _create(
        live_client,
        live_artifacts,
        "/products",
        {
            "name": live_artifacts.tag("MTO-SERIAL"),
            "uom": "pcs",
            "is_producible": True,
            "is_sellable": True,
            "serial_tracked": True,
            "variants": [{"sku": live_artifacts.tag("MTO-SKU")}],
        },
    )
    customer = await _create(
        live_client,
        live_artifacts,
        "/customers",
        {
            "name": live_artifacts.tag("MTO-CUSTOMER"),
        },
    )
    so = await _create(
        live_client,
        live_artifacts,
        "/sales_orders",
        {
            "order_no": live_artifacts.tag("MTO-SO"),
            "customer_id": customer["id"],
            "sales_order_rows": [
                {"variant_id": product["variants"][0]["id"], "quantity": 1}
            ],
        },
    )
    row_id = so["sales_order_rows"][0]["id"]
    mo = await _create(
        live_client,
        live_artifacts,
        "/manufacturing_order_make_to_order",
        {
            "sales_order_row_id": row_id,
            "create_subassemblies": False,
        },
    )
    http = live_client.get_async_httpx_client()
    production_ids: list[int] = []

    async def record_write(response: httpx.Response) -> None:
        if response.request.method != "POST" or not response.is_success:
            return
        await response.aread()
        endpoint = response.request.url.path.rsplit("/", 1)[-1]
        if endpoint == "sales_order_fulfillments":
            # Record before the MCP parses or asserts anything about the response.
            live_artifacts.record(
                endpoint="/sales_order_fulfillments",
                entity_id=response.json()["id"],
                issue="#784",
            )
        elif endpoint == "manufacturing_order_productions":
            # Completed productions are deleted with their already-ledgered MO.
            production_ids.append(response.json()["id"])

    http.event_hooks["response"].append(record_write)
    cache = TypedCacheEngine(in_memory=True)
    await cache.open()
    try:
        context = MagicMock()
        context.request_context.lifespan_context = Services(
            client=live_client, typed_cache=cache
        )
        completed_at = datetime(2026, 9, 21, 12, tzinfo=UTC)
        picked_at = completed_at + timedelta(minutes=1)
        request = FulfillOrderRequest(
            order_id=mo["id"],
            order_type="manufacturing",
            generate_serial_numbers=True,
            completed_at=completed_at,
        )
        preview = await _fulfill_order_impl(request, context)
        assert not any(w.startswith("BLOCK:") for w in preview.warnings)
        assert not production_ids
        produced = await _fulfill_order_impl(
            request.model_copy(update={"preview": False}), context
        )
        assert produced.status == "DONE"
        assert len(production_ids) == 1
        serial_ids = produced.fulfilled_rows[0].serial_numbers
        assert len(serial_ids) == 1
        serial_id = serial_ids[0]
        before = await _serial_history(live_client, serial_id)
        origin = next(
            t
            for t in before
            if t["resource_type"] == "ManufacturingOrder"
            and t["resource_id"] == mo["id"]
        )
        assert origin["quantity_change"] == 1
        assert datetime.fromisoformat(origin["transaction_date"]) == completed_at
        reservation = [
            t
            for t in before
            if t["resource_type"] == "SalesOrderRow" and t["resource_id"] == row_id
        ]
        assert len(reservation) == 1 and reservation[0]["transaction_date"] is None
        assert reservation[0]["quantity_change"] == -1

        rows = (
            [
                {
                    "sales_order_row_id": row_id,
                    "traceability": [{"serial_number_id": serial_id, "quantity": 1}],
                }
            ]
            if explicit
            else None
        )
        delivery = FulfillOrderRequest.model_validate(
            {
                "order_id": so["id"],
                "order_type": "sales",
                "completed_at": picked_at,
                "rows": rows,
            }
        )
        preview = await _fulfill_order_impl(delivery, context)
        assert not any(w.startswith("BLOCK:") for w in preview.warnings)
        assert preview.fulfilled_rows[0].serial_numbers == serial_ids
        delivered = await _fulfill_order_impl(
            delivery.model_copy(update={"preview": False}), context
        )
        assert delivered.status == "DELIVERED"
        assert delivered.picked_date is not None
        assert datetime.fromisoformat(delivered.picked_date) == picked_at
        after = await _serial_history(live_client, serial_id)
        assert origin in after  # Same production transaction identity and timestamp.
        shipments = [
            t
            for t in after
            if t["resource_type"] == "SalesOrderRow" and t["resource_id"] == row_id
        ]
        assert len(shipments) == 1 and shipments[0]["quantity_change"] == -1
        assert datetime.fromisoformat(shipments[0]["transaction_date"]) == picked_at
    finally:
        await cache.close()
        http.event_hooks["response"].remove(record_write)
