"""Pin #782 optional read contracts and the bounded wire-shape probe."""

from collections import Counter

import httpx
import pytest
from scripts.probe_custom_field_reads import field_contract, probe, summarize

from katana_public_api_client import models
from katana_public_api_client.models_pydantic import _generated as pydantic_models

PAYLOADS = (
    {},
    {"custom_fields": None},
    {"custom_fields": []},
    {"custom_fields": [{"field_name": "Grade", "field_value": "A"}]},
)


@pytest.fixture(scope="module")
def schemas(openapi_spec):
    return openapi_spec["components"]["schemas"]


@pytest.mark.parametrize("name", ["Variant", "VariantResponse", "ServiceVariant"])
@pytest.mark.parametrize("payload", PAYLOADS)
def test_legacy_variant_field_roundtrip_preserves_omitted_null_array(
    schemas, name, payload
):
    contract = field_contract(schemas=schemas, name=name)
    assert contract["declared"] is True
    assert contract["required"] is False
    assert summarize(records=[payload], contract=contract)["violations"] == {}
    data = {"id": 1, "sku": "FIXTURE", **payload}
    if name == "ServiceVariant":
        data["service_id"] = 2
    attrs_record = getattr(models, name).from_dict(data)
    assert attrs_record.to_dict() == data
    model = getattr(pydantic_models, name).from_attrs(attrs_obj=attrs_record)
    assert ("custom_fields" in model.model_fields_set) == ("custom_fields" in payload)
    assert model.model_dump(mode="json", exclude_unset=True) == data


@pytest.mark.parametrize("name", ["Product", "Material", "Service"])
@pytest.mark.parametrize("payload", PAYLOADS)
def test_item_top_level_field_is_undeclared_and_attrs_retains_extras(
    schemas, name, payload
):
    contract = field_contract(schemas=schemas, name=name)
    assert contract["declared"] is False
    assert contract["required"] is False
    data = {"id": 1, "name": "Fixture", "type": name.lower(), **payload}
    attrs_record = getattr(models, name).from_dict(data)
    assert attrs_record.to_dict() == data
    assert attrs_record.additional_properties == payload
    model = getattr(pydantic_models, name).from_attrs(attrs_obj=attrs_record)
    # Undeclared fields are ignored by the current typed Pydantic contract.
    assert "custom_fields" not in type(model).model_fields
    assert "custom_fields" not in model.model_dump(exclude_unset=True)


def test_probe_reports_shape_drift_without_echoing_values(schemas):
    contract = field_contract(schemas=schemas, name="Variant")
    result = summarize(
        records=[{"custom_fields": {"secret": "tenant value"}}], contract=contract
    )
    assert result["shapes"] == {"object": 1}
    assert result["violations"] == {"custom_fields/: type": 1}
    assert "secret" not in str(result)
    assert "tenant value" not in str(result)


@pytest.mark.asyncio
async def test_probe_bounds_requests_and_marks_empty_detail_unverified(schemas):
    requests = []

    def handler(request):
        requests.append(request)
        assert request.method == "GET"
        if request.url.path == "/services":
            return httpx.Response(200, json={"data": []})
        if request.url.params:
            assert dict(request.url.params) == {"limit": "2", "page": "1"}
            return httpx.Response(
                200, json={"data": [{"id": 1}, {"id": 2, "custom_fields": None}]}
            )
        return httpx.Response(200, json={"id": 1, "custom_fields": []})

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="https://test.invalid"
    ) as http:
        report = await probe(http=http, schemas=schemas, limit=2)
    assert len(requests) == 7
    assert Counter(request.url.path for request in requests)["/variants/1"] == 1
    assert report["services"]["detail"] == "not probed: empty first page"
    assert report["variants"]["list"]["shapes"] == {"absent": 1, "null": 1}
    assert report["variants"]["detail"]["shapes"] == {"empty_array": 1}
