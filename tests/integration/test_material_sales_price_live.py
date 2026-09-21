"""Live material/product price asymmetry with tenant-scoped cleanup (#1083)."""

import pytest

from katana_public_api_client import KatanaClient
from katana_public_api_client.testing_artifacts import LiveTestArtifacts

pytestmark = [pytest.mark.integration, pytest.mark.live, pytest.mark.asyncio]


async def test_material_price_requires_variant_update(
    live_client: KatanaClient, live_artifacts: LiveTestArtifacts
) -> None:
    http = live_client.get_async_httpx_client()
    for endpoint, nested_price in [
        ("/materials", True),
        ("/materials", False),
        ("/products", True),
    ]:
        variant: dict[str, str | float] = {
            "sku": live_artifacts.tag(f"PRICE-{endpoint[1:]}-{nested_price}")
        }
        body = {
            "name": live_artifacts.tag(f"PRICE-{endpoint[1:]}-{nested_price}"),
            "uom": "pcs",
            "is_sellable": True,
            "variants": [variant],
        }
        if nested_price:
            body["variants"][0]["sales_price"] = 12.34
        response = await http.post(endpoint, json=body)
        if response.is_success:
            live_artifacts.record(
                endpoint=endpoint, entity_id=response.json()["id"], issue="#1083"
            )
        if endpoint == "/materials" and nested_price:
            assert response.status_code == 422
            assert any(
                detail.get("info", {}).get("additionalProperty") == "sales_price"
                for detail in response.json()["error"]["details"]
            )
            continue
        response.raise_for_status()
        variant_id = response.json()["variants"][0]["id"]
        if endpoint == "/materials":
            patched = await http.patch(
                f"/variants/{variant_id}", json={"sales_price": 12.34}
            )
            patched.raise_for_status()
        fetched = await http.get(f"/variants/{variant_id}")
        fetched.raise_for_status()
        assert fetched.json()["sales_price"] == 12.34
