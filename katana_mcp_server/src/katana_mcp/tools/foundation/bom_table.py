"""BOM table-merge domain helpers (non-UI).

Pure-Python projection logic that turns a BOM modify plan (``prior_state``
snapshot + ``ActionResult`` list + resolved-ingredient lookup) into the
DataTable row list the BOM modify card renders. Lives outside ``prefab_ui``
so the tool-impl path (``foundation/bom.py``) can precompute
``extras["applied_plan_rows"]`` server-side without importing UI internals.

Extracted from ``prefab_ui.py`` per #850 — the rendering helpers
(``build_bom_modify_ui`` and friends) stay in ``prefab_ui.py`` and import
from this module. The split is by *kind of work*: this module shapes
plan-action data into row dicts; ``prefab_ui.py`` wraps those rows in
Prefab components.

The row dicts produced here are deliberately wire-format dicts (no
component types, no Prefab refs) so they round-trip through
``response.extras`` and JSON serialization without loss.
"""

from __future__ import annotations

from typing import Any, Literal

from katana_mcp.logging import get_logger

logger = get_logger(__name__)


# Per-row status pill variants. Mirrors the action status_label vocabulary
# from ``_modification._derive_status_label`` but bucketed for Badge variants
# (success / warn / fail / neutral) so the per-row rendering is consistent
# across preview and applied states.
_BOM_ROW_STATUS_VARIANTS: dict[str, str] = {
    "PLANNED": "secondary",
    "APPLIED": "default",
    "APPLIED (verified)": "default",
    "APPLIED (verification mismatch)": "destructive",
    "FAILED": "destructive",
    # ``execute_plan`` is fail-fast — plan entries past the first failure
    # are never attempted. ``_modify_product_bom_impl`` synthesizes these
    # into the rendered ``actions`` list with status_label="NOT RUN" so
    # the morphed table shows what didn't execute (instead of silently
    # hiding the never-run rows).
    "NOT RUN": "secondary",
    # Existing rows that aren't part of the plan render with no status —
    # we use an empty string so the DataTable cell stays empty rather than
    # showing a misleading "PLANNED" badge for context rows.
    "": "outline",
}


# Wire shape of an existing row in ``prior_state.rows`` — pre-serialized by
# ``serialize_for_prior_state`` from ``BomRowInfo.model_dump()``. Carries
# ``id`` (UUID string), ``ingredient_variant_id``, ``sku``, ``display_name``,
# ``quantity``, ``notes``, ``rank``.
_BomMergedRowKind = Literal["existing", "added", "updated", "deleted"]


