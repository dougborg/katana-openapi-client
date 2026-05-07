"""Tests for soft-delete handling in typed-cache sync.

Reproduces the user-reported "ghost record" symptom: a record deleted
in the Katana UI used to remain in the cache without ``deleted_at`` set,
because the API hides soft-deletes by default and our sync inherited
that hiding. With ``include_deleted=True``, the tombstone propagates
into the cache row, and the existing ``deleted_at IS NULL`` filter on
every ``list_*`` query naturally excludes it from results — while the
row itself persists for any future audit/history need (mirroring
Katana's own soft-delete model).
"""

from __future__ import annotations

import contextlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from katana_mcp.typed_cache.sync import ensure_purchase_orders_synced

from katana_public_api_client.models import PurchaseOrderBase as AttrsPurchaseOrder
from katana_public_api_client.models_pydantic._generated import CachedPurchaseOrder


def _empty_response() -> MagicMock:
    """Build a stock 200/empty-data API response for stubbing related-spec fetches."""
    parsed = MagicMock()
    parsed.data = []
    response = MagicMock()
    response.status_code = 200
    response.parsed = parsed
    return response


@contextlib.contextmanager
def _stub_po_row_sync():
    """Stub the ``/purchase_order_rows`` fetch so PO-spec tests don't need to model it.

    The PO sync fans out to the row sync via ``related_specs`` (added to
    catch tombstones the parent response omits). Tests focused on the
    parent path patch only ``find_purchase_orders``; without this stub,
    the related row sync would attempt a real HTTP call against a
    ``MagicMock`` client.
    """
    with patch(
        "katana_mcp.typed_cache.sync.get_all_purchase_order_rows.asyncio_detailed",
        new=AsyncMock(return_value=_empty_response()),
    ):
        yield


