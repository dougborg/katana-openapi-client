# Katana MCP Server Documentation

This directory contains all documentation specific to the `katana-mcp-server` package.

## Documentation Index

### Getting Started

- **[Development Guide](development.md)** - Setup and development workflow
- **[Deployment Guide](deployment.md)** - Production deployment strategies
- **[Docker Guide](docker.md)** - Container deployment
- **[Logging](LOGGING.md)** - Structured logging configuration

### Architecture & Design

- **[Architecture Design](architecture.md)** - Comprehensive MCP architecture and
  patterns
- **[ADRs](adr/README.md)** - Architecture Decision Records

### Subsystem Guides

Topical references that go deeper than the architecture overview. Open the relevant
README when working in that subsystem.

- **[Prefab UI](prefab/README.md)** - Card builders, DataTable mustache binding,
  `register_preview_tool` + `meta=UI_META` contract, browser-render harness pitfalls.
- **[Typed Cache](typed_cache/README.md)** - SQLite-backed cache, FTS5 search, archive /
  deleted soft-state, `Cached<Name>` sibling tables, sync postprocessing.

### Cookbook

Task-oriented recipes covering specific behaviors of the MCP server. Reach for these
when you're debugging a "why doesn't this work?" or extending a subsystem.

- **[Catalog Search](cookbook/catalog-search.md)** - How `search_items` /
  `search_customers` work end-to-end: tokenizer, FTS5 sidecar, SQLite triggers, variant
  denormalization, soft-state filtering.

## Quick Links

- **[Main Repository README](../../README.md)** - Project overview
- **[Contributing Guide](../../docs/CONTRIBUTING.md)** - How to contribute
- **[PyPI Package](https://pypi.org/project/katana-mcp-server/)** - Published package

## Related Packages

This monorepo also contains:

- **[katana-openapi-client](../../katana_public_api_client/docs/README.md)** - Python
  client for Katana Manufacturing API
