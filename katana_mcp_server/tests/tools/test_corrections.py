"""Tests for correct_manufacturing_order, correct_sales_order, and
correct_purchase_order.

Covers the reopen → modify → restore pattern: snapshot capture, ordering
of API calls (revert before edits before recreate before close), preview
shape, and partial-failure breadcrumb.
"""

from contextlib import ExitStack
from dataclasses import dataclass, field
from datetime import UTC, datetime
from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from katana_mcp.tools._reopen import snapshot_po_close_state
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

from katana_public_api_client.client_types import UNSET, Response
from katana_public_api_client.models import (
    ManufacturingOrder,
    ManufacturingOrderProduction,
    ManufacturingOrderRecipeRow,
    ManufacturingOrderStatus,
    PurchaseOrderAdditionalCostRow,
    PurchaseOrderAdditionalCostRowListResponse,
    PurchaseOrderRow,
    PurchaseOrderRowBatchTransactionsItem,
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
    # SO modify-card morph picks them up via ``_actions_with_not_run_tail``.
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
    from katana_mcp.tools.prefab_ui import _actions_with_not_run_tail

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
    merged = _actions_with_not_run_tail(response_dict, is_preview=False)
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
# correct_purchase_order — an in-memory Katana purchase order
# ============================================================================
#
# The PO correction is defined by how Katana reacts to receive / revert /
# row edits, so these tests run it against a small model of that behaviour
# (pinned live by tests/integration/test_po_receipt_groups_live.py) instead
# of canned response sequences:
#
# - each receive call records one new receipt group; a partial quantity
#   splits the row, the received part gets a new id and the original id
#   stays on the open remainder. A first call that receives the whole
#   order keeps the rows in the default group.
# - the revert is refused while PARTIALLY_RECEIVED; otherwise it clears
#   every receipt, returns rows and cost rows to the default group and
#   merges rows identical apart from quantity into the lowest id.
# - received rows cannot be patched and a RECEIVED order refuses new rows.

_PO_ID = 156
_ROW_FIELDS = (
    "variant_id",
    "quantity",
    "price_per_unit",
    "tax_rate_id",
    "arrival_date",
    "location_id",
    "purchase_uom",
    "purchase_uom_conversion_rate",
)
D1 = datetime(2026, 9, 11, 21, 20, tzinfo=UTC)
D2 = datetime(2026, 9, 14, 21, 58, tzinfo=UTC)
D3 = datetime(2026, 9, 20, 9, 0, tzinfo=UTC)


def _response(parsed: object = None, status: int = 200) -> Response:
    return Response(
        status_code=HTTPStatus(status),
        content=b"" if status < 400 else b'{"message": "refused"}',
        headers={},
        parsed=parsed,
    )


@dataclass
class _Row:
    id: int
    variant_id: int
    quantity: float
    price_per_unit: float = 5.0
    received_date: datetime | None = None
    group_id: int = 0
    batches: list[tuple[int | None, float]] = field(default_factory=list)
    tax_rate_id: int = 1
    arrival_date: datetime = datetime(2026, 10, 20, tzinfo=UTC)
    location_id: int = 9
    purchase_uom: str | None = None
    purchase_uom_conversion_rate: float | None = None

    def merge_key(self) -> tuple:
        return (
            self.variant_id,
            self.price_per_unit,
            self.tax_rate_id,
            self.arrival_date,
            self.location_id,
        )


@dataclass
class _CostRow:
    id: int
    group_id: int
    additional_cost_id: int = 3
    tax_rate_id: int | None = 1
    price: float = 12.5
    distribution_method: str = "BY_VALUE"


class FakePurchaseOrder:
    """Just enough of Katana's purchase order behaviour for the correction."""

    def __init__(self) -> None:
        self.default_group = 10
        self.rows: list[_Row] = []
        self.cost_rows: list[_CostRow] = []
        self._next_row = 900
        self._next_group = 20
        self._next_cost = 70
        self.calls: list[str] = []
        self.fail_on: dict[str, int] = {}  # call kind -> 1-based occurrence
        self.after_revert = None  # optional hook to tamper with the reverted rows
        self.timeout_after: set[str] = set()  # kinds applied, then timed out

    # -- setup -----------------------------------------------------------
    def add_row(self, row_id: int, variant_id: int, quantity: float, **kw) -> _Row:
        row = _Row(row_id, variant_id, quantity, group_id=self.default_group, **kw)
        self.rows.append(row)
        return row

    def receive_now(self, items: list[tuple[int, float, datetime]]) -> int:
        """Receive during setup without logging the call."""
        return self._receive(items)

    def add_cost_row(self, group_id: int) -> _CostRow:
        cost = _CostRow(self._next_cost, group_id)
        self._next_cost += 1
        self.cost_rows.append(cost)
        return cost

    # -- state -----------------------------------------------------------
    @property
    def status(self) -> str:
        received = [r.received_date is not None for r in self.rows]
        if received and all(received):
            return "RECEIVED"
        return "PARTIALLY_RECEIVED" if any(received) else "NOT_RECEIVED"

    def summary(self) -> list[tuple]:
        """(variant, qty, price, received_date) per row, sorted."""
        return sorted(
            (r.variant_id, r.quantity, r.price_per_unit, r.received_date or D3)
            for r in self.rows
        )

    def groups_by_date(self) -> dict[datetime, set[int]]:
        out: dict[datetime, set[int]] = {}
        for r in self.rows:
            if r.received_date is not None:
                out.setdefault(r.received_date, set()).add(r.group_id)
        return out

    def to_attrs(self) -> RegularPurchaseOrder:
        rows = []
        for r in self.rows:
            row = mock_entity_for_modify(PurchaseOrderRow, id=r.id)
            row.variant_id = r.variant_id
            row.quantity = r.quantity
            row.price_per_unit = r.price_per_unit
            row.received_date = r.received_date if r.received_date else UNSET
            row.group_id = r.group_id
            row.tax_rate_id = r.tax_rate_id
            row.arrival_date = r.arrival_date
            row.location_id = r.location_id
            row.purchase_uom = r.purchase_uom if r.purchase_uom else UNSET
            row.purchase_uom_conversion_rate = (
                r.purchase_uom_conversion_rate
                if r.purchase_uom_conversion_rate is not None
                else UNSET
            )
            row.batch_transactions = [
                PurchaseOrderRowBatchTransactionsItem(
                    quantity=q, batch_id=b if b is not None else UNSET
                )
                for b, q in r.batches
            ] or UNSET
            rows.append(row)
        po = mock_entity_for_modify(RegularPurchaseOrder, id=_PO_ID)
        po.status = PurchaseOrderStatus(self.status)
        po.purchase_order_rows = rows
        return po

    # -- behaviour -------------------------------------------------------
    def _should_fail(self, kind: str) -> bool:
        count = sum(1 for c in self.calls if c.startswith(kind))
        return self.fail_on.get(kind) == count

    def _receive(self, items: list[tuple[int, float, datetime]]) -> int:
        whole_order = (
            all(r.received_date is None for r in self.rows)
            and {i for i, _, _ in items} == {r.id for r in self.rows}
            and all(
                q == next(r for r in self.rows if r.id == i).quantity
                for i, q, _ in items
            )
        )
        if whole_order:
            group = self.default_group
        else:
            group = self._next_group
            self._next_group += 1
        for row_id, qty, when in items:
            row = next(r for r in self.rows if r.id == row_id)
            assert row.received_date is None and qty <= row.quantity + 1e-9
            if abs(qty - row.quantity) < 1e-9:
                row.received_date, row.group_id = when, group
            else:
                row.quantity -= qty
                self.rows.append(
                    _Row(
                        self._next_row,
                        row.variant_id,
                        qty,
                        row.price_per_unit,
                        when,
                        group,
                        tax_rate_id=row.tax_rate_id,
                        arrival_date=row.arrival_date,
                        location_id=row.location_id,
                        purchase_uom=row.purchase_uom,
                        purchase_uom_conversion_rate=row.purchase_uom_conversion_rate,
                    )
                )
                self._next_row += 1
        return group

    async def fetch(self, services, po_id):
        return self.to_attrs()

    async def receive(self, *, client, body):
        self.calls.append(
            "receive "
            + ",".join(
                f"{b.purchase_order_row_id}:{b.quantity}@{b.received_date:%m-%d}"
                for b in body
            )
        )
        if self._should_fail("receive"):
            return _response(status=422)
        for b in body:
            row = next((r for r in self.rows if r.id == b.purchase_order_row_id), None)
            if row is None or row.received_date is not None:
                return _response(status=422)
            batches = b.batch_transactions if b.batch_transactions is not UNSET else []
            row.batches = [(t.batch_id, t.quantity) for t in batches]
        self._receive(
            [(b.purchase_order_row_id, b.quantity, b.received_date) for b in body]
        )
        return _response(status=204)

    async def update_po(self, *, id, client, body):
        self.calls.append(f"revert {body.status.value}")
        if self._should_fail("revert") or self.status == "PARTIALLY_RECEIVED":
            return _response(status=422)
        merged: dict[tuple, _Row] = {}
        for row in sorted(self.rows, key=lambda r: r.id):
            row.received_date, row.group_id = None, self.default_group
            row.batches = []
            keep = merged.get(row.merge_key())
            if keep is None:
                merged[row.merge_key()] = row
            else:
                keep.quantity += row.quantity
        self.rows = sorted(merged.values(), key=lambda r: r.id)
        for cost in self.cost_rows:
            cost.group_id = self.default_group
        if self.after_revert is not None:
            self.after_revert(self)
        if "revert" in self.timeout_after:
            raise httpx.ReadTimeout("timed out after the revert landed")
        if "revert 5xx" in self.timeout_after:
            return _response(status=500)
        return _response()

    async def update_row(self, *, id, client, body):
        fields = {
            k: getattr(body, k)
            for k in _ROW_FIELDS
            if getattr(body, k, UNSET) is not UNSET
        }
        self.calls.append(f"patch row {id} {fields}")
        row = next(r for r in self.rows if r.id == id)
        if self._should_fail("patch") or row.received_date is not None:
            return _response(status=422)
        for key, value in fields.items():
            setattr(row, key, value)
        return _response(parsed=mock_entity_for_modify(PurchaseOrderRow, id=id))

    async def create_row(self, *, client, body):
        self.calls.append(
            f"create row v{body.variant_id} q{body.quantity} p{body.price_per_unit}"
        )
        if self._should_fail("create row") or self.status == "RECEIVED":
            return _response(status=422)
        row = _Row(
            self._next_row,
            body.variant_id,
            body.quantity,
            body.price_per_unit,
            group_id=self.default_group,
        )
        for key in _ROW_FIELDS[3:]:
            value = getattr(body, key, UNSET)
            if value is not UNSET:
                setattr(row, key, value)
        self._next_row += 1
        self.rows.append(row)
        return _response(parsed=mock_entity_for_modify(PurchaseOrderRow, id=row.id))

    def _cost_attrs(self, cost: _CostRow) -> PurchaseOrderAdditionalCostRow:
        return PurchaseOrderAdditionalCostRow(
            id=cost.id,
            group_id=cost.group_id,
            additional_cost_id=cost.additional_cost_id,
            tax_rate_id=cost.tax_rate_id if cost.tax_rate_id is not None else UNSET,
            price=cost.price,
            distribution_method=cost.distribution_method,
        )

    async def list_cost_rows(self, *, client, group_id):
        data = [self._cost_attrs(c) for c in self.cost_rows if c.group_id == group_id]
        return _response(parsed=PurchaseOrderAdditionalCostRowListResponse(data=data))

    async def get_cost_row(self, *, id, client):
        cost = next(c for c in self.cost_rows if c.id == id)
        return _response(parsed=self._cost_attrs(cost))

    async def create_cost_row(self, *, client, body):
        self.calls.append(f"create cost row on group {body.group_id}")
        cost = self.add_cost_row(body.group_id)
        return _response(parsed=self._cost_attrs(cost))

    async def delete_cost_row(self, *, id, client):
        self.calls.append(f"delete cost row {id}")
        if self._should_fail("delete cost"):
            return _response(status=422)
        self.cost_rows = [c for c in self.cost_rows if c.id != id]
        return _response(status=204)

    def patched(self):
        base = "katana_mcp.tools.foundation.corrections."
        return ExitStackPatches(
            [
                patch(base + "_fetch_purchase_order_attrs", side_effect=self.fetch),
                patch(
                    base + "api_receive_purchase_order.asyncio_detailed",
                    side_effect=self.receive,
                ),
                patch(
                    base + "api_update_purchase_order.asyncio_detailed",
                    side_effect=self.update_po,
                ),
                patch(
                    base + "api_update_purchase_order_row.asyncio_detailed",
                    side_effect=self.update_row,
                ),
                patch(
                    base + "api_create_purchase_order_row.asyncio_detailed",
                    side_effect=self.create_row,
                ),
                patch(
                    base + "api_get_po_cost_rows.asyncio_detailed",
                    side_effect=self.list_cost_rows,
                ),
                patch(
                    base + "api_get_po_cost_row.asyncio_detailed",
                    side_effect=self.get_cost_row,
                ),
                patch(
                    base + "api_create_po_cost_row.asyncio_detailed",
                    side_effect=self.create_cost_row,
                ),
                patch(
                    base + "api_delete_po_cost_row.asyncio_detailed",
                    side_effect=self.delete_cost_row,
                ),
            ]
        )


class ExitStackPatches:
    def __init__(self, patches: list) -> None:
        self._patches = patches
        self._stack = ExitStack()

    def __enter__(self) -> None:
        for p in self._patches:
            self._stack.enter_context(p)

    def __exit__(self, *exc: object) -> None:
        self._stack.close()


async def _correct(fake: FakePurchaseOrder, *changes: PORowCorrection, preview=False):
    context, _ = create_mock_context()
    with fake.patched():
        return await _correct_purchase_order_impl(
            CorrectPurchaseOrderRequest(
                id=_PO_ID, row_changes=list(changes), preview=preview
            ),
            context,
        )


def _two_parcels() -> FakePurchaseOrder:
    """10 + 1 of variant 300 (same price) and 1 of 301: 9 of 300 on D1,
    then the last 300 and the 301 on D2. Leaves rows 501 (300, 1, D2),
    900 (300, 9, D1) and 502 (301, 1, D2)."""
    fake = FakePurchaseOrder()
    fake.add_row(501, 300, 10.0)
    fake.add_row(502, 301, 1.0)
    fake.receive_now([(501, 9.0, D1)])
    fake.receive_now([(501, 1.0, D2), (502, 1.0, D2)])
    return fake


def _assert_succeeded(response) -> None:
    assert all(a.succeeded for a in response.actions), [
        a.error for a in response.actions
    ]


# ============================================================================
# correct_purchase_order — snapshot
# ============================================================================


def test_snapshot_captures_rows_groups_and_predicted_merges():
    fake = _two_parcels()
    fake.add_row(503, 302, 5.0)  # open
    snapshot = snapshot_po_close_state(fake.to_attrs())

    assert [r.row_id for r in snapshot.open_rows] == [503]
    groups = snapshot.receipt_groups()
    assert [g.received_date for g in groups] == [D1, D2]
    assert sorted(r.row_id for r in groups[1].rows) == [501, 502]
    # 501 and its split 900 are identical apart from quantity: one merge set,
    # lowest id first.
    merges = [[r.row_id for r in s] for s in snapshot.predicted_merges()]
    assert [501, 900] in merges


def test_snapshot_without_group_ids_keeps_receipts_apart_by_date():
    fake = FakePurchaseOrder()
    fake.add_row(501, 300, 1.0)
    fake.add_row(502, 301, 1.0)
    fake.receive_now([(501, 1.0, D1)])
    fake.receive_now([(502, 1.0, D2)])
    po = fake.to_attrs()
    rows = po.purchase_order_rows
    assert isinstance(rows, list)
    for row in rows:
        row.group_id = UNSET

    groups = snapshot_po_close_state(po).receipt_groups()

    assert [(g.group_id, g.received_date) for g in groups] == [(None, D1), (None, D2)]


# ============================================================================
# correct_purchase_order — refusals (nothing written)
# ============================================================================


@pytest.mark.asyncio
async def test_correct_po_rejects_open_status():
    fake = FakePurchaseOrder()
    fake.add_row(501, 300, 10.0)
    with pytest.raises(ValueError, match="RECEIVED or PARTIALLY_RECEIVED"):
        await _correct(fake, PORowCorrection(row_id=501, new_variant_id=600))
    assert fake.calls == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("changes", "match"),
    [
        ([PORowCorrection(row_id=999, new_variant_id=600)], "No row on PO 156"),
        ([PORowCorrection(row_id=502)], "must supply at least one"),
        (
            [
                PORowCorrection(row_id=502, price_per_unit=1.0),
                PORowCorrection(row_id=502, quantity=2.0),
            ],
            "more than once",
        ),
    ],
)
async def test_correct_po_rejects_bad_row_changes(changes, match):
    fake = _two_parcels()
    with pytest.raises(ValueError, match=match):
        await _correct(fake, *changes)
    assert fake.calls == []


