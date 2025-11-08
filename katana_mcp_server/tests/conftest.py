"""Shared pytest fixtures for MCP server tests."""

import os
from unittest.mock import MagicMock

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
