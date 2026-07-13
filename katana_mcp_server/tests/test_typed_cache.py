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
from datetime import datetime
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

    @pytest.mark.asyncio
    async def test_open_migrates_pre_671_variant_table_with_not_null_sku(
        self, tmp_path: Path
    ):
        """Pre-#671 caches had ``sku VARCHAR NOT NULL`` baked into the
        ``variant`` CREATE statement; the spec relaxation makes ``sku`` nullable,
        but ``SQLModel.metadata.create_all`` is a no-op on existing tables.
        ``open()`` must detect the stale DDL and rebuild the variant table so
        Katana's null-sku rows insert cleanly on subsequent sync.
        """
        import aiosqlite

        db_path = tmp_path / "stale.db"
        # Hand-craft a pre-#671 variant table with the old NOT NULL constraint.
        # Use aiosqlite (async) for the setup since the rest of the harness
        # is already async — no need to bring in a sync sqlite3 dependency
        # for one fixture.
        async with aiosqlite.connect(str(db_path)) as conn:
            await conn.execute(
                "CREATE TABLE variant (id INTEGER PRIMARY KEY, sku VARCHAR NOT NULL)"
            )
            await conn.execute("INSERT INTO variant (id, sku) VALUES (1, 'OLD-SKU')")
            await conn.commit()

        engine = TypedCacheEngine(db_path=db_path)
        await engine.open()
        try:
            # After open(), inserting a null-sku row must succeed — proves the
            # NOT NULL constraint is gone. The pre-existing 'OLD-SKU' row was
            # dropped along with the table; the cache is derivable from the API.
            from katana_public_api_client.models_pydantic._generated import (
                CachedVariant,
            )

            async with engine.session() as session:
                session.add(CachedVariant(id=42, sku=None))
                await session.commit()
                row = await session.get(CachedVariant, 42)
            assert row is not None
            assert row.sku is None
        finally:
            await engine.close()

    @pytest.mark.asyncio
    async def test_open_migration_is_noop_on_fresh_db(self, tmp_path: Path):
        """A fresh DB without a stale ``variant`` table reopens cleanly."""
        engine = TypedCacheEngine(db_path=tmp_path / "fresh.db")
        await engine.open()
        try:
            from katana_public_api_client.models_pydantic._generated import (
                CachedVariant,
            )

            async with engine.session() as session:
                session.add(CachedVariant(id=1, sku=None))
                await session.commit()
                row = await session.get(CachedVariant, 1)
            assert row is not None
            assert row.sku is None
        finally:
            await engine.close()

    @pytest.mark.asyncio
    async def test_open_rebuilds_pre_669_location_table_missing_deleted_at(
        self, tmp_path: Path
    ):
        """The headline #669 regression: pre-#669 ``CachedLocation`` extended
        ``KatanaPydanticBase``, so the SQLite ``location`` table had only the
        explicit columns (``id``, ``name``, ``legal_name``, ...). #669 promoted
        it to ``DeletableEntity``, adding ``created_at``, ``updated_at``, and
        ``deleted_at``. ``SQLModel.metadata.create_all`` is a no-op against
        existing tables, so an upgraded user keeps the narrow table — and the
        next ``list_locations`` call's ``WHERE deleted_at IS NULL`` blows up
        with ``sqlite3.OperationalError: no such column: location.deleted_at``.

        The schema-fingerprint backstop must catch this on open (no stored
        fingerprint + tables present → upgrade path → drop everything and
        rebuild). After ``open()``, the ``location`` table must have all the
        new columns, and the next ``list_locations`` query path must succeed.
        """
        import aiosqlite
        from sqlalchemy import text

        db_path = tmp_path / "pre_669.db"
        # Hand-craft a pre-#669 ``location`` table — the explicit columns
        # only, no ``DeletableEntity`` audit fields. This is byte-identical
        # to what an upgraded user has on disk.
        async with aiosqlite.connect(str(db_path)) as conn:
            await conn.execute(
                "CREATE TABLE location ("
                "id INTEGER PRIMARY KEY, "
                "name VARCHAR NOT NULL, "
                "legal_name VARCHAR"
                ")"
            )
            await conn.execute(
                "INSERT INTO location (id, name) VALUES (1, 'Old Warehouse')"
            )
            await conn.commit()

        engine = TypedCacheEngine(db_path=db_path)
        await engine.open()
        try:
            # Confirm the rebuild added the missing columns.
            async with engine.session() as session:
                conn = await session.connection()
                cols = (
                    await conn.execute(text("PRAGMA table_info(location)"))
                ).fetchall()
                col_names = {row[1] for row in cols}
            assert "deleted_at" in col_names, (
                f"deleted_at missing — fingerprint backstop failed to "
                f"rebuild. Columns: {col_names}"
            )
            assert "created_at" in col_names
            assert "updated_at" in col_names

            # The ``WHERE deleted_at IS NULL`` query path must now succeed
            # — this is the actual user-visible failure mode #669
            # introduced.
            from katana_public_api_client.models_pydantic._generated import (
                CachedLocation,
            )

            async with engine.session() as session:
                rows = (
                    await session.exec(
                        select(CachedLocation).where(
                            CachedLocation.deleted_at.is_(None)
                        )
                    )
                ).all()
            # Pre-existing 'Old Warehouse' row was dropped along with the
            # narrow table — cache is derivable from the API.
            assert rows == []
        finally:
            await engine.close()

    @pytest.mark.asyncio
    async def test_open_rebuild_drops_fts_sidecars_alongside_main_tables(
        self, tmp_path: Path
    ):
        """When the fingerprint backstop drops a content table, its FTS5
        sidecar + the trigger trio must drop too — otherwise the next
        ``CREATE TRIGGER`` would error on the leftover trigger and the
        FTS5 virtual table would reference a now-missing content table.

        Hand-build a stale variant table and a matching ``variant_fts``
        sidecar (mirroring what a pre-fingerprint engine would have left
        on disk), then confirm both get rebuilt.
        """
        import aiosqlite
        from sqlalchemy import text

        db_path = tmp_path / "stale_with_fts.db"
        async with aiosqlite.connect(str(db_path)) as conn:
            # Stale variant table (forces a fingerprint mismatch) +
            # matching FTS sidecar + one trigger to confirm cleanup.
            await conn.execute(
                "CREATE TABLE variant ("
                "id INTEGER PRIMARY KEY, sku VARCHAR, made_up_old_col VARCHAR"
                ")"
            )
            await conn.execute(
                "CREATE VIRTUAL TABLE variant_fts USING fts5("
                "sku, content='variant', content_rowid='id'"
                ")"
            )
            await conn.execute(
                "CREATE TRIGGER variant_ai AFTER INSERT ON variant BEGIN "
                "INSERT INTO variant_fts (rowid, sku) "
                "VALUES (new.id, IFNULL(new.sku, '')); END"
            )
            await conn.commit()

        engine = TypedCacheEngine(db_path=db_path)
        await engine.open()
        try:
            async with engine.session() as session:
                conn = await session.connection()
                # FTS sidecar exists.
                fts = (
                    await conn.execute(
                        text(
                            "SELECT name FROM sqlite_master "
                            "WHERE type='table' AND name='variant_fts'"
                        )
                    )
                ).first()
                # Trigger exists (recreated post-rebuild by FTS init).
                trigger = (
                    await conn.execute(
                        text(
                            "SELECT name FROM sqlite_master "
                            "WHERE type='trigger' AND name='variant_ai'"
                        )
                    )
                ).first()
                # The stale fictional column is gone — proves the variant
                # table was actually dropped + recreated, not just left in
                # place with a bonus FTS sidecar.
                cols = (
                    await conn.execute(text("PRAGMA table_info(variant)"))
                ).fetchall()
                col_names = {row[1] for row in cols}
            assert fts is not None
            assert trigger is not None
            assert "made_up_old_col" not in col_names
        finally:
            await engine.close()

    @pytest.mark.asyncio
    async def test_open_writes_fingerprint_to_cache_meta(self, tmp_path: Path):
        """First open of a fresh DB stamps a fingerprint row in ``cache_meta``."""
        from katana_mcp.typed_cache.schema_fingerprint import (
            CacheMeta,
            compute_metadata_fingerprint,
        )

        engine = TypedCacheEngine(db_path=tmp_path / "fresh.db")
        await engine.open()
        try:
            async with engine.session() as session:
                row = await session.get(CacheMeta, "schema_fingerprint")
            assert row is not None
            assert row.value == compute_metadata_fingerprint()
            # SHA-256 hex is exactly 64 chars — sanity check we're not
            # storing something pathological like the empty string.
            assert len(row.value) == 64
        finally:
            await engine.close()

    @pytest.mark.asyncio
    async def test_second_open_with_unchanged_metadata_is_a_noop(self, tmp_path: Path):
        """Reopen against an already-stamped DB must NOT rebuild — user
        rows survive across engine restarts unless the schema actually
        changed. This is the most important non-headline guarantee:
        without it, every server restart would clear the cache.
        """
        from katana_public_api_client.models_pydantic._generated import (
            CachedLocation,
        )

        db_path = tmp_path / "stable.db"

        # First open: stamps fingerprint + lays down schema. Seed a row.
        engine = TypedCacheEngine(db_path=db_path)
        await engine.open()
        try:
            async with engine.session() as session:
                session.add(CachedLocation(id=42, name="Survivor Warehouse"))
                await session.commit()
        finally:
            await engine.close()

        # Second open: fingerprint matches → no rebuild → row survives.
        engine = TypedCacheEngine(db_path=db_path)
        await engine.open()
        try:
            async with engine.session() as session:
                row = await session.get(CachedLocation, 42)
            assert row is not None, (
                "Cache row was wiped on a no-op reopen — the fingerprint "
                "backstop is rebuilding when it shouldn't be."
            )
            assert row.name == "Survivor Warehouse"
        finally:
            await engine.close()

    @pytest.mark.asyncio
    async def test_open_rebuilds_when_fingerprint_mismatch(self, tmp_path: Path):
        """Synthetic drift: write a wrong fingerprint to ``cache_meta``,
        seed a row, reopen — the row must be wiped (proves the mismatch
        path runs) and the new fingerprint must overwrite the wrong one.
        """
        from katana_mcp.typed_cache.schema_fingerprint import (
            CacheMeta,
            compute_metadata_fingerprint,
        )

        from katana_public_api_client.models_pydantic._generated import (
            CachedLocation,
        )

        db_path = tmp_path / "drifty.db"

        # First open lays down the schema + writes the correct fingerprint.
        engine = TypedCacheEngine(db_path=db_path)
        await engine.open()
        try:
            async with engine.session() as session:
                session.add(CachedLocation(id=1, name="Will Vanish"))
                # Replace the correct fingerprint with a synthetic wrong one.
                meta = await session.get(CacheMeta, "schema_fingerprint")
                assert meta is not None
                meta.value = "0" * 64
                session.add(meta)
                await session.commit()
        finally:
            await engine.close()

        # Second open: stored fingerprint != current → rebuild fires.
        engine = TypedCacheEngine(db_path=db_path)
        await engine.open()
        try:
            async with engine.session() as session:
                vanished = await session.get(CachedLocation, 1)
                meta = await session.get(CacheMeta, "schema_fingerprint")
            assert vanished is None, (
                "Row survived a fingerprint-mismatch open — rebuild didn't fire."
            )
            assert meta is not None
            assert meta.value == compute_metadata_fingerprint()
        finally:
            await engine.close()

    @pytest.mark.asyncio
    async def test_file_backed_engine_uses_wal_and_busy_timeout(self, tmp_path: Path):
        """File-backed engines apply WAL + busy_timeout PRAGMAs.

        Multiple MCP server processes (Claude Desktop + worktrees) share
        ``typed_cache.db``. Without WAL, a long-running reader blocks
        every writer; without ``busy_timeout`` the loser of a write
        contention raises ``database is locked`` immediately. Both must
        be applied on every checked-out connection.
        """
        from sqlalchemy import text

        engine = TypedCacheEngine(db_path=tmp_path / "test.db")
        await engine.open()
        try:
            async with engine.session() as session:
                conn = await session.connection()
                journal = (await conn.execute(text("PRAGMA journal_mode"))).scalar()
                busy = (await conn.execute(text("PRAGMA busy_timeout"))).scalar()
                synchronous = (await conn.execute(text("PRAGMA synchronous"))).scalar()
            assert journal == "wal"
            assert busy == 30000
            # synchronous=NORMAL is enum value 1.
            assert synchronous == 1
        finally:
            await engine.close()


