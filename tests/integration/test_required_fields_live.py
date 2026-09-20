"""Pin create-request validation against the live tenant (#1045, #1042).

#1034 relaxed two ``required`` lists to match the live gateway, dropping
``stock_adjustment_number`` from ``CreateStockAdjustmentRequest`` and
``stock_transfer_number`` from ``CreateStockTransferRequest``. That change
rested on the *published* gateway spec rather than on observed behaviour —
the gateway not marking a field required and the API actually accepting its
omission are different claims, and only the first had been checked.

#1040 is the cautionary case: our search request shape matched neither the
wire nor upstream, and the client shipped a body the API answered with 422.
A published spec is not evidence.

**These tests create nothing.** They POST an empty body or a deliberately
invalid manufacturing-order ID and read the validation error. Validation
runs before creation, so no tenant data is written and the SDT-tagging +
cleanup contract in ``README.md`` does not apply. The 422 reports required
and disallowed properties without creating and deleting real records
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


async def test_production_batch_transaction_rejects_quantity(
    live_client: KatanaClient,
) -> None:
    """``batch_transaction`` on a production takes ``batch_id`` alone (#1042).

    Our spec pointed this at the shared ``BatchTransaction``, which requires
    ``quantity`` — so every body built through the generated client was
    rejected. Upstream's endpoint-specific ``CompletePartiallyBatchDto``
    declares only ``batch_id`` under ``additionalProperties: false``.

    Creates nothing: ``manufacturing_order_id`` is deliberately invalid, so
    the request never reaches record creation. Schema validation reports the
    extra property alongside the bad id, which is what we assert on.
    """
    invalid_id = {"manufacturing_order_id": -1, "completed_quantity": 1}

    async def _errors(body: dict[str, Any]) -> list[str]:
        response = await live_client.get_async_httpx_client().post(
            "/manufacturing_order_productions", json=body
        )
        assert response.status_code == 422, (
            f"expected 422 from validation, got {response.status_code}"
        )
        details = response.json().get("error", {}).get("details", [])
        assert any(
            d.get("path") == "/manufacturing_order_id" and d.get("code") == "minimum"
            for d in details
        ), (
            f"Expected validation to reject the invalid manufacturing order ID: {details}"
        )
        return [
            f"{d.get('path')}:{d.get('code')}"
            for d in details
            if "batch_transaction" in str(d.get("path", ""))
        ]

    with_quantity = await _errors(
        {**invalid_id, "batch_transaction": {"batch_id": 1, "quantity": 1}}
    )
    assert any("additionalProperties" in e for e in with_quantity), (
        "Sending `quantity` inside batch_transaction is expected to be rejected "
        f"as an additional property; got {with_quantity}"
    )

    batch_id_only = await _errors({**invalid_id, "batch_transaction": {"batch_id": 1}})
    assert not any("additionalProperties" in e for e in batch_id_only), (
        "batch_id alone must be accepted by the schema; got "
        f"{batch_id_only} — if this fires, the endpoint's batch_transaction "
        "shape changed again."
    )
