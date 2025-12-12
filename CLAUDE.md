# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in
this repository.

## Agent Workflow Guide

**NEW:** For complete step-by-step workflow instructions, validation tiers, and parallel
agent coordination strategies, see **[AGENT_WORKFLOW.md](AGENT_WORKFLOW.md)**.

## Quick Start

### Using GitHub Codespaces (Recommended for Agents)

This repository has a fully configured devcontainer with **prebuilds** for instant
startup:

1. **Open in Codespaces**: Click "Code" → "Codespaces" → "Create codespace on main"
1. **Wait ~30 seconds**: Prebuild loads cached environment (uv, dependencies, tools)
1. **Start working**: Everything is ready - no setup needed!

The prebuild includes:

- ✅ uv package manager pre-installed
- ✅ All Python dependencies cached
- ✅ Pre-commit hooks installed
- ✅ VS Code extensions configured

**Configuration**: See `.devcontainer/` directory for details.

### Local Development

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Setup project
uv sync --all-extras
uv run pre-commit install

# Create .env file
cp .env.example .env  # Add your KATANA_API_KEY
```

## Essential Commands

### Validation Tiers (Use the Right One!)

- **`uv run poe quick-check`** (~5-10s) - Format + lint only → Use during development
- **`uv run poe agent-check`** (~8-12s) - Format + lint + ty → Use before committing
- **`uv run poe check`** (~30s) - Full validation → **REQUIRED before opening PR**
- **`uv run poe full-check`** (~40s) - Everything + docs → Use before requesting review

### Development Workflow

- **Setup**: `uv sync --all-extras`
- **Format code**: `uv run poe format`
- **Lint code**: `uv run poe lint` (11 seconds, NEVER CANCEL)
- **Run tests**: `uv run poe test` (16 seconds with 4 workers, NEVER CANCEL)
- **Auto-fix issues**: `uv run poe fix`

## CRITICAL: Zero Tolerance for Ignoring Errors - ABSOLUTE REQUIREMENT

**NEVER say "but these were pre-existing issues so they are fine to ignore" or ANYTHING
like that. This is FORBIDDEN.**

When asked to fix linting, type checking, or test errors:

- **FIX THE ACTUAL ISSUES** - do not use `noqa`, `type: ignore`, exclusions, or skips
- **NO SHORTCUTS** - do not exclude files from linting, skip tests, or ignore type
  errors
- **NO EXCUSES** - "unrelated to my changes" is not a valid reason to ignore errors
- **NO RATIONALIZING** - if you think you have a good reason to ignore an error, you are
  wrong
- **AGENT CODE IS NOT SACRED** - code written by agents must meet the same quality
  standards
- **REFACTOR INSTEAD** - if a function has too many parameters, use a dataclass; if a
  name conflicts with a built-in, rename it
- **ASK FIRST** - only use ignores/exclusions after explicitly asking and receiving
  permission
- **PRE-EXISTING ISSUES ARE NOT EXCUSES** - ALL tests must pass, ALL linting must pass,
  regardless of when the issues were introduced
- If you are unsure how to fix an error properly, ask the user for guidance
- The only acceptable solution is fixing the root cause of the error

**Examples of proper fixes:**

- Too many function parameters (PLR0917)? → Create a dataclass to group related
  parameters
- Method name shadows built-in (type checker error)? → Rename the method (e.g., `list()`
  → `find_all()`)
- Import causing circular dependency? → Restructure the code or use `TYPE_CHECKING`
  block

### MANDATORY COMPLETION CHECKLIST

**Before ANY coding task is considered complete, ALL of the following MUST be true:**

1. **ALL tests pass** - This includes:

   - Tests for new code you wrote
   - ALL existing tests (even if they were broken before)
   - Tests that seem unrelated to your changes
   - Integration tests, unit tests, all test suites
   - **NO EXCEPTIONS** - if a test was broken before, fix it

1. **ALL linting and formatting pass** - This includes:

   - Ruff linting with zero errors
   - Code formatting with zero issues
   - Type checking with zero errors
   - **NO EXCEPTIONS** - if there were linting errors before, fix them

1. **Code is committed** - All changes must be committed to git with appropriate commit
   messages

1. **Code is pushed to a feature branch** - If not already on a feature branch, create
   one and push the changes

**Verification commands:**

```bash
# Run these and ensure ALL pass with zero errors
uv run poe check          # Lint, type-check, and test
uv run poe test           # All tests must pass
uv run poe lint           # All linting must pass
git status                 # Verify all changes are committed
git branch                 # Verify you're on a feature branch
```

### Testing Commands

- **Basic tests**: `uv run poe test` (4 workers, ~16s)
- **Sequential tests**: `uv run poe test-sequential` (if parallel has issues, ~25s)
- **With coverage**: `uv run poe test-coverage` (~22 seconds, NEVER CANCEL)
- **Unit tests only**: `uv run poe test-unit`
- **Integration tests**: `uv run poe test-integration` (requires KATANA_API_KEY in .env)
- **Schema validation**: `uv run poe test-schema` (excluded by default, run explicitly)

**Note**: Tests use pytest-xdist for parallel execution. Schema validation tests are
excluded by default due to pytest-xdist collection issues.

### OpenAPI and Client Management

- **Validate schema**: `uv run poe validate-openapi`
- **Regenerate client**: `uv run poe regenerate-client` (2+ minutes, NEVER CANCEL)
- **Validate with Redocly**: `uv run poe validate-openapi-redocly`

### Documentation

- **Build docs**: `uv run poe docs-build` (2.5 minutes, NEVER CANCEL)
- **Serve locally**: `uv run poe docs-serve`
- **Clean docs**: `uv run poe docs-clean`

### Task Runner

- **List all tasks**: `uv run poe help`
- **Combined workflows**: `uv run poe ci`, `uv run poe prepare`

## Architecture Overview

This is a multi-package repository (monorepo) containing clients for the Katana
Manufacturing ERP API:

- **Python Client** (`katana_public_api_client/`) - Full-featured with transport-layer
  resilience
- **MCP Server** (`katana_mcp_server/`) - Model Context Protocol server for AI
  assistants
- **TypeScript Client** (`packages/katana-client/`) - Browser-compatible with full type
  safety

### Python Client Architecture

The Python client is built with **transport-layer resilience**.

### Core Components

**Main Client Classes:**

- `katana_public_api_client/katana_client.py` - Enhanced client with
  `ResilientAsyncTransport` providing automatic retries, rate limiting, and pagination
- `katana_public_api_client/client.py` - Generated base client classes
  (AuthenticatedClient, Client)

**Generated API Structure:**

- `katana_public_api_client/api/` - 76+ generated API endpoint modules organized by
  resource (DO NOT EDIT)
- `katana_public_api_client/models/` - 150+ generated data models (DO NOT EDIT)
- `katana_public_api_client/client_types.py` - Type definitions (renamed from types.py
  to avoid stdlib conflicts)

**Key Architecture Pattern - Transport-Layer Resilience:** Instead of wrapping API
methods, resilience is implemented at the httpx transport layer. This means ALL API
calls through `KatanaClient` automatically get retries, rate limiting, and pagination
without any code changes needed in the generated client.

**Retry Strategy:**

- **429 Rate Limiting**: ALL HTTP methods (including POST/PATCH) are retried
  automatically with exponential backoff (1s, 2s, 4s, 8s, 16s) and `Retry-After` header
  support
- **502/503/504 Server Errors**: Only idempotent methods (GET, PUT, DELETE, HEAD,
  OPTIONS, TRACE) are retried
- **Other 4xx Client Errors**: No retries (these indicate client-side issues)
- **Network Errors**: Automatic retry with exponential backoff

### Usage Patterns

**Use KatanaClient** (provides automatic retries, rate limiting, and pagination):

```python
from katana_public_api_client import KatanaClient
from katana_public_api_client.api.product import get_all_products

