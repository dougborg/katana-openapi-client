# CHANGELOG

<!-- version list -->

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
