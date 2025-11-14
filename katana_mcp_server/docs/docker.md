# Docker MCP Server Guide

This guide covers building, testing, and submitting the Katana MCP Server to the Docker
MCP Catalog.

## Pre-built Images

Pre-built multi-platform (amd64/arm64) images are automatically published to GitHub
Container Registry on each release:

```bash
# Pull the latest version
docker pull ghcr.io/dougborg/katana-mcp-server:latest

# Or pull a specific version
docker pull ghcr.io/dougborg/katana-mcp-server:0.1.0
```

## Building the Docker Image

### Local Build

```bash
cd katana_mcp_server
docker build -t katana-mcp-server:latest .
```

### Multi-platform Build (for registry)

```bash
docker buildx build --platform linux/amd64,linux/arm64 \
  -t your-registry/katana-mcp-server:latest \
  --push .
```

## Running Locally

### Using Docker Compose

```bash
# Set your API key
export KATANA_API_KEY="your-api-key-here"

# Start the server
docker-compose up
```

### Using Docker Run

```bash
docker run -it \
  -e KATANA_API_KEY="your-api-key-here" \
  katana-mcp-server:latest
```

## Testing the Container

```bash
# Run with test API key
docker run -it \
  -e KATANA_API_KEY="test-key" \
  katana-mcp-server:latest

# Should show:
# - Server initialization logs
# - Ready message
# - Listening for MCP requests on stdio
```

## Docker MCP Catalog Submission

### Prerequisites

1. **GitHub Repository**: Code must be in a public GitHub repository
1. **Working Dockerfile**: Tested and verified locally
1. **Documentation**: README with clear setup instructions
1. **License**: Open source license (MIT in our case)

### Generating Tool Metadata

To generate `tools.json` for Docker MCP Registry submission:

```bash
# Generate to stdout
python scripts/generate_tools_json.py

# Generate to file
python scripts/generate_tools_json.py -o tools.json

# Generate with pretty formatting
python scripts/generate_tools_json.py -o tools.json --pretty
```

The script automatically introspects the FastMCP server to extract tool metadata,
ensuring the tools list stays synchronized with actual implementations.

#### Example Output

```json
[
  {
    "name": "check_inventory",
    "description": "Check stock levels for a specific product SKU."
  },
  {
    "name": "create_purchase_order",
    "description": "Create a purchase order with two-step confirmation."
  },
  {
    "name": "search_items",
    "description": "Search for items by name or SKU."
  }
]
```

#### CI/CD Integration

The script can be run in CI/CD to verify tool metadata is accurate:

```yaml
# In .github/workflows/ci.yml
- name: Generate tools.json
  run: python scripts/generate_tools_json.py -o tools.json --pretty

- name: Verify tools.json is up to date
  run: |
    git diff --exit-code tools.json || {
      echo "tools.json is out of date. Run: python scripts/generate_tools_json.py -o tools.json --pretty"
      exit 1
    }
```

### Submission Process

1. **Fork the MCP Registry**: https://github.com/docker/mcp-registry

1. **Create Submission File**: Add `katana-mcp-server.yml` to the registry

1. **Submit Pull Request**: Follow the CONTRIBUTING guide

### Recommended Approach: Docker-Built

We recommend the **Docker-built** option because:

- ✅ Docker builds and signs the image
- ✅ Automatic security scanning and updates
- ✅ Provenance tracking and SBOMs
- ✅ Published to `mcp/katana-mcp-server` namespace

### Submission File Format

```yaml
name: katana-mcp-server
title: Katana Manufacturing ERP
description: MCP server for interacting with Katana Manufacturing ERP API
repository: https://github.com/dougborg/katana-openapi-client
dockerfile_path: katana_mcp_server/Dockerfile
version: 0.1.0
license: MIT
author: Doug Borg
tags:
  - manufacturing
  - erp
  - inventory
  - orders
categories:
  - business
  - manufacturing
build_type: docker-built  # Docker will build and maintain
```

## Configuration in Claude Desktop

Once published to the Docker MCP Catalog, users can configure it in Claude Desktop:

```json
{
  "mcpServers": {
    "katana": {
      "command": "docker",
      "args": ["run", "-i", "--rm",
               "-e", "KATANA_API_KEY=your-key-here",
               "mcp/katana-mcp-server:latest"]
    }
  }
}
```

## Security Considerations

- ✅ Non-root user (UID 1000)
- ✅ Minimal base image (python:3.13-slim)
- ✅ No unnecessary packages
- ✅ API key passed via environment variable (never hardcoded)
- ✅ Resource limits in docker-compose

## Timeline

- **Submission**: Create PR in mcp-registry
- **Review**: Docker team reviews (typically 1-2 days)
- **Approval**: Available within 24 hours of approval
- **Availability**:
  - Docker MCP Catalog *(link pending official catalog launch)*
  - Docker Desktop MCP Toolkit
  - One-click connection in Claude Desktop

## Resources

- [MCP Registry GitHub](https://github.com/docker/mcp-registry)
- [Docker MCP Documentation](https://docs.docker.com/ai/mcp-catalog-and-toolkit/)
- Docker MCP Catalog *(URL will be provided when officially available)*