async with KatanaClient() as client:
    # Auto-pagination is ON by default - all pages collected automatically
    response = await get_all_products.asyncio_detailed(
        client=client, limit=50  # Sets page size (all pages still collected)
    )

    # Explicit page param disables auto-pagination (get specific page only)
    response = await get_all_products.asyncio_detailed(
        client=client, page=2, limit=50  # Get page 2 only
    )

    # Limit total items collected (via httpx client)
    httpx_client = client.get_async_httpx_client()
    response = await httpx_client.get(
        "/products",
        params={"limit": 50},           # Page size
        extensions={"max_items": 200}   # Stop after 200 items
    )
```

**Note**: All Katana API endpoints require authentication. The `KatanaClient` handles
authentication automatically via `KATANA_API_KEY` environment variable or constructor
parameter.

### File Organization Rules

**DO NOT EDIT (Generated Files):**

- `katana_public_api_client/api/**/*.py`
- `katana_public_api_client/models/**/*.py`
- `katana_public_api_client/client.py`
- `katana_public_api_client/client_types.py`
- `katana_public_api_client/errors.py`
- `katana_public_api_client/py.typed`

**EDIT THESE FILES:**

- `katana_public_api_client/katana_client.py` - Main resilient client
- `katana_public_api_client/log_setup.py` - Logging configuration
- `tests/` - Test files
- `scripts/` - Development scripts
- `docs/` - Documentation

## Documentation Structure

This is a monorepo with module-local documentation. Each package has its own `docs/`
directory.

### Key Documentation Files

**Shared/Monorepo Documentation:**

- **[README.md](README.md)** - Project overview and quick start
- **[CLAUDE.md](CLAUDE.md)** - This file - guidance for Claude Code
- **[docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)** - Contribution guidelines
- **[docs/adr/](docs/adr/)** - Shared/monorepo-level ADRs
- **[docs/UV_USAGE.md](docs/UV_USAGE.md)** - uv package manager guide
- **[docs/MONOREPO_SEMANTIC_RELEASE.md](docs/MONOREPO_SEMANTIC_RELEASE.md)** - Release
  guide

**Client Package Documentation:**

- **[katana_public_api_client/docs/guide.md](katana_public_api_client/docs/guide.md)** -
  Client user guide
- **[katana_public_api_client/docs/testing.md](katana_public_api_client/docs/testing.md)**
  \- Testing strategy
- **[katana_public_api_client/docs/cookbook.md](katana_public_api_client/docs/cookbook.md)**
  \- Usage recipes
- **[katana_public_api_client/docs/adr/](katana_public_api_client/docs/adr/)** - Client
  ADRs

**MCP Server Documentation:**

- **[katana_mcp_server/docs/README.md](katana_mcp_server/docs/README.md)** - MCP docs
  index
- **[katana_mcp_server/docs/architecture.md](katana_mcp_server/docs/architecture.md)** -
  MCP architecture
- **[katana_mcp_server/docs/development.md](katana_mcp_server/docs/development.md)** -
  Development guide
- **[katana_mcp_server/docs/adr/](katana_mcp_server/docs/adr/)** - MCP ADRs

**TypeScript Client Documentation:**

- **[packages/katana-client/README.md](packages/katana-client/README.md)** - TypeScript
  client overview
- **[packages/katana-client/docs/guide.md](packages/katana-client/docs/guide.md)** -
  TypeScript usage guide
- **[packages/katana-client/docs/cookbook.md](packages/katana-client/docs/cookbook.md)**
  \- Usage recipes
- **[packages/katana-client/docs/adr/](packages/katana-client/docs/adr/)** - TypeScript
  ADRs

### Architecture Decision Records (ADRs)

ADRs document key architectural decisions with their context and consequences.

**Client ADRs** -
[katana_public_api_client/docs/adr/](katana_public_api_client/docs/adr/)

Core architectural decisions for the client:

- **[ADR-001](katana_public_api_client/docs/adr/0001-transport-layer-resilience.md)**:
  Transport-Layer Resilience Pattern
- **[ADR-002](katana_public_api_client/docs/adr/0002-openapi-code-generation.md)**:
  Generate Client from OpenAPI Specification
- **[ADR-003](katana_public_api_client/docs/adr/0003-transparent-pagination.md)**:
  Transparent Automatic Pagination
- **[ADR-004](katana_public_api_client/docs/adr/0004-defer-observability-to-httpx.md)**:
  Defer Observability to httpx
- **[ADR-005](katana_public_api_client/docs/adr/0005-sync-async-apis.md)**: Provide Both
  Sync and Async APIs
- **[ADR-006](katana_public_api_client/docs/adr/0006-response-unwrapping-utilities.md)**:
  Response Unwrapping Utilities
- **[ADR-007](katana_public_api_client/docs/adr/0007-domain-helper-classes.md)**:
  Generate Domain Helper Classes
- **[ADR-008](katana_public_api_client/docs/adr/0008-avoid-builder-pattern.md)**: Avoid
  Traditional Builder Pattern (PROPOSED)
- **[ADR-011](katana_public_api_client/docs/adr/0011-pydantic-domain-models.md)**:
  Pydantic Domain Models
- **[ADR-012](katana_public_api_client/docs/adr/0012-validation-tiers-for-agent-workflows.md)**:
  Validation Tiers

**MCP Server ADRs** - [katana_mcp_server/docs/adr/](katana_mcp_server/docs/adr/)

- **[ADR-010](katana_mcp_server/docs/adr/0010-katana-mcp-server.md)**: Create Katana MCP
  Server

**TypeScript Client ADRs** -
[packages/katana-client/docs/adr/](packages/katana-client/docs/adr/)

- **[ADR-001](packages/katana-client/docs/adr/0001-composable-fetch-wrappers.md)**:
  Composable Fetch Wrappers
- **[ADR-002](packages/katana-client/docs/adr/0002-hey-api-code-generation.md)**: Hey
  API Code Generation
- **[ADR-003](packages/katana-client/docs/adr/0003-biome-for-linting.md)**: Biome for
  Linting

**Shared/Monorepo ADRs** - [docs/adr/](docs/adr/)

- **[ADR-009](docs/adr/0009-migrate-from-poetry-to-uv.md)**: Migrate from Poetry to uv

When making architectural decisions or understanding design choices, **consult the ADRs
first** - they explain the "why" behind the codebase structure.

## Development Environment

### Tool Configuration

All tools are configured in `pyproject.toml` (no separate config files):

- **uv**: Package metadata and dependencies
- **Ruff**: Code formatting and linting (replaces Black, isort, flake8)
- **MyPy**: Type checking
- **Pytest**: Test discovery and execution
- **Coverage**: Code coverage reporting
- **Poe**: Task automation
- **Semantic Release**: Automated versioning

### Python and Dependencies

- **Python versions**: 3.11, 3.12, 3.13 supported
- **Package manager**: uv (required - manages virtual environments automatically)
- **Task runner**: poethepoet (poe) - all tasks run via `uv run poe <task>`

### Command Timeouts (CRITICAL)

**NEVER CANCEL** these commands before timeout:

- `uv sync --all-extras`: ~5-10 seconds (timeout: 30+ minutes)
- `uv run poe lint`: ~11 seconds (timeout: 15+ minutes)
- `uv run poe test`: ~16 seconds (timeout: 30+ minutes)
- `uv run poe test-coverage`: ~22 seconds (timeout: 45+ minutes)
- `uv run poe check`: ~30 seconds (timeout: 60+ minutes)
- `uv run poe docs-build`: ~2.5 minutes (timeout: 60+ minutes)
- `uv run poe regenerate-client`: ~2+ minutes (timeout: 60+ minutes)

## Client Generation Process

### Automated Regeneration

The client is generated from `docs/katana-openapi.yaml` using
`scripts/regenerate_client.py`:

1. **Validates** OpenAPI spec with openapi-spec-validator and Redocly
1. **Generates** client using openapi-python-client (npx)
1. **Auto-fixes** code quality with `ruff check --fix --unsafe-fixes`
1. **Moves** generated code to main package location
1. **Runs** final tests and formatting

### Code Quality Automation

The regeneration process uses `ruff --unsafe-fixes` to automatically fix 6,589+ lint
issues including:

- Import sorting and unused imports
- Code style consistency
- Unicode character fixes (×→\* multiplication signs)

No manual patches are required - all fixes are automated.

## API Coverage

The client provides access to all major Katana functionality:

- **Products & Inventory** (25+ endpoints): Products, variants, materials, stock levels
- **Orders** (20+ endpoints): Sales orders, purchase orders, fulfillment
- **Manufacturing** (15+ endpoints): BOMs, manufacturing orders, operations
- **Business Relations** (10+ endpoints): Customers, suppliers, addresses
- **Configuration** (6+ endpoints): Locations, webhooks, custom fields

**Total**: 76+ endpoints with 150+ fully-typed data models

## Testing Strategy

### Test Categories

- **Unit tests** (`-m unit`): Fast tests of individual components
- **Integration tests** (`-m integration`): API integration tests (requires
  KATANA_API_KEY)
- **Documentation tests** (`-m docs`): Slow documentation build tests (CI only)

### Environment Variables

Create `.env` file for credentials:

```bash
KATANA_API_KEY=your-api-key-here
KATANA_BASE_URL=https://api.katanamrp.com/v1  # Optional
```

### Error Patterns

Network/auth errors are expected in tests - use this pattern:

```python
try:
    response = await api_method.asyncio_detailed(client=client)
    assert response.status_code in [200, 404]  # 404 OK for empty test data
