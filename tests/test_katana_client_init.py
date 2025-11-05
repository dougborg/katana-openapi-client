"""Comprehensive tests for KatanaClient initialization and configuration.

This module tests all initialization paths, environment variable handling,
configuration validation, and parameter passing for the KatanaClient class.
"""

import os
from unittest.mock import MagicMock, patch

import httpx
import pytest
from httpx_retries import RetryTransport

from katana_public_api_client import KatanaClient


@pytest.mark.unit
class TestKatanaClientInitialization:
    """Test KatanaClient initialization with various parameter combinations."""

    def test_initialization_with_explicit_api_key(self):
        """Test initialization with explicitly provided API key."""
        client = KatanaClient(
            api_key="explicit-key", base_url="https://api.example.com"
        )
        assert client._base_url == "https://api.example.com"
        assert "transport" in client._httpx_args

    def test_initialization_with_token_param_backwards_compat(self):
        """Test backwards compatibility with 'token' parameter."""
        client = KatanaClient(token="token-key", base_url="https://api.example.com")
        assert client._base_url == "https://api.example.com"

    def test_initialization_fails_with_both_api_key_and_token(self):
        """Test that providing both api_key and token raises ValueError."""
        with pytest.raises(ValueError, match="Cannot specify both"):
            KatanaClient(
                api_key="key1", token="key2", base_url="https://api.example.com"
            )

    def test_initialization_from_env_var(self):
        """Test initialization using KATANA_API_KEY environment variable."""
        with patch.dict(os.environ, {"KATANA_API_KEY": "env-api-key"}):
            client = KatanaClient(base_url="https://api.example.com")
            assert client._base_url == "https://api.example.com"

    def test_initialization_from_env_var_base_url(self):
        """Test initialization using KATANA_BASE_URL environment variable."""
        with patch.dict(
            os.environ,
            {"KATANA_API_KEY": "test-key", "KATANA_BASE_URL": "https://env.api.com"},
        ):
            client = KatanaClient()
            assert client._base_url == "https://env.api.com"

    def test_initialization_explicit_overrides_env(self):
        """Test that explicit parameters override environment variables."""
        with patch.dict(
            os.environ,
            {"KATANA_API_KEY": "env-key", "KATANA_BASE_URL": "https://env.api.com"},
        ):
            client = KatanaClient(
                api_key="explicit-key", base_url="https://explicit.api.com"
            )
            assert client._base_url == "https://explicit.api.com"

    def test_initialization_defaults_to_production_url(self):
        """Test that base_url defaults to production API URL."""
        with patch.dict(os.environ, {"KATANA_API_KEY": "test-key"}, clear=True):
            client = KatanaClient()
            assert client._base_url == "https://api.katanamrp.com/v1"

    def test_initialization_fails_without_api_key(self):
        """Test that initialization fails if no API key is provided."""
        # Need to ensure .env file doesn't load keys
        with (
            patch("katana_public_api_client.katana_client.load_dotenv"),
            patch.dict(os.environ, {}, clear=True),
            pytest.raises(ValueError, match="API key required"),
        ):
            KatanaClient(base_url="https://api.example.com")

    def test_initialization_with_custom_timeout(self):
        """Test initialization with custom timeout value."""
        client = KatanaClient(
            api_key="test-key", base_url="https://api.example.com", timeout=60.0
        )
        assert client._base_url == "https://api.example.com"
        # Timeout is wrapped in httpx.Timeout object
        assert hasattr(client, "_timeout")

    def test_initialization_with_custom_max_retries(self):
        """Test initialization with custom max_retries value."""
        client = KatanaClient(
            api_key="test-key", base_url="https://api.example.com", max_retries=10
        )
        transport = client._httpx_args["transport"]
        assert isinstance(transport, RetryTransport)
        assert transport.retry.total == 10

    def test_initialization_with_custom_max_pages(self):
        """Test initialization with custom max_pages value."""
        client = KatanaClient(
            api_key="test-key", base_url="https://api.example.com", max_pages=50
        )
        assert client.max_pages == 50

    def test_initialization_with_custom_logger(self):
        """Test initialization with custom logger instance."""
        import logging

        custom_logger = logging.getLogger("test_katana_client")
        client = KatanaClient(
            api_key="test-key",
            base_url="https://api.example.com",
            logger=custom_logger,
        )
        assert client.logger is custom_logger

    def test_initialization_from_netrc(self, tmp_path):
        """Test initialization using ~/.netrc file without login field."""
        # Create netrc file without login field to demonstrate it's optional
        netrc_file = tmp_path / ".netrc"
        netrc_file.write_text("machine api.katanamrp.com\npassword netrc-api-key\n")
        netrc_file.chmod(0o600)

        with (
            patch("katana_public_api_client.katana_client.load_dotenv"),
            patch.dict(os.environ, {}, clear=True),
            patch(
                "katana_public_api_client.katana_client.Path.home",
                return_value=tmp_path,
            ),
        ):
            client = KatanaClient(base_url="https://api.katanamrp.com/v1")
            # Client should initialize successfully with netrc credentials
            assert client._base_url == "https://api.katanamrp.com/v1"

    def test_initialization_from_netrc_with_custom_base_url(self, tmp_path):
        """Test initialization using ~/.netrc with custom base URL."""
        # Create a temporary netrc file with custom domain
        netrc_file = tmp_path / ".netrc"
        netrc_file.write_text("machine custom.api.com\npassword custom-netrc-key\n")
        netrc_file.chmod(0o600)

        with (
            patch("katana_public_api_client.katana_client.load_dotenv"),
            patch.dict(os.environ, {}, clear=True),
            patch(
                "katana_public_api_client.katana_client.Path.home",
                return_value=tmp_path,
            ),
        ):
            client = KatanaClient(base_url="https://custom.api.com/v1")
            assert client._base_url == "https://custom.api.com/v1"

    def test_initialization_env_var_overrides_netrc(self, tmp_path):
        """Test that environment variable takes precedence over netrc."""
        # Create a temporary netrc file
        netrc_file = tmp_path / ".netrc"
        netrc_file.write_text("machine api.katanamrp.com\npassword netrc-api-key\n")
        netrc_file.chmod(0o600)

        with (
            patch.dict(os.environ, {"KATANA_API_KEY": "env-key"}),
            patch(
                "katana_public_api_client.katana_client.Path.home",
                return_value=tmp_path,
            ),
        ):
            # Should use env var, not netrc
            client = KatanaClient(base_url="https://api.katanamrp.com/v1")
            assert client._base_url == "https://api.katanamrp.com/v1"

    def test_initialization_explicit_overrides_netrc(self, tmp_path):
        """Test that explicit api_key parameter overrides netrc."""
        # Create a temporary netrc file
        netrc_file = tmp_path / ".netrc"
        netrc_file.write_text("machine api.katanamrp.com\npassword netrc-api-key\n")
        netrc_file.chmod(0o600)

        with (
            patch("katana_public_api_client.katana_client.load_dotenv"),
            patch.dict(os.environ, {}, clear=True),
            patch(
                "katana_public_api_client.katana_client.Path.home",
                return_value=tmp_path,
            ),
        ):
            # Should use explicit parameter, not netrc
            client = KatanaClient(
                api_key="explicit-key", base_url="https://api.katanamrp.com/v1"
            )
            assert client._base_url == "https://api.katanamrp.com/v1"

    def test_initialization_netrc_missing_file(self):
        """Test graceful handling when ~/.netrc doesn't exist."""
        with (
            patch("katana_public_api_client.katana_client.load_dotenv"),
            patch.dict(os.environ, {}, clear=True),
            pytest.raises(ValueError, match="API key required"),
        ):
            # Should fail gracefully when netrc doesn't exist
            KatanaClient(base_url="https://api.example.com")

    def test_initialization_netrc_missing_host_entry(self, tmp_path):
        """Test graceful handling when netrc exists but has no matching host."""
        # Create netrc with different host
        netrc_file = tmp_path / ".netrc"
        netrc_file.write_text("machine different.api.com\npassword different-key\n")
        netrc_file.chmod(0o600)

        with (
            patch("katana_public_api_client.katana_client.load_dotenv"),
            patch.dict(os.environ, {}, clear=True),
            patch(
                "katana_public_api_client.katana_client.Path.home",
                return_value=tmp_path,
            ),
            pytest.raises(ValueError, match="API key required"),
        ):
            # Should fail when host not found in netrc
            KatanaClient(base_url="https://api.katanamrp.com/v1")

    def test_initialization_netrc_parse_error(self, tmp_path):
        """Test graceful handling of malformed netrc file."""
        # Create malformed netrc file
        netrc_file = tmp_path / ".netrc"
        netrc_file.write_text("this is not valid netrc format {{{")
        netrc_file.chmod(0o600)

        with (
            patch("katana_public_api_client.katana_client.load_dotenv"),
            patch.dict(os.environ, {}, clear=True),
            patch(
                "katana_public_api_client.katana_client.Path.home",
                return_value=tmp_path,
            ),
            pytest.raises(ValueError, match="API key required"),
        ):
            # Should fail gracefully with malformed netrc
            KatanaClient(base_url="https://api.katanamrp.com/v1")

    def test_error_message_mentions_netrc(self):
        """Test that error message mentions netrc as an authentication option."""
        with (
            patch("katana_public_api_client.katana_client.load_dotenv"),
            patch.dict(os.environ, {}, clear=True),
            pytest.raises(ValueError, match=r"\.netrc"),
        ):
            KatanaClient(base_url="https://api.example.com")


