"""Shared pytest fixtures for MCP server tests."""

import os
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio


@pytest_asyncio.fixture
async def katana_context():
    """Create a mock context for integration tests that uses real KatanaClient.

    This fixture is used by integration tests to get a context with a real
    KatanaClient initialized from environment variables.

    The fixture requires KATANA_API_KEY to be set in the environment.
    If not set, integration tests will be skipped.

    Returns:
        Mock context object with request_context.lifespan_context.client
        pointing to a real KatanaClient instance.
    """
    # Check if API key is available
    api_key = os.getenv("KATANA_API_KEY")
    if not api_key:
        pytest.skip("KATANA_API_KEY not set - skipping integration test")

    # Import here to avoid import errors if client isn't installed
    try:
        from katana_public_api_client import KatanaClient
    except ImportError:
        pytest.skip("katana_public_api_client not installed")

    # Create mock context structure matching FastMCP
    context = MagicMock()
    mock_request_context = MagicMock()
    mock_lifespan_context = MagicMock()

    # Initialize real KatanaClient
    base_url = os.getenv("KATANA_BASE_URL", "https://api.katanamrp.com/v1")
    client = KatanaClient(
        api_key=api_key,
        base_url=base_url,
        timeout=30.0,
        max_retries=3,  # Fewer retries for tests
        max_pages=10,  # Limit pages for tests
    )

    # Attach client to mock context
    mock_lifespan_context.client = client
    mock_request_context.lifespan_context = mock_lifespan_context
    context.request_context = mock_request_context

    yield context

    # Note: KatanaClient cleanup is handled automatically


# ============================================================================
# Fixtures for tool tests (merged from tests/tools/conftest.py)
# ============================================================================


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
