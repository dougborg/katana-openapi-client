# Katana MCP Server Documentation

This directory contains design and implementation documentation for the Katana Model
Context Protocol (MCP) server.

## Current Implementation

- **[MCP v0.1.0 Implementation Plan](MCP_V0.1.0_IMPLEMENTATION_PLAN.md)** - Current
  implementation plan with 10 tools, 6 resources, 3 prompts
  - **Scope**: "Small set of all MCP features to see how everything works together"
  - **Tools**: Cover all 7 user workflows with elicitation pattern
  - **Resources**: Inventory (items, movements, adjustments) + Orders (sales, purchase,
    manufacturing)
  - **Prompts**: Complete workflow automation
  - **Status**: Ready for implementation

## Reference Documentation

- **[MCP Architecture Design](MCP_ARCHITECTURE_DESIGN.md)** - Comprehensive guide to MCP
  best practices and patterns

  - 2025 MCP specification and primitives
  - Best practices for production MCP servers
  - Security, performance, and observability patterns
  - Tool/resource/prompt design examples
  - **Use this for**: Understanding MCP concepts and design decisions

- **[Development Guide](DEVELOPMENT.md)** - Setup and development workflow

  - Local development setup
  - Testing strategies
  - Debugging tips
  - **Use this for**: Day-to-day development work

## Architecture Decision Records

Key architectural decisions are documented in ADRs:

- **[ADR-010: Katana MCP Server](../adr/0010-katana-mcp-server.md)** - Core architecture
  decisions
  - Monorepo structure with uv workspace
  - Package separation (client vs MCP server)
  - Technology choices (FastMCP framework)

## Quick Links

- [Main Repository README](../../README.md)
- [Client Library Documentation](../../README.md)
- [Katana API Specification](../katana-openapi.yaml)
- [GitHub Issues - MCP Server](https://github.com/dougborg/katana-openapi-client/labels/mcp-server)

## Getting Started

1. Read [MCP v0.1.0 Implementation Plan](MCP_V0.1.0_IMPLEMENTATION_PLAN.md) to
   understand the current scope
1. Review [MCP Architecture Design](MCP_ARCHITECTURE_DESIGN.md) for MCP concepts and
   patterns
1. Follow [Development Guide](DEVELOPMENT.md) to set up your environment
1. Check
   [GitHub Issues](https://github.com/dougborg/katana-openapi-client/labels/mcp-server)
   for current work

## Package Information

The MCP server is published as a separate package:

- **Package Name**: `katana-mcp-server`
- **PyPI**: https://pypi.org/project/katana-mcp-server/
- **Dependencies**: `katana-openapi-client`, `fastmcp`
- **Installation**: `pip install katana-mcp-server` or `uvx katana-mcp-server`
