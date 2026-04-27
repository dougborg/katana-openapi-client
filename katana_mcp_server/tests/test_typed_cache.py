"""Tests for the #342 SQLModel-backed typed cache.

Covers the runtime lifecycle (open/close/session/lock), SyncState
roundtrip, and end-to-end cache interaction with the generated
SalesOrder/SalesOrderRow tables.

Most tests use the shared ``typed_cache_engine`` fixture (in-memory
SQLite, ``StaticPool``). Tests that specifically exercise file-backed
behavior (``test_open_creates_db_file``) use ``tmp_path`` directly.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path

import pytest
from katana_mcp.typed_cache import SyncState, TypedCacheEngine
from sqlmodel import select


class TestLifecycle:
    """Engine open/close and session behavior."""

    @pytest.mark.asyncio
    async def test_open_creates_db_file(self, tmp_path: Path):
        """Regression: file-backed engines materialize the SQLite file."""
        db_path = tmp_path / "test.db"
        engine = TypedCacheEngine(db_path=db_path)
        assert not db_path.exists()
        await engine.open()
        try:
            assert db_path.exists()
        finally:
            await engine.close()

    @pytest.mark.asyncio
    async def test_open_in_memory_skips_file(self, tmp_path: Path):
        """``in_memory=True`` creates no file and reports ``db_path is None``."""
        engine = TypedCacheEngine(in_memory=True)
        assert engine.db_path is None
        await engine.open()
        try:
            # Nothing landed in tmp_path (the canonical "no filesystem" check).
            assert list(tmp_path.iterdir()) == []
        finally:
            await engine.close()

    @pytest.mark.asyncio
    async def test_in_memory_rejects_explicit_db_path(self):
        """Mixing ``in_memory=True`` with ``db_path`` is a user error."""
        with pytest.raises(ValueError, match="Pass either"):
            TypedCacheEngine(db_path=Path("/tmp/anything.db"), in_memory=True)

    @pytest.mark.asyncio
    async def test_double_open_raises(self, typed_cache_engine):
        with pytest.raises(RuntimeError, match="already-open"):
            await typed_cache_engine.open()

    @pytest.mark.asyncio
    async def test_session_before_open_raises(self):
        engine = TypedCacheEngine(in_memory=True)
        with pytest.raises(RuntimeError, match="not open"):
            engine.session()

    @pytest.mark.asyncio
    async def test_close_is_idempotent(self):
        engine = TypedCacheEngine(in_memory=True)
        await engine.open()
        await engine.close()
        # Second close must not raise.
        await engine.close()


class TestSyncState:
    """SyncState upsert / read roundtrip."""

    @pytest.mark.asyncio
    async def test_sync_state_roundtrip(self, typed_cache_engine):
        # SQLite DateTime columns don't preserve tzinfo by default — values
        # round-trip as naive UTC. Using a naive UTC datetime here avoids a
        # comparison mismatch and matches how the sync helpers already
        # work with SyncState under the hood.
        now = datetime.now(tz=UTC).replace(tzinfo=None)
        async with typed_cache_engine.session() as session:
            session.add(
                SyncState(entity_type="sales_order", last_synced=now, row_count=42)
            )
            await session.commit()

        async with typed_cache_engine.session() as session:
            fetched = await session.get(SyncState, "sales_order")
            assert fetched is not None
            assert fetched.entity_type == "sales_order"
            assert fetched.row_count == 42
            assert abs((fetched.last_synced - now).total_seconds()) < 1


class TestCacheTables:
    """Generated cache-target tables are available on the engine."""

    @pytest.mark.asyncio
    async def test_can_insert_and_query_sales_order(self, typed_cache_engine):
        """End-to-end: insert a CachedSalesOrder + CachedSalesOrderRow,
        traverse the relationship, query back. Proves the generator-emitted
        schema is live against the engine's SQLModel.metadata.create_all call."""
        from katana_public_api_client.models_pydantic._generated import (
            CachedSalesOrder,
            CachedSalesOrderRow,
            SalesOrderStatus,
        )

        async with typed_cache_engine.session() as session:
            session.add(
                CachedSalesOrder(
                    id=1,
                    customer_id=42,
                    location_id=1,
                    order_no="SO-INT-001",
                    status=SalesOrderStatus.not_shipped,
                )
            )
            session.add(
                CachedSalesOrderRow(
                    id=1, sales_order_id=1, variant_id=100, quantity=2.0
                )
            )
            await session.commit()

        async with typed_cache_engine.session() as session:
            stmt = select(CachedSalesOrder).where(
                CachedSalesOrder.order_no == "SO-INT-001"
            )
            result = await session.exec(stmt)
            order = result.one()
            assert order.customer_id == 42
            # Relationship resolves when explicitly refreshed.
            await session.refresh(order, attribute_names=["sales_order_rows"])
            assert len(order.sales_order_rows) == 1
            assert order.sales_order_rows[0].variant_id == 100


