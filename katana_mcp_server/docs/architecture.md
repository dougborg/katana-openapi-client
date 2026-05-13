# Katana MCP Server — Architecture

This document describes how the `katana-mcp-server` package is structured today. Design
rationale for individual decisions lives in [ADRs](adr/README.md) — this doc is the map,
not the encyclopedia.

## Overview

The MCP server exposes Katana Manufacturing ERP to AI assistants via the
[Model Context Protocol](https://modelcontextprotocol.io). It is built on
[FastMCP](https://github.com/jlowin/fastmcp) and consumes the Python
[`katana-openapi-client`](../client/README.md) package for HTTP. Resilience (retries,
rate-limiting, smart pagination) lives in the client's transport layer — the MCP server
inherits all of it for free, and **must not** wrap API calls with its own retry /
rate-limit logic.

## Layered structure

```
┌────────────────────────────────────────────────────────────┐
│  FastMCP entry (server.py)                                 │
│   - registers tools / resources / prompts                  │
│   - hot-reload + HTTP/STDIO transports                     │
│   - middleware/ (request-side coercion shims)              │
├────────────────────────────────────────────────────────────┤
│  Tools           Resources         Prompts                 │
│  tools/          resources/        prompts/                │
│   foundation/     help.py           workflows.py           │
│   workflows/      inventory.py                             │
│   prefab_ui.py                                             │
│   decorators.py                                            │
├────────────────────────────────────────────────────────────┤
│  Services / dependencies (services/dependencies.py)        │
│   get_services(context) → KatanaClient + caches            │
├────────────────────────────────────────────────────────────┤
│  Cache (unified — see ADR-0018 + #472 Phase D)             │
│   TypedCacheEngine (typed_cache/)                          │
│   - catalog tier   — variants/products/materials/...       │
│   - transactional  — sales/manufacturing/purchase orders   │
├────────────────────────────────────────────────────────────┤
│  KatanaClient (katana_public_api_client)                   │
│   - transport-layer resilience                             │
│   - generated attrs request/response models                │
│   - generated pydantic models + Cached<Entity> siblings    │
└────────────────────────────────────────────────────────────┘
```

## Tools

Tools live under `katana_mcp/tools/` and split into two sublayers:

- **Foundation tools** (`tools/foundation/`) — thin, single-purpose tools organized by
  Katana domain. Each module exposes the standard CRUD operations for its domain
  (`get_*` / `list_*` / `create_*` / `update_*` / `modify_*` / `delete_*`) plus
  domain-specific operations like `correct_*` for after-the-fact fixes; see the
  directory listing for the canonical surface. Tools follow the conventions in
  [ADR-0016](adr/0016-tool-interface-pattern.md) and
  [ADR-0019](adr/0019-tool-description-batch-conventions.md). The canonical list of
  modules is the directory itself
  ([`tools/foundation/`](https://github.com/dougborg/katana-openapi-client/tree/main/katana_mcp_server/src/katana_mcp/tools/foundation))
  and the live tool surface is exposed at the `katana://help/tools` resource — both stay
  current; this doc does not enumerate.
- **Workflows** (`tools/workflows/`) — a planned extension layer for future multi-step
  compositions built on top of foundation tools. This directory is currently a stub:
  `register_all_workflow_tools` is a no-op and there are no concrete workflow tool
  modules yet. Add fulfilment / production-planning examples here only once real
  workflow tools exist.

Cross-cutting tool infrastructure also lives directly under `tools/`:

- `prefab_ui.py` — Prefab card builders + `register_preview_tool` helper (preview/apply
  pattern). See [Prefab UI — Rendering Pitfalls](prefab/README.md) for the contracts the
  JS renderer enforces.
- `tool_result_utils.py` — `make_tool_result(...)` and the `UI_META` opt-in marker that
  links a tool to the auto-registered widget.
- `decorators.py` — `@cache_read(CachedEntity, ...)` for typed-cache-aware reads.
- `_modification.py` / `_modification_dispatch.py` / `_reopen.py` / `_derived_fields.py`
  / `list_coercion.py` — internal helpers consumed by the foundation tools.

### Tool interface pattern (ADR-0016)

Each tool is built around a pydantic `Request` model + `Response` model and an async
`_impl` function. The `@unpack_pydantic_params` decorator from `katana_mcp/unpack.py`,
combined with the `Unpack` marker on `Annotated[Request, Unpack()]`, unpacks Request
fields into named MCP parameters so the JSON schema exposed to the AI matches the model
— without giving up the structured validation pydantic provides.

State-changing tools (`create_*`, `update_*`, `delete_*`, `fulfill_*`, …) use
elicitation: the first call returns a preview, and the AI must confirm explicitly before
mutation. See [ADR-0016 §4](adr/0016-tool-interface-pattern.md).

### Batch-field & docstring conventions (ADR-0019)

`list_*` tools that accept multiple filter values use the `<entity>_<field>s` naming
(`product_ids`, not `ids`). `get_*` tools use the singular form. Every tool's docstring
opens with a one-line "Returns ..." summary so the AI can route from a partial query
(see [ADR-0019](adr/0019-tool-description-batch-conventions.md)). The
`resources/help.py` reference resource mirrors these conventions; it must be kept in
sync when tool surface changes.

### Cache-aware decorators

`tools/decorators.py` provides `@cache_read(CachedVariant, CachedProduct, ...)`.
`cache_read` triggers an incremental sync of the named typed-cache entities before
invoking the tool. Tool implementations stay focused on business logic; sync
orchestration lives in the decorator.

Cache invalidation after writes is **implicit**: the typed cache pulls incremental
deltas via `updated_at_min` on every `@cache_read`-decorated call, so a freshly-created
or modified entity is picked up automatically by the next read. The legacy `cache_write`
/ `mark_dirty` mechanism was retired alongside `CatalogCache` (#472 Phase D).

## Resources

Resources expose read-only context to the AI. The current set is small:

- `resources/help.py` — tool reference and conventions, registered at `katana://help`,
  `katana://help/workflows`, `katana://help/tools`, `katana://help/resources`
  ([ADR-0019](adr/0019-tool-description-batch-conventions.md))
- `resources/inventory.py` — summary catalog index at `katana://inventory/items`
  (products, materials, services as id / name / type plus capability flags `is_sellable`
  / `is_producible` / `is_purchasable` and per-type counts — *not* the full per-item
  field set), backed by the typed cache. For rich item details, use the `get_item` /
  `get_variant_details` tools.

Reference data (suppliers, locations, tax rates, operators, additional costs) is
**tools-only** — see `tools/foundation/reference.py`. The previous bulk-list resources
for those entities dumped every row as a single JSON blob and flooded agent context;
parameterized tools (FTS-backed `query` + bounded `limit`) replaced them. Transactional
data (sales / manufacturing / purchase orders, stock movements) is also tools-only.

## Prompts

`prompts/workflows.py` provides templated multi-step prompts for common manufacturing
workflows (order fulfilment, cycle counting, etc).

## Services & dependencies

`services/dependencies.py` builds the per-request service container. Tools access it
via:

```python
from katana_mcp.services import get_services

services = get_services(context)
client = services.client            # KatanaClient
typed_cache = services.typed_cache  # TypedCacheEngine
catalog = services.typed_cache.catalog  # CatalogQueries adapter
```

Lifespan management (engine open/close, client cleanup) is handled by `server.py`.

## Cache

The MCP server runs a single SQLModel-backed cache covering both catalog and
transactional tiers (see [ADR-0018](adr/0018-sqlmodel-typed-cache.md) for the original
typed-cache architecture and #472 Phase D for the catalog unification).

### TypedCacheEngine (`katana_mcp/typed_cache/`)

SQLModel-backed per-entity tables for every cached type. Each entity has its own table
with proper FK relationships and JSON columns; nested rows (sales-order rows, MO recipe
rows, ...) become child tables with FKs back to the parent.

The cache is split into two tiers:

- **Catalog tier** — variants, products, materials, services, and the per-domain
  reference taxonomies. Search via per-entity FTS5 sidecar tables (`<entity>_fts`) wired
  through a `CatalogQueries` adapter exposed at `services.typed_cache.catalog`. The
  adapter provides typed `get_by_id` / `get_by_sku` / `get_many_by_ids` / `get_all` /
  `smart_search` / `search_fuzzy` methods that return `Cached*` SQLModel instances
  directly (not dict shims), with default `include_archived=False` /
  `include_deleted=False` filters.
- **Transactional tier** — sales orders, manufacturing orders (+ recipe rows), purchase
  orders (+ rows), stock adjustments (+ rows), stock transfers (+ rows). Searched via
  SQL `WHERE` clauses; no FTS sidecar — these tables don't carry free-text fields.

The canonical entity list lives in
[`typed_cache/sync.py`](https://github.com/dougborg/katana-openapi-client/blob/main/katana_mcp_server/src/katana_mcp/typed_cache/sync.py)
(the `EntitySpec` literals); enumerating it here would drift on every new entity. For
the soft-state filtering rules (`include_archived` / `include_deleted` opt-ins,
`is_archived` / `is_deleted` derived bools, cross-entity ID collision pitfalls) and the
`Cached<Entity>` / API-pydantic-don't-pollute contract, see
[Typed Cache — Patterns and Pitfalls](typed_cache/README.md).

### EntitySpec — the generic sync driver

A single generic `_ensure_synced(client, cache, spec)` in `typed_cache/sync.py` drives
every entity's incremental sync. Each entity has a frozen `EntitySpec` dataclass that
wires together:

- the **entity key** (used for the per-entity sync lock and `SyncState` row)
- the **API endpoint** module (`get_all_*` / `find_*`) to call
- the **cache row class** (`Cached<Entity>`) and the **API pydantic class** (the
  `from_attrs` intermediary)
- optional **child-rows configuration** (child class, parent-side rows field, FK field)
  for entities with nested rows
- an optional **pydantic_resolver** callback for discriminated unions (purchase orders
  pick `RegularPurchaseOrder` vs `OutsourcedPurchaseOrder` per row)

Public `ensure_<entity>_synced(client, cache)` functions are thin wrappers over
`_ensure_synced` so callers and tests stay terse.

The generic driver replaced six near-identical hand-rolled sync helpers — the original
duplication was a source of silent-desync bugs whenever a typo slipped through one
entity's lock-key string. New transactional entities are now added by writing one
`EntitySpec` literal.

### Generated `Cached<Entity>` classes

The `Cached<Entity>` and `Cached<Entity>Row` classes consumed by the typed cache are
**auto-generated** by `scripts/generate_pydantic_models.py` from the same OpenAPI spec
that produces the API attrs/pydantic classes. They sit alongside the API pydantic
classes in `katana_public_api_client/models_pydantic/_generated/` and inherit
`table=True`, FKs, and JSON columns via the generator's
`duplicate_cache_tables_as_cached_siblings` pass.

The contract is one-directional: API pydantic stays a clean wire-shape mirror; cache
concerns (FKs, JSON storage, cache-only fields) live exclusively on the `Cached<Entity>`
siblings. **Never** add a cache-only field to the OpenAPI spec or to an API pydantic
class — it pollutes the published client package for third-party users (see CLAUDE.md
"polluting the API spec/models").

## Client integration

The MCP server depends on [`katana-openapi-client`](../client/README.md) as a published
package. All HTTP behavior — retries, rate limiting, smart pagination, observability
hooks — lives in that client's transport layer (see
[client ADR-0001](../client/adr/0001-transport-layer-resilience.md)). The MCP server
treats the client as a black box and **must not** wrap API methods with its own retry /
rate-limit / pagination logic; doing so double-applies behavior and can introduce subtle
desync between layers.

When a bug surfaces in the MCP server but originates in client-generated code (attrs,
pydantic, `from_attrs`, generator output), fix it at the client/generator layer. The
client is consumed by third-party users — they hit the same bugs (see CLAUDE.md "Fix
bugs at the client/generator layer").

## Adding a new tool

1. **Decide foundation vs workflow.** A direct one-shot Katana operation is a foundation
   tool; a multi-step orchestration is a workflow.
1. **Pick the existing module by Katana domain** (`catalog.py`,
   `manufacturing_orders.py`, etc.) — don't create a new module unless the domain
   genuinely doesn't fit any existing one.
1. **Follow ADR-0016** for the request/response shape and the `Unpack` decorator
   integration; use elicitation for any state-changing operation.
1. **Follow ADR-0019** for naming (`<entity>_<field>s` for batch list filters, singular
   for `get_*`) and the docstring opening sentence.
1. **If the tool reads from cache,** add `@cache_read(CachedEntity, ...)` keyed by the
   typed-cache `Cached*` SQLModel class (e.g. `CachedVariant`, `CachedProduct`).
   Mutating tools do **not** need an explicit invalidation decorator — the typed cache
   pulls incremental deltas via `updated_at_min` on every `@cache_read`-decorated call,
   so a freshly-created or modified entity is picked up by the next read. The legacy
   `@cache_write` / `mark_dirty` mechanism was retired with `CatalogCache` (#472 Phase
   D).
1. **For new transactional list tools backed by typed cache:** add an `EntitySpec`
   literal in `typed_cache/sync.py` and a thin `ensure_<entity>_synced` wrapper. The
   `Cached<Entity>` row class is auto-generated from the spec by the next regen.
1. **Update `resources/help.py`** to mirror the new tool's surface (per
   [ADR-0019 §4](adr/0019-tool-description-batch-conventions.md)).
1. **Add tests:** unit tests for the request/response shape; integration tests if cache
   sync is involved.

## Subsystem deep-dives

This doc is the map; the deep-dives live alongside the code:

- [Prefab UI — Rendering Pitfalls](prefab/README.md) — JSON-envelope contracts the JS
  renderer enforces (`DataTable.rows` mustache binding, `register_preview_tool` +
  `meta=UI_META` symmetry, browser-test wire-shape parity, help-resource drift).
- [Typed Cache — Patterns and Pitfalls](typed_cache/README.md) — soft-state filtering
  (`include_archived` / `include_deleted` + `is_archived` / `is_deleted` derived bools),
  cross-entity ID-collision pitfall, and the API-pydantic / `Cached<Entity>` separation
  contract.
- [Spec Authoring](../client/spec-authoring.md) — OpenAPI 3.1 conventions, the
  generator/spec regen lockstep, breaking-change marker rules, and the "fix bugs at the
  client/generator layer" rule that decides where a sync.py symptom should actually be
  fixed.

## References

The canonical, current list of MCP server ADRs is the [ADR index](adr/README.md) — this
section does not enumerate (drift surface). Adjacent references that aren't in the ADR
index:

- [Client ADR-0001](../client/adr/0001-transport-layer-resilience.md) — transport-layer
  resilience pattern (read this once if you've never touched the client retry/pagination
  layer)
- [CLAUDE.md](https://github.com/dougborg/katana-openapi-client/blob/main/CLAUDE.md) —
  repo-level conventions for AI assistants
- [Development guide](development.md) — local hot-reload workflow
- [Deployment guide](deployment.md) — production deployment

## What this doc replaced

A previous 868-line "Comprehensive Architecture Design" (Oct 2025) drafted the server
before any of it was implemented. It mixed real best-practice notes with hypothetical
pseudo-code tools and a week-by-week implementation schedule, none of which match the
current shape. That document is preserved in git history; the canonical architecture
description is this file plus the ADRs.
