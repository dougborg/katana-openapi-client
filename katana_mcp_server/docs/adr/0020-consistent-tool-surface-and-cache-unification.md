# ADR-0020: Consistent tool surface across entity types + cache unification

## Status

Proposed

Date: 2026-04-30

## Context

PR #464 shipped the unified `modify_<entity>` + `delete_<entity>` surface for the five
major entities (purchase order, sales order, manufacturing order, stock transfer, item).
The **read** surface — search, list, get-single, bulk fetch — never got the same
consistency pass. Two independent symptoms made this gap concrete:

**A user-visible search bug.** A query for `00.4021.018.003` against `search_items`
returned 0 results, even though that string is a real `supplier_item_code` on a variant
in the cache (`get_variant_details` finds the variant immediately by SKU). Triage
initially mis-diagnosed this as a SQLite FTS5 tokenization issue (#471). The actual root
cause: the cache's `entity_index` table only carries three searchable columns (`sku`,
`name`, `name2`); `supplier_item_codes`, `internal_barcode`, `registered_barcode` are
never indexed. The data isn't reachable via search regardless of how the query is
tokenized.

**A whole-surface audit.** Once the search bug forced an audit of the per-entity tool
inventory, the asymmetries were obvious:

| Entity                                        |       Search       |                 List with `ids=`                 | Get-single |      Create       |      Modify       |      Delete       |
| --------------------------------------------- | :----------------: | :----------------------------------------------: | :--------: | :---------------: | :---------------: | :---------------: |
| Items (products / materials / services)       |         ✓          |                        —                         |     ✓      |         ✓         |         ✓         |         ✓         |
| Variants                                      | (via search_items) | ✓ via `get_variant_details(skus=, variant_ids=)` |     ✓      | (via modify_item) | (via modify_item) | (via modify_item) |
| Purchase orders                               |         —          |                        ✓                         |     ✓      |         ✓         |         ✓         |         ✓         |
| Sales orders                                  |         —          |                        ✓                         |     ✓      |         ✓         |         ✓         |         ✓         |
| Manufacturing orders                          |         —          |                        ✓                         |     ✓      |         ✓         |         ✓         |         ✓         |
| Stock transfers                               |         —          |                        —                         |     —      |         ✓         |         ✓         |         ✓         |
| Stock adjustments                             |         —          |                        ✓                         |     —      |         ✓         |      partial      |         ✓         |
| Customers                                     |         ✓          |                        —                         |     ✓      |         —         |         —         |         —         |
| Suppliers / locations / tax rates / operators |         —          |                    (resource)                    |     —      |         —         |         —         |         —         |

Five gaps stand out: no fuzzy search for orders / transfers / adjustments; no get-single
for stock transfers and stock adjustments (Katana exposes no GET-by-id for either, but
both are in the typed cache); no list tool for items (search returns variants, get_item
is single-only); customers have search + get-single only — no modify/delete and no
bulk-by-id; reference data is exposed only as MCP resources, not as searchable /
filterable tools.

**A two-cache architecture.** The MCP server has two caches today, and most of the
asymmetry above lives at the seam between them:

1. **Legacy `CatalogCache`** (`katana_mcp/cache.py`) — single SQLite file with a generic
   JSON-blob `entities` table, a 3-column `entity_index` (sku/name/name2), and FTS5 over
   those three columns. Holds: variants, products, materials, services, customers,
   suppliers, locations, tax rates, operators. This is what `search_items` and
   `search_customers` use.
1. **Typed cache** (`katana_mcp/typed_cache/`) — SQLModel-based, per-entity `Cached*`
   tables with proper foreign keys and relationships, incremental watermark-driven sync
   with soft-delete handling, no FTS5. Holds: purchase orders, sales orders,
   manufacturing orders, stock transfers, stock adjustments. This is what every
   `list_<order>` tool queries (ADR-0018).

The two caches diverge on every dimension: sync mechanics, query patterns (JSON parsing
vs. SQL with FK joins), schema migration (`_SCHEMA_VERSION` rebuild vs. SQLModel
migrations), and search (FTS5 on one side, nothing on the other). A new search tool for
sales orders needs to either add an FTS layer to the typed cache, bridge orders into the
legacy cache, or build a third path — none of which is obviously right.

## Decision

We adopt three coupled commitments:

### 1. The per-entity tool-surface target

