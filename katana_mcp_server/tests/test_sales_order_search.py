"""Live search passes filters intact and enriches without caching result sets."""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from katana_mcp.tools.foundation.custom_fields import ListCustomFieldDefinitionsResponse
from katana_mcp.tools.foundation.sales_order_search import (
    SearchSalesOrdersRequest,
    _search_sales_order_rows_impl,
    _search_sales_orders_impl,
)
from katana_mcp_server.tests.conftest import create_mock_context

from katana_public_api_client.models import SalesOrder, SalesOrderRow
from katana_public_api_client.models_pydantic._generated import CustomFieldDefinition

FIELD_ID = "00000000-0000-0000-0000-000000000001"


def definitions():
    return ListCustomFieldDefinitionsResponse(
        definitions=[
            CustomFieldDefinition.model_validate(
                {
                    "id": FIELD_ID,
                    "label": "Sales Rep",
                    "field_type": "singleSelect",
                    "entity_type": "SalesOrder",
                    "source": "test",
                    "options": {
                        "choices": [{"id": 2, "label": "Morgan", "deleted": True}]
                    },
                }
            )
        ],
        total_count=1,
    )


def search_response(*, data):
    return MagicMock(
        status_code=200,
        parsed=SimpleNamespace(data=data),
        headers={
            "x-pagination": json.dumps(
                {
                    "total_records": 4,
                    "total_pages": 4,
                    "page": 1,
                    "first_page": True,
                    "last_page": False,
                }
            )
        },
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "filter",
    [
        {f"custom_fields.{FIELD_ID}": None},
        {
            "and": [
                {"status": "DELIVERED"},
                {f"custom_fields.{FIELD_ID}": {"inq": [2, 3]}},
            ]
        },
    ],
)
async def test_search_orders_passes_filter_and_resolves_historical_labels(filter):
    context, lifespan = create_mock_context()
    lifespan.typed_cache.catalog.get_many_by_ids.return_value = {
        3: SimpleNamespace(sku="WIDGET", display_name="Widget")
    }
    row = {
        "id": 2,
        "sales_order_id": 1,
        "variant_id": 3,
        "quantity": 1,
        "custom_fields": {"unknown": "retained"},
    }
    order = SalesOrder.from_dict(
        {
            "id": 1,
            "customer_id": 1,
            "order_no": "SO-CF",
            "location_id": 1,
            "status": "DELIVERED",
            "sales_order_rows": [row],
            "custom_fields": {FIELD_ID: 2},
        }
    )
    with (
        patch(
            "katana_mcp.tools.foundation.sales_order_search.api_orders.asyncio_detailed",
            AsyncMock(return_value=search_response(data=[order])),
        ) as endpoint,
        patch(
            "katana_mcp.tools.custom_field_values._list_custom_field_definitions_impl",
            AsyncMock(return_value=definitions()),
        ) as definition_lookup,
    ):
        result = await _search_sales_orders_impl(
            request=SearchSalesOrdersRequest(
                filter=filter, order=["created_at DESC", "id DESC"], limit=1
            ),
            context=context,
        )
        body = endpoint.call_args.kwargs["body"].to_dict()
        assert body == {
            "filter": filter,
            "order": ["created_at DESC", "id DESC"],
            "limit": 1,
            "page": 1,
        }
        definition_lookup.assert_awaited_once()
    assert result.orders[0].custom_fields == {FIELD_ID: 2}
    assert result.orders[0].custom_fields_resolved[0].value_label == "Morgan"
    assert result.orders[0].rows is not None
    assert result.orders[0].rows[0].sku == "WIDGET"
    assert result.orders[0].rows[0].custom_fields_resolved[0].value == "retained"
    assert result.pagination is not None
    assert result.pagination.total_records == 4


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload", [{}, {"custom_fields": None}, {"custom_fields": {}}]
)
async def test_search_rows_preserves_custom_field_presence_and_bypasses_definition_lookup(
    payload,
):
    context, _lifespan = create_mock_context()
    row = SalesOrderRow.from_dict({"id": 1, "quantity": 1, "variant_id": 2, **payload})
    with (
        patch(
            "katana_mcp.tools.foundation.sales_order_search.api_rows.asyncio_detailed",
            AsyncMock(return_value=search_response(data=[row])),
        ) as endpoint,
        patch(
            "katana_mcp.tools.custom_field_values._list_custom_field_definitions_impl",
            AsyncMock(),
        ) as definition_lookup,
    ):
        result = None
        for _ in range(2):
            result = await _search_sales_order_rows_impl(
                request=SearchSalesOrdersRequest(
                    filter={f"custom_fields.{FIELD_ID}": None}
                ),
                context=context,
            )
        assert endpoint.await_count == 2
        definition_lookup.assert_not_awaited()
    assert result is not None
    encoded = result.model_dump(mode="json")["rows"][0]
    assert ("custom_fields" in encoded) == ("custom_fields" in payload)
    if payload:
        assert encoded["custom_fields"] == payload["custom_fields"]
