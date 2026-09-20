"""Manufacturing allocation shapes, wire bodies, and confirmation intent (#1051)."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from katana_mcp.tools.foundation._traceability import (
    ManufacturingIngredientAllocation,
    ManufacturingOutputAllocation,
)
from katana_mcp.tools.foundation.manufacturing_orders import (
    CreateManufacturingOrderRequest,
    MOHeaderPatch,
    MOProductionAdd,
    MOProductionUpdate,
    MORecipeRowAdd,
    MORecipeRowUpdate,
    _build_create_production_request,
    _build_create_recipe_row_request,
    _build_update_header_request,
    _build_update_production_request,
    _build_update_recipe_row_request,
    _create_manufacturing_order_impl,
)
from katana_mcp.tools.foundation.orders import FulfillOrderRequest, _fulfill_order_impl
from katana_mcp.tools.prefab_ui import _build_apply_action
from katana_mcp_server.tests.conftest import create_mock_context
from katana_mcp_server.tests.tools.test_orders import (
    _make_serial_tracked_mo,
    _wire_serial_tracked_cache,
)
from prefab_ui.actions.mcp import CallTool
from pydantic import ValidationError

from katana_public_api_client.models import ManufacturingOrder, ManufacturingOrderStatus


@pytest.mark.parametrize(
    ("model", "forbidden"),
    [
        (ManufacturingOutputAllocation, "bin_location_id"),
        (ManufacturingIngredientAllocation, "serial_number_id"),
    ],
)
def test_allocation_rejects_wrong_axis(model: Any, forbidden: str) -> None:
    with pytest.raises(ValidationError, match="Extra inputs"):
        model.model_validate({forbidden: 42, "quantity": 1})


@pytest.mark.parametrize("quantity", [0, -1])
@pytest.mark.parametrize(
    "model", [ManufacturingOutputAllocation, ManufacturingIngredientAllocation]
)
def test_manufacturing_quantities_are_positive(model: Any, quantity: float) -> None:
    with pytest.raises(ValidationError):
        model.model_validate({"batch_id": 42, "quantity": quantity})


@pytest.mark.parametrize("allocation", [None, [], [{"batch_id": 42, "quantity": 2}]])
@pytest.mark.parametrize(
    "operation",
    [
        "header",
        "recipe_create",
        "recipe_update",
        "production_create",
        "production_update",
    ],
)
def test_modify_serializes_allocations(operation: str, allocation: Any) -> None:
    body = {"traceability": allocation}
    if operation == "header":
        request = _build_update_header_request(MOHeaderPatch.model_validate(body))
    elif operation == "recipe_create":
        request = _build_create_recipe_row_request(
            1,
            MORecipeRowAdd.model_validate(
                {"variant_id": 2, "planned_quantity_per_unit": 2, **body}
            ),
        )
    elif operation == "recipe_update":
        request = _build_update_recipe_row_request(
            MORecipeRowUpdate.model_validate({"id": 3, **body})
        )
    elif operation == "production_create":
        request = _build_create_production_request(
            1, MOProductionAdd.model_validate({"completed_quantity": 2, **body})
        )
    else:
        request = _build_update_production_request(
            MOProductionUpdate.model_validate({"id": 3, **body})
        )
    wire = request.to_dict()
    if allocation is None:
        assert "traceability" not in wire
    else:
        assert wire["traceability"] == allocation


@pytest.mark.asyncio
async def test_creation_preview_and_apply_preserve_allocations() -> None:
    context, _ = create_mock_context()
    allocation = ManufacturingOutputAllocation(batch_id=42, quantity=2)
    request = CreateManufacturingOrderRequest(
        variant_id=2,
        planned_quantity=2,
        location_id=1,
        order_no="MO-TRACE",
        traceability=[allocation],
    )
    preview = await _create_manufacturing_order_impl(request, context)
    assert preview.requested_traceability == [allocation]
    response = MagicMock(
        status_code=200,
        parsed=ManufacturingOrder(id=3, status=ManufacturingOrderStatus.NOT_STARTED),
    )
    with patch(
        "katana_public_api_client.api.manufacturing_order.create_manufacturing_order.asyncio_detailed",
        new_callable=AsyncMock,
        return_value=response,
    ) as create:
        await _create_manufacturing_order_impl(
            request.model_copy(update={"preview": False}), context
        )
    assert create.call_args.kwargs["body"].to_dict()["traceability"] == [
        {"batch_id": 42, "quantity": 2}
    ]


@pytest.mark.asyncio
async def test_make_to_order_refuses_unsupported_allocations() -> None:
    context, _ = create_mock_context()
    with pytest.raises(ValueError, match="Make-to-order creation does not accept"):
        await _create_manufacturing_order_impl(
            CreateManufacturingOrderRequest(sales_order_row_id=3, traceability=[]),
            context,
        )


@pytest.mark.parametrize("preview", [True, False])
@pytest.mark.asyncio
async def test_fulfillment_serial_allocations_reach_preview_and_apply(
    preview: bool,
) -> None:
    context, lifespan = create_mock_context()
    _wire_serial_tracked_cache(lifespan, variant_id=100, sku="TRACE")
    mo = _make_serial_tracked_mo(order_no="MO-TRACE", actual_quantity=2)
    response = MagicMock(status_code=200, parsed=mo)
    allocations = [
        ManufacturingOutputAllocation(batch_id=42, serial_number_id=serial)
        for serial in [501, 502]
    ]
    request = FulfillOrderRequest(
        order_id=42,
        order_type="manufacturing",
        traceability=allocations,
        preview=preview,
    )
    from katana_public_api_client.models import ManufacturingOrderProduction

    production = MagicMock(status_code=200, parsed=ManufacturingOrderProduction(id=9))
    with (
        patch(
            "katana_public_api_client.api.manufacturing_order.get_manufacturing_order.asyncio_detailed",
            new_callable=AsyncMock,
            return_value=response,
        ),
        patch(
            "katana_public_api_client.api.manufacturing_order_production.create_manufacturing_order_production.asyncio_detailed",
            new_callable=AsyncMock,
            return_value=production,
        ) as create,
    ):
        result = await _fulfill_order_impl(request, context)
    assert not any(w.startswith("BLOCK:") for w in result.warnings)
    assert result.fulfilled_rows[0].serial_numbers == [501, 502]
    assert result.fulfilled_rows[0].manufacturing_traceability == allocations
    if preview:
        create.assert_not_called()
        assert result.fulfilled_rows[0].batch_summary == "batch 42x1, batch 42x1"
    else:
        wire = create.call_args.kwargs["body"].to_dict()
        assert wire["traceability"] == [
            a.model_dump(exclude_none=True) for a in allocations
        ]
        assert "serial_numbers" not in wire
    actions = _build_apply_action("fulfill_order", request)
    assert actions is not None
    call = next(a for a in actions if getattr(a, "tool", None) == "fulfill_order")
    assert isinstance(call, CallTool)
    args = call.arguments
    assert args["traceability"] == [a.model_dump() for a in allocations]
    assert args["preview"] is False


@pytest.mark.parametrize(
    "body",
    [
        {"order_type": "sales", "traceability": []},
        {
            "order_type": "manufacturing",
            "serial_numbers": [1],
            "traceability": [{"serial_number_id": 1}],
        },
        {
            "order_type": "manufacturing",
            "traceability": [{"serial_number_id": 1}, {"serial_number_id": 1}],
        },
        {
            "order_type": "manufacturing",
            "traceability": [{"serial_number_id": 1, "quantity": 2}],
        },
    ],
)
def test_fulfillment_rejects_ambiguous_allocations(body: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        FulfillOrderRequest.model_validate({"order_id": 42, **body})
