# Katana Manufacturing ERP - API Ecosystem

Multi-language client ecosystem for the
[Katana Manufacturing ERP API](https://help.katanamrp.com/api). Production-ready clients
with automatic resilience, rate limiting, and pagination.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![TypeScript](https://img.shields.io/badge/typescript-5.0+-blue.svg)](https://www.typescriptlang.org/)
[![OpenAPI 3.1.0](https://img.shields.io/badge/OpenAPI-3.1.0-green.svg)](https://spec.openapis.org/oas/v3.1.0)
[![CI](https://github.com/dougborg/katana-openapi-client/actions/workflows/ci.yml/badge.svg)](https://github.com/dougborg/katana-openapi-client/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/dougborg/katana-openapi-client/branch/main/graph/badge.svg)](https://codecov.io/gh/dougborg/katana-openapi-client)

## Packages

| Package                                            | Language   | Version | Description                                              |
| -------------------------------------------------- | ---------- | ------- | -------------------------------------------------------- |
| [katana-openapi-client](katana_public_api_client/) | Python     | 0.41.0  | Full-featured API client with transport-layer resilience |
| [katana-mcp-server](katana_mcp_server/)            | Python     | 0.25.0  | Model Context Protocol server for AI assistants          |
| [@katana/client](packages/katana-client/)          | TypeScript | 0.0.1   | TypeScript/JavaScript client with full type safety       |

## Features Comparison

| Feature             | Python Client   | TypeScript Client | MCP Server              |
| ------------------- | --------------- | ----------------- | ----------------------- |
| Automatic retries   | Yes             | Yes               | Yes (via Python client) |
| Rate limit handling | Yes             | Yes               | Yes                     |
| Auto-pagination     | Yes             | Yes               | Yes                     |
| Type safety         | Full (Pydantic) | Full (TypeScript) | Full (Pydantic)         |
| Sync + Async        | Yes             | Async only        | Async only              |
| Browser support     | No              | Yes               | No                      |
| AI Integration      | -               | -                 | Claude, Cursor, etc.    |

## Quick Start

### Python Client

```bash
pip install katana-openapi-client
```

```python
import asyncio
from katana_public_api_client import KatanaClient
from katana_public_api_client.api.product import get_all_products

async def main():
    async with KatanaClient() as client:
        response = await get_all_products.asyncio_detailed(client=client)
        products = response.parsed.data
        print(f"Found {len(products)} products")

asyncio.run(main())
```

### TypeScript Client

```bash
npm install katana-openapi-client
```

```typescript
import { KatanaClient } from 'katana-openapi-client';

const client = await KatanaClient.create();
const response = await client.get('/products');
const { data } = await response.json();
console.log(`Found ${data.length} products`);
```

### MCP Server (Claude Desktop)

```bash
pip install katana-mcp-server
```

Add to Claude Desktop config
(`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "katana": {
      "command": "uvx",
      "args": ["katana-mcp-server"],
      "env": {
        "KATANA_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

## Configuration

All packages support the same authentication methods:

1. **Environment variable**: `KATANA_API_KEY`
1. **`.env` file**: Create with `KATANA_API_KEY=your-key`
1. **Direct parameter**: Pass `api_key` to client constructor

```bash
# .env file
KATANA_API_KEY=your-api-key-here
KATANA_BASE_URL=https://api.katanamrp.com/v1  # Optional
```

## API Coverage

All clients provide access to the complete Katana API:

| Category             | Endpoints | Description                                 |
| -------------------- | --------- | ------------------------------------------- |
| Products & Inventory | 25+       | Products, variants, materials, stock levels |
| Orders               | 20+       | Sales orders, purchase orders, fulfillment  |
| Manufacturing        | 15+       | BOMs, manufacturing orders, operations      |
| Business Relations   | 10+       | Customers, suppliers, addresses             |
| Configuration        | 6+        | Locations, webhooks, custom fields          |

**Total**: 76+ endpoints with 150+ fully-typed data models

## Project Structure

```text
katana-openapi-client/               # Monorepo root
├── pyproject.toml                   # Workspace configuration (uv)
├── uv.lock                          # Unified lock file
├── docs/
│   ├── katana-openapi.yaml          # OpenAPI 3.1.0 specification
│   ├── adr/                         # Shared architecture decisions
│   └── *.md                         # Shared documentation
├── katana_public_api_client/        # Python client package
│   ├── katana_client.py             # Resilient client with retries
│   ├── api/                         # Generated API modules (76+)
│   ├── models/                      # Generated data models (150+)
│   └── docs/                        # Package documentation
├── katana_mcp_server/               # MCP server package
│   ├── src/katana_mcp/
│   │   ├── server.py                # FastMCP server
│   │   ├── tools/                   # MCP tools (12)
│   │   └── resources/               # MCP resources (5)
│   └── docs/                        # Package documentation
└── packages/
    └── katana-client/               # TypeScript client package
        ├── src/
        │   ├── client.ts            # Resilient client
        │   └── generated/           # Generated SDK
        └── docs/                    # Package documentation
```

## Documentation

### Package Documentation

Each package has its own documentation in its `docs/` directory:

- **[Python Client Guide](katana_public_api_client/docs/guide.md)** - Complete usage
  guide
- **[Python Client Cookbook](katana_public_api_client/docs/cookbook.md)** - Practical
  recipes
- **[MCP Server Architecture](katana_mcp_server/docs/architecture.md)** - MCP design
  patterns
- **[MCP Server Development](katana_mcp_server/docs/development.md)** - Development
  guide
- **[TypeScript Client Guide](packages/katana-client/docs/guide.md)** - TypeScript usage

### Architecture Decisions

Key architectural decisions are documented as ADRs (Architecture Decision Records):

**Python Client ADRs**
([katana_public_api_client/docs/adr/](katana_public_api_client/docs/adr/)):

- [ADR-001](katana_public_api_client/docs/adr/0001-transport-layer-resilience.md):
  Transport-Layer Resilience
- [ADR-002](katana_public_api_client/docs/adr/0002-openapi-code-generation.md): OpenAPI
  Code Generation
- [ADR-003](katana_public_api_client/docs/adr/0003-transparent-pagination.md):
  Transparent Pagination
- [ADR-006](katana_public_api_client/docs/adr/0006-response-unwrapping-utilities.md):
  Response Unwrapping

**MCP Server ADRs** ([katana_mcp_server/docs/adr/](katana_mcp_server/docs/adr/)):

- [ADR-010](katana_mcp_server/docs/adr/0010-katana-mcp-server.md): MCP Server
  Architecture

**TypeScript Client ADRs**
([packages/katana-client/docs/adr/](packages/katana-client/docs/adr/)):

- [ADR-001](packages/katana-client/docs/adr/0001-composable-fetch-wrappers.md):
  Composable Fetch Wrappers
- [ADR-002](packages/katana-client/docs/adr/0002-hey-api-code-generation.md): Hey API
  Code Generation
- [ADR-003](packages/katana-client/docs/adr/0003-biome-for-linting.md): Biome for
  Linting

**Shared/Monorepo ADRs** ([docs/adr/](docs/adr/)):

- [ADR-009](docs/adr/0009-migrate-from-poetry-to-uv.md): Migrate to uv

### Shared Documentation

- **[Contributing Guide](docs/CONTRIBUTING.md)** - How to contribute
- **[uv Usage Guide](docs/UV_USAGE.md)** - Package manager guide
- **[Monorepo Release Guide](docs/MONOREPO_SEMANTIC_RELEASE.md)** - Semantic release
  setup

## Development

### Prerequisites

- **Python 3.11+** for Python packages
- **Node.js 18+** for TypeScript package
- **uv** package manager
  ([install](https://docs.astral.sh/uv/getting-started/installation/))

### Setup

```bash
# Clone repository
git clone https://github.com/dougborg/katana-openapi-client.git
cd katana-openapi-client

# Install all dependencies
uv sync --all-extras

# Install pre-commit hooks
uv run pre-commit install

# Create .env file
cp .env.example .env  # Add your KATANA_API_KEY
```

### Common Commands

```bash
# Run all checks (lint, type-check, test)
uv run poe check

# Run tests
uv run poe test

# Format code
uv run poe format

# Regenerate Python client from OpenAPI spec
uv run poe regenerate-client
```

### Commit Standards

This project uses semantic-release with conventional commits:

```bash
# Python client changes
git commit -m "feat(client): add new inventory helper"
git commit -m "fix(client): handle pagination edge case"

# MCP server changes
git commit -m "feat(mcp): add manufacturing order tools"
git commit -m "fix(mcp): improve error handling"

# TypeScript client changes
git commit -m "feat(ts): add browser support"

# Documentation only (no release)
git commit -m "docs: update README"
```

See [MONOREPO_SEMANTIC_RELEASE.md](docs/MONOREPO_SEMANTIC_RELEASE.md) for details.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome! See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.