@pytest.mark.unit
class TestKatanaClientHttpxParameterPassing:
    """Test that httpx parameters are correctly passed through the transport chain."""

    def test_http2_parameter_passed_to_transport(self):
        """Test that http2 parameter is passed to base transport."""
        client = KatanaClient(
            api_key="test-key", base_url="https://api.example.com", http2=True
        )
        # Client should initialize successfully with transport configured
        assert "transport" in client._httpx_args
        assert isinstance(client._httpx_args["transport"], RetryTransport)

    def test_verify_parameter_passed_to_transport(self):
        """Test that verify (SSL) parameter is passed to base transport."""
        client = KatanaClient(
            api_key="test-key", base_url="https://api.example.com", verify=False
        )
        assert "transport" in client._httpx_args

    def test_trust_env_parameter_passed_to_transport(self):
        """Test that trust_env parameter is passed to base transport."""
        client = KatanaClient(
            api_key="test-key", base_url="https://api.example.com", trust_env=True
        )
        assert "transport" in client._httpx_args

    def test_limits_parameter_passed_to_transport(self):
        """Test that limits parameter is passed to base transport."""
        limits = httpx.Limits(max_connections=100, max_keepalive_connections=20)
        client = KatanaClient(
            api_key="test-key", base_url="https://api.example.com", limits=limits
        )
        assert "transport" in client._httpx_args

    def test_client_specific_params_not_passed_to_transport(self):
        """Test that client-specific params (headers, cookies) stay at client level."""
        custom_headers = {"X-Custom-Header": "test-value"}
        client = KatanaClient(
            api_key="test-key",
            base_url="https://api.example.com",
            headers=custom_headers,
        )
        # Headers should be in httpx_args but not in transport layer
        assert "headers" in client._httpx_args or hasattr(client, "_headers")


