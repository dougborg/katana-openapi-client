"""Bin-transfer row table-merge domain helpers (non-UI).

Projects a bin-transfer modify plan (``prior_state`` snapshot + row-CRUD
``ActionResult`` list + resolved-variant / resolved-bin lookups) into the
DataTable row list the bin-transfer modify card renders for its line-items
collection. Sibling of :mod:`po_row_table` — same split-by-kind-of-work: this
module shapes plan-action data into wire-format row dicts; ``prefab_ui.py``
wraps them in Prefab components.

Layered on the shared collection-diff skeleton
(:func:`merge_collection_diff_rows`): this module supplies the bin-row cell
builders (SKU / variant name / quantity / from-bin / to-bin) as closures; the
skeleton owns the add/update/delete classification, status stamping, orphan
handling, and materialization order.

Bins render by name via the ``resolved_bins`` lookup (the impl's best-effort
live fetch of the location's storage bins); a miss falls back to ``bin <id>``
and ``None`` (unassigned stock) renders as an em-dash.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Literal

from katana_mcp.tools.foundation.collection_diff import (
    STATUS_PREFIX,
    STATUS_VARIANTS,
    CollectionDiffSpec,
    merge_collection_diff_rows,
)

_BinRowKind = Literal["existing", "added", "updated", "deleted"]

# ``BinTransferOperation`` StrEnum values for the row-CRUD ops
# (bin_transfers.py).
_ADD_OPS = frozenset({"add_row"})
_UPDATE_OPS = frozenset({"update_row"})
_DELETE_OPS = frozenset({"delete_row"})

# ``{variant_id: {"sku": ..., "display_name": ...}}`` — threaded from the
# impl's batched cache lookup (``extras["resolved_variants"]``).
ResolvedVariants = dict[int, dict[str, str | None]]

# ``{bin_id: bin_name}`` — threaded from the impl's best-effort live storage-
# bin fetch (``extras["resolved_bins"]``).
ResolvedBins = dict[int, str]


def _changes_by_field(
    changes: list[dict[str, Any]] | None,
) -> dict[str, dict[str, Any]]:
    """Index an action's ``changes`` list by field name (raw FieldChange dicts)."""
    out: dict[str, dict[str, Any]] = {}
    for c in changes or []:
        if isinstance(c, dict) and isinstance(c.get("field"), str):
            out[c["field"]] = c
    return out


def _format_number(value: Any) -> str:
    """Render a quantity for a table cell, trimmed of trailing zeros.

    ``None`` → em-dash. Mirrors ``po_row_table._format_number`` — quantities
    arrive as wire decimal strings on snapshot rows and as ``Decimal`` /
    ``float`` from the diff pipeline.
    """
    if value is None:
        return "—"
    if isinstance(value, str):
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return value
        return f"{numeric:g}"
    if isinstance(value, (int, float, Decimal)):
        return f"{float(value):g}"
    return str(value)


def _format_number_diff(old: Any, new: Any, *, unknown_prior: bool) -> str:
    """Render a numeric update as ``old → new`` (or ``(prior unknown) → new``)."""
    after = _format_number(new)
    if unknown_prior:
        return f"(prior unknown) → {after}"
    return f"{_format_number(old)} → {after}"


def _resolved_name(
    resolved: ResolvedVariants, variant_id: Any
) -> tuple[str | None, str | None]:
    """Look up ``(sku, display_name)`` for a variant id (``(None, None)`` miss)."""
    if isinstance(variant_id, int):
        hit = resolved.get(variant_id)
        if hit:
            return hit.get("sku"), hit.get("display_name")
    return None, None


def _bin_label(resolved: ResolvedBins, bin_id: Any) -> str:
    """Render one bin cell: resolved name, ``bin <id>`` miss, ``—`` unassigned."""
    if bin_id is None:
        return "—"
    if isinstance(bin_id, int) and bin_id in resolved:
        return resolved[bin_id]
    # ``Decimal`` ids come out of the diff pipeline's ``_normalize``.
    try:
        as_int = int(bin_id)
    except (TypeError, ValueError):
        return str(bin_id)
    return resolved.get(as_int, f"bin {as_int}")


def _bin_label_diff(
    resolved: ResolvedBins, old: Any, new: Any, *, unknown_prior: bool
) -> str:
    """Render a bin reassignment as ``old-name → new-name``."""
    after = _bin_label(resolved, new)
    if unknown_prior:
        return f"(prior unknown) → {after}"
    return f"{_bin_label(resolved, old)} → {after}"


