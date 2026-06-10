"""Tests for bin transfer + bin inventory MCP tools.

Covers the seven-tool surface:
- create_bin_transfer (preview + apply, nested rows + traceability)
- list_bin_transfers (list-tool pattern v2 — limit, page, dates, filters)
- modify_bin_transfer (header + row CRUD + status, canonical order,
  wire-aware verification transforms)
- delete_bin_transfer (preview + apply)
- list_bin_inventory (live read, granularity + 'null' filters)
- list_storage_bins / create_storage_bin (live reads + preview/apply)
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from katana_mcp.tools.foundation.bin_transfers import (
    BinTransferHeaderPatch,
    BinTransferRowAdd,
    BinTransferRowInput,
    BinTransferRowUpdate,
    BinTransferStatusPatch,
    BinTransferTraceabilityInput,
    CreateBinTransferRequest,
    CreateStorageBinRequest,
    DeleteBinTransferRequest,
    ListBinInventoryRequest,
    ListBinTransfersRequest,
    ListStorageBinsRequest,
    ModifyBinTransferRequest,
    _build_nested_rows,
    _create_bin_transfer_impl,
    _create_storage_bin_impl,
    _decimal_or_value,
    _delete_bin_transfer_impl,
    _list_bin_inventory_impl,
    _list_bin_transfers_impl,
    _list_storage_bins_impl,
    _modify_bin_transfer_impl,
    _traceability_cmp,
)
from katana_mcp_server.tests.conftest import create_mock_context, patch_typed_cache_sync

from katana_public_api_client.client_types import UNSET
from katana_public_api_client.models import BinTransfer
from tests.factories import (
    make_bin_transfer,
    make_bin_transfer_row,
    mock_entity_for_modify,
    seed_cache,
)

_BT_MODULE = "katana_mcp.tools.foundation.bin_transfers"
_BT_CREATE = "katana_public_api_client.api.bin_transfer.create_bin_transfer"
_BT_CREATE_ROW = "katana_public_api_client.api.bin_transfer.create_bin_transfer_row"
_BT_UPDATE = "katana_public_api_client.api.bin_transfer.update_bin_transfer"
_BT_UPDATE_ROW = "katana_public_api_client.api.bin_transfer.update_bin_transfer_row"
_BT_DELETE_ROW = "katana_public_api_client.api.bin_transfer.delete_bin_transfer_row"
_BT_UPDATE_STATUS = (
    "katana_public_api_client.api.bin_transfer.update_bin_transfer_status"
)
_BT_DELETE = "katana_public_api_client.api.bin_transfer.delete_bin_transfer"
_SB_INVENTORY = "katana_public_api_client.api.storage_bin.get_bin_inventory"
_SB_LIST = "katana_public_api_client.api.storage_bin.get_all_storage_bins"
_SB_CREATE = "katana_public_api_client.api.storage_bin.create_storage_bin"

_BT_UNWRAP_AS = f"{_BT_MODULE}.unwrap_as"
_BT_UNWRAP = f"{_BT_MODULE}.unwrap"
_BT_UNWRAP_DATA = f"{_BT_MODULE}.unwrap_data"
_BT_FETCH = f"{_BT_MODULE}._fetch_bin_transfer_attrs"
_BT_FETCH_ROW = f"{_BT_MODULE}._fetch_bin_transfer_row"

# The modify/delete dispatcher pipes through ``_modification_dispatch``.
_MODIFY_UNWRAP_AS = "katana_mcp.tools._modification_dispatch.unwrap_as"


def _mock_bin_transfer(
    *,
    id: int = 1,
    bin_transfer_number: str = "BT-1",
    location_id: int = 1,
    status: str = "CREATED",
    rows: list | None = None,
) -> MagicMock:
    """Build a mock BinTransfer attrs object (all other fields UNSET)."""
    return mock_entity_for_modify(
        BinTransfer,
        id=id,
        bin_transfer_number=bin_transfer_number,
        location_id=location_id,
        status=status,
        bin_transfer_rows=rows if rows is not None else UNSET,
    )


# ============================================================================
# create_bin_transfer
# ============================================================================


@pytest.mark.asyncio
async def test_create_bin_transfer_preview():
    """Preview returns is_preview=True and does not call API."""
    context, _ = create_mock_context()

    request = CreateBinTransferRequest(
        location_id=1,
        rows=[BinTransferRowInput(variant_id=100, quantity=5)],
        bin_transfer_number="BT-PREVIEW-1",
        preview=True,
    )
    result = await _create_bin_transfer_impl(request, context)

    assert result.is_preview is True
    assert result.location_id == 1
    assert result.bin_transfer_number == "BT-PREVIEW-1"
    assert result.status == "CREATED"
    assert result.item_count == 1
    assert result.id is None
    assert "Preview" in result.message
    assert len(result.next_actions) > 0


@pytest.mark.asyncio
async def test_create_bin_transfer_confirm_success():
    """preview=False builds the nested-rows request and returns the created
    transfer. Quantities and traceability quantities serialize as decimal
    strings; bin ids and traceability ride the nested row objects."""
    context, _ = create_mock_context()
    mock_transfer = _mock_bin_transfer(
        id=42, bin_transfer_number="BT-42", location_id=1, status="CREATED"
    )

    with (
        patch(f"{_BT_CREATE}.asyncio_detailed", new_callable=AsyncMock) as mock_api,
        patch(_BT_UNWRAP_AS, return_value=mock_transfer),
    ):
        request = CreateBinTransferRequest(
            location_id=1,
            rows=[
                BinTransferRowInput(
                    variant_id=100,
                    quantity=5,
                    source_bin_location_id=7,
                    target_bin_location_id=9,
                    traceability=[
                        BinTransferTraceabilityInput(batch_id=77, quantity=5)
                    ],
                )
            ],
            preview=False,
        )
        result = await _create_bin_transfer_impl(request, context)

    assert result.is_preview is False
    assert result.id == 42
    assert result.bin_transfer_number == "BT-42"
    assert result.status == "CREATED"

    mock_api.assert_awaited_once()
    assert mock_api.await_args is not None
    body = mock_api.await_args.kwargs["body"]
    assert body.location_id == 1
    # Number omitted → UNSET so Katana assigns one server-side.
    assert body.bin_transfer_number is UNSET
    row = body.bin_transfer_rows[0]
    assert row.variant_id == 100
    assert row.quantity == "5.0"
    assert row.source_bin_location_id == 7
    assert row.target_bin_location_id == 9
    trace = row.traceability[0].to_dict()
    assert trace == {"batch_id": 77, "quantity": "5.0"}


@pytest.mark.asyncio
async def test_create_bin_transfer_same_bin_rows_warn():
    """Rows with source == target bin raise an operator-facing warning."""
    context, _ = create_mock_context()

    request = CreateBinTransferRequest(
        location_id=1,
        rows=[
            BinTransferRowInput(
                variant_id=100,
                quantity=1,
                source_bin_location_id=7,
                target_bin_location_id=7,
            ),
            BinTransferRowInput(variant_id=101, quantity=1),
        ],
        preview=True,
    )
    result = await _create_bin_transfer_impl(request, context)

    same_bin = [w for w in result.warnings if "same source and target bin" in w]
    assert len(same_bin) == 1
    assert "Row(s) 1" in same_bin[0]


@pytest.mark.asyncio
async def test_create_bin_transfer_rejects_empty_rows():
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        CreateBinTransferRequest(location_id=1, rows=[], preview=True)


@pytest.mark.parametrize(
    "quantity, expected",
    [
        (1.0, "1.0"),
        (1.5, "1.5"),
        (0.123456789, "0.123456789"),
        # Very small value — must NOT use exponent notation OR round away.
        (1e-7, "0.0000001"),
        (1_000_000.5, "1000000.5"),
    ],
)
def test_build_nested_rows_quantity_serialization(
    quantity: float, expected: str
) -> None:
    """``_build_nested_rows`` emits decimal-form strings without scientific
    notation or rounding (same boundary contract as stock-transfer rows)."""
    rows = _build_nested_rows([BinTransferRowInput(variant_id=42, quantity=quantity)])
    assert rows[0].quantity == expected
    assert "e" not in rows[0].quantity.lower()
    # Optional fields omitted → UNSET, not null.
    assert rows[0].source_bin_location_id is UNSET
    assert rows[0].traceability is UNSET


# ============================================================================
# list_bin_transfers — pattern v2
# ============================================================================


@pytest.fixture
def no_sync():
    """Patch ``ensure_bin_transfers_synced`` to a no-op."""
    with patch_typed_cache_sync("bin_transfers"):
        yield


@pytest.mark.asyncio
async def test_list_bin_transfers_invalid_date_raises(
    context_with_typed_cache, no_sync
):
    """Malformed ISO-8601 date is surfaced as ValueError."""
    context, _, _typed_cache = context_with_typed_cache

    with pytest.raises(ValueError, match="Invalid ISO-8601"):
        await _list_bin_transfers_impl(
            ListBinTransfersRequest(created_after="not-a-date"), context
        )


@pytest.mark.asyncio
async def test_list_bin_transfers_filters_by_status(context_with_typed_cache, no_sync):
    """Status filter — tool literals equal the Katana wire values."""
    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [
            make_bin_transfer(id=1, status="CREATED"),
            make_bin_transfer(id=2, status="IN_TRANSIT"),
            make_bin_transfer(id=3, status="DONE"),
        ],
    )

    result = await _list_bin_transfers_impl(
        ListBinTransfersRequest(status="IN_TRANSIT"), context
    )

    assert {t.id for t in result.transfers} == {2}
    assert result.transfers[0].status == "IN_TRANSIT"


@pytest.mark.asyncio
async def test_list_bin_transfers_filters_by_location(
    context_with_typed_cache, no_sync
):
    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [
            make_bin_transfer(id=1, location_id=5),
            make_bin_transfer(id=2, location_id=6),
        ],
    )

    result = await _list_bin_transfers_impl(
        ListBinTransfersRequest(location_id=5), context
    )

    assert {t.id for t in result.transfers} == {1}


@pytest.mark.asyncio
async def test_list_bin_transfers_filters_by_number_and_ids(
    context_with_typed_cache, no_sync
):
    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [
            make_bin_transfer(id=1, bin_transfer_number="BT-100"),
            make_bin_transfer(id=2, bin_transfer_number="BT-200"),
            make_bin_transfer(id=3, bin_transfer_number="BT-300"),
        ],
    )

    by_number = await _list_bin_transfers_impl(
        ListBinTransfersRequest(bin_transfer_number="BT-200"), context
    )
    assert {t.id for t in by_number.transfers} == {2}

    by_ids = await _list_bin_transfers_impl(
        ListBinTransfersRequest(ids=[1, 3]), context
    )
    assert {t.id for t in by_ids.transfers} == {1, 3}


@pytest.mark.asyncio
async def test_list_bin_transfers_date_filters(context_with_typed_cache, no_sync):
    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [
            make_bin_transfer(id=1, created_at=datetime(2025, 12, 15)),
            make_bin_transfer(id=2, created_at=datetime(2026, 2, 15)),
            make_bin_transfer(id=3, created_at=datetime(2026, 5, 1)),
        ],
    )

    result = await _list_bin_transfers_impl(
        ListBinTransfersRequest(
            created_after="2026-01-01T00:00:00+00:00",
            created_before="2026-04-01T00:00:00+00:00",
        ),
        context,
    )

    assert {t.id for t in result.transfers} == {2}


@pytest.mark.asyncio
async def test_list_bin_transfers_include_deleted_default_excludes(
    context_with_typed_cache, no_sync
):
    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [
            make_bin_transfer(id=1),
            make_bin_transfer(id=2, deleted_at=datetime(2026, 3, 1)),
        ],
    )

    default_result = await _list_bin_transfers_impl(ListBinTransfersRequest(), context)
    assert {t.id for t in default_result.transfers} == {1}

    opt_in = await _list_bin_transfers_impl(
        ListBinTransfersRequest(include_deleted=True), context
    )
    assert {t.id for t in opt_in.transfers} == {1, 2}


@pytest.mark.asyncio
async def test_list_bin_transfers_caps_to_limit(context_with_typed_cache, no_sync):
    context, _, typed_cache = context_with_typed_cache
    await seed_cache(typed_cache, [make_bin_transfer(id=i) for i in range(1, 31)])

    result = await _list_bin_transfers_impl(ListBinTransfersRequest(limit=5), context)

    assert len(result.transfers) == 5


@pytest.mark.asyncio
async def test_list_bin_transfers_include_rows(context_with_typed_cache, no_sync):
    """include_rows=True exposes row details — quantity coerces from the wire
    decimal string to float; bins and traceability surface as-is."""
    context, _, typed_cache = context_with_typed_cache
    await seed_cache(
        typed_cache,
        [
            make_bin_transfer(
                id=7,
                rows=[
                    make_bin_transfer_row(
                        id=1,
                        bin_transfer_id=7,
                        variant_id=100,
                        quantity="5.0000000000",
                        source_bin_location_id=11,
                        target_bin_location_id=12,
                        traceability=[{"batch_id": 9, "quantity": "5"}],
                    ),
                    make_bin_transfer_row(
                        id=2, bin_transfer_id=7, variant_id=200, quantity="2"
                    ),
                ],
            ),
        ],
    )

    with_rows = await _list_bin_transfers_impl(
        ListBinTransfersRequest(include_rows=True), context
    )
    without_rows = await _list_bin_transfers_impl(
        ListBinTransfersRequest(include_rows=False), context
    )

    rows = with_rows.transfers[0].rows
    assert rows is not None
    assert len(rows) == 2
    by_id = {r.id: r for r in rows}
    assert by_id[1].quantity == 5.0
    assert by_id[1].source_bin_location_id == 11
    assert by_id[1].target_bin_location_id == 12
    assert by_id[1].traceability is not None
    assert by_id[1].traceability[0]["batch_id"] == 9
    assert by_id[2].quantity == 2.0
    assert with_rows.transfers[0].row_count == 2
    assert without_rows.transfers[0].rows is None
    assert without_rows.transfers[0].row_count == 2


@pytest.mark.asyncio
async def test_list_bin_transfers_excludes_soft_deleted_rows(
    context_with_typed_cache, no_sync
):
    """Soft-deleted transfer rows are hidden from both ``include_rows`` paths."""
    context, _, typed_cache = context_with_typed_cache
    live_row = make_bin_transfer_row(id=1, bin_transfer_id=7, variant_id=100)
    tombstoned = make_bin_transfer_row(id=2, bin_transfer_id=7, variant_id=200)
    tombstoned.deleted_at = datetime(2026, 5, 20)
    await seed_cache(
        typed_cache, [make_bin_transfer(id=7, rows=[live_row, tombstoned])]
    )

    with_rows = await _list_bin_transfers_impl(
        ListBinTransfersRequest(include_rows=True), context
    )

    assert with_rows.transfers[0].rows is not None
    assert [r.id for r in with_rows.transfers[0].rows] == [1]
    assert with_rows.transfers[0].row_count == 1


@pytest.mark.asyncio
async def test_list_bin_transfers_pagination_meta_when_page_set(
    context_with_typed_cache, no_sync
):
    context, _, typed_cache = context_with_typed_cache
    await seed_cache(typed_cache, [make_bin_transfer(id=i) for i in range(1, 12)])

    result = await _list_bin_transfers_impl(
        ListBinTransfersRequest(limit=5, page=2), context
    )

    assert result.pagination is not None
    assert result.pagination.total_records == 11
    assert result.pagination.total_pages == 3
    assert result.pagination.page == 2


# ============================================================================
# modify_bin_transfer
# ============================================================================


@pytest.mark.asyncio
async def test_modify_bt_requires_at_least_one_subpayload():
    context, _ = create_mock_context()
    with pytest.raises(ValueError, match="At least one sub-payload"):
        await _modify_bin_transfer_impl(
            ModifyBinTransferRequest(id=42, preview=True), context
        )


@pytest.mark.asyncio
async def test_modify_bt_header_preview_diffs_against_fetched_prior():
    """Bin transfers have GET-by-id — header diffs carry real prior values."""
    context, _ = create_mock_context()
    existing = _mock_bin_transfer(id=42, bin_transfer_number="BT-OLD")
    existing.to_dict.return_value = {
        "id": 42,
        "bin_transfer_number": "BT-OLD",
        "location_id": 1,
        "status": "CREATED",
    }

    with patch(_BT_FETCH, new=AsyncMock(return_value=existing)):
        request = ModifyBinTransferRequest(
            id=42,
            update_header=BinTransferHeaderPatch(bin_transfer_number="BT-NEW"),
            preview=True,
        )
        response = await _modify_bin_transfer_impl(request, context)

    assert response.is_preview is True
    assert len(response.actions) == 1
    action = response.actions[0]
    assert action.operation == "update_header"
    change = next(c for c in action.changes if c.field == "bin_transfer_number")
    assert change.old == "BT-OLD"
    assert change.new == "BT-NEW"
    assert not change.is_unknown_prior
    # Prior snapshot rides on the response for the card's entity view.
    assert response.prior_state is not None
    assert response.prior_state.get("bin_transfer_number") == "BT-OLD"


@pytest.mark.asyncio
async def test_modify_bt_plan_canonical_order_status_last():
    """Header → row adds → row updates → row deletes → status: a DONE
    transition must see the final row set."""
    context, _ = create_mock_context()
    existing = _mock_bin_transfer(id=42)

    with (
        patch(_BT_FETCH, new=AsyncMock(return_value=existing)),
        patch(_BT_FETCH_ROW, new=AsyncMock(return_value=None)),
    ):
        request = ModifyBinTransferRequest(
            id=42,
            update_header=BinTransferHeaderPatch(additional_info="note"),
            add_rows=[BinTransferRowAdd(variant_id=100, quantity=1)],
            update_rows=[BinTransferRowUpdate(id=9, quantity=2)],
            delete_row_ids=[10],
            update_status=BinTransferStatusPatch(new_status="DONE"),
            preview=True,
        )
        response = await _modify_bin_transfer_impl(request, context)

    assert [a.operation for a in response.actions] == [
        "update_header",
        "add_row",
        "update_row",
        "delete_row",
        "update_status",
    ]
    # Row CRUD plans thread the resolved lookups for the card's row table.
    assert "resolved_variants" in response.extras
    assert "resolved_bins" in response.extras


@pytest.mark.asyncio
async def test_modify_bt_add_row_confirm_dispatches_post_with_parent_id():
    context, _ = create_mock_context()
    echoed_row = MagicMock()
    echoed_row.variant_id = 100
    echoed_row.quantity = "3.5000000000"
    echoed_row.target_bin_location_id = 7

    with (
        patch(_BT_FETCH, new=AsyncMock(return_value=None)),
        patch(
            f"{_BT_CREATE_ROW}.asyncio_detailed", new_callable=AsyncMock
        ) as mock_post,
        patch(_MODIFY_UNWRAP_AS, return_value=echoed_row),
    ):
        request = ModifyBinTransferRequest(
            id=42,
            add_rows=[
                BinTransferRowAdd(
                    variant_id=100, quantity=3.5, target_bin_location_id=7
                )
            ],
            preview=False,
        )
        response = await _modify_bin_transfer_impl(request, context)

    assert response.actions[0].succeeded is True
    mock_post.assert_awaited_once()
    assert mock_post.await_args is not None
    body = mock_post.await_args.kwargs["body"]
    assert body.bin_transfer_id == 42
    assert body.variant_id == 100
    assert body.quantity == "3.5"
    assert body.target_bin_location_id == 7


@pytest.mark.asyncio
async def test_modify_bt_update_row_verifies_against_wire_decimal_string():
    """The echoed quantity is a decimal string (possibly without a decimal
    point) — verification canonicalizes both sides to Decimal so a successful
    write verifies True."""
    context, _ = create_mock_context()
    echoed_row = MagicMock()
    echoed_row.quantity = "3"  # integer-form decimal string

    with (
        patch(_BT_FETCH, new=AsyncMock(return_value=None)),
        patch(_BT_FETCH_ROW, new=AsyncMock(return_value=None)),
        patch(
            f"{_BT_UPDATE_ROW}.asyncio_detailed", new_callable=AsyncMock
        ) as mock_patch_api,
        patch(_MODIFY_UNWRAP_AS, return_value=echoed_row),
    ):
        request = ModifyBinTransferRequest(
            id=42,
            update_rows=[BinTransferRowUpdate(id=9, quantity=3.0)],
            preview=False,
        )
        response = await _modify_bin_transfer_impl(request, context)

    assert response.actions[0].operation == "update_row"
    assert response.actions[0].succeeded is True
    assert response.actions[0].verified is True
    assert mock_patch_api.await_args is not None
    assert mock_patch_api.await_args.kwargs["id"] == 9
    assert mock_patch_api.await_args.kwargs["body"].quantity == "3.0"


@pytest.mark.asyncio
async def test_modify_bt_header_confirm_dispatches_to_update_endpoint():
    context, _ = create_mock_context()
    echoed = _mock_bin_transfer(id=42, bin_transfer_number="BT-NEW")

    with (
        patch(_BT_FETCH, new=AsyncMock(return_value=None)),
        patch(f"{_BT_UPDATE}.asyncio_detailed", new_callable=AsyncMock) as mock_update,
        patch(_MODIFY_UNWRAP_AS, return_value=echoed),
    ):
        request = ModifyBinTransferRequest(
            id=42,
            update_header=BinTransferHeaderPatch(bin_transfer_number="BT-NEW"),
            preview=False,
        )
        response = await _modify_bin_transfer_impl(request, context)

    assert response.actions[0].operation == "update_header"
    assert response.actions[0].succeeded is True
    mock_update.assert_awaited_once()
    assert mock_update.await_args is not None
    assert mock_update.await_args.kwargs["id"] == 42
    assert mock_update.await_args.kwargs["body"].bin_transfer_number == "BT-NEW"


@pytest.mark.asyncio
async def test_modify_bt_delete_row_confirm_dispatches_row_delete():
    context, _ = create_mock_context()
    delete_response = MagicMock()
    delete_response.status_code = 204

    with (
        patch(_BT_FETCH, new=AsyncMock(return_value=None)),
        patch(
            f"{_BT_DELETE_ROW}.asyncio_detailed",
            new=AsyncMock(return_value=delete_response),
        ) as mock_delete,
    ):
        request = ModifyBinTransferRequest(id=42, delete_row_ids=[9], preview=False)
        response = await _modify_bin_transfer_impl(request, context)

    assert response.actions[0].operation == "delete_row"
    assert response.actions[0].target_id == 9
    assert response.actions[0].succeeded is True
    mock_delete.assert_awaited_once()
    assert mock_delete.await_args is not None
    assert mock_delete.await_args.kwargs["id"] == 9


@pytest.mark.asyncio
async def test_modify_bt_status_confirm_dispatches_to_status_endpoint():
    context, _ = create_mock_context()
    echoed = _mock_bin_transfer(id=42, status="IN_TRANSIT")

    with (
        patch(_BT_FETCH, new=AsyncMock(return_value=None)),
        patch(
            f"{_BT_UPDATE_STATUS}.asyncio_detailed", new_callable=AsyncMock
        ) as mock_status,
        patch(_MODIFY_UNWRAP_AS, return_value=echoed),
    ):
        request = ModifyBinTransferRequest(
            id=42,
            update_status=BinTransferStatusPatch(new_status="IN_TRANSIT"),
            preview=False,
        )
        response = await _modify_bin_transfer_impl(request, context)

    assert response.actions[0].operation == "update_status"
    assert response.actions[0].succeeded is True
    # Tool literal equals the wire value — verification needs no transform.
    assert response.actions[0].verified is True
    assert mock_status.await_args is not None
    assert mock_status.await_args.kwargs["id"] == 42
    assert mock_status.await_args.kwargs["body"].status.value == "IN_TRANSIT"


@pytest.mark.asyncio
async def test_modify_bt_fail_fast_synthesizes_not_run_tail():
    """A failed action halts the plan; the unattempted tail lands in
    ``extras['not_run_actions']`` so the card's row table shows NOT RUN."""
    context, _ = create_mock_context()

    async def _boom(*_args, **_kwargs):
        raise RuntimeError("API down")

    with (
        patch(_BT_FETCH, new=AsyncMock(return_value=None)),
        patch(f"{_BT_CREATE_ROW}.asyncio_detailed", new=AsyncMock(side_effect=_boom)),
    ):
        request = ModifyBinTransferRequest(
            id=42,
            add_rows=[BinTransferRowAdd(variant_id=100, quantity=1)],
            update_status=BinTransferStatusPatch(new_status="DONE"),
            preview=False,
        )
        response = await _modify_bin_transfer_impl(request, context)

    assert [a.succeeded for a in response.actions] == [False]
    not_run = response.extras["not_run_actions"]
    assert len(not_run) == 1
    assert not_run[0]["operation"] == "update_status"
    assert not_run[0]["status_label"] == "NOT RUN"


