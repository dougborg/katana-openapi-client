"""Tests for stock transfer MCP tools (issue #338).

Covers the full five-tool surface:
- create_stock_transfer (preview + confirm)
- list_stock_transfers (list-tool pattern v2 — limit, page, dates, filters)
- update_stock_transfer (preview + confirm)
- update_stock_transfer_status (preview + confirm + invalid-transition error)
- delete_stock_transfer (preview + confirm)
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from katana_mcp.tools.foundation.stock_transfers import (
    CreateStockTransferRequest,
    DeleteStockTransferRequest,
    ListStockTransfersRequest,
    StockTransferBatchTransactionInput,
    StockTransferRowInput,
    UpdateStockTransferRequest,
    UpdateStockTransferStatusRequest,
    _create_stock_transfer_impl,
    _delete_stock_transfer_impl,
    _list_stock_transfers_impl,
    _update_stock_transfer_impl,
    _update_stock_transfer_status_impl,
    list_stock_transfers,
)

from katana_public_api_client.client_types import UNSET
from katana_public_api_client.utils import APIError
from tests.conftest import create_mock_context

_ST_CREATE = "katana_public_api_client.api.stock_transfer.create_stock_transfer"
_ST_LIST = "katana_public_api_client.api.stock_transfer.get_all_stock_transfers"
_ST_UPDATE = "katana_public_api_client.api.stock_transfer.update_stock_transfer"
_ST_UPDATE_STATUS = (
    "katana_public_api_client.api.stock_transfer.update_stock_transfer_status"
)
_ST_DELETE = "katana_public_api_client.api.stock_transfer.delete_stock_transfer"

_ST_UNWRAP_AS = "katana_mcp.tools.foundation.stock_transfers.unwrap_as"
_ST_UNWRAP_DATA = "katana_public_api_client.utils.unwrap_data"
_ST_IS_SUCCESS = "katana_mcp.tools.foundation.stock_transfers.is_success"


# ============================================================================
# Test helpers
# ============================================================================


def _make_mock_transfer(
    *,
    id: int = 1,
    stock_transfer_number: str | None = "ST-1",
    source_location_id: int = 1,
    target_location_id: int = 2,
    status: str = "pending",
    transfer_date: datetime | None = None,
    expected_arrival_date: datetime | None = None,
    created_at: datetime | None = None,
    rows: list | None = None,
) -> MagicMock:
    """Build a mock StockTransfer attrs object for tests."""
    t = MagicMock()
    t.id = id
    t.stock_transfer_number = stock_transfer_number if stock_transfer_number else UNSET
    t.source_location_id = source_location_id
    t.target_location_id = target_location_id
    t.status = status
    t.transfer_date = transfer_date if transfer_date is not None else UNSET
    t.expected_arrival_date = (
        expected_arrival_date if expected_arrival_date is not None else UNSET
    )
    t.created_at = created_at if created_at is not None else UNSET
    t.stock_transfer_rows = rows if rows is not None else UNSET
    t.additional_info = UNSET
    return t


def _make_mock_row(
    *,
    id: int = 1,
    variant_id: int = 100,
    quantity: float = 5,
    cost_per_unit: float | None = None,
    batch_transactions: list | None = None,
) -> MagicMock:
    r = MagicMock()
    r.id = id
    r.variant_id = variant_id
    r.quantity = quantity
    r.cost_per_unit = cost_per_unit if cost_per_unit is not None else UNSET
    r.batch_transactions = (
        batch_transactions if batch_transactions is not None else UNSET
    )
    return r


# ============================================================================
# create_stock_transfer
# ============================================================================


@pytest.mark.asyncio
async def test_create_stock_transfer_preview():
    """Preview returns is_preview=True and does not call API."""
    context, _ = create_mock_context()

    request = CreateStockTransferRequest(
        source_location_id=1,
        destination_location_id=2,
        expected_arrival_date=datetime(2026, 5, 1, 12, 0, tzinfo=UTC),
        rows=[StockTransferRowInput(variant_id=100, quantity=5)],
        order_no="ST-PREVIEW-1",
        confirm=False,
    )
    result = await _create_stock_transfer_impl(request, context)

    assert result.is_preview is True
    assert result.source_location_id == 1
    assert result.target_location_id == 2
    assert result.stock_transfer_number == "ST-PREVIEW-1"
    assert result.id is None
    assert "Preview" in result.message
    assert len(result.next_actions) > 0


@pytest.mark.asyncio
async def test_create_stock_transfer_confirm_success():
    """confirm=True builds the request and returns the created transfer."""
    context, _ = create_mock_context()

    mock_transfer = _make_mock_transfer(
        id=42,
        stock_transfer_number="ST-42",
        source_location_id=1,
        target_location_id=2,
        status="pending",
        expected_arrival_date=datetime(2026, 5, 1, 12, 0, tzinfo=UTC),
    )

    with (
        patch(f"{_ST_CREATE}.asyncio_detailed", new_callable=AsyncMock) as mock_api,
        patch(_ST_UNWRAP_AS, return_value=mock_transfer),
    ):
        request = CreateStockTransferRequest(
            source_location_id=1,
            destination_location_id=2,
            expected_arrival_date=datetime(2026, 5, 1, 12, 0, tzinfo=UTC),
            rows=[
                StockTransferRowInput(
                    variant_id=100,
                    quantity=5,
                    batch_transactions=[
                        StockTransferBatchTransactionInput(batch_id=77, quantity=5)
                    ],
                )
            ],
            confirm=True,
        )
        result = await _create_stock_transfer_impl(request, context)

    assert result.is_preview is False
    assert result.id == 42
    assert result.stock_transfer_number == "ST-42"
    assert result.status == "pending"

    # Verify API was called
    mock_api.assert_awaited_once()
    call_body = mock_api.await_args.kwargs["body"]
    assert call_body.source_location_id == 1
    assert call_body.target_location_id == 2
    # Batch transactions should serialize into the row body
    row_dict = call_body.stock_transfer_rows[0].to_dict()
    assert "batch_transactions" in row_dict
    assert row_dict["batch_transactions"] == [{"batch_id": 77, "quantity": 5}]


@pytest.mark.asyncio
async def test_create_stock_transfer_user_declines():
    """When user declines elicitation, no API call happens; preview returned."""
    context, _ = create_mock_context(elicit_confirm=False)

    request = CreateStockTransferRequest(
        source_location_id=1,
        destination_location_id=2,
        expected_arrival_date=datetime(2026, 5, 1, 12, 0, tzinfo=UTC),
        rows=[StockTransferRowInput(variant_id=100, quantity=5)],
        confirm=True,
    )

    with patch(f"{_ST_CREATE}.asyncio_detailed", new_callable=AsyncMock) as mock_api:
        result = await _create_stock_transfer_impl(request, context)

    assert result.is_preview is True
    assert result.id is None
    assert "cancelled" in result.message.lower()
    mock_api.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_stock_transfer_rejects_empty_rows():
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        CreateStockTransferRequest(
            source_location_id=1,
            destination_location_id=2,
            expected_arrival_date=datetime(2026, 5, 1, tzinfo=UTC),
            rows=[],
            confirm=False,
        )


# ============================================================================
# list_stock_transfers — pattern v2
# ============================================================================


@pytest.mark.asyncio
async def test_list_stock_transfers_page_short_circuit_single_page():
    """limit <= 250 (and no explicit page) adds page=1 to disable auto-pagination."""
    context, _ = create_mock_context()
    captured: dict = {}

    async def fake(**kwargs):
        captured.update(kwargs)
        return MagicMock()

    with (
        patch(f"{_ST_LIST}.asyncio_detailed", side_effect=fake),
        patch(_ST_UNWRAP_DATA, return_value=[]),
    ):
        await _list_stock_transfers_impl(ListStockTransfersRequest(limit=10), context)

    assert captured["page"] == 1
    assert captured["limit"] == 10


@pytest.mark.asyncio
async def test_list_stock_transfers_caller_page_preserved():
    """An explicit page overrides the short-circuit."""
    context, _ = create_mock_context()
    captured: dict = {}

    async def fake(**kwargs):
        captured.update(kwargs)
        return MagicMock()

    with (
        patch(f"{_ST_LIST}.asyncio_detailed", side_effect=fake),
        patch(_ST_UNWRAP_DATA, return_value=[]),
    ):
        await _list_stock_transfers_impl(
            ListStockTransfersRequest(limit=50, page=3), context
        )

    assert captured["page"] == 3
    assert captured["limit"] == 50


@pytest.mark.asyncio
async def test_list_stock_transfers_large_limit_omits_page():
    """limit > 250 lets auto-pagination drive."""
    context, _ = create_mock_context()
    captured: dict = {}

    async def fake(**kwargs):
        captured.update(kwargs)
        return MagicMock()

    with (
        patch(f"{_ST_LIST}.asyncio_detailed", side_effect=fake),
        patch(_ST_UNWRAP_DATA, return_value=[]),
    ):
        await _list_stock_transfers_impl(ListStockTransfersRequest(limit=500), context)

    assert "page" not in captured
    assert captured["limit"] == 500


@pytest.mark.asyncio
async def test_list_stock_transfers_caps_results_to_request_limit():
    """Safety net: even if transport returns more rows than limit, slice them."""
    context, _ = create_mock_context()

    over_fetched = [
        _make_mock_transfer(id=i, stock_transfer_number=f"ST-{i}") for i in range(100)
    ]

    with (
        patch(f"{_ST_LIST}.asyncio_detailed", new_callable=AsyncMock),
        patch(_ST_UNWRAP_DATA, return_value=over_fetched),
    ):
        result = await _list_stock_transfers_impl(
            ListStockTransfersRequest(limit=25), context
        )

    assert len(result.transfers) == 25
    assert result.total_count == 25


@pytest.mark.asyncio
async def test_list_stock_transfers_date_filters_passed_through():
    """created_after / created_before forward as created_at_min / created_at_max datetimes."""
    context, _ = create_mock_context()
    captured: dict = {}

    async def fake(**kwargs):
        captured.update(kwargs)
        return MagicMock()

    with (
        patch(f"{_ST_LIST}.asyncio_detailed", side_effect=fake),
        patch(_ST_UNWRAP_DATA, return_value=[]),
    ):
        await _list_stock_transfers_impl(
            ListStockTransfersRequest(
                created_after="2026-01-01T00:00:00+00:00",
                created_before="2026-04-01T00:00:00+00:00",
            ),
            context,
        )

    assert isinstance(captured["created_at_min"], datetime)
    assert isinstance(captured["created_at_max"], datetime)
    assert captured["created_at_min"].year == 2026
    assert captured["created_at_max"].month == 4


@pytest.mark.asyncio
async def test_list_stock_transfers_invalid_date_raises():
    """Malformed ISO-8601 date is surfaced as ValueError."""
    context, _ = create_mock_context()

    with (
        patch(f"{_ST_LIST}.asyncio_detailed", new_callable=AsyncMock),
        patch(_ST_UNWRAP_DATA, return_value=[]),
        pytest.raises(ValueError, match="Invalid ISO-8601"),
    ):
        await _list_stock_transfers_impl(
            ListStockTransfersRequest(created_after="not-a-date"), context
        )


@pytest.mark.asyncio
async def test_list_stock_transfers_status_filter_client_side():
    """status filter is applied client-side (Katana endpoint has no server filter)."""
    context, _ = create_mock_context()

    transfers = [
        _make_mock_transfer(id=1, status="pending"),
        _make_mock_transfer(id=2, status="in_transit"),
        _make_mock_transfer(id=3, status="completed"),
    ]

    with (
        patch(f"{_ST_LIST}.asyncio_detailed", new_callable=AsyncMock),
        patch(_ST_UNWRAP_DATA, return_value=transfers),
    ):
        result = await _list_stock_transfers_impl(
            ListStockTransfersRequest(status="IN_TRANSIT"), context
        )

    assert result.total_count == 1
    assert result.transfers[0].id == 2


@pytest.mark.asyncio
async def test_list_stock_transfers_location_filters_passed_through():
    """source/destination filters forward to API kwargs."""
    context, _ = create_mock_context()
    captured: dict = {}

    async def fake(**kwargs):
        captured.update(kwargs)
        return MagicMock()

    with (
        patch(f"{_ST_LIST}.asyncio_detailed", side_effect=fake),
        patch(_ST_UNWRAP_DATA, return_value=[]),
    ):
        await _list_stock_transfers_impl(
            ListStockTransfersRequest(source_location_id=5, destination_location_id=9),
            context,
        )

    assert captured["source_location_id"] == 5
    assert captured["target_location_id"] == 9


@pytest.mark.asyncio
async def test_list_stock_transfers_include_rows_populates_details():
    """include_rows=True exposes per-transfer row details."""
    context, _ = create_mock_context()

    mock_transfer = _make_mock_transfer(
        id=7,
        rows=[
            _make_mock_row(id=1, variant_id=100, quantity=5),
            _make_mock_row(id=2, variant_id=200, quantity=2),
        ],
    )

    with (
        patch(f"{_ST_LIST}.asyncio_detailed", new_callable=AsyncMock),
        patch(_ST_UNWRAP_DATA, return_value=[mock_transfer]),
    ):
        result_with = await _list_stock_transfers_impl(
            ListStockTransfersRequest(include_rows=True), context
        )
        result_without = await _list_stock_transfers_impl(
            ListStockTransfersRequest(include_rows=False), context
        )

    assert result_with.transfers[0].rows is not None
    assert len(result_with.transfers[0].rows) == 2
    assert result_with.transfers[0].row_count == 2
    assert result_without.transfers[0].rows is None
    assert result_without.transfers[0].row_count == 2


@pytest.mark.asyncio
async def test_list_stock_transfers_pagination_meta_when_page_set():
    """When page is set, parse x-pagination into PaginationMeta on response."""
    context, _ = create_mock_context()

    mock_response = MagicMock()
    mock_response.headers = {
        "x-pagination": json.dumps(
            {
                "page": 2,
                "total_pages": 5,
                "total_records": 120,
                "first_page": False,
                "last_page": False,
            }
        )
    }

    async def fake(**kwargs):
        return mock_response

    with (
        patch(f"{_ST_LIST}.asyncio_detailed", side_effect=fake),
        patch(_ST_UNWRAP_DATA, return_value=[]),
    ):
        result = await _list_stock_transfers_impl(
            ListStockTransfersRequest(page=2, limit=50), context
        )

    assert result.pagination is not None
    assert result.pagination.page == 2
    assert result.pagination.total_pages == 5
    assert result.pagination.total_records == 120
    assert result.pagination.first_page is False
    assert result.pagination.last_page is False


@pytest.mark.asyncio
async def test_list_stock_transfers_no_pagination_when_page_not_set():
    """When page is not set, pagination meta stays None."""
    context, _ = create_mock_context()

    mock_response = MagicMock()
    mock_response.headers = {"x-pagination": json.dumps({"page": 1, "total_pages": 1})}

    async def fake(**kwargs):
        return mock_response

    with (
        patch(f"{_ST_LIST}.asyncio_detailed", side_effect=fake),
        patch(_ST_UNWRAP_DATA, return_value=[]),
    ):
        result = await _list_stock_transfers_impl(
            ListStockTransfersRequest(limit=10), context
        )

    assert result.pagination is None


# ============================================================================
# update_stock_transfer
# ============================================================================


@pytest.mark.asyncio
async def test_update_stock_transfer_preview():
    context, _ = create_mock_context()

    request = UpdateStockTransferRequest(
        id=42,
        stock_transfer_number="ST-42-revised",
        additional_info="Updated notes",
        confirm=False,
    )
    result = await _update_stock_transfer_impl(request, context)

    assert result.is_preview is True
    assert result.id == 42
    assert "Preview" in result.message
    assert "stock_transfer_number" in result.message


@pytest.mark.asyncio
async def test_update_stock_transfer_requires_at_least_one_field():
    context, _ = create_mock_context()

    request = UpdateStockTransferRequest(id=42, confirm=False)
    with pytest.raises(ValueError, match="At least one field"):
        await _update_stock_transfer_impl(request, context)


@pytest.mark.asyncio
async def test_update_stock_transfer_confirm_success():
    context, _ = create_mock_context()

    mock_transfer = _make_mock_transfer(
        id=42, stock_transfer_number="ST-42-revised", status="pending"
    )

    with (
        patch(f"{_ST_UPDATE}.asyncio_detailed", new_callable=AsyncMock) as mock_api,
        patch(_ST_UNWRAP_AS, return_value=mock_transfer),
    ):
        request = UpdateStockTransferRequest(
            id=42, stock_transfer_number="ST-42-revised", confirm=True
        )
        result = await _update_stock_transfer_impl(request, context)

    assert result.is_preview is False
    assert result.id == 42
    assert result.stock_transfer_number == "ST-42-revised"
    mock_api.assert_awaited_once()
    kwargs = mock_api.await_args.kwargs
    assert kwargs["id"] == 42
    assert kwargs["body"].stock_transfer_number == "ST-42-revised"


# ============================================================================
# update_stock_transfer_status
# ============================================================================


@pytest.mark.asyncio
async def test_update_stock_transfer_status_preview():
    context, _ = create_mock_context()

    request = UpdateStockTransferStatusRequest(
        id=42, new_status="IN_TRANSIT", confirm=False
    )
    result = await _update_stock_transfer_status_impl(request, context)

    assert result.is_preview is True
    assert result.id == 42
    assert result.status == "IN_TRANSIT"
    assert "Preview" in result.message


@pytest.mark.asyncio
async def test_update_stock_transfer_status_confirm_success():
    context, _ = create_mock_context()

    mock_transfer = _make_mock_transfer(id=42, status="in_transit")

    with (
        patch(
            f"{_ST_UPDATE_STATUS}.asyncio_detailed", new_callable=AsyncMock
        ) as mock_api,
        patch(_ST_UNWRAP_AS, return_value=mock_transfer),
    ):
        request = UpdateStockTransferStatusRequest(
            id=42, new_status="IN_TRANSIT", confirm=True
        )
        result = await _update_stock_transfer_status_impl(request, context)

    assert result.is_preview is False
    assert result.id == 42
    assert result.status == "in_transit"
    mock_api.assert_awaited_once()
    kwargs = mock_api.await_args.kwargs
    assert kwargs["id"] == 42
    # Verify the API status enum was set to "in_transit"
    assert kwargs["body"].status.value == "in_transit"


@pytest.mark.asyncio
async def test_update_stock_transfer_status_invalid_transition_surfaces_error():
    """APIError from invalid transition is surfaced as ValueError with message."""
    context, _ = create_mock_context()

    api_error = APIError("Cannot transition from COMPLETED to IN_TRANSIT", 400)

    with (
        patch(f"{_ST_UPDATE_STATUS}.asyncio_detailed", new_callable=AsyncMock),
        patch(_ST_UNWRAP_AS, side_effect=api_error),
    ):
        request = UpdateStockTransferStatusRequest(
            id=42, new_status="IN_TRANSIT", confirm=True
        )
        with pytest.raises(ValueError, match="Cannot transition"):
            await _update_stock_transfer_status_impl(request, context)


@pytest.mark.asyncio
async def test_update_stock_transfer_status_user_declines():
    """Declined elicitation — no API call, preview returned."""
    context, _ = create_mock_context(elicit_confirm=False)

    with patch(
        f"{_ST_UPDATE_STATUS}.asyncio_detailed", new_callable=AsyncMock
    ) as mock_api:
        request = UpdateStockTransferStatusRequest(
            id=42, new_status="CANCELLED", confirm=True
        )
        result = await _update_stock_transfer_status_impl(request, context)

    assert result.is_preview is True
    assert "cancelled" in result.message.lower()
    mock_api.assert_not_awaited()


# ============================================================================
# delete_stock_transfer
# ============================================================================


@pytest.mark.asyncio
async def test_delete_stock_transfer_preview():
    context, _ = create_mock_context()

    request = DeleteStockTransferRequest(id=42, confirm=False)
    result = await _delete_stock_transfer_impl(request, context)

    assert result.is_preview is True
    assert result.id == 42
    assert "Preview" in result.message


@pytest.mark.asyncio
async def test_delete_stock_transfer_confirm_success():
    context, _ = create_mock_context()

    mock_response = MagicMock()
    mock_response.status_code = 204
    mock_response.parsed = None

    with (
        patch(
            f"{_ST_DELETE}.asyncio_detailed",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_api,
        patch(_ST_IS_SUCCESS, return_value=True),
    ):
        request = DeleteStockTransferRequest(id=42, confirm=True)
        result = await _delete_stock_transfer_impl(request, context)

    assert result.is_preview is False
    assert result.id == 42
    assert "deleted" in result.message.lower()
    mock_api.assert_awaited_once()
    kwargs = mock_api.await_args.kwargs
    assert kwargs["id"] == 42


@pytest.mark.asyncio
async def test_delete_stock_transfer_user_declines():
    context, _ = create_mock_context(elicit_confirm=False)

    with patch(f"{_ST_DELETE}.asyncio_detailed", new_callable=AsyncMock) as mock_api:
        request = DeleteStockTransferRequest(id=42, confirm=True)
        result = await _delete_stock_transfer_impl(request, context)

    assert result.is_preview is True
    assert "cancelled" in result.message.lower()
    mock_api.assert_not_awaited()


# ============================================================================
# format=json (stock_transfers read tool)
# ============================================================================


def _content_text(result) -> str:
    return result.content[0].text


@pytest.mark.asyncio
async def test_list_stock_transfers_format_json_returns_json():
    from katana_mcp.tools.foundation.stock_transfers import (
        ListStockTransfersResponse,
    )

    context, _ = create_mock_context()

    with patch(
        "katana_mcp.tools.foundation.stock_transfers._list_stock_transfers_impl",
        new_callable=AsyncMock,
    ) as mock_impl:
        mock_impl.return_value = ListStockTransfersResponse(
            transfers=[], total_count=0, pagination=None
        )
        result = await list_stock_transfers(format="json", context=context)

    data = json.loads(_content_text(result))
    assert data["total_count"] == 0
