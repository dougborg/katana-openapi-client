"""Unit tests for Katana MCP Server and authentication."""

import asyncio
import os
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastmcp import FastMCP
from fastmcp.server.middleware.caching import ResponseCachingMiddleware
from katana_mcp.server import _build_auth, lifespan, main, mcp
from katana_mcp.services import Services

from katana_public_api_client import KatanaClient


@pytest.fixture
def isolated_caches(tmp_path: Path) -> Iterator[None]:
    """Redirect ``lifespan()``'s cache constructor to a per-test temp path.

    ``server.lifespan()`` instantiates ``TypedCacheEngine()`` with no
    args, which defaults to a fixed location under
    ``platformdirs.user_cache_dir("katana-mcp")``. Under pytest-xdist
    (``-n 4`` per the project's ``poe test``), parallel workers race on
    that shared SQLite file and one of them sees ``table sync_state
    already exists`` (#455).

    Patch the constructor at the namespace ``lifespan()``'s deferred
    import resolves through — the ``katana_mcp.typed_cache`` package's
    ``__init__.py`` re-export. The legacy ``CatalogCache`` was retired
    in #472 Phase D so only the typed engine needs isolation.
    """
    from katana_mcp import typed_cache as typed_cache_pkg

    real_typed_engine = typed_cache_pkg.TypedCacheEngine

    def make_isolated_typed_engine(*args, **kwargs):
        # Avoid stomping explicit ``in_memory=True`` (it's incompatible
        # with ``db_path``); only inject the path for file-backed mode.
        if not kwargs.get("in_memory", False):
            kwargs.setdefault("db_path", tmp_path / "typed_cache.db")
        return real_typed_engine(*args, **kwargs)

    with patch.object(
        typed_cache_pkg,
        "TypedCacheEngine",
        side_effect=make_isolated_typed_engine,
    ):
        yield


class TestServices:
    """Tests for Services class."""

    def test_services_initialization(self):
        """Test Services initializes with KatanaClient + typed cache.

        The legacy ``CatalogCache`` was retired in #472 Phase D —
        ``Services`` now carries only the typed cache + client.
        """
        mock_client = MagicMock(spec=KatanaClient)
        mock_typed_cache = MagicMock()
        context = Services(client=mock_client, typed_cache=mock_typed_cache)

        assert context.client is mock_client
        assert context.typed_cache is mock_typed_cache

    def test_services_stores_client(self):
        """Test Services correctly stores and retrieves client."""
        mock_client = MagicMock(spec=KatanaClient)
        mock_typed_cache = MagicMock()
        context = Services(client=mock_client, typed_cache=mock_typed_cache)

        assert context.client is mock_client
        assert context.typed_cache is mock_typed_cache


@pytest.mark.usefixtures("isolated_caches")
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
                assert isinstance(context, Services)
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
                assert isinstance(context, Services)
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