# ----------------------------------------------------------------------------
# Verification transforms
# ----------------------------------------------------------------------------


def test_decimal_or_value_canonicalizes_numeric_forms():
    assert _decimal_or_value("3") == Decimal("3")
    assert _decimal_or_value(3.0) == Decimal("3")
    assert _decimal_or_value("3.5000000000") == Decimal("3.5")
    assert _decimal_or_value(None) is None
    assert _decimal_or_value("abc") == "abc"


def test_traceability_cmp_matches_dump_dicts_against_attrs_objects():
    """The requested side (model_dump dicts) and the echoed side (attrs
    objects) canonicalize to the same tuples."""
    from katana_public_api_client.models import BinTransferTraceability

    requested = [
        {"batch_id": 77, "serial_number_id": None, "quantity": 5.0},
        {"batch_id": None, "serial_number_id": 3, "quantity": 1.0},
    ]
    echoed = [
        BinTransferTraceability(batch_id=None, serial_number_id=3, quantity="1"),
        BinTransferTraceability(batch_id=77, serial_number_id=None, quantity="5.0"),
    ]
    assert _traceability_cmp(requested) == _traceability_cmp(echoed)
    assert _traceability_cmp(None) is None
    assert _traceability_cmp([]) is None


# ============================================================================
# delete_bin_transfer
# ============================================================================


