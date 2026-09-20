"""Request/response material-config model boundaries (#603)."""

from __future__ import annotations

from katana_public_api_client.models import (
    CreateMaterialRequest,
    CreateVariantRequest,
    MaterialConfig,
    UpdateMaterialRequestConfigsItem,
)
from katana_public_api_client.models_pydantic._generated import (
    CreateMaterialRequest as PydanticCreateMaterialRequest,
    MaterialConfig as PydanticMaterialConfig,
)


def test_create_material_config_has_no_response_identifiers() -> None:
    config = MaterialConfig(name="Grade", values=["Premium"])
    request = CreateMaterialRequest(
        name="Steel", variants=[CreateVariantRequest(sku="STEEL-001")], configs=[config]
    )

    assert config.to_dict() == {"name": "Grade", "values": ["Premium"]}
    assert request.to_dict()["configs"] == [{"name": "Grade", "values": ["Premium"]}]


def test_pydantic_create_material_config_has_no_response_identifiers() -> None:
    config = PydanticMaterialConfig(name="Grade", values=["Premium"])
    request = PydanticCreateMaterialRequest.model_validate(
        {
            "name": "Steel",
            "variants": [{"sku": "STEEL-001"}],
            "configs": [config.model_dump()],
        }
    )

    assert config.model_dump() == {"name": "Grade", "values": ["Premium"]}
    assert request.configs == [config]


def test_update_material_config_can_identify_by_id() -> None:
    config = UpdateMaterialRequestConfigsItem(id=10, values=["Premium"])

    assert config.to_dict() == {"id": 10, "values": ["Premium"]}
