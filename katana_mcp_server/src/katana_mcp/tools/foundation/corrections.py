"""Composite ``correct_<entity>`` tools — transactional edit on closed records.

Lets the operator edit a record that has already reached a terminal status
(``DONE`` for an MO, ``DELIVERED`` for an SO, ``RECEIVED`` /
``PARTIALLY_RECEIVED`` for a PO) without losing the original close-state
metadata. Internally implements the proven sequence:

1. **Capture** the close-state (status + key timestamps + child snapshots)
2. **Reopen** by reverting status to an editable value (and, for SO,
   deleting fulfillments first — the close-state restore re-creates them)
3. **Apply** the user's edits (recipe row swap, line item update, PO row
   variant/quantity/price)
4. **Restore** the close-state. For MO this is status → DONE then
   ``done_date`` (Katana validates date fields against the *current*
   status, so combined ``status: DONE + done_date`` calls fail). For SO
   this is re-create fulfillments → status → DELIVERED. For PO this is a
   single ``POST /purchase_order_receive`` per captured receipt group — the
   receive endpoint promotes status back to RECEIVED automatically.

Composes ``ActionSpec`` lists from :mod:`_modification_dispatch` and the
existing per-entity request builders. Each phase runs through
``execute_plan`` separately so fail-fast halts at a phase boundary with the
captured close-state available for manual recovery.

Tracked under #523 (umbrella). MO + SO shipped in #536 / #546; PO ships
under #532. Stock transfer remains deferred — its model has no close-state
worth preserving (see help.py's "Closed-Record Corrections" section).
"""

from __future__ import annotations

import asyncio
import dataclasses
from dataclasses import dataclass
from datetime import UTC, datetime
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
    PO_CLOSED_STATUSES,
    PO_REOPEN_STATUS,
    SO_CLOSED_STATUSES,
    SO_REOPEN_STATUS,
    SO_RESTORE_STATUS,
    MOCloseState,
    MOProductionSnapshot,
    POCloseState,
    POCostRowSnapshot,
    POReceiptGroup,
    PORowSnapshot,
    SOCloseState,
    SOFulfillmentSnapshot,
    snapshot_mo_close_state,
    snapshot_po_close_state,
    snapshot_so_close_state,
)
from katana_mcp.tools.foundation.manufacturing_orders import (
    MOOperation,
    _fetch_manufacturing_order_attrs,
)
from katana_mcp.tools.foundation.purchase_orders import (
    POOperation,
    _fetch_purchase_order_attrs,
)
from katana_mcp.tools.foundation.sales_orders import (
    SOOperation,
    _fetch_sales_order_attrs,
)
from katana_mcp.tools.tool_result_utils import UI_META
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
from katana_public_api_client.api.purchase_order import (
    receive_purchase_order as api_receive_purchase_order,
    update_purchase_order as api_update_purchase_order,
)
from katana_public_api_client.api.purchase_order_additional_cost_row import (
    create_po_additional_cost_row as api_create_po_cost_row,
    delete_po_additional_cost as api_delete_po_cost_row,
    get_po_additional_cost_row as api_get_po_cost_row,
    get_purchase_order_additional_cost_rows as api_get_po_cost_rows,
)
from katana_public_api_client.api.purchase_order_row import (
    create_purchase_order_row as api_create_purchase_order_row,
    update_purchase_order_row as api_update_purchase_order_row,
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
    CostDistributionMethod,
    CreateManufacturingOrderProductionRequest as APICreateMOProductionRequest,
    CreatePurchaseOrderAdditionalCostRowRequest as APICreatePOCostRowRequest,
    CreatePurchaseOrderRowRequest as APICreatePORowRequest,
    CreateSalesOrderFulfillmentRequest as APICreateSOFulfillmentRequest,
    ManufacturingOrderProduction,
    ManufacturingOrderRecipeRow,
    ManufacturingOrderStatus,
    PurchaseOrderAdditionalCostRow,
    PurchaseOrderReceiveRow,
    PurchaseOrderReceiveRowBatchTransactionsItem,
    PurchaseOrderRow,
    PurchaseOrderStatus,
    SalesOrderFulfillment,
    SalesOrderFulfillmentRowRequest,
    SalesOrderFulfillmentStatus,
    SalesOrderRow,
    UpdateManufacturingOrderProductionRequest as APIUpdateMOProductionRequest,
    UpdateManufacturingOrderRecipeRowRequest as APIUpdateMORecipeRowRequest,
    UpdateManufacturingOrderRequest as APIUpdateManufacturingOrderRequest,
    UpdatePurchaseOrderRequest as APIUpdatePurchaseOrderRequest,
    UpdatePurchaseOrderRowRequest as APIUpdatePORowRequest,
    UpdateSalesOrderRequest as APIUpdateSalesOrderRequest,
    UpdateSalesOrderRowRequest as APIUpdateSORowRequest,
    UpdateSalesOrderStatus,
)
from katana_public_api_client.utils import (
    APIError,
    is_success,
    unwrap,
    unwrap_as,
    unwrap_data,
)

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
    snapshot: MOCloseState | SOCloseState | POCloseState,
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
) -> tuple[list[ActionResult], bool, list[ActionSpec]]:
    """Run each phase via :func:`execute_plan`; halt on the first failed action.

    Returns ``(aggregated_results, failed, not_run_specs)`` —
    ``failed=True`` means an action raised in some phase and subsequent
    phases were skipped. ``not_run_specs`` carries every :class:`ActionSpec`
    from the unattempted plan tail (the rest of the current failing phase
    plus every later phase). Callers use the boolean to branch into success
    vs failure response building, and the spec tail to synthesize NOT-RUN
    extras for the per-section row morph in :func:`build_so_modify_ui`
    (#858 finding B; mirrors ``_modify_sales_order_impl``).

    Empty phases are skipped silently.
    """
    aggregated: list[ActionResult] = []
    for phase_idx, phase in enumerate(phases):
        if not phase:
            continue
        phase_results = await execute_plan(phase)
        aggregated.extend(phase_results)
        if any(a.succeeded is False for a in phase_results):
            # Unattempted tail = leftover specs in this phase (after the
            # failing action) + every spec in every later phase. Mirrors
            # ``execute_plan``'s fail-fast contract: it returns results
            # only up through the failed action, so any specs past that
            # index in the phase never ran.
            executed_in_phase = len(phase_results)
            not_run_specs = list(phase[executed_in_phase:])
            for later_phase in phases[phase_idx + 1 :]:
                not_run_specs.extend(later_phase)
            return aggregated, True, not_run_specs
    return aggregated, False, []


