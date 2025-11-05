# Katana MCP Server Documentation

This directory contains all documentation specific to the `katana-mcp-server` package.

## Documentation Index

### Getting Started

- **[Development Guide](development.md)** - Setup and development workflow
- **[Deployment Guide](deployment.md)** - Production deployment strategies
- **[Docker Guide](docker.md)** - Container deployment

### Architecture & Design

- **[Architecture Design](architecture.md)** - Comprehensive MCP architecture and patterns
- **[Implementation Plan](implementation-plan.md)** - MCP v0.1.0 implementation roadmap
- **[StockTrim Migration](stocktrim-migration.md)** - Migration to production patterns
- **[ADRs](adr/README.md)** - Architecture Decision Records

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

- **[katana-openapi-client](../../katana_public_api_client/docs/README.md)** - Python client for Katana Manufacturing API