def _derive_status_label(action: dict[str, Any]) -> str:
    """Compute a status label from raw ``succeeded`` / ``verified`` fields.

    Used as a fallback for action dicts that don't already carry the
    server-derived ``status_label`` (legacy responses, older clients,
    test fixtures). Mirrors
    :func:`katana_mcp.tools._modification._derive_status_label`.

    Generic across entity kinds — lives here (rather than in ``prefab_ui``)
    so the non-UI BOM merge can call it without a reverse import. The
    rendering layer (``_action_to_row`` in ``prefab_ui``) imports it back.
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


def _summarize_apply_outcome(
    actions: list[dict[str, Any]],
) -> tuple[str, str]:
    """Bucket a modify response's action outcomes for the header Badge.

    Returns ``(state_label, badge_variant)``. Variants align with the
    create-card Tier 1 vocabulary (``default`` / ``secondary`` /
    ``destructive`` / ``outline``).

    - **Empty actions**: ``APPLIED`` / default. A modify/delete plan
      can legitimately produce zero actions (no-op patch, or all
      requested changes turned out to be unchanged). The card has
      nothing to "fail" — render success chrome, not destructive.
    - **All succeeded** (any ``verified`` value): ``APPLIED`` / default.
      Note: per the agreed design, verification mismatch is surfaced
      at the card-level header alone; per-field decoration ignores
      ``verified`` because most users don't differentiate.
    - **All failed**: ``FAILED`` / destructive.
    - **Mixed**: ``PARTIAL FAILURE`` / destructive.

    Generic across entity kinds (used by PO modify and BOM modify cards)
    — lives here so ``foundation/bom.py`` can call it without importing
    ``prefab_ui``. The rendering layer imports it back.

    TODO(#859): hoist this + the dict-typed ``_derive_status_label`` into a
    dedicated ``foundation/modify_outcome.py`` once a third caller appears
    (SO/MO modify cards or a generic modify-result renderer). Housed here
    today to keep #857's diff focused.
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


def _bom_change_lookup(
    changes: list[dict[str, Any]] | None,
) -> dict[str, dict[str, Any]]:
    """Index an action's ``changes`` list by field name for quick lookup.

    Each entry is the raw ``FieldChange`` dict (``field``, ``old``, ``new``,
    plus the ``is_*`` flags). Used by the row-merge helper to pluck out
    quantity / notes / ingredient_variant_id changes per action.
    """
    out: dict[str, dict[str, Any]] = {}
    for c in changes or []:
        if isinstance(c, dict) and isinstance(c.get("field"), str):
            out[c["field"]] = c
    return out


def _format_bom_quantity(value: Any) -> str:
    """Render a BOM-row quantity for the table cell.

    Quantity is a numeric field in Katana but the wire shape may serialize
    floats as strings (decimal-padded) or as Python floats. ``None`` renders
    as em-dash. Floats with an integer value render without the trailing
    ``.0`` (so ``2.0`` reads as ``2`` — typical recipe quantities are whole
    units; the decimal only matters when it's non-trivial).
    """
    if value is None:
        return "—"
    if isinstance(value, str):
        # Strip pure-integer decimal strings like "2.0000000000".
        try:
            numeric: float = float(value)
        except (TypeError, ValueError):
            return value
        if numeric.is_integer():
            return str(int(numeric))
        return f"{numeric:g}"
    if isinstance(value, (int, float)):
        if float(value).is_integer():
            return str(int(value))
        return f"{value:g}"
    return str(value)


def _format_bom_quantity_diff(old: Any, new: Any, *, unknown_prior: bool) -> str:
    """Render a quantity update as ``old → new`` (or ``(prior unknown) → new``).

    Used in the Quantity cell for updated rows.
    """
    after = _format_bom_quantity(new)
    if unknown_prior:
        return f"(prior unknown) → {after}"
    return f"{_format_bom_quantity(old)} → {after}"


def _bom_existing_row_from_snapshot(row: dict[str, Any]) -> dict[str, Any]:
    """Project a snapshot row into the merge-row shape with ``kind=existing``.

    Helper for :func:`_merge_bom_rows_for_modify_card` — extracted so the
    main merge stays under ruff's complexity threshold. The snapshot row
    is the wire shape of ``BomRowInfo.model_dump()``.
    """
    kind: _BomMergedRowKind = "existing"
    return {
        "id": row.get("id"),
        "ingredient_variant_id": row.get("ingredient_variant_id"),
        "sku": row.get("sku"),
        "display_name": row.get("display_name"),
        "rank": row.get("rank"),
        "rank_label": (str(row["rank"]) if isinstance(row.get("rank"), int) else "—"),
        "quantity_label": _format_bom_quantity(row.get("quantity")),
        "notes": row.get("notes"),
        "notes_label": row.get("notes") or "—",
        "kind": kind,
        "status_label": "",
        "status_variant": _BOM_ROW_STATUS_VARIANTS[""],
        "status_prefix": "  ",
        "error": None,
    }


def _bom_synth_orphan_row(target_id: str) -> dict[str, Any]:
    """Synthesize a minimal row for an update/delete target absent from the
    snapshot (rare — partial fetch failure or stale id). Lets the action
    surface in the table even without resolved identity context.
    """
    kind: _BomMergedRowKind = "existing"
    return {
        "id": target_id,
        "ingredient_variant_id": None,
        "sku": None,
        "display_name": None,
        "rank": None,
        "rank_label": "—",
        "quantity_label": "—",
        "notes": None,
        "notes_label": "—",
        "kind": kind,
        "status_label": "",
        "status_variant": _BOM_ROW_STATUS_VARIANTS[""],
        "status_prefix": "  ",
        "error": None,
    }


def _bom_add_action_to_row(
    *,
    changes: dict[str, dict[str, Any]],
    resolved_ingredients: dict[int, dict[str, str | None]],
    status_label: str,
    status_variant: str,
    error: str | None,
) -> dict[str, Any]:
    """Synthesize an ``added``-kind merge row from an ``add_bom_row`` action."""
    ingredient_id_change = changes.get("ingredient_variant_id")
    ingredient_id = ingredient_id_change.get("new") if ingredient_id_change else None
    quantity_change = changes.get("quantity")
    new_qty = quantity_change.get("new") if quantity_change else None
    notes_change = changes.get("notes")
    new_notes = notes_change.get("new") if notes_change else None
    resolved = (
        resolved_ingredients.get(int(ingredient_id))
        if isinstance(ingredient_id, int)
        else None
    )
    kind: _BomMergedRowKind = "added"
    return {
        "id": "",  # No UUID yet — server assigns on POST.
        "ingredient_variant_id": ingredient_id,
        "sku": (resolved or {}).get("sku"),
        "display_name": (resolved or {}).get("display_name"),
        "rank": None,
        "rank_label": "—",
        "quantity_label": _format_bom_quantity(new_qty),
        "notes": new_notes,
        "notes_label": new_notes or "—",
        "kind": kind,
        "status_label": status_label,
        "status_variant": status_variant,
        "status_prefix": "+ ",
        "error": error,
    }


def _apply_bom_update_to_row(
    row: dict[str, Any],
    *,
    changes: dict[str, dict[str, Any]],
    resolved_ingredients: dict[int, dict[str, str | None]],
    status_label: str,
    status_variant: str,
    error: str | None,
) -> None:
    """Decorate a snapshot row in-place with an ``update_bom_row`` action's diff.

    Flips ``kind`` to ``updated``, applies quantity/notes/ingredient_swap
    decoration, and overlays the per-row status. Existing identity stays
    unless the ingredient_variant_id is swapped.
    """
    kind: _BomMergedRowKind = "updated"
    row["kind"] = kind
    row["status_label"] = status_label
    row["status_variant"] = status_variant
    row["status_prefix"] = "~ "
    row["error"] = error
    qty_change = changes.get("quantity")
    if qty_change is not None:
        row["quantity_label"] = _format_bom_quantity_diff(
            qty_change.get("old"),
            qty_change.get("new"),
            unknown_prior=bool(qty_change.get("is_unknown_prior")),
        )
    notes_change = changes.get("notes")
    if notes_change is not None:
        new_notes = notes_change.get("new")
        if notes_change.get("is_unknown_prior"):
            row["notes_label"] = f"(prior unknown) → {new_notes or '—'}"
        else:
            old_notes = notes_change.get("old") or "—"
            row["notes_label"] = f"{old_notes} → {new_notes or '—'}"
    ingredient_change = changes.get("ingredient_variant_id")
    if ingredient_change is not None:
        new_ingredient = ingredient_change.get("new")
        if isinstance(new_ingredient, int):
            resolved = resolved_ingredients.get(new_ingredient)
            row["ingredient_variant_id"] = new_ingredient
            row["sku"] = (resolved or {}).get("sku")
            row["display_name"] = (resolved or {}).get("display_name")


def _apply_bom_delete_to_row(
    row: dict[str, Any],
    *,
    status_label: str,
    status_variant: str,
    error: str | None,
) -> None:
    """Decorate a snapshot row in-place with a ``delete_bom_row`` action."""
    kind: _BomMergedRowKind = "deleted"
    row["kind"] = kind
    row["status_label"] = status_label
    row["status_variant"] = status_variant
    row["status_prefix"] = "- "
    row["error"] = error


def _merge_bom_rows_for_modify_card(
    prior_state: dict[str, Any] | None,
    actions: list[dict[str, Any]],
    resolved_ingredients: dict[int, dict[str, str | None]] | None,
) -> list[dict[str, Any]]:
    """Project the existing BOM snapshot + plan actions into a unified row list.

    Each row carries everything the DataTable needs:

    - ``kind``: ``existing`` | ``added`` | ``updated`` | ``deleted``
    - ``rank`` / ``rank_label``: rank for sortable column; ``rank_label`` is
      the display text (``"—"`` for adds with no rank yet, the rank number
      for everything else).
    - ``ingredient_variant_id``, ``sku``, ``display_name``: row identity.
      Adds resolve SKU / display_name from ``resolved_ingredients``; existing
      rows pull from the snapshot (already resolved by ``_fetch_bom_row_infos``).
    - ``quantity_label``: cell text — bare number for existing/added,
      ``old → new`` diff for updated. For deleted rows the snapshot
      quantity is preserved (so the user sees *what* is going away —
      the ``- `` SKU-column gutter + ``deleted`` kind already signal
      the action).
    - ``notes`` / ``notes_label``: notes value, with diff decoration on update.
    - ``status_label`` / ``status_variant``: per-row Badge text + variant.
    - ``error``: failure message (None when not failed). Surfaced in the
      consolidated bottom Alert; not rendered inline.
    - ``status_prefix``: ``"+ "`` / ``"- "`` / ``"  "`` — leading 2-char
      gutter on the SKU / Display Name cells so adds and deletes are
      visually distinct without depending on row-styling that Prefab
      doesn't currently expose. Same layout-stability trick as
      ``_render_field_diff_line``.

    Match rules:

    - delete actions are looked up by ``target_id`` (UUID string) against the
      snapshot rows.
    - update actions are looked up the same way; the resolved ingredient
      reflects the post-patch ingredient (when the update swaps it).
    - add actions are synthesized fresh from the action's ``changes`` —
      they have no ``target_id`` in the plan. SKU/display_name come from
      ``resolved_ingredients``; missing entries gracefully degrade to
      "(unresolved)" so the row still renders with the ingredient_variant_id.

    Empty plan + empty existing → empty list (the caller renders a friendly
    placeholder). The merge is robust against partial data: missing
    ``prior_state`` reduces existing rows to zero but still surfaces planned
    adds + updates + deletes (the latter two with no resolved row to base
    off of — they degrade gracefully).
    """
    resolved_ingredients = resolved_ingredients or {}
    prior_rows: list[dict[str, Any]] = []
    if isinstance(prior_state, dict):
        candidate = prior_state.get("rows")
        if isinstance(candidate, list):
            prior_rows = [r for r in candidate if isinstance(r, dict)]

    # Build a working copy keyed by UUID string for fast update/delete
    # lookup. ``existing_by_id`` is mutated in place as we apply plan
    # decorations, so the final pass over it yields rows in the snapshot's
    # original rank order regardless of plan iteration order.
    existing_by_id: dict[str, dict[str, Any]] = {}
    for row in prior_rows:
        row_id = row.get("id")
        if not isinstance(row_id, str):
            continue
        existing_by_id[row_id] = _bom_existing_row_from_snapshot(row)

    added_rows: list[dict[str, Any]] = []

    for action in actions:
        op = str(action.get("operation") or "").lower()
        status_label = action.get("status_label") or _derive_status_label(action) or ""
        status_variant = _BOM_ROW_STATUS_VARIANTS.get(status_label, "secondary")
        error = action.get("error") if action.get("succeeded") is False else None
        changes = _bom_change_lookup(action.get("changes"))
        target_id = action.get("target_id")
        target_str = str(target_id) if target_id is not None else None

        if op == "add_bom_row":
            added_rows.append(
                _bom_add_action_to_row(
                    changes=changes,
                    resolved_ingredients=resolved_ingredients,
                    status_label=status_label,
                    status_variant=status_variant,
                    error=error,
                )
            )
            continue

        if op == "update_bom_row" and target_str:
            row = existing_by_id.get(target_str)
            if row is None:
                row = _bom_synth_orphan_row(target_str)
                existing_by_id[target_str] = row
            _apply_bom_update_to_row(
                row,
                changes=changes,
                resolved_ingredients=resolved_ingredients,
                status_label=status_label,
                status_variant=status_variant,
                error=error,
            )
            continue

        if op == "delete_bom_row" and target_str:
            row = existing_by_id.get(target_str)
            if row is None:
                row = _bom_synth_orphan_row(target_str)
                existing_by_id[target_str] = row
            _apply_bom_delete_to_row(
                row,
                status_label=status_label,
                status_variant=status_variant,
                error=error,
            )
            continue

        # Unmatched: either an unknown ``operation`` string (future
        # ``reorder_bom_rows`` etc.) or a known op with a missing
        # ``target_id``. Either way the action would silently vanish from
        # the rendered card — log so the gap is visible during dev.
        logger.warning(
            "BOM merge dropped action — unknown operation or missing target",
            operation=op,
            target_id=target_str,
            succeeded=action.get("succeeded"),
        )

    # Materialize: existing-rows (snapshot order, then rank), then adds
    # appended at the end (server assigns the rank, so we don't know
    # where they slot yet). Stable sort on rank: existing rows preserve
    # their snapshot order on equal ranks; adds always trail.
    def _sort_key(r: dict[str, Any]) -> tuple[int, int]:
        rank = r.get("rank")
        return (0, rank) if isinstance(rank, int) else (1, 0)

    materialized = sorted(existing_by_id.values(), key=_sort_key)
    materialized.extend(added_rows)
    return materialized


def _prepare_bom_table_rows(merged: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Compose the final per-row dicts passed to the DataTable.

    The SKU column shows the kind prefix (``+ ``/``- ``/``~ ``/``  ``) inline
    so adds vs deletes are visually obvious even without per-row styling.
    The display_name cell carries the resolved name with a ``(unresolved)``
    fallback so unresolved adds (missing from cache) still render meaningfully.
    """
    out: list[dict[str, Any]] = []
    for r in merged:
        sku = r.get("sku") or "(unresolved)"
        display_name = r.get("display_name") or ""
        if not display_name and r.get("ingredient_variant_id") is not None:
            display_name = f"variant {r['ingredient_variant_id']}"
        out.append(
            {
                **r,
                "sku_label": f"{r['status_prefix']}{sku}",
                "display_name": display_name,
                # For deleted rows, the row identity carries the strike
                # semantically via the kind prefix + status pill — text-
                # decoration isn't available in DataTable cells, so we
                # encode the signal lexically (``- ``) instead.
            }
        )
    return out
