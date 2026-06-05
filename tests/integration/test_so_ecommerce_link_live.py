"""Live write test: ecommerce storefront deep-link round-trips (#913).

Creates a synthetic sales order carrying ecommerce metadata on the test tenant,
reads it back, and asserts the ``ecommerce_*`` fields round-trip as the literal
camelCase key *and* that :func:`ecommerce_storefront_url` builds the expected
"Open in {platform}" link from the persisted values. Covers a Shopify order
(verified against a real captured Katana payload — ``katana.myshopify.com`` /
``19433769``) and a BigCommerce slug order.

This is the empirical proof behind the feature: the wire stores
``ecommerce_order_type`` verbatim (no coercion), and ``ecommerce_store_name``
holds a host/slug the templates can interpolate. It's also the permanent
regression guard.

Cleanup: the ecommerce fields are **create-only** (PATCH rejects them), so
there's no in-place revert — cleanup is a delete. Per the SDT-tagging contract
(``tests/integration/README.md``) every created SO is SDT-tagged, recorded to
the ledger immediately after create (belt-and-suspenders if the process dies),
and deleted in a ``finally`` block. Skips when ``KATANA_TEST_API_KEY`` is unset
(the skip lives in the ``live_client`` fixture).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest
from katana_mcp.web_urls import ecommerce_storefront_url

from katana_public_api_client import KatanaClient
from katana_public_api_client.api.sales_order import (
    create_sales_order,
    delete_sales_order,
    get_all_sales_orders,
    get_sales_order,
)
from katana_public_api_client.client_types import UNSET
from katana_public_api_client.models import CreateSalesOrderRequest, SalesOrder
from katana_public_api_client.models.create_sales_order_request_sales_order_rows_item import (
    CreateSalesOrderRequestSalesOrderRowsItem,
)
from katana_public_api_client.utils import unwrap_as, unwrap_data

_scripts_dir = str(Path(__file__).resolve().parents[2] / "scripts")
# Scope the sys.path mutation to just this import: insert, import, then remove
# in a finally so the entry doesn't linger for the whole test session (where it
# could shadow other imports or shift resolution order). spec_drift_verify is
# cached in sys.modules after the first import, so dropping the path is safe.
sys.path.insert(0, _scripts_dir)
try:
    from spec_drift_verify import (  # type: ignore[import-not-found]
        SDT_PREFIX,
        record_artifact,
    )
finally:
    sys.path.remove(_scripts_dir)

pytestmark = [pytest.mark.integration, pytest.mark.live, pytest.mark.asyncio]


def _clean(value: Any) -> Any:
    return None if (value is UNSET or value is None) else value


async def _known_customer_and_variant(client: KatanaClient) -> tuple[int, int]:
    """Source a valid customer + variant from an existing SO so the created
    order references real entities (avoids tenant-specific fixtures)."""
    # page=1 pins a single GET: an explicit page param disables the
    # PaginationTransport auto-pagination that limit=1 alone would otherwise
    # trigger (which, at page_size=1, walks up to max_pages GETs).
    listing = await get_all_sales_orders.asyncio_detailed(
        client=client, limit=1, page=1
    )
    data = unwrap_data(listing)
    if not data:
        pytest.skip("test tenant has no sales orders to source a customer/variant from")
    full = await get_sales_order.asyncio_detailed(client=client, id=data[0].id)
    so = unwrap_as(full, SalesOrder)
    rows = _clean(so.sales_order_rows) or []
    if not rows:
        pytest.skip("source sales order has no rows to source a variant from")
    customer_id = _clean(so.customer_id)
    variant_id = _clean(rows[0].variant_id)
    # Both must be present or the create call below fails for an unrelated
    # reason (missing FK) instead of testing the ecommerce round-trip — skip
    # with a clear message rather than emit a confusing live-API failure.
    if customer_id is None or variant_id is None:
        pytest.skip(
            "source sales order is missing a customer_id or row variant_id to reference"
        )
    return customer_id, variant_id


@pytest.mark.parametrize(
    ("order_type", "store", "order_id", "expected_url"),
    [
        (
            "shopify",
            "katana.myshopify.com",
            "19433769",
            "https://katana.myshopify.com/admin/orders/19433769",
        ),
        (
            "bigCommerce",
            "acme",
            "777",
            "https://store-acme.mybigcommerce.com/manage/orders/777",
        ),
    ],
)
async def test_ecommerce_fields_round_trip_and_build_link(
    live_client: KatanaClient,
    order_type: str,
    store: str,
    order_id: str,
    expected_url: str,
) -> None:
    customer_id, variant_id = await _known_customer_and_variant(live_client)

    request = CreateSalesOrderRequest(
        customer_id=customer_id,
        order_no=f"{SDT_PREFIX}-ECOM-{order_type}",
        sales_order_rows=[
            CreateSalesOrderRequestSalesOrderRowsItem(quantity=1, variant_id=variant_id)
        ],
        ecommerce_order_type=order_type,
        ecommerce_store_name=store,
        ecommerce_order_id=order_id,
    )
    created = await create_sales_order.asyncio_detailed(
        client=live_client, body=request
    )
    # unwrap_as raises (loudly failing the test) on a non-2xx / error body.
    so_id = _clean(unwrap_as(created, SalesOrder).id)
    # Pin the failure at the real cause site: a missing id would otherwise
    # surface as a confusing error in record_artifact / get / delete below.
    assert so_id is not None, "create_sales_order returned a SalesOrder without an id"

    # Enter the try BEFORE recording the artifact: once so_id is known the SO
    # exists on the tenant and must be deleted, so any failure from here on
    # (including record_artifact itself) has to fall through to the finally.
    try:
        record_artifact(endpoint="/sales_orders", entity_id=so_id, issue="#913")
        got = await get_sales_order.asyncio_detailed(client=live_client, id=so_id)
        parsed = unwrap_as(got, SalesOrder)
        # The literal camelCase key must round-trip with no coercion.
        assert _clean(parsed.ecommerce_order_type) == order_type
        assert _clean(parsed.ecommerce_store_name) == store
        assert _clean(parsed.ecommerce_order_id) == order_id
        # And the persisted values build exactly the expected storefront link.
        assert (
            ecommerce_storefront_url(
                _clean(parsed.ecommerce_order_type),
                _clean(parsed.ecommerce_store_name),
                _clean(parsed.ecommerce_order_id),
            )
            == expected_url
        )
    finally:
        deleted = await delete_sales_order.asyncio_detailed(
            client=live_client, id=so_id
        )
        assert deleted.status_code in (200, 204), (
            f"cleanup delete returned {deleted.status_code}"
        )


async def test_ecommerce_fields_are_create_only_patch_rejected(
    live_client: KatanaClient,
) -> None:
    """The ecommerce_* fields are create-only: ``PATCH /sales_orders/{id}``
    rejects them outright (HTTP 422 ``additionalProperties``) and leaves the
    persisted values untouched. This is the empirical proof behind the
    "create-only" wording in the OpenAPI field descriptions and the create-time
    advisory guard — the modify endpoint has no schema slot for them, so a typo
    can only be caught at creation. Verified live 2026-06-05 (#913).
    """
    customer_id, variant_id = await _known_customer_and_variant(live_client)

    request = CreateSalesOrderRequest(
        customer_id=customer_id,
        order_no=f"{SDT_PREFIX}-ECOM-PATCH",
        sales_order_rows=[
            CreateSalesOrderRequestSalesOrderRowsItem(quantity=1, variant_id=variant_id)
        ],
        ecommerce_order_type="shopify",
        ecommerce_store_name="acme.myshopify.com",
        ecommerce_order_id="111111",
    )
    created = await create_sales_order.asyncio_detailed(
        client=live_client, body=request
    )
    so_id = _clean(unwrap_as(created, SalesOrder).id)
    assert so_id is not None, "create_sales_order returned a SalesOrder without an id"

    try:
        record_artifact(endpoint="/sales_orders", entity_id=so_id, issue="#913")
        # The generated update model has no ecommerce_* params (the spec omits
        # them from UpdateSalesOrderRequest), so send a raw PATCH to prove the
        # *server* rejects them — not just our client.
        resp = await live_client.get_async_httpx_client().patch(
            f"/sales_orders/{so_id}",
            json={
                "ecommerce_order_type": "wooCommerce",
                "ecommerce_store_name": "patched.example.com",
                "ecommerce_order_id": "999999",
            },
        )
        assert resp.status_code == 422, (
            f"expected 422 rejecting ecommerce_* on PATCH, got {resp.status_code}"
        )
        # Assert on the structured Ajv error payload rather than substring-
        # matching the message text, which is brittle to formatting changes.
        # Katana wraps error bodies in {"error": {...}} on the wire (verified
        # live), while the spec models DetailedErrorResponse flat ({"details":
        # [...]}); tolerate both envelopes so the assertion is robust to that
        # documented-vs-actual difference. Each rejected field surfaces as a
        # details entry with code "additionalProperties" and info.additionalProperty.
        payload = resp.json()
        details = payload.get("error", payload).get("details") or []
        rejected = {
            d["info"]["additionalProperty"]
            for d in details
            if d.get("code") == "additionalProperties"
        }
        assert {
            "ecommerce_order_type",
            "ecommerce_store_name",
            "ecommerce_order_id",
        } <= rejected, (
            f"PATCH did not reject all three ecommerce_* fields; got {rejected}"
        )

        # And the persisted values are untouched by the rejected PATCH.
        got = await get_sales_order.asyncio_detailed(client=live_client, id=so_id)
        parsed = unwrap_as(got, SalesOrder)
        assert _clean(parsed.ecommerce_order_type) == "shopify"
        assert _clean(parsed.ecommerce_store_name) == "acme.myshopify.com"
        assert _clean(parsed.ecommerce_order_id) == "111111"
    finally:
        deleted = await delete_sales_order.asyncio_detailed(
            client=live_client, id=so_id
        )
        assert deleted.status_code in (200, 204), (
            f"cleanup delete returned {deleted.status_code}"
        )