except Exception as e:
    error_msg = str(e).lower()
    assert any(word in error_msg for word in ["connection", "network", "auth"])
```

## Commit Standards

This project uses **semantic-release** with conventional commits and **scopes** for
monorepo versioning:

### Commit Scopes for Package Releases

- **`feat(client):`** / **`fix(client):`** - Releases **katana-openapi-client** (MINOR
  /PATCH)
- **`feat(mcp):`** / **`fix(mcp):`** - Releases **katana-mcp-server** (MINOR/PATCH)
- **`feat:`** / **`fix:`** (no scope) - Releases **katana-openapi-client** (default)

### Other Commit Types (No Version Bump)

- **`chore:`** - Development/tooling
- **`docs:`** - Documentation only
- **`test:`** - Test changes
- **`refactor:`** - Code refactoring
- **`ci:`** - CI/CD changes

**Breaking changes**: Use `!` after type (e.g., `feat(client)!:`) for MAJOR version bump

**Examples**:

```bash
# Release client package
git commit -m "feat(client): add Products domain helper"

# Release MCP server package
git commit -m "feat(mcp): add inventory management tools"

# No release (documentation only)
git commit -m "docs: update README"
```

**See**: [docs/MONOREPO_SEMANTIC_RELEASE.md](docs/MONOREPO_SEMANTIC_RELEASE.md) for
complete guide

## Common Pitfalls

1. **Never cancel long-running commands** - Set generous timeouts (30-60+ minutes)
1. **Always use `uv run`** - Don't run commands outside uv environment
1. **Generated code is read-only** - Use regeneration script instead of editing
1. **Integration tests need credentials** - Set `KATANA_API_KEY` in `.env`
1. **Import paths are flattened** - Use direct imports from
   `katana_public_api_client.api` (no `.generated` subdirectory)
1. **Client types import** - Use `from katana_public_api_client.client_types import`
   instead of `types`
1. **Pre-commit may fail** - Network restrictions can cause package download timeouts

## OpenAPI Specification

The OpenAPI spec is located at `docs/katana-openapi.yaml` and represents the
comprehensive Katana Manufacturing ERP API. Key features:

- **OpenAPI 3.1.0** specification
- **100% endpoint coverage** of Katana API
- **Inheritance patterns** with BaseEntity, InventoryItem base schemas
- **Comprehensive validation** with detailed error responses
- **Recent improvements** include date-time formats and schema restructuring for
  inheritance

## MCP Server Implementation

This repository includes a **Model Context Protocol (MCP) server** as a separate package
in the monorepo using uv workspace.

### Key Resources for MCP Work:

- **MCP v0.1.0 Implementation Plan**:
  [katana_mcp_server/docs/implementation-plan.md](katana_mcp_server/docs/implementation-plan.md)
  \- Current plan with 10 tools, 6 resources, 3 prompts
- **MCP Architecture Design**:
  [katana_mcp_server/docs/architecture.md](katana_mcp_server/docs/architecture.md) - MCP
  best practices and patterns
- **ADR-010**:
  [katana_mcp_server/docs/adr/0010-katana-mcp-server.md](katana_mcp_server/docs/adr/0010-katana-mcp-server.md)
  \- Core architecture decisions
- **MCP Documentation Index**:
  [katana_mcp_server/docs/README.md](katana_mcp_server/docs/README.md) - All MCP docs
- **GitHub Issues**:
  [mcp-server label](https://github.com/dougborg/katana-openapi-client/labels/mcp-server)

### MCP Server Structure:

```
katana-openapi-client/          # Repository root (monorepo)
├── pyproject.toml              # Workspace configuration
├── katana_public_api_client/   # Existing client library
└── katana_mcp_server/          # MCP server package
    ├── pyproject.toml          # Depends on client
    ├── src/katana_mcp/
    │   ├── server.py           # FastMCP server
    │   ├── tools/              # 10 tools with elicitation
    │   ├── resources/          # 6 resources (inventory + orders)
    │   └── prompts/            # 3 workflow prompts
    └── tests/
