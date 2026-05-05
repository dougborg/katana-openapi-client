"""Composite ``correct_<entity>`` tools — transactional edit on closed records.

Lets the operator edit a record that has already reached a terminal status
(``DONE`` for an MO, ``DELIVERED`` for an SO) without losing the original
close-state metadata. Internally implements the proven sequence:

1. **Capture** the close-state (status + key timestamps + child snapshots)
2. **Reopen** by reverting status to an editable value (and, for SO,
   deleting fulfillments first — the close-state restore re-creates them)
3. **Apply** the user's edits (recipe row swap, line item update)
4. **Restore** the close-state, observing the mandatory ordering: status
   first, then dates (Katana validates date fields against the *current*
   status, so combined ``status: DONE + done_date`` calls fail).

Composes ``ActionSpec`` lists from :mod:`_modification_dispatch` and the
existing per-entity request builders. Each phase runs through
``execute_plan`` separately so fail-fast halts at a phase boundary with the
captured close-state available for manual recovery.

Tracked under #523 (umbrella). Phase 1 ships MO + SO; PO and stock
transfer are deferred.
"""

from __future__ import annotations

import asyncio
import dataclasses
from typing import Annotated, Any, cast

from fastmcp import Context, FastMCP
from fastmcp.tools import ToolResult
from pydantic import BaseModel, ConfigDict, Field

from katana_mcp.logging import observe_tool
from katana_mcp.services import get_services
from katana_mcp.tools._modification import (
    ActionResult,
    ConfirmableRequest,
    FieldChange,
    ModificationResponse,
    to_tool_result,
)
from katana_mcp.tools._modification_dispatch import (
    ActionSpec,
    ApplyCallable,
    execute_plan,
    plan_to_preview_results,
    serialize_for_prior_state,
)
from katana_mcp.tools._reopen import (
    MO_CLOSED_STATUSES,
    MO_REOPEN_STATUS,
    MO_RESTORE_STATUS,
    SO_CLOSED_STATUSES,
    SO_REOPEN_STATUS,
    SO_RESTORE_STATUS,
    MOCloseState,
    MOProductionSnapshot,
    SOCloseState,
    SOFulfillmentSnapshot,
    snapshot_mo_close_state,
    snapshot_so_close_state,
)
from katana_mcp.tools.foundation.manufacturing_orders import (
    MOOperation,
    _fetch_manufacturing_order_attrs,
)
from katana_mcp.tools.foundation.sales_orders import (
    SOOperation,
    _fetch_sales_order_attrs,
)
from katana_mcp.unpack import Unpack, unpack_pydantic_params
from katana_mcp.web_urls import katana_web_url
from katana_public_api_client.api.manufacturing_order import (
    update_manufacturing_order as api_update_manufacturing_order,
)
from katana_public_api_client.api.manufacturing_order_production import (
    create_manufacturing_order_production as api_create_mo_production,
    update_manufacturing_order_production as api_update_mo_production,
)
from katana_public_api_client.api.manufacturing_order_recipe import (
    update_manufacturing_order_recipe_rows as api_update_mo_recipe_row,
)
from katana_public_api_client.api.sales_order import (
    update_sales_order as api_update_sales_order,
)
from katana_public_api_client.api.sales_order_fulfillment import (
    create_sales_order_fulfillment as api_create_so_fulfillment,
    delete_sales_order_fulfillment as api_delete_so_fulfillment,
    get_all_sales_order_fulfillments as api_get_all_so_fulfillments,
)
from katana_public_api_client.api.sales_order_row import (
    update_sales_order_row as api_update_so_row,
)
from katana_public_api_client.domain.converters import to_unset, unwrap_unset
from katana_public_api_client.models import (
    CreateManufacturingOrderProductionRequest as APICreateMOProductionRequest,
    CreateSalesOrderFulfillmentRequest as APICreateSOFulfillmentRequest,
    ManufacturingOrderProduction,
    ManufacturingOrderRecipeRow,
    ManufacturingOrderStatus,
    SalesOrderFulfillment,
    SalesOrderFulfillmentRowRequest,
    SalesOrderFulfillmentStatus,
    SalesOrderRow,
    UpdateManufacturingOrderProductionRequest as APIUpdateMOProductionRequest,
    UpdateManufacturingOrderRecipeRowRequest as APIUpdateMORecipeRowRequest,
    UpdateManufacturingOrderRequest as APIUpdateManufacturingOrderRequest,
    UpdateSalesOrderRequest as APIUpdateSalesOrderRequest,
    UpdateSalesOrderRowRequest as APIUpdateSORowRequest,
    UpdateSalesOrderStatus,
)
from katana_public_api_client.utils import is_success, unwrap, unwrap_as

# ============================================================================
# Shared apply-builders
# ============================================================================
#
# The composite tools need patch closures that tolerate Katana's empty-200
# bodies on certain transitions (observed live on ``modify_sales_order`` →
# DELIVERED). The framework's ``make_patch_apply`` calls ``unwrap_as``,
# which raises ``APIError("No parsed response data for status 200")`` on
# empty bodies. We special-case here.


