# Catalog Search in the Typed Cache

How `search_items` and `search_customers` actually work, end to end — from the MCP tool
surface down to SQLite triggers. Read [architecture.md](../architecture.md) first for
the structural overview; this recipe focuses on the behavior a contributor needs when
adding a search-backed tool, debugging a "0 results" report, or understanding what
changed in [#472](https://github.com/dougborg/katana-openapi-client/issues/472).

## The 30-second summary

```
search_items({"query": "00.7018.581.003"})
  └─► services.typed_cache.catalog.smart_search(CachedMaterial, "00.7018.581.003")
        ├─► tokenize via re.split(r"\W+", ...)           →  ["00", "7018", "581", "003"]
        ├─► FTS5 MATCH on material_fts                   →  "00"* AND "7018"* AND "581"* AND "003"*
        │   (matches material_fts.supplier_item_codes_text)
        └─► no hits or fts5: syntax error                →  fall through to search_fuzzy
                                                            (difflib via helpers/search.score_match)
```

Per-entity FTS5 virtual tables (`variant_fts`, `customer_fts`, …) sit alongside the
typed cache tables and are kept in lock-step via SQLite triggers. The `CatalogQueries`
adapter at `services.typed_cache.catalog` exposes typed read methods returning `Cached*`
SQLModel instances with default `include_archived=False` / `include_deleted=False`
filters.

## Smart_search internals

`CatalogQueries.smart_search(cls, query, ...)` is the entry point. Implementation lives
at `katana_mcp_server/src/katana_mcp/typed_cache/queries.py`.

### Tokenizer

```python
_TOKEN_RE = re.compile(r"\W+")

def _tokenize_query(query: str) -> list[str]:
    return [tok for tok in _TOKEN_RE.split(query.strip()) if tok]
```

The legacy `CatalogCache` used `query.split()`, which only splits on whitespace. For a
SKU-shaped query like `00.4021.018.003` that produced a single token. FTS5's default
`unicode61` tokenizer would split the *indexed content* on dots — so the query token
never lined up with any index token, and the search returned zero results.

Splitting on `\W+` mirrors how FTS5 tokenized the content, so query tokens line up with
index tokens. This is the
[#471](https://github.com/dougborg/katana-openapi-client/issues/471) /
[#473](https://github.com/dougborg/katana-openapi-client/issues/473) fix that #472
absorbed.

### MATCH expression

Each token becomes a prefix-match clause, ANDed:

```
tokens = ["fox", "fork"]            →  "fox"* AND "fork"*
tokens = ["00", "7018", "581"]      →  "00"* AND "7018"* AND "581"*
```

The implementation in `_build_fts_match` double-quote-escapes each token to protect
against tokens that happen to look like FTS5 keywords (`AND`, `NEAR`, etc.). Ranking is
BM25 (`ORDER BY bm25(<entity>_fts)`), highest signal first.

### Fall-through to fuzzy

```python
try:
    rows = conn.exec_driver_sql(match_sql, params).fetchall()
except OperationalError as exc:
    if not _is_fts_syntax_error(exc):
        raise  # genuine OperationalError (locked DB, missing table) — propagate
    rows = []
if not rows:
    return await self.search_fuzzy(cls, query, limit=limit, ...)
```

Two conditions trigger the fuzzy fall-through:

1. **FTS5 returned zero hits.** Common for partial matches, typos, or queries that
   tokenize to an empty list (e.g., a query of only punctuation).
1. **FTS5 raised an `OperationalError` whose underlying `orig` message starts with
   `fts5: syntax error` or `fts5: unknown`.** This is narrow on purpose — other
   `OperationalError`s (locked DB, missing FTS table, disk I/O) propagate so operators
   see real failures instead of degraded-but-silent search.

The narrowing is done via `str(exc.orig).startswith(...)`. `str(exc)` would include
SQLAlchemy's wrapper decoration `(builtins.Exception) ... [SQL: ...]` and make the
prefix match unreliable.

### Fuzzy scoring

`search_fuzzy` loads candidate rows and ranks them via
`katana_public_api_client.helpers.search.score_match` — the same difflib-based scorer
the legacy cache used. Field weights match the legacy convention:

| Field role           | Weight |
| -------------------- | ------ |
| `sku` (variants)     | 100    |
| Primary name         | 30     |
| Secondary descriptor | 20     |

(`_FUZZY_WEIGHT_SKU` / `_FUZZY_WEIGHT_PRIMARY` / `_FUZZY_WEIGHT_SECONDARY` in
`queries.py`.) Only `CachedVariant` carries a SKU column; for everything else the SKU
bucket stays empty and ranking falls back to the primary/secondary weighting.

## The FTS5 sidecar

`katana_mcp_server/src/katana_mcp/typed_cache/fts.py` is the source-of-truth for the FTS
lifecycle. Two responsibilities: creating the virtual tables and keeping them in sync
with their content tables.

### Per-entity virtual tables

Each `Cached*` class with FTS coverage declares a class-level
`__fts_columns__: ClassVar[tuple[str, ...]]` injected by the generator
(`inject_fts_columns` pass driven by `CACHE_FTS_SPECS` in
`scripts/generate_pydantic_models.py`). At engine open, `_create_fts_tables_ddl` walks
the registered subclasses and emits:

```sql
CREATE VIRTUAL TABLE IF NOT EXISTS variant_fts USING fts5(
    sku, display_name, parent_name,
    supplier_item_codes_text, internal_barcode, registered_barcode,
    content='variant', content_rowid='id'
);
```

`content='<table>' content_rowid='id'` makes this an **external-content** FTS5 table —
it stores the inverted index but not the columns themselves. The index points back at
the content table by `rowid = id`. That's why every FTS-enabled cache class needs an
`id` primary key.

Coverage today (`CACHE_FTS_SPECS`):

| Class            | FTS columns                                                                                                |
| ---------------- | ---------------------------------------------------------------------------------------------------------- |
| `CachedVariant`  | `sku`, `display_name`, `parent_name`, `supplier_item_codes_text`, `internal_barcode`, `registered_barcode` |
| `CachedProduct`  | `name`, `category_name`                                                                                    |
| `CachedMaterial` | `name`, `category_name`                                                                                    |
| `CachedService`  | `name`                                                                                                     |
| `CachedCustomer` | `name`, `email`, `phone`                                                                                   |
| `CachedSupplier` | `name`, `code`, `email`, `phone`                                                                           |

Lookup-only types (`CachedLocation`, `CachedTaxRate`, `CachedOperator`, `CachedFactory`,
`CachedAdditionalCost`) skip FTS — `get_all` + `score_match` fuzzy is plenty for
catalogs that small.

### Why SQLite triggers, not SQLAlchemy mapper events

The original Phase B spike wired `after_insert` / `after_update` / `after_delete` mapper
events. CI was green. A reviewer caught the bug: the typed-cache sync path uses
`_bulk_upsert` (`typed_cache/sync.py:213`), which issues `INSERT ... ON CONFLICT` via
SQLAlchemy Core — **not** ORM-level `session.add()`. Core statements **do not fire
mapper events**.

So every fresh MCP server startup followed by its first sync would leave the FTS
inverted index empty. `smart_search` would silently return zero results until a manual
rebuild ran. In tests this was hidden because the test fixtures used `session.add()`
(the ORM path) and never exercised cold-start through the bulk path.

The fix is SQLite triggers on the content tables:

```sql
CREATE TRIGGER variant_ai AFTER INSERT ON variant BEGIN
    INSERT INTO variant_fts(rowid, sku, display_name, ...)
    VALUES (new.id, new.sku, new.display_name, ...);
END;

CREATE TRIGGER variant_au AFTER UPDATE ON variant BEGIN
    INSERT INTO variant_fts(variant_fts, rowid, ...) VALUES('delete', old.id, ...);
    INSERT INTO variant_fts(rowid, sku, display_name, ...)
    VALUES (new.id, new.sku, new.display_name, ...);
END;

CREATE TRIGGER variant_ad AFTER DELETE ON variant BEGIN
    INSERT INTO variant_fts(variant_fts, rowid, ...) VALUES('delete', old.id, ...);
END;
```

Triggers fire for every write mode SQLite supports — ORM `session.add()`, Core
`INSERT ... ON CONFLICT`, raw `exec_driver_sql`, even a future migration helper issuing
`text(...)` SQL. That's the SQLite-recommended pattern for external- content FTS5 and is
what the typed cache uses now.

The regression test that would have caught the original bug is
`test_ensure_variants_synced_populates_fts_index` in
`katana_mcp_server/tests/test_typed_cache_catalog.py` — it cold-starts the cache via the
bulk-upsert path and asserts that `smart_search` returns the seeded rows. Add an
equivalent test whenever you wire a new entity into the FTS sidecar.

## Variant denormalization

FTS5 can't JOIN. The `variant_fts` virtual table sees only the columns on
`CachedVariant` itself — so any field a caller would reasonably search by needs to live
there directly. The wire `Variant` schema doesn't carry several of those fields; the
typed-cache sync lifts them via `EntitySpec.attrs_postprocess`.

The relevant hook is `_variant_postprocess` in `typed_cache/sync.py`:

```python
def _variant_postprocess(attrs_obj: Any, cache_row: CachedVariant) -> None:
    parent = unwrap_unset(attrs_obj.product_or_material, None)
    if parent is not None:
        cache_row.parent_archived_at = unwrap_unset(
            getattr(parent, "archived_at", None), None
        )
        cache_row.parent_name = unwrap_unset(getattr(parent, "name", None), None)

    display_parts = [parent_name] if parent_name else [sku] if sku else []
    # ...append variant config_attributes...
    cache_row.display_name = " / ".join(display_parts) if display_parts else None

    codes = unwrap_unset(attrs_obj.supplier_item_codes, [])
    cache_row.supplier_item_codes_text = " ".join(codes) if codes else None
```

The four cache-only fields on `CachedVariant`:

| Field                      | Source                                               | Why it's denormalized                                                        |
| -------------------------- | ---------------------------------------------------- | ---------------------------------------------------------------------------- |
| `parent_archived_at`       | `product_or_material.archived_at` (extended payload) | Filter archived variants out of search without a JOIN                        |
| `parent_name`              | `product_or_material.name`                           | Search hits via parent name                                                  |
| `display_name`             | `parent.name` + variant `config_attributes`          | Human-readable result rendering                                              |
| `supplier_item_codes_text` | `" ".join(supplier_item_codes)`                      | FTS5 tokenizes whitespace-separated text; a list field wouldn't be indexable |

The variant `EntitySpec` declares `depends_on=("product", "material")` so the parent
records exist by the time the postprocess hook reads them. Cold-start ordering — parents
before children — is the responsibility of the caller (today, `ensure_variants_synced`
explicitly `asyncio.gather`s product+material syncs before running the variant sync);
`depends_on` is documentation + a future scheduler hook (see
`_validate_dependency_graph`).

## Soft-state filtering

The `CatalogQueries` adapter defaults to filtering archived and soft-deleted rows from
every read. This is a behavior change from the legacy `CatalogCache`, which returned
every row regardless. The defaults match what the agent layer almost always wants —
surface live catalog only — and the kwargs are there for the rare exception (e.g.,
`modify_item` resolving an archived row to unarchive it).

```python
# Default: surface only live rows.
variant = await catalog.get_by_sku("FOX-FORK-160")

# Opt in to archived parents (variant with archived product/material).
variant = await catalog.get_by_sku("FOX-FORK-160", include_archived=True)

# Opt in to soft-deleted customers.
customer = await catalog.get_by_id(CachedCustomer, 42, include_deleted=True)
```

Filtering is implemented generically via `hasattr(cls, "<col>")` checks at query-build
time (see `_archive_col_name` and `_has_deleted_column` in `queries.py`). Adding a new
`Cached*` sibling that carries `archived_at` or `deleted_at` works without any adapter
changes — the filter logic picks the column up automatically.

Per-entity soft-state surface map (from the inheritance audit in #472's plan):

| Class                      | `archived_at` | `deleted_at` (own) | `parent_archived_at` (cache-only) |
| -------------------------- | :-----------: | :----------------: | :-------------------------------: |
| `CachedVariant`            |       —       |         ✓          |                 ✓                 |
| `CachedProduct`/`Material` |       ✓       |         —          |                 —                 |
| `CachedService`            |       ✓       |         ✓          |                 —                 |
| `CachedCustomer`           |       —       |         ✓          |                 —                 |
| `CachedSupplier`           |       —       |         ✓          |                 —                 |
| `CachedOperator`           |       —       |         ✓          |                 —                 |
| `CachedAdditionalCost`     |       —       |         ✓          |                 —                 |
| `CachedTaxRate`            |       —       |         —          |                 —                 |
| `CachedLocation`           |       —       |         —          |                 —                 |
| `CachedFactory`            |       —       |         —          |                 —                 |

`include_archived=True` / `include_deleted=True` are no-ops for classes that don't carry
the relevant column.

## Worked examples

The tests in `katana_mcp_server/tests/test_typed_cache_catalog.py` pin these behaviors.
Reach for them when you change anything in `queries.py` or `fts.py`.

### UPC scan via `registered_barcode`

```python
hits = await catalog.smart_search(CachedVariant, "710845916762")
# → [CachedVariant(sku="FOX-FORK-FACTORY-29-160", registered_barcode="710845916762", ...)]
```

Tokenize: `["710845916762"]`. Match: `"710845916762"*`. Hits `variant_fts` via the
`registered_barcode` column. BM25 ranks the exact-prefix match first.

### Supplier item code

```python
hits = await catalog.smart_search(CachedMaterial, "00.7018.581.003")
# → [CachedMaterial(name="SRAM PG-1170 cassette", ...)]
```

Tokenize: `["00", "7018", "581", "003"]`. Match:
`"00"* AND "7018"* AND "581"* AND "003"*`. The material's `supplier_item_codes_text`
column carries the space-joined supplier codes; all four tokens hit prefixes there.

This is the [#473](https://github.com/dougborg/katana-openapi-client/issues/473) repro
that lived in the cowork retro. It only works because the tokenizer splits on `\W+`;
with the legacy `query.split()` the whole string was one unmatchable token.

### Multi-token natural-language

```python
hits = await catalog.smart_search(CachedProduct, "kitchen knife")
# → BM25-ranked products with "kitchen" and "knife" appearing in name/category_name
```

Tokenize: `["kitchen", "knife"]`. Match: `"kitchen"* AND "knife"*`. Behavior unchanged
from the legacy cache — multi-token AND with prefix expansion.

### Syntax-error fall-through

```python
hits = await catalog.smart_search(CachedVariant, "AND OR NOT")
# → falls through to search_fuzzy; returns whatever difflib scores best
```

Tokenize produces tokens that, after FTS5 sees them, form an invalid match expression.
FTS5 raises `OperationalError("fts5: syntax error near ...")`. `_is_fts_syntax_error`
returns `True`; `search_fuzzy` runs.

A `LockedError` or `OperationalError("no such table: ...")` would **not** match the
prefix check and would propagate. That's the design — silent fall-through is reserved
for the recoverable case.

## Where to look

- **Implementation** — `katana_mcp_server/src/katana_mcp/typed_cache/queries.py`,
  `.../fts.py`, `.../sync.py`.
- **Generator** — `scripts/generate_pydantic_models.py`: `CACHE_FTS_SPECS`,
  `inject_fts_columns`.
- **Tests** — `katana_mcp_server/tests/test_typed_cache_catalog.py` covers the full
  surface (round-trip sync, FTS triggers, smart_search semantics, fall-through,
  soft-state filtering).
- **Architecture overview** — [architecture.md](../architecture.md) §Cache.
- **Decision record** — [ADR-0018](../adr/0018-sqlmodel-typed-cache.md) for the
  typed-cache foundation, ADR-0018 status footer for the #472 unification.
