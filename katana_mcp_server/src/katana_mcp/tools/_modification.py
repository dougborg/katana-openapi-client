"""Shared infrastructure for entity-modification MCP tools.

Provides a uniform Pydantic response model + helpers for consistent
preview/apply UX across modification tools (PO, SO, MO, ...).

A modification tool follows this shape:

1. Build a request Pydantic model with ``preview: bool = True`` and the
   fields to modify (all ``Optional`` for PATCH-style operations).
2. In the impl, optionally fetch the existing entity for diff context, then
   compute a list of :class:`FieldChange` via :func:`compute_field_diff`.
3. If ``preview=True`` return :class:`ModificationResponse` with
   ``is_preview=True``.
4. If ``preview=False`` call the API, then return
   :class:`ModificationResponse` with ``is_preview=False``.

Use :func:`render_modification_md` (or :func:`to_tool_result`) to produce the
markdown for the :class:`ToolResult` content. Markdown rendering is the only
output channel today; Prefab UI for diff visualization can layer on later by
operating on the same response model.
"""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable, Iterable
from datetime import datetime
from enum import Enum
from typing import Any, ClassVar

from fastmcp.tools import ToolResult
from pydantic import BaseModel, ConfigDict, Field

from katana_mcp.tools.tool_result_utils import BLOCK_WARNING_PREFIX, make_simple_result
from katana_public_api_client.client_types import UNSET, Unset
from katana_public_api_client.domain.converters import unwrap_unset


def patch_additional_info(
    caller_value: str | None,
    existing_value: str | None | Unset,
) -> str | Unset:
    """Decide ``additional_info`` for a Katana PATCH body.

    Workaround for the platform's wipe-on-omit asymmetry: Katana clears
    ``additional_info`` to ``""`` whenever the field is omitted from the
    PATCH body, while every other omitted field is preserved. Confirmed
    across PO/Material/Product/MO/StockAdjustment — see #505 and
    ``docs/KATANA_API_QUESTIONS.md`` §6.2.

    Returns:
        - ``caller_value`` when the caller supplied one (their write wins)
        - ``existing_value`` (unwrapped) when caller didn't and existing
          is non-empty (echo to defeat the wipe)
        - ``UNSET`` otherwise (no echo needed; nothing to preserve)

    The ``UNSET`` return is the same as not setting the field on the
    attrs request, so callers can unconditionally pass the result via
    ``additional_info=patch_additional_info(...)``.
    """
    if caller_value is not None:
        return caller_value
    existing = unwrap_unset(existing_value, None)
    return existing if existing else UNSET


class ConfirmableRequest(BaseModel):
    """Base for top-level ``Modify<Entity>Request`` and ``Delete<Entity>Request``
    Pydantic models. Carries the primary entity ``id`` and the ``preview``
    field used by every modification tool's preview/apply gate. Subclasses
    add their entity-specific sub-payload slots and override ``id``'s
    description with an entity-appropriate label.

    ``extra="forbid"`` is set here so direct Python construction (tests,
    internal ``_impl`` callers) catches typos like ``previw=False``. MCP
    protocol traffic is already protected by FastMCP's TypeAdapter against
    the function signature — this config does not fire there because
    ``unpack_pydantic_params`` strips unknown top-level kwargs before
    construction (see ``katana_mcp/unpack.py``). The load-bearing
    ``extra="forbid"`` for catching wire-level silent drops lives on the
    nested sub-payload models (``*Patch``, ``*Add``, ``*Update``, ``*Input``).
    """

    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., description="Entity ID")
    preview: bool = Field(
        default=True,
        description=(
            "If true (default), returns a preview with planned actions. "
            "If false, executes the action plan."
        ),
    )