@pytest.mark.usefixtures("isolated_caches")
class TestCacheWarmup:
    """Tests for the lifespan cache warm-up task (#593)."""

    @staticmethod
    def _find_warmup_task() -> asyncio.Task[object] | None:
        """Look up the running warmup task by its well-known name.

        Avoids spying on ``asyncio.create_task`` (which also fires for
        SQLAlchemy-internal connection close, sqlite engine teardown,
        etc., producing noisy false positives).
        """
        for task in asyncio.all_tasks():
            if task.get_name() == "katana_cache_warmup":
                return task
        return None

    @pytest.mark.asyncio
    async def test_disable_env_var_skips_warmup(self):
        """``MCP_DISABLE_CACHE_WARMUP=1`` prevents the warmup task from being created.

        Pinned because the conftest autouse fixture relies on this
        contract — if a future refactor decouples the env-var check from
        the task creation, the entire test suite suddenly schedules real
        warmup tasks against the mock client.
        """
        mock_server = MagicMock(spec=FastMCP)
        with (
            patch.dict(
                os.environ,
                {
                    "KATANA_API_KEY": "test-api-key-123",
                    "MCP_DISABLE_CACHE_WARMUP": "1",
                },
            ),
            patch("katana_mcp.server.load_dotenv"),
            patch("katana_mcp.server.KatanaClient") as mock_client_class,
        ):
            mock_client_instance = AsyncMock(spec=KatanaClient)
            mock_client_instance.__aenter__ = AsyncMock(
                return_value=mock_client_instance
            )
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client_instance

            async with lifespan(mock_server):
                # No warmup task should be running with the disable flag set.
                assert self._find_warmup_task() is None

    @pytest.mark.cache_warmup_enabled
    @pytest.mark.asyncio
    async def test_warmup_task_scheduled_when_enabled(self):
        """Without the disable flag, lifespan schedules the warmup task and
        the yield happens immediately — proving the task is fire-and-forget
        rather than awaited inline (the whole point of #593).
        """
        import katana_mcp.server as server_mod

        mock_server = MagicMock(spec=FastMCP)

        async def fake_warmup(*_args: object, **_kwargs: object) -> None:
            # Sleep longer than yield will plausibly wait — if the yield
            # blocked on this, the test would hang. Cancelled by lifespan
            # shutdown.
            await asyncio.sleep(60)

        with (
            patch.dict(
                os.environ,
                {"KATANA_API_KEY": "test-api-key-123"},
            ),
            patch("katana_mcp.server.load_dotenv"),
            patch("katana_mcp.server.KatanaClient") as mock_client_class,
            patch.object(server_mod, "_warm_caches_in_background", fake_warmup),
        ):
            os.environ.pop("MCP_DISABLE_CACHE_WARMUP", None)

            mock_client_instance = AsyncMock(spec=KatanaClient)
            mock_client_instance.__aenter__ = AsyncMock(
                return_value=mock_client_instance
            )
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client_instance

            warmup_task_in_lifespan: asyncio.Task[object] | None = None
            async with lifespan(mock_server):
                # Yield reached without waiting on the warmup — the task
                # is running but not done.
                warmup_task_in_lifespan = self._find_warmup_task()
                assert warmup_task_in_lifespan is not None
                assert not warmup_task_in_lifespan.done()

            # After lifespan exit, the task is cancelled cleanly.
            assert warmup_task_in_lifespan is not None
            assert warmup_task_in_lifespan.cancelled() or warmup_task_in_lifespan.done()

    @pytest.mark.cache_warmup_enabled
    @pytest.mark.asyncio
    async def test_warmup_failure_does_not_crash_server(
        self, caplog: pytest.LogCaptureFixture
    ):
        """A warmup task that raises an unexpected exception must not
        propagate out of the lifespan, and the exception must be consumed
        on shutdown — not left to surface as an asyncio "Task exception
        was never retrieved" warning later.

        ``_warm_caches_in_background`` already swallows per-helper errors
        internally via ``return_exceptions=True`` in the inner gather; this
        test exercises the unexpected-error path at the task scope itself
        (something unrelated to a helper raised, e.g. an import bug or
        logging failure).
        """
        import katana_mcp.server as server_mod

        mock_server = MagicMock(spec=FastMCP)

        async def boom_warmup(*_args: object, **_kwargs: object) -> None:
            raise RuntimeError("simulated unexpected task-scope failure")

        with (
            patch.dict(os.environ, {"KATANA_API_KEY": "test-api-key-123"}),
            patch("katana_mcp.server.load_dotenv"),
            patch("katana_mcp.server.KatanaClient") as mock_client_class,
            patch.object(server_mod, "_warm_caches_in_background", boom_warmup),
        ):
            os.environ.pop("MCP_DISABLE_CACHE_WARMUP", None)

            mock_client_instance = AsyncMock(spec=KatanaClient)
            mock_client_instance.__aenter__ = AsyncMock(
                return_value=mock_client_instance
            )
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client_instance

            # Should NOT raise even though warmup body raises.
            async with lifespan(mock_server) as context:
                assert isinstance(context, Services)
                # Give the warmup task a turn to fire its exception.
                await asyncio.sleep(0)

        # The shutdown handler must have consumed the task's exception and
        # logged it — proves the exception was retrieved rather than left
        # to surface later as a noisy asyncio "Task exception was never
        # retrieved" warning. Log records use structlog's event-key, so
        # check both the message and the event attribute.
        warmup_failure_records = [
            r
            for r in caplog.records
            if "cache_warmup_task_raised" in r.getMessage()
            or getattr(r, "event", None) == "cache_warmup_task_raised"
        ]
        assert warmup_failure_records, (
            "lifespan shutdown must log cache_warmup_task_raised when the "
            "warmup task ends with an unexpected exception; otherwise the "
            "task exception goes unretrieved and surfaces as an asyncio "
            "warning later."
        )

    @pytest.mark.asyncio
    async def test_warm_caches_in_background_swallows_per_entity_errors(self):
        """``_warm_caches_in_background`` calls 16 ``ensure_*_synced``
        helpers via ``asyncio.gather(..., return_exceptions=True)``. A
        single helper raising must not stop the others, and the function
        itself must return without raising so the wrapping task doesn't
        surface an exception.
        """
        import katana_mcp.server as server_mod

        mock_client = MagicMock(spec=KatanaClient)
        mock_cache = MagicMock()

        async def ok(*_args: object, **_kwargs: object) -> None:
            return None

        async def boom(*_args: object, **_kwargs: object) -> None:
            raise RuntimeError("transient")

        # Patch one helper to raise; all others succeed. The function
        # must still return cleanly.
        with (
            patch.object(
                server_mod,
                "_warm_caches_in_background",
                wraps=server_mod._warm_caches_in_background,
            ),
            patch(
                "katana_mcp.typed_cache.ensure_sales_orders_synced",
                side_effect=boom,
            ),
            patch(
                "katana_mcp.typed_cache.ensure_purchase_orders_synced",
                side_effect=ok,
            ),
            patch(
                "katana_mcp.typed_cache.ensure_manufacturing_orders_synced",
                side_effect=ok,
            ),
            patch(
                "katana_mcp.typed_cache.ensure_stock_adjustments_synced",
                side_effect=ok,
            ),
            patch(
                "katana_mcp.typed_cache.ensure_stock_transfers_synced",
                side_effect=ok,
            ),
            patch("katana_mcp.typed_cache.ensure_customers_synced", side_effect=ok),
            patch("katana_mcp.typed_cache.ensure_suppliers_synced", side_effect=ok),
            patch("katana_mcp.typed_cache.ensure_locations_synced", side_effect=ok),
            patch("katana_mcp.typed_cache.ensure_tax_rates_synced", side_effect=ok),
            patch("katana_mcp.typed_cache.ensure_operators_synced", side_effect=ok),
            patch(
                "katana_mcp.typed_cache.ensure_additional_costs_synced",
                side_effect=ok,
            ),
            patch("katana_mcp.typed_cache.ensure_variants_synced", side_effect=ok),
            patch("katana_mcp.typed_cache.ensure_products_synced", side_effect=ok),
            patch("katana_mcp.typed_cache.ensure_materials_synced", side_effect=ok),
            patch("katana_mcp.typed_cache.ensure_services_synced", side_effect=ok),
            patch("katana_mcp.typed_cache.ensure_factory_synced", side_effect=ok),
        ):
            # Must not raise.
            await server_mod._warm_caches_in_background(mock_client, mock_cache)


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
        # Version is dynamically updated by semantic-release, just check format
        assert mcp.version  # Not empty
        assert "." in mcp.version  # Has version separators

    def test_mcp_server_has_lifespan(self):
        """Test that mcp server has lifespan configured."""
        # FastMCP stores lifespan in _lifespan attribute
        assert hasattr(mcp, "_lifespan")
        assert mcp._lifespan is not None

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

    def test_main_calls_mcp_run_with_stdio_default(self):
        """Test that main calls mcp.run() with stdio transport by default."""
        with patch.object(mcp, "run") as mock_run:
            main()
            mock_run.assert_called_once_with(transport="stdio")

    def test_main_passes_transport_options_to_run(self):
        """Test that main passes transport options to mcp.run()."""
        with patch.object(mcp, "run") as mock_run:
            main(transport="sse", host="localhost", port=8000)
            mock_run.assert_called_once_with(
                transport="sse", host="localhost", port=8000
            )


