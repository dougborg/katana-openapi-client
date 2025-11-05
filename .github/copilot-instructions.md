# AI Agent Instructions for Katana OpenAPI Client

**CRITICAL: Follow these instructions completely and precisely before attempting any
other actions. Only fallback to additional search or context gathering if the
information in these instructions is incomplete or found to be in error.**

## Quick Reference - Essential Commands

**Development validation tiers:**

- `uv run poe quick-check` - Format + lint only (~5-10s) - **Use during development**
- `uv run poe agent-check` - Format + lint + mypy (~10-15s) - **Use before committing**
- `uv run poe check` - Full validation (~40s) - **Required before opening PR**
- `uv run poe full-check` - Everything including docs (~50s) - **Use before requesting
  review**

**Common tasks:**

- `uv sync --all-extras` - Install/update all dependencies (~5-10s)
- `uv run poe format` - Format code (~2s)
- `uv run poe lint` - Run linting (~11s)
- `uv run poe test` - Run tests (~27s)
- `uv run poe help` - List all available tasks

**Complete workflow documentation:** See [AGENT_WORKFLOW.md](../AGENT_WORKFLOW.md) for
detailed step-by-step instructions.

______________________________________________________________________

## Project Setup

### System Requirements

- **Python**: 3.11, 3.12, or 3.13 supported
- **uv**: Latest version (package and environment manager)
- **Node.js**: 20+ for OpenAPI validation tools
- **npm/npx**: For OpenAPI code generation

### Initial Setup (First Time)

```bash
# 1. Install uv (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Install all dependencies (~5-10 seconds)
# NEVER CANCEL - set timeout to 30+ minutes for safety
uv sync --all-extras

# 3. Create .env file for credentials
cp .env.example .env
# Edit .env and add your KATANA_API_KEY

# 4. Install pre-commit hooks (optional, may fail in restricted networks)
uv run pre-commit install

# 5. Verify installation
uv run poe quick-check
```

### Understanding uv and poe

**uv** (Universal Virtualenv) is our package and environment manager:

- Replaces pip, virtualenv, and Poetry
- Extremely fast dependency resolution and installation
- Automatic virtual environment management
- Compatible with standard Python packaging (PEP 621)

**poe** (poethepoet) is our task runner:

- Defines common development workflows in `pyproject.toml`
- Combines multiple tools into single commands
- Cross-platform compatibility

**Always use: `uv run poe <task>`** to ensure commands run in the correct environment.

______________________________________________________________________

## Validation Tiers (CRITICAL)

Use the appropriate validation tier for your current workflow stage:

### Tier 1: quick-check (~5-10s)

**When:** During active development, rapid iteration **Command:**
`uv run poe quick-check` **Runs:** Format check + ruff linting only **Use for:** Fast
feedback while coding

### Tier 2: agent-check (~10-15s)

**When:** Before committing changes **Command:** `uv run poe agent-check` **Runs:**
Format check + ruff linting + mypy type checking **Use for:** Pre-commit validation

### Tier 3: check (~40s)

**When:** Before opening PR (REQUIRED) **Command:** `uv run poe check` **Runs:** Format
check + lint + test **Use for:** PR readiness check **CRITICAL:** PR must pass this
check before opening!

### Tier 4: full-check (~50s)

**When:** Before requesting review **Command:** `uv run poe full-check` **Runs:**
Everything including docs build **Use for:** Final validation before review

**NEVER CANCEL** any validation command before timeout. Set generous timeouts (30-60+
minutes).

______________________________________________________________________

## Development Workflow

### Before Making Changes

```bash
# 1. Create feature branch
git checkout -b feature/<issue-number>-<description>

# 2. Sync dependencies
uv sync --all-extras

# 3. Run quick validation
uv run poe quick-check
```

### During Development

```bash
# Make changes
vim src/file.py

# Quick validation (fast feedback)
uv run poe quick-check

# Auto-fix issues
uv run poe fix

# Continue iterating
```

### Before Committing

```bash
# Pre-commit validation (required)
uv run poe agent-check

# If passing, commit changes
git add .
git commit -m "feat: add new feature"

# Note: pre-commit hooks will run automatically if installed
```

### Before Opening PR

```bash
# Full PR validation (REQUIRED)
uv run poe check

# If all checks pass, push and open PR
git push -u origin feature/<issue-number>-<description>
gh pr create
```

