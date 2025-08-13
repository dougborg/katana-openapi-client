# AI Agent Instructions for Katana OpenAPI Client

**CRITICAL: Follow these instructions completely and precisely before attempting any
other actions. Only fallback to additional search or context gathering if the
information in these instructions is incomplete or found to be in error.**

## Quick Start - Fresh Clone Setup

Follow these exact commands in order for a fresh clone setup. **NEVER CANCEL any build
or long-running command** - they are expected to take time.

### 1. Install Poetry (Python Package Manager)

```bash
# Install Poetry via pip (network restrictions prevent curl install)
pip install poetry

# Add Poetry to PATH for current session
export PATH="$HOME/.local/bin:$PATH"

# Verify Poetry installation
poetry --version
poetry check
```

**Expected Result**: Poetry 2.1.4+ should be installed successfully.

### 2. Install Project Dependencies

```bash
# Install all project dependencies - NEVER CANCEL, takes 30+ seconds
# TIMEOUT: Set 30+ minutes for safety
poetry install

# Expected time: ~26 seconds
# If failures occur due to network timeouts, retry the command
```

**CRITICAL**: This command **NEVER CANCEL** - may take up to 30 minutes on slow networks
but typically completes in ~26 seconds.

### 3. Verify Installation

```bash
# Test that core imports work
poetry run python -c "import katana_public_api_client; print('✅ Package import successful')"

# Show available development tasks
poetry run poe help
```

## Development Commands - Validated Timings

All commands below have been tested and timed. **NEVER CANCEL** any command before the
timeout expires.

### Code Quality and Formatting

```bash
# Format checking (fastest) - 2 seconds
poetry run poe format-check

# Full formatting - 2 seconds
poetry run poe format

# Python-only formatting - 1 second
poetry run poe format-python

# Markdown formatting - 1 second
poetry run poe format-markdown
```

### Linting and Type Checking

```bash
# Full linting suite - NEVER CANCEL, takes 11 seconds
# TIMEOUT: Set 15+ minutes for safety
poetry run poe lint

# Individual linting commands (faster)
poetry run poe lint-ruff      # 2 seconds - fast linting
poetry run poe lint-mypy      # 8 seconds - type checking
poetry run poe lint-yaml      # 1 second - YAML validation
```

**CRITICAL**: Full linting (`poe lint`) **NEVER CANCEL** - takes ~11 seconds but timeout
to 15+ minutes for safety.

### Testing

```bash
# Basic test suite - NEVER CANCEL, takes 27 seconds
# TIMEOUT: Set 30+ minutes for safety
poetry run poe test

# Test with coverage - NEVER CANCEL, takes 39 seconds
# TIMEOUT: Set 45+ minutes for safety
poetry run poe test-coverage

# Faster individual test categories
poetry run poe test-unit          # Unit tests only
poetry run poe test-integration   # Integration tests only (needs KATANA_API_KEY)
```

**CRITICAL**: Tests **NEVER CANCEL** - take 27-39 seconds but timeout to 30-45+ minutes
for safety.

### Documentation

```bash
# Build documentation - NEVER CANCEL, takes 2.5 minutes
# TIMEOUT: Set 60+ minutes for safety
poetry run poe docs-build

# Clean documentation build
poetry run poe docs-clean

# Serve documentation locally
poetry run poe docs-serve
```

**CRITICAL**: Documentation build **NEVER CANCEL** - takes ~2.5 minutes but timeout to
60+ minutes for safety.

### Combined Workflows

```bash
# Quick development check - NEVER CANCEL, takes ~40 seconds total
# TIMEOUT: Set 60+ minutes for safety
poetry run poe check

# Auto-fix issues - 15 seconds
poetry run poe fix

# Full CI pipeline (will fail on pytest-cov, see Network Limitations)
poetry run poe ci
```

## Pre-commit Hooks Setup

**WARNING**: Pre-commit hooks may fail in network-restricted environments due to PyPI
timeouts.

