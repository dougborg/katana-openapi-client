"""Tests for the rebuild_cache MCP tool."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from katana_mcp.tools.foundation.cache_admin import (
    RebuildCacheRequest,
    _rebuild_cache_impl,
)
from katana_mcp.typed_cache import ENTITY_SPECS, SyncState, force_resync
from sqlmodel import select

from katana_public_api_client.models import (
    RegularPurchaseOrder as AttrsRegularPurchaseOrder,
)
from katana_public_api_client.models_pydantic._generated import (
    CachedManufacturingOrder,
    CachedPurchaseOrder,
    CachedPurchaseOrderRow,
    CachedSalesOrder,
    CachedStockAdjustment,
    CachedStockTransfer,
)
from tests.conftest import create_mock_context
from tests.factories import (
    make_manufacturing_order,
    make_purchase_order,
    make_purchase_order_row,
    make_sales_order,
    make_stock_adjustment,
    make_stock_transfer,
    seed_cache,
)

# ============================================================================
# Helpers
# ============================================================================


def _empty_paginated_response() -> MagicMock:
    """Build a mock matching ``unwrap_data(response, default=[])`` shape with no rows."""
    parsed = MagicMock()
    parsed.data = []
    response = MagicMock()
    response.status_code = 200
    response.parsed = parsed
    return response


def _purchase_orders_response(attrs_pos: list) -> MagicMock:
    """Build a mock paginated response wrapping the given attrs purchase orders."""
    parsed = MagicMock()
    parsed.data = attrs_pos
    response = MagicMock()
    response.status_code = 200
    response.parsed = parsed
    return response


def _make_attrs_po(*, id: int, order_no: str) -> AttrsRegularPurchaseOrder:
    """Build a minimal attrs RegularPurchaseOrder the sync path can convert."""
    return AttrsRegularPurchaseOrder.from_dict(
        {
            "id": id,
            "order_no": order_no,
            "entity_type": "regular",
            "status": "NOT_RECEIVED",
            "supplier_id": 4001,
            "location_id": 1,
            "currency": "USD",
            "purchase_order_rows": [],
        }
    )


def _build_context(typed_cache_engine):
    """Mock context with a real typed_cache engine and a stub client.

    Mirrors the shape ``services.dependencies.get_services`` returns: tools
    read ``services.client``, ``services.typed_cache``. The client is a plain
    MagicMock because the API endpoints are patched at module level — none
    of the actual httpx layer is exercised in these tests.
    """
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.client = MagicMock()
    lifespan_ctx.typed_cache = typed_cache_engine
    return context


def _patch_purchase_order_api(po_response: MagicMock):
    """Patch the PO sync's two endpoints simultaneously."""
    return (
        patch(
            "katana_mcp.typed_cache.sync.find_purchase_orders.asyncio_detailed",
            new=AsyncMock(return_value=po_response),
        ),
        patch(
            "katana_mcp.typed_cache.sync.get_all_purchase_order_rows.asyncio_detailed",
            new=AsyncMock(return_value=_empty_paginated_response()),
        ),
    )


def _patch_sales_order_api():
    """Patch the SO sync's two endpoints to return empty results."""
    return (
        patch(
            "katana_mcp.typed_cache.sync.get_all_sales_orders.asyncio_detailed",
            new=AsyncMock(return_value=_empty_paginated_response()),
        ),
        patch(
            "katana_mcp.typed_cache.sync.get_all_sales_order_rows.asyncio_detailed",
            new=AsyncMock(return_value=_empty_paginated_response()),
        ),
    )


def _patch_manufacturing_order_api():
    """Patch the MO sync's two endpoints to return empty results.

    MO has a related-spec watermark for recipe rows fetched from a separate
    endpoint, so both must be patched.
    """
    return (
        patch(
            "katana_mcp.typed_cache.sync.get_all_manufacturing_orders.asyncio_detailed",
            new=AsyncMock(return_value=_empty_paginated_response()),
        ),
        patch(
            "katana_mcp.typed_cache.sync.get_all_manufacturing_order_recipe_rows.asyncio_detailed",
            new=AsyncMock(return_value=_empty_paginated_response()),
        ),
    )