class TestSoftDeleteSync:
    """Tombstone propagation: API ``deleted_at`` lands on the cache row."""

    @pytest.mark.asyncio
    async def test_deleted_at_propagates_to_cache(self, typed_cache_engine):
        """A row the API reports as deleted lands in the cache with ``deleted_at`` set.

        Reproduces the user-reported symptom: a PO deleted in the Katana
        UI used to remain in the cache as a "live" row because the API
        hides soft-deletes by default. With ``include_deleted=True`` the
        tombstone surfaces, the upsert propagates ``deleted_at``, and the
        ``list_*`` query's existing ``deleted_at IS NULL`` filter hides
        the row from callers — without us losing the historical record.
        """
        # Seed the cache with a "live" PO that the API is about to report deleted.
        async with typed_cache_engine.session() as session:
            session.add(CachedPurchaseOrder(id=42, order_no="PO-GHOST-42"))
            await session.commit()

        # Build the attrs response: same id, but with deleted_at populated.
        deleted_attrs = AttrsPurchaseOrder.from_dict(
            {
                "id": 42,
                "order_no": "PO-GHOST-42",
                "entity_type": "regular",
                "supplier_id": 1,
                "currency": "USD",
                "status": "NOT_RECEIVED",
                "billing_status": "NOT_BILLED",
                "deleted_at": "2026-01-15T10:00:00.000Z",
            }
        )
        mock_parsed = MagicMock()
        mock_parsed.data = [deleted_attrs]
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.parsed = mock_parsed

        with (
            patch(
                "katana_mcp.typed_cache.sync.find_purchase_orders.asyncio_detailed",
                new=AsyncMock(return_value=mock_response),
            ),
            _stub_po_row_sync(),
        ):
            await ensure_purchase_orders_synced(MagicMock(), typed_cache_engine)

        # Row persists for history; deleted_at is set so list queries hide it.
        async with typed_cache_engine.session() as session:
            cached = await session.get(CachedPurchaseOrder, 42)
            assert cached is not None
            assert cached.deleted_at is not None

    @pytest.mark.asyncio
    async def test_sync_passes_include_deleted_true(self, typed_cache_engine):
        """Without ``include_deleted=True`` the API hides soft-deletes — pin the call."""
        mock_parsed = MagicMock()
        mock_parsed.data = []
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.parsed = mock_parsed

        mock_api = AsyncMock(return_value=mock_response)
        with (
            patch(
                "katana_mcp.typed_cache.sync.find_purchase_orders.asyncio_detailed",
                new=mock_api,
            ),
            _stub_po_row_sync(),
        ):
            await ensure_purchase_orders_synced(MagicMock(), typed_cache_engine)

        assert mock_api.call_args.kwargs["include_deleted"] is True

    @pytest.mark.asyncio
    async def test_live_row_alongside_deleted_round_trips_correctly(
        self, typed_cache_engine
    ):
        """Mixed response: live row updates without deleted_at; deleted row gets tombstone."""
        async with typed_cache_engine.session() as session:
            session.add(CachedPurchaseOrder(id=1, order_no="PO-LIVE-1"))
            session.add(CachedPurchaseOrder(id=2, order_no="PO-DEL-2"))
            await session.commit()

        live_attrs = AttrsPurchaseOrder.from_dict(
            {
                "id": 1,
                "order_no": "PO-LIVE-1-UPDATED",
                "entity_type": "regular",
                "supplier_id": 1,
                "currency": "USD",
                "status": "NOT_RECEIVED",
                "billing_status": "NOT_BILLED",
                "deleted_at": None,
            }
        )
        deleted_attrs = AttrsPurchaseOrder.from_dict(
            {
                "id": 2,
                "order_no": "PO-DEL-2",
                "entity_type": "regular",
                "supplier_id": 1,
                "currency": "USD",
                "status": "NOT_RECEIVED",
                "billing_status": "NOT_BILLED",
                "deleted_at": "2026-01-15T10:00:00.000Z",
            }
        )
        mock_parsed = MagicMock()
        mock_parsed.data = [live_attrs, deleted_attrs]
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.parsed = mock_parsed

        with (
            patch(
                "katana_mcp.typed_cache.sync.find_purchase_orders.asyncio_detailed",
                new=AsyncMock(return_value=mock_response),
            ),
            _stub_po_row_sync(),
        ):
            await ensure_purchase_orders_synced(MagicMock(), typed_cache_engine)

        async with typed_cache_engine.session() as session:
            live = await session.get(CachedPurchaseOrder, 1)
            assert live is not None
            assert live.order_no == "PO-LIVE-1-UPDATED"
            assert live.deleted_at is None

            tombstoned = await session.get(CachedPurchaseOrder, 2)
            assert tombstoned is not None
            assert tombstoned.deleted_at is not None

    @pytest.mark.asyncio
    async def test_every_call_re_fetches(self, typed_cache_engine):
        """No debounce: back-to-back calls each issue an API request.

        The API call is cheap (incremental delta with ``updated_at_min``
        usually returns 0 rows). Trading that RTT for cache freshness is
        the explicit design choice — pin it so a future "let's add a
        debounce" change doesn't silently regress freshness.
        """
        mock_parsed = MagicMock()
        mock_parsed.data = []
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.parsed = mock_parsed

        mock_api = AsyncMock(return_value=mock_response)
        with (
            patch(
                "katana_mcp.typed_cache.sync.find_purchase_orders.asyncio_detailed",
                new=mock_api,
            ),
            _stub_po_row_sync(),
        ):
            await ensure_purchase_orders_synced(MagicMock(), typed_cache_engine)
            await ensure_purchase_orders_synced(MagicMock(), typed_cache_engine)
            await ensure_purchase_orders_synced(MagicMock(), typed_cache_engine)

        assert mock_api.call_count == 3


