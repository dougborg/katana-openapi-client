# Katana Manufacturing ERP - API Ecosystem

Multi-language client ecosystem for the
[Katana Manufacturing ERP API](https://help.katanamrp.com/api). Production-ready clients
with automatic resilience, rate limiting, and pagination.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![TypeScript](https://img.shields.io/badge/typescript-5.0+-blue.svg)](https://www.typescriptlang.org/)
[![OpenAPI 3.1.0](https://img.shields.io/badge/OpenAPI-3.1.0-green.svg)](https://spec.openapis.org/oas/v3.1.0)
[![CI](https://github.com/dougborg/katana-openapi-client/actions/workflows/ci.yml/badge.svg)](https://github.com/dougborg/katana-openapi-client/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/dougborg/katana-openapi-client/branch/main/graph/badge.svg)](https://codecov.io/gh/dougborg/katana-openapi-client)

## Packages

| Package                                            | Language   | Version                                                                                                                      | Description                                              |
| -------------------------------------------------- | ---------- | ---------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- |
| [katana-openapi-client](katana_public_api_client/) | Python     | [![PyPI](https://img.shields.io/pypi/v/katana-openapi-client.svg?label=)](https://pypi.org/project/katana-openapi-client/)   | Full-featured API client with transport-layer resilience |
| [katana-mcp-server](katana_mcp_server/)            | Python     | [![PyPI](https://img.shields.io/pypi/v/katana-mcp-server.svg?label=)](https://pypi.org/project/katana-mcp-server/)           | Model Context Protocol server for AI assistants          |
| [katana-openapi-client](packages/katana-client/)   | TypeScript | [![npm](https://img.shields.io/npm/v/katana-openapi-client.svg?label=)](https://www.npmjs.com/package/katana-openapi-client) | TypeScript/JavaScript client with full type safety       |

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

All clients provide access to the complete Katana API. The canonical endpoint surface is
the OpenAPI spec at [`docs/katana-openapi.yaml`](docs/katana-openapi.yaml); the Python
and TypeScript clients are generated from it, and the MCP server wraps a curated subset
of high-level tools on top of the Python client.

- **Python / TypeScript clients** — every operation in the spec, with generated types
  for all request and response models.
- **MCP server** — a higher-level tool surface (search, modify, fulfill, verify, plus
  preview/apply pairs for write operations); the live tool list is exposed via the
  `katana://help/tools` resource.

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
│   ├── api/                         # Generated API modules
│   ├── models/                      # Generated data models
│   ├── models_pydantic/             # Generated pydantic models
│   └── docs/                        # Package documentation
├── katana_mcp_server/               # MCP server package
│   ├── src/katana_mcp/
│   │   ├── server.py                # FastMCP server
│   │   ├── tools/                   # MCP tools
│   │   ├── resources/               # MCP resources
│   │   └── typed_cache/             # SQLite-backed typed cache
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

- **[Python Client Guide](katana_public_api_client/docs/guide.md)** — usage, response
  helpers, pagination, retries
- **[Python Client Cookbook](katana_public_api_client/docs/cookbook.md)** — practical
  recipes
- **[OpenAPI Spec Authoring](katana_public_api_client/docs/spec-authoring.md)** — 3.1
  conventions, generator/regen lockstep, breaking-change markers
- **[MCP Server Architecture](katana_mcp_server/docs/architecture.md)** — MCP design
  patterns
- **[MCP Server Development](katana_mcp_server/docs/development.md)** — development
  workflow
- **[MCP Prefab UI](katana_mcp_server/docs/prefab/README.md)** — card builders and
  renderer pitfalls
- **[MCP Typed Cache](katana_mcp_server/docs/typed_cache/README.md)** — SQLite cache,
  FTS5, soft-state filtering
- **[TypeScript Client Guide](packages/katana-client/docs/guide.md)** — TypeScript usage

### Architecture Decisions

Architecture Decision Records live under each package's `docs/adr/` directory plus
shared monorepo ADRs under `docs/adr/`. Each ADR directory has a `README.md` index that
lists every ADR in that scope with its current status — those indexes are the canonical
list and stay current as ADRs are added or superseded.

- **[Shared / monorepo ADRs](docs/adr/README.md)** — cross-cutting decisions
- **[Python client ADRs](katana_public_api_client/docs/adr/README.md)** — client package
  decisions
- **[MCP server ADRs](katana_mcp_server/docs/adr/README.md)** — MCP package decisions
- **[TypeScript client ADRs](packages/katana-client/docs/adr/README.md)** — TS package
  decisions

### Shared Documentation

- **[Contributing Guide](docs/CONTRIBUTING.md)** — how to contribute
- **[uv Usage Guide](docs/UV_USAGE.md)** — package manager guide
- **[Monorepo Release Guide](docs/MONOREPO_SEMANTIC_RELEASE.md)** — semantic release
  setup

## Development

### Prerequisites

- **Python 3.12+** for Python packages
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
