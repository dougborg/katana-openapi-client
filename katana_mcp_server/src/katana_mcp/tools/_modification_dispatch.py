"""Action-plan dispatcher for unified ``modify_<entity>`` tools.

This module provides the generic execution layer used by every
``modify_<entity>`` tool (modify_purchase_order, modify_sales_order,
modify_manufacturing_order, modify_stock_transfer, modify_item).

## Tool authoring contract

Every ``modify_<entity>`` tool follows this shape:

1. Define a Pydantic ``ModifyXyzRequest`` with one optional sub-payload slot
   per kind of action the entity supports (``update_header``,
   ``add_rows``, ``update_rows``, ``delete_row_ids``, ``delete``, etc.).
2. In the impl, fetch the existing entity (best-effort) for diff context.
3. Build a ``list[ActionSpec]`` translating sub-payloads into planned API
   calls — each ActionSpec carries the operation name, target id, diff
   metadata, and async closures for ``apply`` and (optional) ``verify``.
4. **Preview branch** (``confirm=False``): wrap the plan in
   :class:`ActionResult` entries with ``succeeded=None`` (planned, not run)
   and return the :class:`ModificationResponse`.
5. **Confirm branch** (``confirm=True``): call :func:`execute_plan` to run
   the actions in order, fail-fast on the first error. Capture
   ``prior_state`` before invoking. Return the same response shape with
   ``actions`` populated.

## Why fail-fast + manual revert (not auto-rollback)

The Katana API is not transactional across endpoints. If action 3 of 5
fails, actions 1-2 are already applied server-side. We chose:

- **Fail-fast** — stop at the first error so the caller knows exactly which
  actions ran. Subsequent actions don't get attempted blindly.
- **Manual revert** — capture pre-modification state into
  ``response.prior_state`` so the caller has the data needed to compose a
  follow-up ``modify`` call that restores the prior values. We don't try
  to auto-revert via inverse calls — those have their own failure modes
  (network, timing, server-side state changes between apply and undo) and
  silent inconsistencies are worse than visible partial application.

## Why post-action verification

A 200 response from Katana doesn't always mean the change took effect —
some endpoints silently coerce or reject inputs. Each ActionSpec can
register a ``verify`` callable that re-fetches the targeted entity and
confirms the change actually landed. Verification failure surfaces as
``ActionResult.verified=False`` with an ``actual_after`` snapshot — it
doesn't raise, because the action *did* succeed at the API layer; the
caller just needs to know the post-state diverged from the request.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, cast

from pydantic import BaseModel

from katana_mcp.logging import get_logger
from katana_mcp.tools._modification import (
    ActionResult,
    FieldChange,
    ModificationResponse,
    compute_field_diff,
    make_response_verifier,
)
from katana_mcp.web_urls import EntityKind, katana_web_url
from katana_public_api_client.domain.converters import to_unset
from katana_public_api_client.utils import is_success, unwrap, unwrap_as

logger = get_logger(__name__)


# ``apply`` callable: returns whatever the API call yields (typically the
# parsed response model). Returned to ``verify`` so verification can use it
# (e.g. confirm a created row's id matches what we expected).
ApplyCallable = Callable[[], Awaitable[Any]]

# ``verify`` callable: takes the apply result, returns
# ``(verified, actual_after_dict_or_None)``. Verification failures should
# return ``(False, snapshot)`` rather than raising — the action itself
# succeeded; the caller just needs the divergence visible.
VerifyCallable = Callable[[Any], Awaitable[tuple[bool, dict[str, Any] | None]]]


@dataclass
class ActionSpec:
    """A single planned action — preview metadata + execution closures.

    Constructed by per-entity tool code; consumed by :func:`execute_plan`.
    """

    operation: str
    target_id: int | None
    diff: list[FieldChange] = field(default_factory=list)
    apply: ApplyCallable | None = None
    verify: VerifyCallable | None = None

    def to_planned_result(self) -> ActionResult:
        """Build an ActionResult for the preview branch (action not yet run)."""
        return ActionResult(
            operation=self.operation,
            target_id=self.target_id,
            changes=list(self.diff),
            succeeded=None,
            verified=None,
        )


async def execute_plan(plan: list[ActionSpec]) -> list[ActionResult]:
    """Execute an action plan in order, fail-fast on first error.

    Each :class:`ActionSpec` is awaited via its ``apply`` callable. After a
    successful apply, the optional ``verify`` callable is awaited to confirm
    the change landed; verification failure does NOT halt the plan or
    raise — it surfaces as ``ActionResult.verified=False`` so the caller
    sees the divergence.

    Returns a list of :class:`ActionResult` of length 1..len(plan) — equal
    to the plan length on full success, shorter when fail-fast halted
    after action N (the result list ends at the failed action; later
    actions are not represented).
    """
    results: list[ActionResult] = []

    for spec in plan:
        if spec.apply is None:
            # Should never happen — preview-only specs go through
            # ``to_planned_result`` directly, not execute_plan. Fail loudly.
            raise RuntimeError(
                f"ActionSpec for {spec.operation} (target {spec.target_id}) "
                "has no apply callable; cannot execute."
            )

        try:
            outcome = await spec.apply()
        except Exception as exc:
            logger.warning(
                f"Action {spec.operation} (target {spec.target_id}) failed: "
                f"{type(exc).__name__}: {exc}"
            )
            results.append(
                ActionResult(
                    operation=spec.operation,
                    target_id=spec.target_id,
                    changes=list(spec.diff),
                    succeeded=False,
                    error=f"{type(exc).__name__}: {exc}",
                )
            )
            return results  # fail-fast — do not attempt later actions

        verified: bool | None = None
        actual_after: dict[str, Any] | None = None
        if spec.verify is not None:
            try:
                verified, actual_after = await spec.verify(outcome)
            except Exception as exc:
                logger.info(
                    f"Verification of {spec.operation} (target {spec.target_id}) "
                    f"errored: {type(exc).__name__}: {exc} — marking verified=False"
                )
                verified = False
                actual_after = None

        results.append(
            ActionResult(
                operation=spec.operation,
                target_id=spec.target_id,
                changes=list(spec.diff),
                succeeded=True,
                verified=verified,
                actual_after=actual_after,
            )
        )

    return results


def plan_to_preview_results(plan: list[ActionSpec]) -> list[ActionResult]:
    """Convert a plan to preview-shaped :class:`ActionResult` entries.

    Used by the preview branch (``confirm=False``) where no API calls run.
    Each ActionResult carries the operation/target/diff but
    ``succeeded=None`` to signal "planned, not yet executed".
    """
    return [spec.to_planned_result() for spec in plan]


def unset_dict(
    model: BaseModel,
    *,
    field_map: dict[str, str] | None = None,
    transforms: dict[str, Callable[[Any], Any]] | None = None,
    exclude: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Convert a Pydantic patch model into kwargs for an attrs request constructor.

    For every field on ``model``: ``None`` becomes ``UNSET`` (so PATCH bodies
    omit unset fields), and concrete values pass through unchanged. Used to
    collapse the ``field=to_unset(patch.field)`` per-field repetition in
    every ``_build_*_request`` helper to a single ``**unset_dict(patch)``.

    Args:
        model: A Pydantic patch/payload model.
        field_map: Optional ``pydantic_name -> attrs_name`` rename map for
            fields that don't share names across the layers (e.g.
            ``{"zip": "zip_"}`` for the address ``zip`` field, since
            ``zip`` is a Python builtin and the attrs field is ``zip_``).
        transforms: Optional ``pydantic_name -> callable`` map for value
            conversions applied **before** UNSET-wrapping. Typical use:
            ``{"status": PurchaseOrderStatus}`` to coerce a status literal
            into the API enum. Transforms only fire when the field is
            non-None — None falls straight through to UNSET.
        exclude: Field names on the model to skip entirely (typically
            ``("id",)`` to drop the patch's id when the API request body
            doesn't carry it as a field).
    """
    field_map = field_map or {}
    transforms = transforms or {}
    out: dict[str, Any] = {}
    for k, v in model.model_dump(exclude_none=False).items():
        if k in exclude:
            continue
        value = transforms[k](v) if v is not None and k in transforms else v
        attr_name = field_map.get(k, k)
        out[attr_name] = to_unset(value)
    return out


