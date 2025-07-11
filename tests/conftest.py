"""Test configuration and fixtures for the Katana OpenAPI Client test suite."""

import os
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from katana_public_api_client import KatanaClient


@pytest.fixture
def mock_api_credentials():
    """Provide mock API credentials for testing."""
    return {
        "api_key": "test-api-key-12345",
        "base_url": "https://api.test.katana.example.com",
    }


@pytest.fixture
def katana_client(mock_api_credentials):
    """Create a KatanaClient for testing."""
    return KatanaClient(**mock_api_credentials)


@pytest.fixture
def katana_client_limited_pages(mock_api_credentials):
    """Create a KatanaClient with limited pagination for testing."""
    return KatanaClient(max_pages=5, **mock_api_credentials)


@pytest.fixture
def mock_transport_handler():
    """Create a mock transport handler that can be customized per test."""

    def handler(request: httpx.Request) -> httpx.Response:
        # Default successful response
        return httpx.Response(200, json={"data": [{"id": 1, "name": "Test"}]})

    return handler


@pytest.fixture
def mock_transport(mock_transport_handler):
    """Create a MockTransport instance."""
    return httpx.MockTransport(mock_transport_handler)


@pytest.fixture
def katana_client_with_mock_transport(mock_api_credentials, mock_transport):
    """Create a KatanaClient with MockTransport for testing."""
    # Create a KatanaClient
    client = KatanaClient(**mock_api_credentials)

    # Create a new httpx client with the mock transport and base_url
    mock_httpx_client = httpx.AsyncClient(
        transport=mock_transport, base_url=mock_api_credentials["base_url"]
    )

    # Replace the authenticated client's async client
    client._client._async_client = mock_httpx_client

    return client


@pytest.fixture
def mock_response():
    """Create a mock successful response."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {}
    mock_resp.parsed = MagicMock()
    mock_resp.parsed.data = [{"id": 1, "name": "Test Product"}]
    return mock_resp


@pytest.fixture
def mock_paginated_responses():
    """Create mock responses for pagination testing."""
    import json

    # Page 1: Full page
    page1 = MagicMock()
    page1.status_code = 200
    page1.parsed.data = [{"id": i, "name": f"Product {i}"} for i in range(1, 251)]
    page1.headers = {
        "X-Pagination": json.dumps(
            {
                "total_records": "274",
                "total_pages": "2",
                "offset": "0",
                "page": "1",
                "first_page": "true",
                "last_page": "false",
            }
        )
    }

    # Page 2: Partial page (indicates end)
    page2 = MagicMock()
    page2.status_code = 200
    page2.parsed.data = [{"id": i, "name": f"Product {i}"} for i in range(251, 275)]
    page2.headers = {
        "X-Pagination": json.dumps(
            {
                "total_records": "274",
                "total_pages": "2",
                "offset": "250",
                "page": "2",
                "first_page": "false",
                "last_page": "true",
            }
        )
    }

    return [page1, page2]


@pytest.fixture
def mock_rate_limited_response():
    """Create a mock rate-limited response."""
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_resp.headers = {"Retry-After": "60"}
    return mock_resp


@pytest.fixture
def mock_server_error_response():
    """Create a mock server error response."""
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    return mock_resp


# Environment setup for tests
@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch, request):
    """Set up test environment variables."""
    # Check if this is a real API test by looking for the integration marker
    # or if the test is in test_real_api.py
    is_real_api_test = (
        hasattr(request, "node") and "integration" in request.node.keywords
    ) or (hasattr(request, "module") and "test_real_api" in request.module.__name__)

    if is_real_api_test:
        # For real API tests, don't override existing environment variables
        # Only set defaults if they're not already set
        from dotenv import load_dotenv

        load_dotenv(override=False)  # Don't override existing env vars

        # Only set test defaults if real credentials aren't available
        if not os.getenv("KATANA_API_KEY"):
            monkeypatch.setenv("KATANA_API_KEY", "test-key")
        if not os.getenv("KATANA_BASE_URL"):
            monkeypatch.setenv("KATANA_BASE_URL", "https://api.katanamrp.com/v1")
    else:
        # For unit tests, use test values
        monkeypatch.setenv("KATANA_API_KEY", "test-key")
        monkeypatch.setenv("KATANA_BASE_URL", "https://api.test.katana.example.com")


# Async test utilities
@pytest.fixture
def async_mock():
    """Utility to create async mocks."""

    def _async_mock(*args, **kwargs):
        mock = AsyncMock(*args, **kwargs)
        return mock

    return _async_mock


def create_mock_paginated_response(
    page=1, data=None, is_last_page=False, total_pages=1
):
    """Helper function to create a properly formatted mock response with X-Pagination header."""
    import json

    if data is None:
        data = []

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.parsed = MagicMock()
    mock_response.parsed.data = data
    mock_response.headers = {
        "X-Pagination": json.dumps(
            {
                "total_records": str(len(data) * total_pages),
                "total_pages": str(total_pages),
                "offset": str((page - 1) * len(data)),
                "page": str(page),
                "first_page": "true" if page == 1 else "false",
                "last_page": "true" if is_last_page else "false",
            }
        )
    }
    return mock_response


def create_paginated_mock_handler(pages_data):
    """
    Create a mock handler that returns different responses for different pages.

    Args:
        pages_data: List of data for each page

    Returns:
        A handler function that can be used with MockTransport
    """
    import json

    def handler(request: httpx.Request) -> httpx.Response:
        # Parse the page parameter from the request
        page = int(request.url.params.get("page", 1))

        # Get the data for this page
        if page <= len(pages_data):
            data = pages_data[page - 1]
            is_last_page = page == len(pages_data)
        else:
            # Page doesn't exist
            return httpx.Response(404, json={"error": "Page not found"})

        # Create pagination headers
        headers = {
            "X-Pagination": json.dumps(
                {
                    "total_records": str(
                        sum(len(page_data) for page_data in pages_data)
                    ),
                    "total_pages": str(len(pages_data)),
                    "offset": str((page - 1) * len(data)),
                    "page": str(page),
                    "first_page": "true" if page == 1 else "false",
                    "last_page": "true" if is_last_page else "false",
                }
            )
        }

        return httpx.Response(200, json={"data": data}, headers=headers)

    return handler


def create_auto_paginated_mock_handler(all_items, page_size=50):
    """
    Create a mock handler that automatically paginates a list of items.

    Args:
        all_items: List of all items to paginate
        page_size: Number of items per page

    Returns:
        A handler function that can be used with MockTransport
    """
    import json
    import math

    total_pages = math.ceil(len(all_items) / page_size)

    def handler(request: httpx.Request) -> httpx.Response:
        # Parse the page parameter from the request
        page = int(request.url.params.get("page", 1))
        limit = int(request.url.params.get("limit", page_size))

        # Calculate slice indices
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit

        # Get the data for this page
        page_data = all_items[start_idx:end_idx]

        if not page_data and page > 1:
            # Page doesn't exist
            return httpx.Response(404, json={"error": "Page not found"})

        # Create pagination headers
        headers = {
            "X-Pagination": json.dumps(
                {
                    "total_records": str(len(all_items)),
                    "total_pages": str(total_pages),
                    "offset": str(start_idx),
                    "page": str(page),
                    "first_page": "true" if page == 1 else "false",
                    "last_page": "true" if page >= total_pages else "false",
                }
            )
        }

        return httpx.Response(200, json={"data": page_data}, headers=headers)

    return handler
