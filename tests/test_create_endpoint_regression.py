"""Parser-level regression for the POST-create status-code spec drift fix.

The original symptom: Katana returns 200 from POST create endpoints, but the
spec mis-declared them as 201. The generated ``_parse_response`` only handled
the documented status, so on a real 200 it left ``response.parsed = None`` and
``unwrap_as`` raised ``UnexpectedResponse`` *even though the mutation had
landed server-side*.

The companion YAML-only test
(``test_openapi_specification.py::test_create_endpoint_success_status_codes``)
pins the spec values, but YAML inspection alone wouldn't catch a regression
where the generated client got stale relative to the spec. These tests exercise
the actual parser path with ``httpx.MockTransport``: each returns a 200 with a
real-shape body and asserts ``unwrap_as`` produces a typed model — exactly the
end-to-end behavior the original bug broke.

Same pattern as ``test_update_endpoint_regression.py`` (which covers the
sibling #527 PATCH-200 drift class).
"""

from collections.abc import Callable

import httpx
import pytest

from katana_public_api_client import KatanaClient
from katana_public_api_client.api.inventory import create_inventory_reorder_point
from katana_public_api_client.api.purchase_orders import (
    create_outsourced_purchase_order_recipe_row,
)
from katana_public_api_client.api.sales_order_fulfillment import (
    create_sales_order_fulfillment,
)
from katana_public_api_client.api.sales_return_row import create_sales_return_row
from katana_public_api_client.api.stock_transfer import create_stock_transfer
from katana_public_api_client.models import (
    CreateInventoryReorderPointRequest,
    CreateOutsourcedPurchaseOrderRecipeRowRequest,
    CreateSalesOrderFulfillmentRequest,
    CreateSalesReturnRowRequest,
    CreateStockTransferRequest,
    InventoryReorderPoint,
    OutsourcedPurchaseOrderRecipeRow,
    SalesOrderFulfillment,
    SalesOrderFulfillmentRowRequest,
    SalesOrderFulfillmentStatus,
    SalesReturnRow,
    StockTransfer,
    StockTransferRowRequest,
)
from katana_public_api_client.utils import unwrap_as


def _client_with_mock_transport(
    handler: Callable[[httpx.Request], httpx.Response],
) -> KatanaClient:
    """Build a KatanaClient backed by ``httpx.MockTransport``; caller must use ``async with`` to close it."""
    return KatanaClient(
        api_key="test-api-key",
        base_url="https://api.katana.test",
        transport=httpx.MockTransport(handler),
    )


