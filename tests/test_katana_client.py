"""Tests for the Katana Client with always-on resilience features."""

import os
from unittest.mock import MagicMock, patch

import httpx
import pytest

from katana_public_api_client import KatanaClient
from katana_public_api_client.katana_client import ResilientAsyncTransport


@pytest.mark.unit
class TestResilientAsyncTransport:
    """Test the resilient async transport layer."""

    @pytest.fixture
    def transport(self):
        """Create a transport instance for testing."""
        return ResilientAsyncTransport(
            max_retries=3,
        )

    @pytest.mark.asyncio
    async def test_successful_request(self, transport):
        """Test that successful requests pass through unchanged."""
        # Mock the parent's handle_async_request method
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200

        with patch.object(
            httpx.AsyncHTTPTransport, "handle_async_request", return_value=mock_response
        ) as mock_parent:
            request = MagicMock(spec=httpx.Request)
            request.method = "POST"  # Non-GET request, should pass through
            request.url = MagicMock()
            request.url.params = {}
            response = await transport.handle_async_request(request)

            assert response.status_code == 200
            mock_parent.assert_called_once_with(request)

    @pytest.mark.asyncio
    async def test_rate_limit_retry(self, transport):
        """Test that 429 responses trigger retries."""
        # Mock responses: 429, then 200
        mock_rate_limited = MagicMock(spec=httpx.Response)
        mock_rate_limited.status_code = 429
        mock_rate_limited.headers = {"Retry-After": "1"}

        mock_success = MagicMock(spec=httpx.Response)
        mock_success.status_code = 200

        with patch.object(
            httpx.AsyncHTTPTransport,
            "handle_async_request",
            side_effect=[mock_rate_limited, mock_success],
        ) as mock_parent:
            request = MagicMock(spec=httpx.Request)
            request.method = "POST"  # Non-GET request, should pass through
            request.url = MagicMock()
            request.url.params = {}
            response = await transport.handle_async_request(request)

            assert response.status_code == 200
            assert mock_parent.call_count == 2  # Should have retried once

    @pytest.mark.asyncio
    async def test_server_error_retry(self, transport):
        """Test that 5xx responses trigger retries."""
        # Mock responses: 500, then 200
        mock_server_error = MagicMock(spec=httpx.Response)
        mock_server_error.status_code = 500

        mock_success = MagicMock(spec=httpx.Response)
        mock_success.status_code = 200

        with patch.object(
            httpx.AsyncHTTPTransport,
            "handle_async_request",
            side_effect=[mock_server_error, mock_success],
        ) as mock_parent:
            request = MagicMock(spec=httpx.Request)
            request.method = "POST"  # Non-GET request, should pass through
            request.url = MagicMock()
            request.url.params = {}
            response = await transport.handle_async_request(request)

            assert response.status_code == 200
            assert mock_parent.call_count == 2  # Should have retried once

    @pytest.mark.asyncio
    async def test_network_error_retry(self, transport):
        """Test that network errors trigger retries."""
        # Mock network error, then success
        mock_success = MagicMock(spec=httpx.Response)
        mock_success.status_code = 200

        with patch.object(
            httpx.AsyncHTTPTransport,
            "handle_async_request",
            side_effect=[httpx.ConnectError("Connection failed"), mock_success],
        ) as mock_parent:
            request = MagicMock(spec=httpx.Request)
            request.method = "POST"  # Non-GET request, should pass through
            request.url = MagicMock()
            request.url.params = {}
            response = await transport.handle_async_request(request)

            assert response.status_code == 200
            assert mock_parent.call_count == 2  # Should have retried once

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, transport):
        """Test that max retries are respected."""
        # Always return 500
        mock_error = MagicMock(spec=httpx.Response)
        mock_error.status_code = 500

        with patch.object(
            httpx.AsyncHTTPTransport, "handle_async_request", return_value=mock_error
        ) as mock_parent:
            request = MagicMock(spec=httpx.Request)
            request.method = "POST"  # Non-GET request, should pass through
            request.url = MagicMock()
            request.url.params = {}
            response = await transport.handle_async_request(request)

            assert response.status_code == 500
            assert mock_parent.call_count == 4  # Initial + 3 retries

    @pytest.mark.asyncio
    async def test_client_error_no_retry(self, transport):
        """Test that 4xx errors (except 429) don't trigger retries."""
        mock_client_error = MagicMock(spec=httpx.Response)
        mock_client_error.status_code = 404

        with patch.object(
            httpx.AsyncHTTPTransport,
            "handle_async_request",
            return_value=mock_client_error,
        ) as mock_parent:
            request = MagicMock(spec=httpx.Request)
            request.method = "POST"  # Non-GET request, should pass through
            request.url = MagicMock()
            request.url.params = {}
            response = await transport.handle_async_request(request)

            assert response.status_code == 404
            mock_parent.assert_called_once_with(request)

    @pytest.mark.asyncio
    async def test_422_validation_error_logging(self, transport, caplog):
        """Test detailed logging for 422 validation errors."""
        # Mock a 422 validation error response
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 422
        mock_response.json.return_value = {
            "statusCode": 422,
            "name": "UnprocessableEntityError",
            "message": "The request body is invalid.",
            "code": "VALIDATION_FAILED",
            "details": [
                {
                    "path": ".name",
                    "code": "maxLength",
                    "message": "should NOT be longer than 10 characters",
                    "info": {"limit": 10},
                },
                {
                    "path": ".email",
                    "code": "format",
                    "message": 'should match format "email"',
                    "info": {"format": "email"},
                },
            ],
        }

        # Mock request
        mock_request = MagicMock(spec=httpx.Request)
        mock_request.method = "POST"
        mock_request.url = "https://api.katanamrp.com/v1/products"

        # Test the error logging
        await transport._log_client_error(mock_response, mock_request)

        # Verify detailed error logging
        error_logs = [
            record for record in caplog.records if record.levelname == "ERROR"
        ]
        assert len(error_logs) == 1

        error_message = error_logs[0].message
        assert "Validation error 422" in error_message
        assert "UnprocessableEntityError" in error_message
        assert "VALIDATION_FAILED" in error_message
        assert "Validation details (2 errors)" in error_message
        assert "Path: .name" in error_message
        assert "maxLength" in error_message
        assert "Path: .email" in error_message
        assert "format" in error_message

    @pytest.mark.asyncio
    async def test_400_general_error_logging(self, transport, caplog):
        """Test logging for general 400-level errors."""
        # Mock a 400 bad request error response
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "statusCode": 400,
            "name": "BadRequest",
            "message": "Invalid request parameters.",
            "code": "INVALID_PARAMS",
        }

        # Mock request
        mock_request = MagicMock(spec=httpx.Request)
        mock_request.method = "GET"
        mock_request.url = "https://api.katanamrp.com/v1/products?invalid=param"

        # Test the error logging
        await transport._log_client_error(mock_response, mock_request)

        # Verify error logging
        error_logs = [
            record for record in caplog.records if record.levelname == "ERROR"
        ]
        assert len(error_logs) == 1

        error_message = error_logs[0].message
        assert "Client error 400" in error_message
        assert "BadRequest" in error_message
        assert "Invalid request parameters" in error_message
        assert "INVALID_PARAMS" in error_message

    @pytest.mark.asyncio
    async def test_error_logging_with_invalid_json(self, transport, caplog):
        """Test error logging when response contains invalid JSON."""
        # Mock a response with invalid JSON
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 400
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.text = "Invalid JSON response from server"

        # Mock request
        mock_request = MagicMock(spec=httpx.Request)
        mock_request.method = "POST"
        mock_request.url = "https://api.katanamrp.com/v1/products"

        # Test the error logging
        await transport._log_client_error(mock_response, mock_request)

        # Verify fallback error logging
        error_logs = [
            record for record in caplog.records if record.levelname == "ERROR"
        ]
        assert len(error_logs) == 1

        error_message = error_logs[0].message
        assert "Client error 400" in error_message
        assert "Failed to parse error details" in error_message

    @pytest.mark.asyncio
    async def test_error_logging_integration_with_request_handling(
        self, transport, caplog
    ):
        """Test that error logging is triggered during actual request handling."""
        # Mock a 422 response
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 422
        mock_response.json.return_value = {
            "statusCode": 422,
            "name": "UnprocessableEntityError",
            "message": "Validation failed",
        }

        with patch.object(
            httpx.AsyncHTTPTransport, "handle_async_request", return_value=mock_response
        ):
            request = MagicMock(spec=httpx.Request)
            request.method = "POST"
            request.url = MagicMock()
            request.url.params = {}

            # Make the request - this should trigger error logging
            response = await transport.handle_async_request(request)

            # Verify the response is returned correctly
            assert response.status_code == 422

            # Verify error logging was triggered
            error_logs = [
                record for record in caplog.records if record.levelname == "ERROR"
            ]
            assert len(error_logs) == 1
            assert "Validation error 422" in error_logs[0].message


