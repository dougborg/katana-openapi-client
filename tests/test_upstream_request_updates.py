"""Validate bulk reranking and receipt allocations against the shared spec."""

from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator
from referencing import Registry
from referencing.jsonschema import DRAFT202012

from katana_public_api_client import models

SPEC = yaml.safe_load(
    (Path(__file__).parents[1] / "docs/katana-openapi.yaml").read_text()
)
REGISTRY = Registry().with_resource("urn:katana", DRAFT202012.create_resource(SPEC))


def validator(name):
    return Draft202012Validator(
        {"$ref": f"urn:katana#/components/schemas/{name}"}, registry=REGISTRY
    )


@pytest.mark.parametrize(
    "name", ["RerankSalesOrderRequest", "RerankManufacturingOrderRequest"]
)
@pytest.mark.parametrize(
    "place",
    [{"before_id": 4}, {"after_id": 4}, {"position": "top"}, {"position": "bottom"}],
)
def test_bulk_rerank_serializes_each_placement(name, place):
    body = {"order_ids": list(range(1, 251)), "place": place}
    validator(name).validate(body)
    assert getattr(models, name).from_dict(body).to_dict() == body


@pytest.mark.parametrize(
    "body",
    [
        {"order_ids": [1, 1], "place": {"before_id": 4}},
        {"order_ids": list(range(1, 252)), "place": {"before_id": 4}},
        {"order_ids": [1], "place": {}},
        {"order_ids": [1], "place": {"before_id": 4, "after_id": 5}},
    ],
)
def test_bulk_rerank_rejects_invalid_ids_and_placement(body):
    assert not validator("RerankSalesOrderRequest").is_valid(body)


@pytest.mark.parametrize("quantity", [2, "2.5"])
def test_receive_traceability_round_trip(quantity):
    body = {
        "purchase_order_row_id": 1,
        "quantity": 3,
        "traceability": [
            {"batch_id": 2, "bin_location_id": None, "quantity": quantity}
        ],
    }
    validator("PurchaseOrderReceiveRow").validate(body)
    assert models.PurchaseOrderReceiveRow.from_dict(body).to_dict() == body


@pytest.mark.parametrize("quantity", [0, "0.00", -1, "-1"])
def test_receive_traceability_rejects_nonpositive_quantities(quantity):
    assert not validator("PurchaseOrderReceiveTraceability").is_valid(
        {"quantity": quantity}
    )


@pytest.mark.parametrize(
    "module",
    [
        "sales_order.rerank_sales_order",
        "manufacturing_order.rerank_manufacturing_order",
    ],
)
def test_rerank_parses_updated_success_response(module):
    import importlib

    import httpx

    from katana_public_api_client import Client

    endpoint = importlib.import_module(f"katana_public_api_client.api.{module}")
    response = httpx.Response(200, json={"order_ids": [101, 102]})
    parsed = endpoint._parse_response(
        client=Client(base_url="https://example.com"), response=response
    )
    assert parsed is not None
    assert parsed.to_dict() == {"order_ids": [101, 102]}


def test_inventory_signal_parses_selected_window_and_average():
    body = {
        "variant_id": 1,
        "demand_window": 7,
        "avg_daily_demand": "2.5000000000",
        "committed": "1.0000000000",
    }
    parsed = models.InventorySignal.from_dict(body)
    assert parsed.to_dict() == body
