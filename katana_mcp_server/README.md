# Katana MCP Server

[![PyPI](https://img.shields.io/pypi/v/katana-mcp-server.svg)](https://pypi.org/project/katana-mcp-server/)

Model Context Protocol (MCP) server for Katana Manufacturing ERP.

## Features

- **Inventory Management**: Check stock, find low stock items, search items, get variant
  details
- **Catalog Management**: Create products and materials
- **Order Management**: Create, modify, and fulfill purchase orders, sales orders, and
  manufacturing orders; correct shipped builds
- **Document Verification**: Verify supplier documents against purchase orders
- **Preview / Apply Pattern**: Two-step confirmation for every write operation — preview
  returns a Prefab UI card with Confirm/Cancel; apply executes
- **Environment-based Authentication**: Secure API key management
- **Built-in Resilience**: Automatic retries, rate limiting, and pagination via Python
  client
- **Type Safety**: Pydantic models for all requests and responses
- **Typed SQLite Cache**: Local mirror of catalog _and_ transactional entities (items,
  suppliers, customers, locations, sales / purchase / manufacturing orders, stock
  transfers and adjustments) with FTS5 fuzzy search, soft-state filtering, and
  cold-cache recovery — see [docs/typed_cache/](docs/typed_cache/README.md)

## Installation

```bash
pip install katana-mcp-server
```

## Quick Start

### 1. Get Your Katana API Key

Obtain your API key from your Katana account settings.

### 2. Configure Environment

Create a `.env` file or set environment variable:

```bash
export KATANA_API_KEY=your-api-key-here
```

Or create `.env` file:

```
KATANA_API_KEY=your-api-key-here
KATANA_BASE_URL=https://api.katanamrp.com/v1  # Optional, uses default if not set
```

### 3. Choose Your Transport

The MCP server supports multiple transport protocols for different environments:

| Transport         | Use Case                          | Command                                         |
| ----------------- | --------------------------------- | ----------------------------------------------- |
| `stdio` (default) | Claude Desktop, Claude Code       | `katana-mcp-server`                             |
| `streamable-http` | Claude.ai co-work, remote clients | `katana-mcp-server --transport streamable-http` |
| `sse`             | Cursor IDE                        | `katana-mcp-server --transport sse`             |
| `http`            | Generic HTTP clients              | `katana-mcp-server --transport http`            |

### 4. Use with Claude Desktop (stdio)

Add to your Claude Desktop configuration
(`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

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

Restart Claude Desktop, and you'll see Katana inventory tools available!

### 5. Use with Claude.ai Co-work (streamable-http)

Claude.ai requires **HTTPS** and a **publicly reachable URL**. For local development,
use a tunnel like [ngrok](https://ngrok.com):

```bash
# Terminal 1: Start the MCP server with hot-reload
uv run poe dev

# Terminal 2: Create an HTTPS tunnel
ngrok http 8765
# → Gives you https://abc123.ngrok-free.app
```

Then in Claude.ai:

1. Go to **Customize > Connectors**
1. Select **"Add custom connector"**
1. Paste your ngrok HTTPS URL (e.g., `https://abc123.ngrok-free.app`)

For production, deploy the Docker image behind a reverse proxy with TLS:

```bash
docker run -p 8765:8765 -e KATANA_API_KEY=your-key ghcr.io/dougborg/katana-mcp-server:latest
```

### 6. Run Standalone (Optional)

For testing or development:

```bash
export KATANA_API_KEY=your-api-key
katana-mcp-server
```

## Available Tools and Resources

The server's tool surface covers inventory, catalog, orders (sales / purchase /
manufacturing), stock movement, fulfillment, corrections, and reporting — plus resources
for cached reference data and a built-in help system.

**The live, always-current tool and resource lists are exposed by the server itself:**

- **`katana://help`** — workflow overview and quick reference
- **`katana://help/tools`** — every registered tool with its parameters and docstring
- **`katana://help/resources`** — every registered resource

These resources are the authoritative source — reach for them rather than any
hand-maintained list, which would drift on every release. From an MCP host (Claude
Desktop, Claude.ai, etc.) the tool list also shows up in the host's UI once the server
is connected, and `mcp inspect` / `fastmcp dev` give the same view from the command
line.

Every write tool follows the preview / apply pattern: calling with `preview=true` (the
default) returns a Prefab UI card with Confirm/Cancel buttons; calling with
`preview=false` executes. The destructive-hint annotation also signals to the host to
ask the user before invocation. See [`docs/prefab/README.md`](docs/prefab/README.md) for
the card pattern details.

## Configuration

### Environment Variables

- `KATANA_API_KEY` (required): Your Katana API key
- `KATANA_BASE_URL` (optional): API base URL (default: https://api.katanamrp.com/v1)
- `KATANA_MCP_LOG_LEVEL` (optional): Log level - DEBUG, INFO, WARNING, ERROR (default:
  INFO)
- `KATANA_MCP_LOG_FORMAT` (optional): Log format - json, text (default: json)

### Endpoint Authentication (HTTP transport)

When using HTTP transport, the MCP endpoint is **unauthenticated by default**. Set one
of the following to secure it:

**Bearer token** (simple, for dev/personal use):

```bash
export MCP_AUTH_TOKEN=your-secret-token
```

Clients must send `Authorization: Bearer your-secret-token` with each request. In
Claude.ai, enter the token in the connector's Advanced Settings.

**GitHub OAuth** (production):

```bash
export MCP_GITHUB_CLIENT_ID=your-github-client-id
export MCP_GITHUB_CLIENT_SECRET=your-github-client-secret
export MCP_BASE_URL=https://your-public-url.ngrok-free.app
```

Create a GitHub OAuth App at https://github.com/settings/developers with the callback
URL set to `<MCP_BASE_URL>/auth/callback`.

Auth is **not required** for stdio transport (local only).

### Logging Configuration

The server uses structured logging with configurable output format and verbosity:

**Development (verbose text logs):**

```bash
export KATANA_MCP_LOG_LEVEL=DEBUG
export KATANA_MCP_LOG_FORMAT=text
katana-mcp-server
```

**Production (structured JSON logs):**

```bash
export KATANA_MCP_LOG_LEVEL=INFO
export KATANA_MCP_LOG_FORMAT=json
katana-mcp-server
```

See [docs/LOGGING.md](docs/LOGGING.md) for complete logging documentation.

### Advanced Configuration

The server uses the
[katana-openapi-client](https://pypi.org/project/katana-openapi-client/) library with:

- Automatic retries on rate limits (429) and server errors (5xx)
- Exponential backoff with jitter
- Transparent pagination for large result sets
- 30-second default timeout

## Troubleshooting

### "KATANA_API_KEY environment variable is required"

**Cause**: API key not set in environment.

**Solution**: Set the environment variable or add to `.env` file:

```bash
export KATANA_API_KEY=your-api-key-here
```

### "Authentication error: 401 Unauthorized"

**Cause**: Invalid or expired API key.

**Solution**: Verify your API key in Katana account settings and update the environment
variable.

### Tools not showing up in Claude Desktop

**Cause**: Configuration error or server not starting.

**Solutions**:

1. Check Claude Desktop logs: `~/Library/Logs/Claude/mcp*.log`
1. Verify configuration file syntax (valid JSON)
1. Test server standalone: `katana-mcp-server` (should start without errors)
1. Restart Claude Desktop after configuration changes

### Rate limiting (429 errors)

**Cause**: Too many requests to Katana API.

**Solution**: The server automatically retries with exponential backoff. If you see
persistent rate limiting, reduce request frequency.

## Development

### Prerequisites

- **uv** package manager -
  [Install uv](https://docs.astral.sh/uv/getting-started/installation/)
- **Python 3.12+** (for hot-reload mode)

### Development Mode with Hot Reload ⚡

For **rapid iteration** during development, use hot-reload mode to see changes instantly
without rebuilding or restarting:

```bash
# 1. Install dependencies
cd katana_mcp_server
uv sync

# 2. Install mcp-hmr (requires Python 3.12+)
uv pip install mcp-hmr

# 3. Run with hot reload
uv run mcp-hmr src/katana_mcp/server.py:mcp
```

**Benefits**:

- Edit code → Save → Changes apply instantly
- No rebuild, no reinstall, no restart needed
- Keep your Claude Desktop conversation context
- Iteration time: ~5 seconds instead of 5-10 minutes

**Claude Desktop Configuration for Development**:

```json
{
  "mcpServers": {
    "katana-erp-dev": {
      "comment": "Use full path to uv - find with: which uv",
      "command": "/Users/YOUR_USERNAME/.local/bin/uv",
      "args": ["run", "mcp-hmr", "src/katana_mcp/server.py:mcp"],
      "cwd": "/absolute/path/to/katana-openapi-client/katana_mcp_server",
      "env": {
        "KATANA_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

**Important**:

- Replace `YOUR_USERNAME` with your actual username
- Run `which uv` to find the correct uv path (usually `~/.local/bin/uv`)
- Replace `/absolute/path/to/` with your repository path
- Hot reload requires Python >=3.12. For Python 3.11 users, use the production install
  method.

See [docs/development.md](docs/development.md) for the complete development guide.

### Install from Source

```bash
git clone https://github.com/dougborg/katana-openapi-client.git
cd katana-openapi-client/katana_mcp_server
uv sync
```

### Run Tests

```bash
# Unit tests only (no API key needed)
uv run pytest tests/ -m "not integration"

# All tests (requires KATANA_API_KEY)
export KATANA_API_KEY=your-key
uv run pytest tests/
```

### Build and Install Locally

```bash
# Build the package
uv build

# Install with pipx
pipx install --force dist/katana_mcp_server-*.whl
```

## Links

- **Documentation**: https://github.com/dougborg/katana-openapi-client
- **Issue Tracker**: https://github.com/dougborg/katana-openapi-client/issues
- **PyPI**: https://pypi.org/project/katana-mcp-server/
- **Katana API**: https://help.katanamrp.com/api/overview

## License

MIT License - see LICENSE file for details
