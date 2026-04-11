"""Utilities for creating ToolResult responses with template rendering.

This module provides helpers for converting Pydantic response models
to FastMCP ToolResult objects with:
- Human-readable markdown content (from templates) for non-Prefab clients
- Machine-readable structured content (from Pydantic model) for programmatic access
- Prefab UI (via structuredContent) for Claude Desktop and other Prefab-capable hosts

When a PrefabApp is provided, it takes priority as structured_content. Claude Desktop
renders the Prefab UI; other clients fall back to markdown content.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from fastmcp.tools import ToolResult
from pydantic import BaseModel

from katana_mcp.templates import format_template

if TYPE_CHECKING:
    from prefab_ui.app import PrefabApp


def enum_to_str(value: Any) -> str | None:
    """Extract the string value from an enum, or return as-is.

    Handles the common case where an attrs model field may be a StrEnum,
    a plain string, or None. Pattern: `enum_to_str(status)` instead of
    `status.value if hasattr(status, "value") else status`.
    """
    if value is None:
        return None
    return value.value if hasattr(value, "value") else str(value)


def iso_or_none(dt: datetime | None) -> str | None:
    """Format a datetime as ISO 8601, or return None.

    Shorthand for `dt.isoformat() if dt else None`.
    """
    return dt.isoformat() if dt else None


def format_md_table(
    headers: list[str],
    rows: list[list[Any]],
) -> str:
    """Format a simple markdown table from headers and row data.

    Each row cell is rendered via str(); use "—" or "" for missing values.
    Returns an empty string if `rows` is empty.

    Example:
        format_md_table(
            ["Name", "Qty"],
            [["Apple", 3], ["Banana", 5]],
        )
    """
    if not rows:
        return ""
    header_line = "| " + " | ".join(headers) + " |"
    sep_line = "|" + "|".join("---" for _ in headers) + "|"
    body_lines = ["| " + " | ".join(str(cell) for cell in row) + " |" for row in rows]
    return "\n".join([header_line, sep_line, *body_lines])


def make_tool_result(
    response: BaseModel,
    template_name: str,
    *,
    ui: PrefabApp | None = None,
    **template_vars: Any,
) -> ToolResult:
    """Create a ToolResult with markdown, structured content, and optional Prefab UI.

    The structured_content is either:
    - A PrefabApp JSON envelope (if ``ui`` is provided) — rendered by Claude Desktop
    - The Pydantic model dict (fallback for programmatic access)

    Markdown content from templates is always included for non-Prefab clients.

    Args:
        response: Pydantic model response from the tool
        template_name: Name of the markdown template (without .md extension)
        ui: Optional PrefabApp to use as structured_content for Prefab-capable hosts
        **template_vars: Variables for template rendering

    Returns:
        ToolResult with markdown content and structured_content (Prefab or dict)
    """
    # Render markdown from template using provided vars
    try:
        markdown = format_template(template_name, **template_vars)
    except (FileNotFoundError, KeyError) as e:
        # Fallback to structured data as markdown if template fails
        markdown = (
            f"# Response\n\n```json\n{response.model_dump_json(indent=2)}\n```\n\n"
            f"Template error: {e}"
        )

    # When Prefab UI is provided, include both the UI envelope and the response
    # data so programmatic MCP clients can still access structured fields
    if ui is not None:
        prefab_json = ui.to_json()
        prefab_json["data"] = response.model_dump()
        structured_data = prefab_json
    else:
        structured_data = response.model_dump()

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
