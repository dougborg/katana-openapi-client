# Katana MCP Server — Architecture

This document describes how the `katana-mcp-server` package is structured today. Design
rationale for individual decisions lives in [ADRs](adr/README.md) — this doc is the map,
not the encyclopedia.

## Overview

The MCP server exposes Katana Manufacturing ERP to AI assistants via the
[Model Context Protocol](https://modelcontextprotocol.io). It is built on
[FastMCP](https://github.com/jlowin/fastmcp) and consumes the Python
[`katana-openapi-client`](../../katana_public_api_client/docs/README.md) package for
HTTP. Resilience (retries, rate-limiting, smart pagination) lives in the client's
transport layer — the MCP server inherits all of it for free, and **must not** wrap API
calls with its own retry / rate-limit logic.

## Layered structure

```
┌────────────────────────────────────────────────────────────┐
│  FastMCP entry (server.py)                                 │
│   - registers tools / resources / prompts                  │
│   - hot-reload + HTTP/STDIO transports                     │
├────────────────────────────────────────────────────────────┤
│  Tools           Resources         Prompts                 │
│  tools/          resources/        prompts/                │
│   foundation/     help.py           workflows.py           │
│   workflows/      inventory.py                             │
│                   reference.py                             │
├────────────────────────────────────────────────────────────┤
│  Services / dependencies (services/dependencies.py)        │
│   get_services(context) → KatanaClient + caches            │
├────────────────────────────────────────────────────────────┤
│  Caches (two, by design — see ADR-0018)                    │
│   CatalogCache (cache.py)       — reference entities       │
│   TypedCacheEngine (typed_cache/) — transactional entities │
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
  Katana domain: `catalog.py`, `customers.py`, `inventory.py`, `items.py`,
  `manufacturing_orders.py`, `orders.py`, `purchase_orders.py`, `reporting.py`,
  `sales_orders.py`, `stock_transfers.py`. Each module exposes the `get_*` / `list_*` /
  `create_*` / `update_*` operations for its domain and follows the conventions in
  [ADR-0016](adr/0016-tool-interface-pattern.md) and
  [ADR-0019](adr/0019-tool-description-batch-conventions.md).
- **Workflows** (`tools/workflows/`) — a planned extension layer for future multi-step
  compositions built on top of foundation tools. This directory is currently a stub:
  `register_all_workflow_tools` is a no-op and there are no concrete workflow tool
  modules yet. Add fulfilment / production-planning examples here only once real
  workflow tools exist.

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

`tools/decorators.py` provides `@cache_read("entity")` and
`@cache_write("entity_a", "entity_b")` decorators. `cache_read` triggers an incremental
sync of the named entity before invoking the tool; `cache_write` invalidates the listed
entities after a mutating call so the next list/get returns fresh data. Tool
implementations stay focused on business logic; sync orchestration lives in the
decorator.

## Resources

Resources expose read-only context to the AI:

- `resources/help.py` — tool reference and conventions
  ([ADR-0019](adr/0019-tool-description-batch-conventions.md))
- `resources/inventory.py` — current inventory snapshots
- `resources/reference.py` — Katana taxonomy and lookup tables

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
catalog_cache = services.cache      # CatalogCache
typed_cache = services.typed_cache  # TypedCacheEngine
```

Lifespan management (engine open/close, client cleanup) is handled by `server.py`.

## Caches

The MCP server runs **two** complementary caches. They serve different needs and both
are permanent — neither is a temporary stepping stone toward the other
([ADR-0018](adr/0018-sqlmodel-typed-cache.md)).

### CatalogCache (`katana_mcp/cache.py`, `cache_sync.py`)

A generic SQLite + FTS5 store for the 10 reference entity types: variants, products,
materials, services, suppliers, customers, locations, tax rates, operators, factories.
Every row projects into a three-text-column `entity_index` (name, description, code) for
cheap full-text search across heterogeneous types. Powers `search_items` and
`get_variant_details`-style lookup tools.

### TypedCacheEngine (`katana_mcp/typed_cache/`)

SQLModel-backed per-entity tables for transactional types: sales orders, manufacturing
orders, purchase orders, stock adjustments, stock transfers, manufacturing-order recipe
rows. Each entity has its own table with proper FK relationships and JSON columns;
nested rows (sales-order rows, MO recipe rows, …) become child tables with FKs back to
the parent.

The transactional types' filter shape (status enums, date ranges, customer/ supplier
IDs, variant-id-via-rows) and 30+-field schemas don't fit `CatalogCache`'s
three-text-column projection — hence the dedicated typed store.

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

The MCP server depends on
[`katana-openapi-client`](../../katana_public_api_client/docs/README.md) as a published
package. All HTTP behavior — retries, rate limiting, smart pagination, observability
hooks — lives in that client's transport layer (see
[client ADR-0001](../../katana_public_api_client/docs/adr/0001-transport-layer-resilience.md)).
The MCP server treats the client as a black box and **must not** wrap API methods with
its own retry / rate-limit / pagination logic; doing so double-applies behavior and can
introduce subtle desync between layers.

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
1. **If the tool reads from cache,** add `@cache_read("entity")`. If it writes, add
   `@cache_write("entity_a", "entity_b")` listing every entity whose cache should be
   invalidated.
1. **For new transactional list tools backed by typed cache:** add an `EntitySpec`
   literal in `typed_cache/sync.py` and a thin `ensure_<entity>_synced` wrapper. The
   `Cached<Entity>` row class is auto-generated from the spec by the next regen.
1. **Update `resources/help.py`** to mirror the new tool's surface (per
   [ADR-0019 §4](adr/0019-tool-description-batch-conventions.md)).
1. **Add tests:** unit tests for the request/response shape; integration tests if cache
   sync is involved.

## References

- [ADR-0010](adr/0010-katana-mcp-server.md) — original MCP server scope
- [ADR-0016](adr/0016-tool-interface-pattern.md) — tool interface pattern
- [ADR-0017](adr/0017-automated-tool-documentation.md) — automated tool documentation
- [ADR-0018](adr/0018-sqlmodel-typed-cache.md) — SQLModel typed cache
- [ADR-0019](adr/0019-tool-description-batch-conventions.md) — tool description and
  batch-field conventions
- [Client ADR-0001](../../katana_public_api_client/docs/adr/0001-transport-layer-resilience.md)
  — transport-layer resilience pattern
- [CLAUDE.md](../../CLAUDE.md) — repo-level conventions for AI assistants
- [Development guide](development.md) — local hot-reload workflow
- [Deployment guide](deployment.md) — production deployment

## What this doc replaced

A previous 868-line "Comprehensive Architecture Design" (Oct 2025) drafted the server
before any of it was implemented. It mixed real best-practice notes with hypothetical
pseudo-code tools and a week-by-week implementation schedule, none of which match the
current shape. That document is preserved in git history; the canonical architecture
description is this file plus the ADRs.
