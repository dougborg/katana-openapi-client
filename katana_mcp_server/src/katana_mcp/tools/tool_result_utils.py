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
    **extra_template_vars: Any,
) -> ToolResult:
    """Create a ToolResult with both markdown and structured content.

    Args:
        response: Pydantic model response from the tool
        template_name: Name of the markdown template (without .md extension)
        **extra_template_vars: Additional variables for template rendering
            that aren't in the response model

    Returns:
        ToolResult with:
        - content: Markdown rendered from template
        - structured_content: Dict from Pydantic model

    Example:
        response = PurchaseOrderResponse(order_number="PO-001", ...)
        return make_tool_result(
            response,
            "order_created",
            created_at=datetime.now().isoformat(),
        )
    """
    # Get structured data from Pydantic model
    structured_data = response.model_dump()

    # Merge response data with extra template variables
    template_vars = {**structured_data, **extra_template_vars}

    # Render markdown from template
    try:
        markdown = format_template(template_name, **template_vars)
    except (FileNotFoundError, KeyError) as e:
        # Fallback to structured data as markdown if template fails
        markdown = f"# Response\n\n```json\n{response.model_dump_json(indent=2)}\n```\n\nTemplate error: {e}"

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
