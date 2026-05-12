"""Shared pytest fixtures for MCP server tests."""

import os
from collections.abc import Iterator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio


@pytest.fixture(autouse=True)
def _disable_cache_warmup_by_default(
    request: pytest.FixtureRequest,
) -> Iterator[None]:
    """Skip the background cache warm-up unless a test explicitly opts in.

    ``server.lifespan()`` schedules an ``asyncio.create_task`` that fans
    out ``ensure_*_synced`` calls (closes #500 / #593). Tests that don't
    intentionally exercise warmup don't want it kicking off against a
    mock client — it produces noisy logs, racy task lifecycles, and
    unintentional coverage of unrelated code. Tests that want to verify
    warmup behavior opt in with ``@pytest.mark.cache_warmup_enabled``.
    """
    if "cache_warmup_enabled" in request.keywords:
        # Test wants the real warmup path; let MCP_DISABLE_CACHE_WARMUP
        # flow through unchanged (or be set by the test itself).
        yield
        return
    prev = os.environ.get("MCP_DISABLE_CACHE_WARMUP")
    os.environ["MCP_DISABLE_CACHE_WARMUP"] = "1"
    try:
        yield
    finally:
        if prev is None:
            os.environ.pop("MCP_DISABLE_CACHE_WARMUP", None)
        else:
            os.environ["MCP_DISABLE_CACHE_WARMUP"] = prev


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
        context.request_context.lifespan_context.client (and
        ``.typed_cache.catalog`` for catalog reads).

    This helper creates the nested mock structure that FastMCP uses to provide
    the KatanaClient to tool implementations. The ``typed_cache.catalog``
    adapter is mocked with the same six methods the real
    :class:`katana_mcp.typed_cache.queries.CatalogQueries` exposes
    (``get_by_id`` / ``get_by_sku`` / ``get_many_by_ids`` / ``get_all`` /
    ``smart_search`` / ``search_fuzzy``), each returning the empty
    sentinel for the method's natural shape.
    """
    context = MagicMock()
    mock_request_context = MagicMock()
    mock_lifespan_context = MagicMock()
    context.request_context = mock_request_context
    mock_request_context.lifespan_context = mock_lifespan_context

    # Set up typed_cache.catalog mock with the six CatalogQueries methods.
    # Tests override per-method return values via
    # ``lifespan_ctx.typed_cache.catalog.<method>.return_value = ...`` or
    # by reassigning ``AsyncMock(return_value=...)`` on the attribute.
    mock_catalog = AsyncMock()
    mock_catalog.get_by_id = AsyncMock(return_value=None)
    mock_catalog.get_by_sku = AsyncMock(return_value=None)
    mock_catalog.get_many_by_ids = AsyncMock(return_value={})
    mock_catalog.get_all = AsyncMock(return_value=[])
    mock_catalog.smart_search = AsyncMock(return_value=[])
    mock_catalog.search_fuzzy = AsyncMock(return_value=[])
    mock_lifespan_context.typed_cache = MagicMock()
    mock_lifespan_context.typed_cache.catalog = mock_catalog

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
def mock_get_purchase_order(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    """Fixture for mocking get_purchase_order API call.

    Uses ``monkeypatch.setattr`` so pytest restores the original function
    after the test — without it, the mock would leak across the rest of
    the suite (especially under xdist) and produce ordering-dependent
    flakes for any test that hits the real endpoint or installs a
    different mock.
    """
    from katana_public_api_client.api.purchase_order import (
        get_purchase_order as api_get_purchase_order,
    )

    mock_api = AsyncMock()
    monkeypatch.setattr(api_get_purchase_order, "asyncio_detailed", mock_api)
    return mock_api


@pytest.fixture
def mock_receive_purchase_order(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    """Fixture for mocking receive_purchase_order API call.

    Uses ``monkeypatch.setattr`` so pytest restores the original function
    after the test — see ``mock_get_purchase_order`` for the rationale.
    """
    from katana_public_api_client.api.purchase_order import (
        receive_purchase_order as api_receive_purchase_order,
    )

    mock_api = AsyncMock()
    monkeypatch.setattr(api_receive_purchase_order, "asyncio_detailed", mock_api)
    return mock_api
