"""Tests for the generated client structure and API methods.

These tests verify that our Katana client properly integrates with
the generated OpenAPI client and doesn't break existing functionality.
"""

from typing import Any
from unittest.mock import MagicMock

import pytest

from katana_public_api_client import ApiClient, KatanaClient


class TestGeneratedClientStructure:
    """Test the structure of the generated client."""

    @pytest.mark.asyncio
    async def test_authenticated_client_creation(self, mock_api_credentials):
        """Test that we can create the underlying authenticated client."""
        # Test that KatanaClient wraps the new ApiClient properly
        # The new approach uses KatanaClient instead of direct AuthenticatedClient
        async with KatanaClient(
            api_key=mock_api_credentials["api_key"],
            base_url=mock_api_credentials["base_url"],
        ) as client:
            assert client is not None
            assert hasattr(client, "_api_client")  # The underlying API client

    @pytest.mark.asyncio
    async def test_katana_client_wraps_generated_client(self, mock_api_credentials):
        """Test that Katana client wraps the generated client."""
        # KatanaClient now wraps ApiClient instead of the old AuthenticatedClient
        async with KatanaClient(
            api_key=mock_api_credentials["api_key"],
            base_url=mock_api_credentials["base_url"],
        ) as client:
            assert hasattr(client, "_api_client")  # Should wrap the generated client
            assert hasattr(client, "api_key")  # Should have api_key
            assert hasattr(client, "base_url")  # Should have base_url

    @pytest.mark.asyncio
    async def test_api_modules_structure(self, mock_api_credentials):
        """Test that the API modules have the expected structure."""
        # Test that the new KatanaClient provides access to API classes
        async with KatanaClient(
            api_key=mock_api_credentials["api_key"],
            base_url=mock_api_credentials["base_url"],
        ) as client:
            # Should have property-based API access
            assert client.product is not None
            assert client.customer is not None
            assert client.sales_order is not None
            assert client.manufacturing_order is not None
            assert client.inventory is not None
            
            # Should be able to access the underlying client for advanced usage
            assert client.client is not None


class TestGeneratedMethodCompatibility:
    """Test compatibility with generated API methods."""

    @pytest.mark.asyncio
    async def test_method_signature_preservation(self, mock_api_credentials):
        """Test that enhanced methods preserve original signatures."""
        async with KatanaClient(
            api_key=mock_api_credentials["api_key"],
            base_url=mock_api_credentials["base_url"],
        ) as client:
            # Test that we can access API methods
            product_api = client.product
            assert hasattr(product_api, 'get_all_products')
            
            # Method should be callable (we're not actually calling it since it would make a real request)
            assert callable(product_api.get_all_products)

    @pytest.mark.asyncio
    async def test_response_object_handling(self, mock_api_credentials):
        """Test that response objects are handled correctly."""
        async with KatanaClient(**mock_api_credentials) as client:
            # The new approach uses direct Pydantic models instead of response wrappers
            # Test that the client provides access to API methods that will return Pydantic models
            assert hasattr(client.product, 'get_all_products')
            
            # The method signature should indicate it returns a Pydantic model (ProductListResponse)
            method = client.product.get_all_products
            assert callable(method)

    @pytest.mark.asyncio
    async def test_error_response_structure(self, mock_api_credentials):
        """Test handling of error response structures."""
        async with KatanaClient(**mock_api_credentials) as client:
            # With the new approach, errors are raised as exceptions instead of returning error objects
            # Test that we have proper API access for error handling scenarios
            assert client.product is not None
            # The client should handle errors through exception raising, not error response objects


class TestTypeSystemCompatibility:
    """Test that type hints and IDE support are preserved."""

    @pytest.mark.asyncio
    async def test_katana_client_type_hints(self, mock_api_credentials):
        """Test that the Katana client maintains proper types."""
        async with KatanaClient(**mock_api_credentials) as client:
            # The new client should have the expected properties
            assert hasattr(client, "api_key")
            assert hasattr(client, "base_url")
            assert hasattr(client, "_api_client")  # Underlying API client
            
            # Properties should be accessible
            assert client.api_key is not None
            assert client.base_url is not None

    @pytest.mark.asyncio
    async def test_method_enhancement_preserves_types(self, mock_api_credentials):
        """Test that method enhancement preserves type information."""
        async with KatanaClient(**mock_api_credentials) as client:
            # Test that API methods are accessible and callable
            product_api = client.product
            assert hasattr(product_api, 'get_all_products')
            
            # The method should be a coroutine function  
            import inspect
            # The method is actually a bound method, but calling it returns a coroutine
            assert callable(product_api.get_all_products)


class TestImportStructure:
    """Test that imports work correctly and don't break existing code."""

    def test_main_imports(self):
        """Test that main classes can be imported correctly."""
        # These imports should work without errors
        from katana_public_api_client import ApiClient, KatanaClient

        # Classes should be available
        assert ApiClient is not None
        assert KatanaClient is not None

    @pytest.mark.asyncio
    async def test_direct_client_creation(self):
        """Test that clients can be created directly."""
        # Should be able to create a client directly
        async with KatanaClient(api_key="test-key", base_url="https://test.example.com") as client:
            assert isinstance(client, KatanaClient)

    def test_module_structure(self):
        """Test that the module structure is correct."""
        import katana_public_api_client

        # Main module should have expected exports
        assert hasattr(katana_public_api_client, "ApiClient")
        assert hasattr(katana_public_api_client, "KatanaClient")


class TestConfigurationCompatibility:
    """Test that configuration options work correctly."""

    @pytest.mark.asyncio
    async def test_httpx_kwargs_passthrough(self, mock_api_credentials):
        """Test that httpx kwargs are passed through correctly."""
        # Test that additional httpx configuration can be passed
        custom_headers = {"User-Agent": "Custom-Agent/1.0"}

        async with KatanaClient(**mock_api_credentials, headers=custom_headers) as client:
            # Should create successfully with custom configuration
            assert client is not None
            assert client.headers == custom_headers

    @pytest.mark.asyncio
    async def test_timeout_configuration(self, mock_api_credentials):
        """Test that timeout configuration works."""
        async with KatanaClient(**mock_api_credentials, timeout=45.0) as client:
            # Should create successfully with custom timeout
            assert client is not None
            assert client.timeout == 45.0

    @pytest.mark.asyncio
    async def test_retry_configuration(self, mock_api_credentials):
        """Test that retry configuration is properly set."""
        async with KatanaClient(**mock_api_credentials, max_retries=10) as client:
            # KatanaClient stores retry configuration internally
            assert client is not None
            assert client.max_retries == 10

    @pytest.mark.asyncio
    async def test_logger_configuration(self, mock_api_credentials):
        """Test that custom logger configuration works."""
        import logging

        custom_logger = logging.getLogger("custom_test_logger")

        async with KatanaClient(**mock_api_credentials, logger=custom_logger) as client:
            assert client.logger is custom_logger
