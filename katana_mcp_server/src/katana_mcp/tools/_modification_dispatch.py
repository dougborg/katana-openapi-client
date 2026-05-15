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
4. **Preview branch** (``preview=True``): wrap the plan in
   :class:`ActionResult` entries with ``succeeded=None`` (planned, not run)
   and return the :class:`ModificationResponse`.
5. **Apply branch** (``preview=False``): call :func:`execute_plan` to run
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
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

if TYPE_CHECKING:
    # ``TypedCacheEngine`` is the runtime type of ``CacheMerge.cache``.
    # Top-level import would cycle through tool code; the ``TYPE_CHECKING``
    # guard keeps IDE / pyright accurate without runtime overhead.
    from katana_mcp.typed_cache import TypedCacheEngine

from katana_mcp.logging import get_logger
from katana_mcp.tools._derived_fields import (
    DERIVED_FIELDS,
    check_derived_fields,
)
from katana_mcp.tools._modification import (
    ActionResult,
    ConfirmableRequest,
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


@dataclass(frozen=True)
class EntityNaming:
    """Entity-identifying strings used by ``run_modify_plan``.

    Bundled into one record to keep ``run_modify_plan`` under its
    8-argument PLR0913 budget after ``cache_merge`` was added. The three
    strings move together — every per-tool impl computes them at the same
    time. ``run_delete_plan`` was deliberately left with flat kwargs —
    it doesn't take ``cache_merge`` so it stays under budget without the
    bundle; a future migration for consistency is tracked separately.

    - ``entity_type``: stable machine-readable tag (matches a key in
      ``ENTITY_SPECS`` when the entity is cached). Used for the cache
      merge spec lookup and as the response's ``entity_type`` field.
    - ``entity_label``: human-readable noun including the id
      (e.g. ``"purchase order 42"``). Used in messages and warnings.
    - ``tool_name``: the calling tool's name (e.g.
      ``"modify_purchase_order"``). Used in the manual-revert hint in
      failure messages.
    """

    entity_type: str
    entity_label: str
    tool_name: str


@dataclass(frozen=True)
class CacheMerge:
    """Plumbing for end-of-plan typed-cache write-through.

    Before this hook existed, ``run_modify_plan`` had no cache awareness —
    every successful modify left the typed cache stale until the next sync
    (2026-05-12 supplier PO-reconciliation session, where ``get_variant_details``
    returned pre-modification ``supplier_item_codes`` 10+ minutes after a
    confirmed apply). With ``cache_merge`` wired, ``run_modify_plan``
    re-fetches the parent entity after the plan succeeds and merges it into
    the cache via ``merge_filtered_fetch`` — which does not advance the
    watermark, see ``typed_cache/sync.py:536``. The same refetch naturally
    captures server-side cascades (e.g. PO header ``expected_arrival_date``
    → row ``arrival_date`` cascade).

    Fields:

    - ``cache`` — the ``TypedCacheEngine`` from ``services.typed_cache``.
      Imported under ``TYPE_CHECKING`` to avoid a top-level import cycle
      through tool code; the annotation resolves at type-check time.
    - ``refetch_for_merge(id)`` — returns the post-state parent attrs.
      ``merge_filtered_fetch`` only writes through what the parent's
      ``EntitySpec`` knows about: the parent row itself plus any nested
      children declared via ``child_cls`` / ``rows_field`` (PO/SO rows are
      embedded). Anything the spec lists in ``related_specs`` (separate
      endpoints — MO recipe rows, PO/SO sibling row-watermarks) is NOT
      covered by this single fetch.
    - ``refetch_related`` — optional list of ``(entity_key, refetcher)``
      tuples for any ``related_specs`` that need their own refetch after
      a modify. Currently used by ``modify_manufacturing_order`` to
      refresh recipe rows (separate ``/manufacturing_order_recipe_rows``
      endpoint, not embedded in the MO GET response). Each refetcher
      takes the parent entity id and returns the list of related-spec
      attrs to merge.

    Tools that lack a GET-by-id endpoint (stock_transfers) simply omit
    ``cache_merge`` entirely — their cache stays stale on modify until
    the next sync window.
    """

    cache: TypedCacheEngine
    refetch_for_merge: Callable[[int], Awaitable[Any | None]]
    refetch_related: tuple[tuple[str, Callable[[int], Awaitable[list[Any]]]], ...] = ()


@dataclass
class ActionSpec:
    """A single planned action — preview metadata + execution closures.

    Constructed by per-entity tool code; consumed by :func:`execute_plan`.
    """

    operation: str
    target_id: int | str | None
    diff: list[FieldChange] = field(default_factory=list)
    apply: ApplyCallable | None = None
    verify: VerifyCallable | None = None

    def to_planned_result(self, index: int = 0) -> ActionResult:
        """Build an ActionResult for the preview branch (action not yet run).

        ``index`` is the 1-based position in the plan — used by the Prefab
        card's ``#`` column. The dispatcher passes a real index when
        constructing the list; default 0 is for direct unit-test calls.
        """
        return ActionResult(
            index=index,
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

    for idx, spec in enumerate(plan, start=1):
        if spec.apply is None:
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
                    index=idx,
                    operation=spec.operation,
                    target_id=spec.target_id,
                    changes=list(spec.diff),
                    succeeded=False,
                    error=f"{type(exc).__name__}: {exc}",
                )
            )
            return results

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
                index=idx,
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

    Used by the preview branch (``preview=True``) where no API calls run.
    Each ActionResult carries the operation/target/diff but
    ``succeeded=None`` to signal "planned, not yet executed".
    """
    return [spec.to_planned_result(index=idx) for idx, spec in enumerate(plan, start=1)]


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
    request: BaseModel,
    *,
    exclude: tuple[str, ...] = ModificationResponse.DEFAULT_EXCLUDED,
) -> bool:
    """True if the request has any sub-payload set (any field outside ``exclude``).

    Generic across every ``modify_<entity>`` tool — each has a top-level
    request with a primary id, ``preview``, and a set of optional
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
    exclude: tuple[str, ...] = ("preview",),
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
    exclude: tuple[str, ...] = ("id", "preview"),
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
        return unwrap_as(response, return_type)

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
        return unwrap_as(response, return_type)

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
        verified_count = sum(1 for a in actions if a.verified is True)
        message = (
            f"Successfully applied {succeeded_count}/{plan_len} action(s) "
            f"to {entity_label}"
        )
        next_action = f"{entity_label.capitalize()} modified — {succeeded_count} action(s) applied"
        if verified_count != succeeded_count:
            # Some actions either skipped verify (verifier=None) or post-action
            # re-fetch reported a mismatch (verified=False). Surface the gap so
            # callers know not every applied action was confirmed end-to-end.
            next_action += f" ({verified_count} verified)"
        next_actions = [next_action]
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
# Drivers — wrap the preview/apply scaffolding so per-entity impls are
# left with just ``build the plan`` plus a couple of identifying strings.
# ============================================================================


