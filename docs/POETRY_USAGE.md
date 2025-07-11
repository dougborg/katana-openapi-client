# Poetry Commands for Katana OpenAPI Client

This document provides common Poetry commands for working with the Katana OpenAPI Client
project.

## Task Runner (Poe)

This project uses [poethepoet](https://github.com/nat-n/poethepoet) as a task runner.
All development commands are run through `poe`:

```bash
# Show all available tasks
poetry run poe help

# Quick development workflow
poetry run poe check    # format-check + lint + test
poetry run poe fix      # format + lint-fix
poetry run poe ci       # Full CI pipeline
```

## Basic Commands

### Project Management

```bash
# Check Poetry version
poetry --version

# Show project info
poetry show --tree

# Check dependency status
poetry check

# Update dependencies
poetry update
```

### Environment Management

```bash
# Install all dependencies
poetry install

# Install only production dependencies
poetry install --only main

# Install development dependencies
poetry install --extras dev

# Show virtual environment info
poetry env info

# List available environments
poetry env list

# Remove virtual environment
poetry env remove python
```

### Package Management

```bash
# Add a new dependency
poetry add package-name

# Add a development dependency (with PEP 621 format)
# Note: Manually add to pyproject.toml [project.optional-dependencies] dev array
poetry add package-name

# Remove a dependency
poetry remove package-name

# Show installed packages
poetry show

# Show outdated packages
poetry show --outdated
```

## Testing

### Run Tests

```bash
# Run all tests
poetry run poe test

# Run tests with coverage
poetry run poe test-coverage

# Run specific test categories
poetry run poe test-unit
poetry run poe test-integration

# Run with verbose output
poetry run poe test-verbose

# Run with specific pytest options
poetry run poe test -- -x  # Stop on first failure
poetry run poe test -- tests/test_katana_client.py  # Specific file
```

### Code Quality

```bash
# Format code
poetry run poe format          # Format all (Python + Markdown)
poetry run poe format-python   # Python only
poetry run poe format-check    # Check formatting

# Linting
poetry run poe lint            # All linters
poetry run poe lint-ruff       # Ruff linting
poetry run poe lint-mypy       # Type checking
poetry run poe lint-yaml       # YAML linting
```

### OpenAPI Development

```bash
# Regenerate client from OpenAPI spec
poetry run poe regenerate-client

# Validate OpenAPI specification
poetry run poe validate-openapi

# Check generated client consistency
poetry run poe check-generated-ast
```

### Test Categories

```bash
# Run only unit tests
poetry run pytest -m unit

# Run only integration tests
poetry run pytest -m integration

# Run performance tests
poetry run pytest -m slow
```

## Development

### Legacy Code Quality Commands

```bash
# Run type checking
poetry run mypy katana_public_api_client/

# Run linting
poetry run flake8 katana_public_api_client/

# Run tests with coverage
poetry run pytest --cov=katana_public_api_client --cov-report=html
```

### Interactive Shell

```bash
# Open Python shell with dependencies available
poetry shell

# Or run python directly
poetry run python

# Run a specific script
poetry run python your_script.py
```

## Building and Publishing

### Build Package

```bash
# Build wheel and source distribution
poetry build

# Check built packages
ls dist/
```

### Environment Export

```bash
# Export requirements.txt (requires poetry-plugin-export plugin)
# poetry plugin add poetry-plugin-export
# poetry export -f requirements.txt --output requirements.txt

# Export dev requirements (requires poetry-plugin-export plugin)
# poetry export -f requirements.txt --extras dev --output requirements-dev.txt

# Alternative: Use pip-tools or direct package listing for legacy compatibility
```

## Example Usage

### Testing the Enhanced Client

```bash
# Quick test that imports work
poetry run python -c "from katana_public_api_client import EnhancedKatanaClient; print('✅ Import successful')"

# Run a specific test
poetry run pytest tests/test_enhanced_client.py::TestEnhancedKatanaClient::test_client_initialization -v

# Check test coverage for enhanced client only
poetry run pytest tests/ --cov=katana_public_api_client.enhanced_client --cov-report=term-missing
```

### Development Workflow

```bash
# 1. Install dependencies
poetry install

# 2. Run tests to ensure everything works
./run_tests.sh quick

# 3. Make changes to code

# 4. Run specific tests
poetry run pytest tests/test_enhanced_client.py -v

# 5. Run full test suite
./run_tests.sh

# 6. Check coverage
./run_tests.sh coverage
```

## Troubleshooting

### Common Issues

```bash
# Lock file issues
poetry lock --no-update

# Clear cache
poetry cache clear pypi --all

# Reinstall environment
poetry env remove python
poetry install

# Debug dependency resolution
poetry lock --verbose
```

### Performance

```bash
# Install with pre-built wheels when possible
poetry install --only main

# Skip development dependencies for production
poetry install --only main --no-dev
```

## Code Formatting

### Custom Format and Lint Commands

The project includes custom Poetry scripts for comprehensive code formatting and type
checking:

```bash
# Format both Python and Markdown files
poetry run format

# Check formatting without making changes
poetry run format-check

# Format only Python code (using Black)
poetry run format-python

# Format only Markdown files (using mdformat)
poetry run format-markdown

# Run mypy type checking
poetry run lint
```

### What Gets Formatted

**Python Code:**

- Enhanced client code (`katana_public_api_client/enhanced_client.py`)
- Log setup and error handling
- Custom scripts (`scripts/`)
- Test files (`tests/`)
- Configuration files

**Markdown Files:**

- Main README.md
- All documentation in `docs/`
- Supports GitHub Flavored Markdown
- Table formatting
- Consistent line wrapping

### Integration with Development Workflow

```bash
# Before committing changes
poetry run format-check

# Fix any formatting issues
poetry run format

# Run type checking
poetry run lint

# Then run tests
poetry run pytest
```
