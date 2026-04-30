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

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from katana_mcp.typed_cache.sync import ensure_purchase_orders_synced

from katana_public_api_client.models import PurchaseOrderBase as AttrsPurchaseOrder
from katana_public_api_client.models_pydantic._generated import CachedPurchaseOrder


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

        with patch(
            "katana_mcp.typed_cache.sync.find_purchase_orders.asyncio_detailed",
            new=AsyncMock(return_value=mock_response),
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
        with patch(
            "katana_mcp.typed_cache.sync.find_purchase_orders.asyncio_detailed",
            new=mock_api,
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

        with patch(
            "katana_mcp.typed_cache.sync.find_purchase_orders.asyncio_detailed",
            new=AsyncMock(return_value=mock_response),
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
        with patch(
            "katana_mcp.typed_cache.sync.find_purchase_orders.asyncio_detailed",
            new=mock_api,
        ):
            await ensure_purchase_orders_synced(MagicMock(), typed_cache_engine)
            await ensure_purchase_orders_synced(MagicMock(), typed_cache_engine)
            await ensure_purchase_orders_synced(MagicMock(), typed_cache_engine)

        assert mock_api.call_count == 3


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
