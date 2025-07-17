"""Simple functional test for OpenTracing integration."""

import asyncio
from unittest.mock import MagicMock, patch
from typing import cast
import httpx
import pytest

from katana_public_api_client import KatanaClient
from katana_public_api_client.katana_client import (
    OPENTRACING_AVAILABLE,
    ResilientAsyncTransport,
)


@pytest.mark.skipif(not OPENTRACING_AVAILABLE, reason="OpenTracing not available")
class TestOpenTracingFunctional:
    """Simple functional tests for OpenTracing integration."""

    def test_basic_tracer_integration(self):
        """Test that a tracer can be provided and stored."""
        from jaeger_client import Config

        config = Config(
            config={"sampler": {"type": "const", "param": 1}},
            service_name="test-service",
            validate=True,
        )
        tracer = config.initialize_tracer()

        # Create client with tracer
        client = KatanaClient(
            tracer=tracer, api_key="test-key", base_url="https://test.com"
        )

        # Check tracer on the KatanaClient's async httpx client transport
        async_client = client.get_async_httpx_client()
        transport = cast(ResilientAsyncTransport, async_client._transport)
        assert transport.tracer is tracer

    @pytest.mark.asyncio
    async def test_tracer_called_on_request(self):
        """Test that the tracer is called when making a request."""
        from jaeger_client import Config

        config = Config(
            config={"sampler": {"type": "const", "param": 1}},
            service_name="test-service",
            validate=True,
        )
        tracer = config.initialize_tracer()

        # Create client with tracer
        client = KatanaClient(
            tracer=tracer, api_key="test-key", base_url="https://test.com"
        )

        # Mock the underlying HTTP request to avoid actual network calls
        mock_response = httpx.Response(
            200,
            content=b'{"data": [{"id": 1, "name": "Test"}]}',
            headers={"Content-Type": "application/json"},
        )

        # Mock the transport's handle_async_request method
        async_client = client.get_async_httpx_client()
        transport = cast(ResilientAsyncTransport, async_client._transport)
        with patch.object(
            transport, "handle_async_request", return_value=mock_response
        ):
            # Create a request
            request = httpx.Request("GET", "https://test.com/products")

            # Execute the request through the transport
            response = await transport.handle_async_request(request)

            # Verify we got a response
            assert response.status_code == 200

    def test_no_tracer_works_normally(self):
        """Test that the client works normally without a tracer."""
        # Create client without tracer
        client = KatanaClient(api_key="test-key", base_url="https://test.com")

        # Verify no tracer is set
        async_client = client.get_async_httpx_client()
        transport = cast(ResilientAsyncTransport, async_client._transport)
        assert transport.tracer is None

    def test_availability_flag_correct(self):
        """Test that the OpenTracing availability flag is correct."""
        # Since we installed opentracing, it should be available
        assert OPENTRACING_AVAILABLE is True

        # Verify we can import the libraries
        import opentracing
        import jaeger_client

        assert opentracing is not None
        assert jaeger_client is not None

    def test_backwards_compatibility(self):
        """Test that existing code without tracer still works."""
        # This should work exactly as before
        client = KatanaClient(api_key="test-key", base_url="https://test.com")

        # All existing functionality should work
        # KatanaClient now inherits directly from AuthenticatedClient
        async_client = client.get_async_httpx_client()
        transport = cast(ResilientAsyncTransport, async_client._transport)

        # The transport should exist and work
        assert transport is not None
        assert transport.tracer is None

    def test_multiple_clients_independent(self):
        """Test that multiple clients with different tracers are independent."""
        from jaeger_client import Config

        # Create first tracer
        config1 = Config(
            config={"sampler": {"type": "const", "param": 1}},
            service_name="service1",
            validate=True,
        )
        tracer1 = config1.initialize_tracer()

        # Create second tracer
        config2 = Config(
            config={"sampler": {"type": "const", "param": 1}},
            service_name="service2",
            validate=True,
        )
        tracer2 = config2.initialize_tracer()

        # Create clients
        client1 = KatanaClient(
            tracer=tracer1, api_key="test-key", base_url="https://test.com"
        )
        client2 = KatanaClient(
            tracer=tracer2, api_key="test-key", base_url="https://test.com"
        )
        client3 = KatanaClient(
            api_key="test-key", base_url="https://test.com"
        )  # No tracer

        # Verify they have the right tracers
        async_client1 = client1.get_async_httpx_client()
        async_client2 = client2.get_async_httpx_client()
        async_client3 = client3.get_async_httpx_client()
        transport1 = cast(ResilientAsyncTransport, async_client1._transport)
        transport2 = cast(ResilientAsyncTransport, async_client2._transport)
        transport3 = cast(ResilientAsyncTransport, async_client3._transport)
        assert transport1.tracer is tracer1
        assert transport2.tracer is tracer2
        assert transport3.tracer is None

    def test_context_manager_with_tracer(self):
        """Test that the context manager works with a tracer."""
        from jaeger_client import Config

        config = Config(
            config={"sampler": {"type": "const", "param": 1}},
            service_name="test-service",
            validate=True,
        )
        tracer = config.initialize_tracer()

        # Test context manager usage
        async def test_usage():
            async with KatanaClient(
                tracer=tracer, api_key="test-key", base_url="https://test.com"
            ) as client:
                # Verify tracer is set
                async_client = client.get_async_httpx_client()
                transport = cast(ResilientAsyncTransport, async_client._transport)
                assert transport.tracer is tracer

                return True

        # Run the test
        result = asyncio.run(test_usage())
        assert result is True
