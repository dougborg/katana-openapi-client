"""Item-variant table-merge domain helpers (non-UI).

Pure-Python projection logic that turns an item modify plan (``prior_state``
snapshot + variant-CRUD ``ActionResult`` list) into the DataTable row list the
item modify card renders for its variants collection. Lives outside
``prefab_ui`` — same split-by-kind-of-work as its sibling :mod:`bom_table`: this
module shapes plan-action data into row dicts; ``prefab_ui.py`` wraps those rows
in Prefab components.

The row dicts are deliberately wire-format dicts (no component types, no Prefab
refs) so they round-trip through ``response.extras`` / iframe ``state`` and JSON
serialization without loss.

Generalized atop the shared collection-diff skeleton
(:func:`merge_collection_diff_rows`, #859 / #872) — this module supplies the
variant-specific cell builders (SKU / sales price / purchase price) as closures;
the skeleton owns the add/update/delete classification, status stamping, orphan
handling, and materialization order.
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

_VariantRowKind = Literal["existing", "added", "updated", "deleted"]

# Operation vocabulary — the ``ItemOperation`` StrEnum values the item modify
# plan stamps onto each variant action (foundation/items.py).
_ADD_OPS = frozenset({"add_variant"})
_UPDATE_OPS = frozenset({"update_variant"})
_DELETE_OPS = frozenset({"delete_variant"})


def _changes_by_field(
    changes: list[dict[str, Any]] | None,
) -> dict[str, dict[str, Any]]:
    """Index an action's ``changes`` list by field name.

    Each entry is the raw ``FieldChange`` dict (``field`` / ``old`` / ``new``
    plus the ``is_*`` flags). Mirrors ``bom_table._bom_change_lookup`` — kept
    local so the two table modules stay independent of each other's internals.
    """
    out: dict[str, dict[str, Any]] = {}
    for c in changes or []:
        if isinstance(c, dict) and isinstance(c.get("field"), str):
            out[c["field"]] = c
    return out


def _format_price(value: Any) -> str:
    """Render a variant price for a table cell.

    ``None`` renders as em-dash. Numerics render via ``:g`` to trim trailing
    zeros (``299.0 → '299'`` while preserving ``2.5``) — matching the plain
    variant lines in ``_item_single_variant_lines``. Wire shape may serialize a
    price as a numeric string; coerce so the trailing-zero trim still applies.

    ``Decimal`` is handled explicitly: real modify diffs flow through
    ``compute_field_diff`` → ``_normalize``, which coerces every numeric /
    decimal-looking price to :class:`~decimal.Decimal`. Without this branch a
    ``Decimal("1200.0000000000")`` would fall through to ``str(value)`` and
    render the full unrounded form instead of the trimmed ``1200``.
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


def _format_price_diff(old: Any, new: Any, *, unknown_prior: bool) -> str:
    """Render a price update as ``old → new`` (or ``(prior unknown) → new``)."""
    after = _format_price(new)
    if unknown_prior:
        return f"(prior unknown) → {after}"
    return f"{_format_price(old)} → {after}"


def _existing_row_from_snapshot(variant: dict[str, Any]) -> dict[str, Any]:
    """Project a prior-state variant dict into the merge-row shape.

    The snapshot variant is the wire shape of ``Variant.to_dict()`` — ``id``
    (int), ``sku`` (``str | None``), ``sales_price`` / ``purchase_price``
    (numeric, UNSET-stripped → absent → renders em-dash).
    """
    kind: _VariantRowKind = "existing"
    return {
        "id": variant.get("id"),
        "sku": variant.get("sku"),
        "sales_price_label": _format_price(variant.get("sales_price")),
        "purchase_price_label": _format_price(variant.get("purchase_price")),
        "kind": kind,
        "status_label": "",
        "status_variant": STATUS_VARIANTS[""],
        "status_prefix": STATUS_PREFIX["existing"],
        "error": None,
    }


def _synth_orphan_row(target_id: str) -> dict[str, Any]:
    """Synthesize a minimal row for an update/delete target absent from the
    snapshot (rare — partial fetch failure or stale id). Lets the action
    still surface in the table even without resolved identity context.
    """
    kind: _VariantRowKind = "existing"
    return {
        "id": target_id,
        "sku": None,
        "sales_price_label": "—",
        "purchase_price_label": "—",
        "kind": kind,
        "status_label": "",
        "status_variant": STATUS_VARIANTS[""],
        "status_prefix": STATUS_PREFIX["existing"],
        "error": None,
    }


