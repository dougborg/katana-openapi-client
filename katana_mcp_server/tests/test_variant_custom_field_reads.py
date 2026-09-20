"""Variant detail must not invent an empty array for null or unavailable values."""

import pytest
from katana_mcp.tools.foundation.items import _dict_to_variant_details

from katana_public_api_client.models import Variant
from katana_public_api_client.models_pydantic._generated import CachedVariant


@pytest.mark.parametrize("kind", ["attrs", "cache", "dict"])
@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"custom_fields": None},
        {"custom_fields": []},
        {"custom_fields": [{"field_name": "Grade", "field_value": "A"}]},
    ],
)
def test_variant_detail_retains_null_empty_and_legacy_values(kind, payload):
    data = {"id": 1, "sku": "FIXTURE", **payload}
    if kind == "attrs":
        record = Variant.from_dict(data)
    elif kind == "cache":
        record = CachedVariant.model_validate(data)
    else:
        record = data
    result = _dict_to_variant_details(record)
    # Omitted and null are intentionally indistinguishable in the existing cache.
    assert result.model_dump()["custom_fields"] == payload.get("custom_fields")
