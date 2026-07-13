"""Async SQLAlchemy engine + SQLModel metadata manager for the #342 cache.

Owns the SQLite file, applies the generated schema on ``open()``, and
vends async sessions + per-entity asyncio.Locks that protect cold-start
sync fan-out (two concurrent tool calls must not each kick off a full
fetch).
"""

from __future__ import annotations

import asyncio
import os
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Any

from platformdirs import user_cache_dir
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

# Side-effect imports: register table=True SQLModel classes with
# ``SQLModel.metadata`` so ``create_all`` emits their DDL. Add new
# entity modules here as they come online.
from katana_mcp.typed_cache import (
    schema_fingerprint as _schema_fingerprint_mod,
    sync_state as _sync_state_mod,
)
from katana_public_api_client.models_pydantic._generated import (
    common as _common_mod,
    contacts as _contacts_mod,
    inventory as _inventory_mod,
    manufacturing as _manufacturing_mod,
    purchase_orders as _purchase_orders_mod,
    sales_orders as _sales_orders_mod,
    stock as _stock_mod,
)

# ``stock`` already covers StockTransfer (sibling to StockAdjustment in the
# same generated module), so no extra side-effect import is needed.
# ``inventory`` registers Cached{Variant,Product,Material,Service};
# ``contacts`` registers Cached{Customer,Supplier};
# ``common`` registers Cached{Location,TaxRate,Operator,Factory,AdditionalCost}.
assert _sync_state_mod is not None
assert _schema_fingerprint_mod is not None
assert _sales_orders_mod is not None
assert _stock_mod is not None
assert _manufacturing_mod is not None
assert _purchase_orders_mod is not None
assert _inventory_mod is not None
assert _contacts_mod is not None
assert _common_mod is not None

_CACHE_DIR_ENV = "KATANA_CACHE_DIR"
_DB_FILENAME = "typed_cache.db"


def _default_db_path() -> Path:
    """Resolve the default SQLite cache path, honoring ``KATANA_CACHE_DIR``.

    By default the cache lives at one machine-wide location
    (``platformdirs.user_cache_dir("katana-mcp")/typed_cache.db``), which is
    intentional: a **shared** cache stays warm across every checkout,
    worktree, and connector, so a fresh server process reuses an already-
    synced DB instead of paying the cold-sync cost (Katana meters ~60 req/min
    per API key — see the typed-cache README). The shared file is made
    concurrency-safe via WAL + a generous ``busy_timeout`` (see
    ``_apply_sqlite_pragmas``) so multiple server processes don't deadlock on
    the write lock.

    ``KATANA_CACHE_DIR`` is the hard-isolation escape hatch (#974): point a
    connector / session at its own directory when you deliberately want a
    separate DB — e.g. an ``erp-dev`` connector that must not share state with
    prod. Resolved at call time (not import time) so tests and per-process
    env overrides take effect. An empty / whitespace value is ignored and
    falls back to the shared default. A leading ``~`` is expanded to the user
    home so ``KATANA_CACHE_DIR=~/katana-cache-dev`` behaves like a typical path
    override instead of creating a literal ``~`` directory under the CWD.
    """
    override = os.environ.get(_CACHE_DIR_ENV, "").strip()
    base = (
        Path(override).expanduser() if override else Path(user_cache_dir("katana-mcp"))
    )
    return base / _DB_FILENAME


def _migrate_pre_create_all(sync_conn: Any) -> None:
    """One-shot DDL migrations to run before ``SQLModel.metadata.create_all``.

    ``create_all`` only emits ``CREATE TABLE IF NOT EXISTS``, so it can't
    alter an existing table's column constraints. Whenever a generator-
    driven schema change relaxes a column (e.g., ``NOT NULL`` → nullable)
    or otherwise changes existing DDL, the matching cache rebuild belongs
    here: read the live DDL via ``sqlite_master`` and drop the table when
    it's stale, then ``create_all`` rebuilds it with the current
    generator output and the next entity sync repopulates from the API.

    Each migration block is keyed on a substring of the *stale* DDL so
    re-running ``open()`` against an already-migrated DB is a fast no-op
    (the substring won't match).
    """
    from sqlalchemy import text

    def _table_ddl(name: str) -> str | None:
        row = sync_conn.execute(
            text("SELECT sql FROM sqlite_master WHERE type='table' AND name=:n"),
            {"n": name},
        ).first()
        return row[0] if row else None

    # #671: ``Variant.sku`` was relaxed from required-non-null ``str`` to
    # nullable ``str | None`` to match Katana's wire reality (variants can
    # be created without a SKU; legacy NetSuite imports are a common
    # source). Pre-#671 installations have ``sku VARCHAR NOT NULL`` baked
    # into the CREATE statement, which rejects the null-sku rows Katana
    # legitimately emits. Drop on mismatch so ``create_all`` rebuilds with
    # the nullable column; the FTS sidecar gets rebuilt alongside in the
    # ``initialize_fts_for_connection`` step downstream.
    variant_ddl = _table_ddl("variant")
    if variant_ddl is not None and "sku VARCHAR NOT NULL" in variant_ddl:
        sync_conn.execute(text("DROP TABLE IF EXISTS variant_fts"))
        sync_conn.execute(text("DROP TABLE IF EXISTS variant"))


