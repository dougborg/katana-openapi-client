"""Test the transport-level auto-pagination functionality."""

import json
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from katana_public_api_client.katana_client import PaginationTransport


class TestTransportAutoPagination:
    """Test the transport layer auto-pagination.

    Auto-pagination behavior:
    - ON by default for all GET requests
    - Disabled when extensions={"auto_pagination": False}
    - Only applies to GET requests (POST, PUT, etc. are never paginated)
    """

    @pytest.fixture
    def mock_wrapped_transport(self):
        """Create a mock wrapped transport."""
        return AsyncMock(spec=httpx.AsyncHTTPTransport)

    @pytest.fixture
    def transport(self, mock_wrapped_transport):
        """Create a pagination transport instance for testing."""
        return PaginationTransport(
            wrapped_transport=mock_wrapped_transport,
            max_pages=5,
        )

    @pytest.mark.asyncio
    async def test_auto_pagination_on_by_default(
        self, transport, mock_wrapped_transport
    ):
        """Test that auto-pagination is ON by default for all GET requests."""
        # Create mock responses for 2 pages
        page1_data = {
            "data": [{"id": 1}, {"id": 2}],
            "pagination": {"page": 1, "total_pages": 2},
        }
        page2_data = {
            "data": [{"id": 3}],
            "pagination": {"page": 2, "total_pages": 2},
        }

        def create_response(data):
            mock_resp = MagicMock(spec=httpx.Response)
            mock_resp.status_code = 200
            mock_resp.json.return_value = data
            mock_resp.headers = {}

            async def mock_aread():
                pass

            mock_resp.aread = mock_aread
            return mock_resp

        page1_response = create_response(page1_data)
        page2_response = create_response(page2_data)

        mock_wrapped_transport.handle_async_request.side_effect = [
            page1_response,
            page2_response,
        ]

        # Create a GET request - auto-pagination is ON by default
        request = httpx.Request(
            method="GET",
            url="https://api.example.com/products",
        )

        response = await transport.handle_async_request(request)

        # Should have called wrapped transport twice (once per page)
        assert mock_wrapped_transport.handle_async_request.call_count == 2

        # Response should combine both pages
        combined_data = json.loads(response.content)
        assert len(combined_data["data"]) == 3
        assert combined_data["pagination"]["auto_paginated"] is True

    @pytest.mark.asyncio
    async def test_auto_pagination_disabled_via_extension(
        self, transport, mock_wrapped_transport
    ):
        """Test that auto-pagination can be disabled via extensions."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_wrapped_transport.handle_async_request.return_value = mock_response

        # Create a GET request with auto_pagination disabled via extensions
        request = httpx.Request(
            method="GET",
            url="https://api.example.com/products",
            extensions={"auto_pagination": False},
        )

        response = await transport.handle_async_request(request)

        # Should call wrapped transport only once (no pagination)
        mock_wrapped_transport.handle_async_request.assert_called_once()
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_no_auto_pagination_for_non_get(
        self, transport, mock_wrapped_transport
    ):
        """Test that auto-pagination is NOT triggered for non-GET requests."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_wrapped_transport.handle_async_request.return_value = mock_response

        # Create a POST request - should never be paginated
        request = httpx.Request(
            method="POST",
            url="https://api.example.com/products",
        )

        response = await transport.handle_async_request(request)

        # Should call wrapped transport only once (no pagination)
        mock_wrapped_transport.handle_async_request.assert_called_once()
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_no_auto_pagination_with_explicit_page_param(
        self, transport, mock_wrapped_transport
    ):
        """Test that auto-pagination is disabled when page param is explicit."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_wrapped_transport.handle_async_request.return_value = mock_response

        # Explicit page=2 should NOT trigger auto-pagination
        request = httpx.Request(
            method="GET",
            url="https://api.example.com/products?page=2&limit=50",
        )

        response = await transport.handle_async_request(request)

        # Should call wrapped transport only once (no pagination)
        mock_wrapped_transport.handle_async_request.assert_called_once()
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_single_page_response_returns_data(
        self, transport, mock_wrapped_transport
    ):
        """Test that GET requests without pagination info return data correctly."""
        # Response has no pagination info - should return as single page
        single_page_data = {
            "data": [{"id": 1}, {"id": 2}],
        }

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = single_page_data
        mock_response.headers = {}

        async def mock_aread():
            pass

        mock_response.aread = mock_aread
        mock_wrapped_transport.handle_async_request.return_value = mock_response

        request = httpx.Request(
            method="GET",
            url="https://api.example.com/products",
        )

        response = await transport.handle_async_request(request)

        # Should call wrapped transport only once
        mock_wrapped_transport.handle_async_request.assert_called_once()

        # Response should contain the original data
        response_data = json.loads(response.content)
        assert len(response_data["data"]) == 2

    @pytest.mark.asyncio
    async def test_auto_pagination_stops_on_error(
        self, transport, mock_wrapped_transport
    ):
        """Test that pagination stops when an error response is encountered."""
        # First request succeeds, second request fails
        page1_data = {
            "data": [{"id": 1}],
            "pagination": {"page": 1, "total_pages": 3},
        }

        def create_success_response(data):
            mock_resp = MagicMock(spec=httpx.Response)
            mock_resp.status_code = 200
            mock_resp.json.return_value = data
            mock_resp.headers = {}

            async def mock_aread():
                pass

            mock_resp.aread = mock_aread
            return mock_resp

        page1_response = create_success_response(page1_data)

        # Page 2 returns an error
        page2_response = MagicMock(spec=httpx.Response)
        page2_response.status_code = 500

        mock_wrapped_transport.handle_async_request.side_effect = [
            page1_response,
            page2_response,
        ]

        request = httpx.Request(
            method="GET",
            url="https://api.example.com/products",
        )

        response = await transport.handle_async_request(request)

        # Should have made 2 requests (page 1 success, page 2 error)
        assert mock_wrapped_transport.handle_async_request.call_count == 2

        # Should return the error response
        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_max_items_limits_total_items(
        self, transport, mock_wrapped_transport
    ):
        """Test that max_items limits total items collected."""

        # Create mock responses for 3 pages with 10 items each
        def create_page_data(page_num, items_per_page=10):
            return {
                "data": [
                    {"id": i}
                    for i in range(
                        (page_num - 1) * items_per_page + 1,
                        page_num * items_per_page + 1,
                    )
                ],
                "pagination": {"page": page_num, "total_pages": 3},
            }

        def create_response(data):
            mock_resp = MagicMock(spec=httpx.Response)
            mock_resp.status_code = 200
            mock_resp.json.return_value = data
            mock_resp.headers = {}

            async def mock_aread():
                pass

            mock_resp.aread = mock_aread
            return mock_resp

        # Setup responses for all 3 pages
        mock_wrapped_transport.handle_async_request.side_effect = [
            create_response(create_page_data(1)),
            create_response(create_page_data(2)),
            create_response(create_page_data(3)),
        ]

        # Request with max_items=15 - should collect page 1 (10) + partial page 2 (5)
        request = httpx.Request(
            method="GET",
            url="https://api.example.com/products?limit=10",
            extensions={"max_items": 15},
        )

        response = await transport.handle_async_request(request)

        # Should have made only 2 requests (smart limit adjustment)
        assert mock_wrapped_transport.handle_async_request.call_count == 2

        # Response should contain exactly 15 items
        combined_data = json.loads(response.content)
        assert len(combined_data["data"]) == 15

    @pytest.mark.asyncio
    async def test_max_items_adjusts_limit_on_last_request(
        self, transport, mock_wrapped_transport
    ):
        """Test that limit is reduced on the last page to avoid over-fetching."""

        def create_response(data):
            mock_resp = MagicMock(spec=httpx.Response)
            mock_resp.status_code = 200
            mock_resp.json.return_value = data
            mock_resp.headers = {}

            async def mock_aread():
                pass

            mock_resp.aread = mock_aread
            return mock_resp

        # We'll capture the requests to verify the limit was adjusted
        captured_requests = []

        async def capture_request(req):
            captured_requests.append(req)
            # Return page data based on which page was requested
            page = int(req.url.params.get("page", 1))
            limit = int(req.url.params.get("limit", 10))
            data = {
                "data": [{"id": i} for i in range(1, limit + 1)],
                "pagination": {"page": page, "total_pages": 3},
            }
            return create_response(data)

        mock_wrapped_transport.handle_async_request.side_effect = capture_request

        # Request with limit=10 and max_items=15
        # After page 1 (10 items), should request only 5 items on page 2
        request = httpx.Request(
            method="GET",
            url="https://api.example.com/products?limit=10",
            extensions={"max_items": 15},
        )

        await transport.handle_async_request(request)

        # Verify that the second request had limit=5
        assert len(captured_requests) == 2
        assert captured_requests[1].url.params.get("limit") == "5"
