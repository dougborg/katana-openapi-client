# File Organization Rules

This project has a clear separation between **generated code** (read-only) and
**editable code** (can be modified). Understanding this distinction is critical to avoid
breaking the codebase.

For the high-level rule, see [CLAUDE.md "File Rules"](../../../../CLAUDE.md); this guide
covers the directory-by-directory specifics, the regen workflow, and the import paths so
you don't edit generated code or import from a path that disappears on regeneration.

## Quick Reference

| Category       | Action            | Files                                                          |
| -------------- | ----------------- | -------------------------------------------------------------- |
| **Editable**   | Can modify freely | Custom client, tests, scripts, docs, config                    |
| **Generated**  | **DO NOT EDIT**   | API endpoints, attrs models, base client, generated pydantic   |
| **Regenerate** | Use script        | `uv run poe regenerate-client && uv run poe generate-pydantic` |

______________________________________________________________________

## Generated Files (DO NOT EDIT)

These files are automatically generated from the OpenAPI specification
(`docs/katana-openapi.yaml`). **Any manual edits will be overwritten** during
regeneration.

### Generated API Endpoint Modules

```
katana_public_api_client/api/**/*.py
```

Endpoint modules are organized by resource (one directory per Katana resource:
`product/`, `sales_order/`, `purchase_order/`, `manufacturing_order/`, `inventory/`,
`customer/`, `supplier/`, `location/`, etc.). The full list is whatever
`docs/katana-openapi.yaml` declares — don't hand-quote a count here, since adding any
new endpoint to the spec changes it.

### Generated Data Models

```
katana_public_api_client/models/**/*.py
```

`attrs`-based data classes for request parameters, response bodies, nested objects, enum
types, and error responses. One file per schema in the OpenAPI spec.

### Generated Pydantic Models

```
katana_public_api_client/models_pydantic/_generated/**/*.py
katana_public_api_client/models_pydantic/_auto_registry.py
```

A second generator pass (`scripts/generate_pydantic_models.py`) emits pydantic mirrors
of the attrs models, plus the sibling `Cached<Name>` SQLModel classes used by the typed
cache. The pydantic surface is what MCP tools and the typed cache layer consume.

**Important:** `models_pydantic/` itself contains both generated and hand-maintained
modules. Only `_generated/` and `_auto_registry.py` are regenerated; the other files in
the directory (`_base.py`, `_mapped_shim.py`, `_pydantic_json.py`, `_registry.py`,
`converters.py`) are hand-maintained pydantic infrastructure and must survive regen.

### Generated Base Client and Type Definitions

```
katana_public_api_client/client.py        # Client / AuthenticatedClient
katana_public_api_client/client_types.py  # Response[T], UNSET, File, etc.
katana_public_api_client/errors.py        # UnexpectedStatus
katana_public_api_client/py.typed         # PEP 561 marker
```

`client_types.py` is renamed from upstream's `types.py` to avoid conflicts with Python's
stdlib `types` module — see "Import Path Conventions" below.

______________________________________________________________________

## Editable Files (Can Modify)

These files are **not generated** and can be edited freely.

### Custom Client Implementation

```
katana_public_api_client/katana_client.py    # KatanaClient + ResilientAsyncTransport
katana_public_api_client/utils.py            # unwrap helpers, error classes
katana_public_api_client/log_setup.py        # Logging config
katana_public_api_client/_logging.py         # Internal logging helpers
katana_public_api_client/domain/             # KatanaProduct/Material/Variant/Service domain models + converters
katana_public_api_client/helpers/            # High-level helpers (search, products, materials, variants, services)
katana_public_api_client/api_wrapper/        # Resource/registry/namespace pydantic-friendly facade
katana_public_api_client/models_pydantic/    # Hand-maintained pydantic infra (excluding _generated/ and _auto_registry.py)
```

**Entry point:** `KatanaClient` (from `katana_public_api_client.katana_client`) is the
main client — it wraps `AuthenticatedClient` with `ResilientAsyncTransport` (retries,
rate limiting, transparent pagination). See ARCHITECTURE_QUICK_REF.md for the
transport-layer pattern.

### Tests, Scripts, Docs, Config

