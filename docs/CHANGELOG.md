# CHANGELOG

## v0.8.0 (2025-08-13)

### Features

- **webhooks**: Add comprehensive webhook documentation and fix pagination headers
  ([fc43b5f](https://github.com/dougborg/katana-openapi-client/commit/fc43b5f))
  - Add full OpenAPI 3.1 webhooks section with 59 webhook events
  - Implement WebhookEventPayload schema with proper object references
  - Group webhook events by category (Product, Sales Order, Manufacturing, etc.)
  - Fix X-Pagination header schema types from mixed integer/boolean to string
  - Regenerate client with updated OpenAPI specification
  - All webhook events now properly documented with payload schemas
  - Pagination headers now correctly typed as strings per HTTP standard

### Chore

- **docs**: Restore comprehensive Katana docs and cleanup redundant files
  ([2f2127d](https://github.com/dougborg/katana-openapi-client/commit/2f2127d))
  - Restore complete 245-page Katana API documentation archive
  - Add documentation extraction script for future updates
  - Clean up redundant and empty documentation files
  - Update pre-commit configuration to allow large documentation files

## v0.7.0 (2025-08-13)

### Breaking Changes

- **client**: Streamline regeneration script and flatten import structure
  ([d091c46](https://github.com/dougborg/katana-openapi-client/commit/d091c46))

BREAKING CHANGE: Major restructuring of client generation and import paths

- Flatten generated client structure - eliminate confusing `.generated` subdirectory
- Update import paths: use `from katana_public_api_client.api` directly
- Rename `types.py` to `client_types.py` to avoid stdlib conflicts
- Automate code quality fixes with `ruff --unsafe-fixes`
- Eliminate manual patches - all fixes now automated
- Streamline regeneration process with better error handling
- Update all documentation and examples for new import structure

## v0.6.0 (2025-08-12)

### Features

- **validation**: Complete comprehensive programmatic OpenAPI schema validation
  standards
  ([650f769](https://github.com/dougborg/katana-openapi-client/commit/650f769))
  - Implement comprehensive property description standards
  - Add payload examples for all request/response schemas
  - Establish consistent schema validation patterns
  - Improve API documentation completeness

### Chore

- **setup**: Set up Copilot instructions
  ([69bf6ce](https://github.com/dougborg/katana-openapi-client/commit/69bf6ce))

## v0.5.1 (2025-08-07)

### Fixes

- **schemas**: Improve BOM row schemas and validate against official documentation
  ([42d5bda](https://github.com/dougborg/katana-openapi-client/commit/42d5bda))

### Chore

- **docs**: Document established OpenAPI schema patterns in copilot instructions
  ([fcd31de](https://github.com/dougborg/katana-openapi-client/commit/fcd31de))

## v0.5.0 (2025-08-07)

### Features

- **schemas**: Enhance schema patterns and improve OpenAPI validation
  ([7e6fd3a](https://github.com/dougborg/katana-openapi-client/commit/7e6fd3a))
  - Improve schema consistency and validation patterns
  - Enhance OpenAPI specification quality

## v0.4.0 (2025-08-07)

### Features

- **schemas**: Introduce BaseEntity schema and improve parameter descriptions
  ([ef41c57](https://github.com/dougborg/katana-openapi-client/commit/ef41c57))
  - Add standardized BaseEntity schema for common fields
  - Improve parameter descriptions across endpoints
  - Enhance API documentation consistency

## v0.3.3 (2025-08-07)

### Fixes

- **schemas**: Fix BomRow and Location schemas and endpoints
  ([f017310](https://github.com/dougborg/katana-openapi-client/commit/f017310))

## v0.3.2 (2025-08-01)

### Fixes

- **parameters**: Update sku parameter to accept list of strings in get_all_variants
  ([7a1379a](https://github.com/dougborg/katana-openapi-client/commit/7a1379a))

## v0.3.1 (2025-07-31)

### Fixes

- **enums**: Add missing 'service' value to VariantResponseType enum
  ([707ba13](https://github.com/dougborg/katana-openapi-client/commit/707ba13))

## v0.3.0 (2025-07-30)

### Features

- **architecture**: DRY OpenAPI spec, regenerate client, and simplify error handling
  ([519d9b4](https://github.com/dougborg/katana-openapi-client/commit/519d9b4))
  - Implement DRY (Don't Repeat Yourself) principles in OpenAPI specification
  - Regenerate client with improved structure
  - Simplify error handling patterns
  - Reduce code duplication and improve maintainability

## v0.2.2 (2025-07-30)

### Fixes

- **spec**: Align OpenAPI spec with Katana docs and prep for DRY improvements
  ([cdaba92](https://github.com/dougborg/katana-openapi-client/commit/cdaba92))

## v0.2.1 (2025-07-28)

### Fixes

- **schemas**: Convert optional enum definitions to use anyOf pattern
  ([4ec9ed5](https://github.com/dougborg/katana-openapi-client/commit/4ec9ed5))
- **docs**: Fix AutoAPI duplicate object warnings and ensure generated code formatting
  consistency
  ([ec4de89](https://github.com/dougborg/katana-openapi-client/commit/ec4de89))

### Documentation

- **guides**: Refresh documentation with current project structure and patterns
  ([4988ca0](https://github.com/dougborg/katana-openapi-client/commit/4988ca0))

### Chore

- **schemas**: Standardize OpenAPI schema model names for consistent
  simple/response/list patterns
  ([7c9a775](https://github.com/dougborg/katana-openapi-client/commit/7c9a775))
- **release**: Fix release build failures by updating python-semantic-release to v10.2.0
  ([5008501](https://github.com/dougborg/katana-openapi-client/commit/5008501))

## v0.2.0 (2025-07-24)

### Breaking Changes

- **architecture**: Eliminate confusing client.client pattern - cleaner API design
  ([116ea04](https://github.com/dougborg/katana-openapi-client/commit/116ea04))

BREAKING CHANGE: KatanaClient now inherits directly from AuthenticatedClient instead of
wrapping it.

This significantly improves API ergonomics by eliminating the confusing
'client=client.client' pattern. Users can now pass KatanaClient directly to API methods:
'client=client'.

Changes:

- Make KatanaClient inherit from AuthenticatedClient
- Remove .client property - users pass KatanaClient directly
- Add py.typed file for PEP 561 type information distribution
- Update all documentation and examples to use clean API
- Fix all tests to work with new inheritance-based architecture
- Update AI instructions to reflect new architecture

### Additional Features

- **tracing**: Complete OpenTracing removal and optimize documentation testing
  ([acc71cd](https://github.com/dougborg/katana-openapi-client/commit/acc71cd))
- **client**: Update generated OpenAPI client with latest improvements
  ([29e2e2e](https://github.com/dougborg/katana-openapi-client/commit/29e2e2e))
- **logging**: Enhance error logging with beautiful human-readable formatting
  ([aa9fda1](https://github.com/dougborg/katana-openapi-client/commit/aa9fda1))
- **tracing**: Add OpenTracing support for distributed tracing integration
  ([289184b](https://github.com/dougborg/katana-openapi-client/commit/289184b))

### Bug Fixes

- **linting**: Configure ruff to properly ignore generated code
  ([c112157](https://github.com/dougborg/katana-openapi-client/commit/c112157))
- **linting**: Complete ruff linting fixes for modern Python syntax
  ([f1b88d6](https://github.com/dougborg/katana-openapi-client/commit/f1b88d6))
- **schemas**: Resolve OpenAPI nullable enum issues and enhance code generation
  ([283b74f](https://github.com/dougborg/katana-openapi-client/commit/283b74f))

### Documentation

- **generation**: Update documentation and GitHub workflows
  ([1c0de0b](https://github.com/dougborg/katana-openapi-client/commit/1c0de0b))
- **api**: Include generated API files in documentation
  ([2ffb10c](https://github.com/dougborg/katana-openapi-client/commit/2ffb10c))

### Development and Tooling

- **docs**: Update README.md for python version support
  ([ba2aeb7](https://github.com/dougborg/katana-openapi-client/commit/ba2aeb7))

- **docs**: Add comprehensive documentation generation and GitHub Pages publishing
  ([38b0cc7](https://github.com/dougborg/katana-openapi-client/commit/38b0cc7))

- Add Sphinx documentation generation with AutoAPI

- Add comprehensive docstrings and GitHub Pages workflow

- Add documentation tests and final polishing

- **development**: Add pre-commit hooks and development tooling
  ([d6511e6](https://github.com/dougborg/katana-openapi-client/commit/d6511e6))

- **workflow**: Clean up cruft files and improve .gitignore
  ([fe76ad4](https://github.com/dougborg/katana-openapi-client/commit/fe76ad4))

- **generation**: Optimize regeneration workflow and add systematic patches
  ([0b0560f](https://github.com/dougborg/katana-openapi-client/commit/0b0560f))

- **release**: Configure semantic-release for pre-1.0 development
  ([159f3b4](https://github.com/dougborg/katana-openapi-client/commit/159f3b4))

## v0.1.2 (2025-07-16)

### Initial Release Features

- **client**: Initial release of katana-openapi-client
  ([5ce390a](https://github.com/dougborg/katana-openapi-client/commit/5ce390a))

🚀 Production-ready Python client for Katana Manufacturing ERP API

✨ Key Features:

- Transport-layer resilience with automatic retries and rate limiting
- Smart auto-pagination for large datasets
- Type-safe async client with full mypy compliance
- Modern Python packaging with Poetry and PEP 621

🏗️ Architecture:

- Clean separation of generated OpenAPI client and custom enhancements
- ResilientAsyncTransport handles all HTTP resilience transparently
- Comprehensive error handling and logging
- Context manager pattern for resource management

🧪 Developer Experience:

- Comprehensive test suite with pytest and async support
- Modern development workflow with poethepoet task runner
- Automated formatting, linting, and type checking
- GitHub Actions CI/CD with semantic release
- Complete documentation and usage guides

🔧 Ready for Production:

- Automatic retry logic with exponential backoff
- Rate limiting with 429 response handling
- Pagination that works transparently with all endpoints
- Environment variable configuration
- Comprehensive error types and handling

Perfect for teams needing reliable integration with Katana Manufacturing ERP!

## v0.1.1 (2025-07-16)

### Initial Development

- Project initialization and basic setup

## v0.1.0 (2025-07-16)

### Initial Release

- Initial project creation and release infrastructure setup