For every transactional entity, the MCP server exposes the same operations where they
make sense:

```
search · list (filtered, supporting ids= for bulk-by-id) ·
get-single · create · modify · delete
```

The Context table above is the canonical gap register: cells marked ✓ are conformant,
cells marked — are tracked exceptions to be closed by the workstreams below. "Invariant"
is the long-term target — once the in-scope workstreams (WS-A through WS-F) land, the
matrix should be all ✓ for transactional entities. Reference-data exceptions (WS-G) are
deliberately deferred and not part of the invariant target.

`list_<entity>(ids=[1,2,3])` *is* the bulk-get path — there's no separate
`bulk_get_<entity>` tool. The "bulk-fetch gap" is only worth a dedicated tool when the
entity has no list (items today) or when the business-key dimension differs from numeric
id (variants: `get_variant_details(skus=, variant_ids=)`).

For reference data (suppliers, locations, tax rates, operators), the default is exposure
as MCP resources. Promotion to first-class tools (`search_suppliers` / `get_location` /
etc.) is deferred until concrete caller demand surfaces — these entities are typically
managed in Katana's UI, not via the MCP.

### 2. Long-term: unify on the typed cache with an FTS5 sidecar

The legacy `CatalogCache`'s generic-table-with-skinny-index design was fine for the
original 10 reference entity types, but its 3-column FTS projection is the structural
reason behind #471 and the broader search asymmetry. The typed cache is the better
foundation: per-entity schemas mean a new searchable field is a schema addition (ALTER
TABLE on a specific `Cached*` table) rather than a generic blob-index extension; foreign
keys mean cross-entity queries (e.g. variant → parent product name in the FTS surface)
are real joins; SQLModel migrations replace the full-rebuild `_SCHEMA_VERSION` story.

We migrate the high-value catalog entities (variants, products, materials, services,
customers) into the typed cache and add an FTS5 sidecar table populated via SQLModel
`after_insert` / `after_update` events. Per-entity FTS column sets are declared on the
SQLModel class (`_fts_columns: tuple[str, ...]`).

Reference data (suppliers, locations, tax rates, operators) is deferred — low value to
migrate, low query volume against it.

**Legacy cache retirement criterion (revising ADR-0018).** ADR-0018 stated the legacy
generic cache retires "once every reference type has migrated." This ADR partially
supersedes that: legacy retires once the **catalog entities** (variants, products,
materials, services, customers) complete migration. Reference data (suppliers,
locations, tax rates, operators) is acceptable to leave in a long-lived
reduced-footprint legacy cache, OR to migrate later when concrete demand surfaces (see
WS-G below). The retirement gate is "catalog migration complete," not "all entity types
migrated." This change is intentional: gating the legacy retirement on low-value
reference-data migration would delay the cleanup indefinitely without practical benefit.

### 3. Short-term: don't gate the search bug on the migration

WS-0 (the cache unification) is a 4-6 week lift. Blocking #471 (a real, surfaced user
complaint) behind a multi-week migration is wrong. We extend the legacy cache with one
new column (`entity_index.extras`) and one new field on the per-entity `IndexFields`
config (`extras_keys: tuple[str, ...]`). Variants register
`("supplier_item_codes", "internal_barcode", "registered_barcode")`, and the search bug
is fixed in roughly 150 lines of code that lives against legacy cache infrastructure
we'll throw away when WS-0 lands.

The throwaway-ness is a feature, not a regret. The `extras_keys` API shape we land in
the legacy cache is the same shape we want on the typed-cache `_fts_columns`; the
contract migrates cleanly.

### 4. Workstream organization

Tracked in #469 (cross-WS roadmap tracker). Eight workstreams, two parallel tracks:

**Track 1 — Read-surface unification (immediate user value)**

