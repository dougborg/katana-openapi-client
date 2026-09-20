# Changelog

## [0.117.0](https://github.com/dougborg/katana-openapi-client/compare/mcp-v0.116.0...mcp-v0.117.0) (2026-09-20)


### ⚠ BREAKING CHANGES

* **client:** Variant/service custom fields accept UUID maps or legacy arrays; legacy update entries now require field_name and field_value and are limited to three. Pydantic-to-attrs conversion preserves explicit nullable values and omitted fields.

### Features

* **client:** support endpoint-specific custom field inputs ([#1062](https://github.com/dougborg/katana-openapi-client/issues/1062)) ([150766b](https://github.com/dougborg/katana-openapi-client/commit/150766b477114373973c09efd394f522c591413e))
* **mcp:** expose manufacturing traceability allocations ([#1059](https://github.com/dougborg/katana-openapi-client/issues/1059)) ([65bb993](https://github.com/dougborg/katana-openapi-client/commit/65bb9930cccb02592056188db524de1f18c38165))

## [0.116.0](https://github.com/dougborg/katana-openapi-client/compare/mcp-v0.115.0...mcp-v0.116.0) (2026-09-20)


### Features

* **client:** model traceability on manufacturing-order request DTOs ([#1052](https://github.com/dougborg/katana-openapi-client/issues/1052)) ([8dd7a16](https://github.com/dougborg/katana-openapi-client/commit/8dd7a161170a7b5581bc5b73a5b624b47df50b74))
* **release:** migrate to release-please manifest-mode release automation ([#1005](https://github.com/dougborg/katana-openapi-client/issues/1005)) ([ec4a0d0](https://github.com/dougborg/katana-openapi-client/commit/ec4a0d0fff8ed89f6a0a8f04dd43e704ebd73992))


### Bug Fixes

* **tests:** align MCP package asyncio_mode with the root ([#1004](https://github.com/dougborg/katana-openapi-client/issues/1004)) ([27ee3a1](https://github.com/dougborg/katana-openapi-client/commit/27ee3a1f3e2cd5c8581aed6d702a626ef35bb48f))

## CHANGELOG

All notable changes to the Katana MCP Server will be documented in this file.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
