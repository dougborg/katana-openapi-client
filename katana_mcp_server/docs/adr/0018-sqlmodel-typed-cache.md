# ADR-0018: SQLModel-backed typed cache for transactional list tools

## Status

Accepted

Date: 2026-04-23

## Context

Analytical workflows over Katana data were making large numbers of sequential API calls
— the motivating example filed as #342 was a "top-selling bikes" analysis that took 123
calls because every filter pass and every page of sales orders required a fresh API
round-trip. A related bug (#341) showed that client-side filters on
`list_stock_adjustments(variant_id=...)` could only scan the first server-returned page,
silently truncating results.

The server already has `katana_mcp.cache.CatalogCache` — a SQLite + FTS5 cache for the
10 reference entity types (variants, products, materials, services, suppliers,
customers, locations, tax_rates, operators, factories). It stores every entity in one
generic `entities` table with a skinny `entity_index` projection, uses incremental sync
via Katana's `updated_at_min` parameter, and works well for reference lookup
(`search_items`, `get_variant_details`, etc).

That generic-table pattern doesn't fit the transactional types (sales_orders,
manufacturing_orders, purchase_orders, stock_adjustments, stock_transfers):

- Filter needs are much richer — status, customer/supplier IDs, date ranges,
  variant-id-via-rows — and don't all fit into the three text columns `entity_index`
  exposes.
- Sub-entity queries like "sales orders containing variant X" require scanning line
  items, which aren't modeled in the generic table.
- The entities themselves have richer schemas (30+ fields each) that benefit from typed
  columns over opaque JSON blobs.

## Decision

Introduce a second cache alongside `CatalogCache`:
`katana_mcp.typed_cache.TypedCacheEngine`. Per-entity typed tables, generated from the
existing pydantic models via SQLModel, with proper parent-child relationships and FK
constraints. The two caches coexist during the per-entity rollout; the generic cache
retires once every reference type has migrated.

### Key architectural choices

#### Per-entity typed tables, not a widened generic schema

Transactional types aren't uniform — `sales_order.status` ≠
`manufacturing_order.production_status` ≠ `purchase_order.status`; some have
`delivered_at`, some have `expected_arrival`, some have `production_deadline`. Forcing
them into shared generic columns creates real schema smell. Typed tables read as
documentation of the domain.

#### SQLModel unifies the pydantic and SQLAlchemy layers ("Scope 1")

The generated pydantic layer at `katana_public_api_client/models_pydantic/_generated/`
now extends `SQLModel` (PR #361/#363). A curated registry of cache-target classes
(CACHE_TABLES in `scripts/generate_pydantic_models.py`) adds `table=True` plus
`Relationship()`/`foreign_key` annotations via AST post-processing on the pydantic
generator's output. One class serves two roles:

- **API response shape** — pydantic validation on `.from_attrs()`.
- **Cache row** — SQLAlchemy table with typed columns, indexes, FKs.

The attrs layer at `katana_public_api_client/models/` is unchanged; it stays the API
transport format. Scope 2 ("replace attrs too") was explicitly deferred — it would
rewrite every API function with UNSET semantics and earn no caching benefit.

#### Full schema as typed columns, no JSON blob release valve

Primitive fields → typed columns. Nested single objects and list children that need to
be queryable (e.g., `SalesOrder.sales_order_rows`) → child tables with FKs.
Polymorphic/shared collections that are low-signal for cache queries
(`SalesOrderRow.attributes`, `batch_transactions`, `serial_numbers`,
`SalesOrder.shipping_fee`, `SalesOrder.addresses`) → JSON columns via
`Field(sa_column=Column(JSON))`, keeping the typed pydantic interface but acknowledging
that normalizing them would explode the schema without query benefit. Tracked in
CACHE_JSON_COLUMNS.

#### Opportunistic sync, no cold-start preload

First tool call on a cold cache triggers the first full fetch; every subsequent call
does an incremental `updated_at_min=<last_synced>` sync. Steady-state incremental
returns near-zero rows and is cheap enough to run on every call — no debounce needed.
Avoids the complexity of a separate background sync thread.

#### Per-entity-type `asyncio.Lock`

Two concurrent tool calls must not both kick off a full cold-start fetch.
`TypedCacheEngine.lock_for(entity_type)` hands out a lazy-created `asyncio.Lock` per
type; sync helpers take it before any work.

#### Schema-version-bump rebuild, not Alembic

Cache data is derivable from the API — paying re-sync time on a schema change is
acceptable. The overhead of maintaining Alembic migrations isn't worth it while the
schema is still in flux. `schema_version` bumps (currently implicit via
SQLModel.metadata content) trigger drop + recreate on user machines. Revisit Alembic
when schema stabilizes and re-sync cost becomes painful.

#### Dual-cache coexistence during rollout

Both `CatalogCache` (legacy, generic) and `TypedCacheEngine` (new, per type) open on
server startup. Tools migrate one at a time as PRs land (`list_sales_orders` first, then
`list_manufacturing_orders`, etc.). Once every reference type has its own typed table,
the generic `entities`/`entity_index` schema retires in a follow-up epic. Two mental
models for one PR series' lifetime is acceptable — the alternative (big-bang
unification) would block caching value behind months of refactoring.

## Consequences

### Positive

- Variant-id queries against sales orders, adjustments, and transfers become SQL over
  the cache, not paginated API calls — unblocks #341.
- The "top-selling bikes" analysis (and any similar aggregation) should drop from ~123
  API calls to ~1-2 per run.
- Schema reads as documentation of the Katana API — no per-field guesswork about what's
  cached where.
- Write tools can upsert their response back into the cache directly, so consumers see
  fresh data without a forced re-sync.

### Negative

- Two caches in the codebase during the migration; contributors have to know which holds
  which entity type.
- SQLModel adds a non-trivial dep tree (sqlmodel → sqlalchemy → greenlet).
- `AwareDatetime` → `datetime` swap in generated table classes sacrifices pydantic's
  timezone-aware validator for SQLModel compatibility (Katana wire protocol guarantees
  tzinfo, so the validator was safety belt).
- Pre-existing cold-start time for a shop with large order history; first
  `list_sales_orders` after cache version bump may take a few minutes.

### Neutral

- AST-based regex transforms in the pydantic generator are brittle to output-format
  changes; flagged for a libcst migration if the transform pattern grows beyond ~5 more
  (memory: `feedback_regex_over_templates`).

## Related work

- #342 — this epic (cache-back transactional list tools)
- #341 — stock adjustment variant_id filter breadth (closed by future PR)
- #329/#330 — prior list-tool pattern v2 (limit, page, PaginationMeta)
- PR #361 — SQLModel foundation (base class swap)
- PR #363 — AST generator transforms (table=True, relationships, FKs)
- This ADR — cache runtime + first tool consumer