def _augment_prior_state_with_snapshot(
    prior_state: dict[str, Any] | None,
    snapshot: MOCloseState | SOCloseState,
) -> dict[str, Any]:
    """Inject the captured close-state into ``prior_state`` for recovery.

    The framework's :func:`serialize_for_prior_state` only serializes the
    top-level entity, but the manual-recovery breadcrumb on a failed
    correction needs the per-production / per-fulfillment snapshot too —
    that's the data the operator has to replay to finish the close. This
    splices the dataclass-derived snapshot under a sentinel key.
    """
    base: dict[str, Any] = dict(prior_state) if prior_state else {}
    base["_close_state_snapshot"] = dataclasses.asdict(snapshot)
    return base


async def _run_phases_until_failure(
    phases: list[list[ActionSpec]],
) -> tuple[list[ActionResult], bool]:
    """Run each phase via :func:`execute_plan`; halt on the first failed action.

    Returns ``(aggregated_results, failed)`` — ``failed=True`` means an
    action raised in some phase and subsequent phases were skipped. Callers
    use the boolean to branch into success vs failure response building.
    Empty phases are skipped silently.
    """
    aggregated: list[ActionResult] = []
    for phase in phases:
        if not phase:
            continue
        aggregated.extend(await execute_plan(phase))
        if any(a.succeeded is False for a in aggregated):
            return aggregated, True
    return aggregated, False


def _make_tolerant_patch_apply(
    endpoint: Any, services: Any, target_id: int, body: Any
) -> ApplyCallable:
    """Patch apply that returns ``None`` on a successful empty body.

    Mirrors :func:`make_patch_apply` but treats a missing parsed body on a
    success status as success (``None`` outcome) rather than raising via
    ``unwrap_as``. Used for status round-trips on closed-record restore
    where Katana intermittently echoes nothing on the 200.
    """

    async def apply() -> Any:
        response = await endpoint.asyncio_detailed(
            id=target_id, client=services.client, body=body
        )
        if response.parsed is not None:
            return response.parsed
        if is_success(response):
            return None
        # Surfaces the typed APIError on actual failures.
        unwrap(response)
        return None  # unreachable; unwrap raises on non-success

    return apply


# ============================================================================
# Manufacturing-order corrections
# ============================================================================


class MOIngredientCorrection(BaseModel):
    """One recipe-row edit, identified by the variant currently in the row.

    The tool resolves ``old_variant_id`` to the recipe row ID by inspecting
    the existing MO. If the same variant appears in multiple recipe rows
    on this MO the tool errors and asks the operator to use
    ``modify_manufacturing_order`` directly.
    """

    model_config = ConfigDict(extra="forbid")

    old_variant_id: int = Field(
        ..., description="Variant currently on the recipe row to be edited."
    )
    new_variant_id: int | None = Field(
        default=None,
        description="New variant for the row. None = keep the existing variant.",
    )
    planned_quantity_per_unit: float | None = Field(
        default=None,
        gt=0,
        description="New per-unit quantity. None = keep the existing quantity.",
    )


class CorrectManufacturingOrderRequest(ConfirmableRequest):
    """Reopen a closed MO, edit ingredients, restore the original close-state.

    Entry condition: the MO must be in ``DONE`` or ``PARTIALLY_COMPLETED``
    status. For MOs that haven't shipped yet, use
    ``modify_manufacturing_order`` directly — there's no close-state to
    preserve.
    """

    id: int = Field(..., description="Manufacturing order ID")
    ingredient_changes: list[MOIngredientCorrection] = Field(
        ...,
        min_length=1,
        description=(
            "Recipe-row edits keyed by current variant. At least one entry "
            "is required; each must change at least one of new_variant_id "
            "or planned_quantity_per_unit."
        ),
    )


def _resolve_recipe_row(
    mo_id: int,
    recipe_rows: list[ManufacturingOrderRecipeRow],
    correction: MOIngredientCorrection,
) -> ManufacturingOrderRecipeRow:
    """Find the recipe row matching the correction's ``old_variant_id``.

    Errors on zero or multiple matches — the corrections tool is for
    unambiguous swaps; ambiguous cases route to ``modify_manufacturing_order``.
    """
    matches = [
        row
        for row in recipe_rows
        if unwrap_unset(row.variant_id, None) == correction.old_variant_id
    ]
    if not matches:
        raise ValueError(
            f"No recipe row on MO {mo_id} has variant_id "
            f"{correction.old_variant_id}. Use modify_manufacturing_order "
            "if you need to add the ingredient instead."
        )
    if len(matches) > 1:
        row_ids = [m.id for m in matches]
        raise ValueError(
            f"Variant {correction.old_variant_id} appears in multiple "
            f"recipe rows on MO {mo_id} (rows {row_ids}); "
            "correct_manufacturing_order can't disambiguate. Use "
            "modify_manufacturing_order with the explicit row ID."
        )
    return matches[0]


