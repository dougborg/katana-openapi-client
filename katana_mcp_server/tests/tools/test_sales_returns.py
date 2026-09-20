"""Focused behavior tests for the sales-return MCP tools."""

import json
from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from katana_mcp.tools.foundation.sales_returns import (
    DeleteSalesReturnRequest,
    GetSalesReturnRequest,
    ListSalesReturnsRequest,
    _delete_sales_return_impl,
    _get_sales_return_impl,
    _list_sales_returns_impl,
)
from katana_mcp.tools.prefab_ui import build_sales_return_delete_ui
from katana_mcp_server.tests.conftest import create_mock_context

from katana_public_api_client import KatanaClient
from katana_public_api_client.client_types import Response
from katana_public_api_client.models import (
    SalesReturn,
    SalesReturnRow,
    SalesReturnStatus,
)


def _sales_return(*, id: int, sales_order_id: int | None = 11) -> SalesReturn:
    return SalesReturn(
        id=id,
        customer_id=7,
        sales_order_id=sales_order_id,
        order_no=f"RO-{id}",
        return_location_id=3,
        status=SalesReturnStatus.NOT_RETURNED,
    )


def test_delete_card_exposes_imported_return_error():
    app = build_sales_return_delete_ui(
        {
            "entity_id": 42,
            "is_preview": False,
            "actions": [
                {
                    "operation": "delete",
                    "error": "Return orders not created in Katana cannot be updated in Katana.",
                }
            ],
            "prior_state": {"order_no": "RO-42", "sales_return_rows": []},
            "message": "Deletion failed",
        },
        confirm_request=DeleteSalesReturnRequest(id=42),
        confirm_tool="delete_sales_return",
    )

    rendered = str(app.to_json())
    assert "Delete Sales Return" in rendered
    assert "Return orders not created in Katana" in rendered
    state = app.to_json()["state"]["sales_return"]
    assert state["entity_id"] == 42
    assert state["actions"][0]["error"].startswith("Return orders not created")
    assert state["prior_state"]["order_no"] == "RO-42"


@pytest.mark.asyncio
async def test_list_filters_sales_order_locally_after_complete_fetch():
    context, _ = create_mock_context()
    seen_requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen_requests.append(request)
        page = request.url.params["page"]
        payloads = {
            "1": [_sales_return(id=1, sales_order_id=99).to_dict()],
            "2": [
                _sales_return(id=2, sales_order_id=11).to_dict(),
                _sales_return(id=3, sales_order_id=11).to_dict(),
            ],
        }
        return httpx.Response(
            status_code=200,
            json={"data": payloads[page]},
            headers={
                "X-Pagination": json.dumps(
                    {
                        "page": int(page),
                        "total_pages": 2,
                        "last_page": page == "2",
                    }
                )
            },
        )

    client = KatanaClient(
        api_key="test-key",
        base_url="https://katana.test/v1",
        transport=httpx.MockTransport(handler),
        requests_per_minute=None,
    )
    context.request_context.lifespan_context.client = client
    try:
        response = await _list_sales_returns_impl(
            request=ListSalesReturnsRequest(
                sales_order_id=11,
                order_no="RO-1",
                return_location_id=3,
                status="NOT_RETURNED",
                limit=1,
            ),
            context=context,
        )
    finally:
        await client.get_async_httpx_client().aclose()

    assert response.total_count == 2
    assert [item.id for item in response.sales_returns] == [2]
    assert [request.url.params["page"] for request in seen_requests] == ["1", "2"]
    first_params = seen_requests[0].url.params
    assert first_params["limit"] == "250"
    assert first_params["order_no"] == "RO-1"
    assert first_params["return_location_id"] == "3"
    assert first_params["status"] == "NOT_RETURNED"
    assert "sales_order_id" not in first_params


@pytest.mark.asyncio
async def test_get_includes_sales_return_rows():
    context, _ = create_mock_context()
    sales_return = _sales_return(id=42)
    sales_return.sales_return_rows = [
        SalesReturnRow(
            id=51,
            sales_return_id=42,
            variant_id=71,
            quantity="2.5",
            sales_order_row_id=81,
            reason_id=91,
        )
    ]
    api_response = Response(
        status_code=HTTPStatus.OK,
        content=b"{}",
        headers={},
        parsed=sales_return,
    )

    with patch(
        "katana_mcp.tools.foundation.sales_returns.api_get_sales_return.asyncio_detailed",
        new_callable=AsyncMock,
        return_value=api_response,
    ):
        response = await _get_sales_return_impl(GetSalesReturnRequest(id=42), context)

    assert response.id == 42
    assert response.row_count == 1
    assert response.rows[0].id == 51
    assert response.rows[0].sales_order_row_id == 81
    assert response.rows[0].reason_id == 91


@pytest.mark.asyncio
async def test_delete_preview_captures_prior_state():
    context, _ = create_mock_context()
    with patch(
        "katana_mcp.tools.foundation.sales_returns._fetch_sales_return_attrs",
        new_callable=AsyncMock,
        return_value=_sales_return(id=42),
    ):
        response = await _delete_sales_return_impl(
            DeleteSalesReturnRequest(id=42, preview=True), context
        )

    assert response.is_preview is True
    assert response.actions[0].operation == "delete"
    assert response.prior_state == _sales_return(id=42).to_dict()


@pytest.mark.asyncio
async def test_delete_preserves_imported_return_error_text():
    context, _ = create_mock_context()
    api_response = MagicMock()
    api_response.status_code = HTTPStatus.UNPROCESSABLE_ENTITY
    api_response.parsed = None
    api_response.content = (
        b'{"name":"UnprocessableEntityError",'
        b'"message":"Return orders not created in Katana cannot be updated in Katana."}'
    )
    with (
        patch(
            "katana_mcp.tools.foundation.sales_returns._fetch_sales_return_attrs",
            new_callable=AsyncMock,
            return_value=_sales_return(id=42),
        ),
        patch(
            "katana_mcp.tools.foundation.sales_returns.api_delete_sales_return.asyncio_detailed",
            new_callable=AsyncMock,
            return_value=api_response,
        ),
    ):
        response = await _delete_sales_return_impl(
            DeleteSalesReturnRequest(id=42, preview=False), context
        )

    assert response.actions[0].succeeded is False
    assert "Return orders not created in Katana" in (response.actions[0].error or "")
