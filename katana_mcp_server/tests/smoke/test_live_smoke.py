"""Live smoke tests for high-traffic read-only MCP tools (issue #837, Phase 4).

Each test calls a tool impl through the ``live_smoke_context`` and asserts the
response is *structurally* valid — the right model, a list payload, a
non-negative count. The impls are decorated with ``@cache_read(...)``, which
syncs the entity into the context's typed cache before running, so the tests
don't sync explicitly. Assertions never pin exact values: the test tenant's
data drifts. The point is "auth + sync + tool wiring work end-to-end", not
"there are exactly N locations".

These skip automatically when ``KATANA_TEST_API_KEY`` is unset (the skip lives
in the ``live_smoke_context`` fixture).
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from katana_mcp.tools.foundation.bin_transfers import (
    ListBinInventoryRequest,
    ListBinInventoryResponse,
    ListBinTransfersRequest,
    ListBinTransfersResponse,
    ListStorageBinsRequest,
    ListStorageBinsResponse,
    _list_bin_inventory_impl,
    _list_bin_transfers_impl,
    _list_storage_bins_impl,
)
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

pytestmark = [pytest.mark.integration, pytest.mark.smoke, pytest.mark.asyncio]


async def test_list_locations(live_smoke_context: MagicMock) -> None:
    """list_locations syncs (via @cache_read) and returns a Locations response."""
    response = await _list_locations_impl(ListLocationsRequest(), live_smoke_context)

    assert isinstance(response, ListLocationsResponse)
    assert response.total_count >= 0
    assert isinstance(response.locations, list)
    # Every tenant has at least one location; assert presence without pinning it.
    assert response.locations, "test tenant should have at least one location"
    assert response.locations[0].name


async def test_list_suppliers(live_smoke_context: MagicMock) -> None:
    """list_suppliers syncs (via @cache_read) and returns a Suppliers response."""
    response = await _list_suppliers_impl(ListSuppliersRequest(), live_smoke_context)

    assert isinstance(response, ListSuppliersResponse)
    assert response.total_count >= 0
    # Suppliers may legitimately be empty on a fresh tenant — only assert shape.
    assert isinstance(response.suppliers, list)


async def test_list_tax_rates(live_smoke_context: MagicMock) -> None:
    """list_tax_rates syncs (via @cache_read) and returns a TaxRates response."""
    response = await _list_tax_rates_impl(ListTaxRatesRequest(), live_smoke_context)

    assert isinstance(response, ListTaxRatesResponse)
    assert response.total_count >= 0
    assert isinstance(response.tax_rates, list)


async def test_list_bin_transfers(live_smoke_context: MagicMock) -> None:
    """list_bin_transfers syncs the bin_transfer entity (full fetch — no
    updated_at_min support) and returns a structurally valid response.

    Bin transfers were live-verified on the test tenant during #942; the
    tenant may legitimately have zero at any given time, so only the shape
    is asserted.
    """
    response = await _list_bin_transfers_impl(
        ListBinTransfersRequest(include_rows=True), live_smoke_context
    )

    assert isinstance(response, ListBinTransfersResponse)
    assert response.total_count >= 0
    assert isinstance(response.transfers, list)
    for transfer in response.transfers:
        assert transfer.id > 0
        assert transfer.status in (None, "CREATED", "IN_TRANSIT", "DONE")


async def test_list_storage_bins(live_smoke_context: MagicMock) -> None:
    """list_storage_bins reads the bare-array /bin_locations endpoint live."""
    response = await _list_storage_bins_impl(
        ListStorageBinsRequest(), live_smoke_context
    )

    assert isinstance(response, ListStorageBinsResponse)
    assert response.total_count >= 0
    for bin_info in response.bins:
        assert bin_info.id > 0
        assert bin_info.bin_name
        assert bin_info.location_id > 0


async def test_list_bin_inventory(live_smoke_context: MagicMock) -> None:
    """list_bin_inventory reads per-bin levels live at VARIANT granularity."""
    response = await _list_bin_inventory_impl(
        ListBinInventoryRequest(limit=10), live_smoke_context
    )

    assert isinstance(response, ListBinInventoryResponse)
    assert response.granularity == "VARIANT"
    assert response.total_count >= 0
    for entry in response.entries:
        # Quantities coerce from wire decimal strings to floats.
        assert entry.quantity_in_stock is None or isinstance(
            entry.quantity_in_stock, float
        )
