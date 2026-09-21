# Changelog

## [0.119.1](https://github.com/dougborg/katana-openapi-client/compare/mcp-v0.119.0...mcp-v0.119.1) (2026-09-21)


### Bug Fixes

* **mcp:** carry MTO serial reservations through fulfillment ([#1093](https://github.com/dougborg/katana-openapi-client/issues/1093)) ([1545e62](https://github.com/dougborg/katana-openapi-client/commit/1545e627289417ed1cfb63b608ad8235183d9c70))

## [0.119.0](https://github.com/dougborg/katana-openapi-client/compare/mcp-v0.118.1...mcp-v0.119.0) (2026-09-21)


### ⚠ BREAKING CHANGES

* CreateMaterialRequest.variants now uses CreateMaterialVariantRequest rather than CreateVariantRequest. Nested sales_price and parent IDs are unsupported by POST /materials. Product and standalone variant creation retain their existing request model.

### Bug Fixes

* correct material variant creation and price updates ([#1089](https://github.com/dougborg/katana-openapi-client/issues/1089)) ([f419e1c](https://github.com/dougborg/katana-openapi-client/commit/f419e1ca7c5b4e7dd8221e0a841cf01179770e0a))

## [0.118.1](https://github.com/dougborg/katana-openapi-client/compare/mcp-v0.118.0...mcp-v0.118.1) (2026-09-21)


### Bug Fixes

* restore item config edits and synchronous API calls ([#1085](https://github.com/dougborg/katana-openapi-client/issues/1085)) ([ca70c24](https://github.com/dougborg/katana-openapi-client/commit/ca70c240e7964354bc79ba75d1976f6b2afb5967)), closes [#936](https://github.com/dougborg/katana-openapi-client/issues/936) [#601](https://github.com/dougborg/katana-openapi-client/issues/601)

## [0.118.0](https://github.com/dougborg/katana-openapi-client/compare/mcp-v0.117.0...mcp-v0.118.0) (2026-09-21)


### Features

* **mcp:** add sales return tools ([#1072](https://github.com/dougborg/katana-openapi-client/issues/1072)) ([40bb5a2](https://github.com/dougborg/katana-openapi-client/commit/40bb5a22af5f8de759f67deac6046aeb2c375ba3))
* **mcp:** discover and manage custom-field definitions ([#1066](https://github.com/dougborg/katana-openapi-client/issues/1066)) ([3ffaa6f](https://github.com/dougborg/katana-openapi-client/commit/3ffaa6f9813b706029218b2102284106178edee4))
* **mcp:** support sales-order custom fields ([#1073](https://github.com/dougborg/katana-openapi-client/issues/1073)) ([48334ac](https://github.com/dougborg/katana-openapi-client/commit/48334aca34c65c99da1654782c738092982548e8))


### Bug Fixes

* **mcp:** preserve nullable custom-field reads ([#1071](https://github.com/dougborg/katana-openapi-client/issues/1071)) ([93de279](https://github.com/dougborg/katana-openapi-client/commit/93de2797944f8563a075341a7066541e384c67a5))
* **mcp:** support FastMCP 4 and MCP SDK 2 ([#1079](https://github.com/dougborg/katana-openapi-client/issues/1079)) ([900eb3b](https://github.com/dougborg/katana-openapi-client/commit/900eb3b3d0d23029f2e3fc9d54a2ea4a125735e8))

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
