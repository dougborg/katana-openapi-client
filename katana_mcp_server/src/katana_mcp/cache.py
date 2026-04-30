"""Persistent SQLite catalog cache with FTS5 search for the MCP server.

Provides always-fresh entity caching with incremental sync via the Katana API's
``updated_at_min`` parameter. On each read, the cache checks for updates since
the last sync — typically returning zero records if nothing changed.

FTS5 powers the primary search path; difflib fuzzy matching is used as a
fallback for typo tolerance when FTS5 returns no results.

Usage::

    cache = CatalogCache()
    await cache.open()

    # Sync variants from API data
    await cache.sync("variant", variants_dicts, VARIANT_INDEX)

    # FTS5 search
    results = await cache.search("variant", "fox fork", limit=20)

    # Direct lookup
    variant = await cache.get_by_sku("FOX-FORK-160")
"""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

import aiosqlite
from platformdirs import user_cache_dir

logger = logging.getLogger(__name__)

# Default cache location
_DEFAULT_CACHE_DIR = Path(user_cache_dir("katana-mcp"))
_DEFAULT_DB_PATH = _DEFAULT_CACHE_DIR / "cache.db"

# Schema version — bump to force a rebuild
_SCHEMA_VERSION = 1

_SCHEMA_SQL = """\
-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY
);

-- Core entity storage
CREATE TABLE IF NOT EXISTS entities (
    entity_type TEXT NOT NULL,
    id          INTEGER NOT NULL,
    data        TEXT NOT NULL,
    updated_at  REAL NOT NULL,
    PRIMARY KEY (entity_type, id)
);

-- Searchable index fields extracted from entities
CREATE TABLE IF NOT EXISTS entity_index (
    rowid       INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,
    id          INTEGER NOT NULL,
    sku         TEXT,
    name        TEXT,
    name2       TEXT,
    UNIQUE (entity_type, id)
);

CREATE INDEX IF NOT EXISTS idx_entity_sku
    ON entity_index(sku COLLATE NOCASE) WHERE sku IS NOT NULL;

-- FTS5 full-text search
CREATE VIRTUAL TABLE IF NOT EXISTS entity_fts USING fts5(
    entity_type, sku, name, name2,
    content='entity_index',
    content_rowid='rowid'
);

-- Triggers to keep FTS in sync with entity_index
CREATE TRIGGER IF NOT EXISTS entity_index_ai AFTER INSERT ON entity_index BEGIN
    INSERT INTO entity_fts(rowid, entity_type, sku, name, name2)
    VALUES (new.rowid, new.entity_type, new.sku, new.name, new.name2);
END;

CREATE TRIGGER IF NOT EXISTS entity_index_ad AFTER DELETE ON entity_index BEGIN
    INSERT INTO entity_fts(entity_fts, rowid, entity_type, sku, name, name2)
    VALUES ('delete', old.rowid, old.entity_type, old.sku, old.name, old.name2);
END;

CREATE TRIGGER IF NOT EXISTS entity_index_au AFTER UPDATE ON entity_index BEGIN
    INSERT INTO entity_fts(entity_fts, rowid, entity_type, sku, name, name2)
    VALUES ('delete', old.rowid, old.entity_type, old.sku, old.name, old.name2);
    INSERT INTO entity_fts(rowid, entity_type, sku, name, name2)
    VALUES (new.rowid, new.entity_type, new.sku, new.name, new.name2);
END;

-- Sync metadata
CREATE TABLE IF NOT EXISTS sync_metadata (
    entity_type TEXT PRIMARY KEY,
    last_synced REAL NOT NULL,
    count       INTEGER NOT NULL DEFAULT 0
);
"""


class EntityType(StrEnum):
    """Cached entity types — single source of truth for cache keys."""

    VARIANT = "variant"
    PRODUCT = "product"
    MATERIAL = "material"
    SERVICE = "service"
    SUPPLIER = "supplier"
    CUSTOMER = "customer"
    LOCATION = "location"
    TAX_RATE = "tax_rate"
    OPERATOR = "operator"
    FACTORY = "factory"


@dataclass(frozen=True)
class IndexFields:
    """Mapping from entity dict keys to index columns.

    Attributes:
        sku_key: Dict key for SKU field (variants only), or None.
        name_key: Dict key for the primary name field.
        name2_key: Dict key for the secondary name field (category, parent name, code).
    """

    sku_key: str | None = None
    name_key: str | None = None
    name2_key: str | None = None