class TestBuildAuth:
    """Tests for _build_auth() auth provider configuration."""

    def test_no_env_vars_returns_none(self):
        """No auth env vars → returns None."""
        with patch.dict(os.environ, {}, clear=True):
            assert _build_auth() is None

    def test_bearer_token_returns_static_verifier(self):
        """MCP_AUTH_TOKEN set → returns StaticTokenVerifier."""
        from fastmcp.server.auth import StaticTokenVerifier

        with patch.dict(os.environ, {"MCP_AUTH_TOKEN": "test-secret"}, clear=True):
            result = _build_auth()
            assert isinstance(result, StaticTokenVerifier)

    def test_github_oauth_returns_github_provider(self):
        """All three GitHub vars set → returns GitHubProvider."""
        from fastmcp.server.auth.providers.github import GitHubProvider

        env = {
            "MCP_GITHUB_CLIENT_ID": "test-id",
            "MCP_GITHUB_CLIENT_SECRET": "test-secret",
            "MCP_BASE_URL": "https://example.com",
        }
        with patch.dict(os.environ, env, clear=True):
            result = _build_auth()
            assert isinstance(result, GitHubProvider)

    def test_github_takes_precedence_over_bearer_token(self):
        """GitHub OAuth vars take precedence when both are set."""
        from fastmcp.server.auth.providers.github import GitHubProvider

        env = {
            "MCP_GITHUB_CLIENT_ID": "test-id",
            "MCP_GITHUB_CLIENT_SECRET": "test-secret",
            "MCP_BASE_URL": "https://example.com",
            "MCP_AUTH_TOKEN": "also-set",
        }
        with patch.dict(os.environ, env, clear=True):
            result = _build_auth()
            assert isinstance(result, GitHubProvider)

    def test_partial_github_config_falls_through(self):
        """Partial GitHub vars (missing MCP_BASE_URL) → falls through to None."""
        env = {
            "MCP_GITHUB_CLIENT_ID": "test-id",
            "MCP_GITHUB_CLIENT_SECRET": "test-secret",
        }
        with patch.dict(os.environ, env, clear=True):
            result = _build_auth()
            assert result is None

    def test_partial_github_config_with_token_uses_token(self):
        """Partial GitHub vars + MCP_AUTH_TOKEN → uses bearer token."""
        from fastmcp.server.auth import StaticTokenVerifier

        env = {
            "MCP_GITHUB_CLIENT_ID": "test-id",
            "MCP_AUTH_TOKEN": "my-token",
        }
        with patch.dict(os.environ, env, clear=True):
            result = _build_auth()
            assert isinstance(result, StaticTokenVerifier)