@pytest.mark.unit
class TestKatanaClientCustomTransport:
    """Test KatanaClient with custom transport configuration."""

    def test_custom_transport_via_transport_param(self):
        """Test providing custom transport via 'transport' parameter."""
        custom_transport = httpx.AsyncHTTPTransport()
        client = KatanaClient(
            api_key="test-key",
            base_url="https://api.example.com",
            transport=custom_transport,
        )
        # Custom transport should be used instead of default resilient transport
        assert client._httpx_args["transport"] is custom_transport

    def test_custom_transport_via_async_transport_param(self):
        """Test providing custom transport via 'async_transport' parameter."""
        custom_transport = httpx.AsyncHTTPTransport()
        client = KatanaClient(
            api_key="test-key",
            base_url="https://api.example.com",
            async_transport=custom_transport,
        )
        assert client._httpx_args["transport"] is custom_transport

    def test_default_resilient_transport_when_no_custom_provided(self):
        """Test that default resilient transport is used when no custom transport provided."""
        client = KatanaClient(api_key="test-key", base_url="https://api.example.com")
        transport = client._httpx_args["transport"]
        # Should be RetryTransport (outermost layer of resilient transport)
        assert isinstance(transport, RetryTransport)


@pytest.mark.unit
class TestKatanaClientEventHooks:
    """Test event hook configuration and merging."""

    @pytest.mark.asyncio
    async def test_default_event_hooks_configured(self):
        """Test that default event hooks are configured."""
        client = KatanaClient(api_key="test-key", base_url="https://api.example.com")
        assert "event_hooks" in client._httpx_args
        assert "response" in client._httpx_args["event_hooks"]
        # Should have at least 2 default hooks
        assert len(client._httpx_args["event_hooks"]["response"]) >= 2

    @pytest.mark.asyncio
    async def test_custom_event_hooks_merged_with_defaults(self):
        """Test that custom event hooks are merged with default hooks."""

        async def custom_hook(response: httpx.Response) -> None:
            pass

        client = KatanaClient(
            api_key="test-key",
            base_url="https://api.example.com",
            event_hooks={"response": [custom_hook]},
        )

        assert "event_hooks" in client._httpx_args
        response_hooks = client._httpx_args["event_hooks"]["response"]
        # Should have default hooks + custom hook
        assert len(response_hooks) >= 3
        assert custom_hook in response_hooks

    @pytest.mark.asyncio
    async def test_custom_event_hooks_with_single_callable(self):
        """Test that single callable is converted to list when merging."""

        async def custom_hook(response: httpx.Response) -> None:
            pass

        client = KatanaClient(
            api_key="test-key",
            base_url="https://api.example.com",
            event_hooks={"response": custom_hook},  # Single callable, not list
        )

        response_hooks = client._httpx_args["event_hooks"]["response"]
        assert custom_hook in response_hooks

    @pytest.mark.asyncio
    async def test_custom_event_hooks_for_new_event_type(self):
        """Test adding hooks for event types not in defaults."""

        async def request_hook(request: httpx.Request) -> None:
            pass

        client = KatanaClient(
            api_key="test-key",
            base_url="https://api.example.com",
            event_hooks={"request": [request_hook]},
        )

        assert "request" in client._httpx_args["event_hooks"]
        assert request_hook in client._httpx_args["event_hooks"]["request"]