```
tests/**/*.py                              # Client tests
katana_mcp_server/tests/**/*.py            # MCP tests (incl. browser/ for Prefab UI)
scripts/**/*.py                            # Dev automation (regenerate_client.py etc.)
docs/**/*.md                               # Project docs (ADRs, guides)
katana_public_api_client/docs/**/*.md      # Client-package docs
katana_mcp_server/docs/**/*.md             # MCP-package docs
docs/katana-openapi.yaml                   # OpenAPI spec — drives generation
pyproject.toml, uv.lock, .env*             # Package metadata + dependencies
.pre-commit-config.yaml                    # Hooks
.github/, .claude/                         # CI + Claude harness
```

**Special:** `.claude/worktrees/` are parallel agent workspaces — never delete or modify
them from a sibling worktree (see CLAUDE.md "Known Pitfalls").

______________________________________________________________________

## Package Structure

```
katana-openapi-client/                       # Monorepo root
├── pyproject.toml                           # ✅ Package metadata (Python workspace)
├── uv.lock                                  # ✅ Dependency lock
├── .env.example                             # ✅ Environment template
├── README.md                                # ✅ Project overview
├── CLAUDE.md                                # ✅ AI agent instructions
│
├── katana_public_api_client/                # 📦 Python client package
│   ├── katana_client.py                     # ✅ KatanaClient + transport
│   ├── utils.py                             # ✅ unwrap_*/is_success + error classes
│   ├── log_setup.py, _logging.py            # ✅ Logging
│   ├── domain/, helpers/, api_wrapper/      # ✅ High-level helpers
│   ├── client.py, client_types.py, errors.py, py.typed   # 🚫 GENERATED base
│   ├── api/                                 # 🚫 GENERATED endpoints
│   ├── models/                              # 🚫 GENERATED attrs models
│   ├── models_pydantic/
│   │   ├── _generated/, _auto_registry.py   # 🚫 GENERATED pydantic + Cached* siblings
│   │   ├── _base.py, _registry.py, _mapped_shim.py, _pydantic_json.py, converters.py
│   │   │                                    # ✅ Hand-maintained pydantic infrastructure
│   │   └── …
│   └── docs/                                # ✅ Client-package docs (guide, ADRs, spec-authoring)
│
├── katana_mcp_server/                       # 📦 MCP server package
│   ├── pyproject.toml                       # ✅ Independent versioning + scope
│   ├── src/katana_mcp/                      # ✅ Tools, resources, prompts, typed cache
│   ├── tests/                               # ✅ Includes browser/ harness
│   └── docs/                                # ✅ Architecture, prefab/, typed_cache/, ADRs
│
├── packages/katana-client/                  # 📦 TypeScript client package
│   └── …                                    # ✅ Independent npm versioning
│
├── tests/                                   # ✅ Client tests
├── scripts/                                 # ✅ Dev scripts (regenerate_client.py etc.)
├── docs/                                    # ✅ Shared docs (ADRs, CONTRIBUTING, RELEASE)
│   ├── katana-openapi.yaml                  # ✅ OpenAPI spec
│   ├── adr/                                 # ✅ Shared/monorepo ADRs
│   └── upstream-specs/                      # ✅ Cached upstream spec snapshots
│
├── .github/                                 # ✅ Workflows, agent guides
└── .claude/                                 # ✅ Claude harness (skills, agents)
```

______________________________________________________________________

## Client Regeneration Process

When you need to regenerate the client (e.g., after OpenAPI spec changes):

### 1. Audit upstream drift first

Before editing the spec, run the upstream-spec audit. Full workflow in
[`docs/upstream-specs/README.md`](../../../../docs/upstream-specs/README.md):

```bash
uv run poe refresh-upstream-spec      # Pull cached upstream specs (idempotent)
uv run poe audit-spec                 # Request-side drift vs. live gateway
uv run poe validate-response-examples # Response-side drift vs. README.io portal
uv run poe validate-examples          # Local example/schema consistency
```

### 2. Validate the spec

```bash
uv run poe validate-openapi           # openapi-spec-validator
uv run poe validate-openapi-redocly   # Redocly CLI
```

### 3. Regenerate

