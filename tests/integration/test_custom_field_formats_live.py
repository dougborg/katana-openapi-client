"""Validate custom-field request formats without modifying existing records (#1030)."""

from __future__ import annotations

from typing import Any

import pytest

from katana_public_api_client import KatanaClient
from katana_public_api_client.testing_artifacts import LiveTestArtifacts

pytestmark = [pytest.mark.integration, pytest.mark.live, pytest.mark.asyncio]

OBJECT_ENDPOINTS = [
    ("POST", "/bom_rows"),
    ("PATCH", "/bom_rows/-1"),
    ("POST", "/customers"),
    ("PATCH", "/customers/-1"),
    ("POST", "/manufacturing_order_operation_rows"),
    ("PATCH", "/manufacturing_order_operation_rows/-1"),
    ("POST", "/manufacturing_order_recipe_rows"),
    ("PATCH", "/manufacturing_order_recipe_rows/-1"),
    ("POST", "/manufacturing_orders"),
    ("PATCH", "/manufacturing_orders/-1"),
    ("PATCH", "/product_operation_rows/-1"),
    ("POST", "/purchase_order_rows"),
    ("PATCH", "/purchase_order_rows/-1"),
    ("POST", "/purchase_orders"),
    ("PATCH", "/purchase_orders/-1"),
    ("POST", "/suppliers"),
    ("PATCH", "/suppliers/-1"),
]


def _custom_errors(response: Any) -> list[dict[str, Any]]:
    return [
        detail
        for detail in response.json().get("error", {}).get("details", [])
        if "custom_fields" in detail.get("path", "")
        or detail.get("info", {}).get("additionalProperty") == "custom_fields"
    ]


@pytest.mark.parametrize(("method", "path"), OBJECT_ENDPOINTS)
async def test_object_input_validation(
    live_client: KatanaClient, method: str, path: str
) -> None:
    http = live_client.get_async_httpx_client()
    # Creates omit mandatory business fields; PATCH targets are nonexistent.
    # The malformed-array control proves the gateway validates before lookup.
    rejected = await http.request(method, path, json={"custom_fields": []})
    assert rejected.status_code == 422
    assert any(error["code"] == "type" for error in _custom_errors(rejected))
    for value in [{}, None]:
        accepted_shape = await http.request(method, path, json={"custom_fields": value})
        assert accepted_shape.status_code in {400, 404, 422}
        assert not _custom_errors(accepted_shape)
        # A lookup/domain error does not prove values can be persisted, only
        # that this format reaches the endpoint after gateway validation.


@pytest.mark.parametrize(
    ("method", "path"),
    [("POST", "/variants"), ("PATCH", "/variants/-1"), ("PATCH", "/services/-1")],
)
async def test_variant_service_union_validation(
    live_client: KatanaClient, method: str, path: str
) -> None:
    http = live_client.get_async_httpx_client()
    base = {"product_id": -1} if method == "POST" else {}
    for value in [{}, [], {"00000000-0000-0000-0000-000000000001": "test"}]:
        response = await http.request(
            method, path, json={**base, "custom_fields": value}
        )
        assert response.status_code in {400, 404, 422}
        assert not _custom_errors(response)
    invalid = await http.request(
        method, path, json={**base, "custom_fields": {"not-a-uuid": "test"}}
    )
    assert invalid.status_code == 422
    assert any(
        error["code"] == "additionalProperties" for error in _custom_errors(invalid)
    )


@pytest.mark.parametrize("endpoint", ["/customers", "/suppliers"])
async def test_empty_object_and_null_on_owned_contact(
    live_client: KatanaClient, live_artifacts: LiveTestArtifacts, endpoint: str
) -> None:
    http = live_client.get_async_httpx_client()
    created = await http.post(
        endpoint,
        json={"name": live_artifacts.tag("CUSTOM-FIELDS"), "custom_fields": {}},
    )
    created.raise_for_status()
    entity_id = created.json()["id"]
    live_artifacts.record(endpoint=endpoint, entity_id=entity_id, issue="#1030")
    response = await http.patch(f"{endpoint}/{entity_id}", json={"custom_fields": None})
    response.raise_for_status()
    assert response.json()["custom_fields"] is None
