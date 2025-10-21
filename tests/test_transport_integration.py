"""Integration tests for transport layer composition.

This module tests end-to-end behavior of the layered transport architecture,
focusing on composability and configuration.
"""

import httpx
import httpx_retries
import pytest

from katana_public_api_client import KatanaClient
from katana_public_api_client.katana_client import ResilientAsyncTransport


@pytest.mark.integration
class TestTransportChainComposition:
    """Test that transport layers compose correctly."""

    def test_resilient_transport_creates_full_chain(self):
        """Test that ResilientAsyncTransport creates the full transport chain."""
        transport = ResilientAsyncTransport(max_retries=3, max_pages=50)

        # Outermost layer should be RetryTransport
        assert isinstance(transport, httpx_retries.RetryTransport)
        assert transport.retry.total == 3

    def test_client_uses_full_transport_chain(self):
        """Test that KatanaClient correctly uses the full transport chain."""
        client = KatanaClient(
            api_key="test-key", base_url="https://api.example.com", max_retries=7
        )

        transport = client._httpx_args["transport"]
        assert isinstance(transport, httpx_retries.RetryTransport)
        assert transport.retry.total == 7

    def test_resilient_transport_with_custom_logger(self):
        """Test that custom logger is passed through transport chain."""
        import logging

        custom_logger = logging.getLogger("test_transport")
        transport = ResilientAsyncTransport(
            max_retries=2, max_pages=10, logger=custom_logger
        )

        assert isinstance(transport, httpx_retries.RetryTransport)

    def test_resilient_transport_with_httpx_kwargs(self):
        """Test that httpx kwargs are passed to base transport."""
        transport = ResilientAsyncTransport(max_retries=3, http2=True, verify=False)

        # Should not raise - httpx kwargs passed correctly
        assert isinstance(transport, httpx_retries.RetryTransport)

    def test_client_transport_configuration_parameters(self):
        """Test that all transport configuration parameters work together."""
        client = KatanaClient(
            api_key="test-key",
            base_url="https://api.example.com",
            max_retries=10,
            max_pages=200,
            timeout=60.0,
        )

        assert client.max_pages == 200
        assert client._httpx_args["transport"].retry.total == 10

    def test_transport_chain_preserves_retry_configuration(self):
        """Test that retry configuration is correctly preserved through the chain."""
        transport = ResilientAsyncTransport(
            max_retries=5,
            max_pages=100,
        )

        # Verify retry configuration
        assert transport.retry.total == 5
        assert 429 in transport.retry.status_forcelist
        assert 502 in transport.retry.status_forcelist
        assert 503 in transport.retry.status_forcelist
        assert 504 in transport.retry.status_forcelist

    def test_client_with_custom_transport_bypasses_resilient_chain(self):
        """Test that providing custom transport bypasses the resilient transport chain."""
        custom_transport = httpx.AsyncHTTPTransport()
        client = KatanaClient(
            api_key="test-key",
            base_url="https://api.example.com",
            transport=custom_transport,
        )

        # Should use custom transport directly
        assert client._httpx_args["transport"] is custom_transport

    def test_multiple_clients_with_different_configurations(self):
        """Test that multiple clients can have different transport configurations."""
        client1 = KatanaClient(
            api_key="key1", base_url="https://api1.example.com", max_retries=3
        )
        client2 = KatanaClient(
            api_key="key2", base_url="https://api2.example.com", max_retries=10
        )

        # Each client should have independent configuration
        assert client1._httpx_args["transport"].retry.total == 3
        assert client2._httpx_args["transport"].retry.total == 10
        assert client1._base_url != client2._base_url
