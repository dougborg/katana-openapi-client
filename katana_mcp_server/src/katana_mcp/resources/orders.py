"""Order resources for Katana MCP Server.

Provides read-only access to order data including sales orders, purchase orders,
and manufacturing orders.
"""

# NOTE: Do not use 'from __future__ import annotations' in this module
# FastMCP requires Context to be the actual class, not a string annotation

from fastmcp import FastMCP


def register_resources(mcp: FastMCP) -> None:
    """Register all order resources with the FastMCP instance.

    Args:
        mcp: FastMCP server instance to register resources with
    """
    # Resources will be registered here as they are implemented
    pass


__all__ = ["register_resources"]