def has_any_subpayload(
    request: BaseModel, *, exclude: tuple[str, ...] = ("id", "confirm")
) -> bool:
    """True if the request has any sub-payload set (any field outside ``exclude``).

    Generic across every ``modify_<entity>`` tool — each has a top-level
    request with a primary id, ``confirm``, and a set of optional
    sub-payload slots. This checks whether the caller asked for at least
    one action.
    """
    for name, value in request.model_dump(exclude_none=True).items():
        if name in exclude:
            continue
        if value is False or value == [] or value == {}:
            continue
        return True
    return False


def make_create_action(
    operation: str,
    payload: BaseModel,
    apply: ApplyCallable,
    *,
    exclude: tuple[str, ...] = ("confirm",),
) -> ActionSpec:
    """Build an ActionSpec for a create-style operation (POST).

    Diff is every field on ``payload`` reported as added (no prior state).
    No verify — ``unwrap_as`` raises on parse failure and creation
    succeeds iff the response carries an id, which is implicit in the
    apply outcome.
    """
    return ActionSpec(
        operation=operation,
        target_id=None,
        diff=compute_field_diff(None, payload, exclude=exclude),
        apply=apply,
        verify=None,
    )


async def make_update_action(
    operation: str,
    target_id: int,
    payload: BaseModel,
    fetcher: Callable[[int], Awaitable[Any | None]],
    apply: ApplyCallable,
    *,
    exclude: tuple[str, ...] = ("id", "confirm"),
) -> ActionSpec:
    """Build an ActionSpec for an update-style operation (PATCH).

    Pre-fetches the existing entity for diff context. When the fetch
    fails, fields are marked ``is_unknown_prior=True`` so previews
    distinguish "field was empty" from "we couldn't read prior state".
    Verify reads back the API response and confirms the requested
    fields landed.
    """
    existing = await fetcher(target_id)
    diff = compute_field_diff(
        existing, payload, unknown_prior=existing is None, exclude=exclude
    )
    return ActionSpec(
        operation=operation,
        target_id=target_id,
        diff=diff,
        apply=apply,
        verify=make_response_verifier(diff),
    )


