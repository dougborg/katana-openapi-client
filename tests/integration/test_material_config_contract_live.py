"""Pin material configuration create and update gateway contracts (#603)."""

from __future__ import annotations

import pytest

from katana_public_api_client import KatanaClient
from katana_public_api_client.testing_artifacts import LiveTestArtifacts

pytestmark = [pytest.mark.integration, pytest.mark.live, pytest.mark.asyncio]


async def test_material_config_create_omits_response_identifiers(
    live_client: KatanaClient, live_artifacts: LiveTestArtifacts
) -> None:
    """CREATE accepts name/values; PATCH identifies a config by name or ID."""
    http = live_client.get_async_httpx_client()
    config_name = live_artifacts.tag("MATERIAL-CONFIG-NAME")
    initial_value = live_artifacts.tag("MATERIAL-CONFIG-VALUE")
    created = await http.post(
        "/materials",
        json={
            "name": live_artifacts.tag("MATERIAL-CONFIG"),
            "uom": "pcs",
            "configs": [{"name": config_name, "values": [initial_value]}],
            "variants": [
                {
                    "sku": live_artifacts.tag("MATERIAL-CONFIG-SKU"),
                    "config_attributes": [
                        {"config_name": config_name, "config_value": initial_value}
                    ],
                }
            ],
        },
    )
    created.raise_for_status()
    material = created.json()
    live_artifacts.record(endpoint="/materials", entity_id=material["id"], issue="#603")

    assert len(material["configs"]) == 1
    response_config = material["configs"][0]
    assert response_config["name"] == config_name
    assert response_config["values"] == [initial_value]
    assert isinstance(response_config["id"], int)

    # The gateway requires either a config name or ID. A values-only PATCH is
    # rejected before it can mutate the owned resource.
    values_only = await http.patch(
        f"/materials/{material['id']}",
        json={"configs": [{"values": [initial_value]}]},
    )
    assert values_only.status_code == 422
    assert values_only.json()["error"]["message"] == "Config name or id has to be set"

    added_value = live_artifacts.tag("MATERIAL-CONFIG-ADDED-VALUE")
    updated = await http.patch(
        f"/materials/{material['id']}",
        json={
            "configs": [
                {"id": response_config["id"], "values": [initial_value, added_value]}
            ]
        },
    )
    updated.raise_for_status()
    assert updated.json()["configs"][0]["values"] == [initial_value, added_value]