async def _fetch_mo_recipe_rows_raw(
    services: Any, mo_id: int
) -> list[ManufacturingOrderRecipeRow]:
    """Fetch raw attrs recipe rows for an MO.

    Distinct from :func:`foundation.manufacturing_orders._fetch_mo_recipe_rows`
    which returns SKU-enriched ``RecipeRowInfo`` for the read tool. Here we
    need the raw entity for diff and ID resolution.
    """
    from katana_public_api_client.api.manufacturing_order_recipe import (
        get_all_manufacturing_order_recipe_rows,
    )
    from katana_public_api_client.utils import unwrap_data

    response = await get_all_manufacturing_order_recipe_rows.asyncio_detailed(
        client=services.client,
        manufacturing_order_id=mo_id,
        limit=250,
    )
    return cast(list[ManufacturingOrderRecipeRow], unwrap_data(response, default=[]))


async def _fetch_mo_productions_raw(
    services: Any, mo_id: int
) -> list[ManufacturingOrderProduction]:
    """Fetch raw attrs productions for an MO."""
    from katana_public_api_client.api.manufacturing_order import (
        get_all_manufacturing_order_productions,
    )
    from katana_public_api_client.utils import unwrap_data

    response = await get_all_manufacturing_order_productions.asyncio_detailed(
        client=services.client,
        manufacturing_order_ids=[mo_id],
        limit=250,
    )
    return cast(list[ManufacturingOrderProduction], unwrap_data(response, default=[]))


def _build_revert_mo_action(mo_id: int, services: Any) -> ActionSpec:
    """PATCH MO header → status: IN_PROGRESS. Auto-reverses productions."""
    body = APIUpdateManufacturingOrderRequest(
        status=ManufacturingOrderStatus(MO_REOPEN_STATUS)
    )
    return ActionSpec(
        operation=MOOperation.UPDATE_HEADER,
        target_id=mo_id,
        diff=[FieldChange(field="status", old="DONE", new=MO_REOPEN_STATUS)],
        apply=_make_tolerant_patch_apply(
            api_update_manufacturing_order, services, mo_id, body
        ),
        verify=None,
    )


def _build_recipe_edit_actions(
    mo_id: int,
    recipe_rows: list[ManufacturingOrderRecipeRow],
    corrections: list[MOIngredientCorrection],
    services: Any,
) -> list[ActionSpec]:
    specs: list[ActionSpec] = []
    for correction in corrections:
        if (
            correction.new_variant_id is None
            and correction.planned_quantity_per_unit is None
        ):
            raise ValueError(
                f"ingredient_changes entry for variant "
                f"{correction.old_variant_id}: must supply at least one of "
                "new_variant_id or planned_quantity_per_unit."
            )
        row = _resolve_recipe_row(mo_id, recipe_rows, correction)

        diff: list[FieldChange] = []
        if correction.new_variant_id is not None:
            diff.append(
                FieldChange(
                    field="variant_id",
                    old=correction.old_variant_id,
                    new=correction.new_variant_id,
                )
            )
        if correction.planned_quantity_per_unit is not None:
            diff.append(
                FieldChange(
                    field="planned_quantity_per_unit",
                    old=unwrap_unset(row.planned_quantity_per_unit, None),
                    new=correction.planned_quantity_per_unit,
                )
            )

        body = APIUpdateMORecipeRowRequest(
            variant_id=to_unset(correction.new_variant_id),
            planned_quantity_per_unit=to_unset(correction.planned_quantity_per_unit),
        )
        specs.append(
            ActionSpec(
                operation=MOOperation.UPDATE_RECIPE_ROW,
                target_id=row.id,
                diff=diff,
                apply=_make_tolerant_patch_apply(
                    api_update_mo_recipe_row, services, row.id, body
                ),
                verify=None,
            )
        )
    return specs


def _build_recreate_production_action(
    mo_id: int,
    snapshot: MOProductionSnapshot,
    services: Any,
) -> ActionSpec:
    """POST a new production matching the snapshot, then immediately PATCH
    its ``production_date`` to backdate it.

    Two API calls fused into one ``ActionSpec``: the POST stamps the
    production with server-time (Katana ignores ``completed_date`` on the
    create body for the close-state-restore path), the follow-up PATCH
    backdates ``production_date`` to match the snapshot. Operator-proven
    sequence from the originating Shopify SP73000→SP73001 correction.
    Fusion lets the apply phase stay flat — no inter-action data flow
    needed for the captured-then-patched ID.
    """
    create_body = APICreateMOProductionRequest(
        manufacturing_order_id=mo_id,
        completed_quantity=snapshot.completed_quantity,
        serial_numbers=to_unset(
            list(snapshot.serial_numbers) if snapshot.serial_numbers else None
        ),
    )

    async def apply() -> ManufacturingOrderProduction:
        create_resp = await api_create_mo_production.asyncio_detailed(
            client=services.client, body=create_body
        )
        new_prod = cast(
            ManufacturingOrderProduction,
            unwrap_as(create_resp, ManufacturingOrderProduction),
        )
        if snapshot.production_date is not None:
            patch_body = APIUpdateMOProductionRequest(
                production_date=snapshot.production_date
            )
            patch_resp = await api_update_mo_production.asyncio_detailed(
                id=new_prod.id, client=services.client, body=patch_body
            )
            if not is_success(patch_resp):
                unwrap(patch_resp)
        return new_prod

    diff: list[FieldChange] = [
        FieldChange(
            field="completed_quantity",
            new=snapshot.completed_quantity,
            is_added=True,
        )
    ]
    if snapshot.serial_numbers:
        diff.append(
            FieldChange(
                field="serial_numbers",
                new=list(snapshot.serial_numbers),
                is_added=True,
            )
        )
    if snapshot.production_date is not None:
        diff.append(
            FieldChange(
                field="production_date",
                new=snapshot.production_date.isoformat(),
                is_added=True,
            )
        )
    return ActionSpec(
        operation=MOOperation.ADD_PRODUCTION,
        target_id=None,
        diff=diff,
        apply=apply,
        verify=None,
    )


