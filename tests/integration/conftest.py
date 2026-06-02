"""Fixtures for live-tenant integration tests (issue #837, Phase 2).

The single entry point is the ``live_client`` fixture: it builds a
:class:`~katana_public_api_client.KatanaClient` bound to the test tenant via
:func:`~katana_public_api_client.testing.make_test_client` and yields it inside
an ``async with`` block. If ``KATANA_TEST_API_KEY`` is unset the helper raises
:class:`~katana_public_api_client.testing.MissingTestCredentialsError` and the
fixture turns *that specific* error into a ``pytest.skip`` — so the whole
``tests/integration/`` suite is a no-op for anyone without a test key. Any
*other* failure from the helper propagates and fails the test loudly, rather
than being masked as a skip.

This is the *only* place the skip lives. ``make_test_client`` itself fails
loud (never falls back to the prod key); the auto-skip is a test-harness
concern, so it belongs in the fixture, not the helper.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
import pytest_asyncio

from katana_public_api_client import KatanaClient
from katana_public_api_client.testing import (
    MissingTestCredentialsError,
    make_test_client,
)


@pytest_asyncio.fixture
async def live_client() -> AsyncIterator[KatanaClient]:
    """Yield a KatanaClient bound to the test tenant, or skip if unconfigured.

    Tuned for fast test feedback: fewer retries and a hard page cap so a
    misbehaving endpoint can't fan out into hundreds of live calls.

    Yields:
        KatanaClient: entered client whose requests hit the test tenant.
    """
    try:
        client = make_test_client(max_retries=2, max_pages=5)
    except MissingTestCredentialsError as exc:
        pytest.skip(str(exc))

    async with client:
        yield client
