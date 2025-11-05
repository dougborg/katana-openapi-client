"""MCP tools for Katana Manufacturing ERP.

This module contains tool implementations organized into foundation and workflow layers.

Tool Organization:
-----------------
- **Foundation tools** (tools/foundation/): Low-level operations mapping to API endpoints
  - items.py: Search and manage items (variants, products, materials, services)
  - inventory.py: Stock checking, low stock alerts, inventory operations

- **Workflow tools** (tools/workflows/): High-level intent-based operations
  - Coming in Phase 3

Tool Registration Pattern:
--------------------------
Each tool module exports a register_tools(mcp) function that registers its tools
with the FastMCP instance. This avoids circular imports.

When adding new tool modules:
1. Create the new module (e.g., foundation/purchase_orders.py)
2. Define tools as regular async functions (no decorators)
3. Add a register_tools(mcp: FastMCP) function that calls mcp.tool() on each function
4. Import and call the registration function from foundation/__init__.py or workflows/__init__.py
"""

from fastmcp import FastMCP

from .foundation import register_all_foundation_tools
from .workflows import register_all_workflow_tools


def register_all_tools(mcp: FastMCP) -> None:
    """Register all tools from all modules (foundation + workflow).

    Args:
        mcp: FastMCP server instance to register tools with
    """
    register_all_foundation_tools(mcp)
    register_all_workflow_tools(mcp)


__all__ = [
    "register_all_tools",
]
