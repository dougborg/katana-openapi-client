# CHANGELOG

<!-- version list -->

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

### Features

- Implement MCP Server v0.1.0-alpha with 3 inventory tools, comprehensive tests, and
  documentation ([#66](https://github.com/dougborg/katana-openapi-client/pull/66),
  [`ef22a8c`](https://github.com/dougborg/katana-openapi-client/commit/ef22a8c09549824162f1faa5d7cb81394d004d7b))

## v0.22.0 (2025-10-23)

### Bug Fixes

- Add __future__ annotations import for Python 3.11 compatibility
  ([#62](https://github.com/dougborg/katana-openapi-client/pull/62),
  [`ea504d1`](https://github.com/dougborg/katana-openapi-client/commit/ea504d11598e881217e4ec6de0b10e46eeda6ea2))

- Add type parameters to dict return types in MCP scripts
  ([`3ca82d1`](https://github.com/dougborg/katana-openapi-client/commit/3ca82d11dd5369665bc726e0e6b9eddf542e99d1))

- Resolve mypy type errors in domain helpers
  ([#62](https://github.com/dougborg/katana-openapi-client/pull/62),
  [`ea504d1`](https://github.com/dougborg/katana-openapi-client/commit/ea504d11598e881217e4ec6de0b10e46eeda6ea2))

### Chores

- Remove temporary CI cache refresh comment
  ([#62](https://github.com/dougborg/katana-openapi-client/pull/62),
  [`ea504d1`](https://github.com/dougborg/katana-openapi-client/commit/ea504d11598e881217e4ec6de0b10e46eeda6ea2))

- Trigger CI re-run after annotations fix
  ([#62](https://github.com/dougborg/katana-openapi-client/pull/62),
  [`ea504d1`](https://github.com/dougborg/katana-openapi-client/commit/ea504d11598e881217e4ec6de0b10e46eeda6ea2))

### Continuous Integration

- Force cache refresh for test environment
  ([#62](https://github.com/dougborg/katana-openapi-client/pull/62),
  [`ea504d1`](https://github.com/dougborg/katana-openapi-client/commit/ea504d11598e881217e4ec6de0b10e46eeda6ea2))

- Use SEMANTIC_RELEASE_TOKEN for protected branch bypass
  ([#62](https://github.com/dougborg/katana-openapi-client/pull/62),
  [`ea504d1`](https://github.com/dougborg/katana-openapi-client/commit/ea504d11598e881217e4ec6de0b10e46eeda6ea2))

### Documentation

- Accept ADR-007 and add domain helpers implementation plan
  ([#62](https://github.com/dougborg/katana-openapi-client/pull/62),
  [`ea504d1`](https://github.com/dougborg/katana-openapi-client/commit/ea504d11598e881217e4ec6de0b10e46eeda6ea2))

- Accept ADR-007 and add domain helpers implementation plan
  ([#61](https://github.com/dougborg/katana-openapi-client/pull/61),
  [`6fa8526`](https://github.com/dougborg/katana-openapi-client/commit/6fa8526e1890c7063320d48f53ad7cea24e8ad83))

- Accept ADR-010 with monorepo approach using uv workspace
  ([`8fcdb5c`](https://github.com/dougborg/katana-openapi-client/commit/8fcdb5c342a76f83ad1c3b9f6dfb758ee7cf2e26))

- Add ADR-010 for Katana MCP server implementation
  ([`eea4b21`](https://github.com/dougborg/katana-openapi-client/commit/eea4b21d06d8bb72244bba2742f89de8c6974d1d))

- Add issue number mapping to MCP implementation plan
  ([#59](https://github.com/dougborg/katana-openapi-client/pull/59),
  [`d3e2764`](https://github.com/dougborg/katana-openapi-client/commit/d3e27642e2b217def4b3484fe8c42aee254ca5a6))

- Add MCP server setup completion summary
  ([`f386182`](https://github.com/dougborg/katana-openapi-client/commit/f386182b919cc72cceb3fa3008e5befd3813d991))

- Add release workflow setup guide with PAT instructions
  ([#62](https://github.com/dougborg/katana-openapi-client/pull/62),
  [`ea504d1`](https://github.com/dougborg/katana-openapi-client/commit/ea504d11598e881217e4ec6de0b10e46eeda6ea2))

- Add Repository Rulesets setup guide for automated releases
  ([#62](https://github.com/dougborg/katana-openapi-client/pull/62),
  [`ea504d1`](https://github.com/dougborg/katana-openapi-client/commit/ea504d11598e881217e4ec6de0b10e46eeda6ea2))

- Finalize ADR-010 with purchase orders and answer open questions
  ([`da22985`](https://github.com/dougborg/katana-openapi-client/commit/da2298509bc8f87d87aaadbc69369141bae8bb91))

- Move ADR-009 and ADR-010 to accepted list in README
  ([`5c9fce7`](https://github.com/dougborg/katana-openapi-client/commit/5c9fce76cdf7e9489ea12fc1503f5fbdf1a37080))

- Split release documentation into separate RELEASE.md
  ([#62](https://github.com/dougborg/katana-openapi-client/pull/62),
  [`ea504d1`](https://github.com/dougborg/katana-openapi-client/commit/ea504d11598e881217e4ec6de0b10e46eeda6ea2))

- Update all Poetry references to uv throughout documentation
  ([`f550972`](https://github.com/dougborg/katana-openapi-client/commit/f550972a3f9b37d6bfc2f89f637f67964d44781a))

### Features

- Add GitHub Codespaces devcontainer with prebuilds for MCP server development
  ([`1a8da47`](https://github.com/dougborg/katana-openapi-client/commit/1a8da475d9601308ad34e70bde85684eafc42580))

- Add MCP server implementation plan and issue generation
  ([`ca2779b`](https://github.com/dougborg/katana-openapi-client/commit/ca2779b633b4abaf0e07b65efc972f7730ec4952))

- Create katana_mcp_server package structure
  ([`4d7da0f`](https://github.com/dougborg/katana-openapi-client/commit/4d7da0ff34d1fd7107b9880e37baa38ff0a0c486))

- Implement Inventory domain class with full CRUD support (Phase 1 of #60)
  ([#62](https://github.com/dougborg/katana-openapi-client/pull/62),
  [`ea504d1`](https://github.com/dougborg/katana-openapi-client/commit/ea504d11598e881217e4ec6de0b10e46eeda6ea2))

- Set up uv workspace for monorepo
  ([`4f31a93`](https://github.com/dougborg/katana-openapi-client/commit/4f31a939a231ceed04a0e5ee1b3f238f60df382a))

- **mcp**: Implement basic FastMCP server with authentication
  ([#58](https://github.com/dougborg/katana-openapi-client/pull/58),
  [`9cdfbff`](https://github.com/dougborg/katana-openapi-client/commit/9cdfbff2c3d5c7ed77f31ba240488c379262d697))

- **mcp**: Implement basic FastMCP server with authentication (MCP-03)
  ([#58](https://github.com/dougborg/katana-openapi-client/pull/58),
  [`9cdfbff`](https://github.com/dougborg/katana-openapi-client/commit/9cdfbff2c3d5c7ed77f31ba240488c379262d697))

### Refactoring

- Split into 5 domain classes with proper separation
  ([#62](https://github.com/dougborg/katana-openapi-client/pull/62),
  [`ea504d1`](https://github.com/dougborg/katana-openapi-client/commit/ea504d11598e881217e4ec6de0b10e46eeda6ea2))

- Use getattr() instead of hasattr() for attribute checking
  ([#62](https://github.com/dougborg/katana-openapi-client/pull/62),
  [`ea504d1`](https://github.com/dougborg/katana-openapi-client/commit/ea504d11598e881217e4ec6de0b10e46eeda6ea2))

- Use models-only parameters in domain helpers
  ([#62](https://github.com/dougborg/katana-openapi-client/pull/62),
  [`ea504d1`](https://github.com/dougborg/katana-openapi-client/commit/ea504d11598e881217e4ec6de0b10e46eeda6ea2))

## v0.21.0 (2025-10-21)

### Chores

- Regenerate client with improved docstring formatting
  ([`4b66b20`](https://github.com/dougborg/katana-openapi-client/commit/4b66b203c4544d82e6719dabdd6e74cf6ec5d818))

### Features

- Add comprehensive cookbook documentation and examples
  ([`59ebc5e`](https://github.com/dougborg/katana-openapi-client/commit/59ebc5e22101afefe1a559b83b53c86b263aba66))

### Testing

- Add comprehensive edge case tests for transport layer
  ([`5dadd7a`](https://github.com/dougborg/katana-openapi-client/commit/5dadd7adb5472c8c52e8c28d1369f0bf55289cfe))

- Add comprehensive KatanaClient init and integration tests
  ([`1602409`](https://github.com/dougborg/katana-openapi-client/commit/1602409d0ceb437324594c31f114be962d75adbf))

- Add comprehensive tests for RateLimitAwareRetry class
  ([`f566057`](https://github.com/dougborg/katana-openapi-client/commit/f5660570fe05d4a2df516d01fe64e093c95f8a33))

## v0.20.0 (2025-10-21)

### Chores

- Update uv.lock and CLIENT_README from regeneration
  ([`9d4f781`](https://github.com/dougborg/katana-openapi-client/commit/9d4f7810b47f5ba81a4eca2870d2b3550577ebbb))

### Features

- Add comprehensive validation constraints for ISO standards and data formats
  ([`241ba05`](https://github.com/dougborg/katana-openapi-client/commit/241ba055a2eed725fdc5b05a03495d2a002c89eb))

## v0.19.1 (2025-10-20)

### Bug Fixes

- Add minItems constraint to UpdateProductRequest configs field
  ([`ed1f7b3`](https://github.com/dougborg/katana-openapi-client/commit/ed1f7b370088c76baa5331bf9fb93a206dc639c9))

## v0.19.0 (2025-10-20)

### Features

- Add type overloads for unwrap() to improve type safety
  ([`9e6c656`](https://github.com/dougborg/katana-openapi-client/commit/9e6c6568838418d818a29b7f423ba231eee9289c))

## v0.18.0 (2025-10-20)

### Features

- Enhanced validation error logging with nested details support
  ([`66ee086`](https://github.com/dougborg/katana-openapi-client/commit/66ee08637323df83723c08447f2f9fdb6857db6b))

## v0.17.0 (2025-10-20)

### Chores

- Ignore Claude local settings file
  ([`53243c2`](https://github.com/dougborg/katana-openapi-client/commit/53243c2e6c13e9d9d7c98f02209432cdd2baab0f))

### Documentation

- Simplify README to focus on KatanaClient only
  ([`eaf43f4`](https://github.com/dougborg/katana-openapi-client/commit/eaf43f4be1ce8e1763b30f7f47b31c2156462d49))

- Update CLAUDE.md to focus on KatanaClient only
  ([`ec2915b`](https://github.com/dougborg/katana-openapi-client/commit/ec2915ba3e18e963200ab271137a2a9bdbae0e92))

### Features

- Comprehensive error logging improvements
  ([`5958927`](https://github.com/dougborg/katana-openapi-client/commit/595892783c391f41cfbd34cdf1a0c08c714eea4c))

## v0.16.1 (2025-10-20)

### Bug Fixes

- Correct SerialNumber endpoint response schemas to match actual API
  ([`5a3ce74`](https://github.com/dougborg/katana-openapi-client/commit/5a3ce74f23bfcd89e1d36ef0115ce381af19fb78))

### Documentation

- Optimize documentation build (112x size reduction, 2x speed improvement)
  ([`88a7baf`](https://github.com/dougborg/katana-openapi-client/commit/88a7baf8465a74e8336d2e39b4fbbcb090461aa0))

## v0.16.0 (2025-10-17)

### Continuous Integration

- Complete migration to uv across all workflows and add optimizations
  ([`f856a1c`](https://github.com/dougborg/katana-openapi-client/commit/f856a1cd44ff9fd72fe3079693e2cc5100b2decd))

- Upgrade to setup-uv@v7 and consolidate Python setup
  ([`ac2851f`](https://github.com/dougborg/katana-openapi-client/commit/ac2851f0d21a378f0097549ce7fa392bde592934))

### Documentation

- Accept ADR-009 for Poetry to uv migration
  ([`9dafbbb`](https://github.com/dougborg/katana-openapi-client/commit/9dafbbb7707a70a04e3824378ba084ab21765416))

- Add ADR-009 for Poetry to uv package manager migration
  ([`7a29915`](https://github.com/dougborg/katana-openapi-client/commit/7a29915be99ca49c58a5ed1ce3937bae952ff5c1))

- Update CLAUDE.md and ADR docs to reflect consolidation changes
  ([`49cef79`](https://github.com/dougborg/katana-openapi-client/commit/49cef79ac47e7ec2eb16b5a05732d7839b2d7939))

### Features

- Migrate from Poetry to uv package manager (ADR-009)
  ([`570ab88`](https://github.com/dougborg/katana-openapi-client/commit/570ab88ecf1b3728a47f3ada69a9bbc46c1c1b7d))

## v0.15.0 (2025-10-17)

### Documentation

- Add Architecture Decision Records (ADRs) infrastructure
  ([`41eacdd`](https://github.com/dougborg/katana-openapi-client/commit/41eacddd479ead808d8285beee20126230b00869))

- Clean up temporary analysis files and consolidate documentation
  ([`dc0fcd9`](https://github.com/dougborg/katana-openapi-client/commit/dc0fcd948be733a136fd0e2723e87fe526511030))

### Features

- Add comprehensive codebase assessment and coverage analysis
  ([`c7befd7`](https://github.com/dougborg/katana-openapi-client/commit/c7befd7882730c7738bc8eb3cc4e1f61263ae09c))

## v0.14.1 (2025-10-17)

### Bug Fixes

- Correct unwrap_data type overloads and handle single objects
  ([`6bb7500`](https://github.com/dougborg/katana-openapi-client/commit/6bb750099c5d5a07e948bfa042c1f95ff732d724))

## v0.14.0 (2025-10-17)

### Documentation

- Improve documentation deployment configuration
  ([`82477bc`](https://github.com/dougborg/katana-openapi-client/commit/82477bc0e4ba1b4efe6a302a2c924b58a3747449))

- Update documentation to reflect current retry logic and remove outdated content
  ([`5ba4b48`](https://github.com/dougborg/katana-openapi-client/commit/5ba4b485e62fc4e3d1eeed27b783e814c8a1a99d))

### Features

- Add response unwrapping and error handling utilities
  ([`a237907`](https://github.com/dougborg/katana-openapi-client/commit/a2379071e0561e19129467583dae189c46fe2da1))

## v0.13.1 (2025-10-15)

### Bug Fixes

- Add missing status_forcelist to enable retry logic for 429 errors
  ([`ad4cbb3`](https://github.com/dougborg/katana-openapi-client/commit/ad4cbb316bd700b6e977167235ef2090e5ac034a))

## v0.13.0 (2025-10-10)

### Features

- Add smart retry logic for non-idempotent operations
  ([`64de3e6`](https://github.com/dougborg/katana-openapi-client/commit/64de3e63c76025f3a5b58e8c85bccb1b60e83911))

## v0.12.1 (2025-10-10)

### Bug Fixes

- Handle Unset fields in 429 error logging and enable POST/PATCH retries
  ([`259692c`](https://github.com/dougborg/katana-openapi-client/commit/259692c3620a19f1ce32433e0a95dc92198d09f5))

## v0.12.0 (2025-10-10)

### Features

- Refactor to layered transport architecture with httpx-retries
  ([`9f11717`](https://github.com/dougborg/katana-openapi-client/commit/9f11717cfeaba61f0ad42467a01559f0c82780d7))

## v0.11.0 (2025-10-08)

### Features

- **openapi**: Standardize per-resource extend query parameters and regenerate client
  ([`b5a6c35`](https://github.com/dougborg/katana-openapi-client/commit/b5a6c35e07ccf7318b150d18a03769a93ba2997d))

## v0.10.0 (2025-09-18)

### Bug Fixes

- Add missing format: date-time specifications to date fields in OpenAPI schema
  ([`d8d335c`](https://github.com/dougborg/katana-openapi-client/commit/d8d335c3c856a3b7821753719b210a959ac616cf))

- Remove unused schema components and fix validation warnings
  ([`eea4e33`](https://github.com/dougborg/katana-openapi-client/commit/eea4e3322726577032e7f828e49ec5b50c82e6c7))

### Features

- Comprehensive OpenAPI schema validation and fixes
  ([`95784ef`](https://github.com/dougborg/katana-openapi-client/commit/95784ef5d5527f6ff561d7b47d48678920841042))

- Comprehensive schema restructuring for POs, BaseEntity inheritance and updated service
  endpoints and schemas to match documentation
  ([`1c79b18`](https://github.com/dougborg/katana-openapi-client/commit/1c79b1801e060277387689030469ea2157bc317a))

- Implement InventoryItem base schema with Product/Material inheritance
  ([`7d2237a`](https://github.com/dougborg/katana-openapi-client/commit/7d2237aa9b9eb3fc3762a14e6d66af553c037778))

- Improve documentation extraction and update comprehensive API docs
  ([`dec9725`](https://github.com/dougborg/katana-openapi-client/commit/dec9725c579db7114ca0b8b1d38d74774c710724))

## v0.9.0 (2025-08-21)

### Chores

- Add automated setup workflow for GitHub Copilot coding agent
  ([`112930e`](https://github.com/dougborg/katana-openapi-client/commit/112930ed3d84790d48eccaed9befa2a68ead6650))

- Add pre-commit hooks installation to Copilot setup workflow
  ([`e3eef1a`](https://github.com/dougborg/katana-openapi-client/commit/e3eef1aaff2afbdb6ece367d02640599e2b9d93f))

### Features

- Implement comprehensive API documentation validation framework and add missing
  endpoints
  ([`5bb6873`](https://github.com/dougborg/katana-openapi-client/commit/5bb6873479c63a9fcd2a4b9d9c61f3a1ef6c8a99))

## v0.8.1 (2025-08-19)

### Bug Fixes

- Align sales order schemas with official Katana API documentation
  ([`7d6b9e2`](https://github.com/dougborg/katana-openapi-client/commit/7d6b9e2bdb173939013d053ec039d381e07be90d))

## Unreleased

### Bug Fixes

- Test semantic-release changelog automation for future releases
  ([`d83a575`](https://github.com/dougborg/katana-openapi-client/commit/d83a575c97a274f0580c0a7e4ad9079c44bb0062))

- Update semantic-release changelog configuration for v10 compatibility
  ([`3351d8a`](https://github.com/dougborg/katana-openapi-client/commit/3351d8af3bd9addc6362f7d2051277c493337682))

- Update test file to validate semantic-release changelog generation
  ([`e42e5d6`](https://github.com/dougborg/katana-openapi-client/commit/e42e5d6d9ca08c48d3c0a51de7b05b649072dbf2))

### Chores

- Add test file to verify semantic-release changelog generation
  ([`0168c54`](https://github.com/dougborg/katana-openapi-client/commit/0168c54b1ef7b86b3b646b45f8d9c9edbbc2e0d2))

### Documentation

- Regenerate comprehensive changelog from git history
  ([`1463edb`](https://github.com/dougborg/katana-openapi-client/commit/1463edbada799085649beca41f83ab792cc72f43))

## v0.8.0 (2025-08-13)

### Chores

- Restore comprehensive Katana docs and cleanup redundant files
  ([`2f2127d`](https://github.com/dougborg/katana-openapi-client/commit/2f2127d94690b396564d23cc81340c5f149c5f26))

### Features

- Add comprehensive webhook documentation and fix pagination headers
  ([`fc43b5f`](https://github.com/dougborg/katana-openapi-client/commit/fc43b5fa9ded8c5f976dc545aa6e270edf0d5555))

## v0.7.0 (2025-08-13)

### Features

- Streamline regeneration script and flatten import structure
  ([#26](https://github.com/dougborg/katana-openapi-client/pull/26),
  [`d091c46`](https://github.com/dougborg/katana-openapi-client/commit/d091c46dacbd635b42e0b64cbbe5a20b960c75ab))

## v0.6.0 (2025-08-12)

### Chores

- ✨Set up Copilot instructions
  ([#25](https://github.com/dougborg/katana-openapi-client/pull/25),
  [`69bf6ce`](https://github.com/dougborg/katana-openapi-client/commit/69bf6cef42c8d8ecbbc2884af67e871777d87308))

### Features

- Complete comprehensive programmatic OpenAPI schema validation standards for property
  descriptions and payload examples
  ([#23](https://github.com/dougborg/katana-openapi-client/pull/23),
  [`650f769`](https://github.com/dougborg/katana-openapi-client/commit/650f769ee2f4e5a741095e988c969bf435da8143))

## v0.5.1 (2025-08-07)

### Bug Fixes

- Improve BOM row schemas and validate against official documentation
  ([`42d5bda`](https://github.com/dougborg/katana-openapi-client/commit/42d5bda9d38beb894c32c1406728b2e5becad738))

### Chores

- Document established OpenAPI schema patterns in copilot instructions
  ([`fcd31de`](https://github.com/dougborg/katana-openapi-client/commit/fcd31de157828b84df0fa1686f1f149a30a2a4bc))

## v0.5.0 (2025-08-07)

### Features

- Enhance schema patterns and improve OpenAPI validation
  ([`7e6fd3a`](https://github.com/dougborg/katana-openapi-client/commit/7e6fd3a864844995c1ae21b62ee43ca5b8e45e2b))

## v0.4.0 (2025-08-07)

### Features

- Introduce BaseEntity schema and improve parameter descriptions
  ([`ef41c57`](https://github.com/dougborg/katana-openapi-client/commit/ef41c57a1b44302373d6fb0d2af61c6e51ba0c55))

## v0.3.3 (2025-08-07)

### Bug Fixes

- BomRow and Location schemas and endpoints
  ([`f017310`](https://github.com/dougborg/katana-openapi-client/commit/f017310a1b58b704215ddb6091ecd2a1f4de5405))

## v0.3.2 (2025-08-01)

### Bug Fixes

- Update sku parameter to accept list of strings in get_all_variants
  ([`7a1379a`](https://github.com/dougborg/katana-openapi-client/commit/7a1379a0c554b2d0efc79021dac162646b2d9b20))

## v0.3.1 (2025-07-31)

### Bug Fixes

- Add missing 'service' value to VariantResponseType enum
  ([`707ba13`](https://github.com/dougborg/katana-openapi-client/commit/707ba13e07eb88aa5b43a53984a9f4d1d82a2ba6))

## v0.3.0 (2025-07-30)

### Features

- DRY OpenAPI spec, regenerate client, and simplify error handling
  ([`519d9b4`](https://github.com/dougborg/katana-openapi-client/commit/519d9b477199f2958efeaa41c6c8d6dab84caf8c))

### Breaking Changes

- Many generated model and API files were removed or renamed; client and error handling
  patterns have changed. Review migration notes before upgrading.

## v0.2.2 (2025-07-30)

### Bug Fixes

- Align OpenAPI spec with Katana docs and prep for DRY improvements
  ([`cdaba92`](https://github.com/dougborg/katana-openapi-client/commit/cdaba9251b2e00fe8ad7d08f600d75ac62eef143))

## v0.2.1 (2025-07-28)

### Bug Fixes

- Convert optional enum definitions to use anyOf pattern
  ([#14](https://github.com/dougborg/katana-openapi-client/pull/14),
  [`4ec9ed5`](https://github.com/dougborg/katana-openapi-client/commit/4ec9ed59d7bbf3ddcdf657b6e4db572ed15cb673))

### Chores

- Remove AST check from CI workflow to resolve build failures
  ([#14](https://github.com/dougborg/katana-openapi-client/pull/14),
  [`4ec9ed5`](https://github.com/dougborg/katana-openapi-client/commit/4ec9ed59d7bbf3ddcdf657b6e4db572ed15cb673))

### Documentation

- Refresh documentation with current project structure and patterns
  ([#8](https://github.com/dougborg/katana-openapi-client/pull/8),
  [`4988ca0`](https://github.com/dougborg/katana-openapi-client/commit/4988ca02db83709b700e3ac2d71fb1f11e041507))

## v0.2.0 (2025-07-24)

### Bug Fixes

- Complete ruff linting fixes for modern Python syntax
  ([`f1b88d6`](https://github.com/dougborg/katana-openapi-client/commit/f1b88d685775627ee1762eef14a460982ba313a6))

- Configure ruff to properly ignore generated code
  ([`c112157`](https://github.com/dougborg/katana-openapi-client/commit/c112157bab4cbfa596f151727b78c152f3ce92c8))

- Resolve OpenAPI nullable enum issues and enhance code generation
  ([`283b74f`](https://github.com/dougborg/katana-openapi-client/commit/283b74f55a8c9eb51e04e0335b97a0c1d33f7251))

### Chores

- Add comprehensive documentation generation and GitHub Pages publishing
  ([#4](https://github.com/dougborg/katana-openapi-client/pull/4),
  [`38b0cc7`](https://github.com/dougborg/katana-openapi-client/commit/38b0cc742fc83b64adda2055634979a3829c24ac))

- Add pre-commit hooks and development tooling
  ([#6](https://github.com/dougborg/katana-openapi-client/pull/6),
  [`d6511e6`](https://github.com/dougborg/katana-openapi-client/commit/d6511e68949a95ba6871ad7e60b6b7b9e295a535))

- Clean up cruft files and improve .gitignore
  ([`fe76ad4`](https://github.com/dougborg/katana-openapi-client/commit/fe76ad480851ed4a9a8e22b839d84958118f28d0))

- Configure semantic-release for pre-1.0 development
  ([`159f3b4`](https://github.com/dougborg/katana-openapi-client/commit/159f3b4f1d7ca52620fccd3c4119b546b3344c86))

- Optimize regeneration workflow and add systematic patches
  ([`0b0560f`](https://github.com/dougborg/katana-openapi-client/commit/0b0560f585326ec3ba727f32bdd43dcf2d81699f))

- **docs**: Update README.md for python version support
  ([`ba2aeb7`](https://github.com/dougborg/katana-openapi-client/commit/ba2aeb7cc3d4c412652f74b4d583db1775e354d0))

### Documentation

- Include generated API files in documentation
  ([`2ffb10c`](https://github.com/dougborg/katana-openapi-client/commit/2ffb10cd7da661fd9511619be694bc178965cf8b))

- Update documentation and GitHub workflows
  ([`1c0de0b`](https://github.com/dougborg/katana-openapi-client/commit/1c0de0bed6db14aacb9d7436cffc7319620001bc))

### Features

- Add OpenTracing support for distributed tracing integration
  ([#2](https://github.com/dougborg/katana-openapi-client/pull/2),
  [`289184b`](https://github.com/dougborg/katana-openapi-client/commit/289184b4c6817fefddb63b656b2beb7655af71e4))

- Complete OpenTracing removal and optimize documentation testing
  ([`acc71cd`](https://github.com/dougborg/katana-openapi-client/commit/acc71cd63cb2af7c73fd6181409af4439a8ee72b))

- Eliminate confusing client.client pattern - cleaner API design
  ([#5](https://github.com/dougborg/katana-openapi-client/pull/5),
  [`116ea04`](https://github.com/dougborg/katana-openapi-client/commit/116ea0431a0f0d3e61163ed7076f1b2dd539bfa5))

- Enhance error logging with beautiful human-readable formatting
  ([`aa9fda1`](https://github.com/dougborg/katana-openapi-client/commit/aa9fda1c7f89d84764cae08fa6064f7f5736b4a0))

- Update generated OpenAPI client with latest improvements
  ([`29e2e2e`](https://github.com/dougborg/katana-openapi-client/commit/29e2e2ed4e6831e056a5c2db7242e4c35ed0e614))

## v0.1.0 (2025-07-16)

- Initial Release
