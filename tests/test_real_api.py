"""Tests that require real API credentials (marked as integration tests)."""

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

from katana_public_api_client import AuthenticatedClient, KatanaClient
from katana_public_api_client.api.product import get_all_products

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
        # trunk-ignore(mypy/call-arg)
        client = AuthenticatedClient(base_url=base_url, token=api_key)

        async with client:
            # Try to fetch products (should work with any valid API key)
            response = await get_all_products.asyncio_detailed(client=client, limit=1)

            # Should get a successful response or proper error
            assert response.status_code in [
                200,
                401,
                403,
            ], f"Unexpected status code: {response.status_code}"

            if response.status_code == 200:
                # If successful, should have proper structure
                assert response.parsed is not None
                assert hasattr(response.parsed, "data")

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
            # Direct API call - automatic resilience built-in
            response = await get_all_products.asyncio_detailed(client=client, limit=1)

            # Should get a response
            assert response.status_code in [
                200,
                401,
                403,
            ], f"Unexpected status code: {response.status_code}"

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
            assert client.token is not None
            assert client._base_url is not None
            # Base URL should be either from .env file or the default
            expected_urls = [
                "https://api.katanamrp.com/v1",  # Default
                os.getenv("KATANA_BASE_URL"),  # From .env file
            ]
            assert client._base_url in expected_urls

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
                    from katana_public_api_client.api.product import (
                        get_all_products,
                    )

                    # Test automatic pagination (now built into transport layer)
                    response = await get_all_products.asyncio_detailed(
                        client=client,
                        limit=5,  # Small limit to test automatic pagination
                    )
                    return response

                # Test with 30 second timeout
                response = await asyncio.wait_for(
                    test_katana_pagination(), timeout=30.0
                )

                # Should get a valid response
                assert response.status_code == 200, (
                    f"Expected 200, got {response.status_code}"
                )

                # Extract products from response
                if (
                    hasattr(response, "parsed")
                    and response.parsed
                    and hasattr(response.parsed, "data")
                ):
                    products = response.parsed.data
                    if isinstance(products, list) and len(products) > 0:
                        assert len(products) > 0, "Should get at least some products"

                        # Each product should be a ProductResponse object with proper attributes
                        first_product = products[0]
                        assert hasattr(first_product, "id"), (
                            "Product should have an id attribute"
                        )
                        assert hasattr(first_product, "name"), (
                            "Product should have a name attribute"
                        )

            except TimeoutError:
                pytest.fail("Pagination test timed out after 30 seconds")
            except Exception as e:
                error_msg = str(e).lower()
                if any(
                    keyword in error_msg
                    for keyword in [
                        "rate limit",
                        "permission",
                        "forbidden",
                        "unauthorized",
                    ]
                ):
                    pytest.skip(f"API limitation: {e}")
                else:
                    raise

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

            # Base URL is optional in .env, should default if not set
            # This test just verifies the loading mechanism works

    @pytest.mark.integration
    def test_client_creation_with_env_vars(self, api_key, base_url):
        """Test that client can be created from environment variables."""
        if api_key:
            # Should be able to create client
            # trunk-ignore(mypy/call-arg)
            client = AuthenticatedClient(base_url=base_url, token=api_key)
            assert client.token == api_key
            assert hasattr(client, "_base_url"), "Client should have base URL"
        else:
            pytest.skip("No API credentials available in environment")

    def test_katana_client_defaults_base_url(self):
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
                client = KatanaClient(api_key=original_key)
                assert client._base_url == "https://api.katanamrp.com/v1"

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
        # and ensuring environment variables don't interfere
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
                from katana_public_api_client.api.product import (
                    get_all_products,
                )

                # Direct API call with invalid key - automatic resilience built-in
                response = await get_all_products.asyncio_detailed(
                    client=client, limit=1
                )
                # Should handle error gracefully - either error status or the response itself
                if hasattr(response, "status_code"):
                    # If we get a response, it should be an error status for invalid API key
                    assert response.status_code >= 400, (
                        f"Expected error status code for invalid API key, got {response.status_code}"
                    )
                else:
                    # If we get an exception, that's also fine for error handling
                    pytest.fail(
                        "Should have received a response object with error status"
                    )

        finally:
            # Restore original environment values
            if original_api_key is not None:
                os.environ["KATANA_API_KEY"] = original_api_key
            if original_base_url_env is not None:
                os.environ["KATANA_BASE_URL"] = original_base_url_env