class TestSyncShippingFeeEmpty:
    """Regression tests for shipping_fee: {} Katana quirk.

    Katana returns ``shipping_fee: {}`` (empty object) instead of ``null``
    when a sales order has no shipping fee. Our attrs parser can't populate
    the required inner fields, so it falls back to returning the raw ``{}``
    dict. The ``from_attrs`` converter in ``_base.py`` must normalise that
    empty dict to ``None`` before handing data to pydantic validation — if
    it doesn't, validation raises three ``Field required`` errors and the
    whole cache sync transaction is rolled back.
    """

    def test_attrs_sales_order_with_empty_shipping_fee_converts(self):
        """``from_attrs`` must not raise when attrs shipping_fee is ``{}``."""
        from katana_public_api_client.models import SalesOrder as AttrsSalesOrder
        from katana_public_api_client.models_pydantic._generated import (
            SalesOrder as PydanticSalesOrder,
        )

        # Simulate the wire shape Katana sends for a no-fee order. The attrs
        # parser can't populate required inner fields from {}, catches the
        # KeyError, and falls back to storing the raw {} dict.
        attrs_so = AttrsSalesOrder.from_dict(
            {
                "id": 9001,
                "customer_id": 42,
                "order_no": "SO-FEE-TEST",
                "location_id": 1,
                "status": "NOT_SHIPPED",
                "shipping_fee": {},
            }
        )

        # This must not raise pydantic ValidationError.
        pydantic_so = PydanticSalesOrder.from_attrs(attrs_so)
        assert pydantic_so.shipping_fee is None

    @pytest.mark.asyncio
    async def test_ensure_sales_orders_synced_with_empty_shipping_fee(
        self, typed_cache_engine
    ):
        """Full sync path: ``ensure_sales_orders_synced`` must succeed and
        populate the cache when the API returns an order with
        ``shipping_fee: {}``.
        """
        from unittest.mock import AsyncMock, MagicMock, patch

        from katana_mcp.typed_cache.sync import ensure_sales_orders_synced
        from sqlmodel import select

        from katana_public_api_client.models import SalesOrder as AttrsSalesOrder
        from katana_public_api_client.models_pydantic._generated import CachedSalesOrder

        # Build the attrs order that the paginated API would return.
        attrs_so = AttrsSalesOrder.from_dict(
            {
                "id": 9001,
                "customer_id": 42,
                "order_no": "SO-FEE-SYNC",
                "location_id": 1,
                "status": "NOT_SHIPPED",
                "shipping_fee": {},
            }
        )

        # Build a minimal mock response that satisfies unwrap_data(response).
        mock_parsed = MagicMock()
        mock_parsed.data = [attrs_so]
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.parsed = mock_parsed

        mock_client = MagicMock()

        with patch(
            "katana_mcp.typed_cache.sync.get_all_sales_orders.asyncio_detailed",
            new=AsyncMock(return_value=mock_response),
        ):
            # Should complete without raising.
            await ensure_sales_orders_synced(
                client=mock_client, cache=typed_cache_engine
            )

        # The order must be in the cache.
        async with typed_cache_engine.session() as session:
            stmt = select(CachedSalesOrder).where(CachedSalesOrder.id == 9001)
            result = await session.exec(stmt)
            cached = result.one()
            assert cached.order_no == "SO-FEE-SYNC"
            assert cached.shipping_fee is None


class TestLocks:
    """Per-entity asyncio.Lock registry."""

    @pytest.mark.asyncio
    async def test_same_entity_returns_same_lock(self, typed_cache_engine):
        a = typed_cache_engine.lock_for("sales_order")
        b = typed_cache_engine.lock_for("sales_order")
        assert a is b

    @pytest.mark.asyncio
    async def test_different_entities_distinct_locks(self, typed_cache_engine):
        a = typed_cache_engine.lock_for("sales_order")
        b = typed_cache_engine.lock_for("manufacturing_order")
        assert a is not b

    @pytest.mark.asyncio
    async def test_lock_serializes_concurrent_holders(self, typed_cache_engine):
        """Two coroutines contending on one lock acquire it sequentially,
        not simultaneously — the critical-section invariant sync helpers
        rely on."""
        lock = typed_cache_engine.lock_for("sales_order")
        order: list[str] = []

        async def hold(label: str) -> None:
            async with lock:
                order.append(f"enter-{label}")
                await asyncio.sleep(0.01)
                order.append(f"exit-{label}")

        # asyncio.gather drives them concurrently; the lock enforces
        # sequential execution of the critical section.
        await asyncio.gather(hold("A"), hold("B"))
        # One must fully enter/exit before the other enters.
        assert order[0].startswith("enter-")
        assert order[1].startswith("exit-")
        assert order[2].startswith("enter-")
        assert order[3].startswith("exit-")
