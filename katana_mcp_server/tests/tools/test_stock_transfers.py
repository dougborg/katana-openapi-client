"""Tests for stock transfer MCP tools.

Covers the unified four-tool surface:
- create_stock_transfer (preview + confirm)
- list_stock_transfers (list-tool pattern v2 — limit, page, dates, filters)
- modify_stock_transfer (header + status, preview + confirm + multi-action)
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
    ModifyStockTransferRequest,
    StockTransferBatchTransactionInput,
    StockTransferHeaderPatch,
    StockTransferRowInput,
    StockTransferStatusPatch,
    _create_stock_transfer_impl,
    _delete_stock_transfer_impl,
    _list_stock_transfers_impl,
    _modify_stock_transfer_impl,
    list_stock_transfers,
)

from katana_public_api_client.client_types import UNSET
from katana_public_api_client.utils import APIError
from tests.conftest import create_mock_context, patch_typed_cache_sync
from tests.factories import (
    make_stock_transfer,
    make_stock_transfer_row,
    seed_cache,
)

_ST_CREATE = "katana_public_api_client.api.stock_transfer.create_stock_transfer"
_ST_LIST = "katana_public_api_client.api.stock_transfer.get_all_stock_transfers"
_ST_UPDATE = "katana_public_api_client.api.stock_transfer.update_stock_transfer"
_ST_UPDATE_STATUS = (
    "katana_public_api_client.api.stock_transfer.update_stock_transfer_status"
)
_ST_DELETE = "katana_public_api_client.api.stock_transfer.delete_stock_transfer"

_ST_UNWRAP_AS = "katana_mcp.tools.foundation.stock_transfers.unwrap_as"
_ST_UNWRAP_DATA = "katana_public_api_client.utils.unwrap_data"

# The modify/delete dispatcher pipes through ``_modification_dispatch.unwrap_as``
# and ``is_success`` — modify tests patch those instead of the local re-import.
_MODIFY_ST_UNWRAP_AS = "katana_mcp.tools._modification_dispatch.unwrap_as"
_MODIFY_ST_IS_SUCCESS = "katana_mcp.tools._modification_dispatch.is_success"


# ============================================================================
# Test helpers
# ============================================================================


def _make_mock_transfer(
    *,
    id: int = 1,
    stock_transfer_number: str | None = "ST-1",
    source_location_id: int = 1,
    target_location_id: int = 2,
    status: str = "draft",
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
        status="draft",
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
    assert result.status == "draft"

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
async def test_create_stock_transfer_auto_generates_number_when_order_no_omitted():
    """When ``order_no`` is omitted, the impl auto-generates a timestamped
    ``stock_transfer_number`` rather than sending UNSET — the OpenAPI spec
    marks the field required, so UNSET would 422 at the live API and breaks
    pyright at the construction site (it's typed ``str``, not ``str | Unset``).
    Pins #444.
    """
    import re

    context, _ = create_mock_context()
    mock_transfer = _make_mock_transfer(
        id=99, stock_transfer_number="auto", source_location_id=1, target_location_id=2
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
            # order_no intentionally omitted
            confirm=True,
        )
        await _create_stock_transfer_impl(request, context)

    call_body = mock_api.await_args.kwargs["body"]
    # Auto-generated number is a real string in ``ST-<unix_timestamp>`` form
    # (not UNSET, not empty, not None).
    assert isinstance(call_body.stock_transfer_number, str)
    assert re.fullmatch(r"ST-\d+", call_body.stock_transfer_number), (
        f"expected auto-generated ST-<timestamp> number, got "
        f"{call_body.stock_transfer_number!r}"
    )


@pytest.mark.asyncio
async def test_create_stock_transfer_passes_through_provided_order_no():
    """When ``order_no`` is provided, it flows through verbatim — the
    auto-generation only kicks in when omitted."""
    context, _ = create_mock_context()
    mock_transfer = _make_mock_transfer(
        id=100,
        stock_transfer_number="MY-CUSTOM-99",
        source_location_id=1,
        target_location_id=2,
    )

    with (
        patch(f"{_ST_CREATE}.asyncio_detailed", new_callable=AsyncMock) as mock_api,
        patch(_ST_UNWRAP_AS, return_value=mock_transfer),
    ):
        request = CreateStockTransferRequest(
            source_location_id=1,
            destination_location_id=2,
            expected_arrival_date=datetime(2026, 5, 1, 12, 0, tzinfo=UTC),
            order_no="MY-CUSTOM-99",
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
        await _create_stock_transfer_impl(request, context)

    call_body = mock_api.await_args.kwargs["body"]
    assert call_body.stock_transfer_number == "MY-CUSTOM-99"


@pytest.mark.asyncio
async def test_create_stock_transfer_confirm_refuses_when_source_equals_destination():
    """confirm=True with source==destination must refuse — defense in depth.
    The preview UI's BLOCK warning suppresses Confirm, but a programmatic
    caller skipping the UI would otherwise create a no-op transfer.
    """
    context, _ = create_mock_context()

    with patch(f"{_ST_CREATE}.asyncio_detailed", new_callable=AsyncMock) as mock_api:
        request = CreateStockTransferRequest(
            source_location_id=42,
            destination_location_id=42,  # same!
            expected_arrival_date=datetime(2026, 5, 1, 12, 0, tzinfo=UTC),
            rows=[StockTransferRowInput(variant_id=100, quantity=5)],
            confirm=True,
        )
        result = await _create_stock_transfer_impl(request, context)

    assert result.is_preview is False
    block_warnings = [w for w in result.warnings if w.startswith("BLOCK:")]
    assert len(block_warnings) == 1
    assert "same" in block_warnings[0].lower()
    assert "Refused" in result.message
    # Critical: the create API must NOT have been called.
    mock_api.assert_not_called()


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


@pytest.fixture
def no_sync():
    """Patch ``ensure_stock_transfers_synced`` to a no-op."""
    with patch_typed_cache_sync("stock_transfers"):
        yield


@pytest.mark.asyncio
async def test_list_stock_transfers_invalid_date_raises(
    context_with_typed_cache, no_sync
):
    """Malformed ISO-8601 date is surfaced as ValueError."""
    context, _, _typed_cache = context_with_typed_cache

    with pytest.raises(ValueError, match="Invalid ISO-8601"):
        await _list_stock_transfers_impl(
            ListStockTransfersRequest(created_after="not-a-date"), context
        )


@pytest.mark.asyncio
async def test_list_stock_transfers_filters_by_status(
    context_with_typed_cache, no_sync
):
    """Status filter (uppercase Literal) folds to lowercase against the cache column."""
    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [
            make_stock_transfer(id=1, status="draft"),
            make_stock_transfer(id=2, status="inTransit"),
            make_stock_transfer(id=3, status="received"),
        ],
    )

    result = await _list_stock_transfers_impl(
        ListStockTransfersRequest(status="IN_TRANSIT"), context
    )

    assert {t.id for t in result.transfers} == {2}


@pytest.mark.asyncio
async def test_list_stock_transfers_location_filters(context_with_typed_cache, no_sync):
    """source_location_id / destination_location_id apply as direct column filters."""
    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [
            make_stock_transfer(id=1, source_location_id=5, target_location_id=9),
            make_stock_transfer(id=2, source_location_id=5, target_location_id=10),
            make_stock_transfer(id=3, source_location_id=6, target_location_id=9),
        ],
    )

    by_source = await _list_stock_transfers_impl(
        ListStockTransfersRequest(source_location_id=5), context
    )
    assert {t.id for t in by_source.transfers} == {1, 2}

    by_dest = await _list_stock_transfers_impl(
        ListStockTransfersRequest(destination_location_id=9), context
    )
    assert {t.id for t in by_dest.transfers} == {1, 3}


@pytest.mark.asyncio
async def test_list_stock_transfers_filters_by_number(
    context_with_typed_cache, no_sync
):
    """`stock_transfer_number` is an exact-match column filter."""
    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [
            make_stock_transfer(id=1, stock_transfer_number="ST-100"),
            make_stock_transfer(id=2, stock_transfer_number="ST-200"),
        ],
    )

    result = await _list_stock_transfers_impl(
        ListStockTransfersRequest(stock_transfer_number="ST-200"), context
    )

    assert {t.id for t in result.transfers} == {2}


@pytest.mark.asyncio
async def test_list_stock_transfers_date_filters(context_with_typed_cache, no_sync):
    """`created_after` / `created_before` apply as indexed range filters."""
    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [
            make_stock_transfer(id=1, created_at=datetime(2025, 12, 15)),  # before
            make_stock_transfer(id=2, created_at=datetime(2026, 2, 15)),  # inside
            make_stock_transfer(id=3, created_at=datetime(2026, 5, 1)),  # after
        ],
    )

    result = await _list_stock_transfers_impl(
        ListStockTransfersRequest(
            created_after="2026-01-01T00:00:00+00:00",
            created_before="2026-04-01T00:00:00+00:00",
        ),
        context,
    )

    assert {t.id for t in result.transfers} == {2}


@pytest.mark.asyncio
async def test_list_stock_transfers_caps_to_limit(context_with_typed_cache, no_sync):
    """`limit` caps the result size even when more rows match."""
    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [make_stock_transfer(id=i) for i in range(1, 31)],
    )

    result = await _list_stock_transfers_impl(
        ListStockTransfersRequest(limit=5), context
    )

    assert len(result.transfers) == 5


@pytest.mark.asyncio
async def test_list_stock_transfers_include_rows(context_with_typed_cache, no_sync):
    """include_rows=True exposes per-transfer row details."""
    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [
            make_stock_transfer(
                id=7,
                rows=[
                    make_stock_transfer_row(
                        id=1, stock_transfer_id=7, variant_id=100, quantity=5.0
                    ),
                    make_stock_transfer_row(
                        id=2, stock_transfer_id=7, variant_id=200, quantity=2.0
                    ),
                ],
            ),
        ],
    )

    with_rows = await _list_stock_transfers_impl(
        ListStockTransfersRequest(include_rows=True), context
    )
    without_rows = await _list_stock_transfers_impl(
        ListStockTransfersRequest(include_rows=False), context
    )

    assert with_rows.transfers[0].rows is not None
    assert len(with_rows.transfers[0].rows) == 2
    assert with_rows.transfers[0].row_count == 2
    assert without_rows.transfers[0].rows is None
    assert without_rows.transfers[0].row_count == 2


@pytest.mark.asyncio
async def test_list_stock_transfers_pagination_meta_when_page_set(
    context_with_typed_cache, no_sync
):
    """An explicit `page` populates `pagination` from a SQL COUNT against the same filter set."""
    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [make_stock_transfer(id=i) for i in range(1, 12)],
    )

    result = await _list_stock_transfers_impl(
        ListStockTransfersRequest(limit=5, page=2), context
    )

    assert result.pagination is not None
    assert result.pagination.total_records == 11
    assert result.pagination.total_pages == 3
    assert result.pagination.page == 2
    assert result.pagination.first_page is False


@pytest.mark.asyncio
async def test_list_stock_transfers_no_pagination_when_page_not_set(
    context_with_typed_cache, no_sync
):
    """When page is not set, pagination meta stays None."""
    context, _, typed_cache = context_with_typed_cache
    await seed_cache(typed_cache, [make_stock_transfer(id=1)])

    result = await _list_stock_transfers_impl(
        ListStockTransfersRequest(limit=10), context
    )

    assert result.pagination is None


# ============================================================================
# modify_stock_transfer — unified header + status surface
# ============================================================================


@pytest.mark.asyncio
async def test_modify_st_requires_at_least_one_subpayload():
    context, _ = create_mock_context()
    with pytest.raises(ValueError, match="At least one sub-payload"):
        await _modify_stock_transfer_impl(
            ModifyStockTransferRequest(id=42, confirm=False), context
        )


@pytest.mark.asyncio
async def test_modify_st_header_preview_emits_planned_action():
    context, _ = create_mock_context()
    request = ModifyStockTransferRequest(
        id=42,
        update_header=StockTransferHeaderPatch(
            stock_transfer_number="ST-42-revised",
            additional_info="Updated notes",
        ),
        confirm=False,
    )
    response = await _modify_stock_transfer_impl(request, context)

    assert response.is_preview is True
    assert response.entity_id == 42
    assert len(response.actions) == 1
    action = response.actions[0]
    assert action.operation == "update_header"
    # No GET-by-id endpoint — every change is unknown_prior=True.
    assert all(c.is_unknown_prior for c in action.changes)


@pytest.mark.asyncio
async def test_modify_st_header_confirm_dispatches_to_update_endpoint():
    context, _ = create_mock_context()
    mock_transfer = _make_mock_transfer(
        id=42, stock_transfer_number="ST-42-revised", status="draft"
    )
    with (
        patch(f"{_ST_UPDATE}.asyncio_detailed", new_callable=AsyncMock) as mock_update,
        patch(_MODIFY_ST_UNWRAP_AS, return_value=mock_transfer),
    ):
        request = ModifyStockTransferRequest(
            id=42,
            update_header=StockTransferHeaderPatch(
                stock_transfer_number="ST-42-revised"
            ),
            confirm=True,
        )
        response = await _modify_stock_transfer_impl(request, context)

    assert response.is_preview is False
    assert response.entity_id == 42
    assert len(response.actions) == 1
    assert response.actions[0].operation == "update_header"
    assert response.actions[0].succeeded is True
    mock_update.assert_awaited_once()
    kwargs = mock_update.await_args.kwargs
    assert kwargs["id"] == 42
    assert kwargs["body"].stock_transfer_number == "ST-42-revised"


@pytest.mark.asyncio
async def test_modify_st_status_confirm_dispatches_to_status_endpoint():
    context, _ = create_mock_context()
    mock_transfer = _make_mock_transfer(id=42, status="inTransit")
    with (
        patch(
            f"{_ST_UPDATE_STATUS}.asyncio_detailed", new_callable=AsyncMock
        ) as mock_status,
        patch(_MODIFY_ST_UNWRAP_AS, return_value=mock_transfer),
    ):
        request = ModifyStockTransferRequest(
            id=42,
            update_status=StockTransferStatusPatch(new_status="IN_TRANSIT"),
            confirm=True,
        )
        response = await _modify_stock_transfer_impl(request, context)

    assert response.is_preview is False
    assert len(response.actions) == 1
    assert response.actions[0].operation == "update_status"
    assert response.actions[0].succeeded is True
    mock_status.assert_awaited_once()
    kwargs = mock_status.await_args.kwargs
    assert kwargs["id"] == 42
    # The API status enum should be the camelCase wire value ``inTransit``.
    assert kwargs["body"].status.value == "inTransit"


@pytest.mark.asyncio
async def test_modify_st_canonical_order_header_then_status():
    """Both sub-payloads in one call — header runs first, status runs last."""
    context, _ = create_mock_context()
    mock_after_header = _make_mock_transfer(
        id=42, stock_transfer_number="ST-42-revised", status="draft"
    )
    mock_after_status = _make_mock_transfer(
        id=42, stock_transfer_number="ST-42-revised", status="inTransit"
    )
    with (
        patch(f"{_ST_UPDATE}.asyncio_detailed", new_callable=AsyncMock) as mock_update,
        patch(
            f"{_ST_UPDATE_STATUS}.asyncio_detailed", new_callable=AsyncMock
        ) as mock_status,
        patch(_MODIFY_ST_UNWRAP_AS, side_effect=[mock_after_header, mock_after_status]),
    ):
        request = ModifyStockTransferRequest(
            id=42,
            update_header=StockTransferHeaderPatch(
                stock_transfer_number="ST-42-revised"
            ),
            update_status=StockTransferStatusPatch(new_status="IN_TRANSIT"),
            confirm=True,
        )
        response = await _modify_stock_transfer_impl(request, context)

    assert response.is_preview is False
    assert [a.operation for a in response.actions] == ["update_header", "update_status"]
    assert all(a.succeeded is True for a in response.actions)
    mock_update.assert_awaited_once()
    mock_status.assert_awaited_once()


@pytest.mark.asyncio
async def test_modify_st_status_failfast_halts_remaining_actions():
    """Header fails — status call must not be attempted."""
    context, _ = create_mock_context()
    api_error = APIError("update_stock_transfer rejected", 422)
    with (
        patch(f"{_ST_UPDATE}.asyncio_detailed", new_callable=AsyncMock),
        patch(
            f"{_ST_UPDATE_STATUS}.asyncio_detailed", new_callable=AsyncMock
        ) as mock_status,
        patch(_MODIFY_ST_UNWRAP_AS, side_effect=api_error),
    ):
        request = ModifyStockTransferRequest(
            id=42,
            update_header=StockTransferHeaderPatch(
                stock_transfer_number="ST-42-revised"
            ),
            update_status=StockTransferStatusPatch(new_status="IN_TRANSIT"),
            confirm=True,
        )
        response = await _modify_stock_transfer_impl(request, context)

    assert response.is_preview is False
    # The dispatcher's fail-fast contract: response.actions reflects what was
    # attempted. Header failed (recorded), status was never attempted (omitted).
    assert len(response.actions) == 1
    assert response.actions[0].operation == "update_header"
    assert response.actions[0].succeeded is False
    assert response.actions[0].error is not None
    mock_status.assert_not_awaited()


# ============================================================================
# delete_stock_transfer
# ============================================================================


@pytest.mark.asyncio
async def test_delete_stock_transfer_preview():
    context, _ = create_mock_context()
    request = DeleteStockTransferRequest(id=42, confirm=False)
    response = await _delete_stock_transfer_impl(request, context)

    assert response.is_preview is True
    assert response.entity_id == 42
    assert len(response.actions) == 1
    assert response.actions[0].operation == "delete"


@pytest.mark.asyncio
async def test_delete_stock_transfer_confirm_success():
    context, _ = create_mock_context()
    mock_response = MagicMock(status_code=204, parsed=None)
    with (
        patch(
            f"{_ST_DELETE}.asyncio_detailed",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_delete,
        patch(_MODIFY_ST_IS_SUCCESS, return_value=True),
    ):
        request = DeleteStockTransferRequest(id=42, confirm=True)
        response = await _delete_stock_transfer_impl(request, context)

    assert response.is_preview is False
    assert response.actions[0].succeeded is True
    mock_delete.assert_awaited_once()
    kwargs = mock_delete.await_args.kwargs
    assert kwargs["id"] == 42


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