### PR Readiness Requirements (CRITICAL)

**Before opening a PR, you MUST:**

1. ✅ Run `uv run poe check` and ensure all checks pass
1. ✅ Verify all tests pass (no failures, no errors)
1. ✅ Ensure code is formatted (ruff format)
1. ✅ Fix all linting errors (ruff check)
1. ✅ Fix all type errors (mypy)
1. ✅ Write conventional commit messages

**A PR is NOT ready if:**

- ❌ `uv run poe check` fails
- ❌ Any tests are failing
- ❌ Linting errors exist
- ❌ Type checking errors exist
- ❌ Code is not formatted

______________________________________________________________________

## Available poe Tasks

### Code Quality

```bash
uv run poe format          # Format code (ruff + mdformat)
uv run poe format-check    # Check formatting without changes
uv run poe lint            # Run all linting (ruff + mypy + yamllint)
uv run poe fix             # Auto-fix formatting and linting issues
```

### Testing

```bash
uv run poe test                # Run basic test suite (4 workers, ~16s)
uv run poe test-sequential     # Run tests sequentially if needed (~25s)
uv run poe test-coverage       # Run tests with coverage (~22s)
uv run poe test-unit           # Unit tests only
uv run poe test-integration    # Integration tests (needs KATANA_API_KEY)
uv run poe test-schema         # Schema validation tests (excluded by default)
```

**Note**: Tests use pytest-xdist with 4 workers (optimal for performance). Schema
validation tests are excluded from default runs due to pytest-xdist collection issues
but can be run explicitly with `uv run poe test-schema`.

### Validation Tiers

```bash
uv run poe quick-check     # Tier 1: Fast validation (~5-10s)
uv run poe agent-check     # Tier 2: Pre-commit validation (~10-15s)
uv run poe check           # Tier 3: PR validation (~30s) - REQUIRED
uv run poe full-check      # Tier 4: Full validation (~40s)
```

### Documentation

```bash
uv run poe docs-build      # Build documentation (~2.5 minutes)
uv run poe docs-serve      # Serve docs locally with live reload
uv run poe docs-clean      # Clean documentation build artifacts
```

### OpenAPI

```bash
uv run poe validate-openapi         # Validate OpenAPI spec
uv run poe regenerate-client        # Regenerate client code (~2+ minutes)
```

### Utilities

```bash
uv run poe help            # List all available tasks
uv run poe --help          # Show poe command options
```

______________________________________________________________________

## Pre-commit Hooks

This project has TWO pre-commit configurations:

### Lite Config (.pre-commit-config-lite.yaml)

**When:** Fast iteration during development **Speed:** ~5-10 seconds **Runs:** Format
checking + basic linting only **Install:**
`uv run pre-commit install --config .pre-commit-config-lite.yaml`

### Full Config (.pre-commit-config.yaml)

**When:** Before pushing to remote **Speed:** ~12-15 seconds (with parallel tests)
**Runs:** Full validation including tests **Install:** `uv run pre-commit install`

**Network Issues:** Pre-commit installation may fail in restricted environments. This is
expected and can be skipped.

______________________________________________________________________

## Architecture Overview

### Core Components

- **`katana_public_api_client/katana_client.py`** - Main client with
  `ResilientAsyncTransport`
- **`katana_public_api_client/api/`** - 76+ generated API endpoint modules (DO NOT EDIT)
- **`katana_public_api_client/models/`** - 150+ generated data models (DO NOT EDIT)
- **`katana_public_api_client/domain/`** - Pydantic domain models (EDIT THESE)
- **`katana_public_api_client/helpers/`** - Helper classes for common operations
- **`katana_mcp_server/`** - MCP server implementation (separate package)

### Key Architectural Pattern: Transport-Layer Resilience

Instead of wrapping API methods, resilience is implemented at the httpx transport layer.
This means ALL API calls through `KatanaClient` automatically get retries, rate
limiting, and pagination without any code changes needed in the generated client.

```python
from katana_public_api_client import KatanaClient
from katana_public_api_client.api.product import get_all_products

async with KatanaClient() as client:
    # Automatic retries, rate limiting, and pagination
    response = await get_all_products.asyncio_detailed(
        client=client, limit=50
    )
```

### File Organization Rules

