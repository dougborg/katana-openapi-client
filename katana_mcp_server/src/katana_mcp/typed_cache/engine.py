"""Async SQLAlchemy engine + SQLModel metadata manager for the #342 cache.

Owns the SQLite file, applies the generated schema on ``open()``, and
vends async sessions + per-entity asyncio.Locks that protect cold-start
sync fan-out (two concurrent tool calls must not each kick off a full
fetch).
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from pathlib import Path

from platformdirs import user_cache_dir
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

# Side-effect imports: register table=True SQLModel classes with
# ``SQLModel.metadata`` so ``create_all`` emits their DDL. Add new
# entity modules here as they come online.
from katana_mcp.typed_cache import sync_state as _sync_state_mod
from katana_public_api_client.models_pydantic._generated import (
    sales_orders as _sales_orders_mod,
)

assert _sync_state_mod is not None
assert _sales_orders_mod is not None

_DEFAULT_DB_PATH = Path(user_cache_dir("katana-mcp")) / "typed_cache.db"


class TypedCacheEngine:
    """Owns the async SQLAlchemy engine + SQLModel metadata lifecycle.

    Users call ``open()`` once at process startup (typically in the MCP
    server lifespan) to create/migrate the SQLite file, and ``close()`` at
    shutdown to flush and dispose the engine. Tools obtain sessions via
    the ``session()`` context manager and take ``lock_for(entity_type)``
    before kicking off a sync so concurrent callers don't fan out.
    """

    def __init__(self, db_path: Path | None = None) -> None:
        self._db_path = db_path if db_path is not None else _DEFAULT_DB_PATH
        self._engine: AsyncEngine | None = None
        self._locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    @property
    def db_path(self) -> Path:
        return self._db_path

    async def open(self) -> None:
        """Create the SQLite file (if needed), register cache-target tables,
        and apply the schema via ``SQLModel.metadata.create_all``.

        Safe to call only once per engine instance; subsequent calls raise
        ``RuntimeError``.
        """
        if self._engine is not None:
            msg = "TypedCacheEngine.open() called on an already-open engine"
            raise RuntimeError(msg)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._engine = create_async_engine(
            f"sqlite+aiosqlite:///{self._db_path}",
        )
        async with self._engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

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
