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

    @pytest.mark.asyncio
    async def test_max_items_uses_default_page_size_when_no_limit(
        self, transport, mock_wrapped_transport
    ):
        """Test that max_items uses default page size (250) when no limit specified."""

        def create_response(data):
            mock_resp = MagicMock(spec=httpx.Response)
            mock_resp.status_code = 200
            mock_resp.json.return_value = data
            mock_resp.headers = {}

            async def mock_aread():
                pass

            mock_resp.aread = mock_aread
            return mock_resp

        # Capture requests to verify the limit used
        captured_requests = []

        async def capture_request(req):
            captured_requests.append(req)
            # Return page data
            limit = int(req.url.params.get("limit", 250))
            data = {
                "data": [{"id": i} for i in range(1, min(limit, 100) + 1)],
                "pagination": {"page": 1, "total_pages": 1},
            }
            return create_response(data)

        mock_wrapped_transport.handle_async_request.side_effect = capture_request

        # Request with max_items but NO limit parameter
        request = httpx.Request(
            method="GET",
            url="https://api.example.com/products",  # No limit param
            extensions={"max_items": 500},
        )

        await transport.handle_async_request(request)

        # First request should use min(default_page_size=250, remaining=500) = 250
        assert len(captured_requests) >= 1
        assert captured_requests[0].url.params.get("limit") == "250"

    @pytest.mark.asyncio
    async def test_max_items_respects_small_remaining_over_default(
        self, transport, mock_wrapped_transport
    ):
        """Test that max_items uses remaining items when smaller than default page size."""

        def create_response(data):
            mock_resp = MagicMock(spec=httpx.Response)
            mock_resp.status_code = 200
            mock_resp.json.return_value = data
            mock_resp.headers = {}

            async def mock_aread():
                pass

            mock_resp.aread = mock_aread
            return mock_resp

        # Capture requests to verify the limit used
        captured_requests = []

        async def capture_request(req):
            captured_requests.append(req)
            limit = int(req.url.params.get("limit", 250))
            data = {
                "data": [{"id": i} for i in range(1, min(limit, 50) + 1)],
                "pagination": {"page": 1, "total_pages": 1},
            }
            return create_response(data)

        mock_wrapped_transport.handle_async_request.side_effect = capture_request

        # Request with small max_items (less than default page size 250)
        request = httpx.Request(
            method="GET",
            url="https://api.example.com/products",  # No limit param
            extensions={"max_items": 50},
        )

        await transport.handle_async_request(request)

        # Should use min(default=250, remaining=50) = 50
        assert len(captured_requests) >= 1
        assert captured_requests[0].url.params.get("limit") == "50"


class TestPaginationHeaderValidation:
    """Test validation of pagination headers."""

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
    async def test_malformed_total_pages_header_handled_gracefully(
        self, transport, mock_wrapped_transport
    ):
        """Test that malformed X-Total-Pages header doesn't crash pagination."""
        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"data": [{"id": 1}]}
        # Malformed header value (non-numeric)
        mock_resp.headers = {"X-Total-Pages": "invalid"}

        async def mock_aread():
            pass

        mock_resp.aread = mock_aread
        mock_wrapped_transport.handle_async_request.return_value = mock_resp

        request = httpx.Request(
            method="GET",
            url="https://api.example.com/products",
        )

        # Should not raise ValueError, should gracefully handle malformed header
        response = await transport.handle_async_request(request)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_malformed_current_page_header_handled_gracefully(
        self, transport, mock_wrapped_transport
    ):
        """Test that malformed X-Current-Page header doesn't crash pagination."""
        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"data": [{"id": 1}]}
        # Malformed header value
        mock_resp.headers = {"X-Current-Page": "abc", "X-Total-Pages": "1"}

        async def mock_aread():
            pass

        mock_resp.aread = mock_aread
        mock_wrapped_transport.handle_async_request.return_value = mock_resp

        request = httpx.Request(
            method="GET",
            url="https://api.example.com/products",
        )

        # Should not raise ValueError
        response = await transport.handle_async_request(request)
        assert response.status_code == 200


