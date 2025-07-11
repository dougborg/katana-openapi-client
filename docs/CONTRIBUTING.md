# Contributing to Katana OpenAPI Client

Thank you for your interest in contributing to the Katana OpenAPI Client! This document
provides guidelines and instructions for contributing.

## Development Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/dougborg/katana-openapi-client.git
   cd katana-openapi-client
   ```

1. **Install Poetry** (if not already installed)

   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

1. **Install dependencies**

   ```bash
   poetry install
   ```

1. **Set up environment variables**

   ```bash
   cp .env.example .env
   # Edit .env with your Katana API credentials for testing
   ```

## Development Workflow

### Code Quality

We maintain high code quality standards. Before submitting changes:

```bash
# Format code
poetry run format

# Check formatting
poetry run format-check

# Run type checking
poetry run lint

# Run tests
poetry run pytest
```

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=katana_public_api_client

# Run specific test file
poetry run pytest tests/test_katana_client.py

# Run integration tests (requires API credentials)
poetry run pytest -m integration
```

### Code Style

- We use [Ruff](https://docs.astral.sh/ruff/) for code formatting and linting
- [mypy](https://mypy.readthedocs.io/) for type checking
- [mdformat](https://mdformat.readthedocs.io/) for Markdown formatting

All formatting is automated via `poetry run format`.

## Submitting Changes

### Pull Request Process

1. **Fork the repository** and create a feature branch

   ```bash
   git checkout -b feature/your-feature-name
   ```

1. **Make your changes** following the code style guidelines

1. **Add or update tests** for your changes

1. **Update documentation** if needed

1. **Run the full test suite**

   ```bash
   poetry run format
   poetry run lint
   poetry run pytest
   ```

1. **Commit your changes** with a clear commit message

   ```bash
   git commit -m "feat: add new feature"
   ```

1. **Push to your fork** and create a pull request

### Commit Message Format

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` new features
- `fix:` bug fixes
- `docs:` documentation changes
- `style:` formatting changes
- `refactor:` code refactoring
- `test:` adding or updating tests
- `chore:` maintenance tasks

### Pull Request Guidelines

- Include a clear description of the changes
- Reference any related issues
- Ensure all tests pass
- Update documentation if needed
- Keep the scope focused and atomic

## Project Structure

```text
katana-openapi-client/
├── katana_public_api_client/    # Main package
│   ├── __init__.py
│   ├── katana_client.py         # Main client implementation
│   ├── client.py                # Generated client
│   ├── api/                     # Generated API methods
│   └── models/                  # Generated models
├── tests/                       # Test suite
├── docs/                        # Documentation
├── scripts/                     # Development scripts
└── .github/                     # GitHub workflows
```

## Architecture Guidelines

### Core Principles

1. **Transparency**: Features should work automatically without configuration
1. **Resilience**: All API calls should handle errors gracefully
1. **Type Safety**: Use comprehensive type annotations
1. **Performance**: Leverage async/await and efficient HTTP handling
1. **Compatibility**: Maintain compatibility with the generated client

### Adding New Features

When adding features:

1. **Transport Layer First**: Implement core functionality in `ResilientAsyncTransport`
1. **Automatic Behavior**: Make features work transparently without user configuration
1. **Comprehensive Testing**: Include unit tests, integration tests, and error scenarios
1. **Documentation**: Update relevant documentation and examples

## Testing Guidelines

### Test Categories

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test real API interactions (marked with
  `@pytest.mark.integration`)
- **Transport Tests**: Test the transport layer behavior directly

### Writing Tests

- Use descriptive test names that explain the scenario
- Include both success and error cases
- Mock external dependencies appropriately
- Use fixtures for common test setup

### Test Environment

Integration tests require valid Katana API credentials. Set these in your `.env` file:

```bash
KATANA_API_KEY=your_api_key_here
KATANA_BASE_URL=https://api.katanamrp.com/v1
```

## Documentation

### Updating Documentation

- Update relevant `.md` files in the `docs/` directory
- Keep examples current and working
- Update the README.md if adding user-facing features
- Include docstrings for all public methods

### Documentation Style

- Use clear, concise language
- Include practical examples
- Follow the existing format and style
- Test any code examples to ensure they work

## Release Process

Releases are automated via GitHub Actions:

1. **Version Bump**: Update version in `pyproject.toml`
1. **Update Changelog**: Add entry to `CHANGELOG.md`
1. **Create Tag**: `git tag v1.x.x && git push --tags`
1. **Automated Release**: GitHub Actions handles the rest

## Getting Help

- **Documentation**: Check the `docs/` directory
- **Issues**: Search existing issues or create a new one
- **Discussions**: Use GitHub Discussions for questions

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md).
Please read and follow it in all interactions.

Thank you for contributing! 🎉
