# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in
this repository.

## Essential Commands

### Development Workflow

- **Setup**: `uv sync --all-extras`
- **Format code**: `uv run poe format`
- **Lint code**: `uv run poe lint` (11 seconds, NEVER CANCEL)
- **Run tests**: `uv run poe test` (27 seconds, NEVER CANCEL)
- **Quick check**: `uv run poe check` (40 seconds - runs format-check + lint + test)
- **Auto-fix issues**: `uv run poe fix`

### Testing Commands

- **Basic tests**: `uv run poe test`
- **With coverage**: `uv run poe test-coverage` (39 seconds, NEVER CANCEL)
- **Unit tests only**: `uv run poe test-unit`
- **Integration tests**: `uv run poe test-integration` (requires KATANA_API_KEY in .env)

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

This is a Python client for the Katana Manufacturing ERP API built with
**transport-layer resilience**.

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
    response = await get_all_products.asyncio_detailed(
        client=client, limit=50  # Auto-pagination if needed
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

### Key Documentation Files

- **[README.md](README.md)** - Project overview and quick start
- **[CLAUDE.md](CLAUDE.md)** - This file - guidance for Claude Code
- **[docs/KATANA_CLIENT_GUIDE.md](docs/KATANA_CLIENT_GUIDE.md)** - User guide for the
  client
- **[docs/TESTING_GUIDE.md](docs/TESTING_GUIDE.md)** - Testing strategy and coverage
  analysis
- **[docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)** - Contribution guidelines
- **[docs/adr/](docs/adr/)** - Architecture Decision Records (ADRs)

### Architecture Decision Records (ADRs)

**Location**: [docs/adr/](docs/adr/)

ADRs document key architectural decisions with their context and consequences. See
[docs/adr/README.md](docs/adr/README.md) for the full index.

**Accepted ADRs** (Core Architecture):

- **[ADR-001](docs/adr/0001-transport-layer-resilience.md)**: Transport-Layer Resilience
  Pattern
- **[ADR-002](docs/adr/0002-openapi-code-generation.md)**: Generate Client from OpenAPI
  Specification
- **[ADR-003](docs/adr/0003-transparent-pagination.md)**: Transparent Automatic
  Pagination
- **[ADR-004](docs/adr/0004-defer-observability-to-httpx.md)**: Defer Observability to
  httpx
- **[ADR-005](docs/adr/0005-sync-async-apis.md)**: Provide Both Sync and Async APIs
- **[ADR-006](docs/adr/0006-response-unwrapping-utilities.md)**: Response Unwrapping
  Utilities

**Proposed ADRs** (Under Consideration):

- **[ADR-007](docs/adr/0007-domain-helper-classes.md)**: Generate Domain Helper Classes
  (PROPOSED)
- **[ADR-008](docs/adr/0008-avoid-builder-pattern.md)**: Avoid Traditional Builder
  Pattern (PROPOSED)

When making architectural decisions or understanding design choices, **consult the ADRs
first** - they explain the "why" behind the codebase structure.

## Development Environment

### Tool Configuration

All tools are configured in `pyproject.toml` (no separate config files):

- **Poetry**: Package metadata and dependencies
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
- `uv run poe test`: ~27 seconds (timeout: 30+ minutes)
- `uv run poe test-coverage`: ~39 seconds (timeout: 45+ minutes)
- `uv run poe check`: ~40 seconds (timeout: 60+ minutes)
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

This project uses **semantic-release** with conventional commits:

- **`feat:`** - New features (MINOR version bump)
- **`fix:`** - Bug fixes (PATCH version bump)
- **`chore:`** - Development/tooling (NO version bump)
- **`docs:`** - Documentation only (NO version bump)
- **`test:`** - Test changes (NO version bump)
- **`refactor:`** - Code refactoring (NO version bump)

**Breaking changes**: Use `!` after type (e.g., `feat!:`) for MAJOR version bump

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
