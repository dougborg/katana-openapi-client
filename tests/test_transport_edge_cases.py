"""Edge case tests for transport layer components.

This module tests uncovered edge cases in ErrorLoggingTransport and
PaginationTransport to improve overall code coverage and resilience.
"""

import json
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from katana_public_api_client.katana_client import (
    ErrorLoggingTransport,
    PaginationTransport,
)


@pytest.mark.unit
class TestErrorLoggingTransportEdgeCases:
    """Test edge cases for ErrorLoggingTransport."""

    @pytest.mark.asyncio
    async def test_initialization_without_wrapped_transport(self):
        """Test that transport creates default wrapped transport if none provided."""
        transport = ErrorLoggingTransport()
        assert transport._wrapped_transport is not None
        assert isinstance(transport._wrapped_transport, httpx.AsyncHTTPTransport)

    @pytest.mark.asyncio
    async def test_initialization_with_custom_logger(self):
        """Test initialization with custom logger."""
        import logging

        custom_logger = logging.getLogger("test_logger")
        transport = ErrorLoggingTransport(logger=custom_logger)
        assert transport.logger is custom_logger

    @pytest.mark.asyncio
    async def test_initialization_with_kwargs(self):
        """Test that kwargs are passed to base AsyncHTTPTransport."""
        # Should not raise even with http2 kwarg
        transport = ErrorLoggingTransport(http2=True)
        assert transport._wrapped_transport is not None

    @pytest.mark.asyncio
    async def test_error_with_empty_text_attribute(self):
        """Test error logging when response.text is empty."""
        transport = ErrorLoggingTransport()

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 400
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.text = ""  # Empty text

        mock_request = MagicMock(spec=httpx.Request)
        mock_request.method = "POST"
        mock_request.url = "https://api.example.com/test"

        # Should not raise, just log with truncated empty text
        await transport._log_client_error(mock_response, mock_request)

    @pytest.mark.asyncio
    async def test_error_with_missing_text_attribute(self):
        """Test error logging when response has no text attribute."""
        transport = ErrorLoggingTransport()

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 400
        mock_response.json.side_effect = ValueError("Invalid JSON")
        # Remove text attribute
        del mock_response.text

        mock_request = MagicMock(spec=httpx.Request)
        mock_request.method = "POST"
        mock_request.url = "https://api.example.com/test"

        # Should handle gracefully with getattr fallback
        await transport._log_client_error(mock_response, mock_request)

    @pytest.mark.asyncio
    async def test_detailed_error_with_non_422_status(self):
        """Test _log_detailed_error with non-422 status code."""

        transport = ErrorLoggingTransport()

        error_data = {
            "statusCode": 400,
            "name": "DetailedError",
            "message": "Some detailed error",
            "code": "ERR_CODE",
        }

        # Should use "Detailed error" prefix for non-422
        await transport._log_client_error(
            MagicMock(
                status_code=400,
                json=MagicMock(return_value=error_data),
            ),
            MagicMock(method="GET", url="https://test.com"),
        )

    @pytest.mark.asyncio
    async def test_error_response_with_additional_properties(self, caplog):
        """Test ErrorResponse logging with additional_properties."""
        transport = ErrorLoggingTransport()

        # Mock a response with additional properties
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "statusCode": 400,
            "name": "BadRequest",
            "message": "Invalid parameters",
            "custom_field": "custom_value",
            "another_field": 123,
        }

        mock_request = MagicMock(spec=httpx.Request)
        mock_request.method = "GET"
        mock_request.url = "https://api.example.com/test"

        await transport._log_client_error(mock_response, mock_request)

        error_logs = [
            record for record in caplog.records if record.levelname == "ERROR"
        ]
        assert len(error_logs) == 1
        # Should contain additional info if present
        error_message = error_logs[0].message
        assert "BadRequest" in error_message

    @pytest.mark.asyncio
    async def test_error_response_handles_unexpected_structure(self, caplog):
        """Test that ErrorResponse handles unexpected structure gracefully."""
        transport = ErrorLoggingTransport()

        # Create data with unexpected fields that ErrorResponse will store in additional_properties
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "unexpected": "structure",
            "no_standard": "fields",
        }

        mock_request = MagicMock(spec=httpx.Request)
        mock_request.method = "POST"
        mock_request.url = "https://api.example.com/test"

        await transport._log_client_error(mock_response, mock_request)

        error_logs = [
            record for record in caplog.records if record.levelname == "ERROR"
        ]
        assert len(error_logs) == 1
        # ErrorResponse should parse and log with additional_properties
        error_message = error_logs[0].message
        assert "Client error 400" in error_message
        # Should show fields were not provided but additional info is present
        assert "(not provided)" in error_message or "Additional info:" in error_message