def _build_close_mo_actions(
    mo_id: int, snapshot: MOCloseState, services: Any
) -> list[ActionSpec]:
    """Restore the MO close-state: status first, then ``done_date``.

    Two PATCHes — Katana validates ``done_date`` against the *current*
    status, so the date assignment can only land after the status patch
    completes. Restores to the snapshot's original status (DONE or
    PARTIALLY_COMPLETED), not a hardcoded value, so a PARTIALLY_COMPLETED
    MO isn't silently promoted to DONE on re-close. ``done_date`` is only
    patched when the snapshot was DONE *and* carried a date — for the
    PARTIALLY_COMPLETED path the displayed close timestamp is derived from
    the latest production_date, which the recreate phase already restored.
    """
    target_status = snapshot.status or MO_RESTORE_STATUS
    status_body = APIUpdateManufacturingOrderRequest(
        status=ManufacturingOrderStatus(target_status)
    )
    actions: list[ActionSpec] = [
        ActionSpec(
            operation=MOOperation.UPDATE_HEADER,
            target_id=mo_id,
            diff=[FieldChange(field="status", new=target_status)],
            apply=_make_tolerant_patch_apply(
                api_update_manufacturing_order, services, mo_id, status_body
            ),
            verify=None,
        )
    ]
    if (
        snapshot.status == ManufacturingOrderStatus.DONE.value
        and snapshot.done_date is not None
    ):
        date_body = APIUpdateManufacturingOrderRequest(done_date=snapshot.done_date)
        actions.append(
            ActionSpec(
                operation=MOOperation.UPDATE_HEADER,
                target_id=mo_id,
                diff=[
                    FieldChange(
                        field="done_date",
                        new=snapshot.done_date.isoformat(),
                        is_added=True,
                    )
                ],
                apply=_make_tolerant_patch_apply(
                    api_update_manufacturing_order, services, mo_id, date_body
                ),
                verify=None,
            )
        )
    return actions


async def _correct_manufacturing_order_impl(
    request: CorrectManufacturingOrderRequest, context: Context
) -> ModificationResponse:
    services = get_services(context)
    katana_url = katana_web_url("manufacturing_order", request.id)

    # The three fetches are independent — gather to halve wall-clock latency.
    # Validation runs after; on a missing MO the children fetches were cheap.
    existing_mo, recipe_rows, productions = await asyncio.gather(
        _fetch_manufacturing_order_attrs(services, request.id),
        _fetch_mo_recipe_rows_raw(services, request.id),
        _fetch_mo_productions_raw(services, request.id),
    )
    if existing_mo is None:
        raise ValueError(
            f"Could not fetch manufacturing order {request.id}; "
            "verify it exists before applying corrections."
        )
    status_enum = unwrap_unset(existing_mo.status, None)
    status = status_enum.value if status_enum is not None else ""
    if status not in MO_CLOSED_STATUSES:
        raise ValueError(
            f"correct_manufacturing_order requires the MO to be in DONE or "
            f"PARTIALLY_COMPLETED status; MO {request.id} is in status "
            f"'{status}'. Use modify_manufacturing_order directly for an "
            "open MO — there's no close-state to preserve."
        )

    snapshot = snapshot_mo_close_state(existing_mo, productions)

    # Phases for the apply path (preview flattens them into one action list).
    # Each phase depends on the previous landing successfully — Katana isn't
    # transactional across endpoints, so the helper fail-fasts at boundaries.
    revert_phase = [_build_revert_mo_action(request.id, services)]
    edit_phase = _build_recipe_edit_actions(
        request.id, recipe_rows, request.ingredient_changes, services
    )
    recreate_phase = [
        _build_recreate_production_action(request.id, ps, services)
        for ps in snapshot.productions
    ]
    close_phase = _build_close_mo_actions(request.id, snapshot, services)
    phases = [revert_phase, edit_phase, recreate_phase, close_phase]

    if request.preview:
        full_plan = [action for phase in phases for action in phase]
        return ModificationResponse(
            entity_type="manufacturing_order",
            entity_id=request.id,
            is_preview=True,
            actions=plan_to_preview_results(full_plan),
            warnings=_close_state_warnings_mo(snapshot),
            next_actions=[
                f"Review {len(full_plan)} planned action(s) for MO {request.id}",
                f"Captured close-state: status={snapshot.status}, "
                f"done_date={snapshot.done_date}, "
                f"productions={len(snapshot.productions)}",
                "Set preview=false to execute the plan",
            ],
            katana_url=katana_url,
            message=(
                f"Preview: reopen → edit → restore for "
                f"manufacturing order {request.id} "
                f"({len(full_plan)} action(s))"
            ),
        )

    prior_state = _augment_prior_state_with_snapshot(
        serialize_for_prior_state(existing_mo), snapshot
    )
    aggregated, failed = await _run_phases_until_failure(phases)
    if failed:
        return _build_failure_response(
            request.id, aggregated, prior_state, katana_url, snapshot
        )
    return _build_success_response(
        request.id, aggregated, prior_state, katana_url, snapshot
    )


