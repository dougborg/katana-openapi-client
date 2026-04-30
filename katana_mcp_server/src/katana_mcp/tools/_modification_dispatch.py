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

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel

from katana_mcp.logging import get_logger
from katana_mcp.tools._modification import (
    ActionResult,
    FieldChange,
    compute_field_diff,
    make_response_verifier,
)

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
