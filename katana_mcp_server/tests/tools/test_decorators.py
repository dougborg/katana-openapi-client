"""Tests for the @cache_read / @cache_write decorators.

The decorator's call-time fan-out is exercised indirectly via every tool
test that mocks ``decorators._sync_fns``. This file pins behaviors that
no other test covers — most importantly the decoration-time fail-fast
on unregistered ``Cached*`` classes (#472 Phase C), which prevents a
typo from becoming a silent stale-cache read.
"""

from __future__ import annotations

import pytest
from katana_mcp.tools.decorators import cache_read

from katana_public_api_client.models_pydantic._generated import (
    CachedSalesOrder,
    CachedVariant,
)


def test_cache_read_raises_on_unregistered_class():
    """Decorating with a Cached* class that isn't in the catalog registry
    raises ValueError at decoration time. Catches a typo at import, not
    as a silent stale-cache read on the first request.

    ``CachedSalesOrder`` is a transactional cache class — it's a real
    ``Cached*`` row class that the catalog @cache_read registry does not
    own (the typed cache syncs sales orders via a different code path).
    Using it here exercises the validation without needing a fake class.
    """
    with pytest.raises(ValueError, match="unregistered Cached"):

        @cache_read(CachedSalesOrder)
        async def _impl(request, context):  # pragma: no cover — never called
            return None


def test_cache_read_accepts_registered_class():
    """Sanity: a registered catalog class decorates without raising."""

    @cache_read(CachedVariant)
    async def _impl(request, context):  # pragma: no cover — never called
        return None

    # No exception means the validation pass cleared.
    assert callable(_impl)
