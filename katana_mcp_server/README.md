# Katana MCP Server

A Model Context Protocol (MCP) server for Katana Manufacturing ERP, enabling natural
language interactions with your Katana instance through Claude Code and other MCP
clients.

## Features

- **12 Core Tools**: Covering inventory, sales orders, purchase orders, and manufacturing
  operations
- **Resource Endpoints**: Read-only access to Katana data
- **Workflow Prompts**: Pre-built templates for common manufacturing scenarios
- **Production Ready**: Built on
  [katana-openapi-client](https://github.com/dougborg/katana-openapi-client) with
  automatic retries, rate limiting, and smart pagination

## Installation

### Using uvx (Recommended)

```bash
uvx katana-mcp-server
```

### Using pip

```bash
pip install katana-mcp-server
python -m katana_mcp
```

## Configuration

### Claude Code

Add to your Claude Code MCP settings (`.claude/config.json`):

```json
{
  "mcpServers": {
    "katana-erp": {
      "command": "uvx",
      "args": ["katana-mcp-server"],
      "env": {
        "KATANA_API_KEY": "your-api-key-here",
        "KATANA_BASE_URL": "https://api.katanamrp.com/v1"
      }
    }
  }
}
```

### Environment Variables

- `KATANA_API_KEY` (required): Your Katana API key
- `KATANA_BASE_URL` (optional): API base URL (defaults to
  `https://api.katanamrp.com/v1`)

## Quick Start

Once configured in Claude Code, you can interact with your Katana instance using natural
language:

```
Check inventory levels for SKU-12345
```

```
Create a sales order for customer ACME Corp with 10 units of SKU-12345
```

```
Show me all active manufacturing orders
```

## Available Tools

### Inventory Management

- `check_inventory` - Check stock levels for a specific SKU
- `list_low_stock_items` - Find products below reorder point
- `search_products` - Search products by name or SKU

### Sales Orders

- `create_sales_order` - Create a new sales order
- `get_sales_order_status` - Get order details and status
- `list_recent_sales_orders` - List recent sales orders

### Purchase Orders

- `create_purchase_order` - Create a new purchase order
- `get_purchase_order_status` - Get PO details and status
- `receive_purchase_order` - Mark PO as received

### Manufacturing

- `create_manufacturing_order` - Create a manufacturing order
- `get_manufacturing_order_status` - Get MO details and status
- `list_active_manufacturing_orders` - List in-progress MOs

## Development

This package is part of the
[katana-openapi-client](https://github.com/dougborg/katana-openapi-client) monorepo.

### Setup

```bash
# Clone the repository
git clone https://github.com/dougborg/katana-openapi-client
cd katana-openapi-client

# Install dependencies
uv sync --all-extras

# Run tests
uv run poe test
```

### Running Locally

```bash
# From the repository root
uv run python -m katana_mcp
```

## Documentation

- **Main Documentation**:
  [https://dougborg.github.io/katana-openapi-client/](https://dougborg.github.io/katana-openapi-client/)
- **Architecture Decision Records**:
  [docs/adr/0010-katana-mcp-server.md](../docs/adr/0010-katana-mcp-server.md)
- **Implementation Plan**:
  [docs/mcp-server/IMPLEMENTATION_PLAN.md](../docs/mcp-server/IMPLEMENTATION_PLAN.md)
- **Agent Quick Start**:
  [docs/mcp-server/AGENT_QUICK_START.md](../docs/mcp-server/AGENT_QUICK_START.md)

## Requirements

- Python 3.11, 3.12, or 3.13
- Katana Manufacturing ERP API key
- MCP-compatible client (e.g., Claude Code)

## Version Compatibility

This MCP server requires `katana-openapi-client>=0.21.0`. See the
[compatibility matrix](../README.md#version-compatibility) for details.

## License

MIT License - see [LICENSE](../LICENSE) for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/dougborg/katana-openapi-client/issues)
- **Discussions**:
  [GitHub Discussions](https://github.com/dougborg/katana-openapi-client/discussions)

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.