def make_delete_action(
    operation: str,
    target_id: int,
    apply: ApplyCallable,
) -> ActionSpec:
    """Build an ActionSpec for a delete-style operation (DELETE).

    No verify — the entity is gone, can't fetch.
    """
    return ActionSpec(
        operation=operation,
        target_id=target_id,
        apply=apply,
        verify=None,
    )


# ============================================================================
# Generic API-call helpers shared by every ``modify_<entity>`` tool.
#
# Three layers stacked together cover ~80% of per-entity boilerplate:
#
# 1. ``safe_fetch_for_diff`` — best-effort GET that returns None on failure.
# 2. ``make_post_apply`` / ``make_patch_apply`` / ``make_delete_apply`` —
#    closure factories for ActionSpec.apply.
# 3. ``plan_creates`` / ``plan_updates`` / ``plan_deletes`` — plan-builder
#    factories that consume sub-payloads + a request-builder + an apply-builder
#    and yield ``list[ActionSpec]``.
# ============================================================================


async def safe_fetch_for_diff[T](
    endpoint: Any,
    services: Any,
    target_id: int,
    *,
    return_type: type[T],
    label: str,
) -> T | None:
    """Best-effort GET for diff context. Returns None on any error.

    Centralizes the try/except/log pattern every per-entity ``_fetch_<x>``
    helper used to repeat. ``label`` is the human-readable noun for the
    info-log on failure (e.g. ``"PO row"``, ``"SO fulfillment"``).
    """
    try:
        response = await endpoint.asyncio_detailed(id=target_id, client=services.client)
        return unwrap_as(response, return_type)
    except Exception as exc:
        logger.info(
            f"Could not fetch {label} {target_id} for diff context: {exc} — "
            "preview will report changes without prior values."
        )
        return None


def make_post_apply[T](
    endpoint: Any, services: Any, body: Any, *, return_type: type[T]
) -> ApplyCallable:
    """Build an ``apply`` closure for a POST endpoint that returns a model.

    Used by every ``add_*`` action: the generated client's POST endpoints
    take ``client=`` + ``body=`` and return a parsed entity. ``return_type``
    is the attrs class the response is asserted against by ``unwrap_as``.
    """

    async def apply() -> T:
        response = await endpoint.asyncio_detailed(client=services.client, body=body)
        # ``unwrap_as`` raises on error by default; narrow ``T | None`` → ``T``.
        return cast(T, unwrap_as(response, return_type))

    return apply