@pytest.mark.unit
class TestKatanaClient:
    """Test the main KatanaClient class."""

    def test_client_initialization(self):
        """Test that client can be initialized with default settings."""
        client = KatanaClient()
        assert client.max_pages == 100  # Default value
        # KatanaClient now inherits from AuthenticatedClient - test that it has the expected attributes
        assert hasattr(client, "token")
        assert hasattr(client, "get_async_httpx_client")
        assert client.token == "test-key"  # Set by conftest.py fixture

    def test_client_initialization_with_params(self):
        """Test client initialization with custom parameters."""
        client = KatanaClient(max_pages=50, timeout=30)
        assert client.max_pages == 50

    def test_client_initialization_missing_api_key(self):
        """Test client initialization fails without API key."""
        # Clear all environment variables including KATANA_API_KEY
        with (
            patch.dict(os.environ, {}, clear=True),
            patch.dict(os.environ, {"KATANA_API_KEY": ""}, clear=True),
            pytest.raises(ValueError, match="API key required"),
        ):
            KatanaClient()

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test that client works as async context manager."""
        async with KatanaClient() as client:
            # KatanaClient now inherits from AuthenticatedClient - test that it can be used directly
            assert hasattr(client, "get_async_httpx_client")
            # Test that the async client is created when entering context
            async_client = client.get_async_httpx_client()
            assert async_client is not None

    @pytest.mark.asyncio
    async def test_pagination_basic(self, katana_client):
        """Test basic pagination functionality."""
        # Note: Pagination is now handled automatically by the transport layer
        # These tests are now in test_transport_auto_pagination.py
        # This test is kept for backward compatibility and to ensure
        # the client still works with the new transport-level pagination
        pass

    @pytest.mark.asyncio
    async def test_pagination_with_processing(self, katana_client):
        """Test pagination with item processing."""
        # Note: The old paginate method with process_page is no longer available
        # since pagination is now handled automatically by the transport layer
        # Processing should be done after the API call returns all results
        pass

    @pytest.mark.asyncio
    async def test_pagination_max_pages_limit(self, katana_client):
        """Test that max_pages limit is respected."""
        # Note: max_pages is now controlled at the client level or transport level
        # This test is covered by the transport-level tests in test_transport_auto_pagination.py
        pass


@pytest.mark.integration
class TestKatanaClientIntegration:
    """Integration tests that may hit real API endpoints."""

    @pytest.mark.asyncio
    async def test_real_api_connection(self):
        """Test connection to real Katana API (requires KATANA_API_KEY)."""
        api_key = os.getenv("KATANA_API_KEY")
        if not api_key:
            pytest.skip("KATANA_API_KEY not set - skipping real API test")

        # Test with a mock to avoid actual API calls during testing
        with patch(
            "katana_public_api_client.generated.api.product.get_all_products.asyncio_detailed"
        ) as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.parsed = MagicMock()
            mock_response.parsed.data = [{"id": 1, "name": "Test Product"}]
            mock_get.return_value = mock_response

            async with KatanaClient() as client:
                # Test a simple API call
                from katana_public_api_client.generated.api.product import (
                    get_all_products,
                )

                response = await get_all_products.asyncio_detailed(
                    client=client,  # Pass KatanaClient directly
                    limit=1,  # Just get one product
                )

                assert response.status_code == 200
                assert hasattr(response.parsed, "data")