def _synthesize_correction_not_run_actions(
    specs: list[ActionSpec],
) -> list[dict[str, Any]]:
    """Build NOT-RUN action dicts for the unattempted phase tail.

    Same shape as :func:`_modify_sales_order_impl`'s NOT-RUN synthesis so
    :func:`build_so_modify_ui` (via :func:`_actions_with_not_run_tail`)
    can merge them into the per-section row morph without distinguishing
    apply-vs-correction provenance. ``succeeded=None`` + ``status_label=
    "NOT RUN"`` sets the "secondary" Badge variant.
    """
    return [
        {
            "operation": spec.operation,
            "target_id": spec.target_id,
            "succeeded": None,
            "error": None,
            "changes": [
                c.model_dump() if hasattr(c, "model_dump") else dict(c)
                for c in spec.diff
            ],
            "status_label": "NOT RUN",
        }
        for spec in specs
    ]


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

    ``include_deleted`` is intentionally **not** passed (#693): the close-
    state snapshot and ``_resolve_recipe_row`` match user-supplied
    ``old_variant_id`` against *live* recipe rows so corrections can PATCH
    them. Surfacing tombstoned rows would let a correction target a
    soft-deleted row that Katana would reject downstream. The cache-merge
    fetcher (``manufacturing_orders._fetch_mo_recipe_row_attrs_for_cache_merge``)
    is the one that does pass ``include_deleted=True`` — it has to see
    tombstones so the merged cache row goes away when Katana hard-deletes
    via the soft-delete flow. The agent-facing read
    (``manufacturing_orders._fetch_mo_recipe_rows``) is also live-only;
    different surfaces, different defaults, same "agents never see
    tombstones" rule.
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
        new_prod = unwrap_as(create_resp, ManufacturingOrderProduction)
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

    # ``prior_state`` populated on BOTH branches: apply path uses it for
    # the revert reference; preview path uses it for renderer-side entity
    # view (#721 modify-card design — without prior_state, the rendered
    # card has only the changed-field diffs and an almost-empty header).
    prior_state = _augment_prior_state_with_snapshot(
        serialize_for_prior_state(existing_mo), snapshot
    )

    if request.preview:
        full_plan = [action for phase in phases for action in phase]
        return ModificationResponse(
            entity_type="manufacturing_order",
            entity_id=request.id,
            is_preview=True,
            actions=plan_to_preview_results(full_plan),
            prior_state=prior_state,
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
    aggregated, failed, _not_run_specs = await _run_phases_until_failure(phases)
    if failed:
        # MO modify card doesn't merge NOT-RUN extras yet — drop the spec
        # tail here. SO failure path below synthesizes them for the SO
        # modify-card morph (#858 finding B).
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


def _entity_type_for_snapshot(
    snapshot: MOCloseState | SOCloseState | POCloseState,
) -> str:
    """Map a close-state dataclass to the canonical entity-type string used
    on :class:`ModificationResponse.entity_type` and the preview/failure
    breadcrumb messaging."""
    if isinstance(snapshot, MOCloseState):
        return "manufacturing_order"
    if isinstance(snapshot, SOCloseState):
        return "sales_order"
    return "purchase_order"


def _build_failure_response(
    entity_id: int,
    actions: list[ActionResult],
    prior_state: dict[str, Any] | None,
    katana_url: str | None,
    snapshot: MOCloseState | SOCloseState | POCloseState,
) -> ModificationResponse:
    succeeded = sum(1 for a in actions if a.succeeded is True)
    failed = sum(1 for a in actions if a.succeeded is False)
    return ModificationResponse(
        entity_type=_entity_type_for_snapshot(snapshot),
        entity_id=entity_id,
        is_preview=False,
        actions=actions,
        prior_state=prior_state,
        warnings=[
            "Correction halted mid-flow; the record is left in an "
            "intermediate (open) state. The captured close-state is in "
            "``prior_state`` — replay the remaining steps with the "
            f"modify_{_entity_type_for_snapshot(snapshot)} tool to recover.",
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
    return to_tool_result(
        response,
        confirm_request=request,
        confirm_tool="correct_manufacturing_order",
    )


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
        return unwrap_as(response, SalesOrderFulfillment)

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

    # See #722 note on the MO correction above — prior_state populated
    # on both branches so the per-entity modify card can render the
    # unchanged-field context around the diff overlay on preview too.
    prior_state = _augment_prior_state_with_snapshot(
        serialize_for_prior_state(existing_so), snapshot
    )

    if request.preview:
        full_plan = [action for phase in phases for action in phase]
        return ModificationResponse(
            entity_type="sales_order",
            entity_id=request.id,
            is_preview=True,
            actions=plan_to_preview_results(full_plan),
            prior_state=prior_state,
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
    aggregated, failed, not_run_specs = await _run_phases_until_failure(phases)
    if failed:
        response = _build_failure_response(
            request.id, aggregated, prior_state, katana_url, snapshot
        )
        # Synthesize NOT-RUN entries for the unattempted plan tail so
        # :func:`build_so_modify_ui` (which handles ``correct_sales_order``
        # alongside ``modify_sales_order``) renders skipped restore /
        # recreate / close phases instead of silently overwriting the
        # preview's full sub-entity rows with only the executed prefix
        # (#858 finding B — Copilot comment 3312071378). Mirrors the
        # equivalent synthesis in ``_modify_sales_order_impl``.
        not_run_actions = _synthesize_correction_not_run_actions(not_run_specs)
        if not_run_actions:
            response.extras["not_run_actions"] = not_run_actions
        return response

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
    return to_tool_result(
        response, confirm_request=request, confirm_tool="correct_sales_order"
    )


# ============================================================================
# Purchase-order corrections
# ============================================================================


class PORowCorrection(BaseModel):
    """One PO row edit, identified by the ID of the row currently on the PO.

    PO corrections key by row ID (the MO/SO siblings key by variant)
    because one variant can sit on several rows of a PO: a partial receipt
    splits a row into a received part and an open remainder. Look up the
    current row IDs with ``get_purchase_order`` first.

    An edit applies to that row only. On a received row, ``quantity`` is
    the corrected received quantity and the row is re-received with it.
    The tool edits rows in place; to add or remove a line use
    ``modify_purchase_order`` after the correction lands.
    """

    model_config = ConfigDict(extra="forbid")

    row_id: int = Field(
        ..., description="Existing row ID on the PO (find via get_purchase_order)."
    )
    new_variant_id: int | None = Field(
        default=None,
        description="New variant for the row. None = keep the existing variant.",
    )
    quantity: float | None = Field(
        default=None,
        gt=0,
        description=(
            "New quantity. None = keep the existing quantity. On a received "
            "row this is the corrected received quantity."
        ),
    )
    price_per_unit: float | None = Field(
        default=None,
        ge=0,
        description="New unit price. None = keep the existing price.",
    )


class CorrectPurchaseOrderRequest(ConfirmableRequest):
    """Reopen a closed PO, edit rows, restore the original close-state.

    Entry condition: the PO must be in ``RECEIVED`` or
    ``PARTIALLY_RECEIVED`` status. For POs that haven't been received yet,
    use ``modify_purchase_order`` directly — there's no close-state to
    preserve.
    """

    id: int = Field(..., description="Purchase order ID")
    row_changes: list[PORowCorrection] = Field(
        ...,
        min_length=1,
        description=(
            "Row edits keyed by row ID. At least one entry is required; "
            "each must change at least one of new_variant_id, quantity, "
            "or price_per_unit."
        ),
    )


# Quantities come back from Katana as floats; sums across merged rows are
# compared with this tolerance rather than ``==``.
_PO_QTY_TOLERANCE = 1e-6


@dataclass(frozen=True)
class _PODesiredRow:
    """A captured row with the operator's corrections applied.

    ``source`` is the row as it stood before the revert; the other fields
    are what the rebuilt row must carry. A received source row is
    re-received with ``quantity`` on its own ``received_date``.
    """

    source: PORowSnapshot
    variant_id: int | None
    quantity: float
    price_per_unit: float | None

    @property
    def changed(self) -> bool:
        return (
            self.variant_id != self.source.variant_id
            or abs(self.quantity - self.source.quantity) > _PO_QTY_TOLERANCE
            or self.price_per_unit != self.source.price_per_unit
        )


@dataclass
class _POCorrectionProgress:
    """Apply-time state shared by the phase closures.

    The rebuild records which physical row stands for each captured row;
    the replay records which receipt groups landed and the group id each
    one got, which the cost-row moves need. The failure response reads it
    to tell the operator exactly what is left to do.
    """

    completion_applied: bool = False
    reverted: bool = False
    rows_rebuilt: bool = False
    physical_row_ids: dict[int, int] = dataclasses.field(default_factory=dict)
    replayed_groups: set[int] = dataclasses.field(default_factory=set)
    new_group_ids: dict[int, int] = dataclasses.field(default_factory=dict)
    # Cost rows whose copy exists on the rebuilt group (original id -> copy id)
    # and those fully moved (copy created and original deleted, or no move
    # needed).
    copied_cost_rows: dict[int, int] = dataclasses.field(default_factory=dict)
    moved_cost_rows: set[int] = dataclasses.field(default_factory=set)
    # True when the failing step may have reached Katana anyway (timeout,
    # connection error, 5xx), so local flags cannot say what was written.
    outcome_unknown: bool = False


def _tracked(progress: _POCorrectionProgress, apply: ApplyCallable) -> ApplyCallable:
    """Wrap an apply so a failure records whether its outcome is known.

    A 4xx rejection or one of our own refusals (``ValueError``) means the
    failing call changed nothing. Anything else (a timeout, a dropped
    connection, a 5xx after the transport's retries) may have landed, so the
    failure response must tell the operator to check the PO first.
    """

    async def wrapped() -> Any:
        try:
            return await apply()
        except ValueError:
            raise
        except APIError as exc:
            if not 400 <= exc.status_code < 500:
                progress.outcome_unknown = True
            raise
        except Exception:
            progress.outcome_unknown = True
            raise

    return wrapped


def _desired_po_rows(
    po_id: int, snapshot: POCloseState, corrections: list[PORowCorrection]
) -> list[_PODesiredRow]:
    """Apply ``corrections`` to the captured rows; refuse unsafe edits.

    Every check here runs before anything is written, so a refusal leaves
    the PO untouched.
    """
    by_row: dict[int, PORowCorrection] = {}
    for correction in corrections:
        if (
            correction.new_variant_id is None
            and correction.quantity is None
            and correction.price_per_unit is None
        ):
            raise ValueError(
                f"row_changes entry for row {correction.row_id}: must "
                "supply at least one of new_variant_id, quantity, or "
                "price_per_unit."
            )
        if snapshot.row(correction.row_id) is None:
            raise ValueError(
                f"No row on PO {po_id} has id {correction.row_id}. Look up "
                "current row IDs with get_purchase_order before retrying."
            )
        if correction.row_id in by_row:
            raise ValueError(
                f"row_changes lists row {correction.row_id} more than once; "
                "combine the edits into one entry."
            )
        by_row[correction.row_id] = correction

    desired: list[_PODesiredRow] = []
    for row in snapshot.rows:
        correction = by_row.get(row.row_id)
        if correction is None:
            desired.append(
                _PODesiredRow(
                    source=row,
                    variant_id=row.variant_id,
                    quantity=row.quantity,
                    price_per_unit=row.price_per_unit,
                )
            )
            continue
        target = _PODesiredRow(
            source=row,
            variant_id=(
                correction.new_variant_id
                if correction.new_variant_id is not None
                else row.variant_id
            ),
            quantity=(
                correction.quantity if correction.quantity is not None else row.quantity
            ),
            price_per_unit=(
                correction.price_per_unit
                if correction.price_per_unit is not None
                else row.price_per_unit
            ),
        )
        batched = any(bt.batch_id is not None for bt in row.batch_transactions)
        if batched and (
            target.variant_id != row.variant_id
            or abs(target.quantity - row.quantity) > _PO_QTY_TOLERANCE
        ):
            raise ValueError(
                f"Row {row.row_id} on PO {po_id} was received into batches; "
                "changing its variant or quantity would leave the batch "
                "split inconsistent on replay. Fix the batches in Katana "
                "first, or correct only the price."
            )
        if target.variant_id is None:
            raise ValueError(
                f"Row {row.row_id} on PO {po_id} has no variant; cannot rebuild it."
            )
        desired.append(target)
    return desired


async def _fetch_po_cost_rows(
    services: Any, group_ids: set[int]
) -> list[PurchaseOrderAdditionalCostRow]:
    """Additional cost rows attached to the given receipt groups.

    Read before anything is written: the revert moves these rows to the
    order's default group, so this is the only point their original group
    is visible.
    """
    found: list[PurchaseOrderAdditionalCostRow] = []
    for group_id in sorted(group_ids):
        response = await api_get_po_cost_rows.asyncio_detailed(
            client=services.client, group_id=float(group_id)
        )
        rows = unwrap_data(response=response, default=[])
        found.extend(
            r
            for r in rows
            if isinstance(r, PurchaseOrderAdditionalCostRow)
            and unwrap_unset(r.group_id, None) == group_id
            and unwrap_unset(r.deleted_at, None) is None
        )
    return found


async def _current_po_rows(services: Any, po_id: int) -> list[PurchaseOrderRow]:
    """Re-read the PO's rows; the revert changes them, so apply steps never
    trust ids captured before it."""
    po = await _fetch_purchase_order_attrs(services, po_id)
    if po is None:
        raise ValueError(f"Could not re-read purchase order {po_id}.")
    return [
        r for r in (unwrap_unset(po.purchase_order_rows, []) or []) if r is not None
    ]


def _build_complete_open_rows_action(
    po_id: int,
    open_rows: list[PORowSnapshot],
    progress: _POCorrectionProgress,
    services: Any,
) -> ActionSpec:
    """Temporarily receive a PARTIALLY_RECEIVED PO's open rows.

    Katana refuses ``status: NOT_RECEIVED`` on a PARTIALLY_RECEIVED PO
    (422), so the open quantity is received first (dated now), the PO is
    reverted as a whole, and the rebuilt rows for that quantity are simply
    not re-received.
    """
    received_at = datetime.now(UTC)
    body = [
        PurchaseOrderReceiveRow(
            purchase_order_row_id=r.row_id,
            quantity=r.quantity,
            received_date=received_at,
        )
        for r in open_rows
    ]

    async def apply() -> None:
        response = await api_receive_purchase_order.asyncio_detailed(
            client=services.client, body=body
        )
        if not is_success(response):
            unwrap(response)
        progress.completion_applied = True
        return None

    return ActionSpec(
        operation=POOperation.RECEIVE,
        target_id=po_id,
        diff=[
            FieldChange(
                field="open_rows_received_temporarily",
                new=[
                    {
                        "row_id": r.row_id,
                        "variant_id": r.variant_id,
                        "quantity": r.quantity,
                    }
                    for r in open_rows
                ],
                is_added=True,
            )
        ],
        apply=_tracked(progress, apply),
        verify=None,
    )


def _build_revert_po_action(
    po_id: int, prior_status: str, progress: _POCorrectionProgress, services: Any
) -> ActionSpec:
    """PATCH PO header → status: NOT_RECEIVED.

    The API-sanctioned reopen path: it undoes every receipt so the row
    fields become editable. ``prior_status`` is what the preview reports
    the PO is reverted *from*.
    """
    body = APIUpdatePurchaseOrderRequest(status=PurchaseOrderStatus(PO_REOPEN_STATUS))
    patch = _make_tolerant_patch_apply(api_update_purchase_order, services, po_id, body)

    async def apply() -> Any:
        outcome = await patch()
        progress.reverted = True
        return outcome

    return ActionSpec(
        operation=POOperation.UPDATE_HEADER,
        target_id=po_id,
        diff=[FieldChange(field="status", old=prior_status, new=PO_REOPEN_STATUS)],
        apply=_tracked(progress, apply),
        verify=None,
    )


def _row_patch_body(
    current: PurchaseOrderRow, desired: _PODesiredRow
) -> APIUpdatePORowRequest | None:
    """PATCH body turning ``current`` into ``desired``; None when equal."""
    source = desired.source
    changes: dict[str, Any] = {}
    if unwrap_unset(current.variant_id, None) != desired.variant_id:
        changes["variant_id"] = desired.variant_id
    current_qty = float(unwrap_unset(current.quantity, 0.0) or 0.0)
    if abs(current_qty - desired.quantity) > _PO_QTY_TOLERANCE:
        changes["quantity"] = desired.quantity
    if (
        desired.price_per_unit is not None
        and unwrap_unset(current.price_per_unit, None) != desired.price_per_unit
    ):
        changes["price_per_unit"] = desired.price_per_unit
    if (
        source.tax_rate_id is not None
        and unwrap_unset(current.tax_rate_id, None) != source.tax_rate_id
    ):
        changes["tax_rate_id"] = source.tax_rate_id
    if (
        source.arrival_date is not None
        and unwrap_unset(current.arrival_date, None) != source.arrival_date
    ):
        changes["arrival_date"] = source.arrival_date
    if (
        source.location_id is not None
        and unwrap_unset(current.location_id, None) != source.location_id
    ):
        changes["location_id"] = source.location_id
    if (
        source.purchase_uom is not None
        and unwrap_unset(current.purchase_uom, None) != source.purchase_uom
    ):
        changes["purchase_uom"] = source.purchase_uom
    if (
        source.purchase_uom_conversion_rate is not None
        and unwrap_unset(current.purchase_uom_conversion_rate, None)
        != source.purchase_uom_conversion_rate
    ):
        changes["purchase_uom_conversion_rate"] = source.purchase_uom_conversion_rate
    if not changes:
        return None
    return APIUpdatePORowRequest(**changes)


def _match_rows_after_revert(
    po_id: int, desired: list[_PODesiredRow], current: list[PurchaseOrderRow]
) -> dict[int, PurchaseOrderRow]:
    """Map each captured row id to the post-revert row that will become it.

    The revert merges rows that are identical apart from quantity into the
    lowest id of the set, so a captured id that survived is reused; the
    rest are re-created. Quantities per variant must add up to what was
    captured, otherwise the order changed under us and nothing is edited.
    """
    if any(unwrap_unset(r.received_date, None) is not None for r in current):
        raise ValueError(
            f"PO {po_id} still has received rows after the revert; nothing was edited."
        )
    captured: dict[int | None, float] = {}
    for d in desired:
        captured[d.source.variant_id] = (
            captured.get(d.source.variant_id, 0.0) + d.source.quantity
        )
    found: dict[int | None, float] = {}
    for r in current:
        variant = unwrap_unset(r.variant_id, None)
        found[variant] = found.get(variant, 0.0) + float(
            unwrap_unset(r.quantity, 0.0) or 0.0
        )
    mismatched = sorted(
        (str(v), captured.get(v, 0.0), found.get(v, 0.0))
        for v in set(captured) | set(found)
        if abs(captured.get(v, 0.0) - found.get(v, 0.0)) > _PO_QTY_TOLERANCE
    )
    if mismatched:
        detail = "; ".join(
            f"variant {v}: captured {c}, found {f}" for v, c, f in mismatched
        )
        raise ValueError(
            f"After the revert, PO {po_id}'s rows do not add up to the captured "
            f"rows ({detail}); nothing was edited."
        )

    unclaimed = {r.id: r for r in current}
    matched: dict[int, PurchaseOrderRow] = {}
    for d in desired:
        if d.source.row_id in unclaimed:
            matched[d.source.row_id] = unclaimed.pop(d.source.row_id)
    for d in desired:
        if d.source.row_id in matched:
            continue
        stand_in = next(
            (
                r
                for r in unclaimed.values()
                if unwrap_unset(r.variant_id, None) == d.source.variant_id
            ),
            None,
        )
        if stand_in is not None:
            matched[d.source.row_id] = unclaimed.pop(stand_in.id)
    if unclaimed:
        raise ValueError(
            f"After the revert, PO {po_id} has rows {sorted(unclaimed)} that match "
            "no captured row; nothing was edited."
        )
    return matched


def _build_rebuild_rows_action(
    po_id: int,
    desired: list[_PODesiredRow],
    snapshot: POCloseState,
    progress: _POCorrectionProgress,
    services: Any,
) -> ActionSpec:
    """Turn the reverted order back into one row per captured row, edited.

    Each captured row gets its own physical row again: a surviving row is
    patched to the captured (corrected) values, a row the revert merged
    away is re-created. The replay then receives exact rows by id, so no
    quantity is allocated by variant and an edit never spreads to a row
    it was not aimed at.
    """

    async def apply() -> None:
        current = await _current_po_rows(services, po_id)
        matched = _match_rows_after_revert(po_id, desired, current)
        for d in desired:
            row = matched.get(d.source.row_id)
            if row is not None:
                body = _row_patch_body(row, d)
                if body is not None:
                    response = await api_update_purchase_order_row.asyncio_detailed(
                        id=row.id, client=services.client, body=body
                    )
                    if not is_success(response):
                        unwrap(response)
                progress.physical_row_ids[d.source.row_id] = row.id
                continue
            if d.variant_id is None or d.price_per_unit is None:
                raise ValueError(
                    f"Row {d.source.row_id} has no variant or unit price to "
                    "re-create it with."
                )
            create = APICreatePORowRequest(
                purchase_order_id=po_id,
                variant_id=d.variant_id,
                quantity=d.quantity,
                price_per_unit=d.price_per_unit,
                tax_rate_id=to_unset(d.source.tax_rate_id),
                arrival_date=to_unset(d.source.arrival_date),
                location_id=to_unset(d.source.location_id),
                currency=to_unset(d.source.currency),
                purchase_uom=to_unset(d.source.purchase_uom),
                purchase_uom_conversion_rate=to_unset(
                    d.source.purchase_uom_conversion_rate
                ),
            )
            response = await api_create_purchase_order_row.asyncio_detailed(
                client=services.client, body=create
            )
            created = unwrap_as(response, PurchaseOrderRow)
            progress.physical_row_ids[d.source.row_id] = created.id
        progress.rows_rebuilt = True
        return None

    diff: list[FieldChange] = []
    for d in desired:
        if not d.changed:
            continue
        label = f"row {d.source.row_id}"
        if d.variant_id != d.source.variant_id:
            diff.append(
                FieldChange(
                    field=f"{label} variant_id",
                    old=d.source.variant_id,
                    new=d.variant_id,
                )
            )
        if abs(d.quantity - d.source.quantity) > _PO_QTY_TOLERANCE:
            diff.append(
                FieldChange(
                    field=f"{label} quantity", old=d.source.quantity, new=d.quantity
                )
            )
        if d.price_per_unit != d.source.price_per_unit:
            diff.append(
                FieldChange(
                    field=f"{label} price_per_unit",
                    old=d.source.price_per_unit,
                    new=d.price_per_unit,
                )
            )
    recreated = [row for merged in snapshot.predicted_merges() for row in merged[1:]]
    if recreated:
        diff.append(
            FieldChange(
                field="rows_recreated_after_merge",
                new=[
                    {
                        "source_row_id": r.row_id,
                        "variant_id": r.variant_id,
                        "quantity": r.quantity,
                    }
                    for r in recreated
                ],
                is_added=True,
            )
        )
    return ActionSpec(
        operation=POOperation.UPDATE_ROW,
        target_id=po_id,
        diff=diff,
        apply=_tracked(progress, apply),
        verify=None,
    )


def _build_re_receive_group_action(
    po_id: int,
    index: int,
    group: POReceiptGroup,
    desired_by_row: dict[int, _PODesiredRow],
    progress: _POCorrectionProgress,
    services: Any,
) -> ActionSpec:
    """POST one ``/purchase_order_receive`` call replaying one receipt group.

    One call records one receipt group, so replaying group by group (oldest
    first) rebuilds the original receipts. Each rebuilt row is received in
    full with its own ``received_date``; the group id the call produced is
    recorded for the cost-row moves.
    """
    planned = [desired_by_row[r.row_id] for r in group.rows]

    async def apply() -> None:
        missing = [
            d.source.row_id
            for d in planned
            if d.source.row_id not in progress.physical_row_ids
        ]
        if missing:
            raise ValueError(
                f"Rows {missing} were not rebuilt; cannot replay this receipt."
            )
        body = [
            PurchaseOrderReceiveRow(
                purchase_order_row_id=progress.physical_row_ids[d.source.row_id],
                quantity=d.quantity,
                received_date=d.source.received_date or group.received_date,
                batch_transactions=[
                    PurchaseOrderReceiveRowBatchTransactionsItem(
                        batch_id=bt.batch_id, quantity=bt.quantity
                    )
                    for bt in d.source.batch_transactions
                    if bt.batch_id is not None
                ]
                or to_unset(None),
            )
            for d in planned
        ]
        response = await api_receive_purchase_order.asyncio_detailed(
            client=services.client, body=body
        )
        if not is_success(response):
            unwrap(response)
        progress.replayed_groups.add(index)
        received_ids = {item.purchase_order_row_id for item in body}
        current = await _current_po_rows(services, po_id)
        new_groups = {
            unwrap_unset(r.group_id, None) for r in current if r.id in received_ids
        }
        if len(new_groups) == 1:
            (new_group,) = new_groups
            if isinstance(new_group, int):
                progress.new_group_ids[index] = new_group
        return None

    diff = [
        FieldChange(
            field="received_date", new=group.received_date.isoformat(), is_added=True
        ),
        FieldChange(
            field="rows",
            new=[
                {
                    "source_row_id": d.source.row_id,
                    "variant_id": d.variant_id,
                    "quantity": d.quantity,
                    **(
                        {"received_date": d.source.received_date.isoformat()}
                        if d.source.received_date
                        and d.source.received_date != group.received_date
                        else {}
                    ),
                    **(
                        {
                            "batch_transactions": [
                                {"batch_id": bt.batch_id, "quantity": bt.quantity}
                                for bt in d.source.batch_transactions
                                if bt.batch_id is not None
                            ]
                        }
                        if any(
                            bt.batch_id is not None
                            for bt in d.source.batch_transactions
                        )
                        else {}
                    ),
                }
                for d in planned
            ],
            is_added=True,
        ),
    ]
    return ActionSpec(
        operation=POOperation.RECEIVE,
        target_id=group.group_id,
        diff=diff,
        apply=_tracked(progress, apply),
        verify=None,
    )


def _build_move_cost_row_action(
    index: int,
    group: POReceiptGroup,
    cost_row: POCostRowSnapshot,
    progress: _POCorrectionProgress,
    services: Any,
) -> ActionSpec:
    """Re-attach an additional cost row to its rebuilt receipt group.

    The revert moves cost rows to the default group and receiving does not
    move them back; the group id cannot be patched, so the row is
    re-created on the rebuilt group and the original deleted (create
    first, so a failure never loses the cost).
    """

    async def apply() -> None:
        new_group = progress.new_group_ids.get(index)
        if new_group is None:
            raise ValueError(
                f"Could not tell which group the receipt dated "
                f"{group.received_date.isoformat()} was rebuilt as; additional "
                f"cost row {cost_row.cost_row_id} was left on the default group."
            )
        current = unwrap_as(
            await api_get_po_cost_row.asyncio_detailed(
                id=cost_row.cost_row_id, client=services.client
            ),
            PurchaseOrderAdditionalCostRow,
        )
        if unwrap_unset(current.group_id, None) == new_group:
            progress.moved_cost_rows.add(cost_row.cost_row_id)
            return None
        create = APICreatePOCostRowRequest(
            additional_cost_id=cost_row.additional_cost_id,
            group_id=new_group,
            tax_rate_id=cost_row.tax_rate_id,
            price=cost_row.price,
            distribution_method=(
                CostDistributionMethod(cost_row.distribution_method)
                if cost_row.distribution_method
                else to_unset(None)
            ),
            reference=to_unset(cost_row.reference),
        )
        copy = unwrap_as(
            await api_create_po_cost_row.asyncio_detailed(
                client=services.client, body=create
            ),
            PurchaseOrderAdditionalCostRow,
        )
        progress.copied_cost_rows[cost_row.cost_row_id] = copy.id
        deleted = await api_delete_po_cost_row.asyncio_detailed(
            id=cost_row.cost_row_id, client=services.client
        )
        if not is_success(deleted):
            unwrap(deleted)
        progress.moved_cost_rows.add(cost_row.cost_row_id)
        return None

    return ActionSpec(
        operation=POOperation.UPDATE_ADDITIONAL_COST,
        target_id=cost_row.cost_row_id,
        diff=[
            FieldChange(
                field="group_id",
                old=cost_row.group_id,
                new=f"rebuilt group of the receipt dated {group.received_date.isoformat()}",
            )
        ],
        apply=_tracked(progress, apply),
        verify=None,
    )


def _po_expected_status(desired: list[_PODesiredRow]) -> str:
    if any(not d.source.is_received for d in desired):
        return PurchaseOrderStatus.PARTIALLY_RECEIVED.value
    return PurchaseOrderStatus.RECEIVED.value


async def _correct_purchase_order_impl(
    request: CorrectPurchaseOrderRequest, context: Context
) -> ModificationResponse:
    services = get_services(context)
    katana_url = katana_web_url("purchase_order", request.id)

    existing_po = await _fetch_purchase_order_attrs(services, request.id)
    if existing_po is None:
        raise ValueError(
            f"Could not fetch purchase order {request.id}; verify it exists."
        )
    status_enum = unwrap_unset(existing_po.status, None)
    status = status_enum.value if status_enum is not None else ""
    if status not in PO_CLOSED_STATUSES:
        raise ValueError(
            f"correct_purchase_order requires the PO to be in RECEIVED or "
            f"PARTIALLY_RECEIVED status; PO {request.id} is in status "
            f"'{status}'. Use modify_purchase_order directly for an open "
            "PO — there's no close-state to preserve."
        )

    rows_only = snapshot_po_close_state(existing_po)
    received_groups = {
        r.group_id for r in rows_only.received_rows if r.group_id is not None
    }
    cost_rows = await _fetch_po_cost_rows(services, received_groups)
    snapshot = snapshot_po_close_state(existing_po, cost_rows)
    desired = _desired_po_rows(request.id, snapshot, request.row_changes)
    desired_by_row = {d.source.row_id: d for d in desired}
    groups = snapshot.receipt_groups()
    progress = _POCorrectionProgress()

    # Katana refuses the whole-order revert while PARTIALLY_RECEIVED, so a
    # partially received PO is completed first and its open quantity is
    # simply not replayed afterwards.
    complete_phase = (
        [
            _build_complete_open_rows_action(
                request.id, snapshot.open_rows, progress, services
            )
        ]
        if snapshot.status == PurchaseOrderStatus.PARTIALLY_RECEIVED.value
        and snapshot.open_rows
        else []
    )
    revert_phase = [
        _build_revert_po_action(request.id, snapshot.status, progress, services)
    ]
    rebuild_phase = [
        _build_rebuild_rows_action(request.id, desired, snapshot, progress, services)
    ]
    receive_phase: list[ActionSpec] = []
    for index, group in enumerate(groups):
        receive_phase.append(
            _build_re_receive_group_action(
                request.id, index, group, desired_by_row, progress, services
            )
        )
        receive_phase.extend(
            _build_move_cost_row_action(index, group, cost_row, progress, services)
            for cost_row in snapshot.cost_rows_for_group(group.group_id)
        )
    phases = [complete_phase, revert_phase, rebuild_phase, receive_phase]

    # See #722 note on the MO / SO correction above.
    prior_state = _augment_prior_state_with_snapshot(
        serialize_for_prior_state(existing_po), snapshot
    )
    expected_status = _po_expected_status(desired)
    warnings = _close_state_warnings_po(snapshot, desired)

    if request.preview:
        full_plan = [action for phase in phases for action in phase]
        return ModificationResponse(
            entity_type="purchase_order",
            entity_id=request.id,
            is_preview=True,
            actions=plan_to_preview_results(full_plan),
            prior_state=prior_state,
            warnings=warnings,
            next_actions=[
                f"Review {len(full_plan)} planned action(s) for PO {request.id}",
                f"Captured close-state: status={snapshot.status}, "
                f"{len(snapshot.received_rows)} received row(s) in "
                f"{len(groups)} receipt group(s), "
                f"{len(snapshot.cost_rows)} additional cost row(s)",
                f"Expected status afterwards: {expected_status}",
                "Set preview=false to execute the plan",
            ],
            katana_url=katana_url,
            message=(
                f"Preview: reopen → rebuild rows → re-receive for purchase "
                f"order {request.id} ({len(full_plan)} action(s))"
            ),
        )
    aggregated, failed, _not_run_specs = await _run_phases_until_failure(phases)
    if failed:
        # PO modify card doesn't merge NOT-RUN extras yet — drop the spec
        # tail here. The SO failure path above synthesizes them for the SO
        # modify-card morph (#858 finding B).
        return _build_po_failure_response(
            request.id,
            aggregated,
            prior_state,
            katana_url,
            _POFailureContext(
                snapshot=snapshot, desired=desired, groups=groups, progress=progress
            ),
        )

    final_po = await _fetch_purchase_order_attrs(services, request.id)
    final_enum = unwrap_unset(final_po.status, None) if final_po is not None else None
    final_status = final_enum.value if final_enum is not None else "unknown"
    if final_status != expected_status:
        warnings.append(
            f"PO {request.id} ended in status {final_status}, expected "
            f"{expected_status}. Check its rows with get_purchase_order."
        )
    applied = sum(1 for a in aggregated if a.succeeded)
    return ModificationResponse(
        entity_type="purchase_order",
        entity_id=request.id,
        is_preview=False,
        actions=aggregated,
        prior_state=prior_state,
        warnings=warnings,
        next_actions=[
            f"Purchase order {request.id} corrected — {applied} action(s) applied",
            f"Status now {final_status}; {len(groups)} receipt group(s) "
            "replayed with new group ids",
        ],
        katana_url=katana_url,
        message=(
            f"Successfully corrected purchase order {request.id} "
            f"({applied}/{len(aggregated)} actions applied)"
        ),
    )


def _close_state_warnings_po(
    snapshot: POCloseState, desired: list[_PODesiredRow]
) -> list[str]:
    if not snapshot.received_rows:
        return [
            "No receipts captured on this PO — the reopen step will only "
            "flip status to NOT_RECEIVED without a re-receive phase. "
            "Verify this matches reality before applying."
        ]
    warnings = [
        "Receipts are replayed one receive call per original receipt group, "
        "oldest first, so the groups come back with new group ids."
    ]
    recreated = [
        row.row_id for merged in snapshot.predicted_merges() for row in merged[1:]
    ]
    if recreated:
        warnings.append(
            f"The revert merges rows that are identical apart from quantity; "
            f"rows {recreated} are re-created afterwards with new ids."
        )
    if snapshot.cost_rows:
        warnings.append(
            f"{len(snapshot.cost_rows)} additional cost row(s) on the receipt "
            "groups are re-attached to the rebuilt groups: where a group gets a "
            "new id the cost row is re-created there (new id) and the original "
            "deleted. Katana recalculates landed cost asynchronously, so row "
            "landed costs can take a few seconds to settle."
        )
    if snapshot.skipped_cost_row_ids:
        warnings.append(
            f"Additional cost row(s) {list(snapshot.skipped_cost_row_ids)} lack "
            "a field needed to re-create them; the revert moves them to the "
            "PO's default group and the tool leaves them there. Re-attach them "
            "by hand afterwards."
        )
    recreated_rows = [
        row for merged in snapshot.predicted_merges() for row in merged[1:]
    ]
    if any(row.conversion_rate is not None for row in recreated_rows):
        warnings.append(
            "Re-created rows are priced in the PO's currency; Katana may apply "
            "its current conversion rate to them rather than the original one."
        )
    if any(c.currency_conversion_rate is not None for c in snapshot.cost_rows):
        warnings.append(
            "Re-created additional cost rows may take Katana's current "
            "currency conversion rate rather than the original one."
        )
    if any(d.changed and d.source.is_received for d in desired):
        warnings.append(
            "Edits on received rows are replayed as received: a corrected "
            "quantity is the quantity re-received on that row's original date."
        )
    if snapshot.status == PurchaseOrderStatus.PARTIALLY_RECEIVED.value:
        warnings.append(
            "PO is PARTIALLY_RECEIVED. Katana refuses the revert in that "
            "state, so the open row(s) are received first (dated now), the "
            "PO is reverted as a whole, and only the original receipts are "
            "replayed; the open quantity ends up unreceived again."
        )
    return warnings


@dataclass(frozen=True)
class _POFailureContext:
    snapshot: POCloseState
    desired: list[_PODesiredRow]
    groups: list[POReceiptGroup]
    progress: _POCorrectionProgress


def _describe_remaining_receipts(ctx: _POFailureContext) -> list[str]:
    """One line per receipt group that was not replayed, oldest first."""
    desired_by_row = {d.source.row_id: d for d in ctx.desired}
    lines: list[str] = []
    for index, group in enumerate(ctx.groups):
        if index in ctx.progress.replayed_groups:
            continue
        parts = []
        for row in group.rows:
            physical = ctx.progress.physical_row_ids.get(row.row_id)
            label = (
                f"row {physical}" if physical else f"the row rebuilt from {row.row_id}"
            )
            target = desired_by_row[row.row_id]
            dated = (row.received_date or group.received_date).isoformat()
            parts.append(
                f"{label} (variant {target.variant_id}) qty {target.quantity} "
                f"dated {dated}"
            )
        lines.append(
            f"receipt dated {group.received_date.isoformat()}: " + ", ".join(parts)
        )
    return lines


def _build_po_failure_response(
    po_id: int,
    actions: list[ActionResult],
    prior_state: dict[str, Any] | None,
    katana_url: str | None,
    ctx: _POFailureContext,
) -> ModificationResponse:
    """Failure response that states what was written and how to finish.

    A re-run would snapshot the half-restored order and treat temporary
    or missing receipts as the truth, so once anything was written the
    operator is told not to re-run and given the exact remaining steps.
    """
    progress = ctx.progress
    succeeded = sum(1 for a in actions if a.succeeded is True)
    failed = sum(1 for a in actions if a.succeeded is False)
    remaining = _describe_remaining_receipts(ctx)
    warnings: list[str] = []
    next_actions = [f"{succeeded} action(s) succeeded; {failed} failed"]
    if progress.outcome_unknown:
        warnings.append(
            "The failing call timed out or hit a server error, so it may have "
            f"reached Katana anyway. Check PO {po_id}'s status and rows with "
            "get_purchase_order before acting on the steps below; skip any "
            "step it shows is already done."
        )
    if (
        not progress.completion_applied
        and not progress.reverted
        and not progress.outcome_unknown
    ):
        warnings.append(
            f"Nothing was written; PO {po_id} is unchanged. Fix the cause "
            "in the FAILED action's error and re-run correct_purchase_order."
        )
    else:
        warnings.append(
            "Do not re-run correct_purchase_order on this PO: it would "
            "snapshot the half-restored order and lose the receipts listed "
            "below. Finish by hand with the steps in next_actions."
        )
        if progress.completion_applied and not progress.reverted:
            opened = ", ".join(
                f"row {r.row_id} qty {r.quantity}" for r in ctx.snapshot.open_rows
            )
            warnings.append(
                f"The open rows ({opened}) were received dated now as a "
                "temporary step and the revert then failed, so the PO is "
                "RECEIVED with that extra stock."
            )
            next_actions.append(
                f"Set PO {po_id} to NOT_RECEIVED with modify_purchase_order "
                "to undo every receipt, including the temporary one"
            )
        if not progress.rows_rebuilt:
            done = [
                f"captured row {source} is row {physical}"
                for source, physical in progress.physical_row_ids.items()
            ]
            todo = [
                d.source.row_id
                for d in ctx.desired
                if d.source.row_id not in progress.physical_row_ids
            ]
            next_actions.append(
                "Edit the rows with modify_purchase_order so the PO has one row "
                "per entry in prior_state._close_state_snapshot.rows, with the "
                "requested corrections applied. "
                + (f"Already in place: {'; '.join(done)}. " if done else "")
                + f"Still needing a row: captured rows {todo}"
            )
        if remaining:
            next_actions.append(
                "Re-receive with receive_purchase_order, one call per receipt, "
                "in this order: " + "; ".join(remaining)
            )
        for cost in ctx.snapshot.cost_rows:
            if cost.cost_row_id in progress.moved_cost_rows:
                continue
            copy_id = progress.copied_cost_rows.get(cost.cost_row_id)
            if copy_id is not None:
                next_actions.append(
                    f"Additional cost row {cost.cost_row_id} was copied to its "
                    f"rebuilt group as row {copy_id} but the original was not "
                    f"deleted; delete row {cost.cost_row_id} (do not re-create it)"
                )
            else:
                next_actions.append(
                    f"Additional cost row {cost.cost_row_id} is on the PO's "
                    "default group; re-create it on the rebuilt group of the "
                    "receipt it belonged to and delete the original"
                )
    return ModificationResponse(
        entity_type="purchase_order",
        entity_id=po_id,
        is_preview=False,
        actions=actions,
        prior_state=prior_state,
        warnings=warnings,
        next_actions=next_actions,
        katana_url=katana_url,
        message=(
            f"Partial: {succeeded}/{len(actions)} action(s) applied to "
            f"purchase order {po_id} before fail-fast halt"
        ),
    )


@observe_tool
@unpack_pydantic_params
async def correct_purchase_order(
    request: Annotated[CorrectPurchaseOrderRequest, Unpack()], context: Context
) -> ToolResult:
    """Edit a closed (RECEIVED / PARTIALLY_RECEIVED) PO without losing
    the original receipts.

    Sequence:

    1. Capture every row (received or open) with its receipt group, date,
       batches, price, tax rate and arrival date, plus the additional cost
       rows attached to the receipt groups.
    2. PARTIALLY_RECEIVED only: receive the open rows (dated now), because
       Katana refuses the revert in that state.
    3. PATCH PO status: NOT_RECEIVED. This undoes every receipt and merges
       rows that are identical apart from quantity.
    4. Rebuild one row per captured row with ``row_changes`` applied:
       surviving rows are patched, merged-away rows re-created.
    5. POST /purchase_order_receive once per original receipt group,
       oldest first, receiving each rebuilt row with its original date.
       Additional cost rows are re-created on the rebuilt groups.

    ``row_changes`` entries are keyed by the row's current ID (look up via
    ``get_purchase_order``) and apply to that row only. On a received row,
    ``quantity`` is the corrected received quantity. Rows that were
    received into batches can only have their price corrected.

    The tool edits rows in place; it doesn't delete or add rows. To add or
    remove a line, use ``modify_purchase_order`` after the correction
    lands, or delete + recreate the PO.

    Two-step flow: ``preview=true`` (default) returns the full action
    plan; ``preview=false`` runs it. On a failure the response says
    whether anything was written; if it was, it lists the exact remaining
    steps and the tool must not be re-run on that PO.

    For a PO that hasn't been received yet, use ``modify_purchase_order``
    directly — there's no close-state to preserve.
    """
    response = await _correct_purchase_order_impl(request, context)
    return to_tool_result(
        response, confirm_request=request, confirm_tool="correct_purchase_order"
    )


# ============================================================================
# Registration
# ============================================================================


def register_tools(mcp: FastMCP) -> None:
    """Register correction tools with the FastMCP instance."""
    from mcp.types import ToolAnnotations

    from katana_mcp.tools.prefab_ui import register_preview_tool

    _correct = ToolAnnotations(
        read_only_hint=False,
        destructive_hint=True,
        idempotent_hint=True,
        open_world_hint=True,
    )

    register_preview_tool(
        mcp,
        correct_manufacturing_order,
        tags={"orders", "manufacturing", "write", "correction"},
        annotations=_correct,
        meta=UI_META,
    )
    register_preview_tool(
        mcp,
        correct_sales_order,
        tags={"orders", "sales", "write", "correction"},
        annotations=_correct,
        meta=UI_META,
    )
    register_preview_tool(
        mcp,
        correct_purchase_order,
        tags={"orders", "purchasing", "write", "correction"},
        annotations=_correct,
        meta=UI_META,
    )
