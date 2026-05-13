# Architecture Quick Reference

Quick reference for key architectural patterns and decisions in this project. For
detailed rationale, see the per-package Architecture Decision Record (ADR) indexes
linked at the bottom; for the package-and-directory layout, see
[FILE_ORGANIZATION.md](FILE_ORGANIZATION.md).

## Core Architectural Patterns

### 1. Transport-Layer Resilience

**Pattern:** Implement resilience at the httpx transport layer instead of wrapping
individual API methods.

**Key benefits:**

- Every endpoint exposed by the spec gets automatic retries, rate limiting, and
  transparent pagination — no per-method wrapping.
- No modifications to generated code required.
- Single point of configuration in `katana_client.py`.

**Usage:**

```python
from katana_public_api_client import KatanaClient
from katana_public_api_client.api.product import get_all_products

async with KatanaClient() as client:
    # Automatically gets:
    # - Retry on 429 (rate limit) — all methods, including POST/PATCH
    # - Retry on 502/503/504 — only idempotent (GET, PUT, DELETE)
    # - Exponential backoff
    # - Retry-After header support
    # - Transparent pagination (auto-follows next links, aggregates results)
    response = await get_all_products.asyncio_detailed(client=client)
```

**Retry strategy:**

- **429 Rate Limiting** — all methods retried (Katana correctly returns 429 on read
  *and* write rate-limit hits).
- **502/503/504 Server Errors** — only idempotent methods (GET, PUT, DELETE) so we don't
  double-apply non-idempotent writes.
