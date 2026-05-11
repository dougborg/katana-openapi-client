"""Schema-fingerprint backstop for the typed-cache SQLite file.

Why this exists: ``SQLModel.metadata.create_all`` only emits
``CREATE TABLE IF NOT EXISTS`` — it can't add a column to a table that
already exists. When a generator-driven schema change adds, removes,
or retypes columns (e.g., #669 promoted ``CachedLocation`` from
``KatanaPydanticBase`` to ``DeletableEntity``, adding ``id``,
``created_at``, ``updated_at``, ``deleted_at``), an existing
pre-upgrade SQLite cache file keeps the old, narrower table. The next
query that emits ``WHERE deleted_at IS NULL`` blows up with
``sqlite3.OperationalError: no such column: location.deleted_at``.

There is already a finer-grained migration helper at
``engine._migrate_pre_create_all`` that pattern-matches on stale DDL
substrings — useful when we want to preserve the data in the *other*
tables and only drop one. But that approach requires the developer
who edits the schema to remember to add a migration block; #669
forgot, which produced this regression.

This module provides a backstop that auto-detects schema drift:

1. Compute a deterministic SHA-256 of the current SQLModel metadata
   by compiling each table to its SQLite ``CREATE TABLE`` DDL
   (sorted by name), concatenating, and hashing.
2. Persist the fingerprint in a small ``cache_meta`` table
   (``key TEXT PRIMARY KEY, value TEXT``).
3. On open, compare the stored fingerprint to the current one. On
   mismatch (or if the meta table is absent but the DB already has
   tables — the "first run after upgrade from a pre-fingerprint
   version" case), drop every SQLModel-managed table plus the FTS5
   sidecars and triggers, then ``create_all`` rebuilds them under the
   current schema. The next sync repopulates from the API.
4. After ``create_all`` completes, write the new fingerprint.

The cache is a derived store — losing rows on schema drift is the
right trade. The alternative (silently broken queries until users
manually delete the cache file) is much worse.

Note on stability: the fingerprint depends on SQLAlchemy's SQLite DDL
emission. Across SQLAlchemy minor versions, identical metadata can
in principle compile to slightly different DDL strings (e.g., quoting
or whitespace nuances), which would trigger a one-time spurious
rebuild on upgrade. In practice this is harmless — a one-time
re-fetch on SQLAlchemy upgrade is a small price for the broad
coverage. If we ever observe noisy churn, we can fall back to an
explicit integer ``SCHEMA_VERSION`` constant bumped per-PR.
"""

from __future__ import annotations

import hashlib
from typing import Any

from sqlalchemy import DDL, text
from sqlalchemy.dialects import sqlite as sqlite_dialect
from sqlalchemy.schema import CreateTable
from sqlmodel import Field, SQLModel

from katana_mcp.typed_cache.fts import _safe_identifier

# ``cache_meta`` lives alongside the other SQLModel-managed tables —
# ``create_all`` will create it like any other. Single-row table keyed
# by string. Today the only key is ``schema_fingerprint``; future
# infrastructure-level metadata can land here too without bumping the
# fingerprint logic.
_FINGERPRINT_KEY = "schema_fingerprint"


class CacheMeta(SQLModel, table=True):
    """Single key/value store for cache-engine-level metadata.

    Holds the schema fingerprint today; future infrastructure-level
    state can land here too. Kept separate from :class:`SyncState`
    (per-entity watermarks) because the audiences differ — meta is
    read-by-engine on open, sync_state is read-by-sync on every fetch.
    """

    __tablename__ = "cache_meta"

    key: str = Field(primary_key=True)
    value: str


def compute_metadata_fingerprint() -> str:
    """SHA-256 of the SQLite-compiled DDL for every table in ``SQLModel.metadata``.

    Tables are sorted by name for determinism — ``MetaData.tables``
    iteration order isn't guaranteed stable across runs and we want
    byte-identical input on identical schemas. The dialect is pinned
    to SQLite because that's the only backend the typed cache runs
    against; a different backend would emit different DDL syntax and
    poison the comparison even when the logical schema is identical.
    """
    dialect = sqlite_dialect.dialect()
    parts: list[str] = []
    for table in sorted(SQLModel.metadata.tables.values(), key=lambda t: t.name):
        ddl = str(CreateTable(table).compile(dialect=dialect))
        parts.append(ddl)
    payload = "\n".join(parts).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _table_exists(sync_conn: Any, table_name: str) -> bool:
    """Cheap ``sqlite_master`` lookup for one table."""
    row = sync_conn.execute(
        text("SELECT 1 FROM sqlite_master WHERE type='table' AND name=:n"),
        {"n": table_name},
    ).first()
    return row is not None


def _has_any_managed_tables(sync_conn: Any) -> bool:
    """True when at least one SQLModel-managed table already exists in the DB.

    Used to distinguish a fresh DB (no meta + no tables — first open ever)
    from an upgraded DB (no meta + tables present — pre-fingerprint
    version). Only the latter needs a rebuild on the migration boundary.
    """
    for table in SQLModel.metadata.tables.values():
        if _table_exists(sync_conn, table.name):
            return True
    return False


