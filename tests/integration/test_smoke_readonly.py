"""Read-only smoke tests against the live test tenant (issue #837, Phase 2).

These are the canary tests for the live-integration path: they exercise the
full stack — auth, transport-layer resilience, response parsing — against a
real Katana test tenant, but only touch **read-only** endpoints, so there is
nothing to clean up and no SDT-tagging contract to honour (see
``tests/integration/README.md`` for when that contract *does* apply).

Assertions are structural, not exact-match: the test tenant's data drifts over
time, so we check "the request authenticated and parsed into the right model",
never "there are exactly N users". Every test skips automatically when
``KATANA_TEST_API_KEY`` is unset — the skip lives in the ``live_client``
fixture.
"""

from __future__ import annotations

import pytest

from katana_public_api_client import KatanaClient
from katana_public_api_client.api.custom_fields import (
    get_all_custom_fields_collections,
)
from katana_public_api_client.api.factory import get_factory
from katana_public_api_client.api.user import get_all_users
from katana_public_api_client.models import (
    CustomFieldsCollectionListResponse,
    Factory,
    UserListResponse,
)
from katana_public_api_client.utils import is_success, unwrap_as, unwrap_data

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def test_get_factory(live_client: KatanaClient) -> None:
    """GET /factory authenticates and parses into a Factory model."""
    response = await get_factory.asyncio_detailed(client=live_client)

    assert is_success(response), f"GET /factory returned {response.status_code}"
    factory = unwrap_as(response, Factory)
    # Assert on base_currency_code, not name: ``name`` is Unset on some tenants
    # (the test tenant identifies via ``display_name``), but every factory has a
    # base currency. The exact value drifts, so we only assert presence.
    assert factory.base_currency_code


async def test_get_all_users(live_client: KatanaClient) -> None:
    """GET /users authenticates and parses into a list of users."""
    # Don't pass limit=1: the transport auto-paginates GETs that have no `page`
    # param, so limit=1 would fan out to one request *per user* (capped at the
    # fixture's max_pages). Letting the server use its default page size keeps
    # this to a single request on the small test tenant.
    response = await get_all_users.asyncio_detailed(client=live_client)

    assert is_success(response), f"GET /users returned {response.status_code}"
    unwrap_as(response, UserListResponse)
    # ``data`` is always a list (possibly empty on a fresh tenant).
    users = unwrap_data(response)
    assert isinstance(users, list)


async def test_get_all_custom_fields_collections(live_client: KatanaClient) -> None:
    """GET /custom_fields_collections authenticates and parses into a list."""
    response = await get_all_custom_fields_collections.asyncio_detailed(
        client=live_client
    )

    assert is_success(response), (
        f"GET /custom_fields_collections returned {response.status_code}"
    )
    unwrap_as(response, CustomFieldsCollectionListResponse)
    collections = unwrap_data(response)
    assert isinstance(collections, list)