class FieldChange(BaseModel):
    """A single field-level change in a modification preview/result.

    Exactly one of ``is_added`` / ``is_unchanged`` / ``is_unknown_prior``
    is true, or all three are false (in which case the field's value is
    being replaced with a different non-null value).

    ``is_unknown_prior`` is distinct from ``is_added``: ``is_added`` means
    "the entity didn't have this field set before" (genuine create), while
    ``is_unknown_prior`` means "we couldn't determine the prior state"
    (best-effort fetch failed). Renderers should make the distinction
    visible — implying a field was empty when we just don't know is
    misleading.

    There is no "cleared" / ``is_removed`` flag: the diff source iterates
    ``request.model_dump(exclude_none=True)``, so fields explicitly set to
    ``None`` are skipped. Update tools translate request-side ``None`` to
    UNSET via ``to_unset`` before serializing the PATCH, which omits the
    field from the body — so "set to null to clear" isn't a behavior we
    expose today. If a Katana endpoint ever needs explicit clears, add an
    ``unset_fields: list[str]`` companion alongside the patch body and a
    matching ``is_cleared`` here.
    """

    field: str
    old: Any | None = None
    new: Any | None = None
    is_added: bool = False
    is_unchanged: bool = False
    is_unknown_prior: bool = False


class ActionResult(BaseModel):
    """Per-action result block on a multi-action modification call.

    Populated for each :class:`ActionSpec` in an action plan executed by
    :func:`katana_mcp.tools._modification_dispatch.execute_plan`. Used by
    the unified ``modify_<entity>`` tools to report on each sub-payload's
    outcome independently.

    Three states:

    - **Preview** (``preview=True`` on the parent request): ``succeeded``
      and ``verified`` are both ``None`` — the action hasn't been executed,
      only planned. ``changes`` carries the diff that *would* be applied.
    - **Confirmed success**: ``succeeded=True``. ``verified`` may be
      ``True`` (post-action re-fetch confirmed the change), ``False``
      (re-fetch showed a different value — silent server-side rejection
      or race), or ``None`` (no verification was registered for this
      action).
    - **Confirmed failure**: ``succeeded=False``, ``error`` populated.
      Subsequent actions in the plan are not attempted (fail-fast).
    """

    operation: str
    target_id: int | None = None
    changes: list[FieldChange] = Field(default_factory=list)
    succeeded: bool | None = None
    error: str | None = None
    verified: bool | None = None
    actual_after: dict[str, Any] | None = None


class ModificationResponse(BaseModel):
    """Uniform response for every modification tool.

    Two shapes coexist:

    - **Single-action** (legacy, kept for the few non-unified tools that
      still return one operation per call): ``operation`` and ``changes``
      are populated; ``actions`` is empty.
    - **Multi-action** (the unified ``modify_<entity>`` tools): ``actions``
      is a list of :class:`ActionResult` and ``operation``/``changes`` are
      left at their defaults. ``prior_state`` is populated on the apply
      branch so the caller can manually revert if needed.

    The renderer (:func:`render_modification_md`) checks which shape is in
    use and emits markdown accordingly. New tools should always populate
    ``actions``.
    """

    entity_type: str
    entity_id: int | None = None
    parent_entity_id: int | None = None
    is_preview: bool
    operation: str = ""
    changes: list[FieldChange] = Field(default_factory=list)
    actions: list[ActionResult] = Field(default_factory=list)
    prior_state: dict[str, Any] | None = None
    warnings: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    katana_url: str | None = None
    message: str

    DEFAULT_EXCLUDED: ClassVar[tuple[str, ...]] = ("id", "preview")


def _normalize(value: Any) -> Any:
    """Normalize a value for diff comparison.

    UNSET sentinels collapse to ``None``; datetimes flatten to ISO strings;
    enums to their wire value. Lists and dicts are returned as-is — the
    caller is responsible for upstream comparability.
    """
    if value is UNSET:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    return value


