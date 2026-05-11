# Katana MCP Server Documentation

This directory contains all documentation specific to the `katana-mcp-server` package.

## Documentation Index

### Getting Started

- **[Development Guide](development.md)** - Setup and development workflow
- **[Deployment Guide](deployment.md)** - Production deployment strategies
- **[Docker Guide](docker.md)** - Container deployment

### Architecture & Design

- **[Architecture Design](architecture.md)** - Comprehensive MCP architecture and
  patterns
- **[ADRs](adr/README.md)** - Architecture Decision Records

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

## Package Information

The MCP server is published as a separate package:

- **Package Name**: `katana-mcp-server`
- **PyPI**: https://pypi.org/project/katana-mcp-server/
- **Dependencies**: `katana-openapi-client`, `fastmcp`
- **Installation**: `pip install katana-mcp-server` or `uvx katana-mcp-server`

## Related Packages

This monorepo also contains:

- **[katana-openapi-client](../../katana_public_api_client/docs/README.md)** - Python
  client for Katana Manufacturing API
