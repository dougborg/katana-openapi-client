"""Custom-field request formats verified against the live gateway (#1030)."""

from copy import deepcopy
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator
from pydantic import ValidationError
from referencing import Registry
from referencing.jsonschema import DRAFT202012

from katana_public_api_client import models
from katana_public_api_client.models_pydantic import _generated

SPEC = yaml.safe_load(
    (Path(__file__).parents[1] / "docs" / "katana-openapi.yaml").read_text()
)
SCHEMAS = SPEC["components"]["schemas"]
SCHEMA_REGISTRY = Registry().with_resource(
    "urn:katana", DRAFT202012.create_resource(SPEC)
)
OBJECT_REQUESTS = [
    "CreateBomRowRequest",
    "UpdateBomRowRequest",
    "CreateCustomerRequest",
    "UpdateCustomerRequest",
    "CreateManufacturingOrderOperationRowRequest",
    "UpdateManufacturingOrderOperationRowRequest",
    "CreateManufacturingOrderRecipeRowRequest",
    "UpdateManufacturingOrderRecipeRowRequest",
    "CreateManufacturingOrderRequest",
    "UpdateManufacturingOrderRequest",
    "CreateOutsourcedPurchaseOrderRecipeRowRequest",
    "UpdateOutsourcedPurchaseOrderRecipeRowRequest",
    "UpdateProductOperationRowRequest",
    "CreatePurchaseOrderRowRequest",
    "UpdatePurchaseOrderRowRequest",
    "CreatePurchaseOrderRequest",
    "UpdatePurchaseOrderRequest",
    "CreateSupplierRequest",
    "UpdateSupplierRequest",
]
UNION_REQUESTS = [
    "CreateVariantRequest",
    "UpdateVariantRequest",
    "UpdateServiceRequest",
]
UUID = "00000000-0000-0000-0000-000000000001"


def _payload(name: str, value: object) -> dict:
    schema = SCHEMAS[name]
    example = schema.get("example", {})
    if name == "CreateOutsourcedPurchaseOrderRecipeRowRequest":
        example = {
            "purchase_order_row_id": 1,
            "ingredient_variant_id": 2,
            "planned_quantity_per_unit": 3,
        }
    body = {key: deepcopy(example[key]) for key in schema.get("required", [])}
    body["custom_fields"] = value
    return body


@pytest.mark.parametrize("name", OBJECT_REQUESTS)
@pytest.mark.parametrize("value", [None, {}, {UUID: "test", "another-definition": 3}])
def test_object_custom_fields_round_trip(name: str, value: object) -> None:
    body = _payload(name, value)
    attrs_request = getattr(models, name).from_dict(deepcopy(body))
    assert attrs_request.to_dict()["custom_fields"] == value
    pydantic_request = getattr(_generated, name).model_validate(body)
    assert pydantic_request.model_dump()["custom_fields"] == value
    assert pydantic_request.to_attrs().to_dict()["custom_fields"] == value


@pytest.mark.parametrize("name", OBJECT_REQUESTS)
def test_object_custom_fields_reject_legacy_arrays(name: str) -> None:
    with pytest.raises(ValidationError):
        getattr(_generated, name).model_validate(_payload(name, []))


@pytest.mark.parametrize("name", UNION_REQUESTS)
@pytest.mark.parametrize(
    "value",
    [
        {},
        {UUID: True},
        {UUID: None},
        [{"field_name": "Finish", "field_value": "Matte"}],
    ],
)
def test_union_custom_fields_preserve_both_formats(name: str, value: object) -> None:
    body = _payload(name, value)
    Draft202012Validator(
        {"$ref": f"urn:katana#/components/schemas/{name}"}, registry=SCHEMA_REGISTRY
    ).validate(body)
    attrs_request = getattr(models, name).from_dict(deepcopy(body))
    assert attrs_request.to_dict()["custom_fields"] == value
    pydantic_request = getattr(_generated, name).model_validate(body)
    assert pydantic_request.model_dump()["custom_fields"] == value
    assert pydantic_request.to_attrs().to_dict()["custom_fields"] == value


@pytest.mark.parametrize("name", UNION_REQUESTS)
@pytest.mark.parametrize("value", [{"invalid-key": "test"}, {UUID: ["not-scalar"]}])
def test_union_map_keys_and_values_are_validated(name: str, value: object) -> None:
    with pytest.raises(ValidationError):
        getattr(_generated, name).model_validate(_payload(name, value))


@pytest.mark.parametrize(
    "name", ["UpdateCustomerRequest", "UpdateOutsourcedPurchaseOrderRecipeRowRequest"]
)
def test_omitted_custom_fields_stay_omitted_through_attrs_conversion(name: str) -> None:
    request = getattr(models, name)()
    converted = getattr(_generated, name).from_attrs(request)
    assert converted.to_attrs().to_dict() == {}