def make_patch_apply[T](
    endpoint: Any,
    services: Any,
    target_id: int,
    body: Any,
    *,
    return_type: type[T],
) -> ApplyCallable:
    """Build an ``apply`` closure for a PATCH endpoint that returns a model.

    Used by every ``update_*`` action: PATCH endpoints take ``id=``,
    ``client=``, ``body=`` and return the updated entity.
    """

    async def apply() -> T:
        response = await endpoint.asyncio_detailed(
            id=target_id, client=services.client, body=body
        )
        return cast(T, unwrap_as(response, return_type))

    return apply


def make_delete_apply(endpoint: Any, services: Any, target_id: int) -> ApplyCallable:
    """Build an ``apply`` closure for a DELETE endpoint with no body.

    Used by every ``delete_*`` action and the ``delete_<entity>`` tools.
    DELETE endpoints return 204 No Content on success; ``is_success`` +
    ``unwrap`` translates non-success into a typed error.
    """

    async def apply() -> None:
        response = await endpoint.asyncio_detailed(id=target_id, client=services.client)
        if not is_success(response):
            unwrap(response)
        return None

    return apply


# ============================================================================
# Plan builders — consume sub-payloads and emit ``list[ActionSpec]``.
# ============================================================================


def plan_creates[Payload: BaseModel](
    items: list[Payload] | None,
    operation: str,
    build_request: Callable[[Payload], Any],
    build_apply: Callable[[Any], ApplyCallable],
) -> list[ActionSpec]:
    """Build ActionSpecs for an ``add_*`` sub-payload.

    Args:
        items: The sub-payload list (or None).
        operation: Operation name (StrEnum value).
        build_request: ``Payload -> attrs request body`` (per-entity).
        build_apply: ``request_body -> ApplyCallable`` (per-entity).
    """
    if not items:
        return []
    return [
        make_create_action(operation, item, build_apply(build_request(item)))
        for item in items
    ]


async def plan_updates[Patch: BaseModel, Existing](
    patches: list[Patch] | None,
    operation: str,
    fetcher: Callable[[int], Awaitable[Existing | None]] | None,
    build_request: Callable[[Patch], Any],
    build_apply: Callable[[int, Any], ApplyCallable],
    *,
    target_id_attr: str = "id",
) -> list[ActionSpec]:
    """Build ActionSpecs for an ``update_*`` sub-payload.

    When ``fetcher`` is provided, prefetches the existing target for each
    patch via ``asyncio.gather`` (parallel) and computes a real diff. When
    ``fetcher`` is ``None``, every diff is marked ``is_unknown_prior=True``
    — used for resources without a get-by-id endpoint.

    Args:
        patches: The sub-payload list (or None).
        operation: Operation name (StrEnum value).
        fetcher: ``target_id -> Awaitable[existing | None]`` or ``None``.
        build_request: ``patch -> attrs request body``.
        build_apply: ``(target_id, body) -> ApplyCallable``.
        target_id_attr: Attribute on ``patch`` carrying the target id
            (default ``"id"``).
    """
    if not patches:
        return []

    target_ids = [getattr(p, target_id_attr) for p in patches]
    if fetcher is not None:
        existing_list = await asyncio.gather(*[fetcher(tid) for tid in target_ids])
    else:
        existing_list = [None] * len(patches)

    specs: list[ActionSpec] = []
    for patch, target_id, existing in zip(
        patches, target_ids, existing_list, strict=True
    ):
        diff = compute_field_diff(existing, patch, unknown_prior=existing is None)
        specs.append(
            ActionSpec(
                operation=operation,
                target_id=target_id,
                diff=diff,
                apply=build_apply(target_id, build_request(patch)),
                verify=make_response_verifier(diff),
            )
        )
    return specs


def plan_deletes(
    ids: list[int] | None,
    operation: str,
    build_apply: Callable[[int], ApplyCallable],
) -> list[ActionSpec]:
    """Build ActionSpecs for a ``delete_*_ids`` sub-payload."""
    if not ids:
        return []
    return [
        make_delete_action(operation, target_id, build_apply(target_id))
        for target_id in ids
    ]