@pytest.mark.asyncio
async def test_delete_bt_preview_carries_prior_state():
    context, _ = create_mock_context()
    existing = _mock_bin_transfer(id=42, bin_transfer_number="BT-DOOMED")
    existing.to_dict.return_value = {
        "id": 42,
        "bin_transfer_number": "BT-DOOMED",
        "location_id": 1,
    }

    with patch(_BT_FETCH, new=AsyncMock(return_value=existing)):
        response = await _delete_bin_transfer_impl(
            DeleteBinTransferRequest(id=42, preview=True), context
        )

    assert response.is_preview is True
    assert response.prior_state is not None
    assert response.prior_state.get("bin_transfer_number") == "BT-DOOMED"
    assert response.actions[0].operation == "delete"


@pytest.mark.asyncio
async def test_delete_bt_confirm_calls_delete_endpoint():
    context, _ = create_mock_context()

    delete_response = MagicMock()
    delete_response.status_code = 204

    with (
        patch(_BT_FETCH, new=AsyncMock(return_value=None)),
        patch(
            f"{_BT_DELETE}.asyncio_detailed",
            new=AsyncMock(return_value=delete_response),
        ) as mock_delete,
    ):
        response = await _delete_bin_transfer_impl(
            DeleteBinTransferRequest(id=42, preview=False), context
        )

    assert response.is_preview is False
    assert response.actions[0].succeeded is True
    mock_delete.assert_awaited_once()
    assert mock_delete.await_args is not None
    assert mock_delete.await_args.kwargs["id"] == 42


