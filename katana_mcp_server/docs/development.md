# MCP Server Development Guide

This guide explains how to set up a fast, productive development workflow for the Katana
MCP Server using hot-reload capabilities.

## Prerequisites

1. **Install uv** (if not already installed):

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

   Or see
   [uv installation docs](https://docs.astral.sh/uv/getting-started/installation/)

1. **Python 3.12+** (for hot-reload mode)

1. **Find your uv path**: Run `which uv` (usually `~/.local/bin/uv`)

## Quick Start

### Development Mode (Hot Reload)

The **fastest way** to develop MCP tools with instant feedback:

```bash
cd katana_mcp_server

# 1. Install dependencies
uv sync

# 2. Install mcp-hmr (requires Python 3.12+)
uv pip install mcp-hmr

# 3. Run server with hot reload
uv run mcp-hmr katana_mcp.server:mcp
```

**Result**: Edit code → Save → See changes instantly in Claude Desktop. No rebuild, no
reinstall, no restart needed!

**Note**: `mcp-hmr` requires Python >=3.12. If you're on Python 3.11, use production
mode for testing or upgrade to Python 3.12+.

### Production Mode (Standard Install)

For release testing and production use:

```bash
# Build and install via pipx
cd katana_mcp_server
uv build
pipx install --force dist/katana_mcp_server-*.whl
```

## Development vs Production Modes

| Feature            | Development Mode           | Production Mode             |
| ------------------ | -------------------------- | --------------------------- |
| **Command**        | `uv run mcp-hmr ...`       | `katana-mcp-server`         |
| **Hot Reload**     | ✅ Yes - instant changes   | ❌ No - requires rebuild    |
| **Setup Time**     | ~5 seconds                 | ~5-10 minutes               |
| **Use Case**       | Rapid iteration, debugging | Release testing, deployment |
| **Python Version** | Requires >=3.12            | Supports >=3.11             |
| **Installation**   | Run from source            | Installed via pipx/pip      |

## Claude Desktop Configuration

You can configure Claude Desktop to support both modes simultaneously.

### Configuration File Location

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

### Example Configuration

```json
{
  "mcpServers": {
    "katana-erp-dev": {
      "command": "/absolute/path/to/katana-openapi-client/.venv/bin/mcp-hmr",
      "args": ["katana_mcp.server:mcp"],
      "cwd": "/absolute/path/to/katana-openapi-client/katana_mcp_server",
      "env": {
        "KATANA_API_KEY": "your-api-key-here"
      }
    },
    "katana-erp": {
      "command": "katana-mcp-server",
      "env": {
        "KATANA_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

**Important**:

- Replace `/absolute/path/to/` with your actual repository path
- The `.venv/bin/mcp-hmr` executable is created when you run `uv pip install mcp-hmr`
- On Windows, use `.venv\\Scripts\\mcp-hmr.exe` instead

### Switching Between Modes

- **Development**: Use `@katana-erp-dev` in Claude Desktop
- **Production**: Use `@katana-erp` in Claude Desktop
- Both can be enabled at the same time

**Tip**: Use development mode while coding, then test against production mode before
creating a PR.

## Development Workflow

### Typical Iteration Cycle

```bash
# 1. Start development server (once)
cd katana_mcp_server
uv run mcp-hmr katana_mcp.server:mcp

# 2. Use the MCP server in Claude Desktop
#    - Chat with Claude
#    - Test your tools
#    - Notice a bug or want to add a feature

# 3. Edit code in your editor
#    - Modify src/katana_mcp/tools/inventory.py
#    - Add logging, fix bugs, improve error handling
#    - Save the file

# 4. Test immediately in Claude Desktop
#    - No restart needed!
#    - Try the tool again
#    - See your changes instantly

# 5. Iterate until satisfied
#    - Keep editing and saving
#    - Changes apply in real-time
```

### What Gets Hot-Reloaded?

✅ **Reloads automatically**:

- Tool implementations (`src/katana_mcp/tools/*.py`)
- Helper functions
- Request/response models
- Business logic

❌ **Requires restart**:

- `server.py` changes (FastMCP initialization)
- Lifespan context changes
- New dependencies in `pyproject.toml`

### Adding Debug Logging

Hot reload makes debugging much faster:

```python
# Before (in src/katana_mcp/tools/inventory.py)
async def _check_inventory_impl(request: CheckInventoryRequest, context: Context) -> StockInfo:
    server_context = context.request_context.lifespan_context
    client = server_context.client
    product = await client.inventory.check_stock(request.sku)
    # ... rest of function

# After (add logging - save file - test immediately!)
import logging
logger = logging.getLogger(__name__)

async def _check_inventory_impl(request: CheckInventoryRequest, context: Context) -> StockInfo:
    logger.debug(f"Context structure: {dir(context)}")  # See what's available
    logger.debug(f"Request context: {dir(context.request_context)}")  # Debug paths

    server_context = context.request_context.lifespan_context
    client = server_context.client

    logger.info(f"Checking stock for SKU: {request.sku}")  # Track calls
    product = await client.inventory.check_stock(request.sku)
    logger.info(f"Found product: {product.name if product else 'Not found'}")
    # ... rest of function
```

Save → Test in Claude Desktop → See logs immediately!

## How mcp-hmr Works

**mcp-hmr** (Model Context Protocol Hot Module Replacement) provides:

1. **Fine-grained reloading**: Only reloads changed modules, not the entire process
1. **Preserved state**: Keeps connections alive, database pools intact
1. **Fast feedback**: See changes in seconds, not minutes
1. **Standard Python**: Uses importlib machinery, no magic

### Technical Details

- Watches file system for changes to `.py` files
- Uses Python's import hooks to reload modified modules
- Preserves the FastMCP server instance and lifespan context
- Updates tool registrations without restarting the server

## Testing Your Changes

### Unit Tests (Always Run First)

```bash
# Run tests before committing
uv run poe test

# Pre-commit hooks will also run tests automatically
git commit -m "feat(mcp): add new inventory tool"
```

### Integration Testing Workflow

1. **Development mode**: Iterate rapidly with hot reload
1. **Production mode**: Verify the installed package works
1. **Claude Desktop**: Test actual tool usage
1. **Automated tests**: Ensure everything passes

```bash
# After development, test the full cycle
uv run poe test                    # Unit tests pass
uv build                           # Build package
pipx install --force dist/*.whl    # Install for real
# Test in Claude Desktop with production config
```

## Troubleshooting

### Hot Reload Not Working

**Problem**: Changes don't appear after saving

**Solutions**:

1. Check that you saved the file
1. Verify `mcp-hmr` is installed: `uv run --extra dev mcp-hmr --version`
1. Look for error messages in the terminal running the server
1. Some changes (like `server.py`) require a full restart

### Module Import Errors

**Problem**: `ModuleNotFoundError` or `ImportError`

**Solutions**:

1. Ensure you're running from the correct directory: `cd katana_mcp_server`
1. Verify dependencies are installed: `uv sync --extra dev`
1. Check that the file path in the command is correct: `src/katana_mcp/server.py:mcp`

### Claude Desktop Not Finding Server

**Problem**: MCP server doesn't appear in Claude Desktop

**Solutions**:

1. Verify `claude_desktop_config.json` path is correct
1. Check JSON syntax (use a validator if needed)
1. Restart Claude Desktop after config changes
1. Verify `cwd` path is absolute and correct
1. Check that `KATANA_API_KEY` is set in env

### Permission Errors

**Problem**: `PermissionError` when running server

**Solutions**:

1. Ensure the repository directory is writable
1. Check that `.env` file has correct permissions
1. On Unix: `chmod 600 .env` to secure API key file

## Best Practices

### 1. Use Development Mode for All Coding

```bash
# Start dev server once, keep it running all day
uv run mcp-hmr katana_mcp.server:mcp
```

### 2. Test in Production Mode Before PR

```bash
# Before creating a PR, verify production install
uv build
pipx install --force dist/*.whl
# Test in Claude Desktop with production config
```

### 3. Keep Tests Passing

```bash
# Pre-commit hooks run automatically, but you can run manually:
uv run poe test          # Just tests
uv run poe check         # Full validation (lint + test + format)
```

### 4. Use Descriptive Logging

```python
# Good: Helps debug issues
logger.info(f"Processing inventory check for SKU: {request.sku}")
logger.debug(f"Client config: base_url={client.base_url}, timeout={client.timeout}")
logger.warning(f"SKU not found: {request.sku}, returning empty stock")

# Bad: Not helpful
logger.info("Doing a thing")
logger.debug("Debug message")
```

### 5. Structure for Testability

```python
# Good: Separate implementation from FastMCP decorator
async def _check_inventory_impl(request, context) -> StockInfo:
    \"\"\"Implementation with full business logic.\"\"\"
    # ... implementation

@mcp.tool()
async def check_inventory(request, context) -> StockInfo:
    \"\"\"FastMCP tool wrapper - minimal logic here.\"\"\"
    return await _check_inventory_impl(request, context)
```

This allows testing `_check_inventory_impl` directly with mocks.

## Additional Resources

- **FastMCP Docs**: https://github.com/jlowin/fastmcp
- **mcp-hmr GitHub**: https://github.com/mizchi/mcp-hmr
- **MCP Specification**: https://modelcontextprotocol.io
- **Project README**:
  [../katana_mcp_server/README.md](../../katana_mcp_server/README.md)
- **Testing Guide**: [Client Testing Guide](../../katana_public_api_client/docs/testing.md)

## Getting Help

- **Issues**: https://github.com/dougborg/katana-openapi-client/issues
- **Discussions**: https://github.com/dougborg/katana-openapi-client/discussions
- **MCP Community**: https://discord.gg/modelcontextprotocol

______________________________________________________________________

**Happy coding! 🚀** The hot-reload workflow will dramatically speed up your development
iteration time.
