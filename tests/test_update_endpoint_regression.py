"""Regression tests for #527 — empty 200 schemas on the two PATCH update endpoints caused ``unwrap_as`` to raise on success."""

from collections.abc import Callable

import httpx
import pytest

from katana_public_api_client import KatanaClient
from katana_public_api_client.api.customer_address import update_customer_address
from katana_public_api_client.api.sales_order import update_sales_order
from katana_public_api_client.models.customer_address import CustomerAddress
from katana_public_api_client.models.sales_order import SalesOrder
from katana_public_api_client.models.update_customer_address_request import (
    UpdateCustomerAddressRequest,
)
from katana_public_api_client.models.update_sales_order_request import (
    UpdateSalesOrderRequest,
)
from katana_public_api_client.utils import unwrap_as


def _client_with_mock_transport(
    handler: Callable[[httpx.Request], httpx.Response],
) -> KatanaClient:
    """Build a KatanaClient backed by an ``httpx.MockTransport``; caller must use ``async with`` to close it."""
    return KatanaClient(
        api_key="test-api-key",
        base_url="https://api.katana.test",
        transport=httpx.MockTransport(handler),
    )


@pytest.mark.asyncio
async def test_update_sales_order_parses_200_body() -> None:
    """Successful PATCH /sales_orders/{id} returns a parsed SalesOrder (regression for #527)."""
    sales_order_payload = {
        "id": 42,
        "customer_id": 7,
        "order_no": "SO-000042",
        "location_id": 1,
        "status": "NOT_SHIPPED",
        "order_created_date": "2026-05-06T10:00:00Z",
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "PATCH"
        assert request.url.path == "/sales_orders/42"
        return httpx.Response(200, json=sales_order_payload)

    async with _client_with_mock_transport(handler) as client:
        response = await update_sales_order.asyncio_detailed(
            id=42,
            client=client,
            body=UpdateSalesOrderRequest(),
        )

    order = unwrap_as(response, SalesOrder)
    assert isinstance(order, SalesOrder)
    assert order.id == 42
    assert order.order_no == "SO-000042"


@pytest.mark.asyncio
async def test_update_customer_address_parses_200_body() -> None:
    """Successful PATCH /customer_addresses/{id} returns a parsed CustomerAddress (regression for #527)."""
    customer_address_payload = {
        "id": 99,
        "customer_id": 7,
        "entity_type": "shipping",
        "city": "Springfield",
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "PATCH"
        assert request.url.path == "/customer_addresses/99"
        return httpx.Response(200, json=customer_address_payload)

    async with _client_with_mock_transport(handler) as client:
        response = await update_customer_address.asyncio_detailed(
            id=99,
            client=client,
            body=UpdateCustomerAddressRequest(),
        )

    address = unwrap_as(response, CustomerAddress)
    assert isinstance(address, CustomerAddress)
    assert address.id == 99
    assert address.city == "Springfield"