def _existing_row_from_snapshot(
    row: dict[str, Any], resolved: ResolvedVariants, bins: ResolvedBins
) -> dict[str, Any]:
    """Project a prior-state bin transfer row (raw ``BinTransferRow.to_dict()``)
    into the merge-row shape."""
    sku, display_name = _resolved_name(resolved, row.get("variant_id"))
    kind: _BinRowKind = "existing"
    return {
        "id": row.get("id"),
        "variant_id": row.get("variant_id"),
        "sku": sku,
        "display_name": display_name,
        "quantity_label": _format_number(row.get("quantity")),
        "source_bin_label": _bin_label(bins, row.get("source_bin_location_id")),
        "target_bin_label": _bin_label(bins, row.get("target_bin_location_id")),
        "kind": kind,
        "status_label": "",
        "status_variant": STATUS_VARIANTS[""],
        "status_prefix": STATUS_PREFIX["existing"],
        "error": None,
    }


def _synth_orphan_row(target_id: str) -> dict[str, Any]:
    """Minimal row for an update/delete target absent from the snapshot."""
    kind: _BinRowKind = "existing"
    return {
        "id": target_id,
        "variant_id": None,
        "sku": None,
        "display_name": None,
        "quantity_label": "—",
        "source_bin_label": "—",
        "target_bin_label": "—",
        "kind": kind,
        "status_label": "",
        "status_variant": STATUS_VARIANTS[""],
        "status_prefix": STATUS_PREFIX["existing"],
        "error": None,
    }


def _add_action_to_row(
    action: dict[str, Any],
    resolved: ResolvedVariants,
    bins: ResolvedBins,
    *,
    status_label: str,
    status_variant: str,
    error: str | None,
) -> dict[str, Any]:
    """Synthesize an ``added``-kind row from an ``add_row`` action."""
    changes = _changes_by_field(action.get("changes"))
    variant_change = changes.get("variant_id")
    variant_id = variant_change.get("new") if variant_change else None
    if variant_id is not None:
        # ``_normalize`` coerces ints to Decimal in the diff pipeline.
        variant_id = int(variant_id)
    sku, display_name = _resolved_name(resolved, variant_id)
    qty_change = changes.get("quantity")
    source_change = changes.get("source_bin_location_id")
    target_change = changes.get("target_bin_location_id")
    kind: _BinRowKind = "added"
    return {
        "id": "",  # No row id yet — server assigns on POST.
        "variant_id": variant_id,
        "sku": sku,
        "display_name": display_name,
        "quantity_label": _format_number(qty_change.get("new") if qty_change else None),
        "source_bin_label": _bin_label(
            bins, source_change.get("new") if source_change else None
        ),
        "target_bin_label": _bin_label(
            bins, target_change.get("new") if target_change else None
        ),
        "kind": kind,
        "status_label": status_label,
        "status_variant": status_variant,
        "status_prefix": STATUS_PREFIX["added"],
        "error": error,
    }


def _apply_update_to_row(
    row: dict[str, Any],
    action: dict[str, Any],
    resolved: ResolvedVariants,
    bins: ResolvedBins,
    *,
    status_label: str,
    status_variant: str,
    error: str | None,
) -> None:
    """Decorate a snapshot row in-place with an ``update_row`` action's diff.

    Flips ``kind`` to ``updated`` and overlays before→after on quantity and
    the bin cells. A variant swap re-resolves SKU + name from the new
    ``variant_id``.
    """
    kind: _BinRowKind = "updated"
    row["kind"] = kind
    row["status_label"] = status_label
    row["status_variant"] = status_variant
    row["status_prefix"] = STATUS_PREFIX["updated"]
    row["error"] = error
    changes = _changes_by_field(action.get("changes"))
    qty_change = changes.get("quantity")
    if qty_change is not None:
        row["quantity_label"] = _format_number_diff(
            qty_change.get("old"),
            qty_change.get("new"),
            unknown_prior=bool(qty_change.get("is_unknown_prior")),
        )
    for field, label_key in (
        ("source_bin_location_id", "source_bin_label"),
        ("target_bin_location_id", "target_bin_label"),
    ):
        bin_change = changes.get(field)
        if bin_change is not None:
            row[label_key] = _bin_label_diff(
                bins,
                bin_change.get("old"),
                bin_change.get("new"),
                unknown_prior=bool(bin_change.get("is_unknown_prior")),
            )
    variant_change = changes.get("variant_id")
    if variant_change is not None:
        new_variant = variant_change.get("new")
        if new_variant is not None:
            new_variant = int(new_variant)
        sku, display_name = _resolved_name(resolved, new_variant)
        row["variant_id"] = new_variant
        row["sku"] = sku
        row["display_name"] = display_name


