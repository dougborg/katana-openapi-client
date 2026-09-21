"""Material embedded variants exclude fields supported by standalone variants."""

import pytest
from pydantic import ValidationError

from katana_public_api_client.models import (
    CreateMaterialRequest,
    CreateMaterialVariantRequest,
    CreateVariantRequest,
)
from katana_public_api_client.models_pydantic import (
    CreateMaterialRequest as PydanticMaterialRequest,
)


def test_material_variant_serialization_omits_product_only_fields():
    request = CreateMaterialRequest(
        name="Steel",
        variants=[CreateMaterialVariantRequest(sku="STEEL", purchase_price=5)],
    )
    assert request.to_dict()["variants"] == [{"sku": "STEEL", "purchase_price": 5}]
    assert (
        CreateVariantRequest(sku="FINISHED", sales_price=12.34).to_dict()["sales_price"]
        == 12.34
    )


@pytest.mark.parametrize("field", ["sales_price", "product_id", "material_id"])
def test_pydantic_material_variant_rejects_unsupported_embedded_fields(field):
    with pytest.raises(ValidationError):
        PydanticMaterialRequest.model_validate(
            {"name": "Steel", "variants": [{"sku": "STEEL", field: 1}]}
        )
