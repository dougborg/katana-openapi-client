"""Regression tests for spec-vs-wire response-shape drift on two endpoints.

- #575: ``GET /bin_locations`` returns a **bare JSON array** on the wire, not
  a ``{"data": [...]}`` envelope. The spec previously declared a
  ``StorageBinListResponse`` wrapper, so the generated parser tried
  ``StorageBinListResponse.from_dict(<list>)`` and raised. Aligned to a bare
  ``array`` of ``StorageBin``.
- #820: ``POST /bom_rows`` returns ``HTTP 200`` with the full ``BomRow`` body,
  not ``204 No Content``. The spec previously declared ``204``, so the parser
  had no 200 branch and silently discarded the body.
"""

from collections.abc import Callable

import httpx
import pytest

from katana_public_api_client import KatanaClient
from katana_public_api_client.api.bom_row import create_bom_row
from katana_public_api_client.api.storage_bin import get_all_storage_bins
from katana_public_api_client.models.bom_row import BomRow
from katana_public_api_client.models.create_bom_row_request import CreateBomRowRequest
from katana_public_api_client.models.storage_bin import StorageBin
from katana_public_api_client.utils import unwrap_as


def _client_with_mock_transport(
    handler: Callable[[httpx.Request], httpx.Response],
) -> KatanaClient:
    """Build a KatanaClient backed by an ``httpx.MockTransport``; caller must use ``async with`` to close it."""
    return KatanaClient(
        api_key="test-api-key",
        base_url="https://api.katana.test",
        transport=httpx.MockTransport(handler),
    )


@pytest.mark.asyncio
async def test_get_bin_locations_parses_bare_array() -> None:
    """``GET /bin_locations`` returns a bare array → ``list[StorageBin]`` (regression for #575)."""
    bins_payload = [
        {
            "id": 12345,
            "name": "Bin-2",
            "bin_name": "Bin-2",
            "location_id": 12346,
            "created_at": "2020-10-23T10:37:05.085Z",
            "updated_at": "2020-10-23T10:37:05.085Z",
            "deleted_at": None,
        },
        {
            "id": 12346,
            "name": "Bin-3",
            "bin_name": "Bin-3",
            "location_id": 12346,
            "created_at": "2020-10-24T10:37:05.085Z",
            "updated_at": "2020-10-24T10:37:05.085Z",
            "deleted_at": None,
        },
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/bin_locations"
        # Bare array on the wire — NOT wrapped in ``{"data": [...]}``.
        return httpx.Response(200, json=bins_payload)

    async with _client_with_mock_transport(handler) as client:
        response = await get_all_storage_bins.asyncio_detailed(client=client)

    bins = unwrap_as(response, list)
    assert isinstance(bins, list)
    assert len(bins) == 2
    assert all(isinstance(b, StorageBin) for b in bins)
    assert bins[0].bin_name == "Bin-2"
    assert bins[0].location_id == 12346
    assert bins[1].bin_name == "Bin-3"


@pytest.mark.asyncio
async def test_get_bin_locations_parses_empty_bare_array() -> None:
    """Empty result is a bare ``[]``, not ``{"data": []}`` (regression for #575)."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/bin_locations"
        return httpx.Response(200, json=[])

    async with _client_with_mock_transport(handler) as client:
        response = await get_all_storage_bins.asyncio_detailed(client=client)

    bins = unwrap_as(response, list)
    assert bins == []


@pytest.mark.asyncio
async def test_create_bom_row_parses_200_body() -> None:
    """``POST /bom_rows`` returns 200 with the full ``BomRow`` body (regression for #820)."""
    bom_row_payload = {
        "id": "bf9bffc3-4d9d-4238-8e8c-5d2b183d6fc2",
        "product_item_id": 17224137,
        "product_variant_id": 40674815,
        "ingredient_variant_id": 40674816,
        "quantity": 2,
        "rank": 0,
        "created_at": "2026-05-22T18:37:19.852Z",
        "updated_at": "2026-05-22T18:37:19.852Z",
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/bom_rows"
        return httpx.Response(200, json=bom_row_payload)

    async with _client_with_mock_transport(handler) as client:
        response = await create_bom_row.asyncio_detailed(
            client=client,
            body=CreateBomRowRequest(
                product_item_id=17224137,
                product_variant_id=40674815,
                ingredient_variant_id=40674816,
                quantity=2,
            ),
        )

    row = unwrap_as(response, BomRow)
    assert isinstance(row, BomRow)
    assert str(row.id) == "bf9bffc3-4d9d-4238-8e8c-5d2b183d6fc2"
    assert row.product_variant_id == 40674815
    assert row.rank == 0
