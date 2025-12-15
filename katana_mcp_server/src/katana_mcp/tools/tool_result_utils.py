"""Utilities for creating ToolResult responses with template rendering.

This module provides helpers for converting Pydantic response models
to FastMCP ToolResult objects with both:
- Human-readable markdown content (from templates)
- Machine-readable structured content (from Pydantic model)

This dual-output approach provides:
- Type safety via Pydantic validation
- Clean markdown for AI/human readability
- Structured JSON for programmatic access
- Backward compatibility with all MCP clients
"""

from typing import Any

from fastmcp.tools.tool import ToolResult
from pydantic import BaseModel

from katana_mcp.templates import format_template


def make_tool_result(
    response: BaseModel,
    template_name: str,
    **template_vars: Any,
) -> ToolResult:
    """Create a ToolResult with both markdown and structured content.

    The structured_content always comes from the Pydantic model (response.model_dump()).
    The template_vars are used ONLY for template rendering and override/extend
    the response fields as needed for display formatting.

    Args:
        response: Pydantic model response from the tool (used for structured_content)
        template_name: Name of the markdown template (without .md extension)
        **template_vars: Variables for template rendering. These can include:
            - Formatted versions of response fields (e.g., prices as "$1,234.56")
            - Computed fields (e.g., bullet lists from arrays)
            - Additional context not in the response model

    Returns:
        ToolResult with:
        - content: Markdown rendered from template using template_vars
        - structured_content: Dict from Pydantic model (unmodified)

    Example:
        response = PurchaseOrderResponse(order_number="PO-001", total_cost=1500.0, ...)
        return make_tool_result(
            response,
            "order_created",
            # Override total_cost with formatted version for display
            total_cost=1500.0,  # Template uses ${total_cost:,.2f}
            currency="USD",
            # Add computed field not in response
            next_actions_text="- Review order\\n- Track shipment",
        )
    """
    # Get structured data from Pydantic model (always unmodified)
    structured_data = response.model_dump()

    # Render markdown from template using provided vars
    try:
        markdown = format_template(template_name, **template_vars)
    except (FileNotFoundError, KeyError) as e:
        # Fallback to structured data as markdown if template fails
        markdown = (
            f"# Response\n\n```json\n{response.model_dump_json(indent=2)}\n```\n\n"
            f"Template error: {e}"
        )

    return ToolResult(
        content=markdown,
        structured_content=structured_data,
    )


def make_simple_result(
    message: str,
    structured_data: dict[str, Any] | None = None,
) -> ToolResult:
    """Create a simple ToolResult with a message.

    For simple responses where a full template isn't needed.

    Args:
        message: The message to display
        structured_data: Optional structured data dict

    Returns:
        ToolResult with message as content
    """
    return ToolResult(
        content=message,
        structured_content=structured_data or {},
    )