- **WS-A** (#473) — Search-surface field expansion. `extras` column + `extras_keys`.
  Closes #471. Lands first.
- **WS-B** (#474) — `search_<entity>` tools for purchase orders, sales orders,
  manufacturing orders, stock transfers, stock adjustments.
- **WS-C** (#475) — Get-single parity for stock transfers and stock adjustments + a
  `list_items(ids=, type=)` tool. Pairs with #311 (Prefab UI for inventory movements
  - stock-adjustment) and #316 (`create_stock_adjustment` elicitation failure) — both
    touch the same surface and are natural to fix alongside.
- **WS-D** (#470 + adjacent) — Empty-state UX for search tools.
- **WS-E** — PR #464 modify-pattern follow-ups: #465 (verifier coercion), #466 (parallel
  `plan_updates`), #467 (`prior_state` rendering polish), #468 (dispatcher refinements
  roll-up), #317 (schema-vs-OpenAPI validation test). No umbrella; each issue is its own
  PR, can land any time, no dependencies.
- **WS-F** (#476) — Customer surface parity (`modify_customer` / `delete_customer` /
  list-with-ids).
- **WS-G** — Reference-data tools (`search_suppliers` / `get_location` / etc.). Deferred
  until concrete demand.

**Track 2 — Cache unification (foundational)**

- **WS-0** (#472) — Catalog → typed cache + FTS5 sidecar. Lands incrementally per
  entity; once a `Cached*` arrives, the corresponding read tool migrates off legacy.
  Legacy cache retires when catalog migration completes.

The canonical sequencing detail and per-WS scope lives in #469 (cross-WS roadmap
tracker), referenced from each umbrella issue.

## Consequences

### Easier

- **Predictable agent surface.** Every transactional entity has the same six operations;
  agents don't have to learn per-entity quirks for read-side workflows.
- **Search works for the fields callers actually search by.** Variants matched by
  supplier_item_code, customers matched by phone, orders matched by additional_info —
  all reach FTS via `extras_keys`.
- **One cache to reason about (post-WS-0).** Sync mechanics, query patterns, migration
  strategy, and search infrastructure all live in one place. New entities get added to
  one place.
- **FK relationships unlock cross-entity queries.** Variant → product name joins in the
  FTS surface, sales order rows ↔ variants for aggregation, etc. The typed cache already
  has the data shape; it just needs the rest of the catalog migrated alongside.
- **Schema additions become routine.** Adding a new searchable field is an ALTER TABLE
  on the `Cached*` class plus an entry in `_fts_columns`, not a generic-schema rebuild.

### Harder

- **Bigger maintained surface.** Going from "modify is consistent" to "the whole surface
  is consistent" means more tools, more tests, more help-resource entries. The
  discipline is to keep them mechanically uniform — same param shapes (especially
  `ids: CoercedIntListOpt`, `format: "markdown" | "json"`, `limit` / `page` semantics),
  same response shapes, same empty-state UX.
- **Cache migration is a multi-week lift on the most-used cache entity.** Variants are
  touched by every `search_items` / `get_variant_details` / `check_inventory` call.
  Migration risk is real — incremental rollout per entity with fallback to legacy until
  the corresponding read tool flips over.
- **Two-cache coexistence period.** Between WS-A's first PR and WS-0's catalog
  completion, both caches run side-by-side. Bugs fixed against legacy need to be
  re-checked when the entity migrates; new tests for catalog read tools need to pass
  against both backends until the legacy path retires. This is intentional friction —
  the alternative (block read-surface work until WS-0 lands) is worse.
- **Reference-data ergonomics asymmetry.** Suppliers / locations / tax rates / operators
  stay as resources, not tools, until WS-G ships (deferred). Callers who need to search
  those entities still need workarounds. Acceptable given the low query volume against
  reference data.

### Risks and mitigations

- **Risk: legacy code shipped between now and WS-0 lands becomes technical debt.**
  Mitigation: keep the WS-A scope explicitly throwaway-shaped — small, mechanical, no
  architectural commitments. Two pieces of WS-A behavior carry forward to WS-0 rather
  than being thrown away:

  1. The `extras_keys` API shape (legacy cache) → `_fts_columns` shape (typed cache
     sidecar). The contract migrates cleanly.
  1. The tokenizer fix (`re.split(r"\W+", query)` + per-token prefix matches ANDed) is a
     behavioral contract that has to be reimplemented in the typed-cache FTS5 query
     builder. Not a code-line carry-forward, but a semantic carry-forward — when
     migrating `search_items` etc. off legacy, the test for `00.4021.018.003`-style
     queries must continue to pass.

  The implementation code in legacy `cache.py` is genuinely throwaway; the two
  behavioral contracts above are not. Both are explicit in this ADR so future WS-0 work
  doesn't accidentally regress them.

- **Risk: WS-0 stalls partway through, leaving us with a hybrid catalog (some entities
  on typed cache, some still on legacy).** Mitigation: each WS-0 sub-task is
  independently shippable per entity. A partial migration leaves the legacy cache
  covering the un-migrated entities — equivalent to today's state for those, with the
  migrated ones strictly improved.

- **Risk: FTS5 sidecar over typed cache adds complexity to the sync path (now SQLModel
  events have to fire FTS upserts).** Mitigation: declare per-entity FTS column sets on
  the SQLModel class itself so the sidecar pattern stays per-entity local, not a
  centralized event handler. Same shape for every entity, same code path for every sync.

- **Risk: the search-tool tokenizer is fragile for SKUs / identifiers with internal
  punctuation (`00.4021.018.003`-style strings).** Mitigation: secondary fix in WS-A —
  switch the FTS query builder from `query.split()` (whitespace only) to
  `re.split(r"\W+", query)` with per-token prefix matches ANDed. Ships alongside the
  field-coverage fix; defense in depth.

## Alternatives considered

### Block #471 on WS-0 — fix it correctly the first time

Rejected. WS-0 is a 4-6 week migration covering schema design, sync logic, FTS5 sidecar,
test migration, and rollout risk on the most-used cache entity. Blocking a real
user-visible search bug behind that lift is wrong: the fix is small, the API shape
(`extras_keys`) survives the migration, and the implementation code is genuinely safe to
delete. The deferred-fix path optimizes for theoretical purity over delivered value.

### Pure column-list-of-keys per slot instead of an `extras` column

Considered making `IndexFields.name_key`, `name2_key` accept a `tuple[str, ...]` of keys
to join, instead of adding a new `extras` column. Rejected: splits BM25 ranking
semantics across slots and complicates relevance tuning (a hit in `extras` should not
weigh the same as a hit in `name`). One column, one ranking weight, one schema entry.

### Centralized FTS event handler instead of per-entity `_fts_columns`

Considered a SQLAlchemy event listener registered on a base class that synthesizes FTS5
upserts for any subclass. Rejected: opaque sync path makes debugging harder, and the
per-entity column set still has to live somewhere. Declaring `_fts_columns` on the
SQLModel class makes the searchable surface visible at the entity definition; the
sidecar pattern is still local code, just discoverable.

### Background sync thread for FTS instead of `after_insert` / `after_update` events

Considered a separate process or asyncio task that periodically scans `Cached*` tables
and reconciles FTS rows. Rejected: introduces a staleness window between cache writes
and search visibility, plus a second sync mechanism to reason about. SQLModel events
fire synchronously in the same transaction as the SQLModel write, so search visibility
is consistent with the write itself. The existing typed-cache sync (ADR-0018) already
runs synchronously per request; the FTS layer follows the same model.

### Bulk-fetch as a dedicated `bulk_get_<entity>` tool per entity

Considered a parallel `bulk_get_<entity>(ids: list[int])` tool family alongside
`get_<entity>(id)`. Rejected: `list_<entity>(ids=)` already covers the same use case on
every transactional entity that has a list tool — adding a second tool with the same
semantics doubles the surface without ergonomic benefit. The exception is variants
(`get_variant_details(skus=, variant_ids=)`), where the business-key dimension differs
from numeric id and the bulk-by-business-key path is genuinely distinct from
`list_*(ids=)`.

### Migrate reference data alongside the catalog

Considered including suppliers / locations / tax rates / operators in WS-0's scope and
retiring legacy in one shot. Rejected: low query volume against reference data makes the
migration low-value, and the legacy cache running in a reduced-footprint state for those
entities is acceptable indefinitely. Forcing them into WS-0 would add weeks to a
critical-path workstream for marginal benefit. WS-G (deferred) is the escape hatch if
reference-data demand later justifies promotion to first-class tools.

______________________________________________________________________

## Related

- ADR-0010 — Create Katana MCP Server for Claude Code Integration
- ADR-0018 — SQLModel-backed typed cache for transactional list tools (the typed cache
  that WS-0 absorbs the catalog into; this ADR partially supersedes its retirement
  criterion — see Decision §2)
- ADR-0019 — MCP tool description and batch-field conventions (the discoverability rules
  the new search/list tools must follow)
- #469 — Cross-WS roadmap tracker (the GitHub-side index)
- #464 — PR 2 unified-modify pattern (the precedent this ADR extends to the read
  surface)
- #471 — search_items missing supplier_item_codes (the surfaced bug)
- #472 / #473 / #474 / #475 / #476 — per-WS umbrella issues