class TestRowLevelTombstoneSync:
    """PR #461 added row-level mutations (delete_purchase_order_row etc.).

    The parent ``find_purchase_orders`` response *hides* soft-deleted nested
    rows (top-level ``include_deleted=true`` doesn't propagate to nested),
    so a row deleted via ``delete_purchase_order_row`` would otherwise stay
    in the cache as a ghost. The dedicated row endpoint surfaces the
    tombstone via its own ``include_deleted`` + watermark, and our
    ``related_specs`` wiring fans out the sync.
    """

    @pytest.mark.asyncio
    async def test_po_row_tombstone_lands_via_separate_endpoint(
        self, typed_cache_engine
    ):
        """A row reported deleted by ``/purchase_order_rows`` lands in cache with deleted_at set."""
        from katana_public_api_client.models import PurchaseOrderRow as AttrsPORow
        from katana_public_api_client.models_pydantic._generated import (
            CachedPurchaseOrderRow,
        )

        # Seed the cache with a "live" row that the row endpoint is about
        # to report deleted.
        async with typed_cache_engine.session() as session:
            session.add(
                CachedPurchaseOrderRow(id=99, purchase_order_id=42, variant_id=7)
            )
            await session.commit()

        deleted_row = AttrsPORow.from_dict(
            {
                "id": 99,
                "purchase_order_id": 42,
                "variant_id": 7,
                "quantity": 1,
                "deleted_at": "2026-01-15T10:00:00.000Z",
            }
        )
        mock_parsed = MagicMock()
        mock_parsed.data = [deleted_row]
        rows_response = MagicMock()
        rows_response.status_code = 200
        rows_response.parsed = mock_parsed

        # Parent endpoint returns nothing (no PO updates); rows endpoint
        # returns the tombstone — this is the wire shape we expect when
        # only a row was deleted.
        with (
            patch(
                "katana_mcp.typed_cache.sync.find_purchase_orders.asyncio_detailed",
                new=AsyncMock(return_value=_empty_response()),
            ),
            patch(
                "katana_mcp.typed_cache.sync.get_all_purchase_order_rows.asyncio_detailed",
                new=AsyncMock(return_value=rows_response),
            ),
        ):
            await ensure_purchase_orders_synced(MagicMock(), typed_cache_engine)

        async with typed_cache_engine.session() as session:
            cached_row = await session.get(CachedPurchaseOrderRow, 99)
            assert cached_row is not None
            assert cached_row.deleted_at is not None

    @pytest.mark.asyncio
    async def test_po_sync_calls_both_parent_and_row_endpoints(
        self, typed_cache_engine
    ):
        """Pin the fan-out: one ``ensure_purchase_orders_synced`` → one fetch each."""
        po_api = AsyncMock(return_value=_empty_response())
        rows_api = AsyncMock(return_value=_empty_response())

        with (
            patch(
                "katana_mcp.typed_cache.sync.find_purchase_orders.asyncio_detailed",
                new=po_api,
            ),
            patch(
                "katana_mcp.typed_cache.sync.get_all_purchase_order_rows.asyncio_detailed",
                new=rows_api,
            ),
        ):
            await ensure_purchase_orders_synced(MagicMock(), typed_cache_engine)

        assert po_api.call_count == 1
        assert rows_api.call_count == 1