def _close_state_warnings_mo(snapshot: MOCloseState) -> list[str]:
    if not snapshot.productions:
        return [
            "No productions captured on this MO — the restore step will only "
            "set status: DONE without re-recording any output. Verify this "
            "matches reality before applying."
        ]
    missing_dates = sum(1 for p in snapshot.productions if p.production_date is None)
    if missing_dates:
        return [
            f"{missing_dates} production(s) have no production_date in the "
            "snapshot; their re-creations will land at server-time. "
            "Other productions will be backdated to their original timestamps."
        ]
    return []


def _build_success_response(
    mo_id: int,
    actions: list[ActionResult],
    prior_state: dict[str, Any] | None,
    katana_url: str | None,
    snapshot: MOCloseState,
) -> ModificationResponse:
    return ModificationResponse(
        entity_type="manufacturing_order",
        entity_id=mo_id,
        is_preview=False,
        actions=actions,
        prior_state=prior_state,
        warnings=_close_state_warnings_mo(snapshot),
        next_actions=[
            f"Manufacturing order {mo_id} corrected — "
            f"{sum(1 for a in actions if a.succeeded)} action(s) applied",
            f"Close-state restored: status={snapshot.status}, "
            f"done_date={snapshot.done_date}, "
            f"productions={len(snapshot.productions)}",
        ],
        katana_url=katana_url,
        message=(
            f"Successfully corrected manufacturing order {mo_id} "
            f"({sum(1 for a in actions if a.succeeded)}/{len(actions)} "
            "actions applied)"
        ),
    )


def _build_failure_response(
    entity_id: int,
    actions: list[ActionResult],
    prior_state: dict[str, Any] | None,
    katana_url: str | None,
    snapshot: MOCloseState | SOCloseState,
) -> ModificationResponse:
    succeeded = sum(1 for a in actions if a.succeeded is True)
    failed = sum(1 for a in actions if a.succeeded is False)
    return ModificationResponse(
        entity_type=(
            "manufacturing_order"
            if isinstance(snapshot, MOCloseState)
            else "sales_order"
        ),
        entity_id=entity_id,
        is_preview=False,
        actions=actions,
        prior_state=prior_state,
        warnings=[
            "Correction halted mid-flow; the record is left in an "
            "intermediate (open) state. The captured close-state is in "
            "``prior_state`` — manually replay the remaining steps via "
            "modify_<entity> if you want to recover.",
        ],
        next_actions=[
            f"{succeeded} action(s) succeeded; {failed} failed",
            "Review the FAILED action's error",
            "Use prior_state + the captured close-state snapshot to "
            "reconstruct the missing steps",
        ],
        katana_url=katana_url,
        message=(
            f"Partial: {succeeded}/{len(actions)} action(s) applied to "
            f"entity {entity_id} before fail-fast halt"
        ),
    )


@observe_tool
@unpack_pydantic_params
async def correct_manufacturing_order(
    request: Annotated[CorrectManufacturingOrderRequest, Unpack()],
    context: Context,
) -> ToolResult:
    """Edit a closed MO without losing its original close-state.

    Reopens the MO, swaps ingredient(s) keyed by current variant, then
    re-closes preserving the original status, ``done_date``, and per-
    production ``production_date`` and serial numbers. Use this instead of
    ``modify_manufacturing_order`` when the MO is already DONE or
    PARTIALLY_COMPLETED and you need to fix what was actually consumed.

    Sequence:

    1. Capture close-state (status + done_date + per-production
       quantity/date/serial_numbers).
    2. PATCH status: IN_PROGRESS (Katana auto-reverses productions).
    3. PATCH each recipe row per ``ingredient_changes``.
    4. POST one production per snapshot, replaying quantity + serial_numbers.
    5. PATCH each new production's ``production_date`` to the snapshot value.
    6. PATCH status: DONE.

    Each ``ingredient_changes`` entry is keyed by ``old_variant_id``
    (looked up in the existing recipe rows). Errors if the variant isn't
    present, or appears more than once on this MO — use
    ``modify_manufacturing_order`` with the explicit row ID to disambiguate.

    Two-step flow: ``preview=true`` (default) returns the full action plan
    (revert + edits + recreate + close); ``preview=false`` runs the plan
    in phases and aggregates results. Fail-fast halt at any phase boundary
    leaves the MO in an intermediate state with a breadcrumb in
    ``prior_state``.
    """
    response = await _correct_manufacturing_order_impl(request, context)
    return to_tool_result(response)


# ============================================================================
# Sales-order corrections
# ============================================================================


