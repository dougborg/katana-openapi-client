"""Shared schemas for Katana MCP tools.

This module contains Pydantic models that are shared across multiple tool modules
to ensure consistency and avoid duplication.
"""

from pydantic import BaseModel, Field


class ConfirmationSchema(BaseModel):
    """Schema for user confirmation via elicitation.

    This schema is used with FastMCP's `ctx.elicit()` to request explicit
    user confirmation before executing destructive operations.

    Attributes:
        confirm: Boolean indicating whether the user confirms the action
    """

    confirm: bool = Field(..., description="Confirm the action (true to proceed)")


__all__ = ["ConfirmationSchema"]