**DO NOT EDIT (Generated Files):**

- `katana_public_api_client/api/**/*.py`
- `katana_public_api_client/models/**/*.py`
- `katana_public_api_client/client.py`
- `katana_public_api_client/client_types.py`
- `katana_public_api_client/errors.py`

**EDIT THESE FILES:**

- `katana_public_api_client/katana_client.py`
- `katana_public_api_client/domain/**/*.py`
- `katana_public_api_client/helpers/**/*.py`
- `tests/`
- `scripts/`
- `docs/`

______________________________________________________________________

## Conventional Commits (CRITICAL)

This project uses **semantic-release** with conventional commits and **scopes** for
monorepo versioning.

### Commit Scopes for Package Releases

- **`feat(client):`** / **`fix(client):`** - Releases **katana-openapi-client**
  (MINOR/PATCH)
- **`feat(mcp):`** / **`fix(mcp):`** - Releases **katana-mcp-server** (MINOR/PATCH)
- **`feat:`** / **`fix:`** (no scope) - Releases **katana-openapi-client** (default)

### Other Commit Types (No Version Bump)

- **`chore:`** - Development/tooling
- **`docs:`** - Documentation only
- **`test:`** - Test changes
- **`refactor:`** - Code refactoring
- **`ci:`** - CI/CD changes

### Breaking Changes

Use `!` after type (e.g., `feat(client)!:`) for MAJOR version bump

**Examples:**

```bash
# Release client package
git commit -m "feat(client): add Products domain helper"

# Release MCP server package
git commit -m "feat(mcp): add inventory management tools"

# No release (documentation only)
git commit -m "docs: update README"
```

______________________________________________________________________

## Common Pitfalls

1. **Never cancel long-running commands** - Set generous timeouts (30-60+ minutes)
1. **Always use `uv run poe <task>`** - Don't run commands directly
1. **Generated code is read-only** - Use regeneration script instead of editing
1. **Integration tests need credentials** - Set `KATANA_API_KEY` in `.env`
1. **Conventional commits matter** - Wrong types trigger unwanted releases
1. **PR must pass `check` before opening** - This is non-negotiable
1. **Use correct import paths** - Direct imports from `katana_public_api_client.api` (no
   `.generated`)
1. **Client types import** - Use `from katana_public_api_client.client_types import`
   instead of `types`

______________________________________________________________________

## Command Timeout Reference (CRITICAL)

**NEVER CANCEL these commands before the timeout:**

| Command                        | Expected Time  | Timeout Setting |
| ------------------------------ | -------------- | --------------- |
| `uv sync --all-extras`         | ~5-10 seconds  | 30+ minutes     |
| `uv run poe quick-check`       | ~5-10 seconds  | 15+ minutes     |
| `uv run poe agent-check`       | ~10-15 seconds | 20+ minutes     |
| `uv run poe lint`              | ~11 seconds    | 15+ minutes     |
| `uv run poe test`              | ~16 seconds    | 30+ minutes     |
| `uv run poe test-coverage`     | ~22 seconds    | 45+ minutes     |
| `uv run poe check`             | ~30 seconds    | 60+ minutes     |
| `uv run poe full-check`        | ~40 seconds    | 60+ minutes     |
| `uv run poe docs-build`        | ~2.5 minutes   | 60+ minutes     |
| `uv run poe regenerate-client` | ~2+ minutes    | 60+ minutes     |

**Remember**: Always set generous timeouts. Network delays and package compilation can
extend these times significantly.

______________________________________________________________________

## Additional Resources

- **[AGENT_WORKFLOW.md](../AGENT_WORKFLOW.md)** - Complete step-by-step workflow for AI
  agents
- **[CLAUDE.md](../CLAUDE.md)** - Claude Code specific instructions
- **[CONTRIBUTING.md](docs/CONTRIBUTING.md)** - Contribution guidelines
- **[TESTING_GUIDE.md](docs/TESTING_GUIDE.md)** - Testing strategy and coverage
- **[docs/adr/](docs/adr/)** - Architecture Decision Records

______________________________________________________________________

**Final Reminder**: These instructions are based on exhaustive testing of every command.
Follow them exactly and **NEVER CANCEL** long-running operations. Use the appropriate
validation tier for your workflow stage, and always run `uv run poe check` before
opening a PR.
