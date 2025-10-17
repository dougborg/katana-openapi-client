# Testing Guide

This guide explains the testing architecture and approach for the Katana OpenAPI Client
project.

## Testing Philosophy

Our test suite uses a **zero-tolerance approach** for API quality issues:

- **Equal treatment**: Every endpoint and schema receives identical validation
- **Comprehensive coverage**: All API elements are automatically tested
- **Parameterized testing**: Precise failure identification with detailed context
- **External consistency**: Validation against official Katana documentation

## Test Structure

### Core API Quality Tests

**`test_openapi_specification.py`** - OpenAPI Document Structure

- OpenAPI version compliance and document structure
- Required sections validation (info, paths, components)
- Operation ID uniqueness and YAML syntax validation

**`test_schema_comprehensive.py`** - Schema Validation

- Schema descriptions and property descriptions for all schemas
- BaseEntity inheritance patterns and structure standards
- Automatic coverage for new schemas without maintenance

**`test_endpoint_comprehensive.py`** - Endpoint Validation

- Operation IDs, documentation, response schemas, parameters
- Collection endpoint pagination validation
- Request body validation and error response coverage

**`test_external_documentation_comparison.py`** - External Consistency

- Validates against comprehensive documentation from developer.katanamrp.com
- Endpoint completeness, method coverage, parameter consistency
- Business domain coverage verification

### Specialized Tests

**`test_generated_client.py`** - Generated client structure and imports
**`test_katana_client.py`** - Custom client implementation and transport layer\
**`test_real_api.py`** - Integration tests against real API (requires credentials)
**`test_performance.py`** - Performance, retry behavior, memory usage
**`test_transport_auto_pagination.py`** - Transport layer pagination features
**`test_documentation.py`** - Documentation build and content validation

## Running Tests

### Development Workflow

```bash
# Run all tests
poetry run poe test

# Test specific areas
poetry run pytest tests/test_schema_comprehensive.py        # Schema issues
poetry run pytest tests/test_endpoint_comprehensive.py     # Endpoint issues
poetry run pytest tests/test_openapi_specification.py      # Structure issues
poetry run pytest tests/test_external_documentation_comparison.py  # External consistency

# Run with coverage
poetry run poe test-coverage

# Analyze coverage by category
poetry run poe analyze-coverage
```

### Debugging Test Failures

Parameterized tests provide precise failure identification:

```
test_schema_comprehensive.py::test_schema_has_description[schema-Customer] FAILED
test_endpoint_comprehensive.py::test_endpoint_has_documentation[GET-customers] FAILED
```

Each failure shows exactly which schema or endpoint needs attention.

## Test Categories

### Quality Assurance Tests

- **Zero tolerance**: All tests must pass for release
- **Equal treatment**: No endpoint or schema is more important than another
- **Automatic scaling**: New API elements automatically get full validation

### Integration Tests

- **Real API tests**: Require `KATANA_API_KEY` in `.env` file
- **Network resilience**: Test retry behavior and error handling
- **Performance validation**: Memory usage and response time testing

### Documentation Tests

- **Build validation**: Ensure documentation compiles correctly
- **Content consistency**: Verify examples and API references are current

## Key Benefits

### For Contributors

- **Clear failure messages**: Know exactly what needs to be fixed
- **No maintenance burden**: Tests automatically cover new API elements
- **Consistent standards**: Every addition follows the same quality requirements

### For API Quality

- **Comprehensive coverage**: Nothing falls through the cracks
- **External consistency**: API matches official documentation
- **Schema composition**: Proper `allOf` and `$ref` usage validation

### For CI/CD

- **Fast failure detection**: Issues identified immediately
- **Precise debugging**: No need to hunt through multiple test files
- **Reliable coverage**: Equal validation for all API elements

## Schema Composition Handling

Our tests properly handle OpenAPI schema composition patterns:

- **Direct properties**: Schemas with `properties` are fully validated
- **Composed schemas**: Schemas using `allOf` with `$ref` are correctly skipped
- **Base schema validation**: Referenced schemas (like `BaseEntity`, `UpdatableEntity`)
  are thoroughly tested
- **Inheritance validation**: Property descriptions are inherited through `$ref`
  composition

When tests are skipped for composed schemas, this is expected behavior - the validation
happens at the base schema level.

## Adding New Tests

When extending the test suite:

1. **Use parameterized tests** for comprehensive coverage
1. **Avoid hard-coded entity lists** - let tests discover API elements automatically
1. **Follow the zero-tolerance approach** - no exceptions for specific endpoints or
   schemas
1. **Provide clear failure messages** with actionable debugging information

## Code Coverage Analysis

### Understanding Coverage Metrics

**TL;DR**: Overall coverage of 23% is misleading. **Core logic coverage is 74.8%**,
which is what actually matters.

The overall coverage includes ~30,000 lines of auto-generated code (API modules and
models) that don't need comprehensive unit testing.

```text
Overall Coverage: 23.1%
├── Generated API (197 files, 10,517 lines): 0.6% ❌ Don't worry!
├── Generated Models (337 files, 19,911 lines): 33.5% ❌ Don't worry!
└── Core Logic (5 files, 524 lines): 74.8% ✅ This is what matters!
```

### Why Generated Code Has Low Coverage

1. **API Modules** - Auto-generated from OpenAPI spec, mostly boilerplate
1. **Model Classes** - Auto-generated data classes with simple serialization
1. **Generator is Tested** - The openapi-python-client generator has its own tests
1. **Integration Testing** - Generated code is tested through real API calls

### Core Logic Coverage Breakdown

| File               | Coverage | Status       | Priority                  |
| ------------------ | -------- | ------------ | ------------------------- |
| `utils.py`         | 98.1%    | ✅ Excellent | Maintain                  |
| `katana_client.py` | 85.3%    | ✅ Good      | Maintain, improve to 90%+ |
| `__init__.py`      | 100.0%   | ✅ Perfect   | Maintain                  |
| `client.py`        | 51.3%    | ⚠️ Moderate  | Improve to 70%+           |
| `log_setup.py`     | 0.0%     | ❌ None      | Add basic tests           |

### Running Coverage Analysis

```bash
# Generate coverage data and analyze by category
poetry run pytest --cov=katana_public_api_client --cov-report=json -m 'not docs'
poetry run poe analyze-coverage

# Generate HTML report for detailed inspection
poetry run pytest --cov=katana_public_api_client --cov-report=html -m 'not docs'
open htmlcov/index.html
```

### Coverage Philosophy

**Test what you write, not what's generated.**

- Generated code (248 API modules, 337 models): Low coverage OK
- Core logic (5 files, 524 lines): High coverage essential (target: 70%+)
- Focus testing effort where bugs are likely to occur

### Improving Coverage

See [Issue #31](https://github.com/dougborg/katana-openapi-client/issues/31) for
detailed improvement plan targeting:

- `katana_client.py`: 85% → 90%+ (add edge case tests)
- `client.py`: 51% → 70%+ (test common patterns)
- `log_setup.py`: 0% → 60%+ (add basic smoke tests)

## External Dependencies

- **Official Katana documentation**: Tests validate against `developer.katanamrp.com`
  content
- **Generated client validation**: Ensures openapi-python-client generates valid code
- **Real API integration**: Optional tests with actual Katana API (credentials required)
