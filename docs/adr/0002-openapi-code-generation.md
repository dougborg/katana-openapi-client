# ADR-002: Generate Client from OpenAPI Specification

## Status

Accepted

Date: 2024-07-01 (estimated based on initial project setup)

## Context

Building an API client for Katana Manufacturing ERP requires:

- Coverage of 76+ endpoints
- 150+ data models
- Full type safety with type hints
- Both sync and async support
- Maintenance as API evolves

Options for building the client:

1. **Hand-written client**: Write all API methods and models manually
1. **Generated client**: Auto-generate from OpenAPI specification
1. **Hybrid approach**: Generate base, hand-write wrappers

The Katana API provides an OpenAPI 3.1.0 specification with complete endpoint coverage.

## Decision

We will **auto-generate the client from the OpenAPI specification** using
`openapi-python-client`.

The generation process:

1. Maintain OpenAPI spec in `docs/katana-openapi.yaml`
1. Use `openapi-python-client` to generate Python client
1. Automated generation script: `scripts/regenerate_client.py`
1. Auto-fix generated code with `ruff --unsafe-fixes`
1. Generated code is read-only - never manually edit

Generated code structure:

```
katana_public_api_client/
├── api/              # 248 endpoint modules (generated)
├── models/           # 337 data models (generated)
├── client.py         # Base client classes (generated)
├── client_types.py   # Type definitions (generated)
├── errors.py         # Error classes (generated)
└── katana_client.py  # Enhanced client (hand-written)
```

Clear separation:

- **Generated code** (`api/`, `models/`, `client.py`, etc.): Never edit manually
- **Custom code** (`katana_client.py`, `utils.py`): Hand-written enhancements

## Consequences

### Positive Consequences

1. **Always in Sync**: Client stays current with API specification
1. **Type Safety**: Full type hints for all models and endpoints
1. **Completeness**: 100% endpoint coverage guaranteed
1. **Maintainability**: Regenerate on API changes, no manual updates
1. **Reliability**: Code generator is well-tested
1. **Both Sync and Async**: Generator creates both variants automatically
1. **IDE Support**: Full autocomplete and type checking
1. **Documentation**: Generated docstrings from OpenAPI descriptions
1. **Zero Manual Boilerplate**: 248 endpoint modules + 337 models auto-created

### Negative Consequences

1. **Generator Dependency**: Dependent on `openapi-python-client` updates
1. **Generated Code Style**: Limited control over generated code style
1. **Breaking Changes**: OpenAPI spec changes can break client
1. **Learning Curve**: Need to understand generator's patterns
1. **Large Codebase**: ~30,000 lines of generated code
1. **Limited Customization**: Can't customize generated code directly

### Neutral Consequences

1. **OpenAPI Spec Maintenance**: Must keep spec updated
1. **Generation Time**: ~2 minutes to regenerate client
1. **Build Dependency**: Requires `npx` for generation

## Alternatives Considered

### Alternative 1: Hand-Written Client

Write all API methods and models manually.

**Pros:**

- Full control over implementation
- Custom patterns and conventions
- No generator dependency
- Simpler debugging

**Cons:**

- Massive manual effort (248 endpoints × 2 variants = 496 methods)
- Error-prone (manual typing of 337 models)
- Hard to keep in sync with API changes
- No guarantee of completeness
- Months of initial development

**Why Rejected:** Too much manual work, prone to errors, hard to maintain.

### Alternative 2: Minimal Client + Manual Additions

Generate minimal base client, write wrappers for each endpoint.

**Pros:**

- Some automation
- Can customize wrappers
- Type safety from generation

**Cons:**

- Still requires manual wrappers for 248 endpoints
- Wrappers break on API changes
- Duplication between generated and wrapper code
- Maintenance burden

**Why Rejected:** Still too much manual work without enough benefit.

### Alternative 3: Different Generator

Use alternative OpenAPI generator (e.g., `openapi-generator`, custom generator).

**Pros:**

- Might have different features
- More customization options

**Cons:**

- `openapi-python-client` is well-maintained and Python-focused
- Supports OpenAPI 3.1.0
- Creates clean, idiomatic Python code
- Active community

**Why Rejected:** `openapi-python-client` is the best Python generator available.

## Implementation Details

### Regeneration Process

```bash
poetry run poe regenerate-client
```

The `scripts/regenerate_client.py` script:

1. Validates OpenAPI spec with `openapi-spec-validator`
1. Validates with Redocly for best practices
1. Runs `openapi-python-client` generator
1. Auto-fixes with `ruff check --fix --unsafe-fixes` (fixes 6,589+ issues)
1. Moves generated code to package location
1. Runs tests to verify

### Code Quality Automation

The regeneration automatically fixes:

- Import sorting and unused imports
- Code style consistency
- Unicode character fixes (×→\* multiplication signs)
- Line length and formatting
- Type hint standardization

No manual patches required - all fixes are automated.

### Maintaining Custom Code

Custom enhancements in separate files:

- `katana_client.py`: Enhanced client with resilience
- `utils.py`: Response unwrapping utilities
- `log_setup.py`: Logging configuration

These files are never touched by regeneration.

## References

- [openapi-python-client](https://github.com/openapi-generators/openapi-python-client)
- [OpenAPI 3.1.0 Specification](https://spec.openapis.org/oas/v3.1.0)
- [Katana API Documentation](https://help.katanamrp.com/api)
- [scripts/regenerate_client.py](../../scripts/regenerate_client.py)
- [docs/katana-openapi.yaml](../katana-openapi.yaml)
- [CLAUDE.md - Client Generation Process](../../CLAUDE.md#client-generation-process)
