"""Shared fixtures for integration tests.

These fixtures provide real KatanaClient instances for end-to-end testing.
All integration tests require KATANA_API_KEY environment variable.

TEST DATA ISOLATION:
All test data uses the "MCPTEST-<session_id>" namespace prefix for:
- Easy identification in the Katana UI
- Automatic cleanup after tests
- Isolation between concurrent test runs

See test_utils.py for the TestSession class and cleanup utilities.
"""

import os
import time
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from katana_public_api_client import KatanaClient

from .test_utils import TEST_NAMESPACE_PREFIX, TrackedTestSession, tracked_session


def pytest_configure(config):
    """Register custom markers for integration tests."""
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration test requiring API access",
    )
    config.addinivalue_line(
        "markers",
        "creates_data: mark test as creating real data in Katana (requires cleanup)",
    )


@pytest.fixture(scope="module")
def api_key():
    """Get API key from environment, skip if not available."""
    key = os.getenv("KATANA_API_KEY")
    if not key:
        pytest.skip("KATANA_API_KEY environment variable not set")
    return key


@pytest.fixture(scope="module")
def base_url():
    """Get base URL from environment or use default."""
    return os.getenv("KATANA_BASE_URL", "https://api.katanamrp.com/v1")


@pytest_asyncio.fixture(scope="function")
async def katana_client(api_key, base_url):
    """Create a real KatanaClient for integration tests.

    This fixture creates a new client for each test to ensure isolation.
    The client is configured with:
    - Reduced retries for faster test feedback
    - Limited pages to prevent excessive API calls
    - Standard timeout

    Yields:
        KatanaClient: Initialized client ready for API calls
    """
    async with KatanaClient(
        api_key=api_key,
        base_url=base_url,
        timeout=30.0,
        max_retries=2,  # Fewer retries for faster test feedback
        max_pages=5,  # Limit pages to prevent excessive API calls
    ) as client:
        yield client


@pytest_asyncio.fixture(scope="function")
async def integration_context(katana_client):
    """Create a mock FastMCP context with real KatanaClient.

    This fixture creates the nested mock structure that FastMCP uses
    to provide the KatanaClient to tool implementations.

    Structure:
        context.request_context.lifespan_context.client -> KatanaClient

    Also includes a mock elicit() function that simulates user confirmation.

    Yields:
        MagicMock: Context object with real KatanaClient attached
    """
    context = MagicMock()
    mock_request_context = MagicMock()
    mock_lifespan_context = MagicMock()

    # Attach real client to mock context
    mock_lifespan_context.client = katana_client
    mock_request_context.lifespan_context = mock_lifespan_context
    context.request_context = mock_request_context

    # Mock elicit() to simulate user confirmation (always accept)
    mock_elicit_result = MagicMock()
    mock_elicit_result.action = "accept"
    mock_elicit_result.data = MagicMock()
    mock_elicit_result.data.confirm = True
    context.elicit = AsyncMock(return_value=mock_elicit_result)

    yield context


# Test data generators for creating test entities
@pytest.fixture
def unique_sku():
    """Generate a unique SKU for test entities.

    Note: For tests that actually create data, use test_session.namespaced_sku()
    instead to ensure proper namespace isolation.

    Returns:
        str: SKU in format TEST-<timestamp> to avoid collisions
    """
    return f"TEST-{int(time.time() * 1000)}"


@pytest.fixture
def unique_order_number():
    """Generate a unique order number for test entities.

    Note: For tests that actually create data, use test_session.namespaced_order_number()
    instead to ensure proper namespace isolation.

    Returns:
        str: Order number in format TEST-PO-<timestamp>
    """
    return f"TEST-PO-{int(time.time() * 1000)}"


@pytest_asyncio.fixture(scope="function")
async def tracked_test_session(katana_client):
    """Create a test session with automatic resource tracking and cleanup.

    This fixture provides a TestSession that:
    - Generates namespaced identifiers (SKUs, order numbers, names)
    - Tracks all created resources
    - Automatically cleans up resources when the test completes

    Usage:
        async def test_create_product(tracked_test_session, integration_context):
            session = tracked_test_session
            sku = session.namespaced_sku("WIDGET-001")

            # Create the product (using your tool)
            result = await create_product(sku=sku, ...)

            # Track it for cleanup
            session.track(ResourceType.PRODUCT, result.id, sku)

            # Test assertions...

        # Resources are cleaned up automatically after test

    Yields:
        TrackedTestSession: Session object for tracking resources
    """
    async with tracked_session(katana_client) as session:
        yield session


# Re-export for convenience
__all__ = [
    "TEST_NAMESPACE_PREFIX",
    "TrackedTestSession",
    "tracked_session",
]