@pytest.mark.usefixtures("isolated_caches")
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


class TestResponseCachingMiddleware:
    """Tests for ResponseCachingMiddleware configuration."""

    def test_middleware_is_registered(self):
        """Test that ResponseCachingMiddleware is registered with the MCP server."""
        assert len(mcp.middleware) >= 1, "Expected at least one middleware registered"

    def test_middleware_is_response_caching_type(self):
        """Test that the registered middleware is ResponseCachingMiddleware."""
        caching_middleware = [
            m for m in mcp.middleware if isinstance(m, ResponseCachingMiddleware)
        ]
        assert len(caching_middleware) == 1, (
            "Expected exactly one ResponseCachingMiddleware"
        )

    def test_middleware_has_memory_store_backend(self):
        """Test that the middleware is configured with MemoryStore backend."""
        from key_value.aio.stores.memory import MemoryStore

        caching_middleware = next(
            (m for m in mcp.middleware if isinstance(m, ResponseCachingMiddleware)),
            None,
        )
        assert caching_middleware is not None, "ResponseCachingMiddleware not found"

        # The middleware stores the backend in _backend attribute
        assert hasattr(caching_middleware, "_backend"), (
            "Middleware should have _backend attribute"
        )
        assert isinstance(caching_middleware._backend, MemoryStore), (
            "Backend should be MemoryStore"
        )


class TestServerRegistration:
    """Verify all tools, resources, and prompts register without errors."""

    @pytest.mark.asyncio
    async def test_expected_tools_registered(self):
        """Test that all expected tools are registered (allows additions)."""
        tools = {t.name for t in await mcp.list_tools()}
        expected = {
            "search_items",
            "create_item",
            "get_item",
            "modify_item",
            "delete_item",
            "get_variant_details",
            "check_inventory",
            "list_low_stock_items",
            "create_purchase_order",
            "receive_purchase_order",
            "verify_order_document",
            "create_sales_order",
            "create_product",
            "create_material",
            "create_manufacturing_order",
            "fulfill_order",
        }
        missing = expected - tools
        assert not missing, f"Expected tools not registered: {missing}"

    @pytest.mark.asyncio
    async def test_all_tools_have_annotations(self):
        """Test that every tool has annotations set."""
        for tool in await mcp.list_tools():
            assert tool.annotations is not None, f"{tool.name} missing annotations"

    @pytest.mark.asyncio
    async def test_all_tools_have_tags(self):
        """Test that every tool has tags set."""
        for tool in await mcp.list_tools():
            assert tool.tags, f"{tool.name} missing tags"

    @pytest.mark.asyncio
    async def test_expected_prompts_registered(self):
        """Test that all expected prompts are registered (allows additions)."""
        prompts = {p.name for p in await mcp.list_prompts()}
        expected = {"reorder_low_stock", "receive_delivery", "fulfill_sales_order"}
        missing = expected - prompts
        assert not missing, f"Expected prompts not registered: {missing}"

    @pytest.mark.asyncio
    async def test_expected_resources_registered(self):
        """Test that key resources are registered."""
        resource_uris = {str(r.uri) for r in await mcp.list_resources()}
        assert "katana://help" in resource_uris
        assert "katana://inventory/items" in resource_uris