```bash
uv run poe regenerate-client          # Takes 2+ minutes, NEVER CANCEL
uv run poe generate-pydantic          # Pydantic mirror + Cached<Name> siblings
# Or run both: uv run poe regenerate-all
```

The two passes are deliberately separate but **must both run** — they have to stay in
sync. CLAUDE.md's Known Pitfalls flags drift between them.

### 4. Verify

```bash
uv run poe check                      # Tier 3 validation
```

For the full conventions on regen-in-same-PR and breaking-change markers, see
[COMMIT_STANDARDS.md "Schema and Generator Changes"](COMMIT_STANDARDS.md#schema-and-generator-changes).

For the spec-authoring rules themselves (OpenAPI 3.1, `ListResponse` shape, use-site
descriptions, fix-at-source), see
[`katana_public_api_client/docs/spec-authoring.md`](../../../../katana_public_api_client/docs/spec-authoring.md).

______________________________________________________________________

## Import Path Conventions

### Correct

```python
# Generated API endpoints — flattened, no .generated subdir
from katana_public_api_client.api.product import get_all_products
from katana_public_api_client.api.sales_order import create_sales_order

# Generated attrs models
from katana_public_api_client.models import Product, SalesOrder

# Generated pydantic models
from katana_public_api_client.models_pydantic import PydanticProduct

# Client types — use client_types, NOT types (avoids stdlib conflict)
from katana_public_api_client.client_types import Response, UNSET

# The custom client — use this, not the base AuthenticatedClient
from katana_public_api_client import KatanaClient

# Response handling helpers — use these, not manual status_code checks
from katana_public_api_client.utils import unwrap, unwrap_as, unwrap_data, is_success
from katana_public_api_client.domain.converters import unwrap_unset, to_unset
```

### Incorrect

```python
# DON'T — .generated subdirectory doesn't exist (flattened during regen)
from katana_public_api_client.generated.api.product import get_all_products

# DON'T — conflicts with Python's stdlib types module
from katana_public_api_client.types import Response

# DON'T — use KatanaClient (which adds resilience) instead
from katana_public_api_client.client import AuthenticatedClient
```

______________________________________________________________________

## Common Pitfalls

### Editing generated files

Manual edits to anything under `api/`, `models/`, `models_pydantic/_generated/`,
`_auto_registry.py`, `client.py`, or `client_types.py` are **lost on regen**. Extend
behavior in `katana_client.py`, `domain/`, `helpers/`, or `utils.py` instead.

### Forgetting the second regen pass

After `uv run poe regenerate-client`, also run `uv run poe generate-pydantic` (or just
`uv run poe regenerate-all`). The pydantic + cache schemas must stay in sync with the
attrs surface, otherwise the typed cache will fail to deserialize new fields.

### Wrapping API methods for retries

Don't. Resilience (retries, rate limiting, pagination) is at the **transport layer**.
Every endpoint gets it automatically via `KatanaClient` — see ARCHITECTURE_QUICK_REF.md.

______________________________________________________________________

## Architecture: Transport-Layer Resilience

The architectural pattern that makes this organization work — implementing resilience at
the httpx transport layer instead of wrapping individual API methods — is summarized in
[ARCHITECTURE_QUICK_REF.md](ARCHITECTURE_QUICK_REF.md) and detailed in
[ADR-001](../../../../katana_public_api_client/docs/adr/0001-transport-layer-resilience.md).

The relevance to file organization: because resilience is in `katana_client.py` (not
sprinkled across `api/**/*.py`), the generated tree stays untouched and regeneration
never destroys retry/pagination behavior.

______________________________________________________________________

## Summary

- **Never edit** generated paths: `api/**/*.py`, `models/**/*.py`,
  `models_pydantic/_generated/**`, `models_pydantic/_auto_registry.py`, `client.py`,
  `client_types.py`, `errors.py`, `py.typed`.
- **Always use** `katana_client.py`, `utils.py`, `domain/`, `helpers/`, or
  `api_wrapper/` for custom logic.
- **Regenerate** with `uv run poe regenerate-all` (2+ min — never cancel).
- **Import** from `client_types`, never `types` (stdlib conflict).
- **Use** `KatanaClient`, never the base `AuthenticatedClient` directly.

When in doubt, check whether the file's directory appears in the "Generated Files" list
above.
