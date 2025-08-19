# AI Agent Instructions for Katana OpenAPI Client

**CRITICAL: Follow these instructions completely and precisely before attempting any
other actions. Only fallback to additional search or context gathering if the
information in these instructions is incomplete or found to be in error.**

## Automated Setup for GitHub Copilot Coding Agent

**For GitHub Copilot Coding Agent**: This project includes an automated setup workflow
`.github/workflows/copilot-setup-steps.yml` that handles environment initialization
automatically. The setup process:

1. **Sets up Python 3.12** - Uses official GitHub Actions for Python setup
1. **Installs Poetry** - Python package manager for dependency management
1. **Installs all dependencies** - Runs `poetry install --extras "dev docs"` to install
   production, development, and documentation dependencies
1. **Installs pre-commit hooks** - Runs `poetry run poe pre-commit-install` (may fail in
   restricted environments)
1. **Validates environment** - Tests package imports and runs format checks
1. **Provides task runner** - Verifies `poethepoet (poe)` task runner is available

**Manual Setup**: If you need to set up the environment manually or troubleshoot issues,
follow the detailed steps below.

## Quick Start - Fresh Clone Setup

Follow these exact commands in order for a fresh clone setup. **NEVER CANCEL any build
or long-running command** - they are expected to take time.

### 1. Install Poetry (Python Package Manager)

Poetry is the primary dependency manager for this project. It handles virtual
environments, dependency resolution, and package building automatically.

```bash
# Install Poetry via pip (network restrictions prevent curl install)
pip install poetry

# Add Poetry to PATH for current session (if needed)
export PATH="$HOME/.local/bin:$PATH"

# Verify Poetry installation
poetry --version
poetry check
```

**Expected Result**: Poetry 2.1.4+ should be installed successfully.

**What Poetry Does**:

- Creates isolated virtual environments automatically
- Locks dependency versions for reproducible builds (`poetry.lock`)
- Manages development vs production dependencies
- Handles Python version compatibility

### 2. Install Project Dependencies

Poetry will automatically create a virtual environment and install all dependencies
defined in `pyproject.toml`.

```bash
# Install all project dependencies including dev and docs extras - NEVER CANCEL, takes 30+ seconds
# TIMEOUT: Set 30+ minutes for safety
poetry install --extras "dev docs"

# Expected time: ~26 seconds
# If failures occur due to network timeouts, retry the command
```

**CRITICAL**: This command **NEVER CANCEL** - may take up to 30 minutes on slow networks
but typically completes in ~26 seconds.

**Note**: The automated setup workflow `.github/workflows/copilot-setup-steps.yml` runs
this command automatically for GitHub Copilot Coding Agent.

**What Gets Installed**:

- Production dependencies: httpx, attrs, python-dateutil
- Development dependencies: pytest, ruff, mypy, pre-commit
- Documentation dependencies: sphinx, myst-parser
- Task runner: poethepoet (poe)

### 3. Understanding Task Management with Poe

This project uses **poethepoet (poe)** as a task runner, configured in `pyproject.toml`.
All development tasks are run through `poetry run poe <task>`.

```bash
# Show all available development tasks
poetry run poe help

# Test that core imports work
poetry run python -c "import katana_public_api_client; print('✅ Package import successful')"
```

**Key Poe Tasks Available**:

#### Code Quality and Formatting

- `format` - Apply code formatting to all files (ruff + mdformat)
- `format-check` - Check formatting without making changes (fastest validation)
- `format-python` - Format Python files only using ruff
- `format-markdown` - Format Markdown files only using mdformat

#### Linting and Type Checking

- `lint` - Run all linting tools (ruff + mypy + yamllint)
- `lint-ruff` - Fast Python linting with ruff
- `lint-mypy` - Type checking with mypy
- `lint-yaml` - YAML validation with yamllint

#### Testing

- `test` - Run basic test suite (unit tests, ~27 seconds)
- `test-coverage` - Run tests with coverage reporting (~39 seconds)
- `test-unit` - Run unit tests only
- `test-integration` - Run integration tests (requires KATANA_API_KEY)

