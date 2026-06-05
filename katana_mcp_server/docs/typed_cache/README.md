# Typed Cache — Patterns and Pitfalls

The typed cache is a SQLite-backed mirror of Katana's wire state, with per-entity tables
(`product`, `material`, `supplier`, `manufacturing_order`, …) generated from the same
pydantic models the API client uses. It exists so MCP tools can serve queries without
round-tripping to Katana for every read, and so FTS5 fuzzy search has something to
index.

The rules below are about how the cache layer relates to the API layer (the spec, the
generated pydantic, the attrs models) — what belongs where, and what surprises bite when
those layers blur.

Related code:

- `katana_mcp_server/src/katana_mcp/typed_cache/sync.py` — attrs → API pydantic → cache
  pydantic conversion.
- `scripts/generate_pydantic_models.py` — emits both the API pydantic class and the
  sibling `Cached<Name>` class with `table=True` per entity. See
  `duplicate_cache_tables_as_cached_siblings`.

______________________________________________________________________

## Archive / deleted state — opt-in flags + derived booleans

Katana represents soft-state as nullable timestamps on the wire: `archived_at` (the
user-toggleable archive lifecycle — exposed on catalog items, inventory rows, and a few
other archivable entities) and `deleted_at` (soft-delete, exposed on most entities
including catalog items *and* transactional entities like POs, SOs, MOs, stock
transfers, stock adjustments). The two are independent — an entity can be both archived
and soft-deleted.

Two MCP-side conventions surface this; **keep them symmetric**:

### Query-param flags for opting into soft-state rows (default `False`)

Items use `include_archived` (`search_items`, catalog cache). After #472 Phase D the
canonical wiring is the typed cache's `CatalogQueries` adapter — `parent_archived_at` is
denormalized onto `CachedVariant` at sync time (via the variant `attrs_postprocess` hook
in `typed_cache/sync.py`) and the adapter's default `include_archived=False` /
`include_deleted=False` filters push the `archived_at IS NULL` / `deleted_at IS NULL`
predicates down to SQL.

Transactional entities use `include_deleted` on `list_purchase_orders` /
`list_sales_orders` / `list_manufacturing_orders` / `list_stock_adjustments`, filtering
at the same typed-cache query layer.

### Response-side derived booleans

Every response model that exposes `archived_at` / `deleted_at` should also expose a
convenience `is_archived` / `is_deleted` bool derived from `<timestamp> is not None`,
saving callers from the timestamp/null inspection.

**Note the asymmetry**: `is_archived` mirrors Katana's *write* convention
(`update_<entity>` request bodies accept `is_archived: bool`, so round-tripping through
`modify_<entity>` with `{"update_header": {"is_archived": false}}` works). `is_deleted`,
by contrast, is *read-side only* — Katana exposes deletion through DELETE endpoints, not
as a writable boolean on update bodies. Items expose `is_archived` on `ItemInfo` and
`ItemDetailsResponse` as of #526.

Don't add a new opt-in flag without the matching derived bool, and vice versa. The
shared `SoftDeletableResponse` mixin in `katana_mcp/tools/tool_result_utils.py` provides
the `deleted_at` + `is_deleted` field plumbing and the derivation validator — soft-
deletable response models inherit from it so the `is_deleted = deleted_at is not None`
mapping can't drift across files.

### Three categories of soft-state filtering — keep them separate

| Category                             | Default                 | Mechanism                      | Why                                                                                                                                                                             |
| ------------------------------------ | ----------------------- | ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Direct lookup** (SKU + ID getters) | `include_*=False`       | request flag on the tool       | the matched entity IS the answer; agent opts in to see soft-state rows. SKU lookups also use `get_by_sku`'s ORDER BY tiebreaker so a live row beats a deleted/archived sibling. |
| **List filtering** (`list_*` tools)  | `include_*=False`       | request flag; `CatalogQueries` | which parents appear in the list                                                                                                                                                |
| **Enrichment** (batch lookups by ID) | always `include_*=True` | no flag, hard-coded            | a deleted parent referenced from a live child must still render its identity — e.g. a live SO row referencing a deleted variant still needs to surface its display name         |

The distinction matters because SKUs are non-unique in Katana but IDs are. Direct SKU
lookups need the tiebreaker + the opt-out default (so a deleted-vs-live sibling resolves
to live). Enrichment by ID always wants the row regardless of soft state, because the
parent's response references it by ID and the renderer needs the identity.

______________________________________________________________________

## Cache IDs are not globally unique — never merge cross-entity maps by numeric ID alone

The typed cache stores each entity type in its own table (`product`, `material`,
`supplier`, …), so a product with `id=42` and a material with `id=42` are both legal.
When enriching a list of variants with parent context (or any other cross-entity batch
fetch), keep separate per-type maps (`products`, `materials`) and select based on which
ID the variant carries (`v.product_id` vs `v.material_id`).

Merging into a single dict via `{**products, **materials}` mis-attaches parents on
collision — Python dict-unpack iterates left-to-right and later keys win, so the
material entry silently overwrites the product entry on shared IDs. The bug is symmetric
in practice: every product variant whose ID also exists as a material ID looks up the
material's data instead (and vice versa if you reorder the unpack).

Caught in #542 (variant card redesign) by Copilot review; regression test pins the case
in `test_items.py::test_enrich_variants_keeps_product_and_material_maps_separate`.

______________________________________________________________________

## Don't pollute the API spec/models with cache-only fields

The OpenAPI spec at `docs/katana-openapi.yaml` and the generated pydantic models in
`katana_public_api_client/models_pydantic/_generated/*.py` reflect Katana's actual wire
contract. **Never** add fields to the spec or inject fields into the API pydantic
classes to satisfy cache-schema, MCP-tool, or other consumer needs.

