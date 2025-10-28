"""Katana Manufacturing ERP MCP Server.

This package provides a Model Context Protocol (MCP) server for the Katana
Manufacturing ERP system. It enables natural language interactions with Katana
through Claude Code and other MCP clients.

Key Features:
- 12 tools covering inventory, sales orders, purchase orders, and manufacturing
- Resource endpoints for read-only data access
- Workflow prompts for common manufacturing scenarios
- Built on katana-openapi-client with automatic retries and rate limiting

Example:
    Configure in Claude Code's MCP settings:

    ```json
    {
      "mcpServers": {
        "katana-erp": {
          "command": "uvx",
          "args": ["katana-mcp-server"],
          "env": {
            "KATANA_API_KEY": "your-api-key",
            "KATANA_BASE_URL": "https://api.katanamrp.com/v1"
          }
        }
      }
    }
    ```

For more information, see the documentation at:
https://dougborg.github.io/katana-openapi-client/
"""

from importlib.metadata import version

__version__ = version("katana-mcp-server")

__all__ = ["__version__"]
