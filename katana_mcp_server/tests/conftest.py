"""Shared pytest fixtures for MCP server tests."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio


@pytest_asyncio.fixture
async def katana_context():
    """Create a mock context for integration tests that uses real KatanaClient.

    This fixture is used by integration tests to get a context with a real
    KatanaClient initialized from environment variables.

    The fixture requires KATANA_API_KEY to be set in the environment.
    If not set, integration tests will be skipped.

    Returns:
        Mock context object with request_context.lifespan_context.client
        pointing to a real KatanaClient instance.
    """
    # Check if API key is available
    api_key = os.getenv("KATANA_API_KEY")
    if not api_key:
        pytest.skip("KATANA_API_KEY not set - skipping integration test")

    # Import here to avoid import errors if client isn't installed
    try:
        from katana_public_api_client import KatanaClient
    except ImportError:
        pytest.skip("katana_public_api_client not installed")

    # Create mock context structure matching FastMCP
    context = MagicMock()
    mock_request_context = MagicMock()
    mock_lifespan_context = MagicMock()

    # Initialize real KatanaClient
    base_url = os.getenv("KATANA_BASE_URL", "https://api.katanamrp.com/v1")
    client = KatanaClient(
        api_key=api_key,
        base_url=base_url,
        timeout=30.0,
        max_retries=3,  # Fewer retries for tests
        max_pages=10,  # Limit pages for tests
    )

    # Attach client to mock context
    mock_lifespan_context.client = client
    mock_request_context.lifespan_context = mock_lifespan_context
    context.request_context = mock_request_context

    yield context

    # Note: KatanaClient cleanup is handled automatically


# ============================================================================
# Fixtures for tool tests (merged from tests/tools/conftest.py)
# ============================================================================


def create_mock_context():
    """Create a mock context with proper FastMCP structure.

    Returns:
        Tuple of (context, lifespan_context) where context has the structure:
        context.request_context.lifespan_context.client

    This helper creates the nested mock structure that FastMCP uses to provide
    the KatanaClient to tool implementations.
    """
    context = MagicMock()
    mock_request_context = MagicMock()
    mock_lifespan_context = MagicMock()
    context.request_context = mock_request_context
    mock_request_context.lifespan_context = mock_lifespan_context

    # Set up cache mock with async methods
    mock_cache = AsyncMock()
    mock_cache.get_last_synced = AsyncMock(return_value=None)
    mock_cache.sync = AsyncMock()
    mock_cache.smart_search = AsyncMock(return_value=[])
    mock_cache.get_by_sku = AsyncMock(return_value=None)
    mock_cache.get_by_id = AsyncMock(return_value=None)
    mock_cache.mark_dirty = AsyncMock()
    mock_lifespan_context.cache = mock_cache

    return context, mock_lifespan_context


@pytest.fixture
def mock_context():
    """Fixture providing a mock FastMCP context.

    Returns:
        Tuple of (context, lifespan_context) ready for test use.
    """
    return create_mock_context()


@pytest_asyncio.fixture
async def typed_cache_engine():
    """Per-test in-memory ``TypedCacheEngine``.

    Uses ``in_memory=True`` — a ``:memory:`` SQLite backed by
    ``StaticPool`` so concurrent sessions share one DB within the engine.
    No filesystem I/O per test. Engine and schema are created fresh per
    test function; if this pattern starts feeling slow as the suite
    grows, upgrade to a session-scoped engine with per-test SAVEPOINT
    rollback (SQLAlchemy's "joining an external transaction" recipe).
    """
    from katana_mcp.typed_cache import TypedCacheEngine

    engine = TypedCacheEngine(in_memory=True)
    await engine.open()
    try:
        yield engine
    finally:
        await engine.close()


def patch_typed_cache_sync(entity_type: str):
    """Patch a cache-backed list tool's ``ensure_<entity>_synced`` to a no-op.

    Cache-backed list impls (``_list_<entity>_impl``) do a deferred
    ``from katana_mcp.typed_cache import ensure_<entity>_synced`` inside
    the function body, then call it to refresh the cache before querying.
    Tests that seed the cache directly want that call stubbed so it
    doesn't fire a real API request — and the patch must target the
    source module (``katana_mcp.typed_cache``), not the importer, because
    the deferred import means the name doesn't exist in the tool module's
    namespace until the function runs.

    Usage from a per-test-module fixture::

        @pytest.fixture
        def no_sync():
            with patch_typed_cache_sync("sales_orders"):
                yield

    ``entity_type`` is the plural suffix used in the sync helper's name
    (``sales_orders`` → ``ensure_sales_orders_synced``).
    """

    async def _noop(_client, _cache):
        return None

    return patch(
        f"katana_mcp.typed_cache.ensure_{entity_type}_synced",
        side_effect=_noop,
    )


@pytest_asyncio.fixture
async def context_with_typed_cache(typed_cache_engine):
    """Mock context with a real in-memory ``TypedCacheEngine`` attached.

    Cache-backed tools (``list_sales_orders`` post-#342) need a real
    engine on ``services.typed_cache`` — ``MagicMock`` isn't usable as
    an ``async with`` session. Tests typically seed the cache directly
    via the engine's session and patch the sync helper to a no-op so
    the tool reads the seeded rows without attempting an API fetch.

    Yields:
        Tuple of ``(context, lifespan_context, typed_cache_engine)``.
    """
    context, lifespan_ctx = create_mock_context()
    lifespan_ctx.typed_cache = typed_cache_engine
    yield context, lifespan_ctx, typed_cache_engine


@pytest.fixture
def mock_get_purchase_order():
    """Fixture for mocking get_purchase_order API call."""
    from katana_public_api_client.api.purchase_order import (
        get_purchase_order as api_get_purchase_order,
    )

    mock_api = AsyncMock()
    api_get_purchase_order.asyncio_detailed = mock_api
    return mock_api


@pytest.fixture
def mock_receive_purchase_order():
    """Fixture for mocking receive_purchase_order API call."""
    from katana_public_api_client.api.purchase_order import (
        receive_purchase_order as api_receive_purchase_order,
    )

    mock_api = AsyncMock()
    api_receive_purchase_order.asyncio_detailed = mock_api
    return mock_api
