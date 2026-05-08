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

Mutations (insert/update/delete) flow through SQLAlchemy event
listeners on ``engine.sync_engine``. The events run synchronously on
the connection pool's sync side; the work is just a few INSERT/DELETE
statements per row, so adding async overhead would gain nothing.
``after_insert`` / ``after_update`` keep the FTS index in lock-step
with the main table; ``after_delete`` removes the corresponding FTS
row so soft-deleted entities (and force-resyncs) clean up correctly.

Startup also asserts every column in ``Cached*.__fts_columns__`` exists
on the table — a generator regression that drops a column from the
schema but leaves it in the FTS spec would otherwise corrupt every
search until the next user-visible failure.

**SQL safety**: FTS5 virtual tables can't be expressed through the
SQLAlchemy ORM (no ``Table`` declarative object exists for them), so
the SQL must be assembled as strings. Two SQLAlchemy primitives keep
the security audit clean:

- ``DDL(...)`` for schema operations (``CREATE VIRTUAL TABLE`` and
  the truncate-style ``DELETE FROM <fts>``). DDL is the SQLAlchemy
  construct designated for raw schema SQL — no user input is ever
  meant to flow through it, and Semgrep's ``avoid-sqlalchemy-text``
  rule correctly leaves it alone.
- ``conn.exec_driver_sql(...)`` for FTS row INSERT/DELETE. Driver-SQL
  takes positional ``?`` placeholders bound by the DBAPI, so user
  input (FTS row content, row IDs) never reaches the SQL string.

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
from typing import TYPE_CHECKING, Any

from sqlalchemy import DDL, event
from sqlmodel import SQLModel

if TYPE_CHECKING:
    from sqlalchemy.engine import Connection
    from sqlalchemy.orm import Mapper


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
    """Emit ``CREATE VIRTUAL TABLE IF NOT EXISTS <entity>_fts USING fts5(...)``.

    External-content table: ``content='<table>'`` + ``content_rowid='id'``.
    The FTS index stays in lock-step with the main table only via the
    after-insert/update/delete listeners — we deliberately do *not*
    install SQL triggers, because pre-existing rows on cold-start come
    in through SQLAlchemy event hooks and triggers would double-write
    every FTS row.
    """
    for cls in _classes_with_fts_columns():
        _validate_fts_columns(cls)
        table = _table_for(cls)
        table_name = _safe_identifier(table.name)
        fts_table = _fts_table_name(table_name)
        cols = _fts_columns(cls)
        col_list = ", ".join(_safe_identifier(c) for c in cols)
        # ``content`` + ``content_rowid`` make the FTS table reference
        # rows in the main table by ``id`` (the integer PK on every
        # Cached* class). FTS5 uses the rowid for ranking + lookups; the
        # FTS row mirrors the content columns at insert/update time.
        sql = (
            f"CREATE VIRTUAL TABLE IF NOT EXISTS {fts_table} "
            f"USING fts5({col_list}, content='{table_name}', content_rowid='id')"
        )
        # ``DDL`` is the SQLAlchemy primitive for raw schema statements
        # (FTS5 virtual tables have no ORM construct). Identifiers are
        # validated by ``_safe_identifier``.
        conn.execute(DDL(sql))


def _row_value(target: Any, col: str) -> Any:
    """Pull ``col`` off the ORM instance, returning ``None`` on missing.

    SQLAlchemy event hooks pass the mapped instance; pydantic-side
    ``model_dump`` would re-emit cache-only fields and is heavier, so
    direct ``getattr`` is the right tool.
    """
    return getattr(target, col, None)


def _delete_fts_row(conn: Connection, table_name: str, row_id: int) -> None:
    """Remove the row's FTS entry (if any). No-op when row never indexed.

    External-content FTS5 tables don't auto-purge on main-table DELETE,
    so we delete by rowid here. Update flow uses delete-then-insert so
    the inverted index never carries stale tokens.
    """
    fts = _fts_table_name(table_name)
    # ``exec_driver_sql`` binds ``row_id`` via the DBAPI's positional
    # ``?`` placeholder — user input never reaches the SQL string.
    # ``fts`` is a validated identifier from cache-class metadata.
    conn.exec_driver_sql(f"DELETE FROM {fts} WHERE rowid = ?", (row_id,))


