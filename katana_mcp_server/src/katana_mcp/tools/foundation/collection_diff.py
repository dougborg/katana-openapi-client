"""Entity-agnostic collection-diff row model + merge (non-UI).

Every modify/delete card renders the same conceptual thing for a collection of
sub-entities — "show the CRUD changes, with per-row status that morphs when the
apply lands". This module owns the shared parts of that projection:

- the per-row **status vocabulary** (``PLANNED`` / ``APPLIED`` / ``FAILED`` / …)
  and its Badge-variant + 2-char kind-gutter mapping,
- the **merge skeleton** that folds a ``prior_state`` snapshot together with a
  list of CRUD ``ActionResult`` dicts into one ordered row list, classifying
  each action as add / update / delete and stamping ``kind`` / ``status_label`` /
  ``status_variant`` / ``error`` onto the row,
- the **summary line** (``+N added, ~M updated, -K deleted``).

Per-collection *cell* decoration (what columns a BOM row vs. an item variant vs.
an SO line item shows, and how each field's diff renders) is supplied by the
caller via callbacks — this module is deliberately ignorant of any entity's
column set.

Lives outside ``prefab_ui`` (like its ancestor :mod:`bom_table`) so tool-impl
paths can precompute row lists server-side without importing UI internals, and
the row dicts stay wire-format (no Prefab component types) so they round-trip
through ``response.extras`` + JSON.

Generalized from the BOM table-merge (#811, :mod:`bom_table`); fulfils the
``TODO(#859)`` to hoist :func:`derive_status_label` / :func:`summarize_apply_outcome`
into a shared home once a third caller (item / SO / MO modify cards) appeared.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal, Protocol

from katana_mcp.logging import get_logger

logger = get_logger(__name__)


CollectionRowKind = Literal["existing", "added", "updated", "deleted"]


class _AddRowFn(Protocol):
    """Builds an ``added``-kind row from an add action.

    Receives the merge-derived status fields so it doesn't re-derive them.
    """

    def __call__(
        self,
        action: dict[str, Any],
        /,
        *,
        status_label: str,
        status_variant: str,
        error: str | None,
    ) -> dict[str, Any]: ...


class _MutateRowFn(Protocol):
    """Decorates a matched snapshot row in place for an update / delete action."""

    def __call__(
        self,
        row: dict[str, Any],
        action: dict[str, Any],
        /,
        *,
        status_label: str,
        status_variant: str,
        error: str | None,
    ) -> None: ...


# Per-row status pill variants, bucketed for Badge variants
# (success / warn / fail / neutral) so per-row rendering is consistent across
# preview and applied states. Shared by every modify card's collection table.
STATUS_VARIANTS: dict[str, str] = {
    "PLANNED": "secondary",
    "APPLIED": "default",
    "APPLIED (verified)": "default",
    "APPLIED (verification mismatch)": "destructive",
    "FAILED": "destructive",
    # ``execute_plan`` is fail-fast — plan entries past the first failure are
    # never attempted. Impls synthesize these into the rendered ``actions``
    # list with status_label="NOT RUN" so the morphed table shows what didn't
    # execute (instead of silently hiding never-run rows).
    "NOT RUN": "secondary",
    # Context rows that aren't part of the plan render with no status — empty
    # string keeps the DataTable cell blank rather than a misleading badge.
    "": "outline",
}


# 2-char leading gutter per row kind. DataTable cells can't carry colour or
# strike styling, so add / update / delete is encoded lexically on the
# caller-designated key column (``+ `` / ``~ `` / ``- `` / ``  ``). Same
# layout-stability trick as ``_render_field_diff_line``'s ``✗`` gutter.
STATUS_PREFIX: dict[CollectionRowKind, str] = {
    "existing": "  ",
    "added": "+ ",
    "updated": "~ ",
    "deleted": "- ",
}


def derive_status_label(action: dict[str, Any]) -> str:
    """Compute a status label from raw ``succeeded`` / ``verified`` fields.

    Fallback for action dicts that don't already carry the server-derived
    ``status_label`` (legacy responses, older clients, test fixtures). Mirrors
    :func:`katana_mcp.tools._modification._derive_status_label` but operates on
    plain dicts so the non-UI merge can call it without a reverse import.
    """
    succeeded = action.get("succeeded")
    if succeeded is None:
        return "PLANNED"
    if succeeded is True:
        verified = action.get("verified")
        if verified is False:
            return "APPLIED (verification mismatch)"
        if verified is True:
            return "APPLIED (verified)"
        return "APPLIED"
    return "FAILED"


def summarize_apply_outcome(actions: list[dict[str, Any]]) -> tuple[str, str]:
    """Bucket a modify response's action outcomes for the header Badge.

    Returns ``(state_label, badge_variant)``. Variants align with the
    create-card Tier 1 vocabulary (``default`` / ``secondary`` /
    ``destructive`` / ``outline``).

    - **Empty actions**: ``APPLIED`` / default. A modify/delete plan can
      legitimately produce zero actions (no-op patch, or all requested changes
      turned out unchanged). The card has nothing to "fail" — success chrome.
    - **All succeeded** (any ``verified`` value): ``APPLIED`` / default.
      Verification mismatch surfaces at the card-level header alone; per-field
      decoration ignores ``verified`` because most users don't differentiate.
    - **All failed**: ``FAILED`` / destructive.
    - **Mixed**: ``PARTIAL FAILURE`` / destructive.
    """
    if not actions:
        return "APPLIED", "default"
    succeeded = sum(1 for a in actions if a.get("succeeded") is True)
    failed = sum(1 for a in actions if a.get("succeeded") is False)
    if failed == 0 and succeeded > 0:
        return "APPLIED", "default"
    if succeeded == 0 and failed > 0:
        return "FAILED", "destructive"
    return "PARTIAL FAILURE", "destructive"


def collection_diff_summary(rows: list[dict[str, Any]]) -> str:
    """Build the ``+N added, ~M updated, -K deleted`` summary line.

    Only emits buckets with non-zero counts so the line stays compact on
    simpler plans. Returns the empty string when the plan is a no-op
    (existing-only rows) — the caller skips rendering in that case.
    """
    added = sum(1 for r in rows if r.get("kind") == "added")
    updated = sum(1 for r in rows if r.get("kind") == "updated")
    deleted = sum(1 for r in rows if r.get("kind") == "deleted")
    parts: list[str] = []
    if added:
        parts.append(f"+{added} added")
    if updated:
        parts.append(f"~{updated} updated")
    if deleted:
        parts.append(f"-{deleted} deleted")
    return ", ".join(parts)


@dataclass(frozen=True)
class CollectionDiffSpec:
    """Per-collection vocabulary + cell-builder callbacks for the merge.

    Bundles everything :func:`merge_collection_diff_rows` needs to know about a
    specific collection (BOM rows, item variants, SO line items, …) so the
    merge entrypoint stays a 3-argument function. The callbacks own the
    entity-specific cell text + the ``kind`` / ``status_prefix`` stamping; the
    merge owns the add/update/delete classification, status derivation, orphan
    handling, and materialization order.

    Callbacks (each receives the merge-derived ``status_label`` /
    ``status_variant`` / ``error`` as keyword args so they don't re-derive):

    - ``existing_row(snapshot_row) -> row`` — base row for a snapshot member.
    - ``synth_orphan(target_key) -> row`` — minimal row for an update/delete
      target absent from the snapshot (partial fetch / stale id).
    - ``add_row(action, *, status_label, status_variant, error) -> row``.
    - ``apply_update(row, action, *, status_label, status_variant, error)`` —
      decorate the matched snapshot row in place.
    - ``apply_delete(row, action, *, status_label, status_variant, error)``.

    ``key_of(snapshot_row)`` extracts the snapshot's match key (compared
    against ``str(action["target_id"])``). ``sort_key`` orders the existing
    rows (adds always trail).
    """

    # ``frozenset`` (not ``set``) so the caller-supplied op vocabulary is
    # genuinely immutable — ``frozen=True`` only blocks attribute reassignment,
    # not mutation of a ``set`` field's contents.
    add_ops: frozenset[str]
    update_ops: frozenset[str]
    delete_ops: frozenset[str]
    key_of: Callable[[dict[str, Any]], str | None]
    existing_row: Callable[[dict[str, Any]], dict[str, Any]]
    synth_orphan: Callable[[str], dict[str, Any]]
    add_row: _AddRowFn
    apply_update: _MutateRowFn
    apply_delete: _MutateRowFn
    sort_key: Callable[[dict[str, Any]], Any]


def merge_collection_diff_rows(
    *,
    prior_rows: list[dict[str, Any]],
    actions: list[dict[str, Any]],
    spec: CollectionDiffSpec,
) -> list[dict[str, Any]]:
    """Project a prior-state collection + plan actions into a unified row list.

    The entity-agnostic skeleton behind every modify card's collection table.
    For each action it derives the shared bookkeeping (``status_label`` from
    ``action.status_label`` or :func:`derive_status_label`, ``status_variant``
    from :data:`STATUS_VARIANTS`, and the failure ``error``), classifies the op
    via ``spec.add_ops`` / ``update_ops`` / ``delete_ops``, and dispatches to
    the matching :class:`CollectionDiffSpec` callback.

    Materialization order: existing rows via ``spec.sort_key``, then added rows
    appended (the server assigns their final position). Actions whose op
    matches no bucket, or an update/delete with no ``target_id``, are logged
    and dropped rather than vanishing silently.
    """
    existing_by_key: dict[str, dict[str, Any]] = {}
    for snapshot_row in prior_rows:
        key = spec.key_of(snapshot_row)
        if not isinstance(key, str):
            continue
        existing_by_key[key] = spec.existing_row(snapshot_row)

    added_rows: list[dict[str, Any]] = []

    for action in actions:
        op = str(action.get("operation") or "").lower()
        # ``or``-chain (not ``is not None``): a present-but-empty status_label
        # falls through to derivation. Safe because real ``ActionResult``s
        # always carry a derived label (``ActionResult.__post_init__`` fills
        # it), so "" only occurs for dict fixtures that genuinely want
        # derivation. A future consumer needing explicit-"" semantics should
        # revisit this — it's the one place the merge second-guesses its input.
        status_label = action.get("status_label") or derive_status_label(action) or ""
        status_variant = STATUS_VARIANTS.get(status_label, "secondary")
        error = action.get("error") if action.get("succeeded") is False else None
        target_id = action.get("target_id")
        target_key = str(target_id) if target_id is not None else None

        if op in spec.add_ops:
            added_rows.append(
                spec.add_row(
                    action,
                    status_label=status_label,
                    status_variant=status_variant,
                    error=error,
                )
            )
            continue

        if op in spec.update_ops and target_key:
            row = existing_by_key.get(target_key)
            if row is None:
                row = spec.synth_orphan(target_key)
                existing_by_key[target_key] = row
            spec.apply_update(
                row,
                action,
                status_label=status_label,
                status_variant=status_variant,
                error=error,
            )
            continue

        if op in spec.delete_ops and target_key:
            row = existing_by_key.get(target_key)
            if row is None:
                row = spec.synth_orphan(target_key)
                existing_by_key[target_key] = row
            spec.apply_delete(
                row,
                action,
                status_label=status_label,
                status_variant=status_variant,
                error=error,
            )
            continue

        # Unmatched: unknown ``operation`` (future ops) or a known op missing
        # its ``target_id``. Either way the action would silently vanish from
        # the rendered card — log so the gap is visible during dev.
        logger.warning(
            "collection diff dropped action — unknown operation or missing target",
            operation=op,
            target_id=target_key,
            succeeded=action.get("succeeded"),
        )

    materialized = sorted(existing_by_key.values(), key=spec.sort_key)
    materialized.extend(added_rows)
    return materialized
