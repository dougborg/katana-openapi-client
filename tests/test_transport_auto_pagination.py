"""Test the transport-level auto-pagination functionality."""

import json
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from katana_public_api_client.katana_client import PaginationTransport


class TestTransportAutoPagination:
    """Test the transport layer auto-pagination."""

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
    async def test_auto_pagination_detected(self, transport, mock_wrapped_transport):
        """Test that auto-pagination is triggered for GET requests with pagination params."""
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

        # Create a real httpx.Request with pagination parameters
        request = httpx.Request(
            method="GET",
            url="https://api.example.com/products?page=1&limit=10",
        )

        response = await transport.handle_async_request(request)

        # Should have called wrapped transport twice (once per page)
        assert mock_wrapped_transport.handle_async_request.call_count == 2

        # Response should combine both pages
        combined_data = json.loads(response.content)
        assert len(combined_data["data"]) == 3
        assert combined_data["pagination"]["auto_paginated"] is True

    @pytest.mark.asyncio
    async def test_no_auto_pagination_for_non_get(
        self, transport, mock_wrapped_transport
    ):
        """Test that auto-pagination is NOT triggered for non-GET requests."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_wrapped_transport.handle_async_request.return_value = mock_response

        # Create a POST request with pagination parameters
        request = MagicMock(spec=httpx.Request)
        request.method = "POST"
        request.url = MagicMock()
        request.url.params = {"page": "1", "limit": "10"}

        response = await transport.handle_async_request(request)

        # Should call wrapped transport only once (no pagination)
        mock_wrapped_transport.handle_async_request.assert_called_once()
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_no_auto_pagination_without_params(
        self, transport, mock_wrapped_transport
    ):
        """Test that auto-pagination is NOT triggered for GET requests without pagination params."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_wrapped_transport.handle_async_request.return_value = mock_response

        # Create a GET request without pagination parameters
        request = MagicMock(spec=httpx.Request)
        request.method = "GET"
        request.url = MagicMock()
        request.url.params = {}

        response = await transport.handle_async_request(request)

        # Should call wrapped transport only once (no pagination)
        mock_wrapped_transport.handle_async_request.assert_called_once()
        assert response.status_code == 200

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
            url="https://api.example.com/products?limit=10",
        )

        response = await transport.handle_async_request(request)

        # Should have made 2 requests (page 1 success, page 2 error)
        assert mock_wrapped_transport.handle_async_request.call_count == 2

        # Should return the error response
        assert response.status_code == 500