async def run_modify_plan(
    *,
    request: ConfirmableRequest,
    naming: EntityNaming,
    web_url_kind: EntityKind | None,
    existing: Any | None,
    plan: list[ActionSpec],
    has_get_endpoint: bool = True,
    cache_merge: CacheMerge | None = None,
) -> ModificationResponse:
    """Wrap a built plan in a preview-or-execute :class:`ModificationResponse`.

    The per-entity impl is responsible for the entity-specific bits:
    validating sub-payloads with a domain-friendly error message, fetching
    the existing entity, and assembling the plan list. Everything from
    "compute katana_url and warnings" through "summarize the outcome" lives
    here, identically across PO/SO/MO/etc.

    Args:
        request: The Pydantic request — must have ``id`` and ``preview`` fields.
        naming: ``EntityNaming(entity_type, entity_label, tool_name)`` — see
            its docstring for what each field carries.
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
        cache_merge: When provided, the dispatcher refetches the parent
            after the plan succeeds and merges it into the typed cache so
            ``@cache_read`` tools see fresh data without ``rebuild_cache``.
            Omit for tools without a GET-by-id (stock_transfers) — the
            cache stays stale on modify until the next sync window.
    """
    entity_type = naming.entity_type
    entity_label = naming.entity_label
    tool_name = naming.tool_name
    katana_url = katana_web_url(web_url_kind, request.id) if web_url_kind else None
    warnings = (
        [
            f"Could not fetch {entity_label} for diff context — "
            "preview shows requested values without prior state."
        ]
        if existing is None and has_get_endpoint
        else []
    )

    # Reject server-computed (derived) fields before plan execution. Fires
    # for both preview and apply paths so the caller sees the error
    # immediately, not after a partial plan applies. See
    # ``katana_mcp.tools._derived_fields`` for registry semantics.
    for spec in plan:
        check_derived_fields(
            entity_type=entity_type,
            operation=spec.operation,
            target_id=spec.target_id,
            diff=spec.diff,
        )

    # Reject update-style ActionSpecs with empty diffs. With ``extra="forbid"``
    # on patch models (#487), unknown fields raise ``ValidationError`` at
    # construction and never reach this point. The remaining cause for an
    # empty diff is: the caller supplied only the target ``id`` (and possibly
    # only derived fields, which the prior ``check_derived_fields`` step
    # rejects with a clearer error). Without this guard, Katana returns a
    # generic "At least 1 field is required" 422 that's hard to map back to
    # the original input. Adds and deletes are exempt: adds carry a non-empty
    # diff by construction (required fields), and deletes have empty diffs
    # by design.
    for spec in plan:
        if not spec.operation.startswith("update_"):
            continue
        if spec.diff:
            continue
        derived_for_op = DERIVED_FIELDS.get(entity_type, {}).get(spec.operation, {})
        target = f" (target {spec.target_id})" if spec.target_id is not None else ""
        msg = (
            f"No fields to update for {entity_type} {spec.operation}{target} — "
            f"the patch payload would be empty. Provide at least one patchable "
            f"field on the sub-payload, or omit this operation."
        )
        if derived_for_op:
            derived_names = ", ".join(sorted(derived_for_op))
            msg = (
                f"{msg} Derived fields registered on this operation "
                f"(rejected by the API on update): {derived_names}."
            )
        raise ValueError(msg)

    # ``prior_state`` populated on BOTH branches: apply path uses it for
    # the revert reference; preview path uses it for renderer-side entity
    # view (the modify-card design in #721 wants the unchanged header /
    # reference fields to render as context around the diff-decorated
    # changing fields — without prior_state, the card would show only the
    # changed fields and a mostly-empty header). ``existing`` may be None
    # if the diff fetch failed; ``serialize_for_prior_state`` tolerates
    # that and returns ``None`` so the renderer sees no snapshot.
    prior_state = serialize_for_prior_state(existing)

    if request.preview:
        return ModificationResponse(
            entity_type=entity_type,
            entity_id=request.id,
            is_preview=True,
            actions=plan_to_preview_results(plan),
            prior_state=prior_state,
            warnings=warnings,
            next_actions=[
                f"Review {len(plan)} planned action(s)",
                "Set preview=false to execute the plan",
            ],
            katana_url=katana_url,
            message=f"Preview: {len(plan)} action(s) planned for {entity_label}",
        )

    actions = await execute_plan(plan)
    message, next_actions = summarize_modify_outcome(
        actions, len(plan), entity_label=entity_label, tool_name=tool_name
    )

    # Bug #2 (2026-05-12 supplier session): the typed cache went stale after
    # every modify because nothing wrote the post-state through. The next
    # ``@cache_read`` (e.g. ``get_variant_details``, ``list_purchase_orders``)
    # served pre-modification rows until a manual ``rebuild_cache`` ran.
    #
    # When the tool wires up ``cache`` + ``refetch_for_merge``, do a single
    # post-apply parent fetch and merge it into the cache via the existing
    # ``merge_filtered_fetch`` helper. The same fetch naturally captures
    # server-side cascades (Bug #5 header-date → row-dates) — the cache
    # reflects what Katana actually has, not what the agent thinks it has.
    #
    # Best-effort: failures are logged but do not change the tool's success
    # response — the API write itself succeeded; cache staleness is
    # recoverable on the next ensure_synced cycle.
    if (
        cache_merge is not None
        and actions
        and not any(a.succeeded is False for a in actions)
    ):
        try:
            await _post_apply_cache_merge(
                cache_merge=cache_merge,
                entity_type=entity_type,
                entity_id=request.id,
            )
        except asyncio.CancelledError:
            # Cooperative cancellation (request timeout, shutdown) must
            # propagate — never swallow it in the best-effort handler.
            raise
        except Exception as exc:
            logger.warning(
                f"Post-apply cache merge for {entity_label} failed: "
                f"{type(exc).__name__}: {exc}. Cache may be stale until "
                f"next sync — does not affect the API write."
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


async def _post_apply_cache_merge(
    *,
    cache_merge: CacheMerge,
    entity_type: str,
    entity_id: int,
) -> None:
    """Re-fetch the modified entity from Katana and merge into the typed cache.

    Looks up the ``EntitySpec`` by ``entity_type`` in ``ENTITY_SPECS`` —
    entity types that aren't cached (no spec) skip silently. Returns
    quietly if the parent refetch yields no entity (deleted, race, etc.).

    For entities whose ``EntitySpec.related_specs`` reference data at
    separate API endpoints (MO recipe rows, sibling row-watermarks), the
    caller must wire ``CacheMerge.refetch_related`` to refresh those too
    — the parent fetch alone doesn't cover them. See
    ``CacheMerge.refetch_related`` for the contract.
    """
    # Late import: ``typed_cache`` imports the API client which imports
    # tool code in a few places — top-level import would loop. The
    # function-level import resolves the cycle cleanly.
    from katana_mcp.typed_cache.sync import ENTITY_SPECS, merge_filtered_fetch

    spec = ENTITY_SPECS.get(entity_type)
    if spec is None:
        return  # entity not cached — nothing to merge

    parent = await cache_merge.refetch_for_merge(entity_id)
    if parent is None:
        return  # fetch returned nothing (e.g., the entity was deleted)

    await merge_filtered_fetch(cache_merge.cache, spec, [parent])

    # Fan out to related-spec refetches for entities whose children live
    # at separate API endpoints (MO recipe rows; PO/SO sibling row-
    # watermarks). Look up via the parent spec's ``related_specs`` —
    # sibling row specs are NOT keyed in the top-level ``ENTITY_SPECS``
    # registry (that one is for top-level entity types only). Each
    # related refetcher is awaited independently — a failure on one
    # doesn't block the others, and the parent merge above already
    # succeeded.
    related_by_key = {rs.entity_key: rs for rs in spec.related_specs}
    for related_key, refetcher in cache_merge.refetch_related:
        related_spec = related_by_key.get(related_key)
        if related_spec is None:
            logger.warning(
                f"CacheMerge.refetch_related references {related_key!r} but "
                f"it isn't in {entity_type!r}'s related_specs — skipping. "
                f"Tool wiring is misconfigured."
            )
            continue
        try:
            related_rows = await refetcher(entity_id)
        except asyncio.CancelledError:
            # Propagate cancellation — see the outer handler's note.
            raise
        except Exception as exc:
            logger.warning(
                f"Refetch of related {related_key!r} for {entity_type} "
                f"{entity_id} failed: {type(exc).__name__}: {exc}. "
                f"Related cache table may be stale until next sync."
            )
            continue
        if related_rows:
            await merge_filtered_fetch(cache_merge.cache, related_spec, related_rows)


async def run_delete_plan(
    *,
    request: ConfirmableRequest,
    services: Any,
    entity_type: str,
    entity_label: str,
    web_url_kind: EntityKind | None,
    fetcher: Callable[[Any, int], Awaitable[Any | None]] | None,
    delete_endpoint: Any,
    operation: str,
) -> ModificationResponse:
    """Single-action delete driver — used by every ``delete_<entity>`` tool.

    Captures prior_state, runs a one-action plan, and returns the
    ModificationResponse. Katana cascades child deletes server-side.

    Args:
        request: The Pydantic request — needs ``id`` and ``preview``.
        services: Result of ``get_services(context)``.
        entity_type: Machine tag (e.g. ``"purchase_order"``). The
            human-readable noun ("purchase order") is derived by replacing
            ``_`` with `` `` for the preview message.
        entity_label: Human-readable with id (e.g. ``"purchase order 42"``).
        web_url_kind: ``katana_web_url`` argument. Pass ``None`` for entities
            without a Katana web page (e.g. services).
        fetcher: ``(services, id) -> Awaitable[entity | None]`` for
            prior_state capture, or ``None`` for entities with no GET-by-id
            endpoint (stock transfer) — ``prior_state`` will be ``None``.
        delete_endpoint: The generated client's DELETE module (e.g.
            ``api_delete_purchase_order``).
        operation: Operation name for the ActionSpec (typically the entity's
            ``Operation.DELETE`` enum value).
    """
    existing = await fetcher(services, request.id) if fetcher is not None else None
    prior_state = serialize_for_prior_state(existing)
    plan = plan_deletes(
        [request.id],
        operation,
        lambda eid: make_delete_apply(delete_endpoint, services, eid),
    )
    katana_url = katana_web_url(web_url_kind, request.id) if web_url_kind else None

    if request.preview:
        # Populate prior_state on the preview path so the rendered markdown
        # shows callers a snapshot of what they're about to delete — gives
        # them a chance to verify they targeted the right entity before
        # applying. The fetch is already best-effort: per-entity fetchers
        # wrap ``safe_fetch_for_diff`` which swallows errors to ``None``,
        # so a failed fetch leaves prior_state=None and the preview still
        # renders without raising.
        return ModificationResponse(
            entity_type=entity_type,
            entity_id=request.id,
            is_preview=True,
            actions=plan_to_preview_results(plan),
            prior_state=prior_state,
            next_actions=[
                "Review the deletion",
                f"Set preview=false to delete the {entity_type.replace('_', ' ')}",
            ],
            katana_url=katana_url,
            message=f"Preview: delete {entity_label}",
        )

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
        except Exception as exc:
            logger.info(
                f"prior_state to_dict serialization failed for {type(value).__name__}: "
                f"{type(exc).__name__}: {exc} — falling back to model_dump"
            )
    if hasattr(value, "model_dump"):
        try:
            return dict(value.model_dump())
        except Exception as exc:
            logger.info(
                f"prior_state model_dump serialization failed for {type(value).__name__}: "
                f"{type(exc).__name__}: {exc} — prior_state will be None"
            )
    return None