# ============================================================================
# list_bin_inventory
# ============================================================================


def _mock_bin_inventory_row(
    *,
    location_id: int = 1,
    variant_id: int = 100,
    bin_location_id: int | None = 7,
    batch_id: int | None = None,
    serial_number_id: int | None = None,
    quantity_in_stock: str = "10.0000000000",
    quantity_committed: str = "2",
    quantity_expected: str = "0",
) -> MagicMock:
    row = MagicMock()
    row.location_id = location_id
    row.variant_id = variant_id
    row.bin_location_id = bin_location_id
    row.batch_id = batch_id
    row.serial_number_id = serial_number_id
    row.quantity_in_stock = quantity_in_stock
    row.quantity_committed = quantity_committed
    row.quantity_expected = quantity_expected
    return row


@pytest.mark.asyncio
async def test_list_bin_inventory_coerces_quantities_and_forwards_filters():
    context, _ = create_mock_context()
    rows = [
        _mock_bin_inventory_row(bin_location_id=7),
        _mock_bin_inventory_row(variant_id=200, bin_location_id=None),
    ]

    with (
        patch(f"{_SB_INVENTORY}.asyncio_detailed", new_callable=AsyncMock) as mock_api,
        patch(_BT_UNWRAP_DATA, return_value=rows),
    ):
        result = await _list_bin_inventory_impl(
            ListBinInventoryRequest(
                granularity="BATCH",
                location_id=1,
                bin_location_id="null",
            ),
            context,
        )

    assert result.total_count == 2
    assert result.granularity == "BATCH"
    assert result.entries[0].quantity_in_stock == 10.0
    assert result.entries[0].quantity_committed == 2.0
    assert result.entries[1].bin_location_id is None

    assert mock_api.await_args is not None
    kwargs = mock_api.await_args.kwargs
    assert kwargs["granularity"].value == "BATCH"
    assert kwargs["location_id"] == 1
    # The literal string 'null' passes through (matches unassigned stock).
    assert kwargs["bin_location_id"] == "null"
    # Omitted filters are UNSET, not None.
    assert kwargs["variant_id"] is UNSET