class TestPaginationStringComparison:
    """Test that pagination correctly handles string values from JSON headers.

    The X-Pagination header returns values as strings (e.g., "page":"5", "total_pages":"41").
    Without proper conversion, string comparison "5" >= "41" returns True (lexicographic),
    causing pagination to stop prematurely at page 5 instead of continuing to page 41.
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
            max_pages=50,  # Higher limit to test multi-page scenarios
        )

    @pytest.mark.asyncio
    async def test_string_pagination_values_in_header_are_converted(
        self, transport, mock_wrapped_transport
    ):
        """Test that string pagination values in X-Pagination header are correctly converted.

        This reproduces the bug where "5" >= "41" (string comparison) is True,
        causing pagination to stop at page 5 instead of continuing to page 41.
        """
        pages_fetched = []

        def create_response(page_num, total_pages=10):
            """Create a response with string pagination values in X-Pagination header."""
            pages_fetched.append(page_num)
            mock_resp = MagicMock(spec=httpx.Response)
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"data": [{"id": page_num}]}
            # String values in X-Pagination header - this is what Katana API returns
            mock_resp.headers = {
                "X-Pagination": json.dumps(
                    {
                        "page": str(page_num),  # String "5" not integer 5
                        "total_pages": str(total_pages),  # String "10" not integer 10
                    }
                )
            }

            async def mock_aread():
                pass

            mock_resp.aread = mock_aread
            return mock_resp

        call_count = 0

        async def create_paginated_response(req):
            nonlocal call_count
            call_count += 1
            page = int(req.url.params.get("page", 1))
            return create_response(page, total_pages=10)

        mock_wrapped_transport.handle_async_request.side_effect = (
            create_paginated_response
        )

        request = httpx.Request(
            method="GET",
            url="https://api.example.com/products",
        )

        response = await transport.handle_async_request(request)

        # Should have fetched ALL 10 pages, not stopped early due to string comparison
        assert call_count == 10, (
            f"Expected 10 pages but only fetched {call_count}. "
            f"Pages fetched: {pages_fetched}. "
            "String comparison bug may be present if stopped at page 5 or less."
        )
        combined_data = json.loads(response.content)
        assert len(combined_data["data"]) == 10

    @pytest.mark.asyncio
    async def test_string_page_5_not_greater_than_total_41(
        self, transport, mock_wrapped_transport
    ):
        """Test the specific bug case: page "5" should NOT be >= total_pages "41".

        This is the exact scenario reported where pagination stopped at page 5
        because "5" >= "41" is True in string comparison.
        """
        pages_fetched = []

        def create_response(page_num):
            pages_fetched.append(page_num)
            mock_resp = MagicMock(spec=httpx.Response)
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"data": [{"id": page_num}]}
            mock_resp.headers = {
                "X-Pagination": json.dumps(
                    {
                        "page": str(page_num),  # Will be "5" on page 5
                        "total_pages": "41",  # String "41"
                    }
                )
            }

            async def mock_aread():
                pass

            mock_resp.aread = mock_aread
            return mock_resp

        call_count = 0

        async def create_paginated_response(req):
            nonlocal call_count
            call_count += 1
            page = int(req.url.params.get("page", 1))
            return create_response(page)

        mock_wrapped_transport.handle_async_request.side_effect = (
            create_paginated_response
        )

        request = httpx.Request(
            method="GET",
            url="https://api.example.com/products",
        )

        response = await transport.handle_async_request(request)

        # Should have fetched all 41 pages (or hit max_pages=50 limit)
        assert call_count == 41, (
            f"Expected 41 pages but fetched {call_count}. "
            f"Pages fetched: {sorted(pages_fetched)}. "
            "Bug: string '5' >= '41' is True, incorrectly stopping pagination."
        )
        combined_data = json.loads(response.content)
        assert len(combined_data["data"]) == 41

    @pytest.mark.asyncio
    async def test_string_values_in_response_body_pagination(
        self, transport, mock_wrapped_transport
    ):
        """Test that string pagination values in response body are also converted."""
        pages_fetched = []

        def create_response(page_num, total_pages=8):
            pages_fetched.append(page_num)
            mock_resp = MagicMock(spec=httpx.Response)
            mock_resp.status_code = 200
            # Pagination in response body with string values
            mock_resp.json.return_value = {
                "data": [{"id": page_num}],
                "pagination": {
                    "page": str(page_num),  # String values
                    "total_pages": str(total_pages),
                },
            }
            mock_resp.headers = {}  # No X-Pagination header

            async def mock_aread():
                pass

            mock_resp.aread = mock_aread
            return mock_resp

        call_count = 0

        async def create_paginated_response(req):
            nonlocal call_count
            call_count += 1
            page = int(req.url.params.get("page", 1))
            return create_response(page, total_pages=8)

        mock_wrapped_transport.handle_async_request.side_effect = (
            create_paginated_response
        )

        request = httpx.Request(
            method="GET",
            url="https://api.example.com/products",
        )

        response = await transport.handle_async_request(request)

        # Should have fetched all 8 pages
        assert call_count == 8, (
            f"Expected 8 pages but fetched {call_count}. "
            f"Pages fetched: {pages_fetched}."
        )
        combined_data = json.loads(response.content)
        assert len(combined_data["data"]) == 8

    @pytest.mark.asyncio
    async def test_mixed_integer_and_string_pagination_values(
        self, transport, mock_wrapped_transport
    ):
        """Test that pagination works with a mix of integer and string values."""
        pages_fetched = []

        def create_response(page_num, total_pages=6):
            pages_fetched.append(page_num)
            mock_resp = MagicMock(spec=httpx.Response)
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "data": [{"id": page_num}],
                "pagination": {
                    "page": page_num,  # Integer
                    "total_pages": str(total_pages),  # String
                },
            }
            mock_resp.headers = {}

            async def mock_aread():
                pass

            mock_resp.aread = mock_aread
            return mock_resp

        call_count = 0

        async def create_paginated_response(req):
            nonlocal call_count
            call_count += 1
            page = int(req.url.params.get("page", 1))
            return create_response(page, total_pages=6)

        mock_wrapped_transport.handle_async_request.side_effect = (
            create_paginated_response
        )

        request = httpx.Request(
            method="GET",
            url="https://api.example.com/products",
        )

        response = await transport.handle_async_request(request)

        assert call_count == 6
        combined_data = json.loads(response.content)
        assert len(combined_data["data"]) == 6
