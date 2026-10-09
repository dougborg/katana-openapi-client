"""Response contracts verified by the October 2026 test-tenant audit."""

from pathlib import Path

import httpx
import pytest
from jsonschema import Draft202012Validator
from scripts.validate_response_examples import _build_local_registry, load_yaml_spec
from sqlalchemy import create_engine
from sqlmodel import SQLModel

from katana_public_api_client import Client, models, models_pydantic
from katana_public_api_client.api.sales_orders import (
    create_sales_order_shipping_fee,
    get_sales_order_shipping_fee,
)

SPEC = load_yaml_spec(Path(__file__).parents[1] / "docs/katana-openapi.yaml")
REGISTRY = _build_local_registry(SPEC)


def validate(name, body):
    Draft202012Validator(
        {"$ref": f"urn:openapi-spec#/components/schemas/{name}"}, registry=REGISTRY
    ).validate(body)


def round_trip(name, body):
    validate(name, body)
    attrs_model = getattr(models, name).from_dict(body)
    assert attrs_model.to_dict() == body
    pydantic_model = getattr(models_pydantic, name).from_attrs(attrs_model)
    assert pydantic_model.model_dump(mode="json", exclude_unset=True) == body
    return attrs_model


def test_unstarted_operation_preserves_null_actuals_and_optional_resources():
    round_trip(
        "ManufacturingOrderOperationRow",
        {
            "id": 1,
            "status": "NOT_STARTED",
            "total_actual_time": None,
            "total_actual_cost": None,
            "resource_id": None,
            "resource_name": None,
            "active_operator_id": None,
            "group_boundary": None,
        },
    )


def test_completed_operation_preserves_decimal_strings():
    round_trip(
        "ManufacturingOrderOperationRow",
        {
            "id": 1,
            "status": "COMPLETED",
            "total_actual_time": "1.25",
            "total_actual_cost": "3.14",
        },
    )


@pytest.mark.parametrize("amount", [3.14, "3.1400000000"])
def test_shipping_fee_parsers_preserve_create_and_read_wire_types(amount):
    body = {"id": 1, "sales_order_id": 2, "amount": amount}
    fee = round_trip("SalesOrderShippingFee", body)
    assert type(fee.amount) is type(amount)
    endpoint = (
        create_sales_order_shipping_fee
        if isinstance(amount, float)
        else get_sales_order_shipping_fee
    )
    parsed = endpoint._parse_response(
        client=Client(base_url="https://example.test"),
        response=httpx.Response(200, json=body),
    )
    assert isinstance(parsed, models.SalesOrderShippingFee)
    assert parsed.to_dict() == body


def test_sales_order_without_shipping_fee_accepts_empty_object():
    body = {
        "id": 1,
        "customer_id": 2,
        "order_no": "TEST-SO",
        "location_id": 3,
        "status": "NOT_SHIPPED",
        "shipping_fee": {},
    }
    validate("SalesOrder", body)
    order = models.SalesOrder.from_dict(body)
    assert order.shipping_fee is None
    assert models_pydantic.SalesOrder.from_attrs(order).shipping_fee is None
    validator = Draft202012Validator(
        {"$ref": "urn:openapi-spec#/components/schemas/SalesOrder"}, registry=REGISTRY
    )
    assert not validator.is_valid({**body, "shipping_fee": {"amount": "1"}})


def test_stock_adjustment_traceability_preserves_null_axes_and_string_quantity():
    round_trip(
        "StockAdjustmentRow",
        {
            "variant_id": 1,
            "quantity": 5,
            "traceability": [
                {
                    "batch_id": None,
                    "serial_number_id": None,
                    "bin_location_id": None,
                    "quantity": "5.0000000000",
                }
            ],
        },
    )


def test_stock_adjustment_cache_persists_typed_traceability_as_json():
    table = SQLModel.metadata.tables["stock_adjustment_row"]
    allocation = models_pydantic.StockAdjustmentTraceability(
        batch_id=None,
        serial_number_id=None,
        bin_location_id=None,
        quantity="5.0000000000",
    )
    engine = create_engine("sqlite://")
    try:
        table.create(engine)
        with engine.begin() as connection:
            connection.execute(
                table.insert().values(
                    id=1, variant_id=2, quantity=5, traceability=[allocation]
                )
            )
            restored = connection.execute(table.select()).mappings().one()
            assert restored["traceability"] == [allocation.model_dump(mode="json")]
    finally:
        engine.dispose()


@pytest.mark.parametrize("quantity", ["1.2500000000", 1.25])
def test_outsourced_recipe_decimal_response_and_unallocated_batch(quantity):
    round_trip(
        "OutsourcedPurchaseOrderRecipeRow",
        {
            "id": 1,
            "purchase_order_row_id": 1,
            "ingredient_variant_id": 2,
            "planned_quantity_per_unit": quantity,
            "batch_transactions": [{"batch_id": None, "quantity": 1}],
        },
    )


def test_transfer_response_accepts_unallocated_batch():
    round_trip(
        "StockTransferRow",
        {
            "variant_id": 1,
            "quantity": 1,
            "batch_transactions": [{"batch_id": None, "quantity": 1}],
        },
    )


@pytest.mark.parametrize(
    "name,body",
    [
        (
            "UpdateSalesOrderRowRequest",
            {"batch_transactions": [{"batch_id": None, "quantity": 1}]},
        ),
        (
            "CreateOutsourcedPurchaseOrderRecipeRowRequest",
            {
                "purchase_order_row_id": 1,
                "ingredient_variant_id": 2,
                "planned_quantity_per_unit": 1,
                "batch_transactions": [{"batch_id": None, "quantity": 1}],
            },
        ),
    ],
)
def test_response_nullability_does_not_weaken_legacy_allocation_requests(name, body):
    validator = Draft202012Validator(
        {"$ref": f"urn:openapi-spec#/components/schemas/{name}"}, registry=REGISTRY
    )
    assert not validator.is_valid(body)


def test_published_serial_failure_reason_is_supported():
    round_trip(
        "CreateSerialNumbersResponse",
        {
            "successful": [],
            "failed": [{"serial_number": "TEST-SERIAL-1", "reason": "NOT_IN_STOCK"}],
        },
    )


def test_recipe_notes_and_purchase_conversion_can_be_null():
    round_trip("ManufacturingOrderRecipeRow", {"id": 1, "notes": None})
    round_trip(
        "PurchaseOrderRow",
        {"id": 1, "quantity": 1, "variant_id": 2, "purchase_uom_conversion_rate": None},
    )
