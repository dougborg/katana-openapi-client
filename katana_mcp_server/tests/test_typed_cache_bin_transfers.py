"""Typed-cache sync tests for the bin transfer entity (#943).

Pins the three spec-specific behaviors of ``_BIN_TRANSFER_SPEC``:

- parent + nested rows upsert through the generic pipeline, with the wire
  decimal-string ``quantity`` and the ``traceability`` JSON column intact;
- ``supports_incremental=False`` — the fetch never sends ``updated_at_min``
  even when a watermark exists (the endpoint doesn't support it);
- ``reconcile_children=True`` — a row missing from the parent payload is
  deleted from the cache (generic reconcile behavior, pinned here for the
  bin tables specifically).
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from katana_mcp.typed_cache import ensure_bin_transfers_synced
from katana_mcp.typed_cache.sync_state import SyncState
from sqlmodel import select

from katana_public_api_client.models import BinTransfer as AttrsBinTransfer
from katana_public_api_client.models_pydantic._generated import (
    CachedBinTransfer,
    CachedBinTransferRow,
)

_BT_LIST_API = "katana_mcp.typed_cache.sync.get_all_bin_transfers.asyncio_detailed"


def _bt_attrs(*, bt_id: int, row_ids: list[int]) -> AttrsBinTransfer:
    """Build a BinTransfer attrs payload with the given nested row IDs."""
    return AttrsBinTransfer.from_dict(
        {
            "id": bt_id,
            "bin_transfer_number": f"BT-{bt_id}",
            "location_id": 1,
            "status": "CREATED",
            "created_at": "2026-06-01T00:00:00Z",
            "updated_at": "2026-06-01T00:00:00Z",
            "bin_transfer_rows": [
                {
                    "id": row_id,
                    "bin_transfer_id": bt_id,
                    "variant_id": 100 + row_id,
                    "quantity": "2.5",
                    "source_bin_location_id": 7,
                    "target_bin_location_id": 9,
                    "traceability": [{"batch_id": 3, "quantity": "2.5"}],
                }
                for row_id in row_ids
            ],
        }
    )


def _bt_response(attrs_transfers: list[AttrsBinTransfer]) -> MagicMock:
    parsed = MagicMock()
    parsed.data = attrs_transfers
    response = MagicMock()
    response.status_code = 200
    response.parsed = parsed
    return response


@pytest.mark.asyncio
async def test_bin_transfer_sync_upserts_parents_and_rows(typed_cache_engine):
    """Parent + nested rows land; quantity stays a decimal string and the
    traceability JSON column round-trips."""
    with patch(
        _BT_LIST_API,
        new=AsyncMock(return_value=_bt_response([_bt_attrs(bt_id=5, row_ids=[11])])),
    ):
        await ensure_bin_transfers_synced(MagicMock(), typed_cache_engine)

    async with typed_cache_engine.session() as session:
        parents = (await session.exec(select(CachedBinTransfer))).all()
        rows = (await session.exec(select(CachedBinTransferRow))).all()

    assert [p.id for p in parents] == [5]
    assert parents[0].bin_transfer_number == "BT-5"
    assert parents[0].status == "CREATED"
    assert [r.id for r in rows] == [11]
    row = rows[0]
    assert row.bin_transfer_id == 5
    assert row.variant_id == 111
    assert row.quantity == "2.5"
    assert row.source_bin_location_id == 7
    assert row.target_bin_location_id == 9
    assert row.traceability is not None
    trace = row.traceability[0]
    batch_id = trace.batch_id if hasattr(trace, "batch_id") else trace["batch_id"]
    assert batch_id == 3


@pytest.mark.asyncio
async def test_bin_transfer_sync_never_sends_updated_at_min(typed_cache_engine):
    """``supports_incremental=False``: even with a persisted watermark, the
    fetch carries ``include_deleted=True`` but no ``updated_at_min`` — the
    endpoint doesn't support it and would 4xx or silently ignore it."""
    async with typed_cache_engine.session() as session:
        session.add(
            SyncState(entity_type="bin_transfer", last_synced=datetime(2026, 6, 1))
        )
        await session.commit()

    with patch(_BT_LIST_API, new=AsyncMock(return_value=_bt_response([]))) as mock_api:
        await ensure_bin_transfers_synced(MagicMock(), typed_cache_engine)

    assert mock_api.await_args is not None
    kwargs = mock_api.await_args.kwargs
    assert kwargs["include_deleted"] is True
    assert "updated_at_min" not in kwargs


@pytest.mark.asyncio
async def test_bin_transfer_sync_reconciles_dropped_rows(typed_cache_engine):
    """A cached row missing from the parent's nested list is deleted —
    ``reconcile_children=True`` treats the parent payload as authoritative."""
    with patch(
        _BT_LIST_API,
        new=AsyncMock(
            return_value=_bt_response([_bt_attrs(bt_id=5, row_ids=[11, 12])])
        ),
    ):
        await ensure_bin_transfers_synced(MagicMock(), typed_cache_engine)

    with patch(
        _BT_LIST_API,
        new=AsyncMock(return_value=_bt_response([_bt_attrs(bt_id=5, row_ids=[11])])),
    ):
        await ensure_bin_transfers_synced(MagicMock(), typed_cache_engine)

    async with typed_cache_engine.session() as session:
        rows = (await session.exec(select(CachedBinTransferRow))).all()
    assert [r.id for r in rows] == [11]
