"""MTO serial guards and wire-level orchestration regressions for #784."""

import json
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock

import httpx
import pytest
import pytest_asyncio
from katana_mcp.tools.foundation.orders import FulfillOrderRequest, _fulfill_order_impl
from katana_mcp_server.tests.conftest import create_mock_context
from pydantic import ValidationError

from katana_public_api_client import KatanaClient
from katana_public_api_client.utils import APIError

PRODUCED_AT = "2026-09-21T12:00:00.000Z"
PICKED_AT = "2026-09-21T12:01:00.000Z"


@dataclass
class MtoApi:
    """Only the public endpoints used by production and delivery are available."""

    row: dict[str, Any] = field(
        default_factory=lambda: {
            "id": 1,
            "variant_id": 100,
            "quantity": 1,
            "linked_manufacturing_order_id": 7,
            "serial_numbers": [],
        }
    )
    serial_tracked: bool = True
    produced: bool = False
    generation_status: int = 200
    return_serials: bool = True
    posts: list[tuple[str, dict[str, Any]]] = field(default_factory=list)

    def handle(self, request: httpx.Request) -> httpx.Response:
        path = request.url.path
        serial = {"id": 501, "serial_number": "MTO-0001"}
        if request.method == "POST":
            body = json.loads(request.content)
            self.posts.append((path, body))
            if path == "/manufacturing_order_productions":
                if self.generation_status != 200:
                    return httpx.Response(
                        self.generation_status,
                        json={
                            "error": {
                                "name": "UnprocessableEntityError",
                                "message": "Generation unavailable",
                            }
                        },
                    )
                self.produced = True
                self.row["serial_numbers"] = [501]
                self.row["traceability"] = [{"serial_number_id": 501, "quantity": "1"}]
                return httpx.Response(
                    200,
                    json={
                        "id": 90,
                        "quantity": 1,
                        "production_date": PRODUCED_AT,
                        "serial_numbers": [serial] if self.return_serials else [],
                        "traceability": self.row["traceability"]
                        if self.return_serials
                        else [],
                    },
                )
            if path == "/sales_order_fulfillments":
                return httpx.Response(
                    200,
                    json={
                        "id": 91,
                        "sales_order_id": 42,
                        "status": "DELIVERED",
                        "picked_date": body.get("picked_date", PICKED_AT),
                    },
                )
        if request.method == "GET":
            bodies = {
                "/sales_orders/42": {
                    "id": 42,
                    "customer_id": 12,
                    "location_id": 1,
                    "order_no": "SO-MTO",
                    "status": "NOT_SHIPPED",
                    "sales_order_rows": [self.row],
                },
                "/manufacturing_orders/7": {
                    "id": 7,
                    "order_no": "MO-MTO",
                    "variant_id": 100,
                    "status": "DONE" if self.produced else "NOT_STARTED",
                    "actual_quantity": 1,
                    "sales_order_id": 42,
                    "done_date": PRODUCED_AT if self.produced else None,
                    "serial_numbers": [serial]
                    if self.produced and self.return_serials
                    else [],
                },
                "/variants/100": {"id": 100, "sku": "MTO", "product_id": 10},
                "/products/10": {
                    "id": 10,
                    "name": "MTO product",
                    "type": "product",
                    "serial_tracked": self.serial_tracked,
                },
                "/sales_order_addresses": {"data": []},
            }
            if path in bodies:
                return httpx.Response(200, json=bodies[path])
        raise AssertionError(f"Unexpected API call: {request.method} {path}")


@pytest_asyncio.fixture
async def mto_context() -> AsyncIterator[tuple[MagicMock, MtoApi]]:
    api = MtoApi()
    context, services = create_mock_context()
    async with KatanaClient(
        api_key="test-key",
        base_url="https://katana.test",
        transport=httpx.MockTransport(api.handle),
        requests_per_minute=None,
    ) as client:
        services.client = client
        yield context, api


