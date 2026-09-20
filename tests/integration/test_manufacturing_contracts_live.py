"""Pin the three request-contract corrections verified under #830."""

from __future__ import annotations

import pytest

from katana_public_api_client import KatanaClient
from katana_public_api_client.testing_artifacts import LiveTestArtifacts

pytestmark = [pytest.mark.integration, pytest.mark.live, pytest.mark.asyncio]


def _rejected_properties(payload: dict) -> set[str]:
    return {
        detail["info"]["additionalProperty"]
        for detail in payload["error"]["details"]
        if detail["code"] == "additionalProperties"
    }


async def test_manufacturing_partial_update_contracts(
    live_client: KatanaClient, live_artifacts: LiveTestArtifacts
) -> None:
    http = live_client.get_async_httpx_client()
    listing = await http.get("/manufacturing_orders", params={"limit": 1, "page": 1})
    listing.raise_for_status()
    source = listing.json()["data"][0]
    created = await http.post(
        "/manufacturing_orders",
        json={
            "variant_id": source["variant_id"],
            "location_id": source["location_id"],
            "planned_quantity": 1,
            "order_no": live_artifacts.tag("CONTRACT-MO"),
        },
    )
    created.raise_for_status()
    mo_id = created.json()["id"]
    live_artifacts.record(
        endpoint="/manufacturing_orders", entity_id=mo_id, issue="#830"
    )
    # A successful name-only PATCH was verified on an owned operation row.
    # Pin gateway acceptance here with a missing target plus an invalid-type
    # control, avoiding any dependency on a tenant's operation catalog.
    row_id = -1
    renamed = await http.patch(
        f"/manufacturing_order_operation_rows/{row_id}",
        json={"operation_name": live_artifacts.tag("CONTRACT-OP")},
    )
    assert renamed.status_code == 422
    assert (
        renamed.json()["error"]["message"] == "Invalid manufacturing order operation id"
    )
    invalid = await http.patch(
        f"/manufacturing_order_operation_rows/{row_id}", json={"operation_name": 123}
    )
    assert invalid.status_code == 422
    assert any(
        detail["path"] == "/operation_name" and detail["code"] == "type"
        for detail in invalid.json()["error"]["details"]
    )
    for path, body, rejected in [
        (
            f"/manufacturing_order_operation_rows/{row_id}",
            {"manufacturing_order_id": mo_id},
            "manufacturing_order_id",
        ),
        (f"/manufacturing_orders/{mo_id}", {"serial_numbers": []}, "serial_numbers"),
    ]:
        response = await http.patch(path, json=body)
        assert response.status_code == 422
        assert rejected in _rejected_properties(response.json())

    # With no resource type or labels, the endpoint accepts a no-op, returning
    # no body. This must not try to parse the 204 response as JSON.
    response = await http.post("/serial_numbers", json={"resource_id": mo_id})
    assert response.status_code == 204
    assert response.content == b""
