"""Unit tests for Katana MCP Server and authentication."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastmcp import FastMCP
from katana_mcp.server import ServerContext, lifespan, main, mcp

from katana_public_api_client import KatanaClient


class TestServerContext:
    """Tests for ServerContext class."""

    def test_server_context_initialization(self):
        """Test ServerContext initializes with KatanaClient."""
        mock_client = MagicMock(spec=KatanaClient)
        context = ServerContext(client=mock_client)

        assert context.client is mock_client

    def test_server_context_stores_client(self):
        """Test ServerContext correctly stores and retrieves client."""
        mock_client = MagicMock(spec=KatanaClient)
        context = ServerContext(client=mock_client)

        # Verify we can access the client
        retrieved_client = context.client
        assert retrieved_client is mock_client


class TestLifespan:
    """Tests for server lifespan management."""

    @pytest.mark.asyncio
    async def test_lifespan_with_valid_credentials(self):
        """Test lifespan successfully initializes with valid credentials."""
        mock_server = MagicMock(spec=FastMCP)

        # Mock environment variables
        with (
            patch.dict(
                os.environ,
                {
                    "KATANA_API_KEY": "test-api-key-123",
                    "KATANA_BASE_URL": "https://test.api.example.com",
                },
            ),
            patch("katana_mcp.server.load_dotenv"),
            patch("katana_mcp.server.KatanaClient") as mock_client_class,
        ):
            # Create a mock client instance
            mock_client_instance = AsyncMock(spec=KatanaClient)
            mock_client_instance.__aenter__ = AsyncMock(
                return_value=mock_client_instance
            )
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client_instance

            # Test lifespan context manager
            async with lifespan(mock_server) as context:
                # Verify context is created with client
                assert isinstance(context, ServerContext)
                assert context.client is mock_client_instance

            # Verify KatanaClient was initialized with correct parameters
            mock_client_class.assert_called_once_with(
                api_key="test-api-key-123",
                base_url="https://test.api.example.com",
                timeout=30.0,
                max_retries=5,
                max_pages=100,
            )

    @pytest.mark.asyncio
    async def test_lifespan_with_default_base_url(self):
        """Test lifespan uses default base URL when not provided."""
        mock_server = MagicMock(spec=FastMCP)

        # Mock environment variables (without KATANA_BASE_URL)
        with (
            patch.dict(
                os.environ,
                {"KATANA_API_KEY": "test-api-key-123"},
                clear=True,
            ),
            patch("katana_mcp.server.load_dotenv"),
            patch("katana_mcp.server.KatanaClient") as mock_client_class,
        ):
            # Create a mock client instance
            mock_client_instance = AsyncMock(spec=KatanaClient)
            mock_client_instance.__aenter__ = AsyncMock(
                return_value=mock_client_instance
            )
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client_instance

            # Test lifespan context manager
            async with lifespan(mock_server) as context:
                assert isinstance(context, ServerContext)
                assert context.client is mock_client_instance

            # Verify default base URL was used
            mock_client_class.assert_called_once()
            call_kwargs = mock_client_class.call_args[1]
            assert call_kwargs["base_url"] == "https://api.katanamrp.com/v1"

    @pytest.mark.asyncio
    async def test_lifespan_missing_api_key(self):
        """Test lifespan raises ValueError when API key is missing."""
        mock_server = MagicMock(spec=FastMCP)

        # Mock environment without KATANA_API_KEY
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("katana_mcp.server.load_dotenv"),
        ):
            # Verify ValueError is raised for missing API key
            with pytest.raises(ValueError) as exc_info:
                async with lifespan(mock_server):
                    pass

            assert "KATANA_API_KEY" in str(exc_info.value)
            assert "required for authentication" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_lifespan_handles_client_initialization_error(self):
        """Test lifespan handles KatanaClient initialization errors."""
        mock_server = MagicMock(spec=FastMCP)

        # Mock environment variables
        with (
            patch.dict(
                os.environ,
                {"KATANA_API_KEY": "test-api-key-123"},
            ),
            patch("katana_mcp.server.load_dotenv"),
            patch("katana_mcp.server.KatanaClient") as mock_client_class,
        ):
            # Make KatanaClient raise an exception
            mock_client_class.side_effect = ValueError("Invalid API key format")

            # Verify exception is propagated
            with pytest.raises(ValueError) as exc_info:
                async with lifespan(mock_server):
                    pass

            assert "Invalid API key format" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_lifespan_handles_unexpected_errors(self):
        """Test lifespan handles unexpected errors during initialization."""
        mock_server = MagicMock(spec=FastMCP)

        # Mock environment variables
        with (
            patch.dict(
                os.environ,
                {"KATANA_API_KEY": "test-api-key-123"},
            ),
            patch("katana_mcp.server.load_dotenv"),
            patch("katana_mcp.server.KatanaClient") as mock_client_class,
        ):
            # Make KatanaClient raise an unexpected exception
            mock_client_class.side_effect = RuntimeError("Network error")

            # Verify exception is propagated
            with pytest.raises(RuntimeError) as exc_info:
                async with lifespan(mock_server):
                    pass

            assert "Network error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_lifespan_cleanup_on_success(self):
        """Test lifespan properly cleans up resources after successful execution."""
        mock_server = MagicMock(spec=FastMCP)

        # Mock environment variables
        with (
            patch.dict(
                os.environ,
                {"KATANA_API_KEY": "test-api-key-123"},
            ),
            patch("katana_mcp.server.load_dotenv"),
            patch("katana_mcp.server.KatanaClient") as mock_client_class,
        ):
            # Create a mock client instance
            mock_client_instance = AsyncMock(spec=KatanaClient)
            mock_client_instance.__aenter__ = AsyncMock(
                return_value=mock_client_instance
            )
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client_instance

            # Test lifespan context manager
            async with lifespan(mock_server):
                pass

            # Verify cleanup was called (context manager exit)
            mock_client_instance.__aexit__.assert_called_once()


class TestMCPServerInitialization:
    """Tests for MCP server initialization."""

    def test_mcp_server_exists(self):
        """Test that mcp server instance is created."""
        assert mcp is not None
        assert isinstance(mcp, FastMCP)

    def test_mcp_server_has_name(self):
        """Test that mcp server has correct name."""
        # FastMCP stores name in name attribute
        assert hasattr(mcp, "name")
        assert mcp.name == "katana-erp"

    def test_mcp_server_has_version(self):
        """Test that mcp server has version."""
        # FastMCP stores version in version attribute
        assert hasattr(mcp, "version")
        assert mcp.version == "0.3.0"

    def test_mcp_server_has_lifespan(self):
        """Test that mcp server has lifespan configured."""
        # FastMCP stores lifespan status in _has_lifespan attribute
        assert hasattr(mcp, "_has_lifespan")
        assert mcp._has_lifespan is True

    def test_mcp_server_has_instructions(self):
        """Test that mcp server has instructions."""
        # FastMCP stores instructions in instructions attribute
        assert hasattr(mcp, "instructions")
        assert mcp.instructions is not None
        assert "Katana MCP Server" in mcp.instructions


class TestMainEntryPoint:
    """Tests for main entry point."""

    def test_main_function_exists(self):
        """Test that main function is defined."""
        assert callable(main)

    def test_main_calls_mcp_run(self):
        """Test that main calls mcp.run()."""
        with patch.object(mcp, "run") as mock_run:
            main()
            mock_run.assert_called_once()

    def test_main_passes_kwargs_to_run(self):
        """Test that main passes kwargs to mcp.run()."""
        with patch.object(mcp, "run") as mock_run:
            main(host="localhost", port=8000)
            mock_run.assert_called_once_with(host="localhost", port=8000)


class TestEnvironmentConfiguration:
    """Tests for environment-based configuration."""

    @pytest.mark.asyncio
    async def test_environment_loading_from_dotenv(self):
        """Test that environment variables are loaded from .env file."""
        mock_server = MagicMock(spec=FastMCP)

        with (
            patch.dict(
                os.environ,
                {"KATANA_API_KEY": "test-key"},
            ),
            patch("katana_mcp.server.load_dotenv") as mock_load_dotenv,
            patch("katana_mcp.server.KatanaClient") as mock_client_class,
        ):
            # Create a mock client instance
            mock_client_instance = AsyncMock(spec=KatanaClient)
            mock_client_instance.__aenter__ = AsyncMock(
                return_value=mock_client_instance
            )
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client_instance

            async with lifespan(mock_server):
                pass

            # Verify load_dotenv was called
            mock_load_dotenv.assert_called_once()

    @pytest.mark.asyncio
    async def test_custom_base_url_from_environment(self):
        """Test that custom base URL is read from environment."""
        mock_server = MagicMock(spec=FastMCP)
        custom_url = "https://custom.katana.example.com/api"

        with (
            patch.dict(
                os.environ,
                {
                    "KATANA_API_KEY": "test-key",
                    "KATANA_BASE_URL": custom_url,
                },
            ),
            patch("katana_mcp.server.load_dotenv"),
            patch("katana_mcp.server.KatanaClient") as mock_client_class,
        ):
            # Create a mock client instance
            mock_client_instance = AsyncMock(spec=KatanaClient)
            mock_client_instance.__aenter__ = AsyncMock(
                return_value=mock_client_instance
            )
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client_instance

            async with lifespan(mock_server):
                pass

            # Verify custom base URL was used
            call_kwargs = mock_client_class.call_args[1]
            assert call_kwargs["base_url"] == custom_url
