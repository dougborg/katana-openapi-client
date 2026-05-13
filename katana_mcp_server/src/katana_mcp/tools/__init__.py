"""MCP tools for Katana Manufacturing ERP.

Tools are organized into two layers:

- **Foundation** (``tools/foundation/``) — thin, single-purpose tools organized by
  Katana domain (catalog, items, inventory, orders, purchase / sales / manufacturing
  orders, stock transfers, customers, reference data, reporting, corrections, cache
  admin). See the directory listing for the canonical surface; the live tool list
  is also exposed at the ``katana://help/tools`` resource.
- **Workflows** (``tools/workflows/``) — planned extension layer for multi-step
  intent-based compositions on top of foundation tools. Currently a stub
  (``register_all_workflow_tools`` is a no-op).

Cross-cutting tool infrastructure lives directly under ``tools/`` — ``prefab_ui.py``,
``tool_result_utils.py``, ``decorators.py``, and the ``_modification`` / ``_reopen``
/ ``_derived_fields`` / ``list_coercion`` helpers consumed by foundation modules.

Each foundation/workflow module exports a ``register_tools(mcp)`` function that
registers its tools with the FastMCP instance (avoids circular imports). For the
tool interface pattern (pydantic ``Request`` / ``Response`` models, the
``@unpack_pydantic_params`` decorator, the preview/apply elicitation flow), see
[ADR-0016](../../../docs/adr/0016-tool-interface-pattern.md) and the architecture
guide at ``katana_mcp_server/docs/architecture.md``.
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