class TestConcurrentProcessSharing:
    """#974: two engines sharing one cache dir must not deadlock on writes.

    The default cache path is a single machine-wide location, so every
    running ``katana-mcp-server`` opens the same SQLite file. Before the
    fix, concurrent writers could block on the write lock long enough for
    the MCP client to time a ``tools/call`` out. The engine now defends the
    shared file with WAL + a 30s ``busy_timeout`` and keeps write
    transactions scoped tightly around the DB writes, so contention
    degrades to a brief stall instead of a client-visible hang.
    """

    @pytest.mark.asyncio
    async def test_second_writer_waits_out_held_lock_instead_of_erroring(
        self, tmp_path: Path
    ):
        """A second writer waits out a *held* write lock, then lands.

        Simulates two server processes (a Claude Desktop connector + a Claude
        Code session) sharing ``typed_cache.db``. Rather than racing two quick
        commits (which can serialize and pass even without ``busy_timeout``),
        this forces genuine contention: engine A flushes an insert to acquire
        SQLite's write lock and holds the transaction open while engine B
        attempts its own write in a background task.

        While A holds the lock, B must *block* in its driver thread (waiting
        out ``busy_timeout``) rather than raise ``database is locked`` — proven
        by B being unable to complete within a short window. A holds the lock
        for the whole of that window by construction, so the check is
        deterministic, not timing-sensitive. Once A commits, B lands. With the
        default zero ``busy_timeout`` B would raise immediately instead of
        waiting, so this distinguishes the configured behavior from the default.
        """
        db_path = tmp_path / "shared.db"
        engine_a = TypedCacheEngine(db_path=db_path)
        engine_b = TypedCacheEngine(db_path=db_path)
        await engine_a.open()
        await engine_b.open()

        async def _b_write() -> None:
            async with engine_b.session() as session:
                session.add(
                    SyncState(
                        entity_type="purchase_order",
                        last_synced=datetime(2026, 1, 1, 12, 0, 0),
                        row_count=2,
                    )
                )
                await session.commit()

        task_b: asyncio.Task[None] | None = None
        try:
            async with engine_a.session() as session_a:
                session_a.add(
                    SyncState(
                        entity_type="sales_order",
                        last_synced=datetime(2026, 1, 1, 12, 0, 0),
                        row_count=1,
                    )
                )
                # Acquire the write lock (SQLite RESERVED) without committing.
                await session_a.flush()

                # B races for the same lock. While A holds it, B must block on
                # busy_timeout — it cannot finish, so shielding it from the
                # wait_for cancellation and expecting a timeout proves B is
                # waiting rather than erroring.
                task_b = asyncio.create_task(_b_write())
                with pytest.raises(asyncio.TimeoutError):
                    await asyncio.wait_for(asyncio.shield(task_b), timeout=0.5)
                assert not task_b.done()

                # Release the lock; B's pending write now proceeds.
                await session_a.commit()

            await asyncio.wait_for(task_b, timeout=30)

            # Both writes are durable and visible to a third reader.
            reader = TypedCacheEngine(db_path=db_path)
            await reader.open()
            try:
                async with reader.session() as session:
                    so = await session.get(SyncState, "sales_order")
                    po = await session.get(SyncState, "purchase_order")
                assert so is not None
                assert so.row_count == 1
                assert po is not None
                assert po.row_count == 2
            finally:
                await reader.close()
        finally:
            if task_b is not None and not task_b.done():
                task_b.cancel()
            await engine_a.close()
            await engine_b.close()


