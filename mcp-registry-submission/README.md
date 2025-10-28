# Docker MCP Registry Submission

This directory contains the submission files for publishing the Katana MCP server to the
Docker MCP Registry.

## Directory Structure

```
servers/katana-erp/
├── server.yaml       # Server metadata and configuration
└── tools.json        # Tool definitions
```

## Submission Process

### 1. Fork and Clone docker/mcp-registry

```bash
# Fork https://github.com/docker/mcp-registry on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/mcp-registry.git
cd mcp-registry
```

### 2. Copy Submission Files

```bash
# Copy the entire katana-erp directory to the registry
cp -r /path/to/katana-openapi-client/mcp-registry-submission/servers/katana-erp \
      servers/
```

### 3. Update Commit Hash

Before submitting, update the `commit` field in `server.yaml` to the latest commit hash
from the main branch:

```bash
# Get the latest commit hash
git rev-parse HEAD

# Edit servers/katana-erp/server.yaml and replace "HEAD" with the actual commit hash
```

### 4. Create Pull Request

```bash
# Create a new branch
git checkout -b add-katana-erp-server

# Add and commit
git add servers/katana-erp/
git commit -m "feat: add Katana Manufacturing ERP MCP server"

# Push to your fork
git push origin add-katana-erp-server

# Create PR on GitHub targeting docker/mcp-registry:main
```

### 5. PR Description Template

```markdown
## Summary

Add Katana Manufacturing ERP MCP server to the registry.

## Server Details

- **Name**: katana-erp
- **Category**: productivity
- **Tags**: manufacturing, erp, inventory, production, orders
- **Repository**: https://github.com/dougborg/katana-openapi-client

## Tools Provided

1. **check_inventory** - Check stock levels for specific products
2. **list_low_stock_items** - Identify products below stock threshold
3. **search_products** - Search products by name or SKU

## License

MIT License (compatible with Docker MCP Registry)

## Testing

The server has been tested with:
- Claude Desktop on macOS
- Docker container builds
- Integration tests with Katana API

## Documentation

- Main README: https://github.com/dougborg/katana-openapi-client/blob/main/README.md
- MCP Server README:
https://github.com/dougborg/katana-openapi-client/blob/main/katana_mcp_server/README.md
- Docker Guide:
https://github.com/dougborg/katana-openapi-client/blob/main/katana_mcp_server/DOCKER.md
```

## Files Description

### server.yaml

Server metadata including:

- **Metadata**: Name, category, tags, description
- **Source**: GitHub repository and commit hash
- **Configuration**: Required environment variables (KATANA_API_KEY, KATANA_BASE_URL)
- **Docker**: Image name (mcp/katana-erp)

### tools.json

Tool definitions for the three inventory management tools currently available:

1. `check_inventory` - Check stock levels for a specific SKU
1. `list_low_stock_items` - List products below threshold
1. `search_products` - Search for products

## Timeline

- **After PR #73 merges**: Update commit hash to latest
- **Review period**: Docker typically reviews within 24-48 hours
- **Publication**: Available on Docker MCP Catalog within 24 hours of approval

## Security Notes

The Docker-built image will include:

- Cryptographic signatures
- Provenance tracking
- Software Bill of Materials (SBOM)
- Published to `mcp/katana-erp` on Docker Hub

## References

- Docker MCP Registry: https://github.com/docker/mcp-registry
- Contributing Guide: https://github.com/docker/mcp-registry/blob/main/CONTRIBUTING.md
- MCP Specification: https://modelcontextprotocol.io/