def _add_action_to_row(
    action: dict[str, Any],
    *,
    status_label: str,
    status_variant: str,
    error: str | None,
) -> dict[str, Any]:
    """Synthesize an ``added``-kind row from an ``add_variant`` action.

    Reads SKU / sales price / purchase price from the action's ``changes``
    (every supplied field on the ``VariantAdd`` payload, reported as added).
    SKU is required on ``VariantAdd`` so it's always present; prices are
    optional and degrade to em-dash.
    """
    changes = _changes_by_field(action.get("changes"))
    sku_change = changes.get("sku")
    sales_change = changes.get("sales_price")
    purchase_change = changes.get("purchase_price")
    kind: _VariantRowKind = "added"
    return {
        "id": "",  # No variant id yet — server assigns on POST.
        "sku": sku_change.get("new") if sku_change else None,
        "sales_price_label": _format_price(
            sales_change.get("new") if sales_change else None
        ),
        "purchase_price_label": _format_price(
            purchase_change.get("new") if purchase_change else None
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
    *,
    status_label: str,
    status_variant: str,
    error: str | None,
) -> None:
    """Decorate a snapshot row in-place with an ``update_variant`` action's diff.

    Flips ``kind`` to ``updated`` and overlays before→after on SKU / sales
    price / purchase price when those fields changed. Other variant-field
    edits (barcodes, supplier_item_codes, lead_time, MOQ, config attributes)
    still flip the row to ``updated`` with its status pill — they're carried
    by the action, just not surfaced as dedicated columns in this table.
    """
    kind: _VariantRowKind = "updated"
    row["kind"] = kind
    row["status_label"] = status_label
    row["status_variant"] = status_variant
    row["status_prefix"] = STATUS_PREFIX["updated"]
    row["error"] = error
    changes = _changes_by_field(action.get("changes"))
    sku_change = changes.get("sku")
    if sku_change is not None:
        old_sku = sku_change.get("old") or "(no SKU)"
        new_sku = sku_change.get("new") or "(no SKU)"
        row["sku"] = f"{old_sku} → {new_sku}"
    sales_change = changes.get("sales_price")
    if sales_change is not None:
        row["sales_price_label"] = _format_price_diff(
            sales_change.get("old"),
            sales_change.get("new"),
            unknown_prior=bool(sales_change.get("is_unknown_prior")),
        )
    purchase_change = changes.get("purchase_price")
    if purchase_change is not None:
        row["purchase_price_label"] = _format_price_diff(
            purchase_change.get("old"),
            purchase_change.get("new"),
            unknown_prior=bool(purchase_change.get("is_unknown_prior")),
        )


def _apply_delete_to_row(
    row: dict[str, Any],
    _action: dict[str, Any],
    *,
    status_label: str,
    status_variant: str,
    error: str | None,
) -> None:
    """Decorate a snapshot row in-place with a ``delete_variant`` action.

    Identity (SKU + prices) is preserved so the user sees *what* is going
    away; the ``- `` SKU-column gutter + ``deleted`` kind carry the signal.
    The ``_action`` arg is unused (delete carries no field diff) but the
    positional slot is required by the ``CollectionDiffSpec.apply_delete``
    (:class:`_MutateRowFn`) call convention.
    """
    kind: _VariantRowKind = "deleted"
    row["kind"] = kind
    row["status_label"] = status_label
    row["status_variant"] = status_variant
    row["status_prefix"] = STATUS_PREFIX["deleted"]
    row["error"] = error


def merge_variant_rows_for_modify_card(
    prior_state: dict[str, Any] | None,
    actions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Project the prior variants + plan actions into a unified row list.

    Existing variants render unchanged; ``add_variant`` actions append as
    ``added`` rows; ``update_variant`` actions decorate the matched prior
    variant with before→after on SKU / prices; ``delete_variant`` actions mark
    the matched row ``deleted``. Header-only modifies (no variant CRUD) yield
    just the existing variants (or an empty list when prior_state is absent).

    Match key: ``str(variant["id"])`` against ``str(action["target_id"])``.
    Adds have no target_id and synthesize fresh from their ``changes``.
    """
    prior_rows: list[dict[str, Any]] = []
    if isinstance(prior_state, dict):
        candidate = prior_state.get("variants")
        if isinstance(candidate, list):
            prior_rows = [v for v in candidate if isinstance(v, dict)]

    # Filter to variant-CRUD ops before the merge. The item action list also
    # carries ``update_header`` / ``delete`` actions (handled outside the
    # variant table); ``merge_collection_diff_rows`` would otherwise log a
    # "dropped action — unknown operation" warning for each on every
    # header-only modify / item delete. Filtering here keeps the merge's
    # warning meaningful (a genuinely-unknown variant op) and still renders
    # the existing variant rows for those non-variant plans.
    variant_ops = _ADD_OPS | _UPDATE_OPS | _DELETE_OPS
    variant_actions = [
        a for a in actions if str(a.get("operation") or "").lower() in variant_ops
    ]

    return merge_collection_diff_rows(
        prior_rows=prior_rows,
        actions=variant_actions,
        spec=CollectionDiffSpec(
            add_ops=_ADD_OPS,
            update_ops=_UPDATE_OPS,
            delete_ops=_DELETE_OPS,
            key_of=lambda v: str(v["id"]) if v.get("id") is not None else None,
            existing_row=_existing_row_from_snapshot,
            synth_orphan=_synth_orphan_row,
            add_row=_add_action_to_row,
            apply_update=_apply_update_to_row,
            apply_delete=_apply_delete_to_row,
            # Existing variants sort by SKU (None last); adds trail (appended
            # by the skeleton after the sorted snapshot rows).
            sort_key=lambda v: (v.get("sku") is None, v.get("sku") or ""),
        ),
    )


def prepare_variant_table_rows(
    merged: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Compose the final per-row dicts passed to the DataTable.

    The SKU column shows the kind prefix (``+ ``/``- ``/``~ ``/``  ``) inline
    so adds vs deletes are visually obvious even without per-row styling —
    same lexical-gutter trick as the BOM table. SKU-less variants (Katana
    allows them) render ``(no SKU)`` so the row is never blank.
    """
    out: list[dict[str, Any]] = []
    for r in merged:
        sku = r.get("sku") or "(no SKU)"
        out.append({**r, "sku_label": f"{r['status_prefix']}{sku}"})
    return out