def _patch_stock_adjustment_api():
    """Patch the stock_adjustment sync endpoint (no related rows endpoint)."""
    return patch(
        "katana_mcp.typed_cache.sync.get_all_stock_adjustments.asyncio_detailed",
        new=AsyncMock(return_value=_empty_paginated_response()),
    )


def _patch_stock_transfer_api():
    """Patch the stock_transfer sync endpoint (no related rows endpoint)."""
    return patch(
        "katana_mcp.typed_cache.sync.get_all_stock_transfers.asyncio_detailed",
        new=AsyncMock(return_value=_empty_paginated_response()),
    )


# ============================================================================
# Preview mode — must not modify cache or call the API
# ============================================================================


class TestPreview:
    @pytest.mark.asyncio
    async def test_preview_reports_counts_without_modifying_cache(
        self, typed_cache_engine
    ):
        """preview=True must read counts and last_synced without touching either."""
        await seed_cache(
            typed_cache_engine,
            [
                make_purchase_order(id=1, order_no="PO-001"),
                make_purchase_order(id=2, order_no="PO-002"),
            ],
        )
        async with typed_cache_engine.session() as session:
            session.add(
                SyncState(
                    entity_type="purchase_order",
                    last_synced=datetime(2026, 1, 1, 12, 0, 0),
                    row_count=2,
                )
            )
            await session.commit()

        context = _build_context(typed_cache_engine)

        # Patch API as a tripwire — preview must not invoke any sync.
        po_patch, row_patch = _patch_purchase_order_api(_empty_paginated_response())
        with po_patch as po_mock, row_patch as row_mock:
            response = await _rebuild_cache_impl(
                RebuildCacheRequest(entity_types=["purchase_order"], preview=True),
                context,
            )

            po_mock.assert_not_called()
            row_mock.assert_not_called()

        assert response.is_preview is True
        assert len(response.results) == 1
        result = response.results[0]
        assert result.entity_type == "purchase_order"
        assert result.parent_rows_before == 2
        assert result.parent_rows_after == 2  # unchanged
        assert result.last_synced_before == "2026-01-01T12:00:00"
        assert result.sync_state_keys_cleared == []

        # Cache rows survive the preview.
        async with typed_cache_engine.session() as session:
            cached = (await session.exec(select(CachedPurchaseOrder))).all()
            assert len(cached) == 2


# ============================================================================
# Apply mode — phantom cleanup is the headline behavior
# ============================================================================


