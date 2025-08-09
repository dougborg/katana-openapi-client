# AI Agent Instructions for Katana OpenAPI Client

## Architecture Overview

This is a production-ready Python client for the Katana Manufacturing ERP API built with
a **transport-layer resilience** approach. The key architectural decision is
implementing retry logic, rate limiting, and auto-pagination at the HTTP transport level
rather than as decorators or wrapper methods.

### Core Components

- **`katana_public_api_client/katana_client.py`**: Main client with
  `ResilientAsyncTransport` - all resilience features happen here automatically
- **`katana_public_api_client/client.py`**: Base client classes (enhanced functionality)
- **`katana_public_api_client/generated/api/`**: 76+ generated API endpoint modules
  (don't edit directly)
- **`katana_public_api_client/generated/models/`**: 150+ generated data models (don't
  edit directly)
- **`katana_public_api_client/generated/client.py`**: Generated OpenAPI client (base
  classes)

### The Transport Layer Pattern

**Key insight**: Instead of wrapping API methods, we intercept at the httpx transport
level. This means ALL API calls through `KatanaClient` get automatic retries, rate
limiting, and pagination without any code changes needed in the generated client.

```python
# Generated API methods work transparently with resilience:
from katana_public_api_client import KatanaClient
from katana_public_api_client.generated.api.product import get_all_products

async with KatanaClient() as client:
    # This call automatically gets retries, rate limiting, pagination:
    response = await get_all_products.asyncio_detailed(
        client=client, limit=50  # Will auto-paginate if needed
    )
```

## Development Workflows

### Poe Task Commands (Critical)

```bash
# Format ALL files (Python + Markdown)
poetry run poe format

# Type checking (mypy on 443+ files)
poetry run poe lint

# Check formatting without changes
poetry run poe format-check

# Python-only formatting
poetry run poe format-python

# Quick development check (format-check + lint + test)
poetry run poe check

# Auto-fix formatting and linting issues
poetry run poe fix

# Full CI pipeline
poetry run poe ci

# Show all available tasks
poetry run poe help
```

### Pre-commit Hooks (ALWAYS Use)

Pre-commit hooks are **mandatory** for development - they automatically format and check
code before commits:

```bash
# Install pre-commit hooks (run once after clone)
poetry run poe pre-commit-install

# Run pre-commit on all files (for testing)
poetry run poe pre-commit-run

# Update pre-commit hook versions
poetry run poe pre-commit-update
```

**CRITICAL**: Pre-commit hooks run automatically on `git commit` and will:

- Format code with ruff
- Fix trailing whitespace and file endings
- Check YAML syntax
- Validate large files and merge conflicts

**If pre-commit fails**: Fix the issues and commit again. Never use
`git commit --no-verify` to bypass hooks.

**Development Workflow with Pre-commit**:

1. Make code changes
1. `git add .` (stage changes)
1. `git commit -m "message"` (pre-commit runs automatically)
1. If pre-commit fails: fix issues, `git add .`, commit again
1. If pre-commit passes: commit succeeds

### Testing Strategy

Run tests in this order for debugging:

1. `poetry run poe test` - Run all tests
1. `poetry run poe test-unit` - Unit tests only
1. `poetry run poe test-integration` - Integration tests only
1. `poetry run poe test-coverage` - Tests with coverage report

**Integration tests** require `KATANA_API_KEY` in `.env` - mark with
`@pytest.mark.integration`.

### Code Regeneration

```bash
# Regenerate client from OpenAPI spec (when API changes)
poetry run poe regenerate-client
poetry run poe format  # Always format after regeneration
```

## Project-Specific Patterns

### Configuration Consolidation

All tool configurations are consolidated in `pyproject.toml` following modern Python
standards and **PEP 621** format:

- **Project metadata**: `[project]` section with name, version, dependencies, etc.
- **Project URLs**: `[project.urls]` section with homepage, repository, documentation
  links
- **Project scripts**: `[project.scripts]` section with console scripts
- **Optional dependencies**: `[project.optional-dependencies]` section with dev
  dependencies
- **MyPy**: `[tool.mypy]` section with type checking configuration
- **Pytest**: `[tool.pytest.ini_options]` section with test configuration and markers
- **Ruff**: `[tool.ruff]` section with linting and formatting rules
- **Coverage**: `[tool.coverage]` section with coverage reporting
- **Poe**: `[tool.poe.tasks]` section with task definitions
- **Semantic Release**: `[tool.semantic_release]` section with versioning
- **Poetry**: `[tool.poetry]` section with package discovery and build configuration
  only

No separate `mypy.ini`, `pytest.ini`, or `.flake8` files are used. The project follows
PEP 621 standards for modern Python packaging.

### Client Usage Pattern

**Always use the pattern**: `KatanaClient` can be passed directly to generated API
methods.

```python
# CORRECT pattern:
async with KatanaClient() as client:
    response = await some_api_method.asyncio_detailed(
        client=client,  # Pass KatanaClient directly
        param=value
    )

# AVOID: Don't try to enhance/wrap the generated methods
```

### Resilience Configuration

Resilience is **always-on** and configured in `ResilientAsyncTransport.__init__()`:

- Max retries: 5 attempts with exponential backoff
- Max auto-pagination: 100 pages with safety limits
- Rate limiting: Automatic detection via HTTP 429 responses

### Error Handling Pattern

```python
# Network/auth errors are expected in tests - use this pattern:
try:
    response = await api_method.asyncio_detailed(client=client.client)
    assert response.status_code in [200, 404]  # 404 OK for empty test data
except Exception as e:
    error_msg = str(e).lower()
    assert any(word in error_msg for word in ["connection", "network", "auth"])
```

## File Organization Rules

### Don't Edit (Generated)

- `katana_public_api_client/generated/api/**/*.py`
- `katana_public_api_client/generated/models/**/*.py`

### Format Exclusions

Generated code is excluded from formatting via `pyproject.toml` config. When editing:

- **Edit generated code**: Run regeneration script instead
- **Edit transport logic**: Modify `ResilientAsyncTransport` in `katana_client.py`
- **Add tests**: Use existing fixtures in `conftest.py`

### Documentation Structure

- `docs/KATANA_CLIENT_GUIDE.md` - Main usage guide
- `docs/TESTING_GUIDE.md` - Test patterns and pytest configuration
- `docs/POETRY_USAGE.md` - Development commands reference

## Integration Points

### GitHub CI/CD

- **Supported Python versions**: Only the latest three releases (currently 3.11, 3.12,
  3.13) are supported and tested. Update `pyproject.toml` and CI matrix as new Python
  versions are released.
- **Python matrix**: CI and release workflows run on 3.11, 3.12, 3.13 only.
- **Quality gates**: `poetry run poe lint` (mypy) + `poetry run poe format-check` must
  pass
- **Semantic release**: Uses conventional commits for automated versioning

### Conventional Commits (CRITICAL)

This project uses **semantic-release** with conventional commits for automated
versioning. **ALWAYS** use the correct commit type to control version bumping:

#### Commit Types and When to Use Them

**`feat:`** - New features or functionality changes (triggers MINOR version bump)

- Adding new API endpoints or client methods
- New configuration options or capabilities
- Enhanced error handling or resilience features
- Any user-facing functionality additions

**`fix:`** - Bug fixes or corrections (triggers PATCH version bump)

- Fixing broken API calls or transport issues
- Correcting type annotations or imports
- Resolving authentication or pagination problems
- Any functional issue that affects end users

**`chore:`** - Development tooling and maintenance (NO version bump)

- Pre-commit hooks setup or updates
- CI/CD pipeline changes
- Development dependency updates
- Build script modifications
- Code formatting or linting rule changes
- Documentation tooling improvements

**`docs:`** - Documentation changes only (NO version bump)

- README updates
- API documentation improvements
- Usage guide changes
- Comment updates (unless fixing functional bugs)

**`test:`** - Test-related changes only (NO version bump)

- Adding new test cases
- Improving test coverage
- Test infrastructure improvements
- Mock updates or test utilities

**`refactor:`** - Code refactoring without functional changes (NO version bump)

- Code organization improvements
- Performance optimizations (without new features)
- Internal API improvements (not user-facing)

**`style:`** - Code style changes only (NO version bump)

- Formatting fixes
- Import organization
- Code style compliance

#### Examples

```bash
# ✅ CORRECT: New feature
git commit -m "feat: add automatic retry configuration options"

# ✅ CORRECT: Bug fix
git commit -m "fix: resolve pagination issue with large datasets"

# ✅ CORRECT: Development tooling (this PR)
git commit -m "chore: add pre-commit hooks and fix markdown formatting"

# ✅ CORRECT: Documentation update
git commit -m "docs: update README with new usage examples"

# ❌ WRONG: Don't use feat: for tooling
git commit -m "feat: add pre-commit hooks"  # Should be chore:

# ❌ WRONG: Don't use fix: for new features
git commit -m "fix: add retry configuration"  # Should be feat:
```

#### Breaking Changes

Use `!` after the type for breaking changes (triggers MAJOR version bump):

```bash
git commit -m "feat!: change KatanaClient constructor signature"
git commit -m "fix!: remove deprecated API methods"
```

#### When in Doubt

- **Does this change user-facing functionality?** → `feat:` or `fix:`
- **Is this internal development/tooling only?** → `chore:`
- **Does this break existing code?** → Add `!` after type
- **Is this just documentation?** → `docs:`

### OpenAPI Workflow

1. Update `katana-openapi.yaml`
1. Run `poetry run poe regenerate-client`
1. Run `poetry run poe format`
1. Update tests if endpoint signatures changed

### OpenAPI Schema Standards (Comprehensive Guidelines)

Our OpenAPI specification follows strict quality standards enforced by automated tests
in `tests/test_schema_standards.py`. All schema improvements must pass these tests
before merging.

#### 1. BaseEntity Inheritance Pattern (100% Compliance Required)

**Status**: ✅ **COMPLETE** - All 50 entity schemas properly use BaseEntity inheritance

All domain entities must use our established inheritance hierarchy:

- **`BaseEntity`**: Provides common `id` property for all entities
- **`UpdatableEntity`**: Adds `created_at` and `updated_at` timestamps
- **`DeletableEntity`**: Extends UpdatableEntity with `deleted_at` (soft delete)
- **`ArchivableEntity`**: Extends UpdatableEntity with `archived_at`

**Required Pattern**:

```yaml
# CORRECT: Entity schemas MUST use BaseEntity inheritance
SomeEntity:
  allOf:
    - $ref: "#/components/schemas/BaseEntity"
    - $ref: "#/components/schemas/UpdatableEntity"  # or DeletableEntity/ArchivableEntity
    - type: object
      properties:
        # entity-specific properties
      required:
        - # entity-specific required fields
```

#### 2. Schema Documentation Standards (Current Priority)

**All schemas** must have meaningful descriptions:

- **Schema-level descriptions**: Required for ALL schemas
- **Property descriptions**: Required for significant properties (exclude common
  inherited fields: `id`, `created_at`, `updated_at`, `deleted_at`, `archived_at`)
- **No property-level examples**: Use schema-level examples only to avoid duplication

#### 3. Schema Example Standards (Endpoint-Focused)

**Schema-level examples required for**:

- ✅ Schemas used directly in API endpoint definitions
- ❌ Internal composition schemas (BaseEntity, etc.) - Skip these
- ❌ Simple list response wrappers - Skip these

**Example Quality Requirements**:

- **Realistic data**: Use industry-appropriate naming and values
- **Consistent ID ranges**: 1xx for simple IDs, 2xxx for variants, 3xxx for items
- **Coherent relationships**: All field values should relate realistically
- **Complete coverage**: Include all significant properties in examples

#### 4. Test-Driven Schema Quality

Our comprehensive test suite validates:

- **BaseEntity inheritance**: `test_entity_uses_base_entity_inheritance` (50/50 ✅)
- **Schema descriptions**: `test_schema_has_description` (All schemas)
- **Property descriptions**: `test_schema_properties_have_descriptions` (Significant
  properties)
- **Example placement**: `test_schema_avoids_property_examples` (Schema-level only)
- **Endpoint examples**: `test_endpoint_schema_has_example` (API-used schemas only)

**Test Status** (784 total tests):

- ✅ 474 PASSING (BaseEntity inheritance 100% complete)
- ❌ 188 FAILING (Descriptions and examples need work)
- ⚪ 122 SKIPPED (Base classes and non-endpoint schemas)

#### 5. Schema Validation Workflow

**Before committing schema changes**:

1. Run `poetry run pytest tests/test_schema_standards.py` to validate compliance
1. Address any failing tests before proceeding
1. All BaseEntity inheritance tests must pass (currently ✅ 100%)
1. Focus on endpoint-used schemas for examples (87 schemas identified)

**Validation Approach**:

- Validate against official Katana documentation at developer.katanamrp.com
- Document discrepancies in `docs/KATANA_API_QUESTIONS.md`
- Use `fix:` commits for individual resource improvements
- Use `feat:` only for major structural changes affecting multiple resources

### Type Safety

- **MyPy strict checking** on custom code (443+ files)
- Generated code uses type stubs in `py.typed`
- Transport layer preserves all type information from generated client

## Common Pitfalls

1. **Don't mock the transport layer** - Mock at the httpx client level instead
1. **Pagination is automatic** - Don't try to implement manual pagination
1. **Use `.client` not `._client`** - The property provides the correct interface
1. **Generated imports may change** - Import API methods dynamically in tests if needed
1. **Rate limiting is handled** - Don't add additional retry logic on top
1. **Always install pre-commit hooks** - Run `poetry run poe pre-commit-install` after
   cloning
1. **Never bypass pre-commit** - Don't use `git commit --no-verify` to skip formatting
   checks
1. **Use correct conventional commit types** - See "Conventional Commits" section above.
   Wrong commit types trigger unwanted releases or miss important version bumps.
1. **Always use BaseEntity pattern** - Don't add `id` property directly to schemas, use
   `BaseEntity` reference (100% compliance achieved)
1. **Schema examples over endpoint examples** - Add endpoint examples only when
   necessary (see Schema Standards above), prefer comprehensive schema-level examples
1. **No property-level examples** - Use schema-level examples, not individual property
   examples that clutter the schema definition
1. **Validate against official docs** - Always check developer.katanamrp.com when
   modifying OpenAPI spec
1. **Document discrepancies** - Add any API inconsistencies to
   `docs/KATANA_API_QUESTIONS.md`
1. **Run schema tests before committing** - Execute
   `poetry run pytest tests/test_schema_standards.py` to ensure compliance with quality
   standards

## Version Support Policy

- This library only supports the latest three Python versions. When a new Python release
  is published, update:
  - `pyproject.toml` to restrict to the latest three (e.g. `python = ">=3.12,<3.15"`)
  - CI/CD workflow matrices to match
  - Documentation and classifiers

## Maintenance Checklist

- After updating Python support:
  - Remove older versions from all config files and workflows
  - Confirm all tests pass on the new matrix
  - Update documentation to reflect supported versions

Remember: The transport layer approach makes this client resilient by default without
requiring any wrapper methods or decorators.