# ============================================================================
# Response summary helpers — collapse the duplicated message + next_actions
# blocks at the end of every ``_modify_*_impl`` and ``_delete_*_impl``.
# ============================================================================


def summarize_modify_outcome(
    actions: list[ActionResult],
    plan_len: int,
    *,
    entity_label: str,
    tool_name: str,
) -> tuple[str, list[str]]:
    """Build (message, next_actions) for a multi-action modify result.

    ``entity_label`` is the human-readable noun (e.g. ``"purchase order 42"``).
    ``tool_name`` names the tool the caller would re-invoke for revert
    (e.g. ``"modify_purchase_order"``).
    """
    succeeded_count = sum(1 for a in actions if a.succeeded is True)
    failed_count = sum(1 for a in actions if a.succeeded is False)

    if failed_count > 0:
        message = (
            f"Partial: {succeeded_count}/{plan_len} action(s) applied to "
            f"{entity_label} before fail-fast halt; see actions for details "
            "and prior_state for revert reference."
        )
        next_actions = [
            f"{succeeded_count} action(s) succeeded; {failed_count} failed",
            "Review the FAILED action's error and the prior_state snapshot",
            f"Compose a follow-up {tool_name} call to revert if needed",
        ]
    else:
        message = (
            f"Successfully applied {succeeded_count}/{plan_len} action(s) "
            f"to {entity_label}"
        )
        next_actions = [
            f"{entity_label.capitalize()} modified — "
            f"{succeeded_count} action(s) verified"
        ]
    return message, next_actions


def summarize_delete_outcome(
    actions: list[ActionResult], *, entity_label: str
) -> tuple[str, list[str]]:
    """Build (message, next_actions) for a single-action delete result."""
    failed = any(a.succeeded is False for a in actions)
    if failed:
        message = f"Failed to delete {entity_label}"
        next_actions = [
            "Delete failed — see action error",
            "prior_state carries the pre-delete snapshot",
        ]
    else:
        message = f"Successfully deleted {entity_label}"
        next_actions = [f"{entity_label.capitalize()} has been deleted"]
    return message, next_actions


# ============================================================================
# Drivers — wrap the preview/confirm scaffolding so per-entity impls are
# left with just ``build the plan`` plus a couple of identifying strings.
# ============================================================================


async def run_modify_plan(
    *,
    request: Any,
    entity_type: str,
    entity_label: str,
    tool_name: str,
    web_url_kind: EntityKind | None,
    existing: Any | None,
    plan: list[ActionSpec],
    has_get_endpoint: bool = True,
) -> ModificationResponse:
    """Wrap a built plan in a preview-or-execute :class:`ModificationResponse`.

    The per-entity impl is responsible for the entity-specific bits:
    validating sub-payloads with a domain-friendly error message, fetching
    the existing entity, and assembling the plan list. Everything from
    "compute katana_url and warnings" through "summarize the outcome" lives
    here, identically across PO/SO/MO/etc.

    Args:
        request: The Pydantic request — must have ``id`` and ``confirm`` fields.
        entity_type: Stable machine-readable type tag (e.g. ``"purchase_order"``).
        entity_label: Human-readable label including the id (e.g. ``"purchase
            order 42"``). Used in messages and warnings.
        tool_name: Tool name for the manual-revert hint in the failure path
            (e.g. ``"modify_purchase_order"``).
        web_url_kind: Argument to :func:`katana_web_url`. Pass ``None`` for
            entities without a Katana web page (e.g. services); the response's
            ``katana_url`` will be ``None``.
        existing: The pre-fetched entity, or ``None`` on fetch failure.
            Drives ``prior_state`` capture and the diff-context warning.
        plan: Built ActionSpec list, in canonical order.
        has_get_endpoint: ``True`` when the entity exposes a GET-by-id endpoint
            and ``existing=None`` therefore signals a *fetch failure* worth
            warning about. ``False`` when the entity has no GET-by-id (e.g.
            stock transfer) and ``existing=None`` is the expected steady
            state — suppresses the spurious "could not fetch" warning.
    """
    katana_url = katana_web_url(web_url_kind, request.id) if web_url_kind else None
    warnings = (
        [
            f"Could not fetch {entity_label} for diff context — "
            "preview shows requested values without prior state."
        ]
        if existing is None and has_get_endpoint
        else []
    )

    if not request.confirm:
        return ModificationResponse(
            entity_type=entity_type,
            entity_id=request.id,
            is_preview=True,
            actions=plan_to_preview_results(plan),
            warnings=warnings,
            next_actions=[
                f"Review {len(plan)} planned action(s)",
                "Set confirm=true to execute the plan",
            ],
            katana_url=katana_url,
            message=f"Preview: {len(plan)} action(s) planned for {entity_label}",
        )

    prior_state = serialize_for_prior_state(existing)
    actions = await execute_plan(plan)
    message, next_actions = summarize_modify_outcome(
        actions, len(plan), entity_label=entity_label, tool_name=tool_name
    )

    return ModificationResponse(
        entity_type=entity_type,
        entity_id=request.id,
        is_preview=False,
        actions=actions,
        prior_state=prior_state,
        warnings=warnings,
        next_actions=next_actions,
        katana_url=katana_url,
        message=message,
    )