def _apply_delete_to_row(
    row: dict[str, Any],
    _action: dict[str, Any],
    *,
    status_label: str,
    status_variant: str,
    error: str | None,
) -> None:
    """Decorate a snapshot row in-place with a ``delete_row`` action.

    Identity (SKU / name / qty / bins) is preserved so the user sees *what*
    is going away; the ``- `` gutter + ``deleted`` kind carry the signal.
    """
    kind: _BinRowKind = "deleted"
    row["kind"] = kind
    row["status_label"] = status_label
    row["status_variant"] = status_variant
    row["status_prefix"] = STATUS_PREFIX["deleted"]
    row["error"] = error


def merge_bin_row_rows_for_modify_card(
    prior_state: dict[str, Any] | None,
    actions: list[dict[str, Any]],
    resolved_variants: ResolvedVariants | None,
    resolved_bins: ResolvedBins | None,
) -> list[dict[str, Any]]:
    """Project the prior bin-transfer rows + plan actions into a unified row list.

    Existing rows render unchanged; ``add_row`` actions append as ``added``
    rows; ``update_row`` actions decorate the matched row with before→after on
    quantity / bins; ``delete_row`` actions mark the matched row ``deleted``.
    Header / status ops in the same plan are filtered out (handled outside
    this table) so they don't trip the shared merge's unknown-op warning.

    Match key: ``str(row["id"])`` against ``str(action["target_id"])``. Adds
    have no target_id and synthesize fresh from their ``changes``.
    """
    resolved = resolved_variants or {}
    bins = resolved_bins or {}
    prior_rows: list[dict[str, Any]] = []
    if isinstance(prior_state, dict):
        candidate = prior_state.get("bin_transfer_rows")
        if isinstance(candidate, list):
            prior_rows = [r for r in candidate if isinstance(r, dict)]

    row_ops = _ADD_OPS | _UPDATE_OPS | _DELETE_OPS
    row_actions = [
        a for a in actions if str(a.get("operation") or "").lower() in row_ops
    ]

    def _add(
        action: dict[str, Any],
        *,
        status_label: str,
        status_variant: str,
        error: str | None,
    ) -> dict[str, Any]:
        return _add_action_to_row(
            action,
            resolved,
            bins,
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
        _apply_update_to_row(
            row,
            action,
            resolved,
            bins,
            status_label=status_label,
            status_variant=status_variant,
            error=error,
        )

    return merge_collection_diff_rows(
        prior_rows=prior_rows,
        actions=row_actions,
        spec=CollectionDiffSpec(
            add_ops=_ADD_OPS,
            update_ops=_UPDATE_OPS,
            delete_ops=_DELETE_OPS,
            key_of=lambda r: str(r["id"]) if r.get("id") is not None else None,
            existing_row=lambda r: _existing_row_from_snapshot(r, resolved, bins),
            synth_orphan=_synth_orphan_row,
            add_row=_add,
            apply_update=_update,
            apply_delete=_apply_delete_to_row,
            # Snapshot order is the transfer's row order; adds trail (server
            # assigns the slot). Preserve insertion order via a constant key.
            sort_key=lambda r: 0,
        ),
    )


def prepare_bin_row_table_rows(
    merged: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Compose the final DataTable row dicts.

    The SKU column carries the kind gutter (``+ ``/``- ``/``~ ``/``  ``); the
    name column falls back to ``variant <id>`` when the cache miss left the
    display_name unresolved so the row is never blank. Mirrors
    ``po_row_table.prepare_po_row_table_rows``.
    """
    out: list[dict[str, Any]] = []
    for r in merged:
        sku = r.get("sku") or "(unresolved)"
        display_name = r.get("display_name") or ""
        if not display_name and r.get("variant_id") is not None:
            display_name = f"variant {r['variant_id']}"
        out.append(
            {
                **r,
                "sku_label": f"{r['status_prefix']}{sku}",
                "display_name": display_name,
            }
        )
    return out