class TestRelatedSpecsFanOut:
    """``EntitySpec.related_specs`` syncs sibling entities in parallel."""

    @pytest.mark.asyncio
    async def test_mo_sync_fans_out_to_recipe_rows(self, typed_cache_engine):
        """``ensure_manufacturing_orders_synced`` must also advance the recipe-row watermark.

        Recipe rows live at a separate endpoint with their own watermark
        but are conceptually nested under MO; consumers that join MO ↔
        recipe rows in cache (e.g. ``list_blocking_ingredients``) should
        not need to remember a second sync call. This test pins that
        contract so a future "let's split the syncs" change doesn't
        silently break joins.
        """
        from katana_mcp.typed_cache.sync import ensure_manufacturing_orders_synced

        mock_parsed = MagicMock()
        mock_parsed.data = []
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.parsed = mock_parsed

        mo_api = AsyncMock(return_value=mock_response)
        rows_api = AsyncMock(return_value=mock_response)

        with (
            patch(
                "katana_mcp.typed_cache.sync.get_all_manufacturing_orders.asyncio_detailed",
                new=mo_api,
            ),
            patch(
                "katana_mcp.typed_cache.sync.get_all_manufacturing_order_recipe_rows.asyncio_detailed",
                new=rows_api,
            ),
        ):
            await ensure_manufacturing_orders_synced(MagicMock(), typed_cache_engine)

        # Both endpoints called exactly once during one ensure_*_synced call.
        assert mo_api.call_count == 1
        assert rows_api.call_count == 1


class TestMergeFilteredFetch:
    """``merge_filtered_fetch`` is the filtered write-through entry point.

    Distinct from ``ensure_<entity>_synced``: it merges API results into
    the cache without advancing ``SyncState.last_synced``, so a
    server-side filter (``ingredient_availability=NOT_AVAILABLE``) doesn't
    fool a future watermark-driven delta into thinking it has seen every
    row that changed since the last sync.
    """

    @pytest.mark.asyncio
    async def test_does_not_advance_watermark(self, typed_cache_engine):
        """``merge_filtered_fetch`` leaves the entity's ``SyncState.last_synced`` untouched.

        The watermark means "I've seen everything ≥ this timestamp" — a
        filtered fetch only saw rows matching the predicate, so advancing
        it would silently drift other tools' data. Pin that contract here.
        """
        from datetime import UTC, datetime

        from katana_mcp.typed_cache import (
            MANUFACTURING_ORDER_RECIPE_ROW_SPEC,
            SyncState,
            merge_filtered_fetch,
        )

        from katana_public_api_client.models import (
            ManufacturingOrderRecipeRow as AttrsRecipeRow,
        )

        # Seed the watermark with a known timestamp.
        original = datetime(2026, 1, 15, 10, 0, 0, tzinfo=UTC).replace(tzinfo=None)
        async with typed_cache_engine.session() as session:
            session.add(
                SyncState(
                    entity_type="manufacturing_order_recipe_row",
                    last_synced=original,
                    row_count=10,
                )
            )
            await session.commit()

        attrs_row = AttrsRecipeRow.from_dict(
            {
                "id": 7001,
                "manufacturing_order_id": 5001,
                "variant_id": 9001,
                "ingredient_availability": "NOT_AVAILABLE",
                "planned_quantity_per_unit": 2.0,
                "total_remaining_quantity": 4.0,
            }
        )

        await merge_filtered_fetch(
            typed_cache_engine, MANUFACTURING_ORDER_RECIPE_ROW_SPEC, [attrs_row]
        )

        async with typed_cache_engine.session() as session:
            state = await session.get(SyncState, "manufacturing_order_recipe_row")
            assert state is not None
            assert state.last_synced == original
            assert state.row_count == 10

    @pytest.mark.asyncio
    async def test_populates_cache(self, typed_cache_engine):
        """Rows passed to ``merge_filtered_fetch`` land in the cache via the same conversion as the watermark sync."""
        from katana_mcp.typed_cache import (
            MANUFACTURING_ORDER_RECIPE_ROW_SPEC,
            merge_filtered_fetch,
        )

        from katana_public_api_client.models import (
            ManufacturingOrderRecipeRow as AttrsRecipeRow,
        )
        from katana_public_api_client.models_pydantic._generated import (
            CachedManufacturingOrderRecipeRow,
        )

        attrs_rows = [
            AttrsRecipeRow.from_dict(
                {
                    "id": 7100 + i,
                    "manufacturing_order_id": 5001,
                    "variant_id": 9000 + i,
                    "ingredient_availability": "NOT_AVAILABLE",
                    "planned_quantity_per_unit": float(i),
                    "total_remaining_quantity": float(i * 2),
                }
            )
            for i in range(3)
        ]

        await merge_filtered_fetch(
            typed_cache_engine, MANUFACTURING_ORDER_RECIPE_ROW_SPEC, attrs_rows
        )

        async with typed_cache_engine.session() as session:
            for i in range(3):
                cached = await session.get(CachedManufacturingOrderRecipeRow, 7100 + i)
                assert cached is not None
                assert cached.manufacturing_order_id == 5001
                assert cached.variant_id == 9000 + i
                assert cached.ingredient_availability == "NOT_AVAILABLE"

    @pytest.mark.asyncio
    async def test_empty_input_is_noop(self, typed_cache_engine):
        """Empty iterable: no session opened, no rows written, no exception.

        Cheap guard so callers (filtered tools) can pipe through an
        empty result without conditional logic.
        """
        from katana_mcp.typed_cache import (
            MANUFACTURING_ORDER_RECIPE_ROW_SPEC,
            merge_filtered_fetch,
        )
        from sqlmodel import select

        from katana_public_api_client.models_pydantic._generated import (
            CachedManufacturingOrderRecipeRow,
        )

        await merge_filtered_fetch(
            typed_cache_engine, MANUFACTURING_ORDER_RECIPE_ROW_SPEC, []
        )

        async with typed_cache_engine.session() as session:
            result = await session.exec(select(CachedManufacturingOrderRecipeRow))
            assert result.all() == []