- **4xx Client Errors** — no retries (caller's problem).
- **Network Errors** — automatic retry with exponential backoff.

______________________________________________________________________

### 2. OpenAPI Code Generation

**Pattern:** Generate Python client from OpenAPI spec with two passes that stay in
lockstep.

**Workflow:**

1. Maintain spec at `docs/katana-openapi.yaml`.
1. `uv run poe regenerate-client` — emits attrs models, API methods, base client.
1. `uv run poe generate-pydantic` — emits pydantic mirrors + `Cached<Name>` siblings.
1. Or in one command: `uv run poe regenerate-all`.

**Generator-rewrite philosophy: regex first, libcst when the pattern grows, never
jinja.**

`scripts/generate_pydantic_models.py` runs *on top of* `datamodel-codegen`'s output.
datamodel-codegen does the hard work (OpenAPI → pydantic, type inference, discriminated
unions, validators); our pass is purely additive — inject SQLModel annotations, add
`Cached<Name>` siblings, attach `Column(JSON)` on JSON-typed list fields, etc. For that
scope, regex-based source rewrites on top of the generated output are the right tool:
auditable, minimal, fast, and the failure mode (failed substitution) is loud
(`raise GenerationError`).

Triggers to upgrade the rewriting layer:

- More than ~5 additional transforms accumulate, *or*
- Recurring whitespace/formatting edge cases bite repeated transforms.

→ migrate to **libcst** (preserves formatting exactly, structured idempotent rewrites).
**Do not** swap in jinja or hand-roll a new code-generation framework — full
template-replacement of datamodel-codegen is out of scope and would multiply the surface
area we have to keep in sync with the spec.

**See also:**
[`katana_public_api_client/docs/spec-authoring.md`](../../../../katana_public_api_client/docs/spec-authoring.md)
for the editing rules (OpenAPI 3.1 conventions, `ListResponse` shape, use-site
descriptions, fix-at-source rule).

______________________________________________________________________

### 3. Transparent Automatic Pagination

**Pattern:** Automatically follow pagination links in the background without user
intervention.

```python
# Request 50 items, but the API spans multiple pages.
async with KatanaClient() as client:
    response = await get_all_products.asyncio_detailed(
        client=client,
        limit=50,
    )
    # response.parsed contains ALL aggregated results, not just the first page.
```

The transport layer detects paginated responses, follows `next` links, and aggregates
all results into a single response. Transparent to API method callers.

______________________________________________________________________

### 4. Defer Observability to httpx

**Pattern:** Use httpx's built-in event hooks for observability instead of custom
instrumentation.

```python
async def log_request(request):
    print(f"Request: {request.method} {request.url}")

async def log_response(response):
    print(f"Response: {response.status_code}")

client = httpx.AsyncClient(
    event_hooks={"request": [log_request], "response": [log_response]},
)
```

**Benefits:** standard httpx patterns, no custom instrumentation, works with existing
tools (OpenTelemetry, Sentry, etc.).

______________________________________________________________________

### 5. Sync and Async APIs

Each generated endpoint exposes both:

```python
# Async (recommended)
async with KatanaClient() as client:
    response = await get_all_products.asyncio_detailed(client=client)

# Sync (for simple scripts)
with KatanaClient() as client:
    response = get_all_products.sync_detailed(client=client)
```

**Trade-offs:** async gives better concurrency and non-blocking I/O; sync is simpler for
scripts that don't need an event loop.

______________________________________________________________________

### 6. Response Unwrapping Utilities

**Pattern:** typed helpers in `katana_public_api_client.utils` replace manual
status-code inspection.

```python
from katana_public_api_client.utils import (
    unwrap, unwrap_as, unwrap_data, is_success, is_error,
)
from katana_public_api_client.domain.converters import unwrap_unset, to_unset

# Single object (200 OK)
order = unwrap_as(response, ManufacturingOrder)

# List endpoint (200 OK with `data` array)
items = unwrap_data(response, default=[])

# Success-only (201 Created, 204 No Content)
if is_success(response):
    ...

# attrs model fields that may be UNSET
status = unwrap_unset(order.status, default=None)
```

**Exception hierarchy raised by `unwrap` / `unwrap_as`:**

- `AuthenticationError` (401)
- `ValidationError` (422)
- `RateLimitError` (429)
- `ServerError` (5xx)
- `APIError` (other)

For the full pattern table (when to use each helper, anti-patterns to avoid), see the
[Client Guide](../../../../katana_public_api_client/docs/guide.md) "Response Handling"
section.

______________________________________________________________________

### 7. Domain Helper Classes

**Pattern:** High-level helpers in `katana_public_api_client/helpers/` and
`katana_public_api_client/domain/` provide simpler interfaces for common workflows
(search, products, materials, variants, services).

```python
from katana_public_api_client import KatanaClient
from katana_public_api_client.helpers.search import search_items

async with KatanaClient() as client:
    matches = await search_items(client=client, query="widget")
```

______________________________________________________________________

### 8. Pydantic Domain Models

**Pattern:** Use pydantic models alongside the attrs-generated wire models for business
entities, validation, and the typed cache.

The pydantic surface is generated alongside the attrs surface (see Pattern 2). The typed
cache sibling classes (`Cached<Name>`) inherit from these pydantic models with SQLModel
annotations attached.

______________________________________________________________________

### 9. Validation Tiers for Agent Workflows

**Pattern:** Four-tier validation system — `quick-check` / `agent-check` / `check` /
`full-check` — for different workflow stages.

See [VALIDATION_TIERS.md](VALIDATION_TIERS.md) for the tier-by-tier breakdown and
[CLAUDE.md "Essential Commands"](../../../../CLAUDE.md) for current timings.

______________________________________________________________________

### 10. Katana MCP Server

**Pattern:** Model Context Protocol server (`katana_mcp_server/`) exposes Katana
operations to AI agents via tools, resources, and prompts.

**Architecture areas (subsystem-specific guides own the details):**

- **Tools** — preview/apply pattern with Prefab UI cards. See
  [`katana_mcp_server/docs/prefab/README.md`](../../../../katana_mcp_server/docs/prefab/README.md).
- **Typed cache** — SQLite-backed mirror with FTS5 fuzzy search. See
  [`katana_mcp_server/docs/typed_cache/README.md`](../../../../katana_mcp_server/docs/typed_cache/README.md).
- **Help resources** — progressive-discovery doc surface at `katana://help/*` (the
  canonical "what tools/resources exist?" — never enumerate them in this guide; they
  drift on every PR).

**Integration (Claude Desktop):**

```json
{
  "mcpServers": {
    "katana": {
      "command": "uvx",
      "args": ["katana-mcp-server"],
      "env": { "KATANA_API_KEY": "your-api-key" }
    }
  }
}
```

______________________________________________________________________

### 11. uv Package Manager

**Pattern:** Use uv for fast, reliable Python package management in monorepo.

```bash
uv sync --all-extras        # Install/update dependencies
uv run poe <task>           # Run tasks in virtual environment
uv add <package>            # Add dependency
```

**Benefits:** 10-100× faster than pip; single lockfile across the workspace; compatible
with PyPI.

______________________________________________________________________

### 12. Module-Local Documentation

**Pattern:** Each package has its own `docs/` directory with package-specific
documentation; the root `docs/` holds shared/monorepo content.

```
docs/                                # Shared/monorepo (CONTRIBUTING, RELEASE, ADRs)
  └── adr/
katana_public_api_client/docs/       # Client-specific (guide, testing, spec-authoring, ADRs)
  └── adr/
katana_mcp_server/docs/              # MCP-specific (architecture, prefab/, typed_cache/, ADRs)
  └── adr/
```

**Benefits:** documentation lives next to the code, clear ownership, easy to find.

______________________________________________________________________

## Common Patterns

### Error Handling

Use the unwrap helpers (Pattern 6) — they convert status codes into typed exceptions.
Don't write manual `if response.status_code == 200` checks. Full anti-pattern table in
CLAUDE.md.

### Testing Patterns

- Use `httpx.MockTransport` for HTTP-level mocks.
- Conftest fixtures in `tests/conftest.py` and `katana_mcp_server/tests/conftest.py`
  provide common scaffolding.
- Browser-render tests for Prefab UI live in `katana_mcp_server/tests/browser/` and run
  as Tier 3 (`uv run poe test-browser`).
- See the [Client Testing Guide](../../../../katana_public_api_client/docs/testing.md)
  for the test architecture.

### Environment Configuration

```bash
# .env file
KATANA_API_KEY=your-api-key-here
KATANA_BASE_URL=https://api.katanamrp.com/v1   # Optional; default exists
```

```python
async with KatanaClient() as client:
    pass

# Or explicit:
async with KatanaClient(api_key="explicit-key", base_url="https://custom.api.com") as client:
    pass
```

______________________________________________________________________

## Technology Stack

The lockfile (`uv.lock`) and `pyproject.toml` are the source of truth for exact
versions. High-level shape:

- **Python**: 3.11+ (see `pyproject.toml` for the supported range).
- **httpx**: async HTTP client.
- **attrs** + **pydantic**: data classes (attrs from generated wire models, pydantic for
  validation and the typed cache).
- **SQLModel** + **SQLite/FTS5**: typed cache layer (MCP).
- **uv**: package management.
- **ruff**, **ty**, **pyright**: linting + type checking.
- **pytest**, **pytest-xdist**, **playwright**: testing (incl. headless browser).
- **poethepoet**: task runner (`uv run poe ...`).
- **openapi-python-client**, **datamodel-codegen**, **Redocly**: code generation.
- **MkDocs** + **mkdocstrings**: documentation site.

______________________________________________________________________

## ADR Indexes

ADRs are indexed per scope:

- **Shared / monorepo** — [docs/adr/README.md](../../../../docs/adr/README.md)
- **Client package** —
  [katana_public_api_client/docs/adr/README.md](../../../../katana_public_api_client/docs/adr/README.md)
- **MCP server** —
  [katana_mcp_server/docs/adr/README.md](../../../../katana_mcp_server/docs/adr/README.md)

The ADRs share a single sequential numbering pool across all three directories — see the
shared ADR README for the conventions.

______________________________________________________________________

## Quick Links

- **[CLAUDE.md](../../../../CLAUDE.md)** — session-level guidance.
- **[CONTRIBUTING.md](../../../../docs/CONTRIBUTING.md)** — contribution guidelines
  (incl. the "no hand-maintained drift-prone references" rule).
- **[Client Guide](../../../../katana_public_api_client/docs/guide.md)** — user guide
  for the Python client.
- **[Spec Authoring](../../../../katana_public_api_client/docs/spec-authoring.md)** —
  OpenAPI editing conventions.
- **[Prefab UI Pitfalls](../../../../katana_mcp_server/docs/prefab/README.md)** —
  rendering contracts for MCP tool cards.
- **[Typed Cache Patterns](../../../../katana_mcp_server/docs/typed_cache/README.md)** —
  archive/deleted flags, cross-entity ID handling, cache vs API class boundaries.

______________________________________________________________________

## Summary

**Key Architectural Principles:**

1. **Transport-Layer Resilience** — single point for retries, rate limiting, pagination.
1. **Code Generation** — OpenAPI spec drives a two-pass client generation (attrs +
   pydantic).
1. **Separation of Concerns** — generated vs editable code (see FILE_ORGANIZATION.md).
1. **Validation Tiers** — right validation at right time (see VALIDATION_TIERS.md).
1. **Monorepo Structure** — Python client + MCP server + TypeScript client with shared
   tooling.
1. **Module-Local Docs** — documentation lives with the code it describes.
1. **uv for Speed** — fast, reliable package management.

When in doubt about an architectural decision, read the relevant ADR — the indexes above
are the entry points.