```bash
# Install pre-commit hooks - may fail due to network restrictions
poetry run poe pre-commit-install

# If successful, run pre-commit on all files - NEVER CANCEL, takes 30+ seconds
# TIMEOUT: Set 60+ minutes for safety
poetry run poe pre-commit-run

# Update hooks (when needed)
poetry run poe pre-commit-update
```

**Network Issue**: Pre-commit installation often fails with `ReadTimeoutError` from
PyPI. This is expected in restricted environments.

## OpenAPI and Client Regeneration

### OpenAPI Validation

```bash
# Basic OpenAPI validation - 3 seconds
poetry run poe validate-openapi

# Advanced validation with Redocly (requires Node.js) - 5 seconds
poetry run poe validate-openapi-redocly

# Run both validators - 8 seconds
poetry run poe validate-all
```

### Client Regeneration

```bash
# Full client regeneration - NEVER CANCEL, can take 2+ minutes
# TIMEOUT: Set 60+ minutes for safety
poetry run poe regenerate-client

# Client regeneration
poetry run python scripts/regenerate_client.py
```

**Note**: The regeneration process is now fully automated using npx to install
openapi-python-client temporarily, and ruff --unsafe-fixes to handle code quality
automatically.

## Manual Functionality Validation

After setup, validate functionality with these scenarios:

### 1. Basic Import Test

```bash
poetry run python -c "
from katana_public_api_client import KatanaClient
from katana_public_api_client.api.product import get_all_products
from katana_public_api_client.models import ProductListResponse
print('✅ All imports successful')
"
```

### 2. Client Instantiation Test

```bash
poetry run python -c "
from katana_public_api_client import KatanaClient
client = KatanaClient(api_key='test-key', base_url='https://test.example.com')
print('✅ Client creation successful')
"
```

### 3. API Usage Pattern Test

```bash
poetry run python -c "
import asyncio
from katana_public_api_client import KatanaClient
from katana_public_api_client.api.product import get_all_products

async def test_api_pattern():
    async with KatanaClient(api_key='test-key', base_url='https://test.example.com') as client:
        # This would make a real API call with proper credentials
        print('✅ API usage pattern valid')

asyncio.run(test_api_pattern())
"
```

## System Requirements and Environment

### Required Software

- **Python**: 3.11, 3.12, or 3.13 (verified: Python 3.12.3 works)
- **pip**: 24.0+ (verified: pip 24.0 works)
- **Node.js**: 20.19.4+ for Redocly validation (verified: available)
- **npm/npx**: 10.8.2+ for OpenAPI tools (verified: available)

### Install Commands for Missing Dependencies

```bash
# If Poetry is not installed
pip install poetry

# If pytest-cov is missing (common issue)
poetry run pip install pytest-cov

# If python-dotenv import fails
poetry run pip install python-dotenv
```

## Network Limitations and Workarounds

This environment has **network restrictions** that cause several commands to fail:

### Known Failing Commands

1. **Pre-commit hooks installation**: Fails with `ReadTimeoutError` from PyPI
1. **Poetry official installer**:
   `curl -sSL https://install.python-poetry.org | python3 -` fails due to DNS resolution

### Working Network Commands