class SOLineCorrection(BaseModel):
    """One SO line edit, identified by the variant currently on the row.

    Tool resolves ``old_variant_id`` to the row ID by inspecting the
    existing SO. Errors if the variant isn't present or appears more
    than once.

    Note: ``correct_sales_order`` only updates existing rows in place; it
    does not delete or add rows. This keeps the row IDs stable so the
    re-created fulfillments can reference them by the original
    ``sales_order_row_id``.
    """

    model_config = ConfigDict(extra="forbid")

    old_variant_id: int = Field(
        ..., description="Variant currently on the row to be edited."
    )
    new_variant_id: int | None = Field(
        default=None,
        description="New variant for the row. None = keep the existing variant.",
    )
    quantity: float | None = Field(
        default=None,
        gt=0,
        description=(
            "New quantity. None = keep the existing quantity. Must be >= "
            "the original fulfillment quantity for this row, or Katana will "
            "reject the re-fulfillment step."
        ),
    )
    price_per_unit: float | None = Field(
        default=None,
        description="New unit price. None = keep the existing price.",
    )


class CorrectSalesOrderRequest(ConfirmableRequest):
    """Reopen a closed SO, edit line items, restore the original close-state.

    Entry condition: the SO must be in ``DELIVERED`` status. For SOs that
    haven't shipped yet, use ``modify_sales_order`` directly.
    """

    id: int = Field(..., description="Sales order ID")
    line_changes: list[SOLineCorrection] = Field(
        ...,
        min_length=1,
        description=(
            "Line-item edits keyed by current variant. At least one entry "
            "is required; each must change at least one of new_variant_id, "
            "quantity, or price_per_unit."
        ),
    )


def _resolve_so_row(
    so_id: int, rows: list[SalesOrderRow], correction: SOLineCorrection
) -> SalesOrderRow:
    matches = [
        r for r in rows if unwrap_unset(r.variant_id, None) == correction.old_variant_id
    ]
    if not matches:
        raise ValueError(
            f"No row on SO {so_id} has variant_id {correction.old_variant_id}."
        )
    if len(matches) > 1:
        row_ids = [m.id for m in matches]
        raise ValueError(
            f"Variant {correction.old_variant_id} appears in multiple rows "
            f"on SO {so_id} (rows {row_ids}); correct_sales_order can't "
            "disambiguate. Use modify_sales_order with the explicit row ID."
        )
    return matches[0]


def _check_quantity_covers_fulfillments(
    so_id: int,
    snapshot: SOCloseState,
    rows: list[SalesOrderRow],
    corrections: list[SOLineCorrection],
) -> None:
    """Preflight: refuse if any line drops below the row's already-fulfilled qty.

    The re-fulfillment phase replays the original fulfillment quantities; if
    a row's new quantity is less than what was previously fulfilled, Katana
    rejects the POST and we'd halt mid-flow with the SO already reverted +
    fulfillments already deleted. Catching it here keeps the failure clean —
    no mutations applied yet.
    """
    fulfilled_per_row: dict[int, float] = {}
    for ful in snapshot.fulfillments:
        for r in ful.rows:
            fulfilled_per_row[r.sales_order_row_id] = (
                fulfilled_per_row.get(r.sales_order_row_id, 0.0) + r.quantity
            )

    for correction in corrections:
        if correction.quantity is None:
            continue
        try:
            row = _resolve_so_row(so_id, rows, correction)
        except ValueError:
            # Resolution errors surface during plan-build; skip here so the
            # original error message wins.
            continue
        already_fulfilled = fulfilled_per_row.get(row.id, 0.0)
        if correction.quantity < already_fulfilled:
            raise ValueError(
                f"line_changes for variant {correction.old_variant_id} on SO "
                f"{so_id} drops quantity to {correction.quantity}, but "
                f"{already_fulfilled} was already fulfilled on this row. "
                "Refusing — the re-fulfillment phase would fail and leave "
                "the SO in an intermediate (open) state."
            )


async def _fetch_so_fulfillments(
    services: Any, so_id: int
) -> list[SalesOrderFulfillment]:
    """Fetch all fulfillments for an SO."""
    from katana_public_api_client.utils import unwrap_data

    response = await api_get_all_so_fulfillments.asyncio_detailed(
        client=services.client,
        sales_order_id=so_id,
        limit=250,
    )
    return cast(list[SalesOrderFulfillment], unwrap_data(response, default=[]))


def _build_delete_fulfillment_action(fulfillment_id: int, services: Any) -> ActionSpec:
    async def apply() -> None:
        response = await api_delete_so_fulfillment.asyncio_detailed(
            id=fulfillment_id, client=services.client
        )
        if not is_success(response):
            unwrap(response)
        return None

    return ActionSpec(
        operation=SOOperation.DELETE_FULFILLMENT,
        target_id=fulfillment_id,
        diff=[],
        apply=apply,
        verify=None,
    )


def _build_revert_so_action(so_id: int, services: Any) -> ActionSpec:
    body = APIUpdateSalesOrderRequest(status=UpdateSalesOrderStatus(SO_REOPEN_STATUS))
    return ActionSpec(
        operation=SOOperation.UPDATE_HEADER,
        target_id=so_id,
        diff=[FieldChange(field="status", old=SO_RESTORE_STATUS, new=SO_REOPEN_STATUS)],
        apply=_make_tolerant_patch_apply(api_update_sales_order, services, so_id, body),
        verify=None,
    )