def _read_stored_fingerprint(sync_conn: Any) -> str | None:
    """Fetch the previously-written fingerprint, or None if absent.

    Returns None when ``cache_meta`` doesn't exist yet (first open on
    this DB file) and when it exists but has no fingerprint row (the
    one-table-but-no-row case after a partial migration).
    """
    if not _table_exists(sync_conn, "cache_meta"):
        return None
    row = sync_conn.execute(
        text("SELECT value FROM cache_meta WHERE key=:k"),
        {"k": _FINGERPRINT_KEY},
    ).first()
    return row[0] if row else None


def _drop_all_managed_tables(sync_conn: Any) -> None:
    """Drop every SQLModel-managed table + their FTS sidecars and triggers.

    Run when the stored fingerprint disagrees with the current one. The
    drop must be wide enough to clear stale state but precise enough to
    avoid touching unrelated SQLite metadata.

    Order matters because of foreign-key references and because the FTS
    triggers reference the content tables:

    1. Drop FTS triggers first — they reference the content table by name
       and would error on the table-drop otherwise.
    2. Drop FTS5 virtual tables.
    3. Drop the SQLModel content tables in reverse-dependency order
       (``metadata.sorted_tables`` is dependency-asc; reverse it for the
       drop pass so children go before parents).

    The ``cache_meta`` table itself is included in the drop so the post-
    rebuild ``create_all`` re-creates it cleanly. The fingerprint write
    that follows ``create_all`` will repopulate the row.

    All DDL goes through :class:`DDL` (not :func:`text`) to keep
    Semgrep's ``avoid-sqlalchemy-text`` rule clean. Identifiers come
    exclusively from SQLModel metadata (never user input), and each one
    is additionally run through :func:`fts._safe_identifier` before
    interpolation as a belt-and-suspenders guard against a future
    generator regression that emits something exotic — matching the
    same defense-in-depth convention ``fts._create_fts_tables_ddl``
    applies on the FTS-sidecar side.
    """
    # FTS sidecar names are derived deterministically from the parent
    # table name via the same convention ``fts._fts_table_name`` uses.
    # Mirror it locally rather than reaching into the FTS module's
    # private helper — keeps the dependency one-way (engine → fts) and
    # the drop logic doesn't need the FTS module's column metadata.
    for table in SQLModel.metadata.tables.values():
        table_name = _safe_identifier(table.name)
        fts_table = f"{table_name}_fts"
        # Triggers first (they reference the content table by name).
        sync_conn.execute(DDL(f"DROP TRIGGER IF EXISTS {table_name}_ai"))
        sync_conn.execute(DDL(f"DROP TRIGGER IF EXISTS {table_name}_au"))
        sync_conn.execute(DDL(f"DROP TRIGGER IF EXISTS {table_name}_ad"))
        sync_conn.execute(DDL(f"DROP TABLE IF EXISTS {fts_table}"))

    # Drop in reverse-dependency order so child tables (foreign-key
    # holders) drop before their parents. ``sorted_tables`` is FK-asc;
    # reverse it for the drop pass.
    for table in reversed(SQLModel.metadata.sorted_tables):
        table_name = _safe_identifier(table.name)
        sync_conn.execute(DDL(f"DROP TABLE IF EXISTS {table_name}"))


def check_and_rebuild_on_drift(sync_conn: Any) -> bool:
    """Inspect the DB; drop everything if the fingerprint doesn't match.

    Called from ``TypedCacheEngine.open()`` *before* ``create_all`` (so
    ``create_all`` lays down a fresh schema) and *after* the
    finer-grained ``_migrate_pre_create_all`` pass (whose targeted
    table-level migrations are an optimization for known cases where we
    want to preserve other tables' data; this fingerprint check is the
    catch-all backstop for everything else).

    Returns True when a rebuild was performed (caller may want to log
    or surface it), False when the fingerprint matched and the DB was
    left alone.

    Decision matrix:

    - No managed tables exist (fresh DB) → no-op, return False. The
      caller's ``create_all`` will lay everything down.
    - ``cache_meta`` doesn't exist but other managed tables do → upgrade
      from a pre-fingerprint version. Rebuild and return True.
    - ``cache_meta`` exists with a fingerprint that matches → no-op.
    - Fingerprint mismatch (schema changed since the last write) →
      Rebuild and return True.
    """
    has_tables = _has_any_managed_tables(sync_conn)
    stored = _read_stored_fingerprint(sync_conn)
    current = compute_metadata_fingerprint()

    # Fresh DB — nothing to drop.
    if not has_tables:
        return False

    # Tables present but no stored fingerprint → upgrade from a
    # pre-fingerprint version. Treat as drift and rebuild. (This is the
    # path that fixes #669-style regressions on existing user caches.)
    if stored is None:
        _drop_all_managed_tables(sync_conn)
        return True

    if stored == current:
        return False

    _drop_all_managed_tables(sync_conn)
    return True


def write_current_fingerprint(sync_conn: Any) -> None:
    """Upsert the current fingerprint into ``cache_meta``.

    Called from ``TypedCacheEngine.open()`` *after* ``create_all`` so
    ``cache_meta`` is guaranteed to exist when we write to it.

    Uses SQLite's ``ON CONFLICT(key) DO UPDATE`` rather than two
    separate statements so concurrent opens (rare — engines are opened
    once per process — but cheap to harden against) can't interleave
    a delete with an insert from another connection.
    """
    fingerprint = compute_metadata_fingerprint()
    sync_conn.execute(
        text(
            "INSERT INTO cache_meta (key, value) VALUES (:k, :v) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value"
        ),
        {"k": _FINGERPRINT_KEY, "v": fingerprint},
    )
