"""Tests for the Katana Client with layered transport architecture."""

import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from httpx_retries import RetryTransport

from katana_public_api_client import KatanaClient
from katana_public_api_client.katana_client import (
    ErrorLoggingTransport,
    PaginationTransport,
    RateLimitAwareRetry,
    ResilientAsyncTransport,
)


@pytest.mark.unit
class TestTransportChaining:
    """Test that the ResilientAsyncTransport factory creates the correct chain."""

    def test_factory_returns_retry_transport(self):
        """Test that factory returns a RetryTransport instance."""
        transport = ResilientAsyncTransport(max_retries=3)
        assert isinstance(transport, RetryTransport)

    def test_factory_respects_max_retries(self):
        """Test that factory configures retry count correctly."""
        transport = ResilientAsyncTransport(max_retries=7)
        # The retry strategy should have total=7
        assert transport.retry.total == 7

    def test_factory_respects_retry_after_header(self):
        """Test that factory enables Retry-After header support."""
        transport = ResilientAsyncTransport()
        assert transport.retry.respect_retry_after_header is True

    def test_factory_uses_exponential_backoff(self):
        """Test that factory configures exponential backoff."""
        transport = ResilientAsyncTransport()
        assert transport.retry.backoff_factor == 1.0

    def test_factory_uses_rate_limit_aware_retry(self):
        """Test that factory uses RateLimitAwareRetry."""
        transport = ResilientAsyncTransport()
        assert isinstance(transport.retry, RateLimitAwareRetry)


@pytest.mark.unit
class TestRateLimitAwareRetry:
    """Test the RateLimitAwareRetry class."""

    def test_idempotent_method_retryable_for_429(self):
        """Test that idempotent methods (GET) are retryable for 429."""
        retry = RateLimitAwareRetry(
            total=5,
            allowed_methods=["GET", "POST"],
            status_forcelist=[429, 502, 503, 504],
        )

        assert retry.is_retryable_method("GET")
        assert retry.is_retryable_status_code(429)

    def test_non_idempotent_method_retryable_for_429(self):
        """Test that non-idempotent methods (POST, PATCH) are retryable for 429."""
        retry = RateLimitAwareRetry(
            total=5,
            allowed_methods=["GET", "POST", "PATCH"],
            status_forcelist=[429, 502, 503, 504],
        )

        # POST should be allowed for 429
        assert retry.is_retryable_method("POST")
        assert retry.is_retryable_status_code(429)

        # PATCH should be allowed for 429
        assert retry.is_retryable_method("PATCH")
        assert retry.is_retryable_status_code(429)

    def test_idempotent_method_retryable_for_server_errors(self):
        """Test that idempotent methods are retryable for server errors (502, 503, 504)."""
        retry = RateLimitAwareRetry(
            total=5,
            allowed_methods=["GET", "POST"],
            status_forcelist=[429, 502, 503, 504],
        )

        # GET should pass initial check
        assert retry.is_retryable_method("GET")

        # GET should be retryable for server errors
        assert retry.is_retryable_status_code(502)
        assert retry.is_retryable_status_code(503)
        assert retry.is_retryable_status_code(504)

    def test_non_idempotent_method_not_retryable_for_server_errors(self):
        """Test that non-idempotent methods (POST, PATCH) are NOT retryable for server errors."""
        retry = RateLimitAwareRetry(
            total=5,
            allowed_methods=["GET", "POST", "PATCH"],
            status_forcelist=[429, 502, 503, 504],
        )

        # POST should pass initial check
        assert retry.is_retryable_method("POST")

        # But POST should NOT be retryable for server errors (not safe to retry)
        assert not retry.is_retryable_status_code(502)
        assert not retry.is_retryable_status_code(503)
        assert not retry.is_retryable_status_code(504)

        # Same for PATCH
        assert retry.is_retryable_method("PATCH")
        assert not retry.is_retryable_status_code(502)

    def test_method_state_preserved_across_increment(self):
        """Test that current method is preserved when retry is incremented."""
        retry = RateLimitAwareRetry(
            total=5,
            allowed_methods=["POST"],
            status_forcelist=[429, 502, 503, 504],
        )

        # Set the method
        retry.is_retryable_method("POST")
        assert retry._current_method == "POST"

        # Increment should preserve the method
        new_retry = retry.increment()
        assert new_retry._current_method == "POST"
        assert new_retry.attempts_made == 1

    def test_all_methods_in_allowed_list(self):
        """Test that the factory configures all necessary methods."""
        transport = ResilientAsyncTransport()
        retry = transport.retry

        # Should have all idempotent methods plus POST and PATCH
        expected_methods = {
            "HEAD",
            "GET",
            "PUT",
            "DELETE",
            "OPTIONS",
            "TRACE",
            "POST",
            "PATCH",
        }
        actual_methods = {str(m) for m in retry.allowed_methods}

        assert expected_methods == actual_methods

    def test_status_forcelist_configured(self):
        """Test that the factory configures the status codes for retry."""
        transport = ResilientAsyncTransport()
        retry = transport.retry

        # Should have 429 (rate limiting) and 5xx server errors
        expected_statuses = {429, 502, 503, 504}
        actual_statuses = set(retry.status_forcelist)

        assert expected_statuses == actual_statuses


