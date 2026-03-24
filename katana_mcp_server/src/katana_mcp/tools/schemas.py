"""Shared schemas for Katana MCP tools.

This module contains Pydantic models and helpers that are shared across multiple
tool modules to ensure consistency and avoid duplication.
"""

from enum import StrEnum

from fastmcp import Context
from pydantic import BaseModel, Field


class ConfirmationSchema(BaseModel):
    """Schema for user confirmation via elicitation.

    This schema is used with FastMCP's `ctx.elicit()` to request explicit
    user confirmation before executing destructive operations.

    Attributes:
        confirm: Boolean indicating whether the user confirms the action
    """

    confirm: bool = Field(..., description="Confirm the action (true to proceed)")


class ConfirmationResult(StrEnum):
    """Result of a confirmation request."""

    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    DECLINED = "declined"


async def require_confirmation(context: Context, message: str) -> ConfirmationResult:
    """Request user confirmation via elicitation.

    Encapsulates the common elicitation pattern used across all confirm-mode tools.

    Args:
        context: FastMCP context for elicitation
        message: Confirmation message to display

    Returns:
        ConfirmationResult indicating user's decision
    """
    elicit_result = await context.elicit(message, ConfirmationSchema)

    if elicit_result.action != "accept":
        return ConfirmationResult.CANCELLED

    if not elicit_result.data.confirm:
        return ConfirmationResult.DECLINED

    return ConfirmationResult.CONFIRMED


__all__ = ["ConfirmationResult", "ConfirmationSchema", "require_confirmation"]
