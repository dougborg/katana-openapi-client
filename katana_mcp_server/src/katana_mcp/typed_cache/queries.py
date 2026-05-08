"""``CatalogQueries`` adapter — typed read API over ``TypedCacheEngine`` (#472 Phase B).

Phase D will migrate ~33 ``services.cache.<method>`` call sites onto this
adapter. Until then it ships unused except by Phase B's own tests, but
it's the single place where the new typed-cache search semantics — the
SKU-shaped tokenizer fix, the FTS-syntax-error fall-through to fuzzy,
and the default ``include_archived=False`` / ``include_deleted=False``
filters — converge.

The legacy ``CatalogCache`` returned ``dict[str, Any]`` rows. This
adapter returns the typed ``Cached*`` SQLModel instances directly, so
callers go from ``variant["sku"]`` to ``variant.sku``. Larger Phase D
diff per-site, but the end state is fully typed.

Soft-state filtering rules (per the inheritance map in the plan):

- ``CachedVariant`` — ``deleted_at`` (own) + ``parent_archived_at``
  (cache-only, lifted from parent). Filters: ``deleted_at IS NULL``
  unless ``include_deleted=True``; ``parent_archived_at IS NULL``
  unless ``include_archived=True``.
- ``CachedProduct`` / ``CachedMaterial`` — ``archived_at``. Filter
  unless ``include_archived=True``.
- ``CachedService`` — both ``archived_at`` and ``deleted_at``. Filter
  both.
- ``CachedCustomer`` / ``CachedSupplier`` / ``CachedOperator`` /
  ``CachedAdditionalCost`` — ``deleted_at``. Filter unless
  ``include_deleted=True``.
- ``CachedTaxRate`` / ``CachedLocation`` / ``CachedFactory`` — neither;
  the kwargs are no-ops.

Filtering is implemented generically via ``hasattr(cls, "<col>")``
checks at query-build time so the rules stay in one place and adding
a new ``Cached*`` sibling is hands-off.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, TypeVar

from sqlalchemy.exc import OperationalError
from sqlmodel import SQLModel, select

from katana_public_api_client.helpers.search import score_match
from katana_public_api_client.models_pydantic._generated import CachedVariant

from .fts import (
    _fts_columns as _fts_columns_for,
    _safe_identifier,
)

if TYPE_CHECKING:
    from .engine import TypedCacheEngine


T = TypeVar("T", bound=SQLModel)

# Field weights match the legacy ``CatalogCache.search_fuzzy``: SKU
# carries the most signal, primary name next, secondary descriptor (cat
# name / parent name) last. Only Variant has a SKU column; everything
# else uses the fuzzy fallback's "primary name + secondary text"
# weighting and the SKU bucket stays empty.
_FUZZY_WEIGHT_SKU = 100
_FUZZY_WEIGHT_PRIMARY = 30
_FUZZY_WEIGHT_SECONDARY = 20

# Tokenizer for FTS5 MATCH-clause synthesis. The legacy cache used
# ``query.split()`` which broke on SKU-shaped queries (``00.4021.018.003``
# tokenizes to a single token, then FTS's tokenizer drops the dots and
# the token never matches). Splitting on ``\W+`` here mirrors how FTS5's
# default unicode61 tokenizer would have split the *content*, so query
# tokens line up with index tokens.
_TOKEN_RE = re.compile(r"\W+")


def _tokenize_query(query: str) -> list[str]:
    """Split a search query into FTS5 prefix-AND tokens."""
    return [tok for tok in _TOKEN_RE.split(query.strip()) if tok]


def _build_fts_match(tokens: list[str]) -> str:
    """Build an FTS5 MATCH expression: ``"tok1"* AND "tok2"* AND ...``.

    Quoting each token isolates user-supplied punctuation from FTS5
    operator syntax (``OR``, ``NOT``, etc. become literal tokens, not
    operators). The ``*`` suffix turns each token into a prefix match
    so partial typing (``kitch`` matches ``kitchen``) still works.
    """
    escaped = [tok.replace('"', '""') for tok in tokens]
    return " AND ".join(f'"{tok}"*' for tok in escaped)


def _pk_col(cls: type[SQLModel]) -> Any:
    """Return the SQLAlchemy InstrumentedAttribute for ``cls.id``.

    Every ``Cached*`` class has an ``id`` integer PK, but the static
    checker can't narrow ``getattr`` through the ``T`` TypeVar. Centralize
    the reach so the ``# noqa: B009`` lives in one place.
    """
    return getattr(cls, "id")  # noqa: B009


def _archive_col_name(cls: type[SQLModel]) -> str | None:
    """Return the cache column tracking archive state, or ``None`` if absent.

    Variants don't carry their own archive lifecycle on the wire — Katana
    archives at the parent (Product / Material) level — so the cache
    class denormalizes ``parent_archived_at`` from the extended payload.
    Every other class uses its own ``archived_at`` if present.
    """
    if cls is CachedVariant:
        return "parent_archived_at"
    if hasattr(cls, "archived_at"):
        return "archived_at"
    return None


def _has_deleted_column(cls: type[SQLModel]) -> bool:
    """True iff the class has a ``deleted_at`` column we should filter by."""
    return hasattr(cls, "deleted_at")


def _apply_soft_state_filters(
    stmt: Any,
    cls: type[SQLModel],
    *,
    include_archived: bool,
    include_deleted: bool,
) -> Any:
    """Layer ``WHERE archived_at IS NULL`` / ``deleted_at IS NULL`` on a SELECT.

    The two flags compose: a row that's both archived and deleted is
    dropped unless both ``include_*`` are True. Centralized here so the
    rules can't drift between ``get_*`` / ``smart_search`` / ``search_fuzzy``.

    ``getattr`` keeps the static checker happy across catalog classes
    that don't share an inheritance ancestor for archive/delete columns.
    """
    if not include_archived:
        archive_col = _archive_col_name(cls)
        if archive_col is not None:
            stmt = stmt.where(getattr(cls, archive_col).is_(None))
    if not include_deleted and _has_deleted_column(cls):
        stmt = stmt.where(getattr(cls, "deleted_at").is_(None))  # noqa: B009
    return stmt


def _row_score_fields(row: SQLModel) -> dict[str, tuple[str, int]]:
    """Build the ``score_match`` field dict for fuzzy-fallback ranking.

    Field weights mirror the legacy cache (sku=100, name=30, name2=20)
    so callers don't see scoring drift during the Phase D migration.

    Variant: SKU + display_name + parent_name. Everything else: lift
    the first FTS column as the primary name, the second (if any) as
    the secondary descriptor (category / email / etc.), no SKU bucket.
    """
    if isinstance(row, CachedVariant):
        return {
            "sku": (row.sku or "", _FUZZY_WEIGHT_SKU),
            "display_name": (row.display_name or "", _FUZZY_WEIGHT_PRIMARY),
            "parent_name": (row.parent_name or "", _FUZZY_WEIGHT_SECONDARY),
        }
    fts_cols = _fts_columns_for(type(row))
    # For FTS-enabled classes (Product, Material, Service, Customer,
    # Supplier), score against the declared FTS columns. For lookup-
    # only classes without FTS (TaxRate, Operator, Location, Factory,
    # AdditionalCost), fall back to scoring against ``name`` /
    # ``operator_name`` so smart_search degrades to a useful fuzzy
    # match instead of always returning zero.
    fields: dict[str, tuple[str, int]] = {}
    if fts_cols:
        primary_col = fts_cols[0]
        primary_value = getattr(row, primary_col, None) or ""
        fields[primary_col] = (str(primary_value), _FUZZY_WEIGHT_PRIMARY)
        if len(fts_cols) > 1:
            secondary_col = fts_cols[1]
            secondary_value = getattr(row, secondary_col, None) or ""
            fields[secondary_col] = (str(secondary_value), _FUZZY_WEIGHT_SECONDARY)
        return fields

    # No FTS columns declared — pick the most-likely "name" field. The
    # SQLModel-attribute lookup is defensive: every catalog Cached*
    # class has either ``name`` or (Operator) ``operator_name``.
    for col in ("name", "operator_name", "display_name"):
        value = getattr(row, col, None)
        if value:
            fields[col] = (str(value), _FUZZY_WEIGHT_PRIMARY)
            break
    return fields


class CatalogQueries:
    """Typed read API for the catalog tier of ``TypedCacheEngine``.

    Phase B introduces the adapter; Phase D migrates ~33 call sites
    onto it. Each method ships with the legacy semantics preserved
    *except* for the two papercut fixes called out in the plan:

    1. ``smart_search`` tokenizes via ``re.split(\\W+, ...)`` instead of
       ``query.split()`` so SKU-shaped queries with ``.`` separators
       (``00.4021.018.003``) tokenize correctly.
    2. ``smart_search`` falls back to ``search_fuzzy`` on **both**
       empty results AND ``OperationalError`` (FTS5 syntax error). The
       legacy cache only fell through on empty results, so a syntactically
       invalid query (e.g., unbalanced parens) returned nothing.

    The third user-visible change is **default ``include_archived=False``
    / ``include_deleted=False`` on every read method**. The legacy
    ``get_by_id`` / ``get_by_sku`` / ``get_many_by_ids`` returned soft-
    deleted and archived rows unconditionally; callers that need them
    pass the flag explicitly. This is the right default — the old
    behavior leaked archived rows into search-result expansions.
    """

    def __init__(self, engine: TypedCacheEngine) -> None:
        self._engine = engine

    async def get_by_id(
        self,
        cls: type[T],
        entity_id: int,
        *,
        include_archived: bool = False,
        include_deleted: bool = False,
    ) -> T | None:
        """Fetch one row by primary key, honoring soft-state filters."""
        stmt = select(cls).where(_pk_col(cls) == entity_id)
        stmt = _apply_soft_state_filters(
            stmt,
            cls,
            include_archived=include_archived,
            include_deleted=include_deleted,
        )
        async with self._engine.session() as session:
            result = await session.exec(stmt)
            return result.first()

    async def get_by_sku(
        self,
        sku: str,
        *,
        include_archived: bool = False,
        include_deleted: bool = False,
    ) -> CachedVariant | None:
        """Variant-only SKU lookup, case-insensitive (NOCASE collation).

        The legacy cache's ``entity_index.sku`` had a non-unique index
        with NOCASE collation; we apply NOCASE at query time so the
        cache's main-table column doesn't need to commit to a
        collation choice. ``func.lower``-style coercion would also work
        but ``COLLATE NOCASE`` is the SQLite-native answer.
        """
        sku_col: Any = CachedVariant.sku
        stmt = select(CachedVariant).where(sku_col.collate("NOCASE") == sku)
        stmt = _apply_soft_state_filters(
            stmt,
            CachedVariant,
            include_archived=include_archived,
            include_deleted=include_deleted,
        )
        async with self._engine.session() as session:
            result = await session.exec(stmt)
            return result.first()

    async def get_many_by_ids(
        self,
        cls: type[T],
        entity_ids: Iterable[int],
        *,
        include_archived: bool = False,
        include_deleted: bool = False,
    ) -> dict[int, T]:
        """Batch-fetch by ID; returns ``{id: row}`` for hits, drops misses.

        Empty input is a no-op (no DB round-trip). IDs are deduplicated
        before the IN-clause to keep the parameter list tight on shops
        with batched-row enrichment that may double up on parent IDs.
        """
        ids = list({int(i) for i in entity_ids})
        if not ids:
            return {}
        stmt = select(cls).where(_pk_col(cls).in_(ids))
        stmt = _apply_soft_state_filters(
            stmt,
            cls,
            include_archived=include_archived,
            include_deleted=include_deleted,
        )
        async with self._engine.session() as session:
            result = await session.exec(stmt)
            rows = result.all()
        return {int(getattr(row, "id")): row for row in rows}  # noqa: B009

    async def get_all(
        self,
        cls: type[T],
        *,
        include_archived: bool = False,
        include_deleted: bool = False,
    ) -> list[T]:
        """Fetch every row of ``cls`` honoring soft-state filters.

        Used for small reference tables (locations, tax rates) where
        the entire set fits in memory and callers want the bulk pull
        in one round trip.
        """
        stmt = select(cls)
        stmt = _apply_soft_state_filters(
            stmt,
            cls,
            include_archived=include_archived,
            include_deleted=include_deleted,
        )
        async with self._engine.session() as session:
            result = await session.exec(stmt)
            return list(result.all())

    async def smart_search(
        self,
        cls: type[T],
        query: str,
        limit: int = 50,
        *,
        include_archived: bool = False,
        include_deleted: bool = False,
    ) -> list[T]:
        """FTS5-first search with fuzzy fallback on empty / FTS syntax error.

        Tokenizes via ``re.split(\\W+, ...)`` so SKU-shaped queries
        (``00.4021.018.003``) tokenize the same way FTS5's default
        tokenizer indexed them — single-token text projections like
        ``supplier_item_codes_text`` ("00 4021 018 003") see each
        chunk as a separate term and the prefix-AND match clicks.

        Two papercut fixes vs. the legacy ``CatalogCache.smart_search``:

        1. Empty / blank query short-circuits to an empty list (no
           sense pretending an FTS5 ``MATCH ''`` query was meaningful).
        2. FTS5 ``OperationalError`` (e.g., unbalanced parens, reserved-
           word collision) falls through to ``search_fuzzy`` rather
           than raising. The legacy implementation caught it and
           returned an empty list silently — same shape, but never
           actually offered the user fuzzy results for a malformed
           query. Now we always offer them.
        """
        stripped = query.strip()
        if not stripped:
            return []

        async def _fuzzy() -> list[T]:
            return await self.search_fuzzy(
                cls,
                query,
                limit=limit,
                include_archived=include_archived,
                include_deleted=include_deleted,
            )

        fts_cols = _fts_columns_for(cls)
        if not fts_cols:
            # No FTS sidecar for this entity type — the only sensible
            # fallback is fuzzy.
            return await _fuzzy()

        tokens = _tokenize_query(stripped)
        if not tokens:
            return []

        fts_match = _build_fts_match(tokens)
        # ``__table__`` is set by the SQLModel metaclass on table=True
        # classes; ``Any`` cast keeps the static checker quiet on the
        # otherwise-untyped attribute (see also ``fts.py``).
        table_obj: Any = getattr(cls, "__table__")  # noqa: B009
        # ``_safe_identifier`` validates the cache-class metadata
        # against ``[A-Za-z_][A-Za-z0-9_]*`` before interpolation —
        # belt-and-suspenders against a future generator regression.
        table_name = _safe_identifier(table_obj.name)
        fts_table = f"{table_name}_fts"

        # Build the WHERE-clause filters as raw SQL since the FTS5
        # JOIN sits at the SQL level (FTS virtual tables don't have a
        # SQLModel-mapped class). The bound ``?`` placeholders keep
        # user input safely separated from query text.
        archive_clause = ""
        if not include_archived:
            col = _archive_col_name(cls)
            if col is not None:
                archive_clause = f" AND main.{_safe_identifier(col)} IS NULL"
        deleted_clause = ""
        if not include_deleted and _has_deleted_column(cls):
            deleted_clause = " AND main.deleted_at IS NULL"

        sql = (
            f"SELECT main.id FROM {fts_table} fts "
            f"JOIN {table_name} main ON main.id = fts.rowid "
            f"WHERE {fts_table} MATCH ?"
            f"{archive_clause}{deleted_clause} "
            f"ORDER BY bm25({fts_table}) "
            f"LIMIT ?"
        )

        try:
            async with self._engine.session() as session:
                # FTS5 virtual tables can't be expressed via the
                # SQLAlchemy ORM, and ``session.exec`` is typed for
                # SQLModel SELECT statements only — drop to
                # ``exec_driver_sql`` so user input flows through the
                # DBAPI's positional ``?`` binds. Identifiers
                # (``fts_table`` / ``table_name`` / archive+deleted
                # clauses) come from validated cache-class metadata.
                conn = await session.connection()
                cursor = await conn.exec_driver_sql(sql, (fts_match, limit))
                ids = [int(row[0]) for row in cursor.all()]
        except OperationalError:
            # FTS5 syntax error — surface fuzzy results so the user
            # gets *something* back rather than a silent empty list.
            return await _fuzzy()

        if not ids:
            # Empty FTS result set: try fuzzy in case the user typed a
            # near-match (``stainles`` → ``stainless``). The legacy
            # cache had this same fall-through.
            return await _fuzzy()

        # Re-fetch the typed objects in a single round trip, preserving
        # the bm25 order from the FTS query. Build an ID->row map then
        # iterate the original ID order.
        rows_by_id = await self.get_many_by_ids(
            cls,
            ids,
            include_archived=include_archived,
            include_deleted=include_deleted,
        )
        return [rows_by_id[rid] for rid in ids if rid in rows_by_id]

    async def search_fuzzy(
        self,
        cls: type[T],
        query: str,
        limit: int = 50,
        *,
        include_archived: bool = False,
        include_deleted: bool = False,
    ) -> list[T]:
        """Difflib-backed fuzzy search using ``score_match``.

        Pulls every (filtered) row in one query, scores in Python
        against the entity's FTS columns, returns the top ``limit``.
        Cost scales with row count, so callers should prefer
        ``smart_search`` (which only falls through to fuzzy on empty
        FTS results / syntax errors).

        Field weights mirror the legacy cache (SKU=100, primary name=30,
        secondary=20) — see ``_row_score_fields``.
        """
        stripped = query.strip()
        if not stripped:
            return []

        rows = await self.get_all(
            cls,
            include_archived=include_archived,
            include_deleted=include_deleted,
        )

        scored: list[tuple[T, float]] = []
        for row in rows:
            score = score_match(query=stripped, fields=_row_score_fields(row))
            if score > 0:
                scored.append((row, score))

        scored.sort(key=lambda item: item[1], reverse=True)
        return [row for row, _score in scored[:limit]]