@pytest.mark.asyncio
async def test_correct_po_refuses_quantity_or_variant_edit_on_batched_row():
    fake = FakePurchaseOrder()
    fake.add_row(501, 300, 4.0)
    fake.receive_now([(501, 4.0, D1)])
    fake.rows[0].batches = [(41, 3.0), (42, 1.0)]

    with pytest.raises(ValueError, match="received into batches"):
        await _correct(fake, PORowCorrection(row_id=501, quantity=5.0))
    with pytest.raises(ValueError, match="received into batches"):
        await _correct(fake, PORowCorrection(row_id=501, new_variant_id=301))
    assert fake.calls == []


# ============================================================================
# correct_purchase_order — preview
# ============================================================================


@pytest.mark.asyncio
async def test_correct_po_preview_reports_the_real_plan_and_writes_nothing():
    fake = _two_parcels()

    response = await _correct(
        fake, PORowCorrection(row_id=900, quantity=12.0), preview=True
    )

    assert fake.calls == []
    assert response.is_preview is True
    assert [a.operation for a in response.actions] == [
        "update_header",
        "update_row",
        "receive",
        "receive",
    ]
    rebuild = response.actions[1].changes
    # The requested quantity is shown as requested, not merge-adjusted.
    assert any(
        c.field == "row 900 quantity" and c.old == 9.0 and c.new == 12.0
        for c in rebuild
    )
    recreated = next(c for c in rebuild if c.field == "rows_recreated_after_merge")
    assert recreated.new == [{"source_row_id": 900, "variant_id": 300, "quantity": 9.0}]
    first = next(c for c in response.actions[2].changes if c.field == "rows")
    assert first.new == [{"source_row_id": 900, "variant_id": 300, "quantity": 12.0}]
    assert any("re-created afterwards" in w for w in response.warnings)
    assert any(
        "Expected status afterwards: RECEIVED" in n for n in response.next_actions
    )