@pytest.mark.asyncio
@pytest.mark.parametrize("explicit", [False, True])
async def test_generated_mto_serial_flows_to_delivery(mto_context, explicit):
    context, api = mto_context
    production_request = FulfillOrderRequest(
        order_id=7,
        order_type="manufacturing",
        generate_serial_numbers=True,
        completed_at=datetime.fromisoformat(PRODUCED_AT),
    )
    preview = await _fulfill_order_impl(production_request, context)
    assert not any(w.startswith("BLOCK:") for w in preview.warnings)
    assert any("generate" in update for update in preview.inventory_updates)
    assert not api.posts

    produced = await _fulfill_order_impl(
        production_request.model_copy(update={"preview": False}), context
    )
    assert produced.status == "DONE"
    assert produced.fulfilled_rows[0].serial_numbers == [501]
    path, body = api.posts[0]
    assert path == "/manufacturing_order_productions"
    assert "serial_numbers" not in body and "traceability" not in body
    assert datetime.fromisoformat(body["completed_date"]) == datetime.fromisoformat(
        PRODUCED_AT
    )

    rows = (
        [
            {
                "sales_order_row_id": 1,
                "traceability": [{"serial_number_id": 501, "quantity": 1}],
            }
        ]
        if explicit
        else None
    )
    delivery_request = FulfillOrderRequest.model_validate(
        {
            "order_id": 42,
            "order_type": "sales",
            "rows": rows,
            "completed_at": PICKED_AT,
        }
    )
    preview = await _fulfill_order_impl(delivery_request, context)
    assert not any(w.startswith("BLOCK:") for w in preview.warnings)
    assert preview.fulfilled_rows[0].serial_numbers == [501]
    assert len(api.posts) == 1
    delivered = await _fulfill_order_impl(
        delivery_request.model_copy(update={"preview": False}), context
    )
    assert delivered.status == "DELIVERED"
    assert delivered.fulfilled_rows[0].serial_numbers == [501]
    assert len(api.posts) == 2
    path, body = api.posts[1]
    assert path == "/sales_order_fulfillments"
    assert datetime.fromisoformat(body["picked_date"]) == datetime.fromisoformat(
        PICKED_AT
    )
    wire_row = body["sales_order_fulfillment_rows"][0]
    assert "serial_numbers" not in wire_row
    if explicit:
        assert wire_row["traceability"] == [{"serial_number_id": 501, "quantity": 1.0}]
    else:
        assert "traceability" not in wire_row


@pytest.mark.asyncio
@pytest.mark.parametrize("preview", [True, False])
@pytest.mark.parametrize(
    "reservation",
    [
        {},
        {"serial_numbers": []},
        {"serial_numbers": [501, 502]},
        {"serial_numbers": [501, 501]},
        {"serial_numbers": [0]},
        {"serial_numbers": [501], "traceability": []},
        {
            "serial_numbers": [501],
            "traceability": [{"serial_number_id": 501, "quantity": "0"}],
        },
        {"traceability": [{"serial_number_id": 501, "quantity": "garbage"}]},
        {"traceability": [{"batch_id": 1, "quantity": "1"}]},
        {"serial_number_transactions": [{"serial_number_id": 501, "quantity": 1}]},
    ],
)
async def test_incomplete_reservation_blocks_without_writing(
    mto_context, reservation, preview
):
    context, api = mto_context
    api.row.update(reservation)
    result = await _fulfill_order_impl(
        FulfillOrderRequest(
            order_id=42,
            order_type="sales",
            preview=preview,
        ),
        context,
    )
    assert any(w.startswith("BLOCK:") for w in result.warnings)
    assert not api.posts


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "override",
    [
        {"serial_numbers": []},
        {"traceability": []},
        {"serial_numbers": [501], "traceability": []},
        {"traceability": [{"serial_number_id": 501, "quantity": -1}]},
        {"traceability": [{"serial_number_id": 501, "quantity": 2}]},
        {"traceability": [{"batch_id": 1, "quantity": 1}]},
        {"serial_numbers": [501, 501]},
    ],
)
async def test_explicit_invalid_allocations_never_inherit_reservation(
    mto_context, override
):
    context, api = mto_context
    api.row["serial_numbers"] = [501]
    result = await _fulfill_order_impl(
        FulfillOrderRequest.model_validate(
            {
                "order_id": 42,
                "order_type": "sales",
                "preview": False,
                "rows": [{"sales_order_row_id": 1, **override}],
            }
        ),
        context,
    )
    assert any(w.startswith("BLOCK:") for w in result.warnings)
    assert not api.posts