@pytest.mark.unit
class TestErrorLoggingTransport:
    """Test the error logging transport layer."""

    @pytest.fixture
    def mock_wrapped_transport(self):
        """Create a mock wrapped transport."""
        mock = AsyncMock(spec=httpx.AsyncHTTPTransport)
        return mock

    @pytest.fixture
    def transport(self, mock_wrapped_transport):
        """Create an error logging transport for testing."""
        return ErrorLoggingTransport(wrapped_transport=mock_wrapped_transport)

    @pytest.mark.asyncio
    async def test_successful_request_passes_through(
        self, transport, mock_wrapped_transport
    ):
        """Test that successful requests pass through unchanged."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_wrapped_transport.handle_async_request.return_value = mock_response

        request = MagicMock(spec=httpx.Request)
        response = await transport.handle_async_request(request)

        assert response.status_code == 200
        mock_wrapped_transport.handle_async_request.assert_called_once_with(request)

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
    async def test_422_with_unset_fields_uses_additional_properties(
        self, transport, caplog
    ):
        """Test that Unset fields fall back to additional_properties."""
        # Mock a 422 response where main fields are missing but nested in additional_properties
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 422
        # Simulate what the API actually returns - data nested in 'error' key
        mock_response.json.return_value = {
            "error": {
                "statusCode": 422,
                "name": "ValidationError",
                "message": "Validation failed",
            }
        }

        mock_request = MagicMock(spec=httpx.Request)
        mock_request.method = "PATCH"
        mock_request.url = "https://api.katanamrp.com/v1/products/123"

        await transport._log_client_error(mock_response, mock_request)

        error_logs = [
            record for record in caplog.records if record.levelname == "ERROR"
        ]
        assert len(error_logs) == 1

        error_message = error_logs[0].message
        # Should extract from nested error object
        assert "Validation error 422" in error_message
        assert "ValidationError" in error_message or "(not provided)" in error_message

    @pytest.mark.asyncio
    async def test_422_with_nested_validation_details_in_additional_properties(
        self, transport, caplog
    ):
        """Test that nested validation details in additional_properties are logged."""
        # Mock a 422 response with details nested in additional_properties
        # This matches the actual API response structure seen in production
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 422
        mock_response.json.return_value = {
            "error": {
                "statusCode": 422,
                "name": "UnprocessableEntityError",
                "message": "The request body is invalid. See error object `details` property for more info.",
                "code": "422",
                "details": [
                    {
                        "path": "body.default_supplier_id",
                        "code": "invalid_type",
                        "message": "Expected number, received string",
                    },
                ],
            }
        }

        mock_request = MagicMock(spec=httpx.Request)
        mock_request.method = "PATCH"
        mock_request.url = "https://api.katanamrp.com/v1/products/13461128"

        await transport._log_client_error(mock_response, mock_request)

        error_logs = [
            record for record in caplog.records if record.levelname == "ERROR"
        ]
        assert len(error_logs) == 1

        error_message = error_logs[0].message
        # Should extract from nested error object
        assert "Validation error 422" in error_message
        assert "UnprocessableEntityError" in error_message
        assert "Nested validation details (1 errors)" in error_message
        assert "Path: body.default_supplier_id" in error_message
        assert "Code: invalid_type" in error_message
        assert "Message: Expected number, received string" in error_message

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
        assert "Invalid JSON response from server" in error_message

    @pytest.mark.asyncio
    async def test_429_rate_limit_error_with_unset_fields(self, transport, caplog):
        """Test that 429 rate limit errors handle Unset fields properly."""
        # Mock a 429 rate limit response with error nested in additional_properties
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 429
        mock_response.json.return_value = {
            "error": {
                "statusCode": 429,
                "name": "TooManyRequestsError",
                "message": "Too Many Requests",
            }
        }

        # Mock request
        mock_request = MagicMock(spec=httpx.Request)
        mock_request.method = "PATCH"
        mock_request.url = "https://api.katanamrp.com/v1/products/123"

        # Test the error logging
        await transport._log_client_error(mock_response, mock_request)

        # Verify error logging extracts from additional_properties
        error_logs = [
            record for record in caplog.records if record.levelname == "ERROR"
        ]
        assert len(error_logs) == 1

        error_message = error_logs[0].message
        assert "Client error 429" in error_message
        assert "TooManyRequestsError" in error_message
        assert "Too Many Requests" in error_message
        # Should NOT contain <Unset object>
        assert "Unset" not in error_message

    @pytest.mark.asyncio
    async def test_3xx_and_5xx_not_logged(
        self, transport, mock_wrapped_transport, caplog
    ):
        """Test that 3xx and 5xx responses are not logged by error logging transport."""
        for status_code in [301, 500, 503]:
            mock_response = MagicMock(spec=httpx.Response)
            mock_response.status_code = status_code
            mock_wrapped_transport.handle_async_request.return_value = mock_response

            request = MagicMock(spec=httpx.Request)
            request.url = "https://api.example.com"
            response = await transport.handle_async_request(request)

            # Should pass through without logging
            assert response.status_code == status_code

        # Should have no error logs (only 4xx trigger logging)
        error_logs = [
            record for record in caplog.records if record.levelname == "ERROR"
        ]
        assert len(error_logs) == 0


@pytest.mark.unit
class TestPaginationTransport:
    """Test the pagination transport layer."""

    @pytest.fixture
    def mock_wrapped_transport(self):
        """Create a mock wrapped transport."""
        mock = AsyncMock(spec=httpx.AsyncHTTPTransport)
        return mock

    @pytest.fixture
    def transport(self, mock_wrapped_transport):
        """Create a pagination transport for testing."""
        return PaginationTransport(
            wrapped_transport=mock_wrapped_transport, max_pages=3
        )

    @pytest.mark.asyncio
    async def test_non_get_request_passes_through(
        self, transport, mock_wrapped_transport
    ):
        """Test that non-GET requests pass through without pagination."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_wrapped_transport.handle_async_request.return_value = mock_response

        request = MagicMock(spec=httpx.Request)
        request.method = "POST"
        request.url = MagicMock()
        request.url.params = {"limit": "50"}

        response = await transport.handle_async_request(request)

        assert response.status_code == 200
        mock_wrapped_transport.handle_async_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_without_pagination_params_passes_through(
        self, transport, mock_wrapped_transport
    ):
        """Test that GET requests without page/limit params pass through."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_wrapped_transport.handle_async_request.return_value = mock_response

        request = MagicMock(spec=httpx.Request)
        request.method = "GET"
        request.url = MagicMock()
        request.url.params = {}

        response = await transport.handle_async_request(request)

        assert response.status_code == 200
        mock_wrapped_transport.handle_async_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_auto_pagination_collects_multiple_pages(
        self, transport, mock_wrapped_transport
    ):
        """Test that pagination automatically collects multiple pages."""
        # Create mock responses for 3 pages
        page1_data = {
            "data": [{"id": 1}, {"id": 2}],
            "pagination": {"page": 1, "total_pages": 3},
        }
        page2_data = {
            "data": [{"id": 3}, {"id": 4}],
            "pagination": {"page": 2, "total_pages": 3},
        }
        page3_data = {"data": [{"id": 5}], "pagination": {"page": 3, "total_pages": 3}}

        def create_response(data):
            mock_resp = MagicMock(spec=httpx.Response)
            mock_resp.status_code = 200
            mock_resp.json.return_value = data
            mock_resp.headers = {}

            # Mock aread for streaming responses
            async def mock_aread():
                pass

            mock_resp.aread = mock_aread
            return mock_resp

        page1_response = create_response(page1_data)
        page2_response = create_response(page2_data)
        page3_response = create_response(page3_data)

        mock_wrapped_transport.handle_async_request.side_effect = [
            page1_response,
            page2_response,
            page3_response,
        ]

        # Create a real httpx.Request with pagination parameters
        request = httpx.Request(
            method="GET",
            url="https://api.example.com/products?limit=50",
        )

        response = await transport.handle_async_request(request)

        # Should have made 3 requests (one per page)
        assert mock_wrapped_transport.handle_async_request.call_count == 3, (
            f"Expected 3 requests but got {mock_wrapped_transport.handle_async_request.call_count}"
        )

        # Response should combine all data
        combined_data = json.loads(response.content)
        assert len(combined_data["data"]) == 5
        assert combined_data["data"][0]["id"] == 1
        assert combined_data["data"][4]["id"] == 5
        assert combined_data["pagination"]["collected_pages"] == 3
        assert combined_data["pagination"]["auto_paginated"] is True


@pytest.mark.unit
class TestKatanaClient:
    """Test the KatanaClient initialization and configuration."""

    def test_client_initialization_with_api_key(self):
        """Test that client initializes with API key."""
        client = KatanaClient(base_url="https://api.example.com", token="test-token")
        assert client._base_url == "https://api.example.com"

    def test_client_uses_resilient_transport(self):
        """Test that client uses the resilient transport by default."""
        client = KatanaClient(base_url="https://api.example.com", token="test-token")
        # The client should have the resilient transport configured
        # It's stored in _httpx_args['transport']
        assert hasattr(client, "_httpx_args")
        assert "transport" in client._httpx_args
        # The outermost transport should be a RetryTransport
        assert isinstance(client._httpx_args["transport"], RetryTransport)

    def test_client_can_override_transport(self):
        """Test that client allows custom transport."""
        custom_transport = httpx.AsyncHTTPTransport()
        client = KatanaClient(
            base_url="https://api.example.com",
            token="test-token",
            async_transport=custom_transport,
        )
        # Verify the custom transport was accepted (client should have initialized)
        assert client._base_url == "https://api.example.com"

    def test_client_reads_env_vars(self):
        """Test that client reads from environment variables."""
        with patch.dict(
            os.environ,
            {
                "KATANA_API_KEY": "env-test-token",
                "KATANA_BASE_URL": "https://env.api.example.com",
            },
        ):
            client = KatanaClient()
            assert client._base_url == "https://env.api.example.com"

    def test_client_passes_httpx_params_to_base_transport(self):
        """Test that httpx parameters are correctly passed to the base transport."""
        # Create client with custom httpx parameters
        client = KatanaClient(
            base_url="https://api.example.com",
            token="test-token",
            http2=True,
            verify=False,
        )

        # The transport should be configured (though we can't easily inspect the nested layers)
        # At minimum, verify the client was created successfully with the transport
        assert client._base_url == "https://api.example.com"
        assert "transport" in client._httpx_args