class TestApplyPhantomCleanup:
    @pytest.mark.asyncio
    async def test_phantom_purchase_order_is_removed_after_rebuild(
        self, typed_cache_engine
    ):
        """The headline use case: a PO exists in the cache that Katana no longer
        has. After rebuild, the phantom is gone and the live PO remains."""
        await seed_cache(
            typed_cache_engine,
            [
                make_purchase_order(id=1, order_no="PO-LIVE"),
                make_purchase_order(id=999, order_no="PO-PHANTOM"),  # not in API
            ],
        )

        context = _build_context(typed_cache_engine)
        live_po_response = _purchase_orders_response(
            [_make_attrs_po(id=1, order_no="PO-LIVE")]
        )
        po_patch, row_patch = _patch_purchase_order_api(live_po_response)

        with po_patch, row_patch:
            response = await _rebuild_cache_impl(
                RebuildCacheRequest(entity_types=["purchase_order"], preview=False),
                context,
            )

        assert response.is_preview is False
        result = response.results[0]
        assert result.parent_rows_before == 2
        assert result.parent_rows_after == 1
        assert "purchase_order" in result.sync_state_keys_cleared
        assert "purchase_order_row" in result.sync_state_keys_cleared

        async with typed_cache_engine.session() as session:
            remaining = (await session.exec(select(CachedPurchaseOrder))).all()
        ids = {po.id for po in remaining}
        assert ids == {1}, f"Phantom PO 999 should be gone, got {ids}"

    @pytest.mark.asyncio
    async def test_child_rows_are_truncated_with_parents(self, typed_cache_engine):
        """Both parent and child cache tables clear before the re-pull —
        otherwise child rows could orphan against a freshly-empty parent table."""
        await seed_cache(
            typed_cache_engine,
            [
                make_purchase_order(id=1, order_no="PO-001"),
                make_purchase_order_row(id=10, purchase_order_id=1, variant_id=100),
                make_purchase_order_row(id=11, purchase_order_id=1, variant_id=101),
            ],
        )

        context = _build_context(typed_cache_engine)
        # API returns nothing — parent and child should both end empty.
        po_patch, row_patch = _patch_purchase_order_api(_empty_paginated_response())

        with po_patch, row_patch:
            await _rebuild_cache_impl(
                RebuildCacheRequest(entity_types=["purchase_order"], preview=False),
                context,
            )

        async with typed_cache_engine.session() as session:
            parents = (await session.exec(select(CachedPurchaseOrder))).all()
            children = (await session.exec(select(CachedPurchaseOrderRow))).all()
        assert parents == []
        assert children == []


# ============================================================================
# Watermark behavior — sync_state must be cleared and then repopulated by the re-pull
# ============================================================================


class TestWatermark:
    @pytest.mark.asyncio
    async def test_sync_state_is_repopulated_after_rebuild(self, typed_cache_engine):
        """``ensure_*_synced`` writes a fresh ``SyncState`` row at the end of
        the cold-start pull — so after rebuild, the watermark exists with a
        recent timestamp, not the stale one we started with."""
        async with typed_cache_engine.session() as session:
            session.add(
                SyncState(
                    entity_type="purchase_order",
                    last_synced=datetime(2020, 1, 1, 0, 0, 0),
                    row_count=999,
                )
            )
            await session.commit()

        context = _build_context(typed_cache_engine)
        po_patch, row_patch = _patch_purchase_order_api(_empty_paginated_response())

        before_call = datetime.now(tz=UTC).replace(tzinfo=None)
        with po_patch, row_patch:
            await _rebuild_cache_impl(
                RebuildCacheRequest(entity_types=["purchase_order"], preview=False),
                context,
            )

        async with typed_cache_engine.session() as session:
            state = await session.get(SyncState, "purchase_order")

        assert state is not None
        # New watermark, not the 2020 stale one.
        assert state.last_synced >= before_call


# ============================================================================
# Multi-entity rebuild — each entity processed sequentially
# ============================================================================


class TestMultiEntity:
    @pytest.mark.asyncio
    async def test_rebuild_purchase_orders_and_sales_orders_in_one_call(
        self, typed_cache_engine
    ):
        """Both entity types end up rebuilt independently."""
        await seed_cache(
            typed_cache_engine,
            [
                make_purchase_order(id=1, order_no="PO-001"),
                make_purchase_order(id=2, order_no="PO-002"),
                make_sales_order(id=10, order_no="SO-010"),
            ],
        )

        context = _build_context(typed_cache_engine)
        po_patch, po_row_patch = _patch_purchase_order_api(_empty_paginated_response())
        so_patch, so_row_patch = _patch_sales_order_api()

        with po_patch, po_row_patch, so_patch, so_row_patch:
            response = await _rebuild_cache_impl(
                RebuildCacheRequest(
                    entity_types=["purchase_order", "sales_order"], preview=False
                ),
                context,
            )

        assert len(response.results) == 2
        assert {r.entity_type for r in response.results} == {
            "purchase_order",
            "sales_order",
        }
        for result in response.results:
            assert result.parent_rows_after == 0  # API mocks return empty
            assert result.parent_rows_before > 0  # we seeded both

        async with typed_cache_engine.session() as session:
            assert (await session.exec(select(CachedPurchaseOrder))).all() == []
            assert (await session.exec(select(CachedSalesOrder))).all() == []