@pytest.mark.parametrize(
    "name", ["UpdateCustomerRequest", "UpdateOutsourcedPurchaseOrderRecipeRowRequest"]
)
def test_explicit_null_survives_attrs_conversion(name: str) -> None:
    request = getattr(models, name)(custom_fields=None)
    converted = getattr(_generated, name).from_attrs(request)
    assert converted.to_attrs().to_dict() == {"custom_fields": None}


def test_nested_nonnullable_none_is_omitted() -> None:
    request = _generated.UpdateSalesOrderRowRequest.model_validate(
        {"batch_transactions": [{"batch_id": 1, "quantity": None}]}
    )
    assert request.to_attrs().to_dict() == {"batch_transactions": [{"batch_id": 1}]}


@pytest.mark.parametrize("entity", SCHEMAS["CustomFieldEntityType"]["enum"])
def test_custom_field_definition_entities_round_trip(entity):
    body = {
        "label": "Origin",
        "field_type": "shortText",
        "entity_type": entity,
        "source": "test-integration",
    }
    request = models.CreateCustomFieldDefinitionRequest.from_dict(body)
    assert request.to_dict() == body
    typed = _generated.CreateCustomFieldDefinitionRequest.model_validate(body)
    assert typed.to_attrs().to_dict() == body


@pytest.mark.parametrize("targets", [[], ["SalesOrderRow", "ManufacturingOrder"]])
def test_variant_definition_options_without_choices_round_trip(targets):
    body = {
        "label": "Origin",
        "field_type": "shortText",
        "entity_type": "ProductVariant",
        "source": "test-integration",
        "options": {"appearsOn": targets},
    }
    request = models.CreateCustomFieldDefinitionRequest.from_dict(body)
    assert request.to_dict() == body
    typed = _generated.CreateCustomFieldDefinitionRequest.model_validate(body)
    assert typed.to_attrs().to_dict() == body
    update = {"options": {"appearsOn": targets}}
    assert (
        models.UpdateCustomFieldDefinitionRequest.from_dict(update).to_dict() == update
    )
    assert (
        _generated.UpdateCustomFieldDefinitionRequest.model_validate(update)
        .to_attrs()
        .to_dict()
    ) == update


@pytest.mark.parametrize("name", ["Variant", "ServiceVariant", "VariantResponse"])
@pytest.mark.parametrize("value", [{}, {UUID: "US"}, {UUID: False}, {UUID: None}, None])
def test_variant_custom_field_responses_round_trip(name, value):
    body = deepcopy(SCHEMAS[name].get("example", {}))
    body["custom_fields"] = value
    parsed = getattr(models, name).from_dict(body)
    assert parsed.to_dict()["custom_fields"] == value
    typed = getattr(_generated, name).from_attrs(parsed)
    assert typed.model_dump()["custom_fields"] == value


def test_item_custom_field_format_is_sent_as_header():
    from katana_public_api_client.api.variant import get_all_variants
    from katana_public_api_client.models.get_all_variants_x_custom_fields_format import (
        GetAllVariantsXCustomFieldsFormat,
    )

    kwargs = get_all_variants._get_kwargs(
        x_custom_fields_format=GetAllVariantsXCustomFieldsFormat.DEFAULT
    )
    assert kwargs["headers"]["X-Custom-Fields-Format"] == "default"
    assert "X-Custom-Fields-Format" not in kwargs["params"]
    assert "X-Custom-Fields-Format" not in get_all_variants._get_kwargs()["headers"]


@pytest.mark.parametrize(
    "values", [{}, {UUID: False, "00000000-0000-0000-0000-000000000002": None}]
)
def test_cached_variant_persists_uuid_custom_fields(values):
    from sqlmodel import Session, create_engine

    engine = create_engine("sqlite://")
    _generated.CachedVariant.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(_generated.CachedVariant(id=1, sku="TEST", custom_fields=values))
        session.commit()
        session.expunge_all()
        cached = session.get(_generated.CachedVariant, 1)
        assert cached is not None
        assert cached.custom_fields == values
    engine.dispose()


def test_definition_options_python_names_validate_after_model_dump():
    body = {
        "label": "Origin",
        "field_type": "shortText",
        "entity_type": "ProductVariant",
        "source": "test-integration",
        "options": {"appearsOn": ["SalesOrderRow"]},
    }
    request = _generated.CreateCustomFieldDefinitionRequest.model_validate(body)
    restored = _generated.CreateCustomFieldDefinitionRequest.model_validate(
        request.model_dump(exclude_unset=True)
    )
    assert restored.to_attrs().to_dict() == body
