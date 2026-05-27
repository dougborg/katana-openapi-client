"""Tests for correct_manufacturing_order, correct_sales_order, and
correct_purchase_order.

Covers the reopen → modify → restore pattern: snapshot capture, ordering
of API calls (revert before edits before recreate before close), preview
shape, and partial-failure breadcrumb.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from katana_mcp.tools.foundation.corrections import (
    CorrectManufacturingOrderRequest,
    CorrectPurchaseOrderRequest,
    CorrectSalesOrderRequest,
    MOIngredientCorrection,
    PORowCorrection,
    SOLineCorrection,
    _correct_manufacturing_order_impl,
    _correct_purchase_order_impl,
    _correct_sales_order_impl,
)
from katana_mcp_server.tests.conftest import create_mock_context

from katana_public_api_client.client_types import UNSET
from katana_public_api_client.models import (
    ManufacturingOrder,
    ManufacturingOrderProduction,
    ManufacturingOrderRecipeRow,
    ManufacturingOrderStatus,
    PurchaseOrderRow,
    PurchaseOrderStatus,
    RegularPurchaseOrder,
    SalesOrder,
    SalesOrderFulfillment,
    SalesOrderFulfillmentStatus,
    SalesOrderRow,
    SalesOrderStatus,
    SerialNumber,
)
from tests.factories import mock_entity_for_modify

# ============================================================================
# Test fixtures — fully-formed entities (not MagicMocks) so the snapshot
# code reads real attrs fields.
# ============================================================================


def _make_mo(
    *,
    mo_id: int = 42,
    status: str = "DONE",
    done_date: datetime | None = None,
) -> ManufacturingOrder:
    """Build a real attrs ``ManufacturingOrder`` in the requested status."""
    mo = mock_entity_for_modify(ManufacturingOrder, id=mo_id)
    mo.status = ManufacturingOrderStatus(status)
    mo.done_date = done_date if done_date is not None else UNSET
    return mo


def _make_recipe_row(
    *, row_id: int, variant_id: int, quantity: float = 1.0
) -> ManufacturingOrderRecipeRow:
    row = mock_entity_for_modify(ManufacturingOrderRecipeRow, id=row_id)
    row.variant_id = variant_id
    row.planned_quantity_per_unit = quantity
    return row


def _make_production(
    *,
    prod_id: int,
    quantity: float = 1.0,
    production_date: datetime | None = None,
    serial_numbers: list[str] | None = None,
) -> ManufacturingOrderProduction:
    prod = mock_entity_for_modify(ManufacturingOrderProduction, id=prod_id)
    prod.manufacturing_order_id = 42
    prod.quantity = quantity
    prod.production_date = production_date if production_date is not None else UNSET
    if serial_numbers:
        sn_objs = []
        for sn_str in serial_numbers:
            sn = mock_entity_for_modify(SerialNumber, id=hash(sn_str) & 0xFFFFFF)
            sn.serial_number = sn_str
            sn_objs.append(sn)
        prod.serial_numbers = sn_objs
    else:
        prod.serial_numbers = UNSET
    return prod


def _make_so(
    *,
    so_id: int = 99,
    status: str = "DELIVERED",
    picked_date: datetime | None = None,
) -> SalesOrder:
    so = mock_entity_for_modify(SalesOrder, id=so_id)
    so.status = SalesOrderStatus(status)
    so.picked_date = picked_date if picked_date is not None else UNSET
    so.sales_order_rows = []
    return so


def _make_so_row(
    *, row_id: int, variant_id: int, quantity: float = 1.0, price: float = 10.0
) -> SalesOrderRow:
    row = mock_entity_for_modify(SalesOrderRow, id=row_id)
    row.variant_id = variant_id
    row.quantity = quantity
    row.price_per_unit = price
    return row


def _make_fulfillment(
    *,
    ful_id: int,
    so_id: int,
    row_id: int,
    quantity: float = 1.0,
    picked_date: datetime | None = None,
    status: str = "DELIVERED",
) -> SalesOrderFulfillment:
    ful = mock_entity_for_modify(SalesOrderFulfillment, id=ful_id)
    ful.sales_order_id = so_id
    ful.status = SalesOrderFulfillmentStatus(status)
    ful.picked_date = picked_date if picked_date is not None else UNSET
    row = MagicMock()
    row.sales_order_row_id = row_id
    row.quantity = quantity
    ful.sales_order_fulfillment_rows = [row]
    return ful


# ============================================================================
# correct_manufacturing_order — entry-condition checks
# ============================================================================


@pytest.mark.asyncio
async def test_correct_mo_rejects_open_status():
    """An MO that's still IN_PROGRESS has no close-state to preserve."""
    context, _ = create_mock_context()
    mo = _make_mo(status="IN_PROGRESS")

    with (
        patch(
            "katana_mcp.tools.foundation.corrections._fetch_manufacturing_order_attrs",
            new_callable=AsyncMock,
            return_value=mo,
        ),
        patch(
            "katana_mcp.tools.foundation.corrections._fetch_mo_recipe_rows_raw",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch(
            "katana_mcp.tools.foundation.corrections._fetch_mo_productions_raw",
            new_callable=AsyncMock,
            return_value=[],
        ),
        pytest.raises(ValueError, match="DONE or PARTIALLY_COMPLETED"),
    ):
        await _correct_manufacturing_order_impl(
            CorrectManufacturingOrderRequest(
                id=42,
                ingredient_changes=[
                    MOIngredientCorrection(old_variant_id=100, new_variant_id=200)
                ],
            ),
            context,
        )


@pytest.mark.asyncio
async def test_correct_mo_rejects_missing_variant():
    """If old_variant_id isn't on the MO, the tool errors clearly."""
    context, _ = create_mock_context()
    mo = _make_mo(status="DONE")
    rows = [_make_recipe_row(row_id=1, variant_id=100)]

    with (
        patch(
            "katana_mcp.tools.foundation.corrections._fetch_manufacturing_order_attrs",
            new_callable=AsyncMock,
            return_value=mo,
        ),
        patch(
            "katana_mcp.tools.foundation.corrections._fetch_mo_recipe_rows_raw",
            new_callable=AsyncMock,
            return_value=rows,
        ),
        patch(
            "katana_mcp.tools.foundation.corrections._fetch_mo_productions_raw",
            new_callable=AsyncMock,
            return_value=[],
        ),
        pytest.raises(ValueError, match="No recipe row on MO 42 has variant_id"),
    ):
        await _correct_manufacturing_order_impl(
            CorrectManufacturingOrderRequest(
                id=42,
                ingredient_changes=[
                    MOIngredientCorrection(old_variant_id=999, new_variant_id=200)
                ],
            ),
            context,
        )


@pytest.mark.asyncio
async def test_correct_mo_rejects_empty_correction():
    """An ingredient_change with neither new_variant_id nor quantity is a
    no-op and should error."""
    context, _ = create_mock_context()
    mo = _make_mo(status="DONE")
    rows = [_make_recipe_row(row_id=1, variant_id=100)]

    with (
        patch(
            "katana_mcp.tools.foundation.corrections._fetch_manufacturing_order_attrs",
            new_callable=AsyncMock,
            return_value=mo,
        ),
        patch(
            "katana_mcp.tools.foundation.corrections._fetch_mo_recipe_rows_raw",
            new_callable=AsyncMock,
            return_value=rows,
        ),
        patch(
            "katana_mcp.tools.foundation.corrections._fetch_mo_productions_raw",
            new_callable=AsyncMock,
            return_value=[],
        ),
        pytest.raises(ValueError, match="must supply at least one"),
    ):
        await _correct_manufacturing_order_impl(
            CorrectManufacturingOrderRequest(
                id=42,
                ingredient_changes=[MOIngredientCorrection(old_variant_id=100)],
            ),
            context,
        )


# ============================================================================
# correct_manufacturing_order — preview
# ============================================================================


@pytest.mark.asyncio
async def test_correct_mo_preview_emits_full_action_plan():
    """Preview should plan: revert → edit → recreate productions →
    patch each production_date → close."""
    context, _ = create_mock_context()
    done_date = datetime(2026, 4, 15, 18, 20, 0, tzinfo=UTC)
    prod_date = datetime(2026, 4, 15, 18, 20, 0, tzinfo=UTC)

    mo = _make_mo(status="DONE", done_date=done_date)
    rows = [_make_recipe_row(row_id=1, variant_id=100)]
    productions = [
        _make_production(
            prod_id=10,
            quantity=1.0,
            production_date=prod_date,
            serial_numbers=["SN-001"],
        )
    ]

    with (
        patch(
            "katana_mcp.tools.foundation.corrections._fetch_manufacturing_order_attrs",
            new_callable=AsyncMock,
            return_value=mo,
        ),
        patch(
            "katana_mcp.tools.foundation.corrections._fetch_mo_recipe_rows_raw",
            new_callable=AsyncMock,
            return_value=rows,
        ),
        patch(
            "katana_mcp.tools.foundation.corrections._fetch_mo_productions_raw",
            new_callable=AsyncMock,
            return_value=productions,
        ),
    ):
        response = await _correct_manufacturing_order_impl(
            CorrectManufacturingOrderRequest(
                id=42,
                ingredient_changes=[
                    MOIngredientCorrection(old_variant_id=100, new_variant_id=200)
                ],
                preview=True,
            ),
            context,
        )

    assert response.is_preview is True
    assert response.entity_id == 42
    # Expected sequence:
    # 1. update_header (revert: status → IN_PROGRESS)
    # 2. update_recipe_row (swap)
    # 3. add_production (fused: POST production + PATCH production_date)
    # 4. update_header (close: status → DONE)
    # 5. update_header (close: done_date → snapshot value, only when DONE)
    operations = [a.operation for a in response.actions]
    assert operations == [
        "update_header",
        "update_recipe_row",
        "add_production",
        "update_header",
        "update_header",
    ]
    # The fused add_production action's diff should include production_date
    add_prod_action = next(
        a for a in response.actions if a.operation == "add_production"
    )
    assert any(c.field == "production_date" for c in add_prod_action.changes)
    # The final update_header should patch done_date back to the snapshot value
    final_action = response.actions[-1]
    assert any(c.field == "done_date" for c in final_action.changes)
    # All preview-shape: succeeded=None
    assert all(a.succeeded is None for a in response.actions)


@pytest.mark.asyncio
async def test_correct_mo_preview_skips_production_date_patch_when_none():
    """If a production has no production_date in the snapshot, no patch
    action is planned for it."""
    context, _ = create_mock_context()
    mo = _make_mo(status="DONE")
    rows = [_make_recipe_row(row_id=1, variant_id=100)]
    productions = [_make_production(prod_id=10, quantity=1.0, production_date=None)]

    with (
        patch(
            "katana_mcp.tools.foundation.corrections._fetch_manufacturing_order_attrs",
            new_callable=AsyncMock,
            return_value=mo,
        ),
        patch(
            "katana_mcp.tools.foundation.corrections._fetch_mo_recipe_rows_raw",
            new_callable=AsyncMock,
            return_value=rows,
        ),
        patch(
            "katana_mcp.tools.foundation.corrections._fetch_mo_productions_raw",
            new_callable=AsyncMock,
            return_value=productions,
        ),
    ):
        response = await _correct_manufacturing_order_impl(
            CorrectManufacturingOrderRequest(
                id=42,
                ingredient_changes=[
                    MOIngredientCorrection(old_variant_id=100, new_variant_id=200)
                ],
                preview=True,
            ),
            context,
        )

    operations = [a.operation for a in response.actions]
    # No update_production step since the snapshot has no production_date
    assert operations == [
        "update_header",
        "update_recipe_row",
        "add_production",
        "update_header",
    ]


# ============================================================================
# correct_manufacturing_order — apply
# ============================================================================


@pytest.mark.asyncio
async def test_correct_mo_apply_executes_phases_in_canonical_order():
    """Apply should call the API in this order:
    1. PATCH MO header (revert to IN_PROGRESS)
    2. PATCH recipe row (swap variant)
    3. POST production (recreate)
    4. PATCH production (backdate production_date)
    5. PATCH MO header (close to DONE)"""
    context, _ = create_mock_context()
    prod_date = datetime(2026, 4, 15, 18, 20, 0, tzinfo=UTC)
    mo = _make_mo(status="DONE", done_date=prod_date)
    rows = [_make_recipe_row(row_id=1, variant_id=100)]
    productions = [
        _make_production(
            prod_id=10,
            quantity=1.0,
            production_date=prod_date,
            serial_numbers=["SN-001"],
        )
    ]

    call_log: list[str] = []
    new_prod = MagicMock()
    new_prod.id = 999  # captured for the production_date patch

    async def fake_update_mo(*, id, client, body):
        # The close-state restore issues a status PATCH then a separate
        # done_date PATCH; the fake distinguishes them by which field is set.
        from katana_public_api_client.client_types import UNSET as _UNSET

        if body.status is not _UNSET:
            call_log.append(f"PATCH MO {id} status={body.status.value}")
        else:
            call_log.append(f"PATCH MO {id} done_date={body.done_date.isoformat()}")
        resp = MagicMock()
        resp.parsed = mo  # echoed body
        return resp

    async def fake_update_recipe(*, id, client, body):
        call_log.append(f"PATCH recipe {id}")
        resp = MagicMock()
        resp.parsed = rows[0]
        return resp

    async def fake_create_production(*, client, body):
        call_log.append(f"POST production qty={body.completed_quantity}")
        resp = MagicMock()
        resp.parsed = new_prod
        return resp

    async def fake_update_production(*, id, client, body):
        call_log.append(f"PATCH production {id} production_date")
        resp = MagicMock()
        resp.parsed = MagicMock()
        resp.status_code = 200
        return resp

    with (
        patch(
            "katana_mcp.tools.foundation.corrections._fetch_manufacturing_order_attrs",
            new_callable=AsyncMock,
            return_value=mo,
        ),
        patch(
            "katana_mcp.tools.foundation.corrections._fetch_mo_recipe_rows_raw",
            new_callable=AsyncMock,
            return_value=rows,
        ),
        patch(
            "katana_mcp.tools.foundation.corrections._fetch_mo_productions_raw",
            new_callable=AsyncMock,
            return_value=productions,
        ),
        patch(
            "katana_mcp.tools.foundation.corrections."
            "api_update_manufacturing_order.asyncio_detailed",
            side_effect=fake_update_mo,
        ),
        patch(
            "katana_mcp.tools.foundation.corrections."
            "api_update_mo_recipe_row.asyncio_detailed",
            side_effect=fake_update_recipe,
        ),
        patch(
            "katana_mcp.tools.foundation.corrections."
            "api_create_mo_production.asyncio_detailed",
            side_effect=fake_create_production,
        ),
        patch(
            "katana_mcp.tools.foundation.corrections."
            "api_update_mo_production.asyncio_detailed",
            side_effect=fake_update_production,
        ),
        patch(
            "katana_mcp.tools.foundation.corrections.unwrap_as",
            return_value=new_prod,
        ),
        patch(
            "katana_mcp.tools.foundation.corrections.is_success",
            return_value=True,
        ),
    ):
        response = await _correct_manufacturing_order_impl(
            CorrectManufacturingOrderRequest(
                id=42,
                ingredient_changes=[
                    MOIngredientCorrection(old_variant_id=100, new_variant_id=200)
                ],
                preview=False,
            ),
            context,
        )

    assert response.is_preview is False
    assert all(a.succeeded is True for a in response.actions)
    # Status-before-dates: revert lands first, status: DONE before done_date,
    # done_date PATCH lands last.
    assert call_log == [
        "PATCH MO 42 status=IN_PROGRESS",
        "PATCH recipe 1",
        "POST production qty=1.0",
        "PATCH production 999 production_date",
        "PATCH MO 42 status=DONE",
        f"PATCH MO 42 done_date={prod_date.isoformat()}",
    ]
    assert response.prior_state is not None
    # Snapshot is in prior_state under the documented sentinel key
    assert "_close_state_snapshot" in response.prior_state


@pytest.mark.asyncio
async def test_correct_mo_apply_halts_on_revert_failure():
    """If the revert PATCH fails, no edits or recreates run; the response
    surfaces the breadcrumb."""
    context, _ = create_mock_context()
    mo = _make_mo(status="DONE")
    rows = [_make_recipe_row(row_id=1, variant_id=100)]
    productions = [_make_production(prod_id=10, quantity=1.0)]

    async def boom(*args, **kwargs):
        raise RuntimeError("Katana refused to revert")

    with (
        patch(
            "katana_mcp.tools.foundation.corrections._fetch_manufacturing_order_attrs",
            new_callable=AsyncMock,
            return_value=mo,
        ),
        patch(
            "katana_mcp.tools.foundation.corrections._fetch_mo_recipe_rows_raw",
            new_callable=AsyncMock,
            return_value=rows,
        ),
        patch(
            "katana_mcp.tools.foundation.corrections._fetch_mo_productions_raw",
            new_callable=AsyncMock,
            return_value=productions,
        ),
        patch(
            "katana_mcp.tools.foundation.corrections."
            "api_update_manufacturing_order.asyncio_detailed",
            side_effect=boom,
        ),
    ):
        response = await _correct_manufacturing_order_impl(
            CorrectManufacturingOrderRequest(
                id=42,
                ingredient_changes=[
                    MOIngredientCorrection(old_variant_id=100, new_variant_id=200)
                ],
                preview=False,
            ),
            context,
        )

    assert response.is_preview is False
    # Only the revert action ran, and it failed.
    assert len(response.actions) == 1
    assert response.actions[0].succeeded is False
    # Breadcrumb language flagged
    assert any("intermediate (open) state" in w for w in response.warnings)
    assert response.prior_state is not None


# ============================================================================
# correct_sales_order — entry conditions + preview + apply
# ============================================================================


@pytest.mark.asyncio
async def test_correct_so_rejects_non_delivered_status():
    context, _ = create_mock_context()
    so = _make_so(status="NOT_SHIPPED")

    with (
        patch(
            "katana_mcp.tools.foundation.corrections._fetch_sales_order_attrs",
            new_callable=AsyncMock,
            return_value=so,
        ),
        patch(
            "katana_mcp.tools.foundation.corrections._fetch_so_fulfillments",
            new_callable=AsyncMock,
            return_value=[],
        ),
        pytest.raises(ValueError, match="DELIVERED status"),
    ):
        await _correct_sales_order_impl(
            CorrectSalesOrderRequest(
                id=99,
                line_changes=[SOLineCorrection(old_variant_id=500, new_variant_id=501)],
            ),
            context,
        )


@pytest.mark.asyncio
async def test_correct_so_rejects_quantity_below_already_fulfilled():
    """Preflight: refuse when a line_changes drops a row below the
    already-fulfilled quantity. Catches the failure before any mutations
    land — without this check, the failure would surface only after
    fulfillments were deleted and the SO was reverted."""
    context, _ = create_mock_context()
    picked = datetime(2026, 4, 15, 21, 18, 0, tzinfo=UTC)
    so = _make_so(status="DELIVERED", picked_date=picked)
    # Row with current quantity 5; original fulfillment shipped 3.
    so.sales_order_rows = [_make_so_row(row_id=10, variant_id=500, quantity=5.0)]
    fulfillments = [
        _make_fulfillment(
            ful_id=77, so_id=99, row_id=10, quantity=3.0, picked_date=picked
        )
    ]

    with (
        patch(
            "katana_mcp.tools.foundation.corrections._fetch_sales_order_attrs",
            new_callable=AsyncMock,
            return_value=so,
        ),
        patch(
            "katana_mcp.tools.foundation.corrections._fetch_so_fulfillments",
            new_callable=AsyncMock,
            return_value=fulfillments,
        ),
        pytest.raises(ValueError, match="already fulfilled"),
    ):
        # Drop quantity to 2 — below the 3 already fulfilled.
        await _correct_sales_order_impl(
            CorrectSalesOrderRequest(
                id=99,
                line_changes=[SOLineCorrection(old_variant_id=500, quantity=2.0)],
            ),
            context,
        )


@pytest.mark.asyncio
async def test_correct_so_preview_emits_full_action_plan():
    """Preview should plan: delete fulfillments → revert → edit → recreate
    fulfillments → close."""
    context, _ = create_mock_context()
    picked = datetime(2026, 4, 15, 21, 18, 0, tzinfo=UTC)
    so = _make_so(status="DELIVERED", picked_date=picked)
    so.sales_order_rows = [_make_so_row(row_id=10, variant_id=500)]
    fulfillments = [
        _make_fulfillment(ful_id=77, so_id=99, row_id=10, picked_date=picked)
    ]

    with (
        patch(
            "katana_mcp.tools.foundation.corrections._fetch_sales_order_attrs",
            new_callable=AsyncMock,
            return_value=so,
        ),
        patch(
            "katana_mcp.tools.foundation.corrections._fetch_so_fulfillments",
            new_callable=AsyncMock,
            return_value=fulfillments,
        ),
    ):
        response = await _correct_sales_order_impl(
            CorrectSalesOrderRequest(
                id=99,
                line_changes=[SOLineCorrection(old_variant_id=500, new_variant_id=501)],
                preview=True,
            ),
            context,
        )

    assert response.is_preview is True
    operations = [a.operation for a in response.actions]
    assert operations == [
        "delete_fulfillment",
        "update_header",
        "update_row",
        "add_fulfillment",
        "update_header",
    ]
    assert all(a.succeeded is None for a in response.actions)


@pytest.mark.asyncio
async def test_correct_so_apply_executes_phases_in_canonical_order():
    context, _ = create_mock_context()
    picked = datetime(2026, 4, 15, 21, 18, 0, tzinfo=UTC)
    so = _make_so(status="DELIVERED", picked_date=picked)
    so_row = _make_so_row(row_id=10, variant_id=500)
    so.sales_order_rows = [so_row]
    fulfillments = [
        _make_fulfillment(ful_id=77, so_id=99, row_id=10, picked_date=picked)
    ]

    call_log: list[str] = []
    new_fulfillment = MagicMock()
    new_fulfillment.id = 888

    async def fake_delete_ful(*, id, client):
        call_log.append(f"DELETE fulfillment {id}")
        resp = MagicMock()
        resp.status_code = 204
        return resp

    async def fake_update_so(*, id, client, body):
        call_log.append(f"PATCH SO {id} status={body.status.value}")
        resp = MagicMock()
        resp.parsed = so
        return resp

    async def fake_update_row(*, id, client, body):
        call_log.append(f"PATCH SO row {id}")
        resp = MagicMock()
        resp.parsed = so_row
        return resp

    async def fake_create_ful(*, client, body):
        call_log.append(f"POST fulfillment status={body.status.value}")
        resp = MagicMock()
        resp.parsed = new_fulfillment
        return resp

    with (
        patch(
            "katana_mcp.tools.foundation.corrections._fetch_sales_order_attrs",
            new_callable=AsyncMock,
            return_value=so,
        ),
        patch(
            "katana_mcp.tools.foundation.corrections._fetch_so_fulfillments",
            new_callable=AsyncMock,
            return_value=fulfillments,
        ),
        patch(
            "katana_mcp.tools.foundation.corrections."
            "api_delete_so_fulfillment.asyncio_detailed",
            side_effect=fake_delete_ful,
        ),
        patch(
            "katana_mcp.tools.foundation.corrections."
            "api_update_sales_order.asyncio_detailed",
            side_effect=fake_update_so,
        ),
        patch(
            "katana_mcp.tools.foundation.corrections."
            "api_update_so_row.asyncio_detailed",
            side_effect=fake_update_row,
        ),
        patch(
            "katana_mcp.tools.foundation.corrections."
            "api_create_so_fulfillment.asyncio_detailed",
            side_effect=fake_create_ful,
        ),
        patch(
            "katana_mcp.tools.foundation.corrections.is_success",
            return_value=True,
        ),
        patch(
            "katana_mcp.tools.foundation.corrections.unwrap_as",
            return_value=new_fulfillment,
        ),
    ):
        response = await _correct_sales_order_impl(
            CorrectSalesOrderRequest(
                id=99,
                line_changes=[SOLineCorrection(old_variant_id=500, new_variant_id=501)],
                preview=False,
            ),
            context,
        )

    assert response.is_preview is False
    assert all(a.succeeded is True for a in response.actions)
    assert call_log == [
        "DELETE fulfillment 77",
        "PATCH SO 99 status=PENDING",
        "PATCH SO row 10",
        "POST fulfillment status=DELIVERED",
        "PATCH SO 99 status=DELIVERED",
    ]
    assert response.prior_state is not None


@pytest.mark.asyncio
async def test_correct_so_fail_fast_synthesizes_not_run_tail_for_morph():
    """Fail-fast mid-correction must surface the unattempted phases as
    NOT-RUN extras (#858 finding B — Copilot comment 3312071378).

    ``build_so_modify_ui`` handles ``correct_sales_order`` alongside
    ``modify_sales_order``; both rely on ``response.extras[\"not_run_actions\"]``
    so the per-section row morph can render skipped restore / recreate /
    close phases instead of silently overwriting the preview's full
    sub-entity rows with only the executed prefix.

    Plan: delete fulfillment (phase 1, succeeds) → revert SO (phase 2,
    succeeds) → edit row (phase 3, FAILS). Phases 4 (recreate fulfillment)
    + 5 (close SO) must surface as NOT-RUN entries.
    """
    context, _ = create_mock_context()
    picked = datetime(2026, 4, 15, 21, 18, 0, tzinfo=UTC)
    so = _make_so(status="DELIVERED", picked_date=picked)
    so_row = _make_so_row(row_id=10, variant_id=500)
    so.sales_order_rows = [so_row]
    fulfillments = [
        _make_fulfillment(ful_id=77, so_id=99, row_id=10, picked_date=picked)
    ]

    async def fake_delete_ful(*, id, client):
        resp = MagicMock()
        resp.status_code = 204
        return resp

    async def fake_update_so(*, id, client, body):
        resp = MagicMock()
        resp.parsed = so
        return resp

    async def boom_update_row(*, id, client, body):
        raise RuntimeError("Katana refused the row edit")

    with (
        patch(
            "katana_mcp.tools.foundation.corrections._fetch_sales_order_attrs",
            new_callable=AsyncMock,
            return_value=so,
        ),
        patch(
            "katana_mcp.tools.foundation.corrections._fetch_so_fulfillments",
            new_callable=AsyncMock,
            return_value=fulfillments,
        ),
        patch(
            "katana_mcp.tools.foundation.corrections."
            "api_delete_so_fulfillment.asyncio_detailed",
            side_effect=fake_delete_ful,
        ),
        patch(
            "katana_mcp.tools.foundation.corrections."
            "api_update_sales_order.asyncio_detailed",
            side_effect=fake_update_so,
        ),
        patch(
            "katana_mcp.tools.foundation.corrections."
            "api_update_so_row.asyncio_detailed",
            side_effect=boom_update_row,
        ),
        patch(
            "katana_mcp.tools.foundation.corrections.is_success",
            return_value=True,
        ),
    ):
        response = await _correct_sales_order_impl(
            CorrectSalesOrderRequest(
                id=99,
                line_changes=[SOLineCorrection(old_variant_id=500, new_variant_id=501)],
                preview=False,
            ),
            context,
        )

    # Phases 1+2 succeeded, phase 3 (edit) failed → 3 executed actions.
    assert response.is_preview is False
    assert len(response.actions) == 3
    assert response.actions[0].succeeded is True  # delete_fulfillment
    assert response.actions[1].succeeded is True  # update_header (revert)
    assert response.actions[2].succeeded is False  # update_row (boom)

    # The two unattempted phases must surface as NOT-RUN extras so the
    # SO modify-card morph picks them up via ``_so_actions_with_not_run_tail``.
    not_run = response.extras.get("not_run_actions") or []
    assert len(not_run) == 2, (
        f"Expected 2 NOT-RUN entries (recreate + close); got {len(not_run)}: "
        f"{[a.get('operation') for a in not_run]}"
    )
    assert [a["operation"] for a in not_run] == ["add_fulfillment", "update_header"]
    assert all(a["succeeded"] is None for a in not_run)
    assert all(a["status_label"] == "NOT RUN" for a in not_run)


@pytest.mark.asyncio
async def test_correct_so_fail_fast_morph_renders_not_run_rows():
    """End-to-end check: feed the failed-correction response into
    :func:`build_so_modify_ui` and confirm the NOT-RUN tail makes it into
    the action list the morph paints from (#858 finding B).

    This is the consumer-side proof — the impl-side test above proves
    extras are populated; this one proves the renderer actually reads them.
    """
    from katana_mcp.tools.prefab_ui import _so_actions_with_not_run_tail

    context, _ = create_mock_context()
    picked = datetime(2026, 4, 15, 21, 18, 0, tzinfo=UTC)
    so = _make_so(status="DELIVERED", picked_date=picked)
    so_row = _make_so_row(row_id=10, variant_id=500)
    so.sales_order_rows = [so_row]
    fulfillments = [
        _make_fulfillment(ful_id=77, so_id=99, row_id=10, picked_date=picked)
    ]

    async def fake_delete_ful(*, id, client):
        resp = MagicMock()
        resp.status_code = 204
        return resp

    async def fake_update_so(*, id, client, body):
        resp = MagicMock()
        resp.parsed = so
        return resp

    async def boom_update_row(*, id, client, body):
        raise RuntimeError("Katana refused the row edit")

    with (
        patch(
            "katana_mcp.tools.foundation.corrections._fetch_sales_order_attrs",
            new_callable=AsyncMock,
            return_value=so,
        ),
        patch(
            "katana_mcp.tools.foundation.corrections._fetch_so_fulfillments",
            new_callable=AsyncMock,
            return_value=fulfillments,
        ),
        patch(
            "katana_mcp.tools.foundation.corrections."
            "api_delete_so_fulfillment.asyncio_detailed",
            side_effect=fake_delete_ful,
        ),
        patch(
            "katana_mcp.tools.foundation.corrections."
            "api_update_sales_order.asyncio_detailed",
            side_effect=fake_update_so,
        ),
        patch(
            "katana_mcp.tools.foundation.corrections."
            "api_update_so_row.asyncio_detailed",
            side_effect=boom_update_row,
        ),
        patch(
            "katana_mcp.tools.foundation.corrections.is_success",
            return_value=True,
        ),
    ):
        response = await _correct_sales_order_impl(
            CorrectSalesOrderRequest(
                id=99,
                line_changes=[SOLineCorrection(old_variant_id=500, new_variant_id=501)],
                preview=False,
            ),
            context,
        )

    # Hand the response to the merge helper exactly as ``build_so_modify_ui``
    # does. Result: 3 executed + 2 NOT-RUN = 5 rows visible on the morph.
    response_dict = response.model_dump()
    merged = _so_actions_with_not_run_tail(response_dict, is_preview=False)
    assert len(merged) == 5

    # Plan order preserved: APPLIED, APPLIED, FAILED, NOT RUN, NOT RUN.
    status_labels = [a.get("status_label") for a in merged]
    assert status_labels[-2:] == ["NOT RUN", "NOT RUN"]
    # The trailing two are the recreate + close that never ran.
    assert [a.get("operation") for a in merged[-2:]] == [
        "add_fulfillment",
        "update_header",
    ]


# ============================================================================
# correct_purchase_order — fixtures
# ============================================================================


def _make_po(
    *,
    po_id: int = 156,
    status: str = "RECEIVED",
    rows: list[PurchaseOrderRow] | None = None,
) -> RegularPurchaseOrder:
    """Build a real attrs ``RegularPurchaseOrder`` in the requested status."""
    po = mock_entity_for_modify(RegularPurchaseOrder, id=po_id)
    po.status = PurchaseOrderStatus(status)
    po.purchase_order_rows = rows if rows is not None else []
    return po


def _make_po_row(
    *,
    row_id: int,
    variant_id: int,
    quantity: float = 10.0,
    price_per_unit: float = 5.0,
    received_date: datetime | None = None,
) -> PurchaseOrderRow:
    row = mock_entity_for_modify(PurchaseOrderRow, id=row_id)
    row.variant_id = variant_id
    row.quantity = quantity
    row.price_per_unit = price_per_unit
    row.received_date = received_date if received_date is not None else UNSET
    row.batch_transactions = UNSET
    return row


# ============================================================================
# correct_purchase_order — entry-condition checks
# ============================================================================


@pytest.mark.asyncio
async def test_correct_po_rejects_open_status():
    """A PO that's still NOT_RECEIVED has no close-state to preserve."""
    context, _ = create_mock_context()
    po = _make_po(status="NOT_RECEIVED")

    with (
        patch(
            "katana_mcp.tools.foundation.corrections._fetch_purchase_order_attrs",
            new_callable=AsyncMock,
            return_value=po,
        ),
        pytest.raises(ValueError, match="RECEIVED or PARTIALLY_RECEIVED"),
    ):
        await _correct_purchase_order_impl(
            CorrectPurchaseOrderRequest(
                id=156,
                row_changes=[PORowCorrection(row_id=501, new_variant_id=600)],
            ),
            context,
        )


@pytest.mark.asyncio
async def test_correct_po_rejects_missing_row_id():
    """If row_id isn't on the PO, the tool errors clearly."""
    context, _ = create_mock_context()
    received = datetime(2026, 4, 1, 10, 0, 0, tzinfo=UTC)
    rows = [
        _make_po_row(row_id=501, variant_id=300, received_date=received),
    ]
    po = _make_po(status="RECEIVED", rows=rows)

    with (
        patch(
            "katana_mcp.tools.foundation.corrections._fetch_purchase_order_attrs",
            new_callable=AsyncMock,
            return_value=po,
        ),
        pytest.raises(ValueError, match="No row on PO 156 has id 999"),
    ):
        await _correct_purchase_order_impl(
            CorrectPurchaseOrderRequest(
                id=156,
                row_changes=[PORowCorrection(row_id=999, new_variant_id=600)],
            ),
            context,
        )


@pytest.mark.asyncio
async def test_correct_po_rejects_empty_correction():
    """A row_changes entry with neither variant nor quantity nor price is a
    no-op and should error."""
    context, _ = create_mock_context()
    received = datetime(2026, 4, 1, 10, 0, 0, tzinfo=UTC)
    rows = [
        _make_po_row(row_id=501, variant_id=300, received_date=received),
    ]
    po = _make_po(status="RECEIVED", rows=rows)

    with (
        patch(
            "katana_mcp.tools.foundation.corrections._fetch_purchase_order_attrs",
            new_callable=AsyncMock,
            return_value=po,
        ),
        pytest.raises(ValueError, match="must supply at least one"),
    ):
        await _correct_purchase_order_impl(
            CorrectPurchaseOrderRequest(
                id=156,
                row_changes=[PORowCorrection(row_id=501)],
            ),
            context,
        )


@pytest.mark.asyncio
async def test_correct_po_rejects_quantity_below_already_received():
    """Preflight: refuse when row_changes drops quantity below the
    already-received qty for that row. Catches the failure before any
    mutations land — the receive replay would otherwise fail and leave the
    PO stuck NOT_RECEIVED with the close-state already cleared."""
    context, _ = create_mock_context()
    received = datetime(2026, 4, 1, 10, 0, 0, tzinfo=UTC)
    rows = [
        _make_po_row(row_id=501, variant_id=300, quantity=10.0, received_date=received),
    ]
    po = _make_po(status="RECEIVED", rows=rows)

    with (
        patch(
            "katana_mcp.tools.foundation.corrections._fetch_purchase_order_attrs",
            new_callable=AsyncMock,
            return_value=po,
        ),
        pytest.raises(ValueError, match="already received"),
    ):
        await _correct_purchase_order_impl(
            CorrectPurchaseOrderRequest(
                id=156,
                # Drop quantity to 5 — below the 10 already received.
                row_changes=[PORowCorrection(row_id=501, quantity=5.0)],
            ),
            context,
        )


# ============================================================================
# correct_purchase_order — preview
# ============================================================================


@pytest.mark.asyncio
async def test_correct_po_preview_emits_full_action_plan():
    """Preview should plan: revert → edit → re-receive (per row).

    No final close PATCH — the receive endpoint auto-promotes status back
    to RECEIVED when every row is fully received.
    """
    context, _ = create_mock_context()
    received = datetime(2026, 4, 1, 10, 0, 0, tzinfo=UTC)
    rows = [
        _make_po_row(
            row_id=501,
            variant_id=300,
            quantity=10.0,
            received_date=received,
        ),
    ]
    po = _make_po(status="RECEIVED", rows=rows)

    with patch(
        "katana_mcp.tools.foundation.corrections._fetch_purchase_order_attrs",
        new_callable=AsyncMock,
        return_value=po,
    ):
        response = await _correct_purchase_order_impl(
            CorrectPurchaseOrderRequest(
                id=156,
                row_changes=[PORowCorrection(row_id=501, new_variant_id=400)],
                preview=True,
            ),
            context,
        )

    assert response.is_preview is True
    assert response.entity_id == 156
    operations = [a.operation for a in response.actions]
    # Revert + edit + receive (one per receipt; here exactly one).
    assert operations == ["update_header", "update_row", "receive"]
    receive_action = response.actions[-1]
    # The receive action's diff includes received_date and quantity.
    fields = {c.field for c in receive_action.changes}
    assert "received_date" in fields
    assert "quantity" in fields
    # All preview-shape: succeeded=None
    assert all(a.succeeded is None for a in response.actions)


@pytest.mark.asyncio
async def test_correct_po_preview_partially_received_warns():
    """A PARTIALLY_RECEIVED PO surfaces a warning that the unreceived
    remnant rows stay open after the correction lands."""
    context, _ = create_mock_context()
    received = datetime(2026, 4, 1, 10, 0, 0, tzinfo=UTC)
    rows = [
        # Received split — appears in snapshot.
        _make_po_row(
            row_id=501,
            variant_id=300,
            quantity=7.0,
            received_date=received,
        ),
        # Unreceived remnant — skipped from snapshot.
        _make_po_row(
            row_id=502,
            variant_id=300,
            quantity=3.0,
            received_date=None,
        ),
    ]
    po = _make_po(status="PARTIALLY_RECEIVED", rows=rows)

    with patch(
        "katana_mcp.tools.foundation.corrections._fetch_purchase_order_attrs",
        new_callable=AsyncMock,
        return_value=po,
    ):
        response = await _correct_purchase_order_impl(
            CorrectPurchaseOrderRequest(
                id=156,
                row_changes=[PORowCorrection(row_id=501, new_variant_id=400)],
                preview=True,
            ),
            context,
        )

    # Only one re-receive (for the row that had a received_date).
    operations = [a.operation for a in response.actions]
    assert operations == ["update_header", "update_row", "receive"]
    # Warning about unreceived remnant rows.
    assert any("unreceived remnant" in w for w in response.warnings)


# ============================================================================
# correct_purchase_order — apply
# ============================================================================


@pytest.mark.asyncio
async def test_correct_po_apply_executes_phases_in_canonical_order():
    """Apply order:
    1. PATCH PO header (revert: status → NOT_RECEIVED)
    2. PATCH each row per row_changes
    3. POST /purchase_order_receive once per captured receipt"""
    context, _ = create_mock_context()
    received = datetime(2026, 4, 1, 10, 0, 0, tzinfo=UTC)
    rows = [
        _make_po_row(
            row_id=501,
            variant_id=300,
            quantity=10.0,
            received_date=received,
        ),
    ]
    po = _make_po(status="RECEIVED", rows=rows)

    call_log: list[str] = []

    async def fake_update_po(*, id, client, body):
        call_log.append(f"PATCH PO {id} status={body.status.value}")
        resp = MagicMock()
        resp.parsed = po
        return resp

    async def fake_update_row(*, id, client, body):
        call_log.append(f"PATCH PO row {id}")
        resp = MagicMock()
        resp.parsed = rows[0]
        return resp

    async def fake_receive(*, client, body):
        # body is a PurchaseOrderReceiveRow when single-row.
        call_log.append(
            f"POST receive row={body.purchase_order_row_id} qty={body.quantity}"
        )
        resp = MagicMock()
        resp.status_code = 204
        return resp

    with (
        patch(
            "katana_mcp.tools.foundation.corrections._fetch_purchase_order_attrs",
            new_callable=AsyncMock,
            return_value=po,
        ),
        patch(
            "katana_mcp.tools.foundation.corrections."
            "api_update_purchase_order.asyncio_detailed",
            side_effect=fake_update_po,
        ),
        patch(
            "katana_mcp.tools.foundation.corrections."
            "api_update_purchase_order_row.asyncio_detailed",
            side_effect=fake_update_row,
        ),
        patch(
            "katana_mcp.tools.foundation.corrections."
            "api_receive_purchase_order.asyncio_detailed",
            side_effect=fake_receive,
        ),
        patch(
            "katana_mcp.tools.foundation.corrections.is_success",
            return_value=True,
        ),
    ):
        response = await _correct_purchase_order_impl(
            CorrectPurchaseOrderRequest(
                id=156,
                row_changes=[
                    PORowCorrection(row_id=501, new_variant_id=400, quantity=12.0)
                ],
                preview=False,
            ),
            context,
        )

    assert response.is_preview is False
    assert all(a.succeeded is True for a in response.actions)
    assert call_log == [
        "PATCH PO 156 status=NOT_RECEIVED",
        "PATCH PO row 501",
        "POST receive row=501 qty=10.0",
    ]
    # Snapshot is in prior_state under the documented sentinel key.
    assert response.prior_state is not None
    assert "_close_state_snapshot" in response.prior_state


@pytest.mark.asyncio
async def test_correct_po_apply_halts_on_revert_failure():
    """If the revert PATCH fails, no edits or receives run; the response
    surfaces the breadcrumb."""
    context, _ = create_mock_context()
    received = datetime(2026, 4, 1, 10, 0, 0, tzinfo=UTC)
    rows = [
        _make_po_row(row_id=501, variant_id=300, received_date=received),
    ]
    po = _make_po(status="RECEIVED", rows=rows)

    async def boom(*args, **kwargs):
        raise RuntimeError("Katana refused to revert")

    with (
        patch(
            "katana_mcp.tools.foundation.corrections._fetch_purchase_order_attrs",
            new_callable=AsyncMock,
            return_value=po,
        ),
        patch(
            "katana_mcp.tools.foundation.corrections."
            "api_update_purchase_order.asyncio_detailed",
            side_effect=boom,
        ),
    ):
        response = await _correct_purchase_order_impl(
            CorrectPurchaseOrderRequest(
                id=156,
                row_changes=[PORowCorrection(row_id=501, new_variant_id=400)],
                preview=False,
            ),
            context,
        )

    assert response.is_preview is False
    # Only the revert action ran, and it failed.
    assert len(response.actions) == 1
    assert response.actions[0].succeeded is False
    # Breadcrumb language flagged.
    assert any("intermediate (open) state" in w for w in response.warnings)
    assert response.prior_state is not None
