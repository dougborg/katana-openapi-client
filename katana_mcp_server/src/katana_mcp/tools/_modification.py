"""Shared infrastructure for entity-modification MCP tools.

Provides a uniform Pydantic response model + helpers for consistent
preview/confirm UX across modification tools (PO, SO, MO, ...).

A modification tool follows this shape:

1. Build a request Pydantic model with ``confirm: bool = False`` and the
   fields to modify (all ``Optional`` for PATCH-style operations).
2. In the impl, optionally fetch the existing entity for diff context, then
   compute a list of :class:`FieldChange` via :func:`compute_field_diff`.
3. If ``confirm=False`` return :class:`ModificationResponse` with
   ``is_preview=True``.
4. If ``confirm=True`` call the API, then return
   :class:`ModificationResponse` with ``is_preview=False``.

Use :func:`render_modification_md` (or :func:`to_tool_result`) to produce the
markdown for the :class:`ToolResult` content. Markdown rendering is the only
output channel today; Prefab UI for diff visualization can layer on later by
operating on the same response model.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from enum import Enum
from typing import Any, ClassVar

from fastmcp.tools import ToolResult
from pydantic import BaseModel, Field

from katana_mcp.tools.tool_result_utils import BLOCK_WARNING_PREFIX, make_simple_result
from katana_public_api_client.client_types import UNSET
from katana_public_api_client.domain.converters import unwrap_unset


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


class ModificationResponse(BaseModel):
    """Uniform response for every modification tool.

    The same shape covers update / delete / row-create / row-update /
    row-delete operations. Tool-specific impls populate the fields that
    apply; callers can rely on the common envelope.
    """

    entity_type: str
    entity_id: int | None = None
    parent_entity_id: int | None = None
    operation: str
    is_preview: bool
    changes: list[FieldChange] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    katana_url: str | None = None
    message: str

    DEFAULT_EXCLUDED: ClassVar[tuple[str, ...]] = ("id", "confirm")


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
            ``confirm``).
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


def render_modification_md(response: ModificationResponse) -> str:
    """Render a :class:`ModificationResponse` as the markdown content body."""
    op_title = response.operation.replace("_", " ").title()
    entity_title = response.entity_type.replace("_", " ").title()
    state_label = "PREVIEW" if response.is_preview else op_title.upper()

    lines = [f"## {entity_title} {op_title} ({state_label})"]

    if response.entity_id is not None:
        lines.append(f"- **ID**: {response.entity_id}")
    if response.parent_entity_id is not None:
        lines.append(f"- **Parent ID**: {response.parent_entity_id}")
    lines.append(f"- **Message**: {response.message}")
    if response.katana_url:
        lines.append(f"- **Katana URL**: {response.katana_url}")

    if response.changes:
        lines.append("")
        lines.append("### Changes")
        for change in response.changes:
            if change.is_unchanged:
                lines.append(f"- `{change.field}`: (unchanged) {change.new}")
            elif change.is_unknown_prior:
                lines.append(f"- `{change.field}`: (prior unknown) → {change.new}")
            elif change.is_added:
                lines.append(f"- `{change.field}`: (set) → {change.new}")
            else:
                lines.append(f"- `{change.field}`: {change.old} → {change.new}")

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
