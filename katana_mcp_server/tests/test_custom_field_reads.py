"""SO reads preserve values and distinguish omitted, null, and empty maps."""

from unittest.mock import AsyncMock, patch

import pytest
from katana_mcp.tools.custom_field_values import custom_fields_read_kwargs
from katana_mcp.tools.foundation.custom_fields import ListCustomFieldDefinitionsResponse
from katana_mcp.tools.foundation.sales_orders import (
    ListSalesOrdersRequest,
    _list_sales_orders_impl,
)
from katana_mcp.typed_cache import ENTITY_SPECS, merge_filtered_fetch

from katana_public_api_client.models import SalesOrder
from katana_public_api_client.models_pydantic._generated import (
    CachedSalesOrder,
    CachedSalesOrderRow,
)

FIELD_ID = "00000000-0000-0000-0000-000000000001"


def order_data(payload):
    return {
        "id": 1,
        "order_no": "SO-CF",
        "customer_id": 1,
        "location_id": 1,
        "status": "PENDING",
        "sales_order_rows": [
            {"id": 2, "sales_order_id": 1, "variant_id": 3, "quantity": 1, **payload}
        ],
        **payload,
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"custom_fields": None},
        {"custom_fields": {}},
        {"custom_fields": {FIELD_ID: False}},
    ],
)
async def test_cache_parent_and_nested_row_preserve_wire_presence(
    typed_cache_engine, payload
):
    order = SalesOrder.from_dict(order_data(payload))
    await merge_filtered_fetch(
        cache=typed_cache_engine, spec=ENTITY_SPECS["sales_order"], attrs_objs=[order]
    )
    async with typed_cache_engine.session() as session:
        cached = await session.get(CachedSalesOrder, 1)
        row = await session.get(CachedSalesOrderRow, 2)
        assert cached is not None and row is not None
        assert cached.custom_fields_present == ("custom_fields" in payload)
        assert row.custom_fields_present == ("custom_fields" in payload)
        assert custom_fields_read_kwargs(record=cached) == payload
        assert custom_fields_read_kwargs(record=row) == payload


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"custom_fields": None},
        {"custom_fields": {}},
        {"custom_fields": {FIELD_ID: "text"}},
    ],
)
async def test_list_and_detail_surface_custom_fields_with_presence(
    context_with_typed_cache, payload
):
    context, _lifespan, cache = context_with_typed_cache
    order = SalesOrder.from_dict(order_data(payload))
    await merge_filtered_fetch(
        cache=cache, spec=ENTITY_SPECS["sales_order"], attrs_objs=[order]
    )
    with (
        patch("katana_mcp.typed_cache.ensure_sales_orders_synced", AsyncMock()),
        patch(
            "katana_mcp.tools.custom_field_values._list_custom_field_definitions_impl",
            AsyncMock(
                return_value=ListCustomFieldDefinitionsResponse(
                    definitions=[], total_count=0
                )
            ),
        ),
    ):
        listed = await _list_sales_orders_impl(
            request=ListSalesOrdersRequest(include_rows=True), context=context
        )
    encoded = listed.model_dump(mode="json")
    for record in (encoded["orders"][0], encoded["orders"][0]["rows"][0]):
        assert ("custom_fields" in record) == ("custom_fields" in payload)
        if payload:
            assert record["custom_fields"] == payload["custom_fields"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"custom_fields": None},
        {"custom_fields": {}},
        {"custom_fields": {FIELD_ID: "text"}},
    ],
)
async def test_live_detail_preserves_header_and_row_values(
    context_with_typed_cache, payload
):
    from unittest.mock import MagicMock

    from katana_mcp.tools.foundation.sales_orders import (
        GetSalesOrderRequest,
        _get_sales_order_impl,
    )

    context, _lifespan, _cache = context_with_typed_cache
    order = SalesOrder.from_dict(order_data(payload))
    with (
        patch(
            "katana_public_api_client.api.sales_order.get_sales_order.asyncio_detailed",
            AsyncMock(return_value=MagicMock(status_code=200, parsed=order)),
        ),
        patch(
            "katana_mcp.tools.foundation.sales_orders._fetch_sales_order_addresses",
            AsyncMock(return_value=[]),
        ),
        patch(
            "katana_mcp.tools.custom_field_values._list_custom_field_definitions_impl",
            AsyncMock(
                return_value=ListCustomFieldDefinitionsResponse(
                    definitions=[], total_count=0
                )
            ),
        ),
    ):
        result = await _get_sales_order_impl(
            request=GetSalesOrderRequest(order_id=1), context=context
        )
    encoded = result.model_dump(mode="json")
    for record in (encoded, encoded["rows"][0]):
        assert ("custom_fields" in record) == ("custom_fields" in payload)
        if payload:
            assert record["custom_fields"] == payload["custom_fields"]
