"""Test the transport-level auto-pagination functionality."""

import json
from unittest.mock import MagicMock, patch

import httpx
import pytest

from katana_public_api_client.katana_client import ResilientAsyncTransport


class TestTransportAutoPagination:
    """Test the transport layer auto-pagination."""

    @pytest.fixture
    def transport(self):
        """Create a transport instance for testing."""
        return ResilientAsyncTransport(
            max_retries=3,
            max_pages=5,
        )

    @pytest.mark.asyncio
    async def test_auto_pagination_detected(self, transport):
        """Test that auto-pagination is triggered for GET requests with pagination params."""
        # Create a GET request with pagination parameters
        request = httpx.Request(
            method="GET", url="https://api.example.com/products?page=1&limit=10"
        )

        # Mock the _handle_paginated_request method to verify it's called
        with patch.object(transport, "_handle_paginated_request") as mock_paginated:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_paginated.return_value = mock_response

            response = await transport.handle_async_request(request)

            # Should call the paginated handler
            mock_paginated.assert_called_once_with(request)
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_no_auto_pagination_for_non_get(self, transport):
        """Test that auto-pagination is NOT triggered for non-GET requests."""
        # Create a POST request with pagination parameters
        request = httpx.Request(
            method="POST", url="https://api.example.com/products?page=1&limit=10"
        )

        # Mock the _handle_single_request method to verify it's called instead
        with patch.object(transport, "_handle_single_request") as mock_single:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_single.return_value = mock_response

            response = await transport.handle_async_request(request)

            # Should call the single request handler
            mock_single.assert_called_once_with(request)
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_no_auto_pagination_without_params(self, transport):
        """Test that auto-pagination is NOT triggered for GET requests without pagination params."""
        # Create a GET request without pagination parameters
        request = httpx.Request(method="GET", url="https://api.example.com/products")

        # Mock the _handle_single_request method to verify it's called instead
        with patch.object(transport, "_handle_single_request") as mock_single:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_single.return_value = mock_response

            response = await transport.handle_async_request(request)

            # Should call the single request handler
            mock_single.assert_called_once_with(request)
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_auto_pagination_combines_pages(self, transport):
        """Test that auto-pagination correctly combines multiple pages."""
        # Create a GET request with pagination parameters
        request = httpx.Request(
            method="GET", url="https://api.example.com/products?limit=2"
        )

        # Mock the parent's handle_async_request to return different pages
        page_responses = []

        # Page 1
        page1_data = {"data": [{"id": 1}, {"id": 2}]}
        page1_response = MagicMock()
        page1_response.status_code = 200
        page1_response.json.return_value = page1_data
        page1_response.headers = {"X-Total-Pages": "2", "X-Current-Page": "1"}
        page_responses.append(page1_response)

        # Page 2
        page2_data = {"data": [{"id": 3}]}
        page2_response = MagicMock()
        page2_response.status_code = 200
        page2_response.json.return_value = page2_data
        page2_response.headers = {"X-Total-Pages": "2", "X-Current-Page": "2"}
        page_responses.append(page2_response)

        with patch.object(
            httpx.AsyncHTTPTransport, "handle_async_request"
        ) as mock_parent:
            mock_parent.side_effect = page_responses

            response = await transport.handle_async_request(request)

            # Should have made 2 requests (one for each page)
            assert mock_parent.call_count == 2

            # Should return a combined response
            assert response.status_code == 200

            # Parse the combined response
            combined_data = json.loads(response.content.decode())
            assert "data" in combined_data
            assert len(combined_data["data"]) == 3  # 2 + 1 items
            assert combined_data["data"] == [{"id": 1}, {"id": 2}, {"id": 3}]

            # Should include pagination metadata
            assert "pagination" in combined_data
            assert combined_data["pagination"]["auto_paginated"] is True
            assert combined_data["pagination"]["total_items"] == 3

    @pytest.mark.asyncio
    async def test_auto_pagination_respects_max_pages(self, transport):
        """Test that auto-pagination respects the max_pages limit."""
        # Create a GET request with pagination parameters
        request = httpx.Request(
            method="GET", url="https://api.example.com/products?limit=1"
        )

        # Mock responses that would go beyond max_pages
        def create_page_response(page_num):
            page_data = {"data": [{"id": page_num}]}
            page_response = MagicMock()
            page_response.status_code = 200
            page_response.json.return_value = page_data
            page_response.headers = {
                "X-Total-Pages": "10",
                "X-Current-Page": str(page_num),
            }
            return page_response

        # Create more responses than max_pages allows
        page_responses = [create_page_response(i) for i in range(1, 11)]

        with patch.object(
            httpx.AsyncHTTPTransport, "handle_async_request"
        ) as mock_parent:
            mock_parent.side_effect = page_responses

            response = await transport.handle_async_request(request)

            # Should have stopped at max_pages (5)
            assert mock_parent.call_count == 5

            # Parse the combined response
            combined_data = json.loads(response.content.decode())
            assert len(combined_data["data"]) == 5  # Limited by max_pages

    @pytest.mark.asyncio
    async def test_auto_pagination_stops_on_error(self, transport):
        """Test that auto-pagination stops when it encounters an error."""
        # Create a GET request with pagination parameters
        request = httpx.Request(
            method="GET", url="https://api.example.com/products?limit=2"
        )

        # Page 1 succeeds, Page 2 fails (with retries)
        page1_data = {"data": [{"id": 1}, {"id": 2}]}
        page1_response = MagicMock()
        page1_response.status_code = 200
        page1_response.json.return_value = page1_data
        page1_response.headers = {"X-Total-Pages": "3", "X-Current-Page": "1"}

        page2_response = MagicMock()
        page2_response.status_code = 500  # Error on page 2

        with patch.object(
            httpx.AsyncHTTPTransport, "handle_async_request"
        ) as mock_parent:
            # Page 1 succeeds, then 4 retries for page 2 (3 max_retries + 1 initial attempt)
            mock_parent.side_effect = [
                page1_response,
                page2_response,
                page2_response,
                page2_response,
                page2_response,
            ]

            response = await transport.handle_async_request(request)

            # Should have made 5 requests total (1 for page 1, 4 attempts for page 2)
            assert mock_parent.call_count == 5

            # Should return the error response (not combined)
            assert response.status_code == 500
