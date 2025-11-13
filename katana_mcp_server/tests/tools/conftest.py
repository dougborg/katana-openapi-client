"""Shared pytest fixtures for MCP tool tests."""

from unittest.mock import AsyncMock, MagicMock

import pytest


def create_mock_context(elicit_confirm: bool = True):
    """Create a mock context with proper FastMCP structure.

    Args:
        elicit_confirm: If True, elicit() returns an accepted result with confirm=True.
                       If False, elicit() returns a declined result.

    Returns:
        Tuple of (context, lifespan_context) where context has the structure:
        context.request_context.lifespan_context.client

    This helper creates the nested mock structure that FastMCP uses to provide
    the KatanaClient to tool implementations, and includes a mock for context.elicit()
    that simulates user confirmation behavior.
    """
    context = MagicMock()
    mock_request_context = MagicMock()
    mock_lifespan_context = MagicMock()
    context.request_context = mock_request_context
    mock_request_context.lifespan_context = mock_lifespan_context

    # Mock elicit() to simulate user confirmation
    mock_elicit_result = MagicMock()
    if elicit_confirm:
        mock_elicit_result.action = "accept"
        mock_elicit_result.data = MagicMock()
        mock_elicit_result.data.confirm = True
    else:
        mock_elicit_result.action = "decline"
        mock_elicit_result.data = None

    context.elicit = AsyncMock(return_value=mock_elicit_result)

    return context, mock_lifespan_context


@pytest.fixture
def mock_context():
    """Fixture providing a mock FastMCP context.

    Returns:
        Tuple of (context, lifespan_context) ready for test use.
    """
    return create_mock_context()


@pytest.fixture
def mock_get_purchase_order():
    """Fixture for mocking get_purchase_order API call."""
    from katana_public_api_client.api.purchase_order import (
        get_purchase_order as api_get_purchase_order,
    )

    mock_api = AsyncMock()
    api_get_purchase_order.asyncio_detailed = mock_api
    return mock_api


@pytest.fixture
def mock_receive_purchase_order():
    """Fixture for mocking receive_purchase_order API call."""
    from katana_public_api_client.api.purchase_order import (
        receive_purchase_order as api_receive_purchase_order,
    )

    mock_api = AsyncMock()
    api_receive_purchase_order.asyncio_detailed = mock_api
    return mock_api
