"""Fixtures for live MCP smoke tests (issue #837, Phase 4).

The ``live_smoke_context`` fixture wires up the real runtime dependency graph
against the test tenant:

* a :class:`KatanaClient` from :func:`make_test_client` (test tenant, never
  prod — skips when ``KATANA_TEST_API_KEY`` is unset, the single skip site),
* a fresh in-memory :class:`TypedCacheEngine`, and
* a :class:`Services` container exposed exactly the way the FastMCP lifespan
  exposes it, so ``get_services(context)`` resolves inside tool impls.

Tests seed only the reference data they query (via the per-entity
``ensure_*_synced`` helpers) rather than running the full cache warm-up — a
smoke test wants speed and determinism, not a complete sync.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from katana_mcp.services.dependencies import Services
from katana_mcp.typed_cache import TypedCacheEngine

from katana_public_api_client.testing import (
    MissingTestCredentialsError,
    make_test_client,
)


@pytest_asyncio.fixture
async def live_smoke_context() -> AsyncIterator[MagicMock]:
    """Yield a FastMCP-shaped context backed by the test tenant.

    The yielded object mirrors the structure tools expect:
    ``context.request_context.lifespan_context`` is a real :class:`Services`
    (``get_services`` returns it directly), so cache-backed ``list_*`` tools
    resolve their client + typed cache. Skips when the test key is unset.

    Yields:
        MagicMock: context whose ``request_context.lifespan_context`` is a
            live :class:`Services` (client + in-memory typed cache).
    """
    try:
        client = make_test_client(max_retries=2, max_pages=5)
    except MissingTestCredentialsError as exc:
        pytest.skip(str(exc))

    async with client:
        cache = TypedCacheEngine(in_memory=True)
        await cache.open()
        try:
            services = Services(client=client, typed_cache=cache)
            # Build the nested shape explicitly (rather than leaning on
            # MagicMock's implicit attribute creation) so the context matches
            # what FastMCP provides and stays robust if get_services() tightens
            # its checks. Mirrors the `katana_context` fixture in tests/conftest.
            request_context = MagicMock()
            request_context.lifespan_context = services
            context = MagicMock()
            context.request_context = request_context
            yield context
        finally:
            await cache.close()