```

### MCP v0.1.0 Scope:

**Design Philosophy**: "Small set of all MCP features to see how everything works
together"

**10 Tools** (all 7 user workflows):

- Inventory: search_variants, get_variant_details, check_inventory
- Catalog: create_product, create_material
- Orders: create_purchase_order, receive_purchase_order, verify_order_document,
  create_manufacturing_order, fulfill_order

**6 Resources** (organized by domain):

- Inventory: items, stock-movements, stock-adjustments
- Orders: sales-orders, purchase-orders, manufacturing-orders

**3 Prompts** (complete workflows):

- create_and_receive_po (workflows #3 + #7)
- verify_and_create_po (workflow #6)
- fulfill_order (workflow #5)

**Key Feature**: Elicitation pattern (preview with confirm=false, execute with
confirm=true)

## TypeScript Client

The TypeScript client is located at `packages/katana-client/` and provides a
browser-compatible API client with the same resilience features as the Python client.

### Key Features:

- **Auto-pagination**: Automatically collects all pages for GET requests (default: on)
- **Retry strategy**: Same as Python client (429 retried for all methods, 5xx for
  idempotent only)
- **Full TypeScript types**: Generated from OpenAPI spec
- **Tree-shakeable**: Import only what you need

### TypeScript Structure:

```
packages/katana-client/
├── package.json              # npm package configuration
├── src/
│   ├── client.ts             # KatanaClient with resilience
│   ├── errors.ts             # Typed error classes
│   └── generated/            # openapi-ts generated SDK
├── docs/
│   ├── guide.md              # Usage guide
│   ├── cookbook.md           # Recipes
│   └── adr/                  # Architecture decisions
└── tests/
```

### Development:

```bash
cd packages/katana-client
pnpm install
pnpm build
pnpm test
```

## Development Workflow

### Before Making Changes

```bash
uv run poe check          # Full validation (~40 seconds)
uv run poe fix            # Auto-fix issues if found
```

### After Making Changes

```bash
uv run poe format         # Format code
uv run poe lint           # Run linting
uv run poe test           # Run tests
uv run poe check          # Final validation
```

### Client Regeneration (when needed)

```bash
uv run poe validate-openapi       # Validate spec first
uv run poe regenerate-client      # Regenerate (~2+ minutes)
uv run poe test                   # Verify client works
```
