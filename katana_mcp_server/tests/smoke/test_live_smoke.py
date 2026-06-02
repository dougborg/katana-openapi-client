"""Live smoke tests for high-traffic read-only MCP tools (issue #837, Phase 4).

Each test seeds just the reference data it needs into the in-memory typed cache
(via ``ensure_*_synced``), then calls the tool impl through the
``live_smoke_context`` and asserts the response is *structurally* valid — the
right model, a list payload, a non-negative count. Assertions never pin exact
values: the test tenant's data drifts. The point is "auth + sync + tool wiring
work end-to-end", not "there are exactly N locations".

These skip automatically when ``KATANA_TEST_API_KEY`` is unset (the skip lives
in the ``live_smoke_context`` fixture).
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from katana_mcp.services.dependencies import get_services
from katana_mcp.tools.foundation.reference import (
    ListLocationsRequest,
    ListLocationsResponse,
    ListSuppliersRequest,
    ListSuppliersResponse,
    ListTaxRatesRequest,
    ListTaxRatesResponse,
    _list_locations_impl,
    _list_suppliers_impl,
    _list_tax_rates_impl,
)
from katana_mcp.typed_cache.sync import (
    ensure_locations_synced,
    ensure_suppliers_synced,
    ensure_tax_rates_synced,
)

pytestmark = [pytest.mark.integration, pytest.mark.smoke, pytest.mark.asyncio]


async def test_list_locations(live_smoke_context: MagicMock) -> None:
    """list_locations syncs from the tenant and returns a Locations response."""
    services = get_services(live_smoke_context)
    await ensure_locations_synced(services.client, services.typed_cache)

    response = await _list_locations_impl(ListLocationsRequest(), live_smoke_context)

    assert isinstance(response, ListLocationsResponse)
    assert response.total_count >= 0
    assert isinstance(response.locations, list)
    # Every tenant has at least one location; assert presence without pinning it.
    assert response.locations, "test tenant should have at least one location"
    assert response.locations[0].name


async def test_list_suppliers(live_smoke_context: MagicMock) -> None:
    """list_suppliers syncs from the tenant and returns a Suppliers response."""
    services = get_services(live_smoke_context)
    await ensure_suppliers_synced(services.client, services.typed_cache)

    response = await _list_suppliers_impl(ListSuppliersRequest(), live_smoke_context)

    assert isinstance(response, ListSuppliersResponse)
    assert response.total_count >= 0
    # Suppliers may legitimately be empty on a fresh tenant — only assert shape.
    assert isinstance(response.suppliers, list)


async def test_list_tax_rates(live_smoke_context: MagicMock) -> None:
    """list_tax_rates syncs from the tenant and returns a TaxRates response."""
    services = get_services(live_smoke_context)
    await ensure_tax_rates_synced(services.client, services.typed_cache)

    response = await _list_tax_rates_impl(ListTaxRatesRequest(), live_smoke_context)

    assert isinstance(response, ListTaxRatesResponse)
    assert response.total_count >= 0
    assert isinstance(response.tax_rates, list)
