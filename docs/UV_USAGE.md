# uv Package Manager Guide for Katana OpenAPI Client

This document provides common uv commands for working with the Katana OpenAPI Client
project.

## Task Runner (Poe)

This project uses [poethepoet](https://github.com/nat-n/poethepoet) as a task runner,
which works seamlessly with uv. All development commands are run through `uv run poe`:

```bash
# Show all available tasks
uv run poe help

# Quick development workflow
uv run poe check    # format-check + lint + test
uv run poe fix      # format + lint-fix
uv run poe ci       # Full CI pipeline
```

## Why uv?

This project migrated from Poetry to uv for significant performance improvements:

- **10-100x faster** dependency resolution
- **5x faster** installation (~5-10s vs ~26s)
- **Modern tooling** - Written in Rust by Astral (makers of Ruff)
- **Standards compliant** - Uses PEP 621 format
- **Simpler** - One tool replacing multiple (pip, pip-tools, virtualenv, etc.)

See [ADR-009](../adr/0009-migrate-from-poetry-to-uv.md) for the full migration
rationale.

## Basic Commands

### Project Management

```bash
# Check uv version
uv --version

# Show project info
uv tree

# List installed packages
uv pip list

# Show outdated packages
uv pip list --outdated
```

### Environment Management

```bash
# Install all dependencies (including all extras)
uv sync --all-extras

# Install only production dependencies
uv sync

# Install specific extra groups
uv sync --extra dev
uv sync --extra docs

# Show environment info
uv venv
```

### Package Management

```bash
# Add a new dependency
uv add package-name

# Add a development dependency
uv add --dev package-name

# Remove a dependency
uv remove package-name

# Update all dependencies
uv lock --upgrade

# Update specific package
uv lock --upgrade-package package-name
```

## Testing

### Run Tests

```bash
# Run all tests
uv run poe test

# Run tests with coverage
uv run poe test-coverage

# Run specific test categories
uv run poe test-unit
uv run poe test-integration

# Run with specific pytest options
uv run pytest -x  # Stop on first failure
uv run pytest tests/test_katana_client.py  # Specific file
uv run pytest -v  # Verbose output
```

### Code Quality

```bash
# Format code
uv run poe format          # Format all (Python + Markdown)
uv run poe format-python   # Python only
uv run poe format-check    # Check formatting

# Linting
uv run poe lint            # All linters
uv run poe lint-ruff       # Ruff linting
uv run poe lint-mypy       # Type checking
uv run poe lint-yaml       # YAML linting
```

### OpenAPI Development

```bash
# Regenerate client from OpenAPI spec
uv run poe regenerate-client

# Validate OpenAPI specification
uv run poe validate-openapi
```

### Test Categories

```bash
# Run only unit tests
uv run pytest -m unit

# Run only integration tests
uv run pytest -m integration

# Skip slow tests
uv run pytest -m "not slow"
```

## Development

### Running Python Code

```bash
# Run Python directly in the project environment
uv run python

# Run a specific script
uv run python your_script.py

# Run a module
uv run python -m module_name

# Quick import test
uv run python -c "from katana_public_api_client import KatanaClient; print('✅ Import successful')"
```

### Interactive Development

```bash
# Open IPython shell (if installed)
uv run ipython

# Or standard Python REPL
uv run python

# Run a Jupyter notebook
uv run jupyter notebook
```

## Building and Publishing

### Build Package

```bash
# Build wheel and source distribution
uv build

# Check built packages
ls dist/
```

The build uses hatchling as the backend (configured in `pyproject.toml`).

## Documentation

### Build and Serve Docs

```bash
# Build documentation
uv run poe docs-build

# Serve documentation locally
uv run poe docs-serve

# Auto-rebuild on changes
uv run poe docs-autobuild

# Clean build artifacts
uv run poe docs-clean
```

## Example Usage

### Testing the Client

```bash
# Quick import test
uv run python -c "from katana_public_api_client import KatanaClient; print('✅ Import successful')"

# Run a specific test
uv run pytest tests/test_katana_client.py::TestKatanaClient::test_client_initialization -v

# Check test coverage for specific module
uv run pytest tests/ --cov=katana_public_api_client.katana_client --cov-report=term-missing
```

### Development Workflow

```bash
# 1. Install dependencies
uv sync --all-extras

# 2. Make changes to code

# 3. Run tests
uv run poe test

# 4. Check formatting and linting
uv run poe check

# 5. Fix any issues
uv run poe fix

# 6. Check coverage
uv run poe test-coverage
```

## Pre-commit Hooks

```bash
# Install pre-commit hooks
uv run poe pre-commit-install

# Run pre-commit on all files manually
uv run poe pre-commit-run

# Update pre-commit hook versions
uv run poe pre-commit-update
```

## Troubleshooting

### Common Issues

```bash
# Lock file issues - regenerate
uv lock

# Clear cache
rm -rf .venv
uv sync --all-extras

# Force reinstall all packages
uv sync --reinstall

# Verbose output for debugging
uv sync --verbose
```

### Performance Tips

uv is already extremely fast, but you can optimize further:

```bash
# Use frozen mode (don't update lock file)
uv sync --frozen

# Use locked mode (assert lock file unchanged)
uv sync --locked

# Skip development dependencies for production
uv sync --no-dev
```

## Command Comparison: Poetry → uv

| Task                 | Poetry                               | uv                            |
| -------------------- | ------------------------------------ | ----------------------------- |
| Install dependencies | `poetry install --extras "dev docs"` | `uv sync --all-extras`        |
| Add package          | `poetry add httpx`                   | `uv add httpx`                |
| Add dev package      | `poetry add --group dev pytest`      | `uv add --dev pytest`         |
| Remove package       | `poetry remove httpx`                | `uv remove httpx`             |
| Update dependencies  | `poetry update`                      | `uv lock --upgrade`           |
| Run command          | `poetry run python script.py`        | `uv run python script.py`     |
| Run poe task         | `poetry run poe test`                | `uv run poe test`             |
| Build package        | `poetry build`                       | `uv build`                    |
| Show packages        | `poetry show`                        | `uv pip list`                 |
| Show dependency tree | `poetry show --tree`                 | `uv tree`                     |
| Environment info     | `poetry env info`                    | `uv venv` (or `uv --version`) |
| Lock dependencies    | `poetry lock`                        | `uv lock`                     |
| Clear cache          | `poetry cache clear pypi --all`      | `rm -rf ~/.cache/uv`          |

## Advanced Usage

### Running with Additional Dependencies

```bash
# Run with extra packages temporarily (without adding to project)
uv run --with requests python script.py

# Run with specific package version
uv run --with "httpx==0.24.0" python script.py

# Run in isolated environment
uv run --isolated python script.py
```

### Working with Python Versions

```bash
# Use specific Python version
uv run --python 3.11 python script.py

# Install Python if needed (uv can manage Python installations)
uv python install 3.11
uv python install 3.12
uv python install 3.13

# List available Python versions
uv python list
```

### Lock File Management

```bash
# Generate lock file
uv lock

# Update lock file with latest compatible versions
uv lock --upgrade

# Update specific package in lock file
uv lock --upgrade-package httpx

# Validate lock file is up to date
uv sync --locked  # Will fail if lock file doesn't match pyproject.toml
```

## CI/CD Integration

This project uses uv in GitHub Actions for fast, reliable CI/CD:

```yaml
- name: Install uv
  uses: astral-sh/setup-uv@v7
  with:
    enable-cache: true
    cache-dependency-glob: "uv.lock"
    python-version: "3.13"

- name: Install dependencies
  run: uv sync --all-extras

- name: Run tests
  run: uv run poe test-coverage
```

See `.github/workflows/ci.yml` for complete examples.

## Resources

- [uv Official Documentation](https://docs.astral.sh/uv/)
- [uv GitHub Repository](https://github.com/astral-sh/uv)
- [ADR-009: Poetry to uv Migration](../adr/0009-migrate-from-poetry-to-uv.md)
- [Astral Blog: uv Announcement](https://astral.sh/blog/uv)