def compute_field_diff(
    existing: Any,
    request: BaseModel,
    *,
    field_map: dict[str, str] | None = None,
    exclude: Iterable[str] = ModificationResponse.DEFAULT_EXCLUDED,
    unknown_prior: bool = False,
) -> list[FieldChange]:
    """Compute :class:`FieldChange` entries for fields the request will set.

    Iterates ``request.model_dump(exclude_none=True)`` so only fields the
    caller provided contribute to the diff. For each, the matching attr on
    ``existing`` is fetched (via ``unwrap_unset`` so attrs UNSET sentinels
    behave as ``None``) and compared after :func:`_normalize`.

    Args:
        existing: Existing entity (attrs or pydantic). When ``None`` and
            ``unknown_prior`` is False, every field is reported as
            ``is_added`` (preview before fetch — genuine create).
        request: Pydantic request model. None-valued fields are skipped so
            partial updates only diff the fields the user touched.
        field_map: Optional ``request_field -> entity_attr`` rename map for
            fields that don't share names across the layers.
        exclude: Field names on the request to skip (defaults to ``id`` and
            ``preview``).
        unknown_prior: When True, ``existing`` being ``None`` represents a
            failed best-effort fetch (the entity exists, we just couldn't
            read it). Each change is then marked ``is_unknown_prior`` so
            the rendering layer can show "(prior unknown) → new" instead
            of implying the prior value was empty. Mutually exclusive with
            a non-None ``existing`` — if the fetch succeeded, this flag is
            ignored.
    """
    field_map = field_map or {}
    exclude_set = set(exclude)
    changes: list[FieldChange] = []
    treat_as_unknown = existing is None and unknown_prior
    # ``exclude_none=True`` skips fields the caller didn't supply, which is
    # what we want for partial updates — the diff only covers fields the user
    # actually intends to set. The trade-off is we can't represent "explicit
    # clear" here; see FieldChange's docstring.
    for name, value in request.model_dump(exclude_none=True).items():
        if name in exclude_set:
            continue
        attr_name = field_map.get(name, name)
        old: Any = None
        if existing is not None:
            raw = getattr(existing, attr_name, UNSET)
            old = _normalize(unwrap_unset(raw, None))
        new = _normalize(value)
        if treat_as_unknown:
            changes.append(
                FieldChange(field=name, old=None, new=new, is_unknown_prior=True)
            )
        elif old == new:
            changes.append(FieldChange(field=name, old=old, new=new, is_unchanged=True))
        elif old is None:
            changes.append(FieldChange(field=name, old=None, new=new, is_added=True))
        else:
            changes.append(FieldChange(field=name, old=old, new=new))
    return changes


def make_response_verifier(
    diff: list[FieldChange], *, field_map: dict[str, str] | None = None
) -> Callable[[Any], Awaitable[tuple[bool, dict[str, Any] | None]]]:
    """Build a verify closure that checks the API response body against ``diff``.

    Most Katana mutation endpoints echo the post-state of the affected
    entity in the response body — this verifier reads each requested
    field off ``outcome`` and confirms it matches the requested ``new``
    value. No extra fetch needed. ``field_map`` mirrors the
    :func:`compute_field_diff` parameter for fields with names that
    differ between request and response. Used by every
    ``modify_<entity>`` update action's ``ActionSpec.verify``.
    """
    name_map = field_map or {}

    async def verify(outcome: Any) -> tuple[bool, dict[str, Any] | None]:
        if outcome is None:
            return False, None
        actual: dict[str, Any] = {}
        verified = True
        for change in diff:
            attr = name_map.get(change.field, change.field)
            raw = getattr(outcome, attr, None)
            actual_val = _normalize(unwrap_unset(raw, None))
            actual[change.field] = actual_val
            if change.new is not None and actual_val != change.new:
                verified = False
        return verified, (actual if not verified else None)

    return verify


def _render_changes_block(changes: list[FieldChange]) -> list[str]:
    """Render a flat list of field changes as markdown bullet lines."""
    lines: list[str] = []
    for change in changes:
        if change.is_unchanged:
            lines.append(f"- `{change.field}`: (unchanged) {change.new}")
        elif change.is_unknown_prior:
            lines.append(f"- `{change.field}`: (prior unknown) → {change.new}")
        elif change.is_added:
            lines.append(f"- `{change.field}`: (set) → {change.new}")
        else:
            lines.append(f"- `{change.field}`: {change.old} → {change.new}")
    return lines