class TestCacheDirOverride:
    """#974: ``KATANA_CACHE_DIR`` isolates the cache to a chosen directory."""

    def test_default_path_uses_env_override_when_set(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """``KATANA_CACHE_DIR`` redirects the default DB path under that dir."""
        from katana_mcp.typed_cache.engine import _default_db_path

        # Arrange
        monkeypatch.setenv("KATANA_CACHE_DIR", str(tmp_path))

        # Act
        resolved = _default_db_path()

        # Assert
        assert resolved == tmp_path / "typed_cache.db"

    def test_blank_env_override_falls_back_to_shared_default(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        """An empty / whitespace ``KATANA_CACHE_DIR`` is ignored."""
        from katana_mcp.typed_cache.engine import _default_db_path

        # Arrange
        monkeypatch.setenv("KATANA_CACHE_DIR", "   ")

        # Act
        resolved = _default_db_path()

        # Assert: falls back to the platformdirs cache dir, not "   ".
        assert resolved.name == "typed_cache.db"
        assert "katana-mcp" in str(resolved)

    @pytest.mark.asyncio
    async def test_engine_default_honors_env_override(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """A default-constructed engine writes under ``KATANA_CACHE_DIR``."""
        # Arrange
        monkeypatch.setenv("KATANA_CACHE_DIR", str(tmp_path))
        engine = TypedCacheEngine()

        # Act
        assert engine.db_path == tmp_path / "typed_cache.db"
        await engine.open()

        # Assert: the file materialized under the override dir.
        try:
            assert (tmp_path / "typed_cache.db").exists()
        finally:
            await engine.close()


class TestSyncState:
    """SyncState upsert / read roundtrip."""

    @pytest.mark.asyncio
    async def test_sync_state_roundtrip(self, typed_cache_engine):
        # Fixed naive whole-second timestamp — no wall-clock read (this is a
        # round-trip test, not a timing test; see CLAUDE.md: time-based tests
        # must fake time). SQLite DateTime columns drop tzinfo and store naive
        # UTC, and a whole second round-trips with no sub-second truncation,
        # so we assert *exact* equality instead of a fuzzy tolerance.
        fixed = datetime(2026, 1, 1, 12, 0, 0)
        async with typed_cache_engine.session() as session:
            session.add(
                SyncState(entity_type="sales_order", last_synced=fixed, row_count=42)
            )
            await session.commit()

        async with typed_cache_engine.session() as session:
            fetched = await session.get(SyncState, "sales_order")
            assert fetched is not None
            assert fetched.entity_type == "sales_order"
            assert fetched.row_count == 42
            assert fetched.last_synced == fixed


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

    @pytest.mark.asyncio
    async def test_json_column_round_trips_pydantic_instances(self, typed_cache_engine):
        """Regression: JSON columns with nested pydantic models survive flush.

        ``CachedManufacturingOrder.serial_numbers`` is typed
        ``list[SerialNumber] | None`` and stored via ``Column(PydanticJSON)``.
        The ``model_dump → model_validate`` conversion round-trip re-creates
        real ``SerialNumber`` pydantic instances in the field.  Before the
        ``PydanticJSON`` fix, SQLAlchemy's stock ``JSON`` column called
        ``json.dumps`` on the field value at flush time and raised
        ``TypeError: Object of type SerialNumber is not JSON serializable``.

        This test writes a ``CachedManufacturingOrder`` with a non-empty
        ``serial_numbers`` list *directly via the SQLAlchemy session* (no MCP
        layer) and asserts the round-trip succeeds and the values are
        preserved.  This proves the cache classes are correct standalone —
        not just when MCP does the writing.
        """
        from katana_public_api_client.models_pydantic._generated import (
            CachedManufacturingOrder,
            ManufacturingOrderStatus,
        )
        from katana_public_api_client.models_pydantic._generated.stock import (
            SerialNumber,
        )

        serial_numbers = [
            SerialNumber(serial_number="SN-001"),
            SerialNumber(serial_number="SN-002"),
        ]

        async with typed_cache_engine.session() as session:
            session.add(
                CachedManufacturingOrder(
                    id=99,
                    order_no="MO-JSON-001",
                    status=ManufacturingOrderStatus.in_progress,
                    serial_numbers=serial_numbers,
                )
            )
            await session.commit()

        async with typed_cache_engine.session() as session:
            stmt = select(CachedManufacturingOrder).where(
                CachedManufacturingOrder.order_no == "MO-JSON-001"
            )
            result = await session.exec(stmt)
            mo = result.one()
            assert mo.serial_numbers is not None
            assert len(mo.serial_numbers) == 2
            # SQLAlchemy loads JSON columns as plain Python dicts via json.loads —
            # it never reconstructs pydantic models. The key assertion is that the
            # write succeeded (no TypeError) and data round-tripped faithfully.
            sn0 = mo.serial_numbers[0]
            assert isinstance(sn0, dict)
            assert sn0["serial_number"] == "SN-001"
            sn1 = mo.serial_numbers[1]
            assert isinstance(sn1, dict)
            assert sn1["serial_number"] == "SN-002"
            # Semantic round-trip: the read-back dict must validate cleanly back
            # into the source pydantic model. Catches ``model_dump`` / ``model_validate``
            # format drift (datetime serialization, enum representation, etc.) that
            # would surface only at consumer-side reconstruction.
            assert SerialNumber.model_validate(sn0) == serial_numbers[0]
            assert SerialNumber.model_validate(sn1) == serial_numbers[1]

    @pytest.mark.asyncio
    async def test_json_column_round_trips_empty_list(self, typed_cache_engine):
        """Edge case: empty list in a JSON column round-trips without error."""
        from katana_public_api_client.models_pydantic._generated import (
            CachedManufacturingOrder,
        )

        async with typed_cache_engine.session() as session:
            session.add(
                CachedManufacturingOrder(
                    id=100,
                    order_no="MO-EMPTY-001",
                    batch_transactions=[],
                )
            )
            await session.commit()

        async with typed_cache_engine.session() as session:
            stmt = select(CachedManufacturingOrder).where(
                CachedManufacturingOrder.order_no == "MO-EMPTY-001"
            )
            result = await session.exec(stmt)
            mo = result.one()
            assert mo.batch_transactions == []

    @pytest.mark.asyncio
    async def test_json_column_handles_nested_datetime_in_plain_dicts(
        self, typed_cache_engine
    ):
        """Regression (#659): JSON columns must serialize datetime values nested
        inside plain dicts/lists, not just live ``BaseModel`` instances.

        The user-reported crash on ``list_suppliers`` /
        ``list_sales_orders`` originates in the typed-cache write path.
        ``_convert`` runs ``api_obj.model_dump()`` (default
        ``mode="python"``) → ``cache_cls.model_validate(...)`` to build the
        cache row. ``_bulk_upsert`` then calls
        ``row.model_dump(include=column_names)`` (also default
        ``mode="python"``) for the INSERT VALUES. By the time SQLAlchemy
        binds the JSON-column parameter, the field can be a list of plain
        dicts whose leaves still hold live ``datetime`` instances
        (``SupplierAddress`` extends ``DeletableEntity`` so each entry
        carries ``created_at`` / ``updated_at`` columns). Stock
        ``json.dumps`` then crashes with
        ``TypeError: Object of type datetime is not JSON serializable``.

        This test reproduces the exact path: build the upstream pydantic
        ``Supplier``, run it through the same ``model_dump`` →
        ``model_validate`` → ``model_dump(include=cols)`` chain
        ``_convert`` + ``_bulk_upsert`` use, then INSERT and SELECT it.
        """
        from datetime import UTC, datetime

        from sqlalchemy import inspect as sqla_inspect
        from sqlalchemy.dialects.sqlite import insert as sqlite_insert

        from katana_public_api_client.models_pydantic._generated import (
            CachedSupplier,
            Supplier as PydanticSupplier,
        )
        from katana_public_api_client.models_pydantic._generated.contacts import (
            SupplierAddress,
        )

        # Frozen literal so the test is hermetic — any future value-equality
        # check stays reproducible, and failure output is stable across runs.
        now = datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)
        api_supplier = PydanticSupplier(
            id=42,
            name="Acme Supplies",
            updated_at=now,
            created_at=now,
            addresses=[
                SupplierAddress(
                    id=1,
                    supplier_id=42,
                    line_1="123 Main St",
                    city="Austin",
                    created_at=now,
                    updated_at=now,
                ),
            ],
        )
        # Mirror ``_convert``: model_dump → model_validate. After this,
        # ``cached.addresses`` is a list of plain dicts (not SupplierAddress
        # instances) because SQLModel's ``Mapped[list[X]]`` annotation
        # leaves the field shape as-dumped under default mode="python".
        cached = CachedSupplier.model_validate(api_supplier.model_dump())

        # Mirror ``_bulk_upsert``: include=column_names + dialect insert.
        mapper = sqla_inspect(CachedSupplier)
        column_names = {col.name for col in mapper.columns}
        values = [cached.model_dump(include=column_names)]
        stmt = sqlite_insert(CachedSupplier).values(values)
        async with typed_cache_engine.session() as session:
            await session.exec(stmt)
            await session.commit()

        async with typed_cache_engine.session() as session:
            stmt2 = select(CachedSupplier).where(CachedSupplier.id == 42)
            result = await session.exec(stmt2)
            fetched = result.one()
            assert fetched.addresses is not None
            assert len(fetched.addresses) == 1
            addr = fetched.addresses[0]
            assert isinstance(addr, dict)
            assert addr["line_1"] == "123 Main St"
            # The datetime survived the JSON round-trip as an ISO-8601 string,
            # not as a live ``datetime`` (json.loads doesn't reconstruct
            # datetimes). Both ``created_at`` and ``updated_at`` should be
            # present and string-shaped.
            assert isinstance(addr["created_at"], str)
            assert isinstance(addr["updated_at"], str)

    @pytest.mark.asyncio
    async def test_mo_serial_numbers_datetime_round_trip_via_bulk_upsert(
        self, typed_cache_engine
    ):
        """Regression (#632): ``list_manufacturing_orders`` triggered
        ``Object of type datetime is not JSON serializable`` during
        ``_bulk_upsert`` whenever an MO in the fetched page carried a
        ``SerialNumber`` with a populated ``transaction_date``.

        ``CachedManufacturingOrder.serial_numbers: list[SerialNumber] |
        None`` is a ``Column(PydanticJSON)`` column, and ``SerialNumber``
        has a ``transaction_date: AwareDatetime | None`` field. The full
        production path is:

        1. ``_convert`` runs ``api_obj.model_dump()`` (mode="python") →
           the nested SerialNumber becomes a plain dict whose
           ``transaction_date`` leaf is a live ``datetime``.
        2. ``cache_cls.model_validate(parent_data)`` reconstructs real
           ``SerialNumber`` instances on the cache row (``Mapped`` is an
           identity shim at runtime, so the effective field type is
           ``list[SerialNumber] | None`` and pydantic happily parses the
           dicts back). The ``transaction_date`` stays a live ``datetime``.
        3. ``_bulk_upsert`` calls ``row.model_dump(include=column_names)``
           (also mode="python"). The nested SerialNumbers are flattened
           back to dicts; ``transaction_date`` remains a live ``datetime``
           on the leaf. The list-of-dicts is then handed to
           ``sqlite_insert(...).values(values)``.
        4. SQLAlchemy binds the ``serial_numbers`` value to the
           ``PydanticJSON`` column, which (post #659 / commit 1174c34c)
           routes through ``to_jsonable_python`` and produces a JSON-safe
           value before the stock ``json.dumps`` runs.

        The fix landed in the client; this test pins the MO case
        explicitly so the parallel CachedSupplier coverage above doesn't
        accidentally regress only for MO-shape rows. The two tests are
        kept separate rather than parametrized — distinct import paths
        and field shapes (SupplierAddress vs SerialNumber) make a shared
        fixture noisier than the duplication it would remove.
        """
        from datetime import UTC, datetime

        from sqlalchemy import inspect as sqla_inspect
        from sqlalchemy.dialects.sqlite import insert as sqlite_insert

        from katana_public_api_client.models_pydantic._generated import (
            CachedManufacturingOrder,
            ManufacturingOrder as PydanticManufacturingOrder,
            ManufacturingOrderStatus,
        )
        from katana_public_api_client.models_pydantic._generated.stock import (
            SerialNumber,
        )

        # Frozen literal so the test is hermetic. ``id`` and ``order_no``
        # carry the SO ref + issue number from the #632 crash report as a
        # breadcrumb back to the originating session.
        now = datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)
        api_mo = PydanticManufacturingOrder(
            id=44256191,
            order_no="MFG-#632",
            status=ManufacturingOrderStatus.in_progress,
            order_created_date=now,
            serial_numbers=[
                SerialNumber(
                    id=1,
                    serial_number="SN-001",
                    transaction_date=now,
                    quantity_change=1,
                ),
            ],
        )

        # Mirror ``_convert``: model_dump → model_validate on the cache class.
        cached = CachedManufacturingOrder.model_validate(api_mo.model_dump())

        # Mirror ``_bulk_upsert``: include=column_names + dialect insert.
        # ``_bulk_upsert`` also appends ``on_conflict_do_update`` for the
        # upsert semantics, but the regression target is the bind-param
        # path that runs before the conflict clause is even evaluated, so
        # a plain INSERT is sufficient to exercise it.
        mapper = sqla_inspect(CachedManufacturingOrder)
        column_names = {col.name for col in mapper.columns}
        values = [cached.model_dump(include=column_names)]
        stmt = sqlite_insert(CachedManufacturingOrder).values(values)
        async with typed_cache_engine.session() as session:
            # Pre-fix: this raised ``TypeError: Object of type datetime is
            # not JSON serializable`` and killed the whole 30-row page.
            await session.exec(stmt)
            await session.commit()

        async with typed_cache_engine.session() as session:
            stmt2 = select(CachedManufacturingOrder).where(
                CachedManufacturingOrder.id == 44256191
            )
            result = await session.exec(stmt2)
            fetched = result.one()
            assert fetched.serial_numbers is not None
            assert len(fetched.serial_numbers) == 1
            sn = fetched.serial_numbers[0]
            assert isinstance(sn, dict)
            assert sn["serial_number"] == "SN-001"
            # ``transaction_date`` survives the JSON round-trip as an
            # ISO-8601 string (json.loads doesn't reconstruct datetimes).
            assert isinstance(sn["transaction_date"], str)

    def test_pydantic_json_serializes_plain_dict_with_datetime(self):
        """Unit-level regression (#659): PydanticJSON's ``process_bind_param``
        must JSON-serialize plain dicts/lists whose leaves contain live
        ``datetime`` values.

        The pre-fix encoder only handled ``BaseModel`` instances and
        ``list[BaseModel]``. A plain ``dict`` or ``list[dict]`` containing
        datetimes (the shape ``model_dump(mode='python')`` produces) fell
        through unchanged and crashed at ``json.dumps`` time.
        """
        import json
        from datetime import UTC, datetime

        from katana_public_api_client.models_pydantic._pydantic_json import (
            PydanticJSON,
        )

        encoder = PydanticJSON()

        # A list of plain dicts with live datetime leaves — exactly the
        # shape produced by ``CachedSupplier.model_dump(...)`` for the
        # ``addresses`` field.
        now = datetime.now(tz=UTC)
        value = [{"id": 1, "line_1": "123 Main", "updated_at": now}]
        encoded = encoder.process_bind_param(value, dialect=None)

        # The encoder's output must be plain-JSON-serializable.
        encoded_str = json.dumps(encoded)

        # And the datetime survived as an ISO-8601 string in the encoded
        # payload. Round-trip through json.loads to get a fresh, fully-typed
        # ``list[dict[str, Any]]`` view that ty can reason about (the
        # ``encoded`` value out of ``process_bind_param`` is typed ``object``
        # by SQLAlchemy's TypeDecorator base class).
        round_trip = json.loads(encoded_str)
        assert isinstance(round_trip, list)
        first = round_trip[0]
        assert isinstance(first, dict)
        assert isinstance(first["updated_at"], str)

    def test_pydantic_json_passes_through_none(self):
        """``None`` short-circuits to ``None`` so SQLAlchemy stores SQL NULL."""
        from katana_public_api_client.models_pydantic._pydantic_json import (
            PydanticJSON,
        )

        assert PydanticJSON().process_bind_param(None, dialect=None) is None


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
        """``from_attrs`` must produce ``shipping_fee=None`` when attrs
        shipping_fee originated as ``{}`` on the wire (#509)."""
        from katana_public_api_client.models import SalesOrder as AttrsSalesOrder
        from katana_public_api_client.models_pydantic._generated import (
            SalesOrder as PydanticSalesOrder,
        )

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
        assert attrs_so.shipping_fee is None
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

        # SO sync fans out to ``/sales_order_rows`` via ``related_specs``,
        # so stub that endpoint with an empty response — this test pins
        # the parent's shipping_fee handling, not row sync.
        empty_rows_parsed = MagicMock()
        empty_rows_parsed.data = []
        empty_rows_response = MagicMock()
        empty_rows_response.status_code = 200
        empty_rows_response.parsed = empty_rows_parsed

        with (
            patch(
                "katana_mcp.typed_cache.sync.get_all_sales_orders.asyncio_detailed",
                new=AsyncMock(return_value=mock_response),
            ),
            patch(
                "katana_mcp.typed_cache.sync.get_all_sales_order_rows.asyncio_detailed",
                new=AsyncMock(return_value=empty_rows_response),
            ),
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