@pytest.mark.asyncio
async def test_create_sales_order_fulfillment_parses_200_body() -> None:
    """Successful POST /sales_order_fulfillments returns a parsed SalesOrderFulfillment.

    Regression: the spec used to declare 201; the parser would leave parsed=None
    on the real 200 response, and unwrap_as would raise UnexpectedResponse.
    """
    fulfillment_payload = {
        "id": 40036770,
        "sales_order_id": 44857034,
        "status": "DELIVERED",
        "picked_date": "2026-05-08T23:14:00Z",
        "sales_order_fulfillment_rows": [
            {"sales_order_row_id": 111041720, "quantity": 1},
        ],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/sales_order_fulfillments"
        return httpx.Response(200, json=fulfillment_payload)

    async with _client_with_mock_transport(handler) as client:
        response = await create_sales_order_fulfillment.asyncio_detailed(
            client=client,
            body=CreateSalesOrderFulfillmentRequest(
                sales_order_id=44857034,
                status=SalesOrderFulfillmentStatus.DELIVERED,
                sales_order_fulfillment_rows=[
                    SalesOrderFulfillmentRowRequest(
                        sales_order_row_id=111041720, quantity=1
                    )
                ],
            ),
        )

    fulfillment = unwrap_as(response, SalesOrderFulfillment)
    assert isinstance(fulfillment, SalesOrderFulfillment)
    assert fulfillment.id == 40036770
    assert fulfillment.sales_order_id == 44857034


@pytest.mark.asyncio
async def test_create_stock_transfer_parses_200_body() -> None:
    """Successful POST /stock_transfers returns a parsed StockTransfer."""
    transfer_payload = {
        "id": 332638,
        "stock_transfer_number": "ST-001",
        "source_location_id": 184871,
        "target_location_id": 184870,
        "status": "draft",
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/stock_transfers"
        return httpx.Response(200, json=transfer_payload)

    async with _client_with_mock_transport(handler) as client:
        response = await create_stock_transfer.asyncio_detailed(
            client=client,
            body=CreateStockTransferRequest(
                stock_transfer_number="ST-001",
                source_location_id=184871,
                target_location_id=184870,
                stock_transfer_rows=[
                    StockTransferRowRequest(variant_id=40699265, quantity="1"),  # type: ignore[arg-type]
                ],
            ),
        )

    transfer = unwrap_as(response, StockTransfer)
    assert isinstance(transfer, StockTransfer)
    assert transfer.id == 332638
    assert transfer.stock_transfer_number == "ST-001"


@pytest.mark.asyncio
async def test_create_sales_return_row_parses_200_body() -> None:
    """Successful POST /sales_return_rows returns a parsed SalesReturnRow."""
    row_payload = {
        "id": 365609,
        "sales_return_id": 412115,
        "variant_id": 40699258,
        "fulfillment_row_id": 91491911,
        "sales_order_row_id": 111041721,
        "quantity": "1.00000000000000000000",
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/sales_return_rows"
        return httpx.Response(200, json=row_payload)

    async with _client_with_mock_transport(handler) as client:
        response = await create_sales_return_row.asyncio_detailed(
            client=client,
            body=CreateSalesReturnRowRequest(
                sales_return_id=412115,
                variant_id=40699258,
                fulfillment_row_id=91491911,
                quantity=1,
            ),
        )

    row = unwrap_as(response, SalesReturnRow)
    assert isinstance(row, SalesReturnRow)
    assert row.id == 365609
    assert row.sales_return_id == 412115


@pytest.mark.asyncio
async def test_create_inventory_reorder_point_parses_200_body() -> None:
    """Successful POST /inventory_reorder_points returns a parsed InventoryReorderPoint.

    Note the live Katana response lacks an ``id`` field and serializes
    ``value`` as a string — both are separate field-level drifts tracked in
    other follow-ups. This test mirrors the wire shape we actually observe.
    """
    reorder_payload = {
        "location_id": 184871,
        "variant_id": 40699264,
        "value": "2",
        "updated_at": "2026-05-28T16:51:53.865Z",
        "created_at": "2026-05-28T16:51:53.865Z",
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/inventory_reorder_points"
        return httpx.Response(200, json=reorder_payload)

    async with _client_with_mock_transport(handler) as client:
        response = await create_inventory_reorder_point.asyncio_detailed(
            client=client,
            body=CreateInventoryReorderPointRequest(
                variant_id=40699264, location_id=184871, value=2.0
            ),
        )

    reorder = unwrap_as(response, InventoryReorderPoint)
    assert isinstance(reorder, InventoryReorderPoint)
    assert reorder.location_id == 184871
    assert reorder.variant_id == 40699264


@pytest.mark.asyncio
async def test_create_outsourced_purchase_order_recipe_row_parses_200_body() -> None:
    """Successful POST /outsourced_purchase_order_recipe_rows returns a parsed model.

    Fifth and final spec-drift outlier from the 201→200 sweep. Live-verified
    2026-05-28 against the test tenant after creating an outsourced PO fixture.
    """
    recipe_row_payload = {
        "id": 719973,
        "purchase_order_id": 2751274,
        "purchase_order_row_id": 7949057,
        "ingredient_variant_id": 40699264,
        "planned_quantity_per_unit": "2.00000000000000000000",
        "notes": None,
        "batch_transactions": [],
        "cost": None,
        "created_at": "2026-05-28T19:07:45.541Z",
        "updated_at": "2026-05-28T19:07:45.541Z",
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/outsourced_purchase_order_recipe_rows"
        return httpx.Response(200, json=recipe_row_payload)

    async with _client_with_mock_transport(handler) as client:
        response = await create_outsourced_purchase_order_recipe_row.asyncio_detailed(
            client=client,
            body=CreateOutsourcedPurchaseOrderRecipeRowRequest(
                purchase_order_row_id=7949057,
                ingredient_variant_id=40699264,
                planned_quantity_per_unit=2.0,
            ),
        )

    row = unwrap_as(response, OutsourcedPurchaseOrderRecipeRow)
    assert isinstance(row, OutsourcedPurchaseOrderRecipeRow)
    assert row.id == 719973
    assert row.purchase_order_row_id == 7949057
    assert row.ingredient_variant_id == 40699264
