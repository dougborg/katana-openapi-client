"""Status filter enums serialize to the gateway's query values (#938)."""

from collections.abc import Awaitable, Callable
from enum import Enum
from typing import Any

import httpx
import pytest

from katana_public_api_client import KatanaClient
from katana_public_api_client.api.sales_order import get_all_sales_orders
from katana_public_api_client.api.sales_order_fulfillment import (
    get_all_sales_order_fulfillments,
)
from katana_public_api_client.api.sales_return import get_all_sales_returns
from katana_public_api_client.api.stocktake import get_all_stocktakes
from katana_public_api_client.client_types import UNSET, Unset
from katana_public_api_client.models import (
    SalesOrderFulfillmentStatus,
    SalesOrderProductionStatus,
    SalesReturnStatus,
    StocktakeStatus,
)

_FILTERS = [
    (
        get_all_sales_order_fulfillments,
        "/sales_order_fulfillments",
        "status",
        SalesOrderFulfillmentStatus,
    ),
    (
        get_all_sales_orders,
        "/sales_orders",
        "production_status",
        SalesOrderProductionStatus,
    ),
    (get_all_sales_returns, "/sales_returns", "status", SalesReturnStatus),
    (get_all_stocktakes, "/stocktakes", "status", StocktakeStatus),
]
_CASES = [
    pytest.param(
        endpoint.asyncio_detailed,
        endpoint.sync_detailed,
        path,
        field,
        value,
        id=f"{path[1:]}-{value.value if isinstance(value, Enum) else 'omitted'}",
    )
    for endpoint, path, field, enum in _FILTERS
    for value in [*enum, UNSET]
]


@pytest.mark.asyncio
@pytest.mark.parametrize("async_endpoint,sync_endpoint,path,field,value", _CASES)
async def test_status_filter_wire_values(
    async_endpoint: Callable[..., Awaitable[Any]],
    sync_endpoint: Callable[..., Any],
    path: str,
    field: str,
    value: Enum | Unset,
) -> None:
    """Both public transports send each accepted value and omit an unset filter."""
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"data": []})

    with KatanaClient(
        api_key="test-api-key",
        base_url="https://api.katana.test",
        transport=httpx.MockTransport(handler),
        requests_per_minute=None,
    ) as client:
        async with client:
            await async_endpoint(client=client, page=1, **{field: value})
            sync_endpoint(client=client, page=1, **{field: value})

    assert len(requests) == 2
    for request in requests:
        assert request.method == "GET"
        assert request.url.path == path
        if isinstance(value, Enum):
            assert request.url.params[field] == value.value
        else:
            assert field not in request.url.params


@pytest.mark.parametrize("enum", [item[3] for item in _FILTERS])
def test_status_filter_rejects_unknown_value(enum: type[Enum]) -> None:
    with pytest.raises(ValueError):
        enum("UNKNOWN_STATUS")
