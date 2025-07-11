# Testing Guide for Katana OpenAPI Client

## Overview

We've replaced all the scattered test scripts with a proper pytest-based test suite that
uses Poetry for dependency management and execution.

## Test Structure

```text
tests/
├── conftest.py              # Test configuration and fixtures
├── test_enhanced_client.py  # Core enhanced client functionality
├── test_integration.py      # Integration tests with generated client
├── test_performance.py      # Performance and stress tests
└── test_generated_client.py # Generated client compatibility tests
```

**Configuration**: All test configuration is centralized in `pyproject.toml` under
`[tool.pytest.ini_options]`.

## Running Tests

### Basic Test Execution

```bash
# Run all tests
poetry run poe test

# Run with verbose output
poetry run poe test-verbose

# Run specific test file
poetry run poe test tests/test_katana_client.py

# Run specific test class
poetry run poe test tests/test_katana_client.py::TestKatanaClient

# Run specific test method
poetry run poe test tests/test_katana_client.py::TestKatanaClient::test_client_initialization
```

### Test Categories

```bash
# Run only unit tests
poetry run poe test-unit

# Run only integration tests
poetry run poe test-integration

# Skip slow tests
poetry run poe test -- -m "not slow"

# Run async tests only
poetry run poe test -- -m asyncio
```

### Coverage Reports

```bash
# Run tests with coverage
poetry run poe test-coverage

# Generate HTML coverage report
poetry run poe test-coverage-html

# Open coverage report
open htmlcov/index.html
```

## Test Features

### Fixtures Available

- `mock_api_credentials`: Mock API credentials for testing
- `enhanced_client`: Pre-configured enhanced client instance
- `mock_response`: Mock successful API response
- `mock_paginated_responses`: Mock responses for pagination testing
- `async_mock`: Utility for creating async mocks

### Test Organization

1. **Unit Tests**: Test individual components in isolation
1. **Integration Tests**: Test interaction with generated client
1. **Performance Tests**: Test pagination, concurrency, and memory usage
1. **Compatibility Tests**: Ensure backward compatibility and proper imports

### What's Tested

- ✅ Enhanced client initialization and configuration
- ✅ Method enhancement with retry logic
- ✅ Pagination functionality with various scenarios
- ✅ Error handling and rate limiting
- ✅ Integration with generated OpenAPI client
- ✅ Type safety and IDE support preservation
- ✅ Backward compatibility
- ✅ Performance characteristics
- ✅ Concurrent usage scenarios

## Poetry Commands for Testing

```bash
# Install all dependencies including test deps
poetry install

# Update dependencies
poetry update

# Add new test dependency to dev extras
# Note: With PEP 621, manually add to pyproject.toml [project.optional-dependencies] dev array
poetry add <package>

# Run tests in isolated environment
poetry run pytest

# Check installed packages
poetry show

# Check virtual environment info
poetry env info

# Activate shell in poetry environment
poetry shell
```

## Continuous Integration

The test suite is designed to work well in CI environments:

- Fast execution with proper async handling
- Comprehensive mocking to avoid external dependencies
- Clear separation of unit vs integration tests
- Configurable test markers for selective execution

## Migration from Old Test Scripts

All functionality from the old test scripts has been consolidated:

- `test_*.py` scripts → Proper pytest test classes
- Ad-hoc testing → Structured test fixtures and scenarios
- Manual verification → Automated assertions
- Scattered functionality → Organized test categories

## Best Practices

1. **Use fixtures** for common test setup
1. **Mock external dependencies** to keep tests fast and reliable
1. **Test both success and failure scenarios**
1. **Use descriptive test names** that explain what's being tested
1. **Group related tests** in classes for better organization
1. **Mark slow tests** appropriately so they can be skipped during development
