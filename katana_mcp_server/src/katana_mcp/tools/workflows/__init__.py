"""Workflow tools for Katana MCP Server.

Workflow tools are high-level operations that combine multiple foundation tools
to accomplish complex, intent-based tasks. They provide convenience for common
multi-step workflows.

Future modules:
- po_lifecycle.py: Purchase order creation and receiving workflows
- manufacturing.py: Manufacturing order workflows
- document_verification.py: Document verification and PO creation workflows
"""

from fastmcp import FastMCP


def register_all_workflow_tools(mcp: FastMCP) -> None:
    """Register all workflow tools from all modules.

    Args:
        mcp: FastMCP server instance to register tools with
    """
    # No workflow tools yet - Phase 3 implementation
    pass


__all__ = [
    "register_all_workflow_tools",
]
