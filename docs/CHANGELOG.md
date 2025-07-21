# CHANGELOG


## v0.2.0 (2025-07-21)

### Breaking

- feat: eliminate confusing client.client pattern - cleaner API design (#5)

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
  ([`116ea04`](https://github.com/dougborg/katana-openapi-client/commit/116ea0431a0f0d3e61163ed7076f1b2dd539bfa5))

### Chore

* chore(docs): Update README.md for python version support

We support 3.11 and newer. ([`ba2aeb7`](https://github.com/dougborg/katana-openapi-client/commit/ba2aeb7cc3d4c412652f74b4d583db1775e354d0))

* chore(release): 1.0.0 ([`b7af850`](https://github.com/dougborg/katana-openapi-client/commit/b7af8509ff9ec0805ff549290273f485d454d0f7))

* chore: Add comprehensive documentation generation and GitHub Pages publishing (#4)

- Add Sphinx documentation generation with AutoAPI

- Add comprehensive docstrings and GitHub Pages workflow

- Add documentation tests and final polishing
  ([`38b0cc7`](https://github.com/dougborg/katana-openapi-client/commit/38b0cc742fc83b64adda2055634979a3829c24ac))

* chore: add pre-commit hooks and development tooling (#6)

* Add comprehensive pre-commit configuration with ruff, yamllint, and general checks
* Add pre-commit poe tasks for installation, running, and updating hooks
* Update README with pre-commit setup instructions and workflow
* Update copilot instructions with pre-commit best practices and mandatory usage
* Add pre-commit to dev dependencies in pyproject.toml
* Add mdformat pre-commit hook to catch markdown formatting issues locally
* Auto-update pre-commit hooks to latest versions (mdformat 0.7.17 → 0.7.22)
* Fix CHANGELOG.md formatting that was causing CI failures
* Fix line wrapping in copilot instructions and PR template
* Add comprehensive conventional commit guidelines with examples
* Clarify when to use feat/fix/chore/docs/test/refactor/style
* Add explicit rules for version bumping to prevent release mistakes
* Improve formatting of conventional commit section for readability
* Ensure pre-commit hooks now match CI format-check requirements

This resolves the CI formatting failure and provides clear guidelines to prevent
incorrect conventional commit usage and establishes consistent code quality enforcement
across the development team without changing any functional codebase behavior.
([`d6511e6`](https://github.com/dougborg/katana-openapi-client/commit/d6511e68949a95ba6871ad7e60b6b7b9e295a535))

### Feature

* feat: Add OpenTracing support for distributed tracing integration (#2)

* Add OpenTracing support to Katana client with comprehensive tests and examples
* Update README with comprehensive OpenTracing documentation and usage examples ([`289184b`](https://github.com/dougborg/katana-openapi-client/commit/289184b4c6817fefddb63b656b2beb7655af71e4))

## v0.1.0 (2025-07-16)

### Chore

- chore(release): 0.1.0
  ([`88d5e94`](https://github.com/dougborg/katana-openapi-client/commit/88d5e94cbcd39049219fd02504a9af5f346c3394))

### Feature

- feat: initial release of katana-openapi-client

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
([`5ce390a`](https://github.com/dougborg/katana-openapi-client/commit/5ce390a604cc6f10993a3a5b416f7b55ef805871))