class TestBulkUpsert:
    """``_sync_one_locked`` writes parents and children via a chunked bulk upsert
    (``INSERT ... ON CONFLICT(id) DO UPDATE``) instead of per-row
    ``session.merge``. These tests pin the contract: idempotency, incremental
    column updates, no-op on empty fetches, and correctness when row count
    drives the batch past SQLite's bound-parameter chunk boundary so that
    multiple ``INSERT`` statements are emitted in one sync.
    """

    @pytest.mark.asyncio
    async def test_idempotent_resync(self, typed_cache_engine):
        """Running the same sync twice produces identical state, no errors."""
        from sqlmodel import select

        attrs = AttrsPurchaseOrder.from_dict(
            {
                "id": 7,
                "order_no": "PO-IDEMPOTENT-7",
                "entity_type": "regular",
                "supplier_id": 1,
                "currency": "USD",
                "status": "NOT_RECEIVED",
                "billing_status": "NOT_BILLED",
            }
        )
        parsed = MagicMock()
        parsed.data = [attrs]
        response = MagicMock()
        response.status_code = 200
        response.parsed = parsed

        with (
            patch(
                "katana_mcp.typed_cache.sync.find_purchase_orders.asyncio_detailed",
                new=AsyncMock(return_value=response),
            ),
            _stub_po_row_sync(),
        ):
            await ensure_purchase_orders_synced(MagicMock(), typed_cache_engine)
            await ensure_purchase_orders_synced(MagicMock(), typed_cache_engine)

        async with typed_cache_engine.session() as session:
            result = await session.exec(select(CachedPurchaseOrder))
            rows = result.all()
        assert len(rows) == 1
        assert rows[0].id == 7
        assert rows[0].order_no == "PO-IDEMPOTENT-7"

    @pytest.mark.asyncio
    async def test_incremental_column_update(self, typed_cache_engine):
        """A re-sync with the same id but a different column value updates the row.

        Pins the ``ON CONFLICT DO UPDATE`` half: bulk upsert must overwrite
        existing column values, not silently ignore the conflict.
        """
        async with typed_cache_engine.session() as session:
            session.add(CachedPurchaseOrder(id=11, order_no="PO-OLD-NAME"))
            await session.commit()

        attrs = AttrsPurchaseOrder.from_dict(
            {
                "id": 11,
                "order_no": "PO-NEW-NAME",
                "entity_type": "regular",
                "supplier_id": 1,
                "currency": "USD",
                "status": "NOT_RECEIVED",
                "billing_status": "NOT_BILLED",
            }
        )
        parsed = MagicMock()
        parsed.data = [attrs]
        response = MagicMock()
        response.status_code = 200
        response.parsed = parsed

        with (
            patch(
                "katana_mcp.typed_cache.sync.find_purchase_orders.asyncio_detailed",
                new=AsyncMock(return_value=response),
            ),
            _stub_po_row_sync(),
        ):
            await ensure_purchase_orders_synced(MagicMock(), typed_cache_engine)

        async with typed_cache_engine.session() as session:
            cached = await session.get(CachedPurchaseOrder, 11)
            assert cached is not None
            assert cached.order_no == "PO-NEW-NAME"

    @pytest.mark.asyncio
    async def test_empty_response_writes_no_rows_no_error(self, typed_cache_engine):
        """Zero-row response advances ``SyncState`` without a SQL error.

        Bulk insert with an empty values list raises ``CompileError``; the
        helper's early return guards against that. Also verifies the
        ``SyncState`` watermark still moves so the next sync is incremental.
        """
        from katana_mcp.typed_cache.sync_state import SyncState
        from sqlmodel import select

        with (
            patch(
                "katana_mcp.typed_cache.sync.find_purchase_orders.asyncio_detailed",
                new=AsyncMock(return_value=_empty_response()),
            ),
            _stub_po_row_sync(),
        ):
            await ensure_purchase_orders_synced(MagicMock(), typed_cache_engine)

        async with typed_cache_engine.session() as session:
            po_rows = (await session.exec(select(CachedPurchaseOrder))).all()
            state = await session.get(SyncState, "purchase_order")
        assert po_rows == []
        assert state is not None
        assert state.last_synced is not None
        assert state.row_count == 0

    @pytest.mark.asyncio
    async def test_bulk_upsert_past_chunking_boundary(self, typed_cache_engine):
        """Sync 250 recipe rows in one shot — exercises multi-chunk bulk upsert.

        Row count, not column count, drives this case past SQLite's 999
        bound-parameter cap: ``CachedManufacturingOrderRecipeRow`` is a
        narrow schema (~13 cols), but 250 rows at ~13 cols each = ~3250
        params, well over the cap. Confirms the ``itertools.batched``
        chunking emits multiple ``INSERT ... ON CONFLICT`` statements that
        together cover the whole batch with no rows dropped.
        """
        from katana_mcp.typed_cache.sync import (
            ensure_manufacturing_order_recipe_rows_synced,
        )
        from sqlmodel import func, select

        from katana_public_api_client.models import (
            ManufacturingOrderRecipeRow as AttrsRecipeRow,
        )
        from katana_public_api_client.models_pydantic._generated import (
            CachedManufacturingOrderRecipeRow,
        )

        attrs_rows = [
            AttrsRecipeRow.from_dict(
                {
                    "id": i,
                    "manufacturing_order_id": 1,
                    "variant_id": 100 + i,
                    "planned_quantity_per_unit": 1.0,
                    "total_actual_quantity": 0.0,
                    "cost": 0.0,
                }
            )
            for i in range(1, 251)
        ]
        parsed = MagicMock()
        parsed.data = attrs_rows
        response = MagicMock()
        response.status_code = 200
        response.parsed = parsed

        with patch(
            "katana_mcp.typed_cache.sync.get_all_manufacturing_order_recipe_rows.asyncio_detailed",
            new=AsyncMock(return_value=response),
        ):
            await ensure_manufacturing_order_recipe_rows_synced(
                MagicMock(), typed_cache_engine
            )

        async with typed_cache_engine.session() as session:
            count = (
                await session.exec(
                    select(func.count()).select_from(CachedManufacturingOrderRecipeRow)
                )
            ).one()
        assert count == 250