# ============================================================================
# Per-entity dispatch coverage — make sure ENTITY_SPECS wiring works for each
# of the 5 supported types, not just PO/SO. A typo on a less-trafficked entity
# would otherwise ship green.
# ============================================================================


class TestPerEntityDispatch:
    @pytest.mark.asyncio
    async def test_rebuild_manufacturing_order_clears_recipe_row_watermark(
        self, typed_cache_engine
    ):
        """MO carries a related-spec watermark for recipe rows that lives at a
        separate API endpoint. Both watermarks must be cleared."""
        await seed_cache(
            typed_cache_engine,
            [make_manufacturing_order(id=1, order_no="MO-001")],
        )
        async with typed_cache_engine.session() as session:
            for key in ("manufacturing_order", "manufacturing_order_recipe_row"):
                session.add(
                    SyncState(
                        entity_type=key,
                        last_synced=datetime(2020, 1, 1),
                        row_count=1,
                    )
                )
            await session.commit()

        context = _build_context(typed_cache_engine)
        mo_patch, recipe_patch = _patch_manufacturing_order_api()

        with mo_patch, recipe_patch:
            response = await _rebuild_cache_impl(
                RebuildCacheRequest(
                    entity_types=["manufacturing_order"], preview=False
                ),
                context,
            )

        result = response.results[0]
        assert set(result.sync_state_keys_cleared) == {
            "manufacturing_order",
            "manufacturing_order_recipe_row",
        }
        async with typed_cache_engine.session() as session:
            assert (await session.exec(select(CachedManufacturingOrder))).all() == []
            # Both watermarks freshly written by the cold-start re-pull.
            mo_state = await session.get(SyncState, "manufacturing_order")
            recipe_state = await session.get(
                SyncState, "manufacturing_order_recipe_row"
            )
        assert mo_state is not None and mo_state.last_synced > datetime(2020, 1, 1)
        assert recipe_state is not None and recipe_state.last_synced > datetime(
            2020, 1, 1
        )

    @pytest.mark.asyncio
    async def test_rebuild_stock_adjustment_with_no_related_specs(
        self, typed_cache_engine
    ):
        """stock_adjustment has nested child rows but no related-spec
        sibling endpoint — exercises the single-key dispatch path."""
        await seed_cache(
            typed_cache_engine,
            [make_stock_adjustment(id=1, stock_adjustment_number="SA-001")],
        )

        context = _build_context(typed_cache_engine)
        with _patch_stock_adjustment_api():
            response = await _rebuild_cache_impl(
                RebuildCacheRequest(entity_types=["stock_adjustment"], preview=False),
                context,
            )

        result = response.results[0]
        assert result.sync_state_keys_cleared == ["stock_adjustment"]
        assert result.parent_rows_before == 1
        assert result.parent_rows_after == 0
        async with typed_cache_engine.session() as session:
            assert (await session.exec(select(CachedStockAdjustment))).all() == []

    @pytest.mark.asyncio
    async def test_rebuild_stock_transfer_with_no_related_specs(
        self, typed_cache_engine
    ):
        """stock_transfer mirrors stock_adjustment's shape — single watermark,
        nested rows on the parent payload, no sibling row endpoint."""
        await seed_cache(
            typed_cache_engine,
            [make_stock_transfer(id=1, stock_transfer_number="ST-001")],
        )

        context = _build_context(typed_cache_engine)
        with _patch_stock_transfer_api():
            response = await _rebuild_cache_impl(
                RebuildCacheRequest(entity_types=["stock_transfer"], preview=False),
                context,
            )

        result = response.results[0]
        assert result.sync_state_keys_cleared == ["stock_transfer"]
        assert result.parent_rows_before == 1
        assert result.parent_rows_after == 0
        async with typed_cache_engine.session() as session:
            assert (await session.exec(select(CachedStockTransfer))).all() == []