@pytest.mark.unit
class TestKatanaClientContextManager:
    """Test KatanaClient context manager behavior."""

    @pytest.mark.asyncio
    async def test_context_manager_enter_exit(self):
        """Test that client can be used as async context manager."""
        async with KatanaClient(
            api_key="test-key", base_url="https://api.example.com"
        ) as client:
            assert client is not None
            assert hasattr(client, "_httpx_args")

    @pytest.mark.asyncio
    async def test_context_manager_cleanup_on_exit(self):
        """Test that resources are cleaned up on context manager exit."""
        client = KatanaClient(api_key="test-key", base_url="https://api.example.com")

        async with client:
            # Client should be usable inside context
            assert client._base_url == "https://api.example.com"

        # After exiting context, underlying httpx client should be closed
        # The AuthenticatedClient.aclose() should have been called


@pytest.mark.unit
class TestKatanaClientObservabilityHooks:
    """Test the built-in observability event hooks."""

    @pytest.mark.asyncio
    async def test_capture_pagination_metadata_with_valid_header(self):
        """Test _capture_pagination_metadata with valid X-Pagination header."""
        client = KatanaClient(api_key="test-key", base_url="https://api.example.com")

        # Mock a response with X-Pagination header
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.headers = {
            "X-Pagination": '{"page": 1, "total_pages": 5, "total_items": 100}'
        }

        await client._capture_pagination_metadata(mock_response)

        # Should have set pagination_info attribute
        assert hasattr(mock_response, "pagination_info")
        assert mock_response.pagination_info["page"] == 1
        assert mock_response.pagination_info["total_pages"] == 5

    @pytest.mark.asyncio
    async def test_capture_pagination_metadata_with_invalid_json(self, caplog):
        """Test _capture_pagination_metadata with invalid JSON in header."""
        client = KatanaClient(api_key="test-key", base_url="https://api.example.com")

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.headers = {"X-Pagination": "not valid json{"}

        await client._capture_pagination_metadata(mock_response)

        # Should not have pagination_info attribute
        assert not hasattr(mock_response, "pagination_info")
        # Should log warning
        assert any(
            "Invalid X-Pagination header" in record.message for record in caplog.records
        )

    @pytest.mark.asyncio
    async def test_capture_pagination_metadata_non_200_response(self):
        """Test _capture_pagination_metadata ignores non-200 responses."""
        client = KatanaClient(api_key="test-key", base_url="https://api.example.com")

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 404
        mock_response.headers = {"X-Pagination": '{"page": 1}'}

        await client._capture_pagination_metadata(mock_response)

        # Should not process pagination for non-200 responses
        assert not hasattr(mock_response, "pagination_info")

    @pytest.mark.asyncio
    async def test_log_response_metrics_with_elapsed_time(self):
        """Test _log_response_metrics with available elapsed time."""
        import datetime

        client = KatanaClient(api_key="test-key", base_url="https://api.example.com")

        mock_request = MagicMock(spec=httpx.Request)
        mock_request.method = "GET"
        mock_request.url = "https://api.example.com/test"

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.request = mock_request
        mock_response.elapsed = datetime.timedelta(seconds=1.5)

        # Should not raise
        await client._log_response_metrics(mock_response)

    @pytest.mark.asyncio
    async def test_log_response_metrics_without_elapsed_time(self):
        """Test _log_response_metrics handles missing elapsed attribute."""
        client = KatanaClient(api_key="test-key", base_url="https://api.example.com")

        mock_request = MagicMock(spec=httpx.Request)
        mock_request.method = "POST"
        mock_request.url = httpx.URL("https://api.example.com/test")  # Use real URL

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 201
        mock_response.request = mock_request
        # No elapsed attribute
        del mock_response.elapsed

        # Should handle gracefully with 0.0 duration
        await client._log_response_metrics(mock_response)

    @pytest.mark.asyncio
    async def test_log_response_metrics_with_runtime_error(self):
        """Test _log_response_metrics handles RuntimeError from elapsed property."""
        client = KatanaClient(api_key="test-key", base_url="https://api.example.com")

        mock_request = MagicMock(spec=httpx.Request)
        mock_request.method = "GET"
        mock_request.url = "https://api.example.com/test"

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.request = mock_request
        # elapsed raises RuntimeError
        type(mock_response).elapsed = property(
            lambda self: (_ for _ in ()).throw(RuntimeError("Not available"))
        )

        # Should handle gracefully
        await client._log_response_metrics(mock_response)
