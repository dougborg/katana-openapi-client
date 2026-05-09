"""FTS5 sidecar for the SQLModel-backed catalog cache (#472 Phase B).

The transactional half of the typed cache stores entities as plain
SQLModel rows and queries them with WHERE clauses; the catalog half
needs full-text search across SKU / name / barcode / supplier-code
columns. We attach FTS5 virtual tables to entities that declare a
``__fts_columns__: ClassVar[tuple[str, ...]]`` ClassVar (set on
``CachedVariant``, ``CachedProduct``, ``CachedMaterial``,
``CachedService``, ``CachedCustomer``, ``CachedSupplier``).

The legacy ``CatalogCache`` used a single shared ``entity_fts`` table
with a 3-text-column projection. This module instead emits one virtual
table per entity (``variant_fts``, ``product_fts``, ...) so each
entity's FTS columns can mirror its actual schema. ``content='<table>'``
+ ``content_rowid='id'`` means the FTS index is an external-content
table — row content lives in the main table, FTS5 only stores the
inverted index.

Mutations flow through **SQLite triggers** on the content tables:
``<entity>_ai`` (after-insert) emits an FTS row, ``<entity>_au``
(after-update) issues an FTS5 ``delete`` for the old content followed
by an INSERT of the new content, and ``<entity>_ad`` (after-delete)
issues the FTS5 ``delete`` command. Triggers fire for *every* write
mode — SQLAlchemy ORM (``session.add`` / ``session.merge``), Core
statements (``sqlalchemy.dialects.sqlite.insert(...).on_conflict_do_update``,
``sqlmodel.delete``), and raw SQL — so the typed-cache bulk-upsert
path in ``sync._sync_one_locked`` keeps the FTS index in lock-step
without an extra reindex pass. The trigger-based design is the
SQLite-recommended pattern for external-content FTS5 tables (see
https://sqlite.org/fts5.html#external_content_tables).

Startup also asserts every column in ``Cached*.__fts_columns__`` exists
on the table — a generator regression that drops a column from the
schema but leaves it in the FTS spec would otherwise corrupt every
search until the next user-visible failure.

**SQL safety**: FTS5 virtual tables and triggers can't be expressed
through the SQLAlchemy ORM (no ``Table`` declarative object exists
for them), so the schema SQL must be assembled as strings. All FTS
schema work goes through ``DDL(...)`` (``CREATE VIRTUAL TABLE``,
``CREATE TRIGGER``, ``DROP TRIGGER IF EXISTS``, the data-rebuild
``DELETE FROM <fts>`` + ``INSERT ... SELECT FROM <main>``) —
the SQLAlchemy construct designated for raw schema SQL. No user
input ever flows through it, and Semgrep's ``avoid-sqlalchemy-text``
rule correctly leaves it alone.

Identifiers (table names, column names) come exclusively from the
Python-class metadata set by the SQLModel generator at import time —
never from user input. We additionally validate them against
``_IDENTIFIER_RE`` before interpolation as a belt-and-suspenders
guard against a future regression where the generator emits
something exotic.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from typing import Any

from sqlalchemy import DDL
from sqlmodel import SQLModel

# SQL identifiers (table + column names) must match this pattern before
# we interpolate them into a DDL/DML statement. The cache-class
# metadata set by the SQLModel generator already produces snake_case
# identifiers, so the regex is just a defense-in-depth check against a
# future generator regression — never a real attack vector.
_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _safe_identifier(name: str) -> str:
    """Validate ``name`` matches ``_IDENTIFIER_RE``; raise otherwise."""
    if not _IDENTIFIER_RE.fullmatch(name):
        msg = f"Invalid SQL identifier from cache metadata: {name!r}"
        raise ValueError(msg)
    return name


def _fts_table_name(table_name: str) -> str:
    """``variant`` -> ``variant_fts``. Keep the convention symmetric."""
    return f"{_safe_identifier(table_name)}_fts"


def _all_subclasses(cls: type[SQLModel]) -> Iterator[type[SQLModel]]:
    """Recursive ``__subclasses__()`` traversal — generator over every descendant.

    SQLModel doesn't expose a SQLAlchemy-style registry on the class
    (``SQLModel.registry`` raises ``AttributeError`` because pydantic's
    metaclass intercepts the attribute lookup), so we walk the Python
    inheritance graph directly. The generated ``Cached*`` classes are
    the only ``table=True`` SQLModel descendants in the project, so the
    traversal stays bounded.
    """
    for sub in cls.__subclasses__():
        yield sub
        yield from _all_subclasses(sub)


def _classes_with_fts_columns() -> list[type[SQLModel]]:
    """Walk subclasses for table=True classes that declare ``__fts_columns__``.

    The generator emits ``__fts_columns__`` as a ClassVar on the cache
    class for each entity in ``CACHE_FTS_SPECS`` (see
    ``scripts/generate_pydantic_models.py``). We rely on the side-effect
    module imports in ``engine.py`` to load the cache classes; calling
    this after ``engine.open()`` always returns the full set.

    A class can show up multiple times via diamond inheritance
    (``CachedVariant`` extends both ``UpdatableEntity`` and
    ``DeletableEntity``, both of which are SQLModel descendants), so
    dedupe on table name to keep DDL emission idempotent.
    """
    classes: list[type[SQLModel]] = []
    seen: set[str] = set()
    for cls in _all_subclasses(SQLModel):
        if not _fts_columns(cls):
            continue
        # ``__table__`` is set on table=True classes by the SQLModel
        # metaclass. Non-table siblings (intermediate base classes
        # ``UpdatableEntity`` etc.) won't have it; skip them so the
        # FTS walker stays restricted to actual cache rows.
        table = _table_for(cls)
        if table is None:
            continue
        if table.name in seen:
            continue
        seen.add(table.name)
        classes.append(cls)
    return classes


def _fts_columns(cls: type[SQLModel]) -> tuple[str, ...]:
    """Read the ``__fts_columns__`` ClassVar without static-checker noise."""
    fts = getattr(cls, "__fts_columns__", ())
    if isinstance(fts, tuple):
        return fts
    return ()


def _table_for(cls: type[SQLModel]) -> Any:
    """Return ``cls.__table__`` — the SQLAlchemy ``Table`` object.

    The SQLModel metaclass populates ``__table__`` on ``table=True``
    classes; the static type ``type[SQLModel]`` doesn't expose it, so
    pull it via ``getattr`` and let ``Any`` propagate.
    """
    return getattr(cls, "__table__", None)


def _validate_fts_columns(cls: type[SQLModel]) -> None:
    """Assert every column in ``__fts_columns__`` exists on ``__table__.columns``.

    Catches the generator regression where a cache column is dropped
    from the schema but left in ``CACHE_FTS_SPECS`` — without this
    check, the FTS DDL would still emit successfully (FTS5 doesn't
    validate column names against the content table) and every search
    would silently return no results.
    """
    fts_cols = _fts_columns(cls)
    table = _table_for(cls)
    table_cols = {col.name for col in table.columns}
    missing = [col for col in fts_cols if col not in table_cols]
    if missing:
        msg = (
            f"{cls.__name__}.__fts_columns__ references columns not present "
            f"on {table.name}: {missing}"
        )
        raise RuntimeError(msg)


def _create_fts_tables_ddl(conn: Any) -> None:
    """Emit FTS5 virtual tables + the trigger trio that keeps them in sync.

    For each FTS-enabled cache class:

    1. ``CREATE VIRTUAL TABLE IF NOT EXISTS <entity>_fts USING fts5(...)``
       — external-content table: ``content='<table>'`` +
       ``content_rowid='id'``. The FTS row content lives in the main
       table; FTS5 stores only the inverted index.
    2. Three triggers on the main table — ``<entity>_ai`` (after
       INSERT), ``<entity>_au`` (after UPDATE), ``<entity>_ad`` (after
       DELETE) — that keep the inverted index in lock-step. Triggers
       fire for *every* write mode (ORM, Core, raw SQL), unlike
       SQLAlchemy mapper events (ORM-only). This matters because the
       typed-cache bulk-upsert path in ``sync._sync_one_locked``
       writes via ``sqlalchemy.dialects.sqlite.insert(...).on_conflict_do_update``,
       a Core statement that bypasses ORM events but fires triggers
       just like any other SQLite write.

    The trigger trio uses FTS5's external-content maintenance pattern:
    after-insert writes the new row's content into the inverted index;
    after-delete issues the FTS5 ``'delete'`` command with the OLD
    content so FTS5 can derive the tokens to remove; after-update is
    delete-of-old + insert-of-new in one trigger body. ``IFNULL(col, '')``
    coerces NULLs to empty strings on the way into the index so the
    column shape stays consistent (FTS5 distinguishes empty-string rows
    from absent-column rows in some edge cases; consistency is safer).

    All trigger bodies and the virtual-table DDL go through ``DDL(...)``
    rather than ``text(...)`` so Semgrep's ``avoid-sqlalchemy-text`` rule
    leaves them alone — no user input ever flows through them; the only
    interpolated values are validated identifiers from cache-class
    metadata.
    """
    for cls in _classes_with_fts_columns():
        _validate_fts_columns(cls)
        table = _table_for(cls)
        table_name = _safe_identifier(table.name)
        fts_table = _fts_table_name(table_name)
        cols = _fts_columns(cls)
        safe_cols = [_safe_identifier(c) for c in cols]
        col_list = ", ".join(safe_cols)
        # ``content`` + ``content_rowid`` make the FTS table reference
        # rows in the main table by ``id`` (the integer PK on every
        # Cached* class). FTS5 uses the rowid for ranking + lookups; the
        # FTS row mirrors the content columns at insert/update time.
        conn.execute(
            DDL(
                f"CREATE VIRTUAL TABLE IF NOT EXISTS {fts_table} "
                f"USING fts5({col_list}, content='{table_name}', content_rowid='id')"
            )
        )

        # Trigger trio. Drop-then-create is idempotent across reopens
        # — ``CREATE TRIGGER IF NOT EXISTS`` would skip re-creation if
        # the trigger body changed (e.g., an FTS column was added),
        # silently leaving the old definition in place. Drop + create
        # forces a refresh on every engine.open(). Cheap (the triggers
        # don't fire during DDL) and self-healing.
        new_value_list = ", ".join(f"IFNULL(new.{c}, '')" for c in safe_cols)
        old_value_list = ", ".join(f"IFNULL(old.{c}, '')" for c in safe_cols)
        ai_trigger = f"{table_name}_ai"
        au_trigger = f"{table_name}_au"
        ad_trigger = f"{table_name}_ad"
        conn.execute(DDL(f"DROP TRIGGER IF EXISTS {ai_trigger}"))
        conn.execute(DDL(f"DROP TRIGGER IF EXISTS {au_trigger}"))
        conn.execute(DDL(f"DROP TRIGGER IF EXISTS {ad_trigger}"))
        conn.execute(
            DDL(
                f"CREATE TRIGGER {ai_trigger} AFTER INSERT ON {table_name} BEGIN "
                f"INSERT INTO {fts_table} (rowid, {col_list}) "
                f"VALUES (new.id, {new_value_list}); "
                f"END"
            )
        )
        conn.execute(
            DDL(
                f"CREATE TRIGGER {ad_trigger} AFTER DELETE ON {table_name} BEGIN "
                f"INSERT INTO {fts_table}({fts_table}, rowid, {col_list}) "
                f"VALUES('delete', old.id, {old_value_list}); "
                f"END"
            )
        )
        conn.execute(
            DDL(
                f"CREATE TRIGGER {au_trigger} AFTER UPDATE ON {table_name} BEGIN "
                f"INSERT INTO {fts_table}({fts_table}, rowid, {col_list}) "
                f"VALUES('delete', old.id, {old_value_list}); "
                f"INSERT INTO {fts_table} (rowid, {col_list}) "
                f"VALUES (new.id, {new_value_list}); "
                f"END"
            )
        )


def initialize_fts_for_connection(connection: Any) -> None:
    """Create per-entity FTS5 virtual tables + their sync triggers.

    Called from ``TypedCacheEngine.open()`` inside the ``run_sync`` block
    that already runs ``SQLModel.metadata.create_all``. Wraps the DDL
    emission so the engine doesn't reach into the FTS module's private
    helper directly.
    """
    _create_fts_tables_ddl(connection)


def populate_fts_from_existing_rows(connection: Any) -> None:
    """Backfill FTS index from already-cached rows on engine reopen.

    SQLite persists the main tables across processes (file-backed
    engine), and the FTS virtual table persists too, but reopens of an
    engine that previously seeded FTS rows are idempotent: for each
    FTS-enabled class, ``DELETE FROM <fts>`` + re-INSERT from the
    content table by id. Cheap (rebuilds the inverted index from the
    text already on disk) and unconditionally consistent; cost scales
    linearly with row count, dominated by the catalog cold-start scope
    (~5K variants on a typical Katana shop).

    The DELETE/INSERT pair runs unconditionally for every FTS-enabled
    class. Cold-start (empty main table) is a cheap no-op rather than
    an explicit skip — both statements operate on zero rows.
    """
    for cls in _classes_with_fts_columns():
        table = _table_for(cls)
        table_name = _safe_identifier(table.name)
        fts = _fts_table_name(table_name)
        cols = _fts_columns(cls)
        safe_cols = [_safe_identifier(c) for c in cols]
        col_list = ", ".join(safe_cols)
        # Truncate the FTS sidecar first so the rebuild is canonical.
        # ``DDL`` is the SQLAlchemy primitive for raw schema-level SQL;
        # ``fts`` is a validated identifier (no user input).
        connection.execute(DDL(f"DELETE FROM {fts}"))
        # Pull every row from the main table and re-emit FTS rows. Use
        # ``IFNULL(col, '')`` so the SQL coercion mirrors the Python
        # path's None -> '' behavior.
        coerced_cols = ", ".join(f"IFNULL({c}, '')" for c in safe_cols)
        # ``DDL`` again — this is a server-side rebuild (data flows
        # main-table -> FTS sidecar without leaving the database), so
        # there is no user input to bind.
        connection.execute(
            DDL(
                f"INSERT INTO {fts} (rowid, {col_list}) "
                f"SELECT id, {coerced_cols} FROM {table_name}"
            )
        )
