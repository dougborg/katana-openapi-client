"""Pin required-field sets for create endpoints against the live tenant (#1045).

#1034 relaxed two ``required`` lists to match the live gateway, dropping
``stock_adjustment_number`` from ``CreateStockAdjustmentRequest`` and
``stock_transfer_number`` from ``CreateStockTransferRequest``. That change
rested on the *published* gateway spec rather than on observed behaviour —
the gateway not marking a field required and the API actually accepting its
omission are different claims, and only the first had been checked.

#1040 is the cautionary case: our search request shape matched neither the
wire nor upstream, and the client shipped a body the API answered with 422.
A published spec is not evidence.

**These tests create nothing.** They POST an *empty* body and read the
validation error. Validation runs before creation, so no tenant data is
written and the SDT-tagging + cleanup contract in ``README.md`` does not
apply. The 422 enumerates precisely which properties the API considers
required, which is exactly the claim under test — a far cheaper and safer
probe than creating a real stock adjustment and deleting it afterwards
(which would move inventory on the tenant in between).

Assertions are written as **subset/absence** checks rather than exact-set
equality: a future upstream addition of a new required field should be
caught by the endpoint's own drift audit, not by breaking this test.
"""

from __future__ import annotations

from typing import Any

import pytest

from katana_public_api_client import KatanaClient

pytestmark = [pytest.mark.integration, pytest.mark.live, pytest.mark.asyncio]


async def _required_properties(client: KatanaClient, path: str) -> set[str]:
    """POST an empty body and return the property names the API demands.

    Creates nothing: the request fails validation before any record is
    written. Returns the ``missingProperty`` values from the 422 detail list.
    """
    response = await client.get_async_httpx_client().post(path, json={})

    assert response.status_code == 422, (
        f"POST {path} with an empty body returned {response.status_code}, "
        "expected 422 from request-body validation. If this endpoint now "
        "accepts an empty body, this probe no longer proves anything."
    )

    payload: dict[str, Any] = response.json()
    details = payload.get("error", {}).get("details", [])
    return {
        info["missingProperty"]
        for detail in details
        if (info := detail.get("info") or {}).get("missingProperty")
    }


async def test_stock_adjustment_number_is_not_required(
    live_client: KatanaClient,
) -> None:
    """``stock_adjustment_number`` is optional on POST /stock_adjustments.

    Pins the #1034 relaxation. If Katana ever makes it mandatory, this fails
    and the ``required`` list in the spec needs restoring.
    """
    required = await _required_properties(live_client, "/stock_adjustments")

    assert "stock_adjustment_number" not in required, (
        "The API now requires stock_adjustment_number; restore it to "
        "CreateStockAdjustmentRequest.required in docs/katana-openapi.yaml."
    )
    # Sanity-check the probe itself: if these stopped being reported, an
    # empty required set would make the assertion above vacuously true.
    assert {"location_id", "stock_adjustment_rows"} <= required, (
        f"Expected location_id and stock_adjustment_rows to be required; got {required}"
    )


async def test_stock_transfer_number_is_not_required(
    live_client: KatanaClient,
) -> None:
    """``stock_transfer_number`` is optional on POST /stock_transfers.

    Pins the #1034 relaxation, as above.
    """
    required = await _required_properties(live_client, "/stock_transfers")

    assert "stock_transfer_number" not in required, (
        "The API now requires stock_transfer_number; restore it to "
        "CreateStockTransferRequest.required in docs/katana-openapi.yaml."
    )
    assert {
        "source_location_id",
        "target_location_id",
        "stock_transfer_rows",
    } <= required, (
        f"Expected the three location/row fields to be required; got {required}"
    )