@pytest.mark.unit
class TestPaginationTransportEdgeCases:
    """Test edge cases for PaginationTransport."""

    @pytest.mark.asyncio
    async def test_initialization_without_wrapped_transport(self):
        """Test that transport creates default wrapped transport if none provided."""
        transport = PaginationTransport()
        assert transport._wrapped_transport is not None
        assert isinstance(transport._wrapped_transport, httpx.AsyncHTTPTransport)

    @pytest.mark.asyncio
    async def test_initialization_with_custom_max_pages(self):
        """Test initialization with custom max_pages."""
        transport = PaginationTransport(max_pages=50)
        assert transport.max_pages == 50

    @pytest.mark.asyncio
    async def test_initialization_with_custom_logger(self):
        """Test initialization with custom logger."""
        import logging

        custom_logger = logging.getLogger("test_pagination")
        transport = PaginationTransport(logger=custom_logger)
        assert transport.logger is custom_logger

    @pytest.mark.asyncio
    async def test_non_200_response_stops_pagination(self):
        """Test that non-200 response immediately stops pagination."""
        mock_wrapped = AsyncMock(spec=httpx.AsyncHTTPTransport)
        transport = PaginationTransport(wrapped_transport=mock_wrapped)

        # Mock a 500 error response
        error_response = MagicMock(spec=httpx.Response)
        error_response.status_code = 500
        mock_wrapped.handle_async_request.return_value = error_response

        request = httpx.Request(
            method="GET",
            url="https://api.example.com/items?limit=10",
        )

        response = await transport.handle_async_request(request)

        # Should return error response immediately
        assert response.status_code == 500
        # Should only make one request
        assert mock_wrapped.handle_async_request.call_count == 1

    @pytest.mark.asyncio
    async def test_pagination_with_x_pagination_header(self):
        """Test pagination info extraction from X-Pagination header."""
        mock_wrapped = AsyncMock(spec=httpx.AsyncHTTPTransport)
        transport = PaginationTransport(wrapped_transport=mock_wrapped, max_pages=2)

        page1_data = {"data": [{"id": 1}]}
        page2_data = {"data": [{"id": 2}]}

        def create_response_with_header(data, page, total):
            mock_resp = MagicMock(spec=httpx.Response)
            mock_resp.status_code = 200
            mock_resp.json.return_value = data
            mock_resp.headers = {
                "X-Pagination": json.dumps({"page": page, "total_pages": total})
            }

            async def mock_aread():
                pass

            mock_resp.aread = mock_aread
            return mock_resp

        mock_wrapped.handle_async_request.side_effect = [
            create_response_with_header(page1_data, 1, 2),
            create_response_with_header(page2_data, 2, 2),
        ]

        request = httpx.Request(
            method="GET",
            url="https://api.example.com/items?limit=10",
        )

        response = await transport.handle_async_request(request)

        # Should collect both pages
        combined_data = json.loads(response.content)
        assert len(combined_data["data"]) == 2

    @pytest.mark.asyncio
    async def test_pagination_with_individual_headers(self):
        """Test pagination info extraction from individual X-Total-Pages/X-Current-Page headers."""
        mock_wrapped = AsyncMock(spec=httpx.AsyncHTTPTransport)
        transport = PaginationTransport(wrapped_transport=mock_wrapped, max_pages=2)

        page1_data = {"data": [{"id": 1}]}
        page2_data = {"data": [{"id": 2}]}

        def create_response_with_headers(data, page, total):
            mock_resp = MagicMock(spec=httpx.Response)
            mock_resp.status_code = 200
            mock_resp.json.return_value = data
            mock_resp.headers = {
                "X-Total-Pages": str(total),
                "X-Current-Page": str(page),
            }

            async def mock_aread():
                pass

            mock_resp.aread = mock_aread
            return mock_resp

        mock_wrapped.handle_async_request.side_effect = [
            create_response_with_headers(page1_data, 1, 2),
            create_response_with_headers(page2_data, 2, 2),
        ]

        request = httpx.Request(
            method="GET",
            url="https://api.example.com/items?limit=10",
        )

        response = await transport.handle_async_request(request)

        combined_data = json.loads(response.content)
        assert len(combined_data["data"]) == 2

    @pytest.mark.asyncio
    async def test_pagination_with_meta_structure(self):
        """Test pagination info extraction from meta.pagination structure."""
        mock_wrapped = AsyncMock(spec=httpx.AsyncHTTPTransport)
        transport = PaginationTransport(wrapped_transport=mock_wrapped, max_pages=2)

        page1_data = {
            "data": [{"id": 1}],
            "meta": {"pagination": {"page": 1, "total_pages": 2}},
        }
        page2_data = {
            "data": [{"id": 2}],
            "meta": {"pagination": {"page": 2, "total_pages": 2}},
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

        mock_wrapped.handle_async_request.side_effect = [
            create_response(page1_data),
            create_response(page2_data),
        ]

        request = httpx.Request(
            method="GET",
            url="https://api.example.com/items?limit=10",
        )

        response = await transport.handle_async_request(request)

        combined_data = json.loads(response.content)
        assert len(combined_data["data"]) == 2

    @pytest.mark.asyncio
    async def test_pagination_stops_on_empty_page(self):
        """Test that pagination stops when encountering an empty page."""
        mock_wrapped = AsyncMock(spec=httpx.AsyncHTTPTransport)
        transport = PaginationTransport(wrapped_transport=mock_wrapped, max_pages=10)

        page1_data = {
            "data": [{"id": 1}, {"id": 2}],
            "pagination": {"page": 1, "total_pages": 10},
        }
        # Empty page should stop pagination
        page2_data = {"data": [], "pagination": {"page": 2, "total_pages": 10}}

        def create_response(data):
            mock_resp = MagicMock(spec=httpx.Response)
            mock_resp.status_code = 200
            mock_resp.json.return_value = data
            mock_resp.headers = {}

            async def mock_aread():
                pass

            mock_resp.aread = mock_aread
            return mock_resp

        mock_wrapped.handle_async_request.side_effect = [
            create_response(page1_data),
            create_response(page2_data),
        ]

        request = httpx.Request(
            method="GET",
            url="https://api.example.com/items?limit=10",
        )

        response = await transport.handle_async_request(request)

        # Should only have collected first page before empty page
        combined_data = json.loads(response.content)
        assert len(combined_data["data"]) == 2
        # Should have only made 2 requests (not all 10)
        assert mock_wrapped.handle_async_request.call_count == 2

    @pytest.mark.asyncio
    async def test_pagination_with_malformed_json(self):
        """Test that malformed JSON returns original response."""
        mock_wrapped = AsyncMock(spec=httpx.AsyncHTTPTransport)
        transport = PaginationTransport(wrapped_transport=mock_wrapped)

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("msg", "doc", 0)
        mock_response.headers = {}

        async def mock_aread():
            pass

        mock_response.aread = mock_aread

        mock_wrapped.handle_async_request.return_value = mock_response

        request = httpx.Request(
            method="GET",
            url="https://api.example.com/items?limit=10",
        )

        response = await transport.handle_async_request(request)

        # Should return the original response when JSON parsing fails
        assert response is mock_response

    @pytest.mark.asyncio
    async def test_pagination_without_pagination_info(self):
        """Test pagination handling when response has no pagination metadata."""
        mock_wrapped = AsyncMock(spec=httpx.AsyncHTTPTransport)
        transport = PaginationTransport(wrapped_transport=mock_wrapped)

        # Response with data but no pagination info
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"id": 1}, {"id": 2}]}
        mock_response.headers = {}

        async def mock_aread():
            pass

        mock_response.aread = mock_aread

        mock_wrapped.handle_async_request.return_value = mock_response

        request = httpx.Request(
            method="GET",
            url="https://api.example.com/items?limit=10",
        )

        response = await transport.handle_async_request(request)

        # Should treat as single page and return data
        combined_data = json.loads(response.content)
        assert len(combined_data["data"]) == 2
        # Should only make one request
        assert mock_wrapped.handle_async_request.call_count == 1

    @pytest.mark.asyncio
    async def test_pagination_with_invalid_x_pagination_header(self):
        """Test handling of invalid X-Pagination header JSON."""
        mock_wrapped = AsyncMock(spec=httpx.AsyncHTTPTransport)
        transport = PaginationTransport(wrapped_transport=mock_wrapped, max_pages=2)

        page1_data = {
            "data": [{"id": 1}],
            "pagination": {"page": 1, "total_pages": 1},
        }

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = page1_data
        # Invalid JSON in header
        mock_response.headers = {"X-Pagination": "not valid json{"}

        async def mock_aread():
            pass

        mock_response.aread = mock_aread

        mock_wrapped.handle_async_request.return_value = mock_response

        request = httpx.Request(
            method="GET",
            url="https://api.example.com/items?limit=10",
        )

        response = await transport.handle_async_request(request)

        # Should fall back to body pagination info
        combined_data = json.loads(response.content)
        assert len(combined_data["data"]) == 1