def test_list_bin_inventory_rejects_malformed_id_filters():
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ListBinInventoryRequest(bin_location_id="abc")
    with pytest.raises(ValidationError):
        ListBinInventoryRequest(batch_id="-3")


# ============================================================================
# list_storage_bins / create_storage_bin
# ============================================================================


def _mock_storage_bin(
    *, id: int = 1, bin_name: str = "A-01", location_id: int = 1
) -> MagicMock:
    b = MagicMock()
    b.id = id
    b.bin_name = bin_name
    b.location_id = location_id
    b.created_at = UNSET
    b.deleted_at = UNSET
    return b


@pytest.mark.asyncio
async def test_list_storage_bins_unwraps_bare_array():
    """``GET /bin_locations`` returns a bare array (documented exception) —
    the impl unwraps the response body itself, not a ``data`` field."""
    context, _ = create_mock_context()
    bins = [
        _mock_storage_bin(id=1, bin_name="A-01"),
        _mock_storage_bin(id=2, bin_name="B-02", location_id=2),
    ]

    with (
        patch(f"{_SB_LIST}.asyncio_detailed", new_callable=AsyncMock) as mock_api,
        patch(_BT_UNWRAP, return_value=bins),
    ):
        result = await _list_storage_bins_impl(
            ListStorageBinsRequest(location_id=1, bin_name="A-01"), context
        )

    assert result.total_count == 2
    assert result.bins[0].bin_name == "A-01"
    assert mock_api.await_args is not None
    kwargs = mock_api.await_args.kwargs
    assert kwargs["location_id"] == 1
    assert kwargs["bin_name"] == "A-01"
    assert kwargs["include_deleted"] is False


@pytest.mark.asyncio
async def test_create_storage_bin_preview_and_apply():
    context, _ = create_mock_context()

    preview = await _create_storage_bin_impl(
        CreateStorageBinRequest(bin_name="C-03", location_id=1, preview=True), context
    )
    assert preview.is_preview is True
    assert preview.id is None
    assert "C-03" in preview.message

    created = _mock_storage_bin(id=55, bin_name="C-03")
    with (
        patch(f"{_SB_CREATE}.asyncio_detailed", new_callable=AsyncMock) as mock_api,
        patch(_BT_UNWRAP_AS, return_value=created),
    ):
        applied = await _create_storage_bin_impl(
            CreateStorageBinRequest(bin_name="C-03", location_id=1, preview=False),
            context,
        )

    assert applied.is_preview is False
    assert applied.id == 55
    assert mock_api.await_args is not None
    body = mock_api.await_args.kwargs["body"]
    assert body.bin_name == "C-03"
    assert body.location_id == 1