Cache schemas live on sibling `Cached<Name>` classes emitted by the same generator pass
— the API class stays pure pydantic, the cache class carries `table=True`, foreign keys,
relationships, JSON columns, and any cache-only fields. See
`scripts/generate_pydantic_models.py::duplicate_cache_tables_as_cached_siblings` and
`katana_mcp_server/src/katana_mcp/typed_cache/sync.py::_attrs_<entity>_to_cached` for
the conversion pattern: attrs → API pydantic (via the registry) → cache pydantic (via
`model_dump`/`model_validate`), with relationship fields set after construction since
SQLModel `Relationship` descriptors don't accept input via `__init__`.

If a bug surfaces in `sync.py` but originates in generated client code (attrs, pydantic,
`from_attrs`, `Cached*` schemas), fix it at the generator/spec layer — not in `sync.py`.
See
[Fix bugs at the client/generator layer](../../../katana_public_api_client/docs/spec-authoring.md#fix-bugs-at-the-clientgenerator-layer-when-the-root-cause-lives-there)
in the spec-authoring guide.

______________________________________________________________________

## Cache-only columns written cross-table need preserve-on-conflict

A cache-only column is populated one of two ways, and the distinction is load-bearing:

- **From the entity's own wire payload**, during its conversion — via the
  `EntitySpec.attrs_postprocess` hook. Example: `CachedVariant.parent_archived_at` /
  `display_name` / `parent_name` / `supplier_item_codes_text`, all derived from the
  extended `/variants` payload in `_variant_postprocess`. These are **re-derived on
  every sync**, so the upsert naturally rewrites the correct value each time. No special
  handling needed.

- **From a *different* entity's sync** (cross-table), because the value doesn't exist on
  this entity's wire payload at all — via the source entity's `EntitySpec.post_sync`
  hook. Example: `CachedVariant.service_id` is backfilled by the **service** spec's
  `post_sync` (`_backfill_service_variant_links`), because the variant→service link
  lives only on `/services`, never on `/variants`.

The trap is in the second case. `_bulk_upsert` issues
`INSERT ... ON CONFLICT(id) DO UPDATE SET <every non-id column>`. When the owning entity
re-syncs, its payload has **no value** for the cross-table column, so the upsert writes
the column's default (`NULL`) — silently clobbering whatever the `post_sync` backfill
wrote. The column would then only be correct for the brief window between a
source-entity sync and the next owning-entity delta.

**The contract:** any cache-only column written by another entity's `post_sync` (not by
the owning entity's own payload) **must** be listed in the owning spec's
`preserve_columns_on_conflict`. `_bulk_upsert` excludes those columns from the
`ON CONFLICT DO UPDATE SET` clause, so a re-sync preserves the existing value (INSERT
still lands the default for brand-new rows). The variant spec does exactly this:

```python
_VARIANT_SPEC = EntitySpec(
    entity_key="variant",
    ...
    attrs_postprocess=_variant_postprocess,        # owns: parent_*, display_name, etc.
    preserve_columns_on_conflict=frozenset({"service_id"}),  # owned by the service spec
)
```

With the column durable, readers can treat it as a plain row read. `search_items` reads
`service_id` directly (its `@cache_read(CachedVariant, CachedService)` refreshes
services — and runs the backfill — before the search), rather than re-syncing and
re-fetching to dodge a stale value. Pinned by
`test_typed_cache_catalog.py::TestServiceVariantLinkBackfill::test_variant_resync_preserves_backfilled_service_id`.

______________________________________________________________________

## Bulk cache work runs on an optional dedicated rate-limit budget

Cache (re)builds are bandwidth-heavy: a cold rebuild auto-paginates every entity
(`include_deleted` / `include_archived`, 250/page across thousands of rows). Katana caps
each API key at ~60 req/min, so that burst exhausts the budget, trips the client's
rate-limit reset gate (`RateLimitTransport`, a ~57s global stall on `remaining=0`), and
— because it shares the one client — **starves foreground tool calls**, surfacing to the
host as timeouts.

**Katana meters the rate limit per API key, not per tenant** (verified empirically:
draining key A leaves key B's `X-Ratelimit-Remaining` untouched, separate reset epochs).
So the server supports an optional second key, `KATANA_SYNC_API_KEY`, dedicated to
*bulk* cache work — it gets its own independent 60/min budget, keeping the foreground
key's budget clean. No smoothing/pacing is applied: the bulk path is free to burst and
absorb 429s on its own budget.

Two code paths run on this dedicated client; everything else (interactive reads, lazy
on-demand syncs) stays on the foreground client:

- the background warm-up task (`server._warm_caches_in_background`, scheduled in
  `lifespan`), and
- the explicit `rebuild_cache` tool (`tools/foundation/cache_admin.py`), via
  `Services.sync_client`.

`Services.sync_client` is the single resolution point: it returns
`dedicated_sync_client` when `KATANA_SYNC_API_KEY` is set (and differs from
`KATANA_API_KEY`), else falls back to the foreground `client` — so unset = prior
single-key behavior. Both keys **must** be on the same tenant. Pinned by
`test_server.py::TestCacheWarmup` (warm-up routing) and
`test_cache_admin.py::TestSyncClientRouting` (rebuild routing).

This isolates the *budget*, not the per-entity `cache.lock_for(entity)` wait — a
foreground call for an entity mid-rebuild still waits on that lock, but the rebuild now
runs at full speed on its own key instead of contending for the foreground budget, so
the wait shrinks.