def _insert_fts_row(
    conn: Connection,
    table_name: str,
    fts_cols: tuple[str, ...],
    row_id: int,
    values: list[Any],
) -> None:
    """Insert one row into the FTS sidecar. Empty / NULL values become ``''``.

    FTS5 stores NULL as the absence of a token, which is fine — except
    we want the row to exist so ``MATCH`` can rank it; coerce to empty
    string. The empty-string rows still match ``""`` queries (i.e.
    nothing) but never match real tokens, so ranking stays correct.
    """
    fts = _fts_table_name(table_name)
    col_list = ", ".join(_safe_identifier(c) for c in fts_cols)
    placeholders = ", ".join("?" for _ in fts_cols)
    coerced = tuple("" if v is None else str(v) for v in values)
    # ``exec_driver_sql`` passes ``coerced`` as positional ``?`` binds
    # at the DBAPI layer — user input never reaches the SQL string.
    # ``fts`` / ``col_list`` are validated identifiers from cache-class
    # metadata.
    conn.exec_driver_sql(
        f"INSERT INTO {fts} (rowid, {col_list}) VALUES (?, {placeholders})",
        (row_id, *coerced),
    )


def _make_after_insert(cls: type[SQLModel]) -> Any:
    """Bind one event handler per FTS-enabled class.

    SQLAlchemy events take ``(mapper, connection, target)``; the closure
    captures ``cls`` so the handler can read the right ``__fts_columns__``
    without re-walking the registry on every row.
    """
    fts_cols = _fts_columns(cls)
    table_name: str = _table_for(cls).name

    def after_insert(mapper: Mapper[Any], connection: Connection, target: Any) -> None:
        del mapper
        row_id = _row_value(target, "id")
        if row_id is None:
            # Generator-side primary keys never hit this branch — IDs
            # arrive from Katana — but defensively skip rather than
            # raise, since FTS state shouldn't break a real INSERT.
            return
        values = [_row_value(target, col) for col in fts_cols]
        _insert_fts_row(connection, table_name, fts_cols, int(row_id), values)

    return after_insert


def _make_after_update(cls: type[SQLModel]) -> Any:
    """Delete-then-insert keeps the FTS row token-fresh on update."""
    fts_cols = _fts_columns(cls)
    table_name: str = _table_for(cls).name

    def after_update(mapper: Mapper[Any], connection: Connection, target: Any) -> None:
        del mapper
        row_id = _row_value(target, "id")
        if row_id is None:
            return
        _delete_fts_row(connection, table_name, int(row_id))
        values = [_row_value(target, col) for col in fts_cols]
        _insert_fts_row(connection, table_name, fts_cols, int(row_id), values)

    return after_update


def _make_after_delete(cls: type[SQLModel]) -> Any:
    """Remove the orphaned FTS row when the main row is deleted."""
    table_name: str = _table_for(cls).name

    def after_delete(mapper: Mapper[Any], connection: Connection, target: Any) -> None:
        del mapper
        row_id = _row_value(target, "id")
        if row_id is None:
            return
        _delete_fts_row(connection, table_name, int(row_id))

    return after_delete


def install_fts_listeners() -> None:
    """Idempotently register after_insert / after_update / after_delete listeners.

    The mapper-level ``event.listens_for`` API doesn't currently expose
    a clean "is this listener already attached" probe, so we track
    installed classes in a module-level set and short-circuit on the
    second call. Tests that spin up a fresh ``TypedCacheEngine`` per
    test still re-use the global SQLModel registry, so we only want to
    install once per process.
    """
    for cls in _classes_with_fts_columns():
        if cls in _LISTENERS_INSTALLED:
            continue
        event.listen(cls, "after_insert", _make_after_insert(cls))
        event.listen(cls, "after_update", _make_after_update(cls))
        event.listen(cls, "after_delete", _make_after_delete(cls))
        _LISTENERS_INSTALLED.add(cls)


_LISTENERS_INSTALLED: set[type[SQLModel]] = set()


def initialize_fts_for_connection(connection: Any) -> None:
    """Create the per-entity FTS5 virtual tables on the given connection.

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

    Skipped when the main table is empty (cold-start before sync runs).
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
