# CHANGELOG

<!-- version list -->

## v0.46.0 (2026-02-11)

### Bug Fixes

- **client**: Address review — clarify logger call convention, add end-to-end test
  ([#274](https://github.com/dougborg/katana-openapi-client/pull/274),
  [`a9e3453`](https://github.com/dougborg/katana-openapi-client/commit/a9e3453de9c33c5fd6f8868176702203144e81f8))

### Documentation

- **spec**: Document cost_per_unit constraint on stock adjustment rows
  ([#273](https://github.com/dougborg/katana-openapi-client/pull/273),
  [`35a5a30`](https://github.com/dougborg/katana-openapi-client/commit/35a5a3009b7ed030cd5c9bede2ce1a247f2bbb11))

- **spec**: Document cost_per_unit constraint on stock adjustment rows
  ([#274](https://github.com/dougborg/katana-openapi-client/pull/274),
  [`a9e3453`](https://github.com/dougborg/katana-openapi-client/commit/a9e3453de9c33c5fd6f8868176702203144e81f8))

### Features

- **client**: Accept duck-typed loggers via Logger protocol
  ([#274](https://github.com/dougborg/katana-openapi-client/pull/274),
  [`a9e3453`](https://github.com/dougborg/katana-openapi-client/commit/a9e3453de9c33c5fd6f8868176702203144e81f8))

## v0.45.0 (2026-02-11)

### Bug Fixes

- **client**: Preserve array query params across paginated requests
  ([#272](https://github.com/dougborg/katana-openapi-client/pull/272),
  [`599880f`](https://github.com/dougborg/katana-openapi-client/commit/599880f981579ec5891e18783ba37930f5bdb48d))

### Chores

- **release**: Mcp v0.30.0
  ([`d17976b`](https://github.com/dougborg/katana-openapi-client/commit/d17976bccd35e4470f40521851b2db05cd8776f1))

### Features

- **mcp**: Update client dependency to v0.44.6
  ([`e4559a3`](https://github.com/dougborg/katana-openapi-client/commit/e4559a3c23de1105c170e0c788a82ba3347225d8))

## v0.44.6 (2026-02-09)

### Bug Fixes

- Apply ruff 0.15.0 formatting and lint fixes
  ([`aefc8f7`](https://github.com/dougborg/katana-openapi-client/commit/aefc8f74d32ed6276643e44c13ba0606a2ef07c1))

### Chores

- **deps)(deps**: Bump the python-minor-patch group with 4 updates
  ([`58602a0`](https://github.com/dougborg/katana-openapi-client/commit/58602a0ac5590bb35277c4c604993585600d5e7f))

- **deps)(deps-dev**: Bump types-jsonschema
  ([`4960c8c`](https://github.com/dougborg/katana-openapi-client/commit/4960c8c384b636b4d5c7f7cb331251c6ca9587cc))

## v0.44.5 (2026-02-07)

### Bug Fixes

- Address second round of PR review comments
  ([#268](https://github.com/dougborg/katana-openapi-client/pull/268),
  [`8aa46b9`](https://github.com/dougborg/katana-openapi-client/commit/8aa46b9a990dbae3015b42d8413806bfd6161cf7))

- **client**: Address PR review comments
  ([#268](https://github.com/dougborg/katana-openapi-client/pull/268),
  [`8aa46b9`](https://github.com/dougborg/katana-openapi-client/commit/8aa46b9a990dbae3015b42d8413806bfd6161cf7))

- **client**: Address second round of PR review comments
  ([#268](https://github.com/dougborg/katana-openapi-client/pull/268),
  [`8aa46b9`](https://github.com/dougborg/katana-openapi-client/commit/8aa46b9a990dbae3015b42d8413806bfd6161cf7))

- **client**: Align P4 OpenAPI schemas with Katana official API
  ([#268](https://github.com/dougborg/katana-openapi-client/pull/268),
  [`8aa46b9`](https://github.com/dougborg/katana-openapi-client/commit/8aa46b9a990dbae3015b42d8413806bfd6161cf7))

- **client**: Preserve original response shape in PaginationTransport
  ([#268](https://github.com/dougborg/katana-openapi-client/pull/268),
  [`8aa46b9`](https://github.com/dougborg/katana-openapi-client/commit/8aa46b9a990dbae3015b42d8413806bfd6161cf7))

- **client**: Regenerate TypeScript client for P4 schema alignment
  ([#268](https://github.com/dougborg/katana-openapi-client/pull/268),
  [`8aa46b9`](https://github.com/dougborg/katana-openapi-client/commit/8aa46b9a990dbae3015b42d8413806bfd6161cf7))

- **mcp**: Update stock adjustment field references after P4 alignment
  ([#268](https://github.com/dougborg/katana-openapi-client/pull/268),
  [`8aa46b9`](https://github.com/dougborg/katana-openapi-client/commit/8aa46b9a990dbae3015b42d8413806bfd6161cf7))

### Documentation

- Add Katana API questions document for P4 alignment follow-up
  ([#268](https://github.com/dougborg/katana-openapi-client/pull/268),
  [`8aa46b9`](https://github.com/dougborg/katana-openapi-client/commit/8aa46b9a990dbae3015b42d8413806bfd6161cf7))

- Add live API investigation findings to API questions document
  ([#268](https://github.com/dougborg/katana-openapi-client/pull/268),
  [`8aa46b9`](https://github.com/dougborg/katana-openapi-client/commit/8aa46b9a990dbae3015b42d8413806bfd6161cf7))

- Update endpoint and model counts after P4 alignment
  ([#268](https://github.com/dougborg/katana-openapi-client/pull/268),
  [`8aa46b9`](https://github.com/dougborg/katana-openapi-client/commit/8aa46b9a990dbae3015b42d8413806bfd6161cf7))

- Update endpoint count in OpenAPI docs page
  ([#268](https://github.com/dougborg/katana-openapi-client/pull/268),
  [`8aa46b9`](https://github.com/dougborg/katana-openapi-client/commit/8aa46b9a990dbae3015b42d8413806bfd6161cf7))

### Refactoring

- **client**: Extract 22 inline schemas to named schemas in OpenAPI spec
  ([#268](https://github.com/dougborg/katana-openapi-client/pull/268),
  [`8aa46b9`](https://github.com/dougborg/katana-openapi-client/commit/8aa46b9a990dbae3015b42d8413806bfd6161cf7))

## v0.44.4 (2026-02-06)

### Bug Fixes

- **client**: Align P3 OpenAPI schemas with Katana official API
  ([#267](https://github.com/dougborg/katana-openapi-client/pull/267),
  [`9cd8ba0`](https://github.com/dougborg/katana-openapi-client/commit/9cd8ba01ff18efddc192b6641ff8f25cd3ed23a4))

### Documentation

- **client**: Add default page size to ADR-003 context
  ([#235](https://github.com/dougborg/katana-openapi-client/pull/235),
  [`ca346ff`](https://github.com/dougborg/katana-openapi-client/commit/ca346ffa61149a81872c186af3216d449334531e))

- **client**: Update ADR-003 to reflect limit=250 default
  ([#235](https://github.com/dougborg/katana-openapi-client/pull/235),
  [`ca346ff`](https://github.com/dougborg/katana-openapi-client/commit/ca346ffa61149a81872c186af3216d449334531e))

## v0.44.3 (2026-02-06)

### Bug Fixes

- **client**: Align P2 OpenAPI schemas with Katana official API
  ([#266](https://github.com/dougborg/katana-openapi-client/pull/266),
  [`af03314`](https://github.com/dougborg/katana-openapi-client/commit/af033145b709c840aadbd74f8fb7f471a28c5a70))

## v0.44.2 (2026-02-06)

### Bug Fixes

- **client**: Add missing is_archived field to UpdateProductRequest
  ([#265](https://github.com/dougborg/katana-openapi-client/pull/265),
  [`ddbcc0b`](https://github.com/dougborg/katana-openapi-client/commit/ddbcc0b0bb0a9e3ade60469e2908680eb43f254c))

- **client**: Align P1 OpenAPI schemas with Katana official API
  ([#265](https://github.com/dougborg/katana-openapi-client/pull/265),
  [`ddbcc0b`](https://github.com/dougborg/katana-openapi-client/commit/ddbcc0b0bb0a9e3ade60469e2908680eb43f254c))

- **client**: Align P1 OpenAPI schemas with Katana official API spec
  ([#265](https://github.com/dougborg/katana-openapi-client/pull/265),
  [`ddbcc0b`](https://github.com/dougborg/katana-openapi-client/commit/ddbcc0b0bb0a9e3ade60469e2908680eb43f254c))

- **scripts**: Remove API key logging to address security warning
  ([#265](https://github.com/dougborg/katana-openapi-client/pull/265),
  [`ddbcc0b`](https://github.com/dougborg/katana-openapi-client/commit/ddbcc0b0bb0a9e3ade60469e2908680eb43f254c))

### Documentation

- Add Katana API comprehensive documentation for spec comparison
  ([#265](https://github.com/dougborg/katana-openapi-client/pull/265),
  [`ddbcc0b`](https://github.com/dougborg/katana-openapi-client/commit/ddbcc0b0bb0a9e3ade60469e2908680eb43f254c))

## v0.44.1 (2026-02-06)

### Bug Fixes

- **client**: Correct pagination defaults for auto-pagination
  ([#234](https://github.com/dougborg/katana-openapi-client/pull/234),
  [`5c97def`](https://github.com/dougborg/katana-openapi-client/commit/5c97deff077316f660278e8c28cadf375762ca34))

### Testing

- **client**: Add missing zero limit edge case test
  ([#234](https://github.com/dougborg/katana-openapi-client/pull/234),
  [`5c97def`](https://github.com/dougborg/katana-openapi-client/commit/5c97deff077316f660278e8c28cadf375762ca34))

## v0.44.0 (2026-02-05)

### Bug Fixes

- **client**: Align stocktake row schema with Katana API
  ([#231](https://github.com/dougborg/katana-openapi-client/pull/231),
  [`2827857`](https://github.com/dougborg/katana-openapi-client/commit/28278571e9a801271d2dcb586e977c5d8705046f))

- **client**: Handle null ingredient_expected_date in ManufacturingOrderRecipeRow
  ([`6ffd928`](https://github.com/dougborg/katana-openapi-client/commit/6ffd928cee225b07d147b98a2181bb05fa0f9dda))

- **client**: Handle null sales_order_delivery_deadline in ManufacturingOrder
  ([`c89b8f4`](https://github.com/dougborg/katana-openapi-client/commit/c89b8f48542bb366ee9be2503fcfc50533682ba4))

- **deps**: Bump urllib3 to 2.6.3 for CVE-2026-21441
  ([#227](https://github.com/dougborg/katana-openapi-client/pull/227),
  [`1124ea8`](https://github.com/dougborg/katana-openapi-client/commit/1124ea828596e6ae3ab8078a353d63feea0942bc))

### Chores

- **deps)(deps**: Bump the python-minor-patch group with 11 updates
  ([#228](https://github.com/dougborg/katana-openapi-client/pull/228),
  [`9b81517`](https://github.com/dougborg/katana-openapi-client/commit/9b8151777e3156ba4b1feaed4cab10299c7f1d6d))

- **deps)(deps**: Bump the python-minor-patch group with 2 updates
  ([#229](https://github.com/dougborg/katana-openapi-client/pull/229),
  [`dcfa11f`](https://github.com/dougborg/katana-openapi-client/commit/dcfa11f47c61dc0a055c2143e458122050ffd773))

- **deps)(deps**: Bump types-python-dateutil
  ([#230](https://github.com/dougborg/katana-openapi-client/pull/230),
  [`5563c70`](https://github.com/dougborg/katana-openapi-client/commit/5563c703ab0227dc2a1ee2eb28f2e0abd231a71d))

- **deps)(deps-dev**: Bump ty in the python-minor-patch group
  ([#232](https://github.com/dougborg/katana-openapi-client/pull/232),
  [`9617414`](https://github.com/dougborg/katana-openapi-client/commit/96174148c049748dc05586142cec3e0e175081bf))

- **release**: Mcp v0.29.0
  ([`deec6f3`](https://github.com/dougborg/katana-openapi-client/commit/deec6f355a83e93e3f8f471e708d6f0d29722fec))

### Documentation

- Remove stale docs and fix placeholder references
  ([#233](https://github.com/dougborg/katana-openapi-client/pull/233),
  [`3f73417`](https://github.com/dougborg/katana-openapi-client/commit/3f734170b1c0e0332acce021a08704d5c79e5aa2))

### Features

- **mcp**: Update client dependency to v0.43.0
  ([#226](https://github.com/dougborg/katana-openapi-client/pull/226),
  [`a6e177c`](https://github.com/dougborg/katana-openapi-client/commit/a6e177ce07a01389585528b1ce967c92f76dca13))

## v0.43.0 (2026-01-16)

### Bug Fixes

- **client**: Address PR review comments from Copilot
  ([#214](https://github.com/dougborg/katana-openapi-client/pull/214),
  [`1d5200b`](https://github.com/dougborg/katana-openapi-client/commit/1d5200b6bb987d3594705d579a6b35cac37a7286))

- **client**: Resolve type errors for ty 0.0.11 compatibility
  ([#224](https://github.com/dougborg/katana-openapi-client/pull/224),
  [`f5ea245`](https://github.com/dougborg/katana-openapi-client/commit/f5ea245094414ba0b9f1fde5260a181a9486ddb1))

- **client**: Resolve type errors for ty 0.0.1a25 compatibility
  ([#225](https://github.com/dougborg/katana-openapi-client/pull/225),
  [`13dbf43`](https://github.com/dougborg/katana-openapi-client/commit/13dbf43cf400c16fedd86a87fe44d239aa46b16d))

- **mcp**: Address review comments on hardcoded values
  ([#213](https://github.com/dougborg/katana-openapi-client/pull/213),
  [`cbe040e`](https://github.com/dougborg/katana-openapi-client/commit/cbe040eb765e7b38bb664e431e33cf11637aba4b))

- **mcp**: Fix incomplete template variable check in test
  ([#213](https://github.com/dougborg/katana-openapi-client/pull/213),
  [`cbe040e`](https://github.com/dougborg/katana-openapi-client/commit/cbe040eb765e7b38bb664e431e33cf11637aba4b))

- **mcp**: Use explicit if-else for empty list fallbacks
  ([#213](https://github.com/dougborg/katana-openapi-client/pull/213),
  [`cbe040e`](https://github.com/dougborg/katana-openapi-client/commit/cbe040eb765e7b38bb664e431e33cf11637aba4b))

### Chores

- **actions)(deps**: Bump the github-actions group with 4 updates
  ([#212](https://github.com/dougborg/katana-openapi-client/pull/212),
  [`792734d`](https://github.com/dougborg/katana-openapi-client/commit/792734dd6008cfe65339508cb247a2cc7a2c832a))

- **deps)(deps**: Bump the python-minor-patch group across 1 directory with 11 updates
  ([#224](https://github.com/dougborg/katana-openapi-client/pull/224),
  [`f5ea245`](https://github.com/dougborg/katana-openapi-client/commit/f5ea245094414ba0b9f1fde5260a181a9486ddb1))

- **deps)(deps**: Bump the python-minor-patch group with 9 updates
  ([#217](https://github.com/dougborg/katana-openapi-client/pull/217),
  [`a91edbb`](https://github.com/dougborg/katana-openapi-client/commit/a91edbb2ee228aea30b6eb3f8f8ba48d3325794a))

- **deps)(deps**: Bump types-python-dateutil
  ([#218](https://github.com/dougborg/katana-openapi-client/pull/218),
  [`4a9d5b6`](https://github.com/dougborg/katana-openapi-client/commit/4a9d5b61c6163ba314b7ad3f489596172e84f6c3))

- **infra**: Enable Dependabot uv support for Python dependencies
  ([#216](https://github.com/dougborg/katana-openapi-client/pull/216),
  [`b00b0a1`](https://github.com/dougborg/katana-openapi-client/commit/b00b0a1241e44b147c3a079ae129137eab0afe74))

- **release**: Mcp v0.27.0
  ([`38556ce`](https://github.com/dougborg/katana-openapi-client/commit/38556ce6404ae2d3b9f2ae5a3b36e1746a3773bd))

- **release**: Mcp v0.28.0
  ([`45580ed`](https://github.com/dougborg/katana-openapi-client/commit/45580ed4e2f5d8b8b6361c951d7df35972225fb3))

### Documentation

- Fix exception hierarchy documentation in CLAUDE.md
  ([#214](https://github.com/dougborg/katana-openapi-client/pull/214),
  [`1d5200b`](https://github.com/dougborg/katana-openapi-client/commit/1d5200b6bb987d3594705d579a6b35cac37a7286))

### Features

- **client**: Add ProductionIngredient resource type to inventory movements
  ([#225](https://github.com/dougborg/katana-openapi-client/pull/225),
  [`13dbf43`](https://github.com/dougborg/katana-openapi-client/commit/13dbf43cf400c16fedd86a87fe44d239aa46b16d))

- **mcp**: Add token reduction patterns and ToolResult integration
  ([#213](https://github.com/dougborg/katana-openapi-client/pull/213),
  [`cbe040e`](https://github.com/dougborg/katana-openapi-client/commit/cbe040eb765e7b38bb664e431e33cf11637aba4b))

- **mcp**: Update client dependency to v0.42.0
  ([#211](https://github.com/dougborg/katana-openapi-client/pull/211),
  [`990dd93`](https://github.com/dougborg/katana-openapi-client/commit/990dd931430b0d2de5e113f675407f51d52f4259))

### Refactoring

- **client,mcp**: Use consistent helper utilities for API response handling
  ([#214](https://github.com/dougborg/katana-openapi-client/pull/214),
  [`1d5200b`](https://github.com/dougborg/katana-openapi-client/commit/1d5200b6bb987d3594705d579a6b35cac37a7286))

- **mcp**: Use shared make_tool_result utility
  ([#213](https://github.com/dougborg/katana-openapi-client/pull/213),
  [`cbe040e`](https://github.com/dougborg/katana-openapi-client/commit/cbe040eb765e7b38bb664e431e33cf11637aba4b))

## v0.42.0 (2025-12-12)

### Bug Fixes

- **client**: Handle boolean string pagination fields (first_page, last_page)
  ([#210](https://github.com/dougborg/katana-openapi-client/pull/210),
  [`bb2238d`](https://github.com/dougborg/katana-openapi-client/commit/bb2238d55b0a9639d476e609ff4b70c6e54137cd))

- **docs**: Address PR review comments
  ([#208](https://github.com/dougborg/katana-openapi-client/pull/208),
  [`860be5a`](https://github.com/dougborg/katana-openapi-client/commit/860be5aaebe62bc34afae974b89152f5557cb470))

- **docs**: Correct TypeScript ADR references and MCP tool counts
  ([#208](https://github.com/dougborg/katana-openapi-client/pull/208),
  [`860be5a`](https://github.com/dougborg/katana-openapi-client/commit/860be5aaebe62bc34afae974b89152f5557cb470))

- **mcp**: Address additional PR review comments
  ([#205](https://github.com/dougborg/katana-openapi-client/pull/205),
  [`dd41a07`](https://github.com/dougborg/katana-openapi-client/commit/dd41a07f1b99780f7a8941bdbbfbce0b9615a32c))

- **mcp**: Patch FastMCP for Pydantic 2.12+ compatibility
  ([#204](https://github.com/dougborg/katana-openapi-client/pull/204),
  [`9a651b2`](https://github.com/dougborg/katana-openapi-client/commit/9a651b253a72990363c25a76134cb5e63df7a579))

- **mcp**: Remove dead code and unused fixture params from integration tests
  ([#205](https://github.com/dougborg/katana-openapi-client/pull/205),
  [`dd41a07`](https://github.com/dougborg/katana-openapi-client/commit/dd41a07f1b99780f7a8941bdbbfbce0b9615a32c))

- **mcp**: Use unwrap_data helper for list response extraction
  ([#205](https://github.com/dougborg/katana-openapi-client/pull/205),
  [`dd41a07`](https://github.com/dougborg/katana-openapi-client/commit/dd41a07f1b99780f7a8941bdbbfbce0b9615a32c))

### Chores

- **release**: Mcp v0.24.0
  ([`85bdbb4`](https://github.com/dougborg/katana-openapi-client/commit/85bdbb48ff82746bb6763b353d3e17fe5573597b))

- **release**: Mcp v0.25.0
  ([`6748599`](https://github.com/dougborg/katana-openapi-client/commit/6748599d174fe39779d2b0595128739962310b11))

- **release**: Mcp v0.26.0
  ([`d77f3b6`](https://github.com/dougborg/katana-openapi-client/commit/d77f3b65bda9437aa4b5c4837c24537b3d10fcda))

### Code Style

- **mcp**: Move imports to module level per review feedback
  ([#205](https://github.com/dougborg/katana-openapi-client/pull/205),
  [`dd41a07`](https://github.com/dougborg/katana-openapi-client/commit/dd41a07f1b99780f7a8941bdbbfbce0b9615a32c))

### Documentation

- Overhaul documentation for multi-package ecosystem
  ([#208](https://github.com/dougborg/katana-openapi-client/pull/208),
  [`860be5a`](https://github.com/dougborg/katana-openapi-client/commit/860be5aaebe62bc34afae974b89152f5557cb470))

### Features

- **mcp**: Add CLI transport options and simplify CLAUDE.md
  ([#209](https://github.com/dougborg/katana-openapi-client/pull/209),
  [`103ea19`](https://github.com/dougborg/katana-openapi-client/commit/103ea19854d55d2dac2b3d0783fcf7e8f6391b67))

- **mcp**: Add integration tests for end-to-end workflows
  ([#205](https://github.com/dougborg/katana-openapi-client/pull/205),
  [`dd41a07`](https://github.com/dougborg/katana-openapi-client/commit/dd41a07f1b99780f7a8941bdbbfbce0b9615a32c))

- **mcp**: Add response caching middleware and migrate pytest to native TOML
  ([#204](https://github.com/dougborg/katana-openapi-client/pull/204),
  [`9a651b2`](https://github.com/dougborg/katana-openapi-client/commit/9a651b253a72990363c25a76134cb5e63df7a579))

- **mcp**: Add test data isolation and cleanup utilities
  ([#205](https://github.com/dougborg/katana-openapi-client/pull/205),
  [`dd41a07`](https://github.com/dougborg/katana-openapi-client/commit/dd41a07f1b99780f7a8941bdbbfbce0b9615a32c))

- **mcp**: Update client dependency to v0.41.0
  ([#203](https://github.com/dougborg/katana-openapi-client/pull/203),
  [`4b3ea94`](https://github.com/dougborg/katana-openapi-client/commit/4b3ea944f15ea5d664720a957f9be744b9b7c2be))

### Testing

- **client**: Add edge case tests for boolean pagination field conversion
  ([#210](https://github.com/dougborg/katana-openapi-client/pull/210),
  [`bb2238d`](https://github.com/dougborg/katana-openapi-client/commit/bb2238d55b0a9639d476e609ff4b70c6e54137cd))

- **client**: Improve test coverage per review feedback
  ([#210](https://github.com/dougborg/katana-openapi-client/pull/210),
  [`bb2238d`](https://github.com/dougborg/katana-openapi-client/commit/bb2238d55b0a9639d476e609ff4b70c6e54137cd))

## v0.41.0 (2025-12-10)

### Bug Fixes

- **client**: Update dependencies to address urllib3 security vulnerabilities
  ([#202](https://github.com/dougborg/katana-openapi-client/pull/202),
  [`d4d1fb1`](https://github.com/dougborg/katana-openapi-client/commit/d4d1fb1481e5039cbdf79c35c39465450c647b53))

### Chores

- **release**: Mcp v0.23.0
  ([`5ade79f`](https://github.com/dougborg/katana-openapi-client/commit/5ade79fb9d863d4a96aa0c7377bf957036b8d7a7))

### Features

- **mcp**: Add create_sales_order tool
  ([#201](https://github.com/dougborg/katana-openapi-client/pull/201),
  [`055352c`](https://github.com/dougborg/katana-openapi-client/commit/055352cb8c66a734ff1f7bbafe6d3055fd65061f))

## v0.40.0 (2025-12-10)

### Bug Fixes

- Address self-review feedback and exclude integration tests
  ([#198](https://github.com/dougborg/katana-openapi-client/pull/198),
  [`5fb337d`](https://github.com/dougborg/katana-openapi-client/commit/5fb337d9dabc0d03b60de306f9497dfe007e4181))

- **client**: Address PR review feedback - remove unused code
  ([#197](https://github.com/dougborg/katana-openapi-client/pull/197),
  [`744aabc`](https://github.com/dougborg/katana-openapi-client/commit/744aabccc62ee9a926681de8675e25a15aba0b74))

- **client**: Align domain model types and constraints with OpenAPI spec
  ([#199](https://github.com/dougborg/katana-openapi-client/pull/199),
  [`86f454e`](https://github.com/dougborg/katana-openapi-client/commit/86f454e9fbf8fc2284ada4bd9c429d45188e79a6))

- **client**: Use AwareDatetime for all timestamp fields in domain models
  ([#199](https://github.com/dougborg/katana-openapi-client/pull/199),
  [`86f454e`](https://github.com/dougborg/katana-openapi-client/commit/86f454e9fbf8fc2284ada4bd9c429d45188e79a6))

- **client**: Use datetime for archived_at and deleted_at fields
  ([#199](https://github.com/dougborg/katana-openapi-client/pull/199),
  [`86f454e`](https://github.com/dougborg/katana-openapi-client/commit/86f454e9fbf8fc2284ada4bd9c429d45188e79a6))

### Chores

- **client**: Update dependencies to latest versions
  ([#197](https://github.com/dougborg/katana-openapi-client/pull/197),
  [`744aabc`](https://github.com/dougborg/katana-openapi-client/commit/744aabccc62ee9a926681de8675e25a15aba0b74))

- **release**: Mcp v0.22.0
  ([`72cd376`](https://github.com/dougborg/katana-openapi-client/commit/72cd3766338e71a30a22164e370c7f91e74fac6a))

### Documentation

- **client**: Add comprehensive TypeScript client documentation
  ([#198](https://github.com/dougborg/katana-openapi-client/pull/198),
  [`5fb337d`](https://github.com/dougborg/katana-openapi-client/commit/5fb337d9dabc0d03b60de306f9497dfe007e4181))

### Features

- **client**: Add auto-generated Pydantic models from OpenAPI
  ([#199](https://github.com/dougborg/katana-openapi-client/pull/199),
  [`86f454e`](https://github.com/dougborg/katana-openapi-client/commit/86f454e9fbf8fc2284ada4bd9c429d45188e79a6))

- **client**: Add auto-generated Pydantic v2 models from OpenAPI
  ([#199](https://github.com/dougborg/katana-openapi-client/pull/199),
  [`86f454e`](https://github.com/dougborg/katana-openapi-client/commit/86f454e9fbf8fc2284ada4bd9c429d45188e79a6))

- **mcp**: Update client dependency to v0.39.0
  ([#196](https://github.com/dougborg/katana-openapi-client/pull/196),
  [`95cda20`](https://github.com/dougborg/katana-openapi-client/commit/95cda20ab5c0381755bd813a36ac56da1f53b5d0))

- **ts-client**: Add TypeScript client with resilient transport
  ([#197](https://github.com/dougborg/katana-openapi-client/pull/197),
  [`744aabc`](https://github.com/dougborg/katana-openapi-client/commit/744aabccc62ee9a926681de8675e25a15aba0b74))

- **ts-client**: Add TypeScript client with retry and pagination transport
  ([#197](https://github.com/dougborg/katana-openapi-client/pull/197),
  [`744aabc`](https://github.com/dougborg/katana-openapi-client/commit/744aabccc62ee9a926681de8675e25a15aba0b74))

- **ts-client**: Integrate KatanaClient with generated SDK and add tests
  ([#197](https://github.com/dougborg/katana-openapi-client/pull/197),
  [`744aabc`](https://github.com/dougborg/katana-openapi-client/commit/744aabccc62ee9a926681de8675e25a15aba0b74))

### Refactoring

- **client**: Improve pydantic models code quality
  ([#199](https://github.com/dougborg/katana-openapi-client/pull/199),
  [`86f454e`](https://github.com/dougborg/katana-openapi-client/commit/86f454e9fbf8fc2284ada4bd9c429d45188e79a6))

- **client**: Modernize dependencies for 2025
  ([#198](https://github.com/dougborg/katana-openapi-client/pull/198),
  [`5fb337d`](https://github.com/dougborg/katana-openapi-client/commit/5fb337d9dabc0d03b60de306f9497dfe007e4181))

- **client**: Modernize TypeScript client dependencies for 2025
  ([#198](https://github.com/dougborg/katana-openapi-client/pull/198),
  [`5fb337d`](https://github.com/dougborg/katana-openapi-client/commit/5fb337d9dabc0d03b60de306f9497dfe007e4181))

- **client**: Use composition pattern for domain models
  ([#199](https://github.com/dougborg/katana-openapi-client/pull/199),
  [`86f454e`](https://github.com/dougborg/katana-openapi-client/commit/86f454e9fbf8fc2284ada4bd9c429d45188e79a6))

### Testing

- **client**: Add comprehensive tests for domain model factory methods
  ([#199](https://github.com/dougborg/katana-openapi-client/pull/199),
  [`86f454e`](https://github.com/dougborg/katana-openapi-client/commit/86f454e9fbf8fc2284ada4bd9c429d45188e79a6))

## v0.39.0 (2025-12-05)

### Bug Fixes

- **client**: Address Copilot review feedback for pagination normalization
  ([#195](https://github.com/dougborg/katana-openapi-client/pull/195),
  [`5665061`](https://github.com/dougborg/katana-openapi-client/commit/5665061e87fc77fddc610e1009e4e3ec6a0dccf7))

- **client**: Convert pagination string values to integers for correct comparison
  ([#195](https://github.com/dougborg/katana-openapi-client/pull/195),
  [`5665061`](https://github.com/dougborg/katana-openapi-client/commit/5665061e87fc77fddc610e1009e4e3ec6a0dccf7))

- **client**: Improve pagination value normalization edge case handling
  ([#195](https://github.com/dougborg/katana-openapi-client/pull/195),
  [`5665061`](https://github.com/dougborg/katana-openapi-client/commit/5665061e87fc77fddc610e1009e4e3ec6a0dccf7))

### Chores

- **release**: Mcp v0.21.0
  ([`86c11de`](https://github.com/dougborg/katana-openapi-client/commit/86c11de0e981296408a8fe4be42315983959f8c7))

### Features

- **mcp**: Update client dependency to v0.38.0
  ([#194](https://github.com/dougborg/katana-openapi-client/pull/194),
  [`9d9a4f3`](https://github.com/dougborg/katana-openapi-client/commit/9d9a4f324c8d9e988bac9251f764104aa8a7a24e))

## v0.38.0 (2025-12-05)

### Bug Fixes

- **client**: Address code review feedback on auto-pagination
  ([#193](https://github.com/dougborg/katana-openapi-client/pull/193),
  [`b85351b`](https://github.com/dougborg/katana-openapi-client/commit/b85351b7ee449b8ca0971c07bd6e160e27d4ae94))

- **client**: Enable auto-pagination by default in generated code
  ([#193](https://github.com/dougborg/katana-openapi-client/pull/193),
  [`b85351b`](https://github.com/dougborg/katana-openapi-client/commit/b85351b7ee449b8ca0971c07bd6e160e27d4ae94))

- **client**: Improve auto-pagination defaults and explicit controls
  ([#193](https://github.com/dougborg/katana-openapi-client/pull/193),
  [`b85351b`](https://github.com/dougborg/katana-openapi-client/commit/b85351b7ee449b8ca0971c07bd6e160e27d4ae94))

- **client**: Make regex pattern more robust for page defaults
  ([#193](https://github.com/dougborg/katana-openapi-client/pull/193),
  [`b85351b`](https://github.com/dougborg/katana-openapi-client/commit/b85351b7ee449b8ca0971c07bd6e160e27d4ae94))

- **mcp**: Consolidate test fixtures to resolve conftest plugin conflict
  ([#193](https://github.com/dougborg/katana-openapi-client/pull/193),
  [`b85351b`](https://github.com/dougborg/katana-openapi-client/commit/b85351b7ee449b8ca0971c07bd6e160e27d4ae94))

### Chores

- Add .cursor/ to .gitignore
  ([#193](https://github.com/dougborg/katana-openapi-client/pull/193),
  [`b85351b`](https://github.com/dougborg/katana-openapi-client/commit/b85351b7ee449b8ca0971c07bd6e160e27d4ae94))

- **release**: Mcp v0.20.0
  ([`ce3a2a6`](https://github.com/dougborg/katana-openapi-client/commit/ce3a2a6cf5ee911b9247d30ab52a6d9453864446))

### Features

- **client**: Improve auto-pagination with explicit controls
  ([#193](https://github.com/dougborg/katana-openapi-client/pull/193),
  [`b85351b`](https://github.com/dougborg/katana-openapi-client/commit/b85351b7ee449b8ca0971c07bd6e160e27d4ae94))

- **mcp**: Update client dependency to v0.37.0
  ([#192](https://github.com/dougborg/katana-openapi-client/pull/192),
  [`c8c62c4`](https://github.com/dougborg/katana-openapi-client/commit/c8c62c4c35765e32aec8d30e10f45ed14954cc3f))

## v0.37.0 (2025-12-05)

### Bug Fixes

- **client**: Address code review feedback on auto-pagination
  ([#191](https://github.com/dougborg/katana-openapi-client/pull/191),
  [`8dc3cfc`](https://github.com/dougborg/katana-openapi-client/commit/8dc3cfcb1e9751b2c204a709846bee9dd1cc9eea))

- **mcp**: Consolidate test fixtures to resolve conftest plugin conflict
  ([#191](https://github.com/dougborg/katana-openapi-client/pull/191),
  [`8dc3cfc`](https://github.com/dougborg/katana-openapi-client/commit/8dc3cfcb1e9751b2c204a709846bee9dd1cc9eea))

### Chores

- **actions)(deps**: Bump actions/checkout in the github-actions group
  ([#190](https://github.com/dougborg/katana-openapi-client/pull/190),
  [`76ad170`](https://github.com/dougborg/katana-openapi-client/commit/76ad170e6855db06ac464e69729fb4a34267d581))

- **release**: Mcp v0.19.0
  ([`33b13f6`](https://github.com/dougborg/katana-openapi-client/commit/33b13f640bcdfbad0cc1395ef114158e6d79dec2))

### Documentation

- Add strict quality standards - no ignoring pre-existing issues
  ([#188](https://github.com/dougborg/katana-openapi-client/pull/188),
  [`c7424a2`](https://github.com/dougborg/katana-openapi-client/commit/c7424a290477dffff0f9a1f18c046764c3654b91))

### Features

- **client**: Improve auto-pagination with explicit controls
  ([#191](https://github.com/dougborg/katana-openapi-client/pull/191),
  [`8dc3cfc`](https://github.com/dougborg/katana-openapi-client/commit/8dc3cfcb1e9751b2c204a709846bee9dd1cc9eea))

- **mcp**: Update client dependency to v0.36.0
  ([`e31ddb5`](https://github.com/dougborg/katana-openapi-client/commit/e31ddb52bacb9c9a0c62eaad19239c4f241d4d15))

## v0.36.0 (2025-11-22)

### Bug Fixes

- Address Copilot review comments in .cursorrules
  ([`f1007f4`](https://github.com/dougborg/katana-openapi-client/commit/f1007f4d9e476c725e13d71629aeeca39eb1faf0))

### Chores

- **release**: Mcp v0.18.0
  ([`7cdd30c`](https://github.com/dougborg/katana-openapi-client/commit/7cdd30c781b64aec24b14f3ea31ae0f686ca813c))

### Features

- Add Cursor rules for better AI assistance
  ([`65851d4`](https://github.com/dougborg/katana-openapi-client/commit/65851d4a9880589c62a664dd2b192d62cb5ff0bc))

## v0.35.0 (2025-11-21)

### Bug Fixes

- **client**: Add SalesOrderFulfillmentRow to SerialNumberResourceType enum
  ([`701580e`](https://github.com/dougborg/katana-openapi-client/commit/701580eadd9acb56cf03a83138f6d257d1b21bb0))

### Features

- **mcp**: Update client dependency to v0.34.0
  ([`42be36e`](https://github.com/dougborg/katana-openapi-client/commit/42be36e94d75b521970de8e231f9166fb9897457))

## v0.34.0 (2025-11-18)

### Bug Fixes

- **ci**: Ignore site/ directory in yamllint config
  ([`2aed19f`](https://github.com/dougborg/katana-openapi-client/commit/2aed19f7b422f1451bd617671fa439fc1ddbe25b))

- **ci**: Ignore site/ directory in yamllint config
  ([`6aa1e54`](https://github.com/dougborg/katana-openapi-client/commit/6aa1e542dee736107db1eef8c0c0d46bfbaf836e))

### Chores

- **actions)(deps**: Bump python-semantic-release/python-semantic-release
  ([#176](https://github.com/dougborg/katana-openapi-client/pull/176),
  [`c8b3a7d`](https://github.com/dougborg/katana-openapi-client/commit/c8b3a7ded982974ac54b9658a12c9a1587ac3f86))

- **release**: Mcp v0.17.0
  ([`a995d0b`](https://github.com/dougborg/katana-openapi-client/commit/a995d0b0a2d42afbfb937323a637febff5909cda))

### Documentation

- **mcp**: Add ADRs for tool interface pattern and automated documentation
  ([`4f5425f`](https://github.com/dougborg/katana-openapi-client/commit/4f5425f8686b3685e1779762c1559cb09948daac))

### Features

- **client**: Enhance invalid_type validation error messages
  ([`5df0d0f`](https://github.com/dougborg/katana-openapi-client/commit/5df0d0f6d0789251e31011db5b587a91c8ca58fb))

- **client**: Enhance min/max validation error messages
  ([`574cd44`](https://github.com/dougborg/katana-openapi-client/commit/574cd44d75c18c76faa2177ac68d01fba2051c52))

- **client**: Enhance pattern validation error messages
  ([`491cf3c`](https://github.com/dougborg/katana-openapi-client/commit/491cf3c791c8788795bdcd105ec887e05c42c0b8))

- **client**: Enhance required field validation error messages
  ([`f41e25f`](https://github.com/dougborg/katana-openapi-client/commit/f41e25fb30539d0fb735ed61e5ddc3805ebddddc))

- **client**: Enhance too_small/too_big validation error messages
  ([`85a4543`](https://github.com/dougborg/katana-openapi-client/commit/85a45433e1ed2863d068e7f6b6fa28f93d8e3caa))

- **client**: Enhance unrecognized_keys validation error messages
  ([`9a64a55`](https://github.com/dougborg/katana-openapi-client/commit/9a64a55f25533c50b0ae00bb889c465c334fbd6a))

- **client**: Improve enum validation error messages
  ([`f86c5ff`](https://github.com/dougborg/katana-openapi-client/commit/f86c5ff095993dd19be78678a64c7028cf0f20af))

- **mcp**: Update client dependency to v0.33.0
  ([#181](https://github.com/dougborg/katana-openapi-client/pull/181),
  [`5aa64dc`](https://github.com/dougborg/katana-openapi-client/commit/5aa64dc5e58a4b05c2953f99a018a7af212d4422))

### Refactoring

- **client**: Use discriminated unions for validation errors
  ([`ce67506`](https://github.com/dougborg/katana-openapi-client/commit/ce67506e90625dd5cc16afba117c03e64b795b13))

## v0.33.0 (2025-11-14)

### Chores

- Configure yamllint with 120 char line length
  ([#173](https://github.com/dougborg/katana-openapi-client/pull/173),
  [`fe49bd2`](https://github.com/dougborg/katana-openapi-client/commit/fe49bd2b51bd8480f5994db38e1a15a88097c5d6))

- Consolidate config and cleanup documentation
  ([`36a2b0f`](https://github.com/dougborg/katana-openapi-client/commit/36a2b0f87151eb6c2d74c733a57226a411a6d0b5))

- **actions)(deps**: Bump the github-actions group with 2 updates
  ([`7ca453a`](https://github.com/dougborg/katana-openapi-client/commit/7ca453ac54954b0ea8a45279749356ae83e7d98a))

- **release**: Mcp v0.10.0
  ([`14f1835`](https://github.com/dougborg/katana-openapi-client/commit/14f183557e2dc172ed952e8da1a7e016934e12a6))

- **release**: Mcp v0.11.0
  ([`74d0dd2`](https://github.com/dougborg/katana-openapi-client/commit/74d0dd2e7cd882606cce67f2460dceb8507fa352))

- **release**: Mcp v0.12.0
  ([`1e54f96`](https://github.com/dougborg/katana-openapi-client/commit/1e54f96a9790e272265a67d41aa5f3d99c4e40bf))

- **release**: Mcp v0.13.0
  ([`911b0ef`](https://github.com/dougborg/katana-openapi-client/commit/911b0efdd5e22d5ddde46781576f8ab28d62a82d))

- **release**: Mcp v0.14.0
  ([`8f33a95`](https://github.com/dougborg/katana-openapi-client/commit/8f33a959b011eaa037f10b9323ebed51827a292f))

- **release**: Mcp v0.15.0
  ([`5310d08`](https://github.com/dougborg/katana-openapi-client/commit/5310d08626e8fad4572e139f95566381c4cf45dd))

- **release**: Mcp v0.16.0
  ([`65b09a0`](https://github.com/dougborg/katana-openapi-client/commit/65b09a0d0c39c81505581e42f1fded9ad426c34a))

- **release**: Mcp v0.9.0
  ([`2ec7337`](https://github.com/dougborg/katana-openapi-client/commit/2ec73379b775646bad3bd4adc2bd39b5cbfeb4fc))

### Documentation

- **client**: Add pending changelog entry for stock adjustment rows
  ([#178](https://github.com/dougborg/katana-openapi-client/pull/178),
  [`6ef834e`](https://github.com/dougborg/katana-openapi-client/commit/6ef834ebfd765e0ad982a5db6561fa7a68823b16))

- **mcp**: Add comprehensive documentation for observability decorators to LOGGING.md
  ([#172](https://github.com/dougborg/katana-openapi-client/pull/172),
  [`c1c2a48`](https://github.com/dougborg/katana-openapi-client/commit/c1c2a48011b2ba8319f40989556de8bacaa207de))

- **mcp**: Add tools.json generator documentation to docker.md
  ([#175](https://github.com/dougborg/katana-openapi-client/pull/175),
  [`9c2c6f2`](https://github.com/dougborg/katana-openapi-client/commit/9c2c6f27e55424c67e1920df06902f29c5957a7d))

### Features

- **client**: Add stock adjustment rows, reason field, and regen script improvements
  (#178) ([#179](https://github.com/dougborg/katana-openapi-client/pull/179),
  [`c57c5f3`](https://github.com/dougborg/katana-openapi-client/commit/c57c5f39682fe4d2a19af227070565c2c978452c))

- **mcp**: Add @observe_tool and @observe_service decorators with tests
  ([#172](https://github.com/dougborg/katana-openapi-client/pull/172),
  [`c1c2a48`](https://github.com/dougborg/katana-openapi-client/commit/c1c2a48011b2ba8319f40989556de8bacaa207de))

- **mcp**: Add FastMCP elicitation pattern to destructive operations
  ([#173](https://github.com/dougborg/katana-openapi-client/pull/173),
  [`fe49bd2`](https://github.com/dougborg/katana-openapi-client/commit/fe49bd2b51bd8480f5994db38e1a15a88097c5d6))

- **mcp**: Add observability decorators for automatic tool instrumentation
  ([#172](https://github.com/dougborg/katana-openapi-client/pull/172),
  [`c1c2a48`](https://github.com/dougborg/katana-openapi-client/commit/c1c2a48011b2ba8319f40989556de8bacaa207de))

- **mcp**: Add resources foundation and first inventory/items resource
  ([`c0b5459`](https://github.com/dougborg/katana-openapi-client/commit/c0b54593e54c268cd9e170af2b6cfdb0cd56c2d2))

- **mcp**: Add tools.json generator for Docker MCP Registry submission
  ([#175](https://github.com/dougborg/katana-openapi-client/pull/175),
  [`9c2c6f2`](https://github.com/dougborg/katana-openapi-client/commit/9c2c6f27e55424c67e1920df06902f29c5957a7d))

- **mcp**: Add tools.json generator script with comprehensive tests
  ([#175](https://github.com/dougborg/katana-openapi-client/pull/175),
  [`9c2c6f2`](https://github.com/dougborg/katana-openapi-client/commit/9c2c6f27e55424c67e1920df06902f29c5957a7d))

- **mcp**: Apply @observe_tool decorator to all foundation tools
  ([#172](https://github.com/dougborg/katana-openapi-client/pull/172),
  [`c1c2a48`](https://github.com/dougborg/katana-openapi-client/commit/c1c2a48011b2ba8319f40989556de8bacaa207de))

- **mcp**: Apply Unpack decorator to all remaining MCP tools
  ([`ef59809`](https://github.com/dougborg/katana-openapi-client/commit/ef5980912bb2afa40b1b2d41a7c45639a33ba237))

- **mcp**: Implement FastMCP elicitation pattern for destructive operations
  ([#173](https://github.com/dougborg/katana-openapi-client/pull/173),
  [`fe49bd2`](https://github.com/dougborg/katana-openapi-client/commit/fe49bd2b51bd8480f5994db38e1a15a88097c5d6))

- **mcp**: Implement remaining MCP resources for inventory and orders
  ([`062fedd`](https://github.com/dougborg/katana-openapi-client/commit/062feddcd2a2fc789e35b8c5ba1cc0d1c836cfb3))

- **mcp**: Implement Unpack decorator for flat tool parameters
  ([`862ce79`](https://github.com/dougborg/katana-openapi-client/commit/862ce79f10c244c3b711487cccbed7ccf744d27f))

- **mcp**: Implement Unpack decorator for flat tool parameters
  ([`a025ca9`](https://github.com/dougborg/katana-openapi-client/commit/a025ca98e0f8d279da03471800b7ebeb8da20ec7))

- **mcp**: Update client dependency to v0.32.0
  ([#158](https://github.com/dougborg/katana-openapi-client/pull/158),
  [`ff8f2be`](https://github.com/dougborg/katana-openapi-client/commit/ff8f2be1ab84d5cabeffa41b32e425a7ad0dc41f))

### Refactoring

- **mcp**: Extract ConfirmationSchema to shared module
  ([#173](https://github.com/dougborg/katana-openapi-client/pull/173),
  [`fe49bd2`](https://github.com/dougborg/katana-openapi-client/commit/fe49bd2b51bd8480f5994db38e1a15a88097c5d6))

### Testing

- **mcp**: Add test reproducing Claude Code parameter passing issue
  ([`05f643e`](https://github.com/dougborg/katana-openapi-client/commit/05f643eabf2880c3577259baf4b81a9e4433ce4f))

- **mcp**: Fix integration tests with pytest-asyncio fixture decorator
  ([`36db39d`](https://github.com/dougborg/katana-openapi-client/commit/36db39d548f4573a1714d56a99dff3355b5f0a96))

- **mcp**: Fix wrapper test to call implementation directly
  ([#173](https://github.com/dougborg/katana-openapi-client/pull/173),
  [`fe49bd2`](https://github.com/dougborg/katana-openapi-client/commit/fe49bd2b51bd8480f5994db38e1a15a88097c5d6))

## v0.32.0 (2025-11-08)

### Bug Fixes

- **client**: Allow empty SKUs and support service variant type
  ([`1baae73`](https://github.com/dougborg/katana-openapi-client/commit/1baae73535c8db1b95547ff4a43fce12992a23a2))

- **copilot**: Repair YAML frontmatter in agent definition files
  ([`1c6fc85`](https://github.com/dougborg/katana-openapi-client/commit/1c6fc85abad148235639fc2e1c95920f4948c642))

- **mcp**: Add .client attribute to mock context in test_orders
  ([#157](https://github.com/dougborg/katana-openapi-client/pull/157),
  [`621925c`](https://github.com/dougborg/katana-openapi-client/commit/621925c23baa0194b94f8bc06c14160a09032394))

- **mcp**: Remove unnecessary @pytest.mark.asyncio decorators from sync validation tests
  ([#153](https://github.com/dougborg/katana-openapi-client/pull/153),
  [`80da12c`](https://github.com/dougborg/katana-openapi-client/commit/80da12cd1129e2d571acde48f9055343003acb29))

- **mcp**: Remove unused ManufacturingOrderStatus import
  ([#157](https://github.com/dougborg/katana-openapi-client/pull/157),
  [`621925c`](https://github.com/dougborg/katana-openapi-client/commit/621925c23baa0194b94f8bc06c14160a09032394))

### Chores

- Migrate from mypy to ty for type checking
  ([#137](https://github.com/dougborg/katana-openapi-client/pull/137),
  [`87ad793`](https://github.com/dougborg/katana-openapi-client/commit/87ad7936bd31116d8326c2ea9de4b412e48b3d6e))

- Update Python version support to 3.12, 3.13, and 3.14
  ([#147](https://github.com/dougborg/katana-openapi-client/pull/147),
  [`7183e55`](https://github.com/dougborg/katana-openapi-client/commit/7183e550f8efa0b2defc862fe8cf3494fb0493b6))

- **copilot**: Remove duplicate agent files with .md extension
  ([`a0e27e1`](https://github.com/dougborg/katana-openapi-client/commit/a0e27e197c191bed55aafdf5a67b48205dc16b61))

- **release**: Mcp v0.7.0
  ([`c5e5dc2`](https://github.com/dougborg/katana-openapi-client/commit/c5e5dc2a5ff92d17fc2987d35b87817c45839c26))

- **release**: Mcp v0.8.0
  ([`e7a3c31`](https://github.com/dougborg/katana-openapi-client/commit/e7a3c31c3b777bd06cbf1917aee2777eb9824910))

### Continuous Integration

- Fix required status checks for docs-only PRs
  ([#149](https://github.com/dougborg/katana-openapi-client/pull/149),
  [`d366560`](https://github.com/dougborg/katana-openapi-client/commit/d3665606fe2bd29bde4189f8ed6ffb3124f8b336))

- Fix required status checks for docs-only PRs
  ([#148](https://github.com/dougborg/katana-openapi-client/pull/148),
  [`902b62a`](https://github.com/dougborg/katana-openapi-client/commit/902b62aa739bec456d1570b447a74673db1d703e))

### Documentation

- Add ADR-014 for GitHub Copilot custom agents architecture
  ([#149](https://github.com/dougborg/katana-openapi-client/pull/149),
  [`d366560`](https://github.com/dougborg/katana-openapi-client/commit/d3665606fe2bd29bde4189f8ed6ffb3124f8b336))

- Add ADR-014 for GitHub Copilot custom agents architecture
  ([#148](https://github.com/dougborg/katana-openapi-client/pull/148),
  [`902b62a`](https://github.com/dougborg/katana-openapi-client/commit/902b62aa739bec456d1570b447a74673db1d703e))

- Reorganize to module-local structure
  ([#143](https://github.com/dougborg/katana-openapi-client/pull/143),
  [`5646bee`](https://github.com/dougborg/katana-openapi-client/commit/5646bee800eb6bc945804ab4476a14cb325fbb0f))

- **mcp**: Add ADR-014 and MCP v0.1.0 release checklist
  ([#149](https://github.com/dougborg/katana-openapi-client/pull/149),
  [`d366560`](https://github.com/dougborg/katana-openapi-client/commit/d3665606fe2bd29bde4189f8ed6ffb3124f8b336))

- **mcp**: Create comprehensive v0.1.0 release checklist
  ([#149](https://github.com/dougborg/katana-openapi-client/pull/149),
  [`d366560`](https://github.com/dougborg/katana-openapi-client/commit/d3665606fe2bd29bde4189f8ed6ffb3124f8b336))

- **mcp**: Fix tool name in README (search_items not search_products)
  ([#151](https://github.com/dougborg/katana-openapi-client/pull/151),
  [`01b410e`](https://github.com/dougborg/katana-openapi-client/commit/01b410e8b845468511a2c313ae08ab6aa863adf8))

- **mcp**: Include stock_level field in search_items response example
  ([#151](https://github.com/dougborg/katana-openapi-client/pull/151),
  [`01b410e`](https://github.com/dougborg/katana-openapi-client/commit/01b410e8b845468511a2c313ae08ab6aa863adf8))

### Features

- **mcp**: Add create_product and create_material catalog tools
  ([#153](https://github.com/dougborg/katana-openapi-client/pull/153),
  [`80da12c`](https://github.com/dougborg/katana-openapi-client/commit/80da12cd1129e2d571acde48f9055343003acb29))

- **mcp**: Add dedicated create_product and create_material catalog management tools
  ([#153](https://github.com/dougborg/katana-openapi-client/pull/153),
  [`80da12c`](https://github.com/dougborg/katana-openapi-client/commit/80da12cd1129e2d571acde48f9055343003acb29))

- **mcp**: Add get_variant_details tool for fetching variant info by SKU
  ([#152](https://github.com/dougborg/katana-openapi-client/pull/152),
  [`8246b95`](https://github.com/dougborg/katana-openapi-client/commit/8246b955d7f389628f09bbbf6ff052b5bb4d998b))

- **mcp**: Implement create_manufacturing_order tool
  ([#156](https://github.com/dougborg/katana-openapi-client/pull/156),
  [`bc78244`](https://github.com/dougborg/katana-openapi-client/commit/bc782442b00cf6ae35512009e5f0c3b4bd6ec04d))

- **mcp**: Implement create_manufacturing_order tool for issue #44
  ([#156](https://github.com/dougborg/katana-openapi-client/pull/156),
  [`bc78244`](https://github.com/dougborg/katana-openapi-client/commit/bc782442b00cf6ae35512009e5f0c3b4bd6ec04d))

- **mcp**: Implement fulfill_order tool for manufacturing and sales orders
  ([#157](https://github.com/dougborg/katana-openapi-client/pull/157),
  [`621925c`](https://github.com/dougborg/katana-openapi-client/commit/621925c23baa0194b94f8bc06c14160a09032394))

- **mcp**: Implement verify_order_document tool with comprehensive tests for #86
  ([#154](https://github.com/dougborg/katana-openapi-client/pull/154),
  [`a1671b5`](https://github.com/dougborg/katana-openapi-client/commit/a1671b569485515604e68fa2bbd5316a80b48903))

- **mcp**: Implement verify_order_document tool with structured response models
  ([#154](https://github.com/dougborg/katana-openapi-client/pull/154),
  [`a1671b5`](https://github.com/dougborg/katana-openapi-client/commit/a1671b569485515604e68fa2bbd5316a80b48903))

- **mcp**: Update client dependency to v0.31.0
  ([#141](https://github.com/dougborg/katana-openapi-client/pull/141),
  [`7bf1c59`](https://github.com/dougborg/katana-openapi-client/commit/7bf1c591abc1fc26200f5878a1ae8e73463596b7))

### Refactoring

- **copilot**: Adopt official GitHub Copilot agent structure
  ([#146](https://github.com/dougborg/katana-openapi-client/pull/146),
  [`0523a50`](https://github.com/dougborg/katana-openapi-client/commit/0523a5019616f8c8de42598cd46e73fc2f33a896))

- **copilot**: Adopt official GitHub Copilot agent structure
  ([#145](https://github.com/dougborg/katana-openapi-client/pull/145),
  [`e0311c5`](https://github.com/dougborg/katana-openapi-client/commit/e0311c5e7178858b0017b829d0694f5abaf98b7e))

- **copilot**: Migrate agents to awesome-copilot three-tier architecture
  ([#145](https://github.com/dougborg/katana-openapi-client/pull/145),
  [`e0311c5`](https://github.com/dougborg/katana-openapi-client/commit/e0311c5e7178858b0017b829d0694f5abaf98b7e))

- **mcp**: Address code review feedback for verify_order_document
  ([#154](https://github.com/dougborg/katana-openapi-client/pull/154),
  [`a1671b5`](https://github.com/dougborg/katana-openapi-client/commit/a1671b569485515604e68fa2bbd5316a80b48903))

- **mcp**: Address PR review feedback for manufacturing orders
  ([#156](https://github.com/dougborg/katana-openapi-client/pull/156),
  [`bc78244`](https://github.com/dougborg/katana-openapi-client/commit/bc782442b00cf6ae35512009e5f0c3b4bd6ec04d))

- **mcp**: Move create_mock_context to shared conftest
  ([#155](https://github.com/dougborg/katana-openapi-client/pull/155),
  [`156727a`](https://github.com/dougborg/katana-openapi-client/commit/156727a20a8c62dcf25b611683a590d74494c3c4))

### Testing

- **mcp**: Add API payload and response structure validation tests
  ([#155](https://github.com/dougborg/katana-openapi-client/pull/155),
  [`156727a`](https://github.com/dougborg/katana-openapi-client/commit/156727a20a8c62dcf25b611683a590d74494c3c4))

- **mcp**: Add comprehensive edge case tests for receive_purchase_order
  ([#155](https://github.com/dougborg/katana-openapi-client/pull/155),
  [`156727a`](https://github.com/dougborg/katana-openapi-client/commit/156727a20a8c62dcf25b611683a590d74494c3c4))

- **mcp**: Add comprehensive integration tests for inventory tools
  ([#150](https://github.com/dougborg/katana-openapi-client/pull/150),
  [`b84b05b`](https://github.com/dougborg/katana-openapi-client/commit/b84b05b7a225faa7dc21933eb6ddb5b8994cec1b))

- **mcp**: Add comprehensive test coverage for receive_purchase_order tool
  ([#155](https://github.com/dougborg/katana-openapi-client/pull/155),
  [`156727a`](https://github.com/dougborg/katana-openapi-client/commit/156727a20a8c62dcf25b611683a590d74494c3c4))

- **mcp**: Add comprehensive unit tests for receive_purchase_order tool
  ([#155](https://github.com/dougborg/katana-openapi-client/pull/155),
  [`156727a`](https://github.com/dougborg/katana-openapi-client/commit/156727a20a8c62dcf25b611683a590d74494c3c4))

- **mcp**: Address PR review feedback for integration tests
  ([#150](https://github.com/dougborg/katana-openapi-client/pull/150),
  [`b84b05b`](https://github.com/dougborg/katana-openapi-client/commit/b84b05b7a225faa7dc21933eb6ddb5b8994cec1b))

## v0.31.0 (2025-11-05)

### Bug Fixes

- **ci**: Convert pre-commit to local hooks via uv
  ([#135](https://github.com/dougborg/katana-openapi-client/pull/135),
  [`12d86d6`](https://github.com/dougborg/katana-openapi-client/commit/12d86d6e3b14d1251822f4c6bf96545dde8c8240))

- **copilot**: Address review comments on custom agent definitions
  ([#139](https://github.com/dougborg/katana-openapi-client/pull/139),
  [`b1558f4`](https://github.com/dougborg/katana-openapi-client/commit/b1558f4e0807aba89b8e58bf5ad139cefc6e59a4))

- **mcp**: Address PR review comments on purchase order tools
  ([#125](https://github.com/dougborg/katana-openapi-client/pull/125),
  [`5f1351b`](https://github.com/dougborg/katana-openapi-client/commit/5f1351b5f38a4df4d8148a30962f2aadeaa312db))

- **test**: Use .test TLD for mock URLs to avoid DNS lookups
  ([#140](https://github.com/dougborg/katana-openapi-client/pull/140),
  [`5e78ef8`](https://github.com/dougborg/katana-openapi-client/commit/5e78ef890a79c44756093d1ea357335f2df95290))

### Chores

- **actions)(deps**: Bump the github-actions group with 6 updates
  ([#130](https://github.com/dougborg/katana-openapi-client/pull/130),
  [`4da0481`](https://github.com/dougborg/katana-openapi-client/commit/4da0481da939e9d277a187ce3dd207d2c1ed8d67))

- **docker)(deps**: Bump python in /katana_mcp_server
  ([#129](https://github.com/dougborg/katana-openapi-client/pull/129),
  [`286b536`](https://github.com/dougborg/katana-openapi-client/commit/286b536efa6f1a49d44e6e8643a54c504804e4b0))

- **release**: Mcp v0.6.0
  ([`ec773ed`](https://github.com/dougborg/katana-openapi-client/commit/ec773ed50e0fab2104b476d3819b9ac93b5a3216))

### Documentation

- Initial plan for custom GitHub Copilot agents
  ([#139](https://github.com/dougborg/katana-openapi-client/pull/139),
  [`b1558f4`](https://github.com/dougborg/katana-openapi-client/commit/b1558f4e0807aba89b8e58bf5ad139cefc6e59a4))

- Update workflows README with automated dependency management
  ([#122](https://github.com/dougborg/katana-openapi-client/pull/122),
  [`30510f5`](https://github.com/dougborg/katana-openapi-client/commit/30510f597e14d89b10c951af28de12963aed3976))

### Features

- Add automated MCP dependency update workflow
  ([#122](https://github.com/dougborg/katana-openapi-client/pull/122),
  [`30510f5`](https://github.com/dougborg/katana-openapi-client/commit/30510f597e14d89b10c951af28de12963aed3976))

- Add custom GitHub Copilot agents for specialized tasks
  ([#139](https://github.com/dougborg/katana-openapi-client/pull/139),
  [`b1558f4`](https://github.com/dougborg/katana-openapi-client/commit/b1558f4e0807aba89b8e58bf5ad139cefc6e59a4))

- Define custom GitHub Copilot agents for specialized development tasks
  ([#139](https://github.com/dougborg/katana-openapi-client/pull/139),
  [`b1558f4`](https://github.com/dougborg/katana-openapi-client/commit/b1558f4e0807aba89b8e58bf5ad139cefc6e59a4))

- **mcp**: Add structured logging with performance metrics
  ([`dbba41e`](https://github.com/dougborg/katana-openapi-client/commit/dbba41eb3712c83b9d1540f64b1fd416227f317d))

- **mcp**: Add stub purchase order foundation tools
  ([#125](https://github.com/dougborg/katana-openapi-client/pull/125),
  [`5f1351b`](https://github.com/dougborg/katana-openapi-client/commit/5f1351b5f38a4df4d8148a30962f2aadeaa312db))

- **mcp**: Automate MCP dependency updates on client releases
  ([#122](https://github.com/dougborg/katana-openapi-client/pull/122),
  [`30510f5`](https://github.com/dougborg/katana-openapi-client/commit/30510f597e14d89b10c951af28de12963aed3976))

- **mcp**: Implement create_purchase_order with real API integration
  ([#125](https://github.com/dougborg/katana-openapi-client/pull/125),
  [`5f1351b`](https://github.com/dougborg/katana-openapi-client/commit/5f1351b5f38a4df4d8148a30962f2aadeaa312db))

- **mcp**: Implement purchase order foundation tools
  ([#125](https://github.com/dougborg/katana-openapi-client/pull/125),
  [`5f1351b`](https://github.com/dougborg/katana-openapi-client/commit/5f1351b5f38a4df4d8148a30962f2aadeaa312db))

- **mcp**: Implement receive_purchase_order with real API integration
  ([#125](https://github.com/dougborg/katana-openapi-client/pull/125),
  [`5f1351b`](https://github.com/dougborg/katana-openapi-client/commit/5f1351b5f38a4df4d8148a30962f2aadeaa312db))

- **mcp**: Implement verify_order_document tool
  ([#125](https://github.com/dougborg/katana-openapi-client/pull/125),
  [`5f1351b`](https://github.com/dougborg/katana-openapi-client/commit/5f1351b5f38a4df4d8148a30962f2aadeaa312db))

### Performance Improvements

- **mcp**: Optimize variant fetching with API-level ID filtering
  ([#125](https://github.com/dougborg/katana-openapi-client/pull/125),
  [`5f1351b`](https://github.com/dougborg/katana-openapi-client/commit/5f1351b5f38a4df4d8148a30962f2aadeaa312db))

### Testing

- **mcp**: Add comprehensive logging tests and documentation
  ([`dbba41e`](https://github.com/dougborg/katana-openapi-client/commit/dbba41eb3712c83b9d1540f64b1fd416227f317d))

## v0.30.0 (2025-11-05)

### Chores

- Clean up trigger file
  ([#121](https://github.com/dougborg/katana-openapi-client/pull/121),
  [`b5346bc`](https://github.com/dougborg/katana-openapi-client/commit/b5346bc0f02164c8cdcb00b5d7dd7797412bcbe4))

- Trigger push of README badge changes
  ([#121](https://github.com/dougborg/katana-openapi-client/pull/121),
  [`b5346bc`](https://github.com/dougborg/katana-openapi-client/commit/b5346bc0f02164c8cdcb00b5d7dd7797412bcbe4))

- **infra**: Add Dependabot configuration for GitHub Actions and Docker updates
  ([#119](https://github.com/dougborg/katana-openapi-client/pull/119),
  [`555122b`](https://github.com/dougborg/katana-openapi-client/commit/555122bbbf45675c0aef0acba6c26872c1b4670b))

- **infra**: Add Dependabot configuration for weekly dependency updates
  ([#119](https://github.com/dougborg/katana-openapi-client/pull/119),
  [`555122b`](https://github.com/dougborg/katana-openapi-client/commit/555122bbbf45675c0aef0acba6c26872c1b4670b))

- **infra**: Remove Python pip config from Dependabot (uv incompatibility)
  ([#119](https://github.com/dougborg/katana-openapi-client/pull/119),
  [`555122b`](https://github.com/dougborg/katana-openapi-client/commit/555122bbbf45675c0aef0acba6c26872c1b4670b))

### Continuous Integration

- Add path filters to skip CI for docs-only changes
  ([#123](https://github.com/dougborg/katana-openapi-client/pull/123),
  [`722a6f8`](https://github.com/dougborg/katana-openapi-client/commit/722a6f869df737857261c936990a1f5b76ae5b2a))

- Add path filters to skip unnecessary CI runs
  ([#123](https://github.com/dougborg/katana-openapi-client/pull/123),
  [`722a6f8`](https://github.com/dougborg/katana-openapi-client/commit/722a6f869df737857261c936990a1f5b76ae5b2a))

### Documentation

- Add CI, coverage, and docs status badges to README
  ([#121](https://github.com/dougborg/katana-openapi-client/pull/121),
  [`b5346bc`](https://github.com/dougborg/katana-openapi-client/commit/b5346bc0f02164c8cdcb00b5d7dd7797412bcbe4))

- Add CI, coverage, docs, and security status badges to README
  ([#121](https://github.com/dougborg/katana-openapi-client/pull/121),
  [`b5346bc`](https://github.com/dougborg/katana-openapi-client/commit/b5346bc0f02164c8cdcb00b5d7dd7797412bcbe4))

- **client**: Fix inline comment to reflect actual priority order
  ([#117](https://github.com/dougborg/katana-openapi-client/pull/117),
  [`509a010`](https://github.com/dougborg/katana-openapi-client/commit/509a010a52d944e7f819d5ce366b00346b9ddf86))

### Features

- **client**: Add netrc support for API authentication
  ([#117](https://github.com/dougborg/katana-openapi-client/pull/117),
  [`509a010`](https://github.com/dougborg/katana-openapi-client/commit/509a010a52d944e7f819d5ce366b00346b9ddf86))

- **client**: Add ~/.netrc support for API authentication
  ([#117](https://github.com/dougborg/katana-openapi-client/pull/117),
  [`509a010`](https://github.com/dougborg/katana-openapi-client/commit/509a010a52d944e7f819d5ce366b00346b9ddf86))

### Refactoring

- **client**: Address code review feedback
  ([#117](https://github.com/dougborg/katana-openapi-client/pull/117),
  [`509a010`](https://github.com/dougborg/katana-openapi-client/commit/509a010a52d944e7f819d5ce366b00346b9ddf86))

- **client**: Improve hostname extraction robustness and type safety
  ([#117](https://github.com/dougborg/katana-openapi-client/pull/117),
  [`509a010`](https://github.com/dougborg/katana-openapi-client/commit/509a010a52d944e7f819d5ce366b00346b9ddf86))

- **client**: Improve netrc hostname extraction robustness
  ([#117](https://github.com/dougborg/katana-openapi-client/pull/117),
  [`509a010`](https://github.com/dougborg/katana-openapi-client/commit/509a010a52d944e7f819d5ce366b00346b9ddf86))

## v0.29.0 (2025-11-05)

### Bug Fixes

- **client**: Correct BatchCreateBomRowsRequest field name from bom_rows to data
  ([#115](https://github.com/dougborg/katana-openapi-client/pull/115),
  [`5bb9918`](https://github.com/dougborg/katana-openapi-client/commit/5bb9918095c33f06b2502f944b7ae1df708c9dcc))

### Chores

- **release**: Mcp v0.4.0
  ([`c3594e4`](https://github.com/dougborg/katana-openapi-client/commit/c3594e404b660ccd6e06b16dcc133ccae91d5866))

- **release**: Mcp v0.5.0
  ([`0c67647`](https://github.com/dougborg/katana-openapi-client/commit/0c67647906e83400e8df2767547892ba1a6a9736))

### Documentation

- Fix 66 OpenAPI spec example warnings
  ([#116](https://github.com/dougborg/katana-openapi-client/pull/116),
  [`d20997c`](https://github.com/dougborg/katana-openapi-client/commit/d20997c6a8287659ca1ccc7ed4f487e4bd1816fb))

### Features

- **mcp**: Complete unified item CRUD interface
  ([`9c123e3`](https://github.com/dougborg/katana-openapi-client/commit/9c123e3619b9e872d4ce8aa360d11ec6779002f1))

- **mcp**: Migrate to StockTrim architecture with unified item creation
  ([`8645d9d`](https://github.com/dougborg/katana-openapi-client/commit/8645d9dd15dc302b2f64938d8b6f61ce390e13d4))

## v0.28.0 (2025-11-05)

### Bug Fixes

- Address additional review feedback on PR #78
  ([#78](https://github.com/dougborg/katana-openapi-client/pull/78),
  [`0547845`](https://github.com/dougborg/katana-openapi-client/commit/054784522fd46954ca689d886cbc4bf33913d2db))

- Address code review feedback from PR #78
  ([#78](https://github.com/dougborg/katana-openapi-client/pull/78),
  [`0547845`](https://github.com/dougborg/katana-openapi-client/commit/054784522fd46954ca689d886cbc4bf33913d2db))

- Correct Product converter to use archived_at instead of deleted_at
  ([#78](https://github.com/dougborg/katana-openapi-client/pull/78),
  [`0547845`](https://github.com/dougborg/katana-openapi-client/commit/054784522fd46954ca689d886cbc4bf33913d2db))

- Remove reference to non-existent variant.product_or_material_name field
  ([#78](https://github.com/dougborg/katana-openapi-client/pull/78),
  [`0547845`](https://github.com/dougborg/katana-openapi-client/commit/054784522fd46954ca689d886cbc4bf33913d2db))

- Update devcontainer and deployment docs with corrected MCP doc references
  ([#78](https://github.com/dougborg/katana-openapi-client/pull/78),
  [`0547845`](https://github.com/dougborg/katana-openapi-client/commit/054784522fd46954ca689d886cbc4bf33913d2db))

- Update MCP issue creation scripts to reference new documentation paths
  ([#78](https://github.com/dougborg/katana-openapi-client/pull/78),
  [`0547845`](https://github.com/dougborg/katana-openapi-client/commit/054784522fd46954ca689d886cbc4bf33913d2db))

### Chores

- **client**: Regenerate client after removing product_or_material_name field
  ([`fa53c7c`](https://github.com/dougborg/katana-openapi-client/commit/fa53c7cedacabe3934c950291acd5fc104fbc898))

### Continuous Integration

- Prevent race conditions in release workflow with proper concurrency control
  ([#109](https://github.com/dougborg/katana-openapi-client/pull/109),
  [`4fc496f`](https://github.com/dougborg/katana-openapi-client/commit/4fc496f06403bc09e094b94513974986b1abb3b9))

### Documentation

- Create AGENT_WORKFLOW.md for AI agent development guide
  ([#78](https://github.com/dougborg/katana-openapi-client/pull/78),
  [`0547845`](https://github.com/dougborg/katana-openapi-client/commit/054784522fd46954ca689d886cbc4bf33913d2db))

- Enhance agent coordination guidelines with detailed patterns
  ([#110](https://github.com/dougborg/katana-openapi-client/pull/110),
  [`9478f42`](https://github.com/dougborg/katana-openapi-client/commit/9478f4238b77b79305337393fb1d638577e1e7fd))

- Update copilot-instructions.md and CLAUDE.md with uv and validation tiers
  ([#107](https://github.com/dougborg/katana-openapi-client/pull/107),
  [`9d3c383`](https://github.com/dougborg/katana-openapi-client/commit/9d3c3838ce815d53993e3b39b1ee01c567da7531))

- **mcp**: Add StockTrim architecture migration plan
  ([#112](https://github.com/dougborg/katana-openapi-client/pull/112),
  [`8d081e4`](https://github.com/dougborg/katana-openapi-client/commit/8d081e45cae909543e7cd6a1e754a5c9aca0cd60))

- **mcp**: Reorganize MCP documentation and align issues with v0.1.0 plan
  ([#78](https://github.com/dougborg/katana-openapi-client/pull/78),
  [`0547845`](https://github.com/dougborg/katana-openapi-client/commit/054784522fd46954ca689d886cbc4bf33913d2db))

### Features

- **client**: Add Product, Material, Service domain models with helper integration
  ([#78](https://github.com/dougborg/katana-openapi-client/pull/78),
  [`0547845`](https://github.com/dougborg/katana-openapi-client/commit/054784522fd46954ca689d886cbc4bf33913d2db))

- **client**: Add Pydantic domain models for ETL and data processing
  ([#78](https://github.com/dougborg/katana-openapi-client/pull/78),
  [`0547845`](https://github.com/dougborg/katana-openapi-client/commit/054784522fd46954ca689d886cbc4bf33913d2db))

- **client**: Add pytest-xdist for parallel test execution
  ([#111](https://github.com/dougborg/katana-openapi-client/pull/111),
  [`c96bee1`](https://github.com/dougborg/katana-openapi-client/commit/c96bee1e83c214097711d622d74b6add2b1854f3))

- **client+mcp**: Add Pydantic domain models for catalog entities
  ([#78](https://github.com/dougborg/katana-openapi-client/pull/78),
  [`0547845`](https://github.com/dougborg/katana-openapi-client/commit/054784522fd46954ca689d886cbc4bf33913d2db))

## v0.27.0 (2025-10-28)

### Bug Fixes

- Correct incomplete sentence in import comment
  ([#72](https://github.com/dougborg/katana-openapi-client/pull/72),
  [`6d046f2`](https://github.com/dougborg/katana-openapi-client/commit/6d046f239df54d750f8b8a8148e1bbe259e3dd8e))

- **client**: Implement client-side fuzzy search for products
  ([`4fa5907`](https://github.com/dougborg/katana-openapi-client/commit/4fa5907e10a1b3fccc09e33d1bd9f8e7df36a679))

- **client**: Use enum for extend parameter in variant search
  ([`ad36ea9`](https://github.com/dougborg/katana-openapi-client/commit/ad36ea940d06f768cae679b196896c538637ceea))

- **client+mcp**: Handle nested product_or_material object in variant responses
  ([`9dd0251`](https://github.com/dougborg/katana-openapi-client/commit/9dd0251dff9ded3ac05391273c6e4592abda0e23))

- **mcp**: Configure semantic-release to update __init__.py version
  ([#75](https://github.com/dougborg/katana-openapi-client/pull/75),
  [`fd58272`](https://github.com/dougborg/katana-openapi-client/commit/fd58272ef5beb08725b19035c94e854932f08a64))

- **mcp**: Correct context access pattern to use request_context.lifespan_context
  ([#75](https://github.com/dougborg/katana-openapi-client/pull/75),
  [`fd58272`](https://github.com/dougborg/katana-openapi-client/commit/fd58272ef5beb08725b19035c94e854932f08a64))

- **mcp**: Correct semantic-release paths for subdirectory execution
  ([#75](https://github.com/dougborg/katana-openapi-client/pull/75),
  [`fd58272`](https://github.com/dougborg/katana-openapi-client/commit/fd58272ef5beb08725b19035c94e854932f08a64))

- **mcp**: Correct semantic-release paths for subdirectory execution
  ([#74](https://github.com/dougborg/katana-openapi-client/pull/74),
  [`804beee`](https://github.com/dougborg/katana-openapi-client/commit/804beee0843a633a9c6524fd4637fa24b7e4dbd7))

- **mcp**: Extract SKU from first product variant in search results
  ([`d4c8594`](https://github.com/dougborg/katana-openapi-client/commit/d4c8594c3f080ca3795d384f93e35a417a74b9ae))

- **mcp**: Implement proper FastMCP tool registration pattern
  ([`b6aee3c`](https://github.com/dougborg/katana-openapi-client/commit/b6aee3c3ddda9f1998d56d6c60c6865763eb33b4))

- **mcp**: Import tools/resources/prompts modules to register decorators
  ([#70](https://github.com/dougborg/katana-openapi-client/pull/70),
  [`de4eaa2`](https://github.com/dougborg/katana-openapi-client/commit/de4eaa23fe6bc990fff45d2ac92e73ce5211ebe0))

- **mcp**: Register tools with MCP server and release v0.1.0
  ([#70](https://github.com/dougborg/katana-openapi-client/pull/70),
  [`de4eaa2`](https://github.com/dougborg/katana-openapi-client/commit/de4eaa23fe6bc990fff45d2ac92e73ce5211ebe0))

- **mcp**: Use context.server_context instead of context.state
  ([#75](https://github.com/dougborg/katana-openapi-client/pull/75),
  [`fd58272`](https://github.com/dougborg/katana-openapi-client/commit/fd58272ef5beb08725b19035c94e854932f08a64))

- **mcp**: Use full path to uv and add prerequisites documentation
  ([`a95feb3`](https://github.com/dougborg/katana-openapi-client/commit/a95feb36242b14704e9be222a8eccc394311cd1b))

- **spec**: Remove non-existent product_or_material_name field from Variant schema
  ([`b04fa35`](https://github.com/dougborg/katana-openapi-client/commit/b04fa3539f42dbfc057d77f9a65032fed3557fb1))

### Chores

- Add pytest to pre-commit hooks
  ([#75](https://github.com/dougborg/katana-openapi-client/pull/75),
  [`fd58272`](https://github.com/dougborg/katana-openapi-client/commit/fd58272ef5beb08725b19035c94e854932f08a64))

- Remove CLIENT_README.md with Poetry references
  ([#72](https://github.com/dougborg/katana-openapi-client/pull/72),
  [`6d046f2`](https://github.com/dougborg/katana-openapi-client/commit/6d046f239df54d750f8b8a8148e1bbe259e3dd8e))

- Remove generated CLIENT_README.md and stop generating it
  ([#72](https://github.com/dougborg/katana-openapi-client/pull/72),
  [`6d046f2`](https://github.com/dougborg/katana-openapi-client/commit/6d046f239df54d750f8b8a8148e1bbe259e3dd8e))

- Update uv.lock after rebase
  ([`d72fb38`](https://github.com/dougborg/katana-openapi-client/commit/d72fb38ce9a9ee830a2628efef150c9a28a340c3))

- **mcp**: Remove alpha version specifier for v0.1.0 release
  ([#70](https://github.com/dougborg/katana-openapi-client/pull/70),
  [`de4eaa2`](https://github.com/dougborg/katana-openapi-client/commit/de4eaa23fe6bc990fff45d2ac92e73ce5211ebe0))

- **mcp**: Sync version to 0.2.0 in __init__.py
  ([#75](https://github.com/dougborg/katana-openapi-client/pull/75),
  [`fd58272`](https://github.com/dougborg/katana-openapi-client/commit/fd58272ef5beb08725b19035c94e854932f08a64))

- **release**: Mcp v0.2.0
  ([`59989e8`](https://github.com/dougborg/katana-openapi-client/commit/59989e8c4fdb6e421930907eab3e13b29c36068b))

- **release**: Mcp v0.2.1
  ([`f3ce21e`](https://github.com/dougborg/katana-openapi-client/commit/f3ce21e1ad34fd588ebd6f67d2d2647fde74b63e))

- **release**: Mcp v0.3.0
  ([`70d5546`](https://github.com/dougborg/katana-openapi-client/commit/70d554601285edd00802010b4da537a447f0b1ca))

### Documentation

- **mcp**: Improve comment explaining side-effect imports
  ([#71](https://github.com/dougborg/katana-openapi-client/pull/71),
  [`0910a93`](https://github.com/dougborg/katana-openapi-client/commit/0910a93a5f3b10dbb05d912cb5c14184797309fd))

### Features

- **client**: Add variant search caching with relevance ranking
  ([`754a3c8`](https://github.com/dougborg/katana-openapi-client/commit/754a3c89f22b59da2dbcc546089ea6a6135ad5af))

- **client+mcp**: Format variant names to match Katana UI
  ([`78922b9`](https://github.com/dougborg/katana-openapi-client/commit/78922b9d82f054ac16eda8defb0611df5779f9d9))

- **mcp**: Add Docker support and MCP registry submission materials
  ([#73](https://github.com/dougborg/katana-openapi-client/pull/73),
  [`01f1671`](https://github.com/dougborg/katana-openapi-client/commit/01f1671339eb099ea41e60b1bd17ceef4ec1cfb5))

- **mcp**: Add hot-reload development workflow with mcp-hmr
  ([`0bcc707`](https://github.com/dougborg/katana-openapi-client/commit/0bcc707e80651f9313feb5d6a163d287bd7817c6))

### Refactoring

- Address code review feedback
  ([`5112abb`](https://github.com/dougborg/katana-openapi-client/commit/5112abb66327d3f0c893a5a8487b25eebfe4422f))

- Extract variant display name logic to shared utility
  ([`ed33fc8`](https://github.com/dougborg/katana-openapi-client/commit/ed33fc8cf7671983303da9656cc9ee21d04cf7a4))

- Use generated API models instead of dicts in client helpers
  ([#75](https://github.com/dougborg/katana-openapi-client/pull/75),
  [`fd58272`](https://github.com/dougborg/katana-openapi-client/commit/fd58272ef5beb08725b19035c94e854932f08a64))

- **client+mcp**: Search variants instead of products
  ([`d22ac02`](https://github.com/dougborg/katana-openapi-client/commit/d22ac0242553b6d94c1a13bd9db55902784029ba))

- **mcp**: Add error handling, logging, and validation to tools
  ([#75](https://github.com/dougborg/katana-openapi-client/pull/75),
  [`fd58272`](https://github.com/dougborg/katana-openapi-client/commit/fd58272ef5beb08725b19035c94e854932f08a64))

- **mcp**: Use importlib.metadata for version instead of hardcoded string
  ([#75](https://github.com/dougborg/katana-openapi-client/pull/75),
  [`fd58272`](https://github.com/dougborg/katana-openapi-client/commit/fd58272ef5beb08725b19035c94e854932f08a64))

### Testing

- **mcp**: Update inventory tool tests for new interfaces
  ([#75](https://github.com/dougborg/katana-openapi-client/pull/75),
  [`fd58272`](https://github.com/dougborg/katana-openapi-client/commit/fd58272ef5beb08725b19035c94e854932f08a64))

## v0.26.5 (2025-10-27)

### Bug Fixes

- Add Production enum option for InventoryMovement resource_type
  ([#69](https://github.com/dougborg/katana-openapi-client/pull/69),
  [`1962398`](https://github.com/dougborg/katana-openapi-client/commit/196239878edf28e4dd6bc4c75f14f3f2aca45990))

### Chores

- Remove and ignore claude settings file
  ([#69](https://github.com/dougborg/katana-openapi-client/pull/69),
  [`1962398`](https://github.com/dougborg/katana-openapi-client/commit/196239878edf28e4dd6bc4c75f14f3f2aca45990))

## v0.26.4 (2025-10-27)

### Bug Fixes

- Correct MCP artifact upload path
  ([`336fe14`](https://github.com/dougborg/katana-openapi-client/commit/336fe1497c8490e7cefae2d37b5aa9af0968fef4))

## v0.26.3 (2025-10-27)

### Bug Fixes

- Use inputs context instead of github.event.inputs
  ([`78924e5`](https://github.com/dougborg/katana-openapi-client/commit/78924e56e6a6917259992d89129adadaed4ec8f7))

## v0.26.2 (2025-10-27)

### Bug Fixes

- Handle skipped release steps in build conditions
  ([`f565b7a`](https://github.com/dougborg/katana-openapi-client/commit/f565b7ad0a69dd827065985b1f5c1cdad904444d))

## v0.26.1 (2025-10-27)

### Bug Fixes

- Correct boolean comparison in workflow_dispatch conditions
  ([`a4d3c54`](https://github.com/dougborg/katana-openapi-client/commit/a4d3c548a5c5a783ed2e754f09cd4bd67f3df79a))

## v0.26.0 (2025-10-26)

### Bug Fixes

- **mcp**: Correct semantic-release paths for subdirectory execution
  ([`7b4119e`](https://github.com/dougborg/katana-openapi-client/commit/7b4119e2a1ae79ecbc966318ea6d0576d74ac796))

- **mcp**: Use python -m build instead of uv build in semantic-release
  ([`c7071c2`](https://github.com/dougborg/katana-openapi-client/commit/c7071c2d62abe6fb23fad9d4965912501b320419))

- **mcp**: Use same build_command pattern as client - format changelog only
  ([`7603014`](https://github.com/dougborg/katana-openapi-client/commit/760301487546c0e5e4b41fc8d3e97a4519407f0a))

### Chores

- Remove duplicate Release MCP Server workflow
  ([`314c591`](https://github.com/dougborg/katana-openapi-client/commit/314c5917c0dddc5b4a13b77422658ab60c5b0c94))

- **release**: Mcp v0.1.0
  ([`93e2583`](https://github.com/dougborg/katana-openapi-client/commit/93e2583498913d256ded067afab7bc60ebe3c29a))

### Documentation

- Add comprehensive monorepo semantic-release guide
  ([#68](https://github.com/dougborg/katana-openapi-client/pull/68),
  [`db1eef3`](https://github.com/dougborg/katana-openapi-client/commit/db1eef33f542e5d0d26291ee8c279f7a62c6b552))

- Add MCP deployment summary
  ([#68](https://github.com/dougborg/katana-openapi-client/pull/68),
  [`db1eef3`](https://github.com/dougborg/katana-openapi-client/commit/db1eef33f542e5d0d26291ee8c279f7a62c6b552))

- Update all documentation for monorepo semantic-release
  ([#68](https://github.com/dougborg/katana-openapi-client/pull/68),
  [`db1eef3`](https://github.com/dougborg/katana-openapi-client/commit/db1eef33f542e5d0d26291ee8c279f7a62c6b552))

- Update deployment docs and fix release workflow
  ([#68](https://github.com/dougborg/katana-openapi-client/pull/68),
  [`db1eef3`](https://github.com/dougborg/katana-openapi-client/commit/db1eef33f542e5d0d26291ee8c279f7a62c6b552))

- **mcp**: Update DEPLOYMENT.md for automated semantic-release
  ([#68](https://github.com/dougborg/katana-openapi-client/pull/68),
  [`db1eef3`](https://github.com/dougborg/katana-openapi-client/commit/db1eef33f542e5d0d26291ee8c279f7a62c6b552))

### Features

- Add manual publish triggers for both packages
  ([`29c1377`](https://github.com/dougborg/katana-openapi-client/commit/29c1377db6d7212e7e069cf35112f9165021f180))

- Prepare MCP server v0.1.0a1 for PyPI deployment
  ([#68](https://github.com/dougborg/katana-openapi-client/pull/68),
  [`db1eef3`](https://github.com/dougborg/katana-openapi-client/commit/db1eef33f542e5d0d26291ee8c279f7a62c6b552))

- **mcp**: Configure monorepo semantic-release for independent versioning
  ([#68](https://github.com/dougborg/katana-openapi-client/pull/68),
  [`db1eef3`](https://github.com/dougborg/katana-openapi-client/commit/db1eef33f542e5d0d26291ee8c279f7a62c6b552))

## v0.25.0 (2025-10-24)

### Bug Fixes

- **client**: Remove invalid root_options parameter from workflow
  ([`8e313f3`](https://github.com/dougborg/katana-openapi-client/commit/8e313f37714af9d7814e088f3e0286c64ca61da9))

### Features

- **mcp**: Add package README for better documentation
  ([`9f9cebf`](https://github.com/dougborg/katana-openapi-client/commit/9f9cebfe86a739993b147b775cfc87439feb4e0b))

## v0.24.0 (2025-10-24)

### Documentation

- Add comprehensive monorepo semantic-release guide
  ([#67](https://github.com/dougborg/katana-openapi-client/pull/67),
  [`b10ad4a`](https://github.com/dougborg/katana-openapi-client/commit/b10ad4a980d34433c8d23a49ad64c5863f076283))

- Add MCP deployment summary
  ([#67](https://github.com/dougborg/katana-openapi-client/pull/67),
  [`b10ad4a`](https://github.com/dougborg/katana-openapi-client/commit/b10ad4a980d34433c8d23a49ad64c5863f076283))

- Update all documentation for monorepo semantic-release
  ([#67](https://github.com/dougborg/katana-openapi-client/pull/67),
  [`b10ad4a`](https://github.com/dougborg/katana-openapi-client/commit/b10ad4a980d34433c8d23a49ad64c5863f076283))

### Features

- Prepare MCP server v0.1.0a1 for PyPI deployment
  ([#67](https://github.com/dougborg/katana-openapi-client/pull/67),
  [`b10ad4a`](https://github.com/dougborg/katana-openapi-client/commit/b10ad4a980d34433c8d23a49ad64c5863f076283))

- **mcp**: Configure monorepo semantic-release for independent versioning
  ([#67](https://github.com/dougborg/katana-openapi-client/pull/67),
  [`b10ad4a`](https://github.com/dougborg/katana-openapi-client/commit/b10ad4a980d34433c8d23a49ad64c5863f076283))

## v0.23.0 (2025-10-24)

- Initial Release