def _build_so_row_edit_actions(
    so_id: int,
    rows: list[SalesOrderRow],
    corrections: list[SOLineCorrection],
    services: Any,
) -> list[ActionSpec]:
    specs: list[ActionSpec] = []
    for correction in corrections:
        if (
            correction.new_variant_id is None
            and correction.quantity is None
            and correction.price_per_unit is None
        ):
            raise ValueError(
                f"line_changes entry for variant {correction.old_variant_id}: "
                "must supply at least one of new_variant_id, quantity, or "
                "price_per_unit."
            )
        row = _resolve_so_row(so_id, rows, correction)

        diff: list[FieldChange] = []
        if correction.new_variant_id is not None:
            diff.append(
                FieldChange(
                    field="variant_id",
                    old=correction.old_variant_id,
                    new=correction.new_variant_id,
                )
            )
        if correction.quantity is not None:
            diff.append(
                FieldChange(
                    field="quantity",
                    old=unwrap_unset(row.quantity, None),
                    new=correction.quantity,
                )
            )
        if correction.price_per_unit is not None:
            diff.append(
                FieldChange(
                    field="price_per_unit",
                    old=unwrap_unset(row.price_per_unit, None),
                    new=correction.price_per_unit,
                )
            )

        body = APIUpdateSORowRequest(
            variant_id=to_unset(correction.new_variant_id),
            quantity=to_unset(correction.quantity),
            price_per_unit=to_unset(correction.price_per_unit),
        )
        specs.append(
            ActionSpec(
                operation=SOOperation.UPDATE_ROW,
                target_id=row.id,
                diff=diff,
                apply=_make_tolerant_patch_apply(
                    api_update_so_row, services, row.id, body
                ),
                verify=None,
            )
        )
    return specs


def _build_recreate_fulfillment_action(
    so_id: int,
    snapshot: SOFulfillmentSnapshot,
    services: Any,
) -> ActionSpec:
    rows = [
        SalesOrderFulfillmentRowRequest(
            sales_order_row_id=row.sales_order_row_id, quantity=row.quantity
        )
        for row in snapshot.rows
    ]
    body = APICreateSOFulfillmentRequest(
        sales_order_id=so_id,
        sales_order_fulfillment_rows=rows,
        status=SalesOrderFulfillmentStatus(snapshot.status or SO_RESTORE_STATUS),
        picked_date=to_unset(snapshot.picked_date),
        conversion_rate=to_unset(snapshot.conversion_rate),
        conversion_date=to_unset(snapshot.conversion_date),
        tracking_number=to_unset(snapshot.tracking_number),
        tracking_url=to_unset(snapshot.tracking_url),
        tracking_carrier=to_unset(snapshot.tracking_carrier),
        tracking_method=to_unset(snapshot.tracking_method),
    )

    async def apply() -> SalesOrderFulfillment:
        response = await api_create_so_fulfillment.asyncio_detailed(
            client=services.client, body=body
        )
        return cast(SalesOrderFulfillment, unwrap_as(response, SalesOrderFulfillment))

    diff: list[FieldChange] = [
        FieldChange(field="status", new=snapshot.status, is_added=True),
        FieldChange(
            field="rows",
            new=[
                {"sales_order_row_id": r.sales_order_row_id, "quantity": r.quantity}
                for r in snapshot.rows
            ],
            is_added=True,
        ),
    ]
    if snapshot.picked_date is not None:
        diff.append(
            FieldChange(
                field="picked_date",
                new=snapshot.picked_date.isoformat(),
                is_added=True,
            )
        )
    return ActionSpec(
        operation=SOOperation.ADD_FULFILLMENT,
        target_id=None,
        diff=diff,
        apply=apply,
        verify=None,
    )


def _build_close_so_action(so_id: int, services: Any) -> ActionSpec:
    body = APIUpdateSalesOrderRequest(status=UpdateSalesOrderStatus(SO_RESTORE_STATUS))
    return ActionSpec(
        operation=SOOperation.UPDATE_HEADER,
        target_id=so_id,
        diff=[FieldChange(field="status", new=SO_RESTORE_STATUS)],
        apply=_make_tolerant_patch_apply(api_update_sales_order, services, so_id, body),
        verify=None,
    )


