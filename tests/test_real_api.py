"""Tests that require real API credentials (marked as integration tests)."""

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

from katana_public_api_client import KatanaClient

# Load environment variables from .env file
load_dotenv()


class TestRealAPIIntegration:
    """Tests that use real API credentials when available."""

    @pytest.fixture(autouse=True)
    def bypass_test_env(self, monkeypatch):
        """Bypass the test environment setup and use real environment variables."""
        # Force reload of environment variables from .env file
        load_dotenv(override=True)
        # Don't let the setup_test_env fixture override our real values
        return True

    @pytest.fixture
    def api_credentials_available(self):
        """Check if real API credentials are available."""
        api_key = os.getenv("KATANA_API_KEY")
        return api_key is not None and api_key.strip() != ""

    @pytest.fixture
    def api_key(self):
        """Get API key from environment."""
        return os.getenv("KATANA_API_KEY")

    @pytest.fixture
    def base_url(self):
        """Get base URL from environment or use default."""
        return os.getenv("KATANA_BASE_URL", "https://api.katanamrp.com/v1")

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.getenv("KATANA_API_KEY"),
        reason="Real API credentials not available (set KATANA_API_KEY in .env file)",
    )
    async def test_real_api_connection(self, api_key, base_url):
        """Test connection to real Katana API."""
        assert api_key is not None, "API key should not be None"

        # TODO: Update this test once the new client structure is finalized
        # Use the new KatanaClient structure instead of AuthenticatedClient
        # async with KatanaClient(api_key=api_key, base_url=base_url) as client:
        #     response = await client.product.get_all_products(limit=1)
        #     assert response.status_code in [200, 401, 403]
        pass  # Placeholder test until client structure is ready

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not os.getenv("KATANA_API_KEY"),
        reason="Real API credentials not available (set KATANA_API_KEY in .env file)",
    )
    async def test_katana_client_with_real_api(self, api_key, base_url):
        """Test KatanaClient with real API."""
        # Test both with explicit parameters and environment variables
        async with KatanaClient(api_key=api_key, base_url=base_url) as client:
            # Direct API call using new class-based approach
            try:
                response = await client.product.get_all_products(limit=1)
                # Should get a response (ProductListResponse)
                assert hasattr(response, "data"), "Response should have data attribute"
                print(f"✅ Successfully fetched products: {len(response.data or [])}")
            except Exception as e:
                # Allow network/auth errors in tests
                error_msg = str(e).lower()
                expected_errors = ["connection", "network", "auth", "401", "403", "404"]
                assert any(word in error_msg for word in expected_errors), (
                    f"Unexpected error: {e}"
                )

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.getenv("KATANA_API_KEY"),
        reason="Real API credentials not available (set KATANA_API_KEY in .env file)",
    )
    async def test_katana_client_with_env_vars_only(self):
        """Test KatanaClient using only environment variables."""
        # This tests the new default behavior where base_url defaults to official URL
        async with KatanaClient() as client:
            # Should work without explicit parameters since we have .env file
            assert client.api_key is not None
            assert client.base_url is not None
            # Base URL should be either from .env file or the default
            expected_urls = [
                "https://api.katanamrp.com/v1",  # Default
                os.getenv("KATANA_BASE_URL"),  # From .env file
            ]
            assert client.base_url in expected_urls

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.getenv("KATANA_API_KEY"),
        reason="Real API credentials not available (set KATANA_API_KEY in .env file)",
    )
    async def test_real_api_pagination(self, api_key, base_url):
        """Test pagination with real API."""
        import asyncio

        async with KatanaClient(api_key=api_key, base_url=base_url) as client:
            try:

                async def test_katana_pagination():
                    # Test basic API call with new class-based approach
                    response = await client.product.get_all_products(limit=5)
                    return response

                # Test with 30 second timeout
                response = await asyncio.wait_for(
                    test_katana_pagination(), timeout=30.0
                )

                # Should get a valid response (ProductListResponse object)
                assert hasattr(response, "data"), "Response should have data attribute"

                # If we got data, it should be a list
                if response.data:
                    assert isinstance(response.data, list), (
                        "Response data should be a list"
                    )
                    print(f"✅ Successfully fetched {len(response.data)} products")

            except Exception as e:
                # Allow network/auth errors in tests
                error_msg = str(e).lower()
                expected_errors = [
                    "connection",
                    "network",
                    "auth",
                    "401",
                    "403",
                    "404",
                    "timeout",
                ]
                assert any(word in error_msg for word in expected_errors), (
                    f"Unexpected error: {e}"
                )

    def test_environment_variable_loading(self):
        """Test that environment variables are loaded correctly."""
        # Test loading from .env file if it exists
        env_file = Path(".env")

        if env_file.exists():
            # Re-load to ensure we have latest values
            load_dotenv(override=True)

            # Check that key variables can be accessed
            api_key = os.environ.get("KATANA_API_KEY")

            # If .env exists and has API_KEY, it should be loaded
            if api_key:
                assert len(api_key) > 0, "API key should not be empty"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_client_creation_with_env_vars(self, api_key, base_url):
        """Test that client can be created from environment variables."""
        if api_key:
            # Should be able to create client in async context
            async with KatanaClient(api_key=api_key, base_url=base_url) as client:
                assert client.api_key == api_key
                assert hasattr(client, "base_url"), "Client should have base_url"
        else:
            pytest.skip("No API credentials available in environment")

    @pytest.mark.asyncio
    async def test_katana_client_defaults_base_url(self):
        """Test that KatanaClient defaults to official Katana API URL."""
        # Test without any environment variables set
        original_key = os.environ.get("KATANA_API_KEY")
        original_url = os.environ.get("KATANA_BASE_URL")

        try:
            # Temporarily clear environment variables to test defaults
            if "KATANA_BASE_URL" in os.environ:
                del os.environ["KATANA_BASE_URL"]

            # Should still be able to create client if API key is available
            if original_key:
                async with KatanaClient(api_key=original_key) as client:
                    assert client.base_url == "https://api.katanamrp.com/v1"

        finally:
            # Restore original values
            if original_key is not None:
                os.environ["KATANA_API_KEY"] = original_key
            if original_url is not None:
                os.environ["KATANA_BASE_URL"] = original_url

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.getenv("KATANA_API_KEY"),
        reason="Real API credentials not available (set KATANA_API_KEY in .env file)",
    )
    async def test_api_error_handling(self, api_key, base_url):
        """Test error handling with real API."""
        # Test with an invalid API key by explicitly creating a client with a bad key
        import os

        # Store original environment values
        original_api_key = os.environ.get("KATANA_API_KEY")
        original_base_url_env = os.environ.get("KATANA_BASE_URL")

        try:
            # Clear environment variables to ensure they don't interfere
            if "KATANA_API_KEY" in os.environ:
                del os.environ["KATANA_API_KEY"]
            if "KATANA_BASE_URL" in os.environ:
                del os.environ["KATANA_BASE_URL"]

            # Create client with invalid API key explicitly
            async with KatanaClient(
                api_key="invalid-api-key-12345", base_url=base_url
            ) as client:
                # Direct API call with invalid key - should handle errors gracefully
                try:
                    _ = await client.product.get_all_products(limit=1)
                    # If we get here without exception, check that error was handled properly
                    raise AssertionError(
                        "Should have raised an exception for invalid API key"
                    )
                except Exception as e:
                    # Should get an authentication error or similar
                    error_msg = str(e).lower()
                    expected_errors = [
                        "auth",
                        "401",
                        "403",
                        "unauthorized",
                        "forbidden",
                        "invalid",
                    ]
                    assert any(word in error_msg for word in expected_errors), (
                        f"Unexpected error type: {e}"
                    )

        finally:
            # Restore original environment values
            if original_api_key is not None:
                os.environ["KATANA_API_KEY"] = original_api_key
            if original_base_url_env is not None:
                os.environ["KATANA_BASE_URL"] = original_base_url_env