#### Documentation

- `docs-build` - Build Sphinx documentation (~2.5 minutes)
- `docs-serve` - Serve documentation locally with live reload
- `docs-clean` - Clean documentation build artifacts

#### OpenAPI and Client Management

- `validate-openapi` - Validate OpenAPI specification
- `validate-openapi-redocly` - Advanced validation with Redocly
- `regenerate-client` - Regenerate Python client from OpenAPI spec (~2+ minutes)

#### Workflow Combinations

- `check` - Combined format-check + lint + test (~40 seconds)
- `fix` - Auto-fix formatting and linting issues (~15 seconds)
- `ci` - Full CI pipeline including docs and coverage

#### Development Environment

- `pre-commit-install` - Install pre-commit hooks
- `pre-commit-run` - Run pre-commit on all files
- `pre-commit-update` - Update pre-commit hook versions

### 4. Verify Installation Success

```bash
# Verify Poetry environment is working
poetry env info

# Test package imports
poetry run python -c "
import katana_public_api_client
from katana_public_api_client import KatanaClient
print('✅ Package import successful')
"

# Run quick format check to verify development tools
poetry run poe format-check

# Show task runner is working
poetry run poe --help
```

**Note**: The automated setup workflow `.github/workflows/copilot-setup-steps.yml`
performs these verification steps automatically for GitHub Copilot Coding Agent.

## Development Commands - Validated Timings

All commands below have been tested and timed. **NEVER CANCEL** any command before the
timeout expires.

**Important**: All development commands must be run through Poetry to use the correct
virtual environment: `poetry run poe <task>`

### Understanding Poetry and Poe Architecture

This project uses a **two-layer development workflow**:

#### Poetry (Dependency & Environment Manager)

Poetry is the foundation layer that handles:

- **Virtual Environment**: Automatically creates and manages isolated Python
  environments
- **Dependency Resolution**: Ensures compatible package versions via `poetry.lock`
- **Package Installation**: Installs both production and development dependencies
- **Environment Activation**: Runs commands in the correct virtual environment

```bash
# Poetry commands (environment management):
poetry install          # Install all dependencies
poetry add <package>     # Add new dependency
poetry env info         # Show environment details
poetry shell            # Activate virtual environment
poetry run <command>    # Run command in Poetry's virtual environment
```

#### Poe (Task Runner)

Poe (poethepoet) is the workflow layer that provides:

- **Predefined Tasks**: Common development workflows in `pyproject.toml`
- **Command Composition**: Combines multiple tools into single commands
- **Cross-Platform**: Works consistently across different operating systems
- **Dependency Ordering**: Ensures tasks run in correct sequence

```bash
# Poe commands (task execution) - always run via Poetry:
poetry run poe <task>    # Execute a predefined task
poetry run poe help      # List all available tasks
poetry run poe --help    # Show poe command options
```

#### The Combined Workflow: `poetry run poe <task>`

**Critical Pattern**: Always use `poetry run poe <task>` to ensure:

1. **Poetry** activates the correct virtual environment
1. **Poe** executes the task with proper tool configuration
1. All dependencies are available and properly versioned

**Examples**:

```bash
poetry run poe format    # Format code using ruff in Poetry's environment
poetry run poe test      # Run pytest with all test dependencies
poetry run poe lint      # Run multiple linting tools in sequence
```

### Essential Task Categories

#### Code Quality and Formatting

```bash
# Format checking (fastest) - 2 seconds
poetry run poe format-check

# Full formatting (applies fixes) - 2 seconds
poetry run poe format

# Python-only formatting - 1 second
poetry run poe format-python

# Markdown formatting - 1 second
poetry run poe format-markdown
```

**Tools Used**: ruff (Python formatting/linting), mdformat (Markdown)

#### Linting and Type Checking