async def run_delete_plan(
    *,
    request: Any,
    services: Any,
    entity_type: str,
    entity_label: str,
    web_url_kind: EntityKind | None,
    fetcher: Callable[[Any, int], Awaitable[Any | None]],
    delete_endpoint: Any,
    operation: str,
) -> ModificationResponse:
    """Single-action delete driver — used by every ``delete_<entity>`` tool.

    Captures prior_state, runs a one-action plan, and returns the
    ModificationResponse. Katana cascades child deletes server-side.

    Args:
        request: The Pydantic request — needs ``id`` and ``confirm``.
        services: Result of ``get_services(context)``.
        entity_type: Machine tag (e.g. ``"purchase_order"``). The
            human-readable noun ("purchase order") is derived by replacing
            ``_`` with `` `` for the preview message.
        entity_label: Human-readable with id (e.g. ``"purchase order 42"``).
        web_url_kind: ``katana_web_url`` argument. Pass ``None`` for entities
            without a Katana web page (e.g. services).
        fetcher: ``(services, id) -> Awaitable[entity | None]`` — for
            prior_state capture.
        delete_endpoint: The generated client's DELETE module (e.g.
            ``api_delete_purchase_order``).
        operation: Operation name for the ActionSpec (typically the entity's
            ``Operation.DELETE`` enum value).
    """
    existing = await fetcher(services, request.id)
    plan = plan_deletes(
        [request.id],
        operation,
        lambda eid: make_delete_apply(delete_endpoint, services, eid),
    )
    katana_url = katana_web_url(web_url_kind, request.id) if web_url_kind else None

    if not request.confirm:
        return ModificationResponse(
            entity_type=entity_type,
            entity_id=request.id,
            is_preview=True,
            actions=plan_to_preview_results(plan),
            next_actions=[
                "Review the deletion",
                f"Set confirm=true to delete the {entity_type.replace('_', ' ')}",
            ],
            katana_url=katana_url,
            message=f"Preview: delete {entity_label}",
        )

    prior_state = serialize_for_prior_state(existing)
    actions = await execute_plan(plan)
    message, next_actions = summarize_delete_outcome(actions, entity_label=entity_label)

    return ModificationResponse(
        entity_type=entity_type,
        entity_id=request.id,
        is_preview=False,
        actions=actions,
        prior_state=prior_state,
        next_actions=next_actions,
        # On successful delete the entity URL no longer resolves.
        katana_url=None if all(a.succeeded for a in actions) else katana_url,
        message=message,
    )


def serialize_for_prior_state(value: Any) -> dict[str, Any] | None:
    """Best-effort serialization of an attrs/pydantic entity for prior_state.

    Tries ``.to_dict()`` (attrs) first, then ``.model_dump()`` (pydantic),
    falling back to ``None`` for values we can't serialize. The resulting
    dict goes into :attr:`ModificationResponse.prior_state` so the caller
    has the pre-modification snapshot for manual revert.
    """
    if value is None:
        return None
    if hasattr(value, "to_dict"):
        try:
            return dict(value.to_dict())
        except Exception:
            pass
    if hasattr(value, "model_dump"):
        try:
            return dict(value.model_dump())
        except Exception:
            pass
    return None
