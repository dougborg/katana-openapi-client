"""MCP prompts for Katana Manufacturing ERP.

Prompts provide guided multi-step workflow templates for common manufacturing
operations. They help LLMs structure the correct tool sequence for complex tasks.
"""

from fastmcp import FastMCP


def register_all_prompts(mcp: FastMCP) -> None:
    """Register all prompts with the FastMCP server instance.

    Args:
        mcp: FastMCP server instance to register prompts with
    """
    from .workflows import register_prompts as register_workflow_prompts

    register_workflow_prompts(mcp)


__all__ = ["register_all_prompts"]