1. **pip install poetry**: Works (uses system pip)
1. **poetry install**: Works (uses Poetry's caching)
1. **npm/npx commands**: Work (including Redocly validation and openapi-python-client)
1. **poetry run pip install**: Works for individual packages

### Workarounds

- Use `pip install poetry` instead of curl installer
- Use `poetry run pip install package-name` for missing packages
- Skip pre-commit setup in network-restricted environments
- Document pre-commit requirements for later setup

## Architecture Overview

This is a production-ready Python client for the Katana Manufacturing ERP API built with
a **transport-layer resilience** approach.

### Core Components

- **`katana_public_api_client/katana_client.py`**: Main client with
  `ResilientAsyncTransport` - all resilience features happen automatically
- **`katana_public_api_client/api/`**: 76+ generated API endpoint modules (flattened
  structure, don't edit directly)
- **`katana_public_api_client/models/`**: 150+ generated data models (flattened
  structure, don't edit directly)
- **`katana_public_api_client/client.py`**: Generated OpenAPI client (base classes)
- **`katana_public_api_client/client_types.py`**: Type definitions (renamed from
  types.py to avoid stdlib conflicts)

### Key Architectural Pattern

**Transport-Layer Resilience**: Instead of wrapping API methods, we intercept at the
httpx transport level. This means ALL API calls through `KatanaClient` get automatic
retries, rate limiting, and pagination without any code changes needed in the generated
client.

```python
# Generated API methods work transparently with resilience:
from katana_public_api_client import KatanaClient
from katana_public_api_client.api.product import get_all_products

async with KatanaClient() as client:
    # This call automatically gets retries, rate limiting, pagination:
    response = await get_all_products.asyncio_detailed(
        client=client, limit=50  # Will auto-paginate if needed
    )
```

## File Organization Rules

### Don't Edit (Generated)

- `katana_public_api_client/api/**/*.py`
- `katana_public_api_client/models/**/*.py`
- `katana_public_api_client/client.py`
- `katana_public_api_client/client_types.py`
- `katana_public_api_client/errors.py`
- `katana_public_api_client/py.typed`

### Edit These Files

- `katana_public_api_client/katana_client.py` - Main resilient client
- `katana_public_api_client/log_setup.py` - Logging configuration
- `tests/` - Test files
- `scripts/` - Development scripts
- `docs/` - Documentation

## Recent Optimizations (2025)

The client generation process has been significantly optimized:

### Automated Code Quality with ruff --unsafe-fixes

The regeneration script now uses `ruff check --fix --unsafe-fixes` to automatically fix
the vast majority of lint issues. This eliminated the need for manual patches and
post-processing.

**Benefits:**

- Fixes 6,589+ lint issues automatically (import sorting, unused imports, code style)
- No manual patches required
- Consistent code quality without maintenance overhead

### Source-Level Problem Prevention

Fixed issues at the OpenAPI specification source instead of post-processing:

- **Unicode multiplication signs**: Fixed `×` to `*` in `katana-openapi.yaml` to prevent
  RUF002 lint errors
- **Non-interactive generation**: Added `--yes` flag to npx commands to prevent hanging

### Streamlined File Organization

- **Eliminated patches/ directory**: All fixes now automated
- **Clear temp directory naming**: `openapi_gen_temp` instead of confusing package names
- **Flattened import structure**: Direct imports without `.generated` subdirectory

**Result**: The regeneration process is now fully automated and requires no manual
intervention.

## Configuration Consolidation

All tool configurations are in `pyproject.toml` following **PEP 621** standards:

- **Project metadata**: `[project]` section
- **MyPy**: `[tool.mypy]` section
- **Pytest**: `[tool.pytest.ini_options]` section
- **Ruff**: `[tool.ruff]` section (replaces Black, isort, flake8)
- **Coverage**: `[tool.coverage]` section
- **Poe Tasks**: `[tool.poe.tasks]` section
- **Semantic Release**: `[tool.semantic_release]` section

No separate `mypy.ini`, `pytest.ini`, or `.flake8` files are used.

## Common Development Workflows

### Before Making Changes

```bash
# 1. Run full development check (~40 seconds)
poetry run poe check

# 2. If issues found, auto-fix what can be fixed
poetry run poe fix

# 3. Install pre-commit hooks (if network allows)
poetry run poe pre-commit-install
```

### After Making Changes

```bash
# 1. Format code
poetry run poe format

# 2. Run linting
poetry run poe lint

# 3. Run tests
poetry run poe test

# 4. Build documentation (if doc changes)
poetry run poe docs-build

# 5. Final validation
poetry run poe check
```

### Integration Testing Requirements

Integration tests require `KATANA_API_KEY` in `.env` file:

```bash
# Create .env file
echo "KATANA_API_KEY=your-actual-api-key" > .env

# Run integration tests
poetry run poe test-integration
```

Without credentials, integration tests are skipped.

## Conventional Commits (CRITICAL)

This project uses **semantic-release** with conventional commits for automated
versioning. **ALWAYS** use the correct commit type:

### Commit Types

- **`feat:`** - New features (triggers MINOR version bump)
- **`fix:`** - Bug fixes (triggers PATCH version bump)
- **`chore:`** - Development/tooling (NO version bump)
- **`docs:`** - Documentation only (NO version bump)
- **`test:`** - Test changes only (NO version bump)
- **`refactor:`** - Code refactoring (NO version bump)
- **`style:`** - Code style (NO version bump)

### Breaking Changes

Use `!` after the type for breaking changes (triggers MAJOR version bump):

```bash
git commit -m "feat!: change KatanaClient constructor signature"
```

## Error Handling Patterns

### Network/Auth Errors in Tests

```python
# Network/auth errors are expected in tests - use this pattern:
try:
    response = await api_method.asyncio_detailed(client=client)
    assert response.status_code in [200, 404]  # 404 OK for empty test data
except Exception as e:
    error_msg = str(e).lower()
    assert any(word in error_msg for word in ["connection", "network", "auth"])
```

### Client Usage Pattern

```python
# CORRECT pattern:
async with KatanaClient() as client:
    response = await some_api_method.asyncio_detailed(
        client=client,  # Pass KatanaClient directly
        param=value
    )

# AVOID: Don't try to enhance/wrap the generated methods
```

## Common Pitfalls

1. **Never cancel builds/tests** - Set long timeouts (30-60+ minutes)
1. **Network timeouts are common** - Retry failed package installations
1. **Use `poetry run`** - Don't run commands outside Poetry environment
1. **Pre-commit may fail** - Network restrictions cause PyPI timeouts
1. **Generated code is read-only** - Use regeneration script instead of editing
1. **Conventional commits matter** - Wrong types trigger unwanted releases
1. **Integration tests need credentials** - Set `KATANA_API_KEY` in `.env`
1. **Use correct import paths** - Direct imports from `katana_public_api_client.api` (no
   `.generated` subdirectory)
1. **Client types import** - Use `from katana_public_api_client.client_types import`
   instead of `types`

## Version Support Policy

- **Python versions**: Only 3.11, 3.12, 3.13 are supported
- **Dependencies**: Updated via Poetry lock file
- **CI/CD**: Tests run on all supported Python versions

## Timeout Reference (CRITICAL)

**NEVER CANCEL these commands before the timeout:**

| Command                            | Expected Time | Timeout Setting |
| ---------------------------------- | ------------- | --------------- |
| `poetry install`                   | ~26 seconds   | 30+ minutes     |
| `poetry run poe lint`              | ~11 seconds   | 15+ minutes     |
| `poetry run poe test`              | ~27 seconds   | 30+ minutes     |
| `poetry run poe test-coverage`     | ~39 seconds   | 45+ minutes     |
| `poetry run poe check`             | ~40 seconds   | 60+ minutes     |
| `poetry run poe docs-build`        | ~2.5 minutes  | 60+ minutes     |
| `poetry run poe regenerate-client` | ~2+ minutes   | 60+ minutes     |
| `poetry run poe pre-commit-run`    | ~30+ seconds  | 60+ minutes     |

**Remember**: Always set generous timeouts. Network delays and package compilation can
extend these times significantly.

______________________________________________________________________

**Final Reminder**: These instructions are based on exhaustive testing of every command.
Follow them exactly and **NEVER CANCEL** long-running operations. The transport-layer
resilience approach makes this client robust without requiring wrapper methods or
decorators.