```bash
# Full linting suite - NEVER CANCEL, takes 11 seconds
# TIMEOUT: Set 15+ minutes for safety
poetry run poe lint

# Individual linting commands (faster)
poetry run poe lint-ruff      # 2 seconds - fast linting with ruff
poetry run poe lint-mypy      # 8 seconds - type checking with mypy
poetry run poe lint-yaml      # 1 second - YAML validation with yamllint
```

**CRITICAL**: Full linting (`poe lint`) **NEVER CANCEL** - takes ~11 seconds but timeout
to 15+ minutes for safety.

**Tools Used**: ruff, mypy, yamllint

#### Testing

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

**Tools Used**: pytest, pytest-cov, pytest-asyncio

#### Documentation

```bash
# Build documentation - NEVER CANCEL, takes 2.5 minutes
# TIMEOUT: Set 60+ minutes for safety
poetry run poe docs-build

# Clean documentation build
poetry run poe docs-clean

# Serve documentation locally (opens browser)
poetry run poe docs-serve
```

**CRITICAL**: Documentation build **NEVER CANCEL** - takes ~2.5 minutes but timeout to
60+ minutes for safety.

**Tools Used**: sphinx, myst-parser, sphinx-autoapi

### Workflow Commands

#### Combined Workflows

```bash
# Quick development check - NEVER CANCEL, takes ~40 seconds total
# TIMEOUT: Set 60+ minutes for safety
poetry run poe check              # Runs: format-check + lint + test

# Auto-fix issues - 15 seconds
poetry run poe fix                # Runs: format + lint fixes

# Full CI pipeline (may fail on pytest-cov, see Network Limitations)
poetry run poe ci                 # Runs: check + docs-build + coverage
```

#### Dependency Management Commands

```bash
# Install project dependencies (first time setup)
poetry install                   # Install all dependencies from poetry.lock

# Add new dependencies
poetry add <package-name>        # Add production dependency
poetry add --group dev <package-name>  # Add development dependency
poetry add --group docs <package-name> # Add documentation dependency

# Update dependencies
poetry update                    # Update all dependencies to latest compatible versions
poetry update <package-name>     # Update specific package

# Remove dependencies
poetry remove <package-name>     # Remove production dependency
poetry remove --group dev <package-name>  # Remove development dependency

# Environment management
poetry env info                  # Show current environment details
poetry env list                  # List all environments for this project
poetry shell                     # Activate virtual environment in current shell

# Dependency inspection
poetry show                      # List all installed packages
poetry show --tree               # Show dependency tree
poetry show <package-name>       # Show details for specific package
poetry show --outdated          # Show packages with available updates

# Lock file management
poetry lock                      # Update poetry.lock without installing
poetry lock --no-update         # Regenerate lock file without updating versions

# Export for other tools
poetry export -f requirements.txt --output requirements.txt  # Export to requirements.txt
poetry export --group dev -f requirements.txt --output dev-requirements.txt

# Installation options
poetry install --only main      # Install only production dependencies
poetry install --only dev       # Install only development dependencies
poetry install --no-dev         # Install without development dependencies
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

## Automated Setup Workflow

For GitHub Copilot Coding Agent users, the `.github/workflows/copilot-setup-steps.yml`
workflow automatically handles the complete environment setup:

1. **Checkout code** - Uses `actions/checkout@v4`
1. **Setup Python** - Uses `actions/setup-python@v5` with Python 3.12
1. **Install Poetry** - Installs via pip and configures virtual environments
1. **Install dependencies** - Runs `poetry install --extras "dev docs"`
1. **Verify installation** - Tests Poetry environment, package imports, and task runner
1. **Quick validation** - Runs `poetry run poe format-check` to ensure tools work

This workflow runs automatically when the coding agent starts and can be manually
triggered from the GitHub Actions tab for testing. If any step fails, the agent will
continue with the current environment state.

______________________________________________________________________

**Final Reminder**: These instructions are based on exhaustive testing of every command.
Follow them exactly and **NEVER CANCEL** long-running operations. The transport-layer
resilience approach makes this client robust without requiring wrapper methods or
decorators.