@pytest.mark.asyncio
async def test_legacy_current_serials_and_empty_override_carry_reservation(mto_context):
    context, api = mto_context
    api.row["serial_numbers"] = [501]
    api.row["serial_number_transactions"] = [{"serial_number_id": 502, "quantity": 0}]
    result = await _fulfill_order_impl(
        FulfillOrderRequest.model_validate(
            {
                "order_id": 42,
                "order_type": "sales",
                "preview": False,
                "rows": [{"sales_order_row_id": 1}],
            }
        ),
        context,
    )
    assert result.status == "DELIVERED"
    assert result.fulfilled_rows[0].serial_numbers == [501]
    assert api.posts[0][1]["sales_order_fulfillment_rows"] == [
        {"sales_order_row_id": 1, "quantity": 1}
    ]


@pytest.mark.parametrize(
    "options",
    [
        {"order_type": "sales"},
        {"serial_numbers": []},
        {"traceability": []},
        {"serial_numbers": [501]},
    ],
)
def test_generation_conflicts_are_rejected(options):
    with pytest.raises(ValidationError):
        FulfillOrderRequest.model_validate(
            {
                "order_id": 7,
                "order_type": "manufacturing",
                "generate_serial_numbers": True,
                **options,
            }
        )


@pytest.mark.asyncio
async def test_generation_requires_serial_tracked_product(mto_context):
    context, api = mto_context
    api.serial_tracked = False
    result = await _fulfill_order_impl(
        FulfillOrderRequest(
            order_id=7,
            order_type="manufacturing",
            preview=False,
            generate_serial_numbers=True,
        ),
        context,
    )
    assert any(w.startswith("BLOCK:") for w in result.warnings)
    assert not api.posts


@pytest.mark.asyncio
async def test_generation_errors_do_not_retry_production(mto_context):
    context, api = mto_context
    api.generation_status = 422
    with pytest.raises(APIError):
        await _fulfill_order_impl(
            FulfillOrderRequest(
                order_id=7,
                order_type="manufacturing",
                preview=False,
                generate_serial_numbers=True,
            ),
            context,
        )
    assert len(api.posts) == 1


@pytest.mark.asyncio
async def test_missing_generated_serial_readback_warns_without_retry(mto_context):
    context, api = mto_context
    api.return_serials = False
    result = await _fulfill_order_impl(
        FulfillOrderRequest(
            order_id=7,
            order_type="manufacturing",
            preview=False,
            generate_serial_numbers=True,
        ),
        context,
    )
    assert result.status == "DONE"
    assert any("do not repeat production" in w for w in result.warnings)
    assert len(api.posts) == 1


@pytest.mark.asyncio
async def test_reserved_serials_do_not_bypass_timestamp_guard(mto_context):
    context, api = mto_context
    api.produced = True
    api.row["serial_numbers"] = [501]
    result = await _fulfill_order_impl(
        FulfillOrderRequest(
            order_id=42,
            order_type="sales",
            preview=False,
            completed_at=datetime(2026, 9, 21, 12, tzinfo=UTC),
        ),
        context,
    )
    assert any(w.startswith("BLOCK:") for w in result.warnings)
    assert not api.posts


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "serials,allowed", [([501, 502], True), ([501], False), ([501, 501], False)]
)
@pytest.mark.parametrize("explicit", [False, True])
async def test_multiunit_allocation_requires_distinct_complete_serials(
    mto_context, serials, allowed, explicit
):
    context, api = mto_context
    api.row["quantity"] = 2
    allocations = [{"serial_number_id": sid, "quantity": 1} for sid in serials]
    if explicit:
        overrides = [
            {"sales_order_row_id": 1, "traceability": allocations, "serial_numbers": []}
        ]
    else:
        api.row["traceability"] = allocations
        overrides = None
    result = await _fulfill_order_impl(
        FulfillOrderRequest.model_validate(
            {
                "order_id": 42,
                "order_type": "sales",
                "preview": False,
                "rows": overrides,
            }
        ),
        context,
    )
    assert bool(api.posts) is allowed
    assert any(w.startswith("BLOCK:") for w in result.warnings) is not allowed
    if allowed:
        assert result.fulfilled_rows[0].serial_numbers == serials
