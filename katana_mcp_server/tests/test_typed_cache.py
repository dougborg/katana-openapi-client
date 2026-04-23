"""Tests for the #342 SQLModel-backed typed cache.

Covers the runtime lifecycle (open/close/session/lock), SyncState
roundtrip, and end-to-end cache interaction with the generated
SalesOrder/SalesOrderRow tables.
"""

from __future__ import annotations

import asyncio
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import pytest
import pytest_asyncio
from katana_mcp.typed_cache import SyncState, TypedCacheEngine
from sqlmodel import select


@pytest_asyncio.fixture
async def open_engine():
    """Yield a TypedCacheEngine backed by a temporary SQLite file."""
    with tempfile.TemporaryDirectory() as td:
        engine = TypedCacheEngine(db_path=Path(td) / "test.db")
        await engine.open()
        try:
            yield engine
        finally:
            await engine.close()


class TestLifecycle:
    """Engine open/close and session behavior."""

    @pytest.mark.asyncio
    async def test_open_creates_db_file(self):
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "test.db"
            engine = TypedCacheEngine(db_path=db_path)
            assert not db_path.exists()
            await engine.open()
            try:
                assert db_path.exists()
            finally:
                await engine.close()

    @pytest.mark.asyncio
    async def test_double_open_raises(self):
        with tempfile.TemporaryDirectory() as td:
            engine = TypedCacheEngine(db_path=Path(td) / "test.db")
            await engine.open()
            try:
                with pytest.raises(RuntimeError, match="already-open"):
                    await engine.open()
            finally:
                await engine.close()

    @pytest.mark.asyncio
    async def test_session_before_open_raises(self):
        engine = TypedCacheEngine(db_path=Path("/tmp/never-created.db"))
        with pytest.raises(RuntimeError, match="not open"):
            engine.session()

    @pytest.mark.asyncio
    async def test_close_is_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            engine = TypedCacheEngine(db_path=Path(td) / "test.db")
            await engine.open()
            await engine.close()
            # Second close must not raise.
            await engine.close()


class TestSyncState:
    """SyncState upsert / read roundtrip."""

    @pytest.mark.asyncio
    async def test_sync_state_roundtrip(self, open_engine):
        # SQLite DateTime columns don't preserve tzinfo by default — values
        # round-trip as naive UTC. Using a naive UTC datetime here avoids a
        # comparison mismatch and matches how the sync helpers already
        # work with SyncState under the hood.
        now = datetime.now(tz=UTC).replace(tzinfo=None)
        async with open_engine.session() as session:
            session.add(
                SyncState(entity_type="sales_order", last_synced=now, row_count=42)
            )
            await session.commit()

        async with open_engine.session() as session:
            fetched = await session.get(SyncState, "sales_order")
            assert fetched is not None
            assert fetched.entity_type == "sales_order"
            assert fetched.row_count == 42
            assert abs((fetched.last_synced - now).total_seconds()) < 1


class TestCacheTables:
    """Generated cache-target tables are available on the engine."""

    @pytest.mark.asyncio
    async def test_can_insert_and_query_sales_order(self, open_engine):
        """End-to-end: insert a SalesOrder + SalesOrderRow, traverse the
        relationship, query back. Proves the generator-emitted schema is
        live against the engine's SQLModel.metadata.create_all call."""
        from katana_public_api_client.models_pydantic._generated import (
            SalesOrder,
            SalesOrderRow,
            SalesOrderStatus,
        )

        async with open_engine.session() as session:
            session.add(
                SalesOrder(
                    id=1,
                    customer_id=42,
                    location_id=1,
                    order_no="SO-INT-001",
                    status=SalesOrderStatus.not_shipped,
                )
            )
            session.add(
                SalesOrderRow(id=1, sales_order_id=1, variant_id=100, quantity=2.0)
            )
            await session.commit()

        async with open_engine.session() as session:
            stmt = select(SalesOrder).where(SalesOrder.order_no == "SO-INT-001")
            result = await session.exec(stmt)
            order = result.one()
            assert order.customer_id == 42
            # Relationship resolves when explicitly refreshed.
            await session.refresh(order, attribute_names=["sales_order_rows"])
            assert len(order.sales_order_rows) == 1
            assert order.sales_order_rows[0].variant_id == 100


class TestLocks:
    """Per-entity asyncio.Lock registry."""

    @pytest.mark.asyncio
    async def test_same_entity_returns_same_lock(self, open_engine):
        a = open_engine.lock_for("sales_order")
        b = open_engine.lock_for("sales_order")
        assert a is b

    @pytest.mark.asyncio
    async def test_different_entities_distinct_locks(self, open_engine):
        a = open_engine.lock_for("sales_order")
        b = open_engine.lock_for("manufacturing_order")
        assert a is not b

    @pytest.mark.asyncio
    async def test_lock_serializes_concurrent_holders(self, open_engine):
        """Two coroutines contending on one lock acquire it sequentially,
        not simultaneously — the critical-section invariant sync helpers
        rely on."""
        lock = open_engine.lock_for("sales_order")
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
