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
from katana_mcp.tools.foundation.collection_diff import (
    STATUS_VARIANTS as _BOM_ROW_STATUS_VARIANTS,
    CollectionDiffSpec,
    derive_status_label as _derive_status_label,
    merge_collection_diff_rows,
    summarize_apply_outcome as _summarize_apply_outcome,
)

logger = get_logger(__name__)

# ``_BOM_ROW_STATUS_VARIANTS`` / ``_derive_status_label`` /
# ``_summarize_apply_outcome`` were hoisted into :mod:`collection_diff` (the
# generic home for the modify-card collection-diff machinery, per the old
# ``TODO(#859)``). They're re-exported here under their original private names
# so existing importers (``prefab_ui``, ``bom``, tests) keep working unchanged.
__all__ = [
    "_BOM_ROW_STATUS_VARIANTS",
    "_derive_status_label",
    "_merge_bom_rows_for_modify_card",
    "_prepare_bom_table_rows",
    "_summarize_apply_outcome",
]


# Wire shape of an existing row in ``prior_state.rows`` — pre-serialized by
# ``serialize_for_prior_state`` from ``BomRowInfo.model_dump()``. Carries
# ``id`` (UUID string), ``ingredient_variant_id``, ``sku``, ``display_name``,
# ``quantity``, ``notes``, ``rank``.
_BomMergedRowKind = Literal["existing", "added", "updated", "deleted"]


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

    # Delegate the snapshot+actions → rows projection to the shared
    # collection-diff skeleton (:func:`merge_collection_diff_rows`), supplying
    # the BOM-specific cell builders as closures. The skeleton owns the
    # add/update/delete classification, status stamping, orphan handling, and
    # materialization order; the closures own ingredient resolution + the
    # quantity/notes diff formatting. ``resolved_ingredients`` is bound here so
    # the generic add/update callbacks stay entity-agnostic.
    def _add(
        action: dict[str, Any],
        *,
        status_label: str,
        status_variant: str,
        error: str | None,
    ) -> dict[str, Any]:
        return _bom_add_action_to_row(
            changes=_bom_change_lookup(action.get("changes")),
            resolved_ingredients=resolved_ingredients,
            status_label=status_label,
            status_variant=status_variant,
            error=error,
        )

    def _update(
        row: dict[str, Any],
        action: dict[str, Any],
        *,
        status_label: str,
        status_variant: str,
        error: str | None,
    ) -> None:
        _apply_bom_update_to_row(
            row,
            changes=_bom_change_lookup(action.get("changes")),
            resolved_ingredients=resolved_ingredients,
            status_label=status_label,
            status_variant=status_variant,
            error=error,
        )

    def _delete(
        row: dict[str, Any],
        action: dict[str, Any],
        *,
        status_label: str,
        status_variant: str,
        error: str | None,
    ) -> None:
        _apply_bom_delete_to_row(
            row,
            status_label=status_label,
            status_variant=status_variant,
            error=error,
        )

    # Materialize: existing rows in rank order (snapshot order on equal ranks),
    # then adds appended (server assigns their rank, so we don't know the slot).
    def _sort_key(r: dict[str, Any]) -> tuple[int, int]:
        rank = r.get("rank")
        return (0, rank) if isinstance(rank, int) else (1, 0)

    return merge_collection_diff_rows(
        prior_rows=prior_rows,
        actions=actions,
        spec=CollectionDiffSpec(
            add_ops=frozenset({"add_bom_row"}),
            update_ops=frozenset({"update_bom_row"}),
            delete_ops=frozenset({"delete_bom_row"}),
            key_of=lambda row: (
                row.get("id") if isinstance(row.get("id"), str) else None
            ),
            existing_row=_bom_existing_row_from_snapshot,
            synth_orphan=_bom_synth_orphan_row,
            add_row=_add,
            apply_update=_update,
            apply_delete=_delete,
            sort_key=_sort_key,
        ),
    )


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