# ============================================================================
# Atomicity — concurrent readers must never observe the empty intermediate
# state between truncate and re-pull. This is the headline guarantee
# ``force_resync`` exists to provide.
# ============================================================================


class TestForceResyncAtomicity:
    @pytest.mark.asyncio
    async def test_concurrent_reader_blocked_until_repull_completes(
        self, typed_cache_engine
    ):
        """A coroutine that takes the parent's sync lock concurrently with
        ``force_resync`` must block until the re-pull lands new rows.

        Models the ``list_*`` tool path: it calls ``ensure_*_synced`` (which
        takes the lock), then runs its SQL read. If ``force_resync`` released
        the lock between truncate and re-pull, the reader could acquire the
        lock during the empty window and see zero rows. Holding the lock
        across both phases prevents that — verified here by confirming the
        lock contention serializes the two operations.
        """
        await seed_cache(
            typed_cache_engine,
            [make_purchase_order(id=1, order_no="PO-INITIAL")],
        )

        events: list[str] = []
        repull_started = asyncio.Event()
        repull_can_finish = asyncio.Event()

        async def slow_api_call(**_kwargs):
            """Simulated API call that blocks until the test releases it,
            forcing the re-pull to span the lock window."""
            events.append("repull-fetch-started")
            repull_started.set()
            await repull_can_finish.wait()
            events.append("repull-fetch-finished")
            return _purchase_orders_response(
                [_make_attrs_po(id=1, order_no="PO-INITIAL")]
            )

        async def reader():
            """Acquire the same lock ``list_*`` would take during sync."""
            spec = ENTITY_SPECS["purchase_order"]
            await repull_started.wait()  # let the rebuild start first
            events.append("reader-waiting-for-lock")
            async with typed_cache_engine.lock_for(spec.entity_key):
                events.append("reader-acquired-lock")

        with (
            patch(
                "katana_mcp.typed_cache.sync.find_purchase_orders.asyncio_detailed",
                new=AsyncMock(side_effect=slow_api_call),
            ),
            patch(
                "katana_mcp.typed_cache.sync.get_all_purchase_order_rows.asyncio_detailed",
                new=AsyncMock(return_value=_empty_paginated_response()),
            ),
        ):
            rebuild_task = asyncio.create_task(
                force_resync(MagicMock(), typed_cache_engine, "purchase_order")
            )
            reader_task = asyncio.create_task(reader())

            # Confirm the reader is parked on the lock before the rebuild's
            # API call returns.
            await repull_started.wait()
            await asyncio.sleep(0)  # let reader run up to the lock
            assert "reader-waiting-for-lock" in events
            assert "reader-acquired-lock" not in events

            # Release the rebuild's API call. The rebuild finishes the
            # sync (still under lock), then releases. The reader proceeds.
            repull_can_finish.set()
            await asyncio.gather(rebuild_task, reader_task)

        # Order proves the lock held across both phases — the reader never
        # interleaved between truncate and re-pull.
        assert events == [
            "repull-fetch-started",
            "reader-waiting-for-lock",
            "repull-fetch-finished",
            "reader-acquired-lock",
        ]


# ============================================================================
# Request validation — invalid entity types fail at the request boundary
# ============================================================================


class TestRequestValidation:
    def test_unknown_entity_type_fails_pydantic_validation(self):
        """The Literal-typed ``entity_types`` field rejects unknown values."""
        with pytest.raises(ValueError):
            RebuildCacheRequest(entity_types=["not_a_real_entity"], preview=True)  # type: ignore[list-item]

    def test_empty_entity_types_fails_pydantic_validation(self):
        """``min_length=1`` blocks empty lists at construction time."""
        with pytest.raises(ValueError):
            RebuildCacheRequest(entity_types=[], preview=True)
