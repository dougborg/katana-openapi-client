"""Reference data tool wrappers for Katana MCP Server.

These tools expose the same cached reference data as the
``katana://locations`` / ``katana://suppliers`` / ``katana://tax-rates`` /
``katana://operators`` / ``katana://additional-costs`` resources, but as
``tools/list`` entries so LLM agents discover them through the surface
they reach for first.

Each tool is a thin wrapper around the corresponding resource handler in
``katana_mcp.resources.reference`` — same cache, same shape, same data.
The duplication is intentional: ``tools/list`` is what LLMs scan; making
reference data discoverable there closes a long-standing gap where agents
would fall back to the Katana web UI or ask the user for IDs that the
server already had cached locally.

(``list_items`` is intentionally **not** exposed here — ``search_items``
already covers the catalog surface.)
"""

# NOTE: Do not use 'from __future__ import annotations' in this module.
# FastMCP requires Context to be the actual class, not a string annotation —
# matching the convention used in ``katana_mcp.resources.reference``.

import json

from fastmcp import Context, FastMCP
from fastmcp.tools import ToolResult

from katana_mcp.logging import observe_tool
from katana_mcp.resources.reference import (
    get_additional_costs,
    get_locations,
    get_operators,
    get_suppliers,
    get_tax_rates,
)


async def _to_tool_result(payload: str) -> ToolResult:
    """Wrap a resource's JSON-string payload as a ``ToolResult``.

    The resource handlers return ``str`` (JSON-serialized); ``ToolResult``
    needs both a ``content`` string and ``structured_content`` dict, so we
    parse once and feed both. Exposing the parsed dict as
    ``structured_content`` lets downstream tools / aggregations consume the
    payload without re-parsing.
    """
    return ToolResult(
        content=payload,
        structured_content=json.loads(payload),
    )


# ============================================================================
# list_locations — wraps katana://locations
# ============================================================================


@observe_tool
async def list_locations(context: Context) -> ToolResult:
    """List all warehouses and facilities. Returns each location's id, name,
    address, and primary flag. Use the `id` value when creating orders or
    filtering inventory queries.

    This is the tool surface for the `katana://locations` resource; both
    return the same cache-backed data.
    """
    payload = await get_locations(context)
    return await _to_tool_result(payload)


# ============================================================================
# list_suppliers — wraps katana://suppliers
# ============================================================================


@observe_tool
async def list_suppliers(context: Context) -> ToolResult:
    """List all suppliers. Returns each supplier's id, name, contact info,
    and currency. Use the `id` value when creating purchase orders or setting
    a default supplier on a material.

    This is the tool surface for the `katana://suppliers` resource; both
    return the same cache-backed data.
    """
    payload = await get_suppliers(context)
    return await _to_tool_result(payload)


# ============================================================================
# list_tax_rates — wraps katana://tax-rates
# ============================================================================


@observe_tool
async def list_tax_rates(context: Context) -> ToolResult:
    """List all configured tax rates. Returns each tax rate's id, name, rate,
    display name, and default-for-sales / default-for-purchases flags. Use
    the `id` value when creating sales orders or purchase-order line items
    with explicit tax assignments.

    This is the tool surface for the `katana://tax-rates` resource; both
    return the same cache-backed data.
    """
    payload = await get_tax_rates(context)
    return await _to_tool_result(payload)


# ============================================================================
# list_operators — wraps katana://operators
# ============================================================================


@observe_tool
async def list_operators(context: Context) -> ToolResult:
    """List all manufacturing operators. Returns each operator's id and name.
    Use the `id` value when assigning operators to manufacturing-order
    operation rows or naming the packer on a sales order.

    This is the tool surface for the `katana://operators` resource; both
    return the same cache-backed data.
    """
    payload = await get_operators(context)
    return await _to_tool_result(payload)


# ============================================================================
# list_additional_costs — wraps katana://additional-costs
# ============================================================================


@observe_tool
async def list_additional_costs(context: Context) -> ToolResult:
    """List the additional-cost catalog (freight, duties, handling fees, etc.).
    Returns each entry's id and name. Use the `id` value when calling
    `modify_purchase_order` with `add_additional_costs=[...]`. Pair with
    `list_tax_rates` for the matching `tax_rate_id`.

    This is the tool surface for the `katana://additional-costs` resource;
    both return the same cache-backed data.
    """
    payload = await get_additional_costs(context)
    return await _to_tool_result(payload)


# ============================================================================
# Registration
# ============================================================================


def register_tools(mcp: FastMCP) -> None:
    """Register reference-data list tools with the FastMCP instance."""
    from mcp.types import ToolAnnotations

    _read = ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    )

    mcp.tool(tags={"reference", "read"}, annotations=_read)(list_locations)
    mcp.tool(tags={"reference", "read"}, annotations=_read)(list_suppliers)
    mcp.tool(tags={"reference", "read"}, annotations=_read)(list_tax_rates)
    mcp.tool(tags={"reference", "read"}, annotations=_read)(list_operators)
    mcp.tool(tags={"reference", "read"}, annotations=_read)(list_additional_costs)


__all__ = ["register_tools"]
