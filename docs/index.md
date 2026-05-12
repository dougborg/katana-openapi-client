# Katana OpenAPI Client Documentation

Welcome to the documentation site for the **Katana OpenAPI Client** monorepo — a
production-ready set of clients for the
[Katana Manufacturing ERP API](https://help.katanamrp.com/api), with automatic
resilience built in at the HTTP transport layer.

The site is generated from the per-package docs that live next to each package's source.
Each section below links straight to the canonical doc for that area; the indexes
themselves are the source of truth and stay current as features ship.

## What's in the monorepo

This repository is a workspace with three published packages plus a shared MCP server.
For installation, current version, and a quick-start example for each, follow the link
to the package README:

- **[Python client](../katana_public_api_client/docs/README.md)** —
  [`katana-openapi-client`](https://pypi.org/project/katana-openapi-client/) on PyPI.
  Sync + async API, transport-layer retries / rate-limiting / pagination, full pydantic
  models. Generated from `docs/katana-openapi.yaml`.
- **[MCP server](../katana_mcp_server/README.md)** —
  [`katana-mcp-server`](https://pypi.org/project/katana-mcp-server/) on PyPI. Model
  Context Protocol server that wraps the Python client with high-level tools (search,
  modify, fulfill, verify, plus preview/apply pairs for write operations) for use with
  Claude Desktop, Cursor, and other MCP hosts.
- **[TypeScript client](../packages/katana-client/README.md)** —
  [`katana-openapi-client`](https://www.npmjs.com/package/katana-openapi-client) on npm.
  Async API with the same resilience guarantees as the Python client; works in browsers.

The
[root `README.md`](https://github.com/dougborg/katana-openapi-client/blob/main/README.md)
is the front door — it has the multi-package install table, a side-by-side feature
comparison, and the cross-cutting setup steps. Read that first if you're new to the
project.

## Architecture in one paragraph

Resilience (retries, rate limiting, pagination) is implemented **at the httpx transport
layer**, not as a wrapper. Every generated API method gets it automatically — including
new endpoints added by spec regeneration. No decorators, no method-by-method opt-in. See
[ADR-0001](client/adr/0001-transport-layer-resilience.md) for the full rationale.

## Documentation by package

### Python client

- **[Guide](client/guide.md)** — installation, response unwrapping helpers
  (`unwrap_data`, `unwrap_as`, `is_success`), pagination, retries, logging.
- **[Cookbook](client/cookbook.md)** — task-oriented recipes.
- **[Testing](client/testing.md)** — `httpx.MockTransport` patterns, conftest fixtures.
- **[Spec authoring](client/spec-authoring.md)** — OpenAPI 3.1 conventions, generator /
  regen lockstep, breaking-change markers.
- **[Changelog](client/CHANGELOG.md)** — release notes.
- **[ADRs](client/adr/README.md)** — client architectural decisions.

### MCP server

- **[Overview](mcp-server/index.md)** — package landing page with the full doc index.
- **[Architecture](mcp-server/architecture.md)** — design patterns and component layout.
- **[Development](mcp-server/development.md)** — local dev workflow.
- **[Deployment](mcp-server/deployment.md)** / **[Docker](mcp-server/docker.md)** —
  production deploys.
- **[ADRs](mcp-server/adr/README.md)** — MCP architectural decisions.

The live MCP tool list is exposed at runtime via the `katana://help/tools` resource —
that's the canonical inventory, not anything in this docsite.

### TypeScript client

The TS client docs live with the package source on GitHub —
[`packages/katana-client/`](https://github.com/dougborg/katana-openapi-client/tree/main/packages/katana-client).
The current published version is on the
[npm page](https://www.npmjs.com/package/katana-openapi-client).

## Reference

- **[OpenAPI specification](openapi-docs.md)** — interactive viewer for
  `docs/katana-openapi.yaml`, the canonical endpoint surface that drives both generated
  clients.
- **[API reference](reference/)** — auto-generated from the Python source via
  `mkdocstrings`; one page per module.

## Process and contribution

- **[Contributing guide](CONTRIBUTING.md)** — development setup, code style, the "no
  hand-maintained drift-prone references" rule, spec-maintenance workflow.
- **[Release guide](RELEASE.md)** /
  **[Monorepo semantic-release](MONOREPO_SEMANTIC_RELEASE.md)** — how the
  conventional-commit → release pipeline drives per-package versioning.
- **[uv usage](UV_USAGE.md)** — the `uv` package manager and `poe` task conventions this
  repo uses.
- **[Code of conduct](CODE_OF_CONDUCT.md)**.

## Architecture decision records

ADRs live next to the package they govern. Each directory has a `README.md` index
listing every ADR with its current status — those indexes are the canonical list and
stay current as ADRs are added or superseded.

- **[Shared / monorepo ADRs](adr/README.md)** — cross-cutting decisions.
- **[Python client ADRs](client/adr/README.md)** — client package decisions.
- **[MCP server ADRs](mcp-server/adr/README.md)** — MCP package decisions.

## Support

- **Issues**: [GitHub Issues](https://github.com/dougborg/katana-openapi-client/issues)
- **Source**: [GitHub Repository](https://github.com/dougborg/katana-openapi-client)
- **Project board**: [Rolling Backlog](https://github.com/users/dougborg/projects/5) —
  what's actively in flight.

MIT licensed —
[LICENSE](https://github.com/dougborg/katana-openapi-client/blob/main/LICENSE).