# ============================================================================
# correct_purchase_order — apply
# ============================================================================


@pytest.mark.asyncio
async def test_correct_po_rebuilds_both_parcels_with_their_dates():
    fake = _two_parcels()
    before = fake.summary()

    response = await _correct(fake, PORowCorrection(row_id=502, price_per_unit=2.0))

    _assert_succeeded(response)
    assert fake.status == "RECEIVED"
    assert fake.summary() == [
        (r[0], r[1], 2.0 if r[0] == 301 else r[2], r[3]) for r in before
    ]
    groups = fake.groups_by_date()
    assert set(groups) == {D1, D2}
    assert all(len(g) == 1 for g in groups.values())
    assert groups[D1] != groups[D2]
    # 501 absorbed its split 900 in the revert: 501 is patched back to 1,
    # 900 is re-created, then each parcel is received by exact row id.
    assert fake.calls == [
        "revert NOT_RECEIVED",
        "patch row 501 {'quantity': 1.0}",
        "patch row 502 {'price_per_unit': 2.0}",
        "create row v300 q9.0 p5.0",
        "receive 901:9.0@09-11",
        "receive 501:1.0@09-14,502:1.0@09-14",
    ]
    assert any("Status now RECEIVED" in n for n in response.next_actions)


@pytest.mark.asyncio
async def test_correct_po_variant_change_on_split_row_leaves_its_sibling_alone():
    """Finding: re-varianting a row the revert merges used to drag the other
    rows of that variant along and then fail the replay."""
    fake = _two_parcels()

    response = await _correct(fake, PORowCorrection(row_id=900, new_variant_id=400))

    _assert_succeeded(response)
    assert fake.status == "RECEIVED"
    assert fake.summary() == sorted(
        [(400, 9.0, 5.0, D1), (300, 1.0, 5.0, D2), (301, 1.0, 5.0, D2)]
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("variant_first", [True, False])
async def test_correct_po_two_edits_on_merging_rows_work_in_either_order(
    variant_first,
):
    fake = _two_parcels()
    edits = [
        PORowCorrection(row_id=900, new_variant_id=400),
        PORowCorrection(row_id=501, quantity=3.0),
    ]
    if not variant_first:
        edits.reverse()

    response = await _correct(fake, *edits)

    _assert_succeeded(response)
    assert fake.summary() == sorted(
        [(400, 9.0, 5.0, D1), (300, 3.0, 5.0, D2), (301, 1.0, 5.0, D2)]
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("new_qty", [12.0, 4.0])
async def test_correct_po_quantity_edit_on_received_row_is_re_received(new_qty):
    """A corrected quantity on a received row is the quantity received:
    the PO comes back RECEIVED, not PARTIALLY_RECEIVED, and a lower
    quantity is no longer refused."""
    fake = _two_parcels()

    response = await _correct(fake, PORowCorrection(row_id=900, quantity=new_qty))

    _assert_succeeded(response)
    assert fake.status == "RECEIVED"
    assert (300, new_qty, 5.0, D1) in fake.summary()
    assert not any("ended in status" in w for w in response.warnings)


@pytest.mark.asyncio
async def test_correct_po_price_edit_does_not_spread_to_merged_rows():
    fake = _two_parcels()

    response = await _correct(fake, PORowCorrection(row_id=900, price_per_unit=6.0))

    _assert_succeeded(response)
    assert fake.summary() == sorted(
        [(300, 9.0, 6.0, D1), (300, 1.0, 5.0, D2), (301, 1.0, 5.0, D2)]
    )


@pytest.mark.asyncio
async def test_correct_po_keeps_rows_with_different_prices_apart():
    fake = FakePurchaseOrder()
    # Listed out of id order: surviving rows must be matched by id, not by
    # position or variant, so only the edited row is written.
    fake.add_row(502, 300, 2.0, price_per_unit=7.0)
    fake.add_row(501, 300, 9.0, price_per_unit=5.0)
    fake.receive_now([(501, 9.0, D1)])
    fake.receive_now([(502, 2.0, D2)])

    response = await _correct(fake, PORowCorrection(row_id=502, price_per_unit=8.0))

    _assert_succeeded(response)
    assert fake.summary() == [(300, 2.0, 8.0, D2), (300, 9.0, 5.0, D1)]
    assert fake.calls == [
        "revert NOT_RECEIVED",
        "patch row 502 {'price_per_unit': 8.0}",
        "receive 501:9.0@09-11",
        "receive 502:2.0@09-14",
    ]


@pytest.mark.asyncio
async def test_correct_po_fractional_quantities_replay_exactly():
    fake = FakePurchaseOrder()
    fake.add_row(501, 300, 0.3)
    fake.receive_now([(501, 0.1, D1)])
    fake.receive_now([(501, 0.2, D2)])

    response = await _correct(fake, PORowCorrection(row_id=501, price_per_unit=1.0))

    _assert_succeeded(response)
    assert fake.status == "RECEIVED"
    # The fake's own setup split leaves 0.3 - 0.1 = 0.19999...; the replay
    # must receive exactly what was captured, with no allocation slack.
    replayed = sorted((r.received_date, r.quantity) for r in fake.rows)
    assert [d for d, _ in replayed] == [D1, D2]
    assert [q for _, q in replayed] == pytest.approx([0.1, 0.2])


@pytest.mark.asyncio
async def test_correct_po_partially_received_completes_reverts_and_leaves_rest_open():
    fake = FakePurchaseOrder()
    fake.add_row(501, 300, 10.0)
    fake.add_row(502, 301, 1.0)
    fake.receive_now([(501, 9.0, D1)])  # 900 = 9 received, 501 = 1 open

    response = await _correct(fake, PORowCorrection(row_id=900, price_per_unit=2.5))

    _assert_succeeded(response)
    assert fake.status == "PARTIALLY_RECEIVED"
    assert fake.summary() == sorted(
        [(300, 9.0, 2.5, D1), (300, 1.0, 5.0, D3), (301, 1.0, 5.0, D3)]
    )
    receives = [c for c in fake.calls if c.startswith("receive")]
    assert len(receives) == 2  # the temporary completion + one replay
    assert receives[0].startswith("receive 501:1.0@") and "502:1.0" in receives[0]
    assert any("Status now PARTIALLY_RECEIVED" in n for n in response.next_actions)
    assert not any("ended in status" in w for w in response.warnings)


@pytest.mark.asyncio
async def test_correct_po_replays_batches_on_a_price_only_edit():
    fake = FakePurchaseOrder()
    fake.add_row(501, 300, 4.0)
    fake.receive_now([(501, 4.0, D1)])
    fake.rows[0].batches = [(41, 3.0), (42, 1.0), (None, 0.0)]

    response = await _correct(fake, PORowCorrection(row_id=501, price_per_unit=1.0))

    _assert_succeeded(response)
    assert fake.rows[0].batches == [(41, 3.0), (42, 1.0)]


@pytest.mark.asyncio
async def test_correct_po_moves_cost_rows_to_the_rebuilt_groups():
    fake = _two_parcels()
    d2_group = next(iter(fake.groups_by_date()[D2]))
    original = fake.add_cost_row(d2_group)

    response = await _correct(fake, PORowCorrection(row_id=502, price_per_unit=2.0))

    _assert_succeeded(response)
    (moved,) = fake.cost_rows
    assert moved.id != original.id
    assert {moved.group_id} == fake.groups_by_date()[D2]
    assert response.actions[-1].operation == "update_additional_cost"


@pytest.mark.asyncio
async def test_correct_po_keeps_cost_row_when_the_replay_reuses_its_group():
    """A single receipt of the whole order stays in the default group, which
    is where the revert already put the cost row: nothing to move."""
    fake = FakePurchaseOrder()
    fake.add_row(501, 300, 2.0)
    fake.receive_now([(501, 2.0, D1)])
    original = fake.add_cost_row(fake.default_group)

    response = await _correct(fake, PORowCorrection(row_id=501, price_per_unit=1.0))

    _assert_succeeded(response)
    assert [c.id for c in fake.cost_rows] == [original.id]
    assert not any("cost row" in c for c in fake.calls)


# ============================================================================
# correct_purchase_order — failures
# ============================================================================


@pytest.mark.asyncio
async def test_correct_po_revert_failure_on_received_po_writes_nothing():
    fake = _two_parcels()
    fake.fail_on = {"revert": 1}
    before = fake.summary()

    response = await _correct(fake, PORowCorrection(row_id=502, price_per_unit=2.0))

    assert [a.succeeded for a in response.actions] == [False]
    assert fake.summary() == before
    assert any("Nothing was written" in w for w in response.warnings)
    assert response.prior_state is not None
    assert "_close_state_snapshot" in response.prior_state


@pytest.mark.asyncio
async def test_correct_po_revert_failure_after_completion_explains_temporary_receipt():
    fake = FakePurchaseOrder()
    fake.add_row(501, 300, 10.0)
    fake.receive_now([(501, 9.0, D1)])
    fake.fail_on = {"revert": 1}

    response = await _correct(fake, PORowCorrection(row_id=900, price_per_unit=2.5))

    assert [a.succeeded for a in response.actions] == [True, False]
    assert fake.status == "RECEIVED"
    assert any("Do not re-run" in w for w in response.warnings)
    assert any(
        "temporary step" in w and "row 501 qty 1.0" in w for w in response.warnings
    )
    assert any(
        "NOT_RECEIVED with modify_purchase_order" in n for n in response.next_actions
    )
    assert any("dated 2026-09-11" in n for n in response.next_actions)


@pytest.mark.asyncio
async def test_correct_po_mid_replay_failure_lists_the_receipts_left():
    fake = _two_parcels()
    fake.fail_on = {"receive": 2}

    response = await _correct(fake, PORowCorrection(row_id=502, price_per_unit=2.0))

    assert response.actions[-1].succeeded is False
    assert fake.status == "PARTIALLY_RECEIVED"
    assert any("Do not re-run" in w for w in response.warnings)
    (remaining,) = [n for n in response.next_actions if "receive_purchase_order" in n]
    assert "receipt dated 2026-09-14" in remaining
    assert "2026-09-11" not in remaining
    open_ids = sorted(r.id for r in fake.rows if r.received_date is None)
    for row_id in open_ids:
        assert f"row {row_id} " in remaining


@pytest.mark.asyncio
async def test_correct_po_keeps_per_row_dates_inside_one_receipt_group():
    """One receive call can carry a different date per row and still records
    one group; the replay keeps each row's own date and the single group."""
    fake = FakePurchaseOrder()
    fake.add_row(501, 300, 1.0)
    fake.add_row(502, 301, 1.0)
    fake.add_row(503, 302, 1.0)
    fake.receive_now([(501, 1.0, D1), (502, 1.0, D2)])
    fake.receive_now([(503, 1.0, D3)])

    response = await _correct(fake, PORowCorrection(row_id=503, price_per_unit=1.0))

    _assert_succeeded(response)
    dates = {r.variant_id: r.received_date for r in fake.rows}
    assert dates == {300: D1, 301: D2, 302: D3}
    groups = {r.variant_id: r.group_id for r in fake.rows}
    assert groups[300] == groups[301] != groups[302]


@pytest.mark.asyncio
async def test_correct_po_splits_a_row_received_in_three_parcels_back_apart():
    fake = FakePurchaseOrder()
    fake.add_row(501, 300, 10.0)
    fake.add_row(502, 301, 1.0)
    fake.receive_now([(501, 3.0, D1)])
    fake.receive_now([(501, 3.0, D2)])
    fake.receive_now([(501, 4.0, D3), (502, 1.0, D3)])

    response = await _correct(fake, PORowCorrection(row_id=502, price_per_unit=2.0))

    _assert_succeeded(response)
    assert fake.status == "RECEIVED"
    assert fake.summary() == sorted(
        [
            (300, 3.0, 5.0, D1),
            (300, 3.0, 5.0, D2),
            (300, 4.0, 5.0, D3),
            (301, 1.0, 2.0, D3),
        ]
    )
    assert len({g for gs in fake.groups_by_date().values() for g in gs}) == 3


@pytest.mark.asyncio
async def test_correct_po_variant_change_on_a_row_that_survives_the_revert():
    fake = _two_parcels()

    response = await _correct(fake, PORowCorrection(row_id=502, new_variant_id=400))

    _assert_succeeded(response)
    assert "patch row 502 {'variant_id': 400}" in fake.calls
    assert fake.summary() == sorted(
        [(300, 9.0, 5.0, D1), (300, 1.0, 5.0, D2), (400, 1.0, 5.0, D2)]
    )


def _drop_quantity(fake: FakePurchaseOrder) -> None:
    fake.rows[0].quantity -= 1.0


def _add_stray_row(fake: FakePurchaseOrder) -> None:
    fake.rows.append(_Row(999, 301, 0.0, group_id=fake.default_group))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("tamper", "match"),
    [
        (_drop_quantity, "do not add up"),
        (_add_stray_row, "match no captured row"),
    ],
)
async def test_correct_po_stops_before_editing_when_the_revert_looks_wrong(
    tamper, match
):
    """If the reverted rows do not account for exactly the captured rows,
    nothing is edited and the operator is told how to finish by hand."""
    fake = _two_parcels()
    fake.after_revert = tamper

    response = await _correct(fake, PORowCorrection(row_id=502, price_per_unit=2.0))

    assert [a.succeeded for a in response.actions] == [True, False]
    assert match in (response.actions[1].error or "")
    assert not any(c.startswith(("patch", "create", "receive")) for c in fake.calls)
    assert any("Do not re-run" in w for w in response.warnings)
    assert any("one row per entry" in n for n in response.next_actions)
    (remaining,) = [n for n in response.next_actions if "receive_purchase_order" in n]
    assert "rebuilt from 900" in remaining and "2026-09-11" in remaining


@pytest.mark.asyncio
async def test_correct_po_recreated_row_keeps_tax_arrival_location_and_uom():
    arrival = datetime(2026, 11, 30, tzinfo=UTC)
    fake = FakePurchaseOrder()
    fake.add_row(
        501,
        300,
        10.0,
        tax_rate_id=7,
        arrival_date=arrival,
        location_id=4,
        purchase_uom="box",
        purchase_uom_conversion_rate=12.0,
    )
    fake.receive_now([(501, 9.0, D1)])
    fake.receive_now([(501, 1.0, D2)])

    response = await _correct(fake, PORowCorrection(row_id=501, price_per_unit=6.0))

    _assert_succeeded(response)
    recreated = next(r for r in fake.rows if r.id != 501)
    assert (
        recreated.tax_rate_id,
        recreated.arrival_date,
        recreated.location_id,
        recreated.purchase_uom,
        recreated.purchase_uom_conversion_rate,
    ) == (7, arrival, 4, "box", 12.0)


def test_snapshot_skips_soft_deleted_rows():
    fake = _two_parcels()
    po = fake.to_attrs()
    rows = po.purchase_order_rows
    assert isinstance(rows, list)
    rows[0].deleted_at = D3

    snapshot = snapshot_po_close_state(po)

    assert rows[0].id not in {r.row_id for r in snapshot.rows}


@pytest.mark.asyncio
async def test_correct_po_cost_copy_made_but_original_not_deleted_says_delete():
    """Re-creating would double the cost: the copy already exists."""
    fake = _two_parcels()
    original = fake.add_cost_row(next(iter(fake.groups_by_date()[D2])))
    fake.fail_on = {"delete cost": 1}

    response = await _correct(fake, PORowCorrection(row_id=502, price_per_unit=2.0))

    assert response.actions[-1].succeeded is False
    copy = next(c for c in fake.cost_rows if c.id != original.id)
    (advice,) = [n for n in response.next_actions if "cost row" in n]
    assert f"as row {copy.id}" in advice
    assert f"delete row {original.id}" in advice
    assert "do not re-create" in advice


@pytest.mark.asyncio
async def test_correct_po_mid_rebuild_failure_lists_rows_done_and_left():
    fake = _two_parcels()
    fake.fail_on = {"create row": 1}

    response = await _correct(fake, PORowCorrection(row_id=502, price_per_unit=2.0))

    assert [a.succeeded for a in response.actions] == [True, False]
    (rebuild,) = [n for n in response.next_actions if "one row per entry" in n]
    assert "captured row 501 is row 501" in rebuild
    assert "captured row 502 is row 502" in rebuild
    assert "Still needing a row: captured rows [900]" in rebuild


@pytest.mark.asyncio
async def test_correct_po_failed_completion_writes_nothing():
    fake = FakePurchaseOrder()
    fake.add_row(501, 300, 10.0)
    fake.receive_now([(501, 9.0, D1)])
    fake.fail_on = {"receive": 1}
    before = fake.summary()

    response = await _correct(fake, PORowCorrection(row_id=900, price_per_unit=2.5))

    assert [a.succeeded for a in response.actions] == [False]
    assert fake.summary() == before
    assert any("Nothing was written" in w for w in response.warnings)


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["revert", "revert 5xx"])
async def test_correct_po_timeout_is_reported_as_unknown_outcome(failure):
    """A revert that times out or returns a server error after landing must
    not be reported as 'nothing was written': the receipts are already gone."""
    fake = _two_parcels()
    fake.timeout_after = {failure}

    response = await _correct(fake, PORowCorrection(row_id=502, price_per_unit=2.0))

    assert fake.status == "NOT_RECEIVED"
    assert any("may have reached Katana" in w for w in response.warnings)
    assert not any("Nothing was written" in w for w in response.warnings)
    assert any("Do not re-run" in w for w in response.warnings)
    assert any("receive_purchase_order" in n for n in response.next_actions)


@pytest.mark.asyncio
async def test_correct_po_warns_about_cost_rows_it_cannot_recreate():
    fake = _two_parcels()
    unusable = fake.add_cost_row(next(iter(fake.groups_by_date()[D2])))
    unusable.tax_rate_id = None

    response = await _correct(
        fake, PORowCorrection(row_id=502, price_per_unit=2.0), preview=True
    )

    assert any(
        f"[{unusable.id}]" in w and "leaves them there" in w for w in response.warnings
    )