def _apply_sqlite_pragmas(dbapi_conn: sqlite3.Connection, _record: object) -> None:
    """Per-connection PRAGMAs for the file-backed typed cache.

    Multiple MCP server processes (Claude Desktop + worktrees) share the
    same SQLite file (#974). WAL lets concurrent readers coexist with a
    writer; ``busy_timeout`` makes a contended writer wait instead of
    failing immediately with ``database is locked``; ``synchronous=NORMAL``
    is the standard pairing with WAL. Registered via ``event.listen`` on
    the file-backed engine so every checked-out connection has them.

    ``busy_timeout`` is 30s: a cold sync writes the cache in many short
    transactions (the ``_sync_one_locked`` write blocks are scoped tightly
    around the DB writes, *not* the network fetch), so a contended writer
    only ever waits out another process's brief commit, not a full sync.
    The generous ceiling means transient contention degrades to a short
    stall well within the MCP client's call timeout instead of surfacing
    as a ``database is locked`` error or a client-visible ``tools/call``
    hang.
    """
    cursor = dbapi_conn.cursor()
    try:
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.execute("PRAGMA synchronous=NORMAL")
    finally:
        cursor.close()


class TypedCacheEngine:
    """Owns the async SQLAlchemy engine + SQLModel metadata lifecycle.

    Users call ``open()`` once at process startup (typically in the MCP
    server lifespan) to create/migrate the SQLite file, and ``close()`` at
    shutdown to flush and dispose the engine. Tools obtain sessions via
    the ``session()`` context manager and take ``lock_for(entity_type)``
    before kicking off a sync so concurrent callers don't fan out.

    The ``catalog`` attribute exposes a :class:`CatalogQueries` adapter
    that wraps typed reads (``get_by_id``, ``smart_search``, ...) over
    the catalog tier of the cache. As of #472 Phase D this is the only
    catalog read path — the legacy ``CatalogCache`` was decommissioned.
    """

    def __init__(
        self,
        db_path: Path | None = None,
        *,
        in_memory: bool = False,
    ) -> None:
        """Configure the engine but don't open it yet.

        Args:
            db_path: SQLite file path for file-backed mode. Defaults to
                ``_default_db_path()`` when ``None`` and ``in_memory`` is
                false — the shared machine-wide cache dir, or the
                ``KATANA_CACHE_DIR`` override when set (#974). Must not be
                provided when ``in_memory=True``.
            in_memory: Use a ``:memory:`` SQLite backend instead of a file.
                Intended for tests — all data lives in process memory and
                is lost when the engine is closed. A ``StaticPool`` keeps
                one connection alive across sessions so they share the
                same in-memory database (the default pool would give each
                session a fresh, empty DB). Passing ``db_path`` together
                with ``in_memory=True`` raises ``ValueError``.
        """
        if in_memory and db_path is not None:
            msg = "Pass either `db_path` or `in_memory=True`, not both."
            raise ValueError(msg)
        self._in_memory = in_memory
        self._db_path: Path | None = (
            None
            if in_memory
            else (db_path if db_path is not None else _default_db_path())
        )
        self._engine: AsyncEngine | None = None
        self._locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        # Lazy import — ``queries`` imports from this module's siblings,
        # so doing it at function definition time would create a cycle.
        from .queries import CatalogQueries

        self.catalog: CatalogQueries = CatalogQueries(self)

    @property
    def db_path(self) -> Path | None:
        """The SQLite file path, or ``None`` for in-memory engines."""
        return self._db_path

    async def open(self) -> None:
        """Create/open the SQLite backend and apply the SQLModel schema.

        Safe to call only once per engine instance; subsequent calls raise
        ``RuntimeError``.
        """
        if self._engine is not None:
            msg = "TypedCacheEngine.open() called on an already-open engine"
            raise RuntimeError(msg)
        if self._in_memory:
            # ``StaticPool`` + ``check_same_thread=False`` are the canonical
            # pairing for async :memory: SQLite: a single shared connection
            # that all sessions bind to, so seeded data persists across
            # session boundaries within one engine.
            self._engine = create_async_engine(
                "sqlite+aiosqlite:///:memory:",
                poolclass=StaticPool,
                connect_args={"check_same_thread": False},
            )
        else:
            # ``_db_path`` is never None on this branch (``__init__`` only
            # leaves it unset when ``in_memory`` is true), but narrow the
            # type explicitly so static checkers see it.
            db_path = self._db_path
            if db_path is None:
                msg = "TypedCacheEngine: db_path is required for file-backed mode"
                raise RuntimeError(msg)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            self._engine = create_async_engine(
                f"sqlite+aiosqlite:///{db_path}",
            )
            event.listen(self._engine.sync_engine, "connect", _apply_sqlite_pragmas)

        # Validate the EntitySpec dependency graph before any sync runs.
        # Lazy import — ``sync`` imports from ``engine`` for typing
        # (``TYPE_CHECKING``), but the runtime call needs to land here.
        from .fts import (
            initialize_fts_for_connection,
            populate_fts_from_existing_rows,
        )
        from .schema_fingerprint import (
            check_and_rebuild_on_drift,
            write_current_fingerprint,
        )
        from .sync import ENTITY_SPECS, _validate_dependency_graph

        _validate_dependency_graph(ENTITY_SPECS.values())

        async with self._engine.begin() as conn:
            # Run targeted DDL migrations against the pre-existing schema
            # *before* ``create_all``, since ``create_all`` is a no-op on
            # tables that already exist. Anything that needs to widen an
            # existing column or relax a NOT NULL constraint has to drop
            # the affected table first; ``create_all`` then rebuilds it
            # with the current generator output, and the next sync
            # repopulates from the API. The cache is a derived store —
            # losing rows on schema drift is the right trade.
            await conn.run_sync(_migrate_pre_create_all)
            # Schema-fingerprint backstop runs AFTER the targeted
            # migration pass so the targeted migrations get to do their
            # fine-grained work first (only dropping one table's data
            # for known regressions). The fingerprint backstop only
            # fires for changes the targeted migrations didn't catch.
            # The two coexist by design:
            #   - ``_migrate_pre_create_all`` is the narrow optimization
            #     for known cases where we want to keep *other* tables'
            #     data and only drop the one we're migrating.
            #   - ``check_and_rebuild_on_drift`` is the wide net: any
            #     remaining change to ``SQLModel.metadata`` (column
            #     added/removed, type changed, constraint changed) trips
            #     it. Drops every managed table + FTS sidecar;
            #     ``create_all`` rebuilds. After a targeted migration
            #     ran, only the unmigrated drift remains for this pass
            #     to catch.
            await conn.run_sync(check_and_rebuild_on_drift)
            await conn.run_sync(SQLModel.metadata.create_all)
            # Write the current fingerprint AFTER ``create_all`` so the
            # ``cache_meta`` table is guaranteed to exist when we INSERT.
            # Stamps both fresh DBs and post-rebuild DBs so the next
            # open's drift check has a comparison baseline.
            await conn.run_sync(write_current_fingerprint)
            # FTS5 virtual tables sit alongside the SQLModel-managed
            # tables and need their own DDL. Two steps, in order:
            # 1. ``initialize_fts_for_connection`` — emit
            #    ``CREATE VIRTUAL TABLE IF NOT EXISTS <entity>_fts``
            #    plus the trigger trio (``<entity>_ai`` / ``_au`` /
            #    ``_ad``) that keeps the inverted index in sync with
            #    the content table for every write mode (ORM, Core,
            #    raw SQL). Triggers replace the pre-#646 mapper-event
            #    listeners, which fired only for ORM writes and so
            #    silently missed the typed-cache bulk-upsert path.
            # 2. ``populate_fts_from_existing_rows`` — direct-SQL
            #    rebuild from the main tables. Backfills pre-existing
            #    rows on reopen and is the canonical recovery path if
            #    the FTS index ever drifts out of sync with the main
            #    table (cheap server-side ``DELETE`` + ``INSERT
            #    ... SELECT`` per entity, idempotent).
            await conn.run_sync(initialize_fts_for_connection)
            await conn.run_sync(populate_fts_from_existing_rows)

    async def close(self) -> None:
        """Dispose the underlying SQLAlchemy engine.

        No-op if already closed — safe to call from a ``finally`` block
        even when ``open()`` raised.
        """
        if self._engine is None:
            return
        await self._engine.dispose()
        self._engine = None

    def session(self) -> AsyncSession:
        """Return a new async session bound to the engine.

        Use as an ``async with`` context manager; the session closes on
        exit and commits must be explicit.
        """
        if self._engine is None:
            msg = "TypedCacheEngine is not open — call open() first"
            raise RuntimeError(msg)
        return AsyncSession(self._engine)

    def lock_for(self, entity_type: str) -> asyncio.Lock:
        """Per-entity-type asyncio.Lock.

        Take before initiating a sync so two concurrent tool calls don't
        both kick off a full cold-start fetch. ``defaultdict`` creates the
        lock lazily on first lookup.
        """
        return self._locks[entity_type]