async def _correct_sales_order_impl(
    request: CorrectSalesOrderRequest, context: Context
) -> ModificationResponse:
    services = get_services(context)
    katana_url = katana_web_url("sales_order", request.id)

    existing_so, fulfillments = await asyncio.gather(
        _fetch_sales_order_attrs(services, request.id),
        _fetch_so_fulfillments(services, request.id),
    )
    if existing_so is None:
        raise ValueError(f"Could not fetch sales order {request.id}; verify it exists.")
    status_enum = unwrap_unset(existing_so.status, None)
    status = status_enum.value if status_enum is not None else ""
    if status not in SO_CLOSED_STATUSES:
        raise ValueError(
            f"correct_sales_order requires the SO to be in DELIVERED status; "
            f"SO {request.id} is in status '{status}'. Use modify_sales_order "
            "directly for an open SO — there's no close-state to preserve."
        )

    rows = [
        r
        for r in (unwrap_unset(existing_so.sales_order_rows, []) or [])
        if r is not None
    ]
    snapshot = snapshot_so_close_state(existing_so, fulfillments)
    _check_quantity_covers_fulfillments(
        request.id, snapshot, rows, request.line_changes
    )

    delete_phase = [
        _build_delete_fulfillment_action(fid, services)
        for fid in snapshot.fulfillment_ids
    ]
    revert_phase = [_build_revert_so_action(request.id, services)]
    edit_phase = _build_so_row_edit_actions(
        request.id, rows, request.line_changes, services
    )
    recreate_phase = [
        _build_recreate_fulfillment_action(request.id, fs, services)
        for fs in snapshot.fulfillments
    ]
    close_phase = [_build_close_so_action(request.id, services)]
    phases = [delete_phase, revert_phase, edit_phase, recreate_phase, close_phase]

    if request.preview:
        full_plan = [action for phase in phases for action in phase]
        return ModificationResponse(
            entity_type="sales_order",
            entity_id=request.id,
            is_preview=True,
            actions=plan_to_preview_results(full_plan),
            warnings=_close_state_warnings_so(snapshot),
            next_actions=[
                f"Review {len(full_plan)} planned action(s) for SO {request.id}",
                f"Captured close-state: status={snapshot.status}, "
                f"picked_date={snapshot.picked_date}, "
                f"fulfillments={len(snapshot.fulfillments)}",
                "Set preview=false to execute the plan",
            ],
            katana_url=katana_url,
            message=(
                f"Preview: reopen → edit → restore for sales order "
                f"{request.id} ({len(full_plan)} action(s))"
            ),
        )

    prior_state = _augment_prior_state_with_snapshot(
        serialize_for_prior_state(existing_so), snapshot
    )
    aggregated, failed = await _run_phases_until_failure(phases)
    if failed:
        return _build_failure_response(
            request.id, aggregated, prior_state, katana_url, snapshot
        )

    return ModificationResponse(
        entity_type="sales_order",
        entity_id=request.id,
        is_preview=False,
        actions=aggregated,
        prior_state=prior_state,
        warnings=_close_state_warnings_so(snapshot),
        next_actions=[
            f"Sales order {request.id} corrected — "
            f"{sum(1 for a in aggregated if a.succeeded)} action(s) applied",
            f"Close-state restored: status={snapshot.status}, "
            f"picked_date={snapshot.picked_date}, "
            f"fulfillments={len(snapshot.fulfillments)}",
        ],
        katana_url=katana_url,
        message=(
            f"Successfully corrected sales order {request.id} "
            f"({sum(1 for a in aggregated if a.succeeded)}/"
            f"{len(aggregated)} actions applied)"
        ),
    )


def _close_state_warnings_so(snapshot: SOCloseState) -> list[str]:
    if not snapshot.fulfillments:
        return [
            "No fulfillments captured on this SO — the restore step will only "
            "set status: DELIVERED without re-creating any fulfillment. "
            "Verify this matches reality before applying."
        ]
    return []


@observe_tool
@unpack_pydantic_params
async def correct_sales_order(
    request: Annotated[CorrectSalesOrderRequest, Unpack()], context: Context
) -> ToolResult:
    """Edit a closed (DELIVERED) SO without losing its picked_date and
    fulfillment metadata.

    Reopens the SO, edits line items keyed by current variant, then
    re-closes preserving the original status, ``picked_date``, and per-
    fulfillment metadata (status, picked_date, tracking_*).

    Sequence:

    1. Capture close-state (status + picked_date + per-fulfillment
       snapshots).
    2. DELETE each fulfillment (Katana returns an empty 200 body — the
       tolerant patch handler treats this as success).
    3. PATCH SO status: PENDING.
    4. PATCH each row per ``line_changes``.
    5. POST one fulfillment per snapshot, replaying status + tracking_* +
       row references.
    6. PATCH SO status: DELIVERED.

    Each ``line_changes`` entry is keyed by ``old_variant_id`` (looked up
    in the existing SO rows). Errors if the variant isn't present or
    appears more than once on this SO — use ``modify_sales_order`` with
    the explicit row ID to disambiguate.

    The tool only updates rows in place; it does not delete or add rows.
    Row IDs must stay stable so the re-created fulfillments can reference
    them by the original ``sales_order_row_id``. If you need to add or
    remove a line, use ``modify_sales_order``.

    Two-step flow: ``preview=true`` (default) returns the full action plan;
    ``preview=false`` runs the plan in phases. Fail-fast halt leaves the
    SO in an intermediate state with a breadcrumb in ``prior_state``.
    """
    response = await _correct_sales_order_impl(request, context)
    return to_tool_result(response)


# ============================================================================
# Registration
# ============================================================================


def register_tools(mcp: FastMCP) -> None:
    """Register correction tools with the FastMCP instance."""
    from mcp.types import ToolAnnotations

    _update = ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    )

    mcp.tool(
        tags={"orders", "manufacturing", "write", "correction"},
        annotations=_update,
    )(correct_manufacturing_order)
    mcp.tool(
        tags={"orders", "sales", "write", "correction"},
        annotations=_update,
    )(correct_sales_order)