# Pre-defined index field mappings for each entity type
VARIANT_INDEX = IndexFields(
    sku_key="sku", name_key="display_name", name2_key="parent_name"
)
PRODUCT_INDEX = IndexFields(name_key="name", name2_key="category_name")
MATERIAL_INDEX = IndexFields(name_key="name", name2_key="category_name")
SERVICE_INDEX = IndexFields(name_key="name", name2_key="category_name")
SUPPLIER_INDEX = IndexFields(name_key="name", name2_key="code")
CUSTOMER_INDEX = IndexFields(name_key="name", name2_key="email")
# No FTS for small/stable entity types
LOCATION_INDEX = IndexFields(name_key="name")
TAX_RATE_INDEX = IndexFields(name_key="name")
OPERATOR_INDEX = IndexFields(name_key="name")


class CatalogCache:
    """Persistent SQLite cache with FTS5 search for Katana catalog entities.

    The cache uses a unified schema: all entity types share the same tables,
    distinguished by ``entity_type``. FTS5 provides fast full-text search,
    and direct indexed lookups support SKU and ID-based access.
    """

    def __init__(self, db_path: Path | None = None) -> None:
        self._db_path = db_path or _DEFAULT_DB_PATH
        self._db: aiosqlite.Connection | None = None

    @property
    def db_path(self) -> Path:
        """Path to the SQLite database file."""
        return self._db_path

    async def open(self) -> None:
        """Open the database and ensure schema is up to date."""
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db = await aiosqlite.connect(self._db_path)
        self._db.row_factory = aiosqlite.Row

        # Enable WAL mode for better concurrent read/write performance
        await self._db.execute("PRAGMA journal_mode=WAL")
        await self._db.execute("PRAGMA synchronous=NORMAL")

        await self._ensure_schema()
        logger.info("cache_opened", extra={"db_path": str(self._db_path)})

    async def close(self) -> None:
        """Close the database connection."""
        if self._db:
            await self._db.close()
            self._db = None

    async def _ensure_schema(self) -> None:
        """Create or migrate the schema if needed."""
        assert self._db is not None

        # Check current schema version
        try:
            async with self._db.execute(
                "SELECT version FROM schema_version LIMIT 1"
            ) as cursor:
                row = await cursor.fetchone()
                current_version = row[0] if row else 0
        except aiosqlite.OperationalError:
            current_version = 0

        if current_version < _SCHEMA_VERSION:
            if current_version > 0:
                # Drop old schema and rebuild
                logger.info(
                    "cache_schema_upgrade",
                    extra={"from": current_version, "to": _SCHEMA_VERSION},
                )
                await self._db.executescript(
                    "DROP TABLE IF EXISTS entity_fts;"
                    "DROP TABLE IF EXISTS entity_index;"
                    "DROP TABLE IF EXISTS entities;"
                    "DROP TABLE IF EXISTS sync_metadata;"
                    "DROP TABLE IF EXISTS schema_version;"
                )

            await self._db.executescript(_SCHEMA_SQL)
            await self._db.execute(
                "INSERT OR REPLACE INTO schema_version (version) VALUES (?)",
                (_SCHEMA_VERSION,),
            )
            await self._db.commit()

    def _conn(self) -> aiosqlite.Connection:
        """Get the active connection or raise."""
        if self._db is None:
            msg = "CatalogCache is not open. Call open() first."
            raise RuntimeError(msg)
        return self._db

    # ── Sync operations ──────────────────────────────────────────────

    async def sync(
        self,
        entity_type: str,
        entities: list[dict[str, Any]],
        index_fields: IndexFields | None = None,
    ) -> None:
        """Upsert entities into the cache and update FTS index.

        Args:
            entity_type: Entity type key (e.g., "variant", "product").
            entities: List of entity dicts. Each must have an "id" key.
            index_fields: Field mapping for FTS indexing. If None, no FTS index.
        """
        db = self._conn()
        now = time.time()

        if not entities:
            # No entities to upsert, but still update sync metadata
            # so last_synced advances (prevents re-checking immediately)
            count = await self._count(entity_type)
            await db.execute(
                "INSERT OR REPLACE INTO sync_metadata (entity_type, last_synced, count) "
                "VALUES (?, ?, ?)",
                (entity_type, now, count),
            )
            await db.commit()
            return

        # Batch upsert into entities table
        entity_rows = [
            (entity_type, e["id"], json.dumps(e), e.get("updated_at", now))
            for e in entities
        ]
        await db.executemany(
            "INSERT OR REPLACE INTO entities (entity_type, id, data, updated_at) "
            "VALUES (?, ?, ?, ?)",
            entity_rows,
        )

        # Batch upsert into index table (for FTS)
        if index_fields:
            index_ids = [(entity_type, e["id"]) for e in entities]
            index_rows = [
                (
                    entity_type,
                    e["id"],
                    e.get(index_fields.sku_key) if index_fields.sku_key else None,
                    e.get(index_fields.name_key) if index_fields.name_key else None,
                    e.get(index_fields.name2_key) if index_fields.name2_key else None,
                )
                for e in entities
            ]

            # Delete then insert to fire FTS triggers correctly
            await db.executemany(
                "DELETE FROM entity_index WHERE entity_type = ? AND id = ?",
                index_ids,
            )
            await db.executemany(
                "INSERT INTO entity_index (entity_type, id, sku, name, name2) "
                "VALUES (?, ?, ?, ?, ?)",
                index_rows,
            )

        # Update sync metadata
        count = await self._count(entity_type)
        await db.execute(
            "INSERT OR REPLACE INTO sync_metadata (entity_type, last_synced, count) "
            "VALUES (?, ?, ?)",
            (entity_type, now, count),
        )

        await db.commit()
        logger.info(
            "cache_synced",
            extra={
                "entity_type": entity_type,
                "upserted": len(entities),
                "total": count,
            },
        )

    async def get_last_synced(self, entity_type: str) -> float | None:
        """Get the timestamp of the last sync for an entity type.

        Returns:
            Unix timestamp of last sync, or None if never synced.
        """
        db = self._conn()
        async with db.execute(
            "SELECT last_synced FROM sync_metadata WHERE entity_type = ?",
            (entity_type,),
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

    async def mark_dirty(self, entity_type: str) -> None:
        """Clear the last_synced timestamp, forcing a resync on next access."""
        db = self._conn()
        await db.execute(
            "DELETE FROM sync_metadata WHERE entity_type = ?",
            (entity_type,),
        )
        await db.commit()

    # ── Search ───────────────────────────────────────────────────────

    async def search(
        self,
        entity_type: str,
        query: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Search entities using FTS5 with BM25 ranking.

        Tokenizes the query and requires all tokens to match (AND logic).

        Args:
            entity_type: Entity type to search within.
            query: Search query string.
            limit: Maximum results to return.

        Returns:
            List of entity dicts, ranked by relevance.
        """
        query = query.strip()
        if not query:
            return []

        db = self._conn()

        # Build FTS5 match expression: all tokens must match
        tokens = query.split()
        # Escape double quotes in tokens
        escaped_tokens = [t.replace('"', '""') for t in tokens]
        # FTS5 query: each token as a prefix match, ANDed together
        fts_query = " AND ".join(f'"{t}"*' for t in escaped_tokens)

        try:
            async with db.execute(
                """
                SELECT e.data
                FROM entity_fts fts
                JOIN entity_index idx ON fts.rowid = idx.rowid
                JOIN entities e ON e.entity_type = idx.entity_type AND e.id = idx.id
                WHERE entity_fts MATCH ? AND idx.entity_type = ?
                ORDER BY bm25(entity_fts)
                LIMIT ?
                """,
                (fts_query, entity_type, limit),
            ) as cursor:
                rows = await cursor.fetchall()
                return [json.loads(row[0]) for row in rows]
        except aiosqlite.OperationalError as exc:
            # FTS5 query syntax error — fall through to fuzzy
            logger.debug("fts5_query_failed", extra={"query": query, "error": str(exc)})
            return []

    async def search_fuzzy(
        self,
        entity_type: str,
        query: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Fuzzy search fallback using difflib on cached entity index fields.

        Used when FTS5 returns no results (e.g., typos like "stainles").

        Args:
            entity_type: Entity type to search within.
            query: Search query string.
            limit: Maximum results to return.

        Returns:
            List of entity dicts, ranked by fuzzy relevance.
        """
        from katana_public_api_client.helpers.search import score_match

        query = query.strip()
        if not query:
            return []

        db = self._conn()

        # Load all index entries for this entity type
        async with db.execute(
            "SELECT idx.id, idx.sku, idx.name, idx.name2, e.data "
            "FROM entity_index idx "
            "JOIN entities e ON e.entity_type = idx.entity_type AND e.id = idx.id "
            "WHERE idx.entity_type = ?",
            (entity_type,),
        ) as cursor:
            rows = await cursor.fetchall()

        scored: list[tuple[dict[str, Any], float]] = []
        for row in rows:
            score = score_match(
                query=query,
                fields={
                    "sku": (row[1] or "", 100),
                    "name": (row[2] or "", 30),
                    "name2": (row[3] or "", 20),
                },
            )
            if score > 0:
                scored.append((json.loads(row[4]), score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [entity for entity, _score in scored[:limit]]

    # ── Direct lookups ───────────────────────────────────────────────

    async def get_by_id(
        self, entity_type: str, entity_id: int
    ) -> dict[str, Any] | None:
        """Look up a single entity by type and ID."""
        db = self._conn()
        async with db.execute(
            "SELECT data FROM entities WHERE entity_type = ? AND id = ?",
            (entity_type, entity_id),
        ) as cursor:
            row = await cursor.fetchone()
            return json.loads(row[0]) if row else None

    async def get_many_by_ids(
        self, entity_type: str, entity_ids: Iterable[int]
    ) -> dict[int, dict[str, Any]]:
        """Look up many entities by type and IDs in one query.

        Returns ``{id: data}`` for IDs that hit the cache; missing IDs are
        absent from the result. Empty input → empty dict (no DB read). Use
        instead of ``asyncio.gather(get_by_id(...) ...)`` when enriching a
        batch of rows with cached lookups — one query replaces N reads.

        IDs are passed as a JSON array parameter and expanded via
        ``json_each``, so the SQL text is constant (no string interpolation)
        and the IDs go through SQLite's regular parameter binding.
        """
        ids = list({int(i) for i in entity_ids})
        if not ids:
            return {}
        db = self._conn()
        async with db.execute(
            "SELECT id, data FROM entities "
            "WHERE entity_type = ? "
            "AND id IN (SELECT value FROM json_each(?))",
            (entity_type, json.dumps(ids)),
        ) as cursor:
            return {int(row[0]): json.loads(row[1]) for row in await cursor.fetchall()}

    async def get_by_sku(self, sku: str) -> dict[str, Any] | None:
        """Look up a variant by SKU (case-insensitive)."""
        db = self._conn()
        async with db.execute(
            "SELECT e.data FROM entity_index idx "
            "JOIN entities e ON e.entity_type = idx.entity_type AND e.id = idx.id "
            "WHERE idx.sku = ? COLLATE NOCASE AND idx.entity_type = ?",
            (sku, EntityType.VARIANT),
        ) as cursor:
            row = await cursor.fetchone()
            return json.loads(row[0]) if row else None

    async def get_all(self, entity_type: str) -> list[dict[str, Any]]:
        """Get all cached entities of a given type."""
        db = self._conn()
        async with db.execute(
            "SELECT data FROM entities WHERE entity_type = ?",
            (entity_type,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [json.loads(row[0]) for row in rows]

    # ── Invalidation ─────────────────────────────────────────────────

    async def invalidate(self, entity_type: str, entity_id: int | None = None) -> None:
        """Remove cached entities and force resync.

        Args:
            entity_type: Entity type to invalidate.
            entity_id: If provided, only invalidate this specific entity.
                If None, invalidate all entities of the type.
        """
        db = self._conn()

        if entity_id is not None:
            await db.execute(
                "DELETE FROM entity_index WHERE entity_type = ? AND id = ?",
                (entity_type, entity_id),
            )
            await db.execute(
                "DELETE FROM entities WHERE entity_type = ? AND id = ?",
                (entity_type, entity_id),
            )
        else:
            await db.execute(
                "DELETE FROM entity_index WHERE entity_type = ?",
                (entity_type,),
            )
            await db.execute(
                "DELETE FROM entities WHERE entity_type = ?",
                (entity_type,),
            )
            await db.execute(
                "DELETE FROM sync_metadata WHERE entity_type = ?",
                (entity_type,),
            )

        await db.commit()

    async def clear(self) -> None:
        """Remove all cached data."""
        db = self._conn()
        await db.execute("DELETE FROM entity_index")
        await db.execute("DELETE FROM entities")
        await db.execute("DELETE FROM sync_metadata")
        await db.commit()

    # ── Stats ────────────────────────────────────────────────────────

    async def stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        db = self._conn()

        result: dict[str, Any] = {"db_path": str(self._db_path), "entities": {}}

        async with db.execute(
            "SELECT entity_type, last_synced, count FROM sync_metadata"
        ) as cursor:
            async for row in cursor:
                result["entities"][row[0]] = {
                    "count": row[2],
                    "last_synced": row[1],
                    "age_seconds": round(time.time() - row[1], 1),
                }

        return result

    # ── Combined search ──────────────────────────────────────────────

    async def smart_search(
        self,
        entity_type: str,
        query: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Search with FTS5 primary and difflib fuzzy fallback.

        Tries FTS5 first (fast, handles prefix matching). If no results,
        falls back to difflib fuzzy matching (handles typos).

        Args:
            entity_type: Entity type to search within.
            query: Search query string.
            limit: Maximum results to return.

        Returns:
            List of entity dicts, ranked by relevance.
        """
        # Try FTS5 first
        results = await self.search(entity_type, query, limit=limit)
        if results:
            return results

        # Fuzzy fallback for typos
        return await self.search_fuzzy(entity_type, query, limit=limit)

    # ── Internal ─────────────────────────────────────────────────────

    async def _count(self, entity_type: str) -> int:
        """Count entities of a given type."""
        db = self._conn()
        async with db.execute(
            "SELECT COUNT(*) FROM entities WHERE entity_type = ?",
            (entity_type,),
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0