def _render_action_block(idx: int, action: ActionResult) -> list[str]:
    """Render one action's status + diff as a markdown sub-section."""
    op_title = action.operation.replace("_", " ").title()
    target = f" #{action.target_id}" if action.target_id is not None else ""
    if action.succeeded is None:
        status = "PLANNED"
    elif action.succeeded is True:
        if action.verified is False:
            status = "APPLIED (verification mismatch)"
        elif action.verified is None:
            status = "APPLIED"
        else:
            status = "APPLIED (verified)"
    else:
        status = "FAILED"

    lines = [f"#### {idx}. {op_title}{target} — {status}"]
    if action.error:
        lines.append(f"- **Error**: {action.error}")
    if action.changes:
        lines.extend(_render_changes_block(action.changes))
    if action.actual_after is not None and action.verified is False:
        # Surface the actual-vs-requested mismatch so the caller can act
        lines.append(f"- **Actual after verification**: `{action.actual_after}`")
    return lines


def render_modification_md(response: ModificationResponse) -> str:
    """Render a :class:`ModificationResponse` as the markdown content body.

    Handles both the legacy single-action shape (``operation`` + ``changes``)
    and the multi-action shape (``actions``). When ``actions`` is non-empty,
    that takes precedence and each action gets its own sub-section.
    """
    entity_title = response.entity_type.replace("_", " ").title()

    if response.actions:
        state_label = "PREVIEW" if response.is_preview else "APPLIED"
        n = len(response.actions)
        plural = "action" if n == 1 else "actions"
        lines = [f"## Modify {entity_title} ({state_label}) — {n} {plural}"]
    else:
        op_title = response.operation.replace("_", " ").title()
        state_label = "PREVIEW" if response.is_preview else op_title.upper()
        lines = [f"## {entity_title} {op_title} ({state_label})"]

    if response.entity_id is not None:
        lines.append(f"- **ID**: {response.entity_id}")
    if response.parent_entity_id is not None:
        lines.append(f"- **Parent ID**: {response.parent_entity_id}")
    lines.append(f"- **Message**: {response.message}")
    if response.katana_url:
        lines.append(f"- **Katana URL**: {response.katana_url}")

    # Multi-action: per-action sections
    if response.actions:
        lines.append("")
        lines.append("### Actions")
        for idx, action in enumerate(response.actions, start=1):
            lines.append("")
            lines.extend(_render_action_block(idx, action))
    # Legacy single-action: top-level changes block
    elif response.changes:
        lines.append("")
        lines.append("### Changes")
        lines.extend(_render_changes_block(response.changes))

    if response.prior_state is not None:
        lines.append("")
        if response.is_preview:
            lines.append("### Current State (preview snapshot)")
            lines.append(
                "Snapshot of the entity in its current state — verify this is "
                "the right target before setting `preview=false` to apply."
            )
        else:
            lines.append("### Prior State (for manual revert)")
            lines.append(
                "Snapshot of pre-modification entity captured before applying. "
                "Pass these values back through a follow-up modify call to revert "
                "if needed — Katana's API is not transactional, so verify each "
                "field manually."
            )
        lines.append("")
        lines.append("```json")
        # ``default=str`` collapses datetime / Enum / Decimal sentinels to
        # strings so the snapshot serializes deterministically. The dict is
        # already pre-serialized via ``serialize_for_prior_state``; this is
        # a belt-and-suspenders for any remaining non-JSON-native values.
        lines.append(json.dumps(response.prior_state, indent=2, default=str))
        lines.append("```")

    if response.warnings:
        lines.append("")
        lines.append("### Warnings")
        for w in response.warnings:
            is_block = w.startswith(BLOCK_WARNING_PREFIX)
            display = w.removeprefix(BLOCK_WARNING_PREFIX).lstrip() if is_block else w
            prefix = "**[BLOCKED]** " if is_block else ""
            lines.append(f"- {prefix}{display}")

    if response.next_actions:
        lines.append("")
        lines.append("### Next Actions")
        lines.extend(f"- {a}" for a in response.next_actions)

    return "\n".join(lines)


def to_tool_result(response: ModificationResponse) -> ToolResult:
    """Build a :class:`ToolResult` from a :class:`ModificationResponse`."""
    return make_simple_result(
        render_modification_md(response),
        structured_data=response.model_dump(),
    )
