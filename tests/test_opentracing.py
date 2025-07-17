"""Tests for OpenTracing integration in the Katana OpenAPI client."""

import httpx
import pytest
from unittest.mock import MagicMock, patch

from katana_public_api_client import KatanaClient
from katana_public_api_client.katana_client import ResilientAsyncTransport, OPENTRACING_AVAILABLE


@pytest.mark.unit
class TestOpenTracingIntegration:
    """Test OpenTracing integration with the client."""

    def test_opentracing_availability_detection(self):
        """Test that OpenTracing availability is correctly detected."""
        # This test depends on whether opentracing is actually installed
        # Since we're not installing it by default, it should be False
        assert isinstance(OPENTRACING_AVAILABLE, bool)

    def test_transport_initialization_without_tracer(self):
        """Test that transport can be initialized without a tracer."""
        transport = ResilientAsyncTransport()
        assert transport.tracer is None

    def test_transport_initialization_with_none_tracer(self):
        """Test that transport can be initialized with None tracer."""
        transport = ResilientAsyncTransport(tracer=None)
        assert transport.tracer is None

    def test_client_initialization_without_tracer(self, mock_api_credentials):
        """Test that client can be initialized without tracer."""
        client = KatanaClient(**mock_api_credentials)
        # Transport should be created but tracer should be None
        assert hasattr(client, '_client')

    def test_client_initialization_with_none_tracer(self, mock_api_credentials):
        """Test that client can be initialized with None tracer."""
        client = KatanaClient(tracer=None, **mock_api_credentials)
        # Transport should be created but tracer should be None
        assert hasattr(client, '_client')

    @patch('katana_public_api_client.katana_client.OPENTRACING_AVAILABLE', False)
    def test_transport_warns_when_tracer_provided_but_not_available(self, caplog):
        """Test that warning is logged when tracer is provided but opentracing is not available."""
        mock_tracer = MagicMock()
        
        with caplog.at_level('WARNING'):
            transport = ResilientAsyncTransport(tracer=mock_tracer)
        
        assert "OpenTracing tracer provided but opentracing library is not installed" in caplog.text
        assert transport.tracer is mock_tracer  # Should still store the tracer

    @patch('katana_public_api_client.katana_client.OPENTRACING_AVAILABLE', True)
    def test_transport_accepts_tracer_when_available(self):
        """Test that transport accepts tracer when opentracing is available."""
        mock_tracer = MagicMock()
        transport = ResilientAsyncTransport(tracer=mock_tracer)
        assert transport.tracer is mock_tracer

    @patch('katana_public_api_client.katana_client.OPENTRACING_AVAILABLE', True)
    @patch('katana_public_api_client.katana_client.opentracing')
    @patch('katana_public_api_client.katana_client.tags')
    @pytest.mark.asyncio
    async def test_request_tracing_with_tracer(self, mock_tags, mock_opentracing):
        """Test that requests are traced when tracer is provided."""
        # Setup mocks
        mock_tracer = MagicMock()
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=None)
        mock_tracer.start_span.return_value = mock_span
        
        mock_tags.COMPONENT = "component"
        mock_tags.HTTP_METHOD = "http.method"
        mock_tags.HTTP_URL = "http.url"
        mock_tags.SPAN_KIND = "span.kind"
        mock_tags.SPAN_KIND_RPC_CLIENT = "client"
        mock_tags.HTTP_STATUS_CODE = "http.status_code"
        mock_tags.ERROR = "error"
        
        # Create transport with tracer
        transport = ResilientAsyncTransport(tracer=mock_tracer)
        
        # Create a request
        request = httpx.Request(method="GET", url="https://api.example.com/products")
        
        # Mock the actual HTTP request
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        with patch.object(transport, '_handle_request_with_span', return_value=mock_response) as mock_handle:
            response = await transport.handle_async_request(request)
            
            # Verify tracer was called
            mock_tracer.start_span.assert_called_once()
            call_args = mock_tracer.start_span.call_args
            assert call_args[1]['operation_name'] == 'katana_client.GET'
            
            # Verify span was configured
            expected_tags = {
                'component': 'katana-openapi-client',
                'http.method': 'GET',
                'http.url': 'https://api.example.com/products',
                'span.kind': 'client',
            }
            assert call_args[1]['tags'] == expected_tags
            
            # Verify span was tagged with response status
            mock_span.set_tag.assert_called_with('http.status_code', 200)
            
            # Verify the handler was called with the span
            mock_handle.assert_called_once_with(request, mock_span)

    @patch('katana_public_api_client.katana_client.OPENTRACING_AVAILABLE', True)
    @patch('katana_public_api_client.katana_client.opentracing')
    @patch('katana_public_api_client.katana_client.tags')
    @pytest.mark.asyncio
    async def test_request_tracing_with_error(self, mock_tags, mock_opentracing):
        """Test that errors are properly traced."""
        # Setup mocks
        mock_tracer = MagicMock()
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=None)
        mock_tracer.start_span.return_value = mock_span
        
        mock_tags.COMPONENT = "component"
        mock_tags.HTTP_METHOD = "http.method"
        mock_tags.HTTP_URL = "http.url"
        mock_tags.SPAN_KIND = "span.kind"
        mock_tags.SPAN_KIND_RPC_CLIENT = "client"
        mock_tags.ERROR = "error"
        
        # Create transport with tracer
        transport = ResilientAsyncTransport(tracer=mock_tracer)
        
        # Create a request
        request = httpx.Request(method="GET", url="https://api.example.com/products")
        
        # Mock the actual HTTP request to raise an exception
        test_exception = Exception("Test error")
        
        with patch.object(transport, '_handle_request_with_span', side_effect=test_exception):
            with pytest.raises(Exception) as exc_info:
                await transport.handle_async_request(request)
            
            assert exc_info.value is test_exception
            
            # Verify error was tagged
            mock_span.set_tag.assert_called_with('error', True)
            mock_span.log_kv.assert_called_with({"error": "Test error"})

    @patch('katana_public_api_client.katana_client.OPENTRACING_AVAILABLE', True)
    @patch('katana_public_api_client.katana_client.opentracing')
    @patch('katana_public_api_client.katana_client.tags')
    @pytest.mark.asyncio
    async def test_request_tracing_with_http_error(self, mock_tags, mock_opentracing):
        """Test that HTTP errors are properly traced."""
        # Setup mocks
        mock_tracer = MagicMock()
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=None)
        mock_tracer.start_span.return_value = mock_span
        
        mock_tags.COMPONENT = "component"
        mock_tags.HTTP_METHOD = "http.method"
        mock_tags.HTTP_URL = "http.url"
        mock_tags.SPAN_KIND = "span.kind"
        mock_tags.SPAN_KIND_RPC_CLIENT = "client"
        mock_tags.HTTP_STATUS_CODE = "http.status_code"
        mock_tags.ERROR = "error"
        
        # Create transport with tracer
        transport = ResilientAsyncTransport(tracer=mock_tracer)
        
        # Create a request
        request = httpx.Request(method="GET", url="https://api.example.com/products")
        
        # Mock the actual HTTP request to return an error response
        mock_response = MagicMock()
        mock_response.status_code = 500
        
        with patch.object(transport, '_handle_request_with_span', return_value=mock_response):
            response = await transport.handle_async_request(request)
            
            # Verify error was tagged for HTTP error status
            mock_span.set_tag.assert_any_call('http.status_code', 500)
            mock_span.set_tag.assert_any_call('error', True)

    @pytest.mark.asyncio
    async def test_request_without_tracer(self):
        """Test that requests work normally without tracer."""
        # Create transport without tracer
        transport = ResilientAsyncTransport()
        
        # Create a request
        request = httpx.Request(method="GET", url="https://api.example.com/products")
        
        # Mock the actual HTTP request
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        with patch.object(transport, '_handle_request_with_span', return_value=mock_response) as mock_handle:
            response = await transport.handle_async_request(request)
            
            # Verify handler was called with None span
            mock_handle.assert_called_once_with(request, None)
            assert response.status_code == 200

    @patch('katana_public_api_client.katana_client.OPENTRACING_AVAILABLE', True)
    @patch('katana_public_api_client.katana_client.opentracing')
    @patch('katana_public_api_client.katana_client.tags')
    @pytest.mark.asyncio
    async def test_pagination_tracing(self, mock_tags, mock_opentracing):
        """Test that pagination-specific tracing information is added."""
        # Setup mocks
        mock_tracer = MagicMock()
        mock_span = MagicMock()
        mock_span.__enter__ = MagicMock(return_value=mock_span)
        mock_span.__exit__ = MagicMock(return_value=None)
        mock_tracer.start_span.return_value = mock_span
        
        mock_tags.COMPONENT = "component"
        mock_tags.HTTP_METHOD = "http.method"
        mock_tags.HTTP_URL = "http.url"
        mock_tags.SPAN_KIND = "span.kind"
        mock_tags.SPAN_KIND_RPC_CLIENT = "client"
        mock_tags.HTTP_STATUS_CODE = "http.status_code"
        
        # Create transport with tracer
        transport = ResilientAsyncTransport(tracer=mock_tracer)
        
        # Create a paginated request
        request = httpx.Request(method="GET", url="https://api.example.com/products?page=1&limit=10")
        
        # Mock the pagination response
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        with patch.object(transport, '_handle_paginated_request', return_value=mock_response) as mock_paginated:
            response = await transport.handle_async_request(request)
            
            # Verify pagination was tagged
            mock_span.set_tag.assert_any_call("katana.pagination.enabled", True)
            
            # Verify paginated handler was called with span
            mock_paginated.assert_called_once_with(request, mock_span)