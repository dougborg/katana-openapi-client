"""Manufacturing-order collection table-merge helpers (non-UI).

A manufacturing order has three editable collections — recipe rows
(ingredients), operation rows (production steps), and production records — each
of which the MO modify card renders as its own diff table. This module projects
a modify plan (``prior_state`` snapshot + CRUD ``ActionResult`` list) onto the
DataTable row list for each, layered on the shared collection-diff skeleton
(:func:`merge_collection_diff_rows`, #859 / #872). Sibling of
:mod:`po_row_table` / :mod:`item_variant_table` / :mod:`bom_table`.

Per-collection cell builders live here as closures; the skeleton owns the
add/update/delete classification, status stamping, orphan handling, and order.
Row dicts are wire-format (no Prefab types) so they round-trip through
``response.extras`` / iframe ``state`` + JSON.

Net-new MO modify card under the #721 umbrella (Phase 4) — replaces the generic
``ActionResult`` table for ``modify_manufacturing_order`` / ``delete_manufacturing_order``.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from katana_mcp.tools.foundation.collection_diff import (
    STATUS_PREFIX,
    STATUS_VARIANTS,
    CollectionDiffSpec,
    merge_collection_diff_rows,
)

# Resolved-variant lookup ``{variant_id: {"sku", "display_name"}}`` threaded
# from the impl's batched cache lookup (``extras["resolved_variants"]``) —
# needed for *added* recipe rows (existing rows already carry resolved names).
ResolvedVariants = dict[int, dict[str, str | None]]

# ``MOOperation`` StrEnum values, grouped per collection (manufacturing_orders.py).
_RECIPE_ADD = frozenset({"add_recipe_row"})
_RECIPE_UPDATE = frozenset({"update_recipe_row"})
_RECIPE_DELETE = frozenset({"delete_recipe_row"})
_OP_ADD = frozenset({"add_operation_row"})
_OP_UPDATE = frozenset({"update_operation_row"})
_OP_DELETE = frozenset({"delete_operation_row"})
_PROD_ADD = frozenset({"add_production"})
_PROD_UPDATE = frozenset({"update_production"})
_PROD_DELETE = frozenset({"delete_production"})


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
    """Render a quantity / time for a table cell, trimmed of trailing zeros.

    ``None`` → em-dash. ``Decimal`` (the shape ``compute_field_diff`` →
    ``_normalize`` produces) and ``float`` render via ``:g``; numeric strings
    coerce first. Mirrors ``po_row_table._format_number``.
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


def _format_text(value: Any) -> str:
    """Render a text cell (``None`` / empty → em-dash)."""
    if value is None or value == "":
        return "—"
    return str(value)


def _format_text_diff(old: Any, new: Any) -> str:
    """Render a text update as ``old → new`` (em-dash for missing sides)."""
    return f"{_format_text(old)} → {_format_text(new)}"


def _format_date(value: Any) -> str:
    """Trim an ISO datetime string to its ``YYYY-MM-DD`` date (or em-dash)."""
    if not value:
        return "—"
    text = str(value)
    return text[:10] if len(text) >= 10 else text


def _format_date_diff(old: Any, new: Any) -> str:
    return f"{_format_date(old)} → {_format_date(new)}"


def _resolved_name(
    resolved: ResolvedVariants, variant_id: Any
) -> tuple[str | None, str | None]:
    """Look up ``(sku, display_name)`` for a variant id (``(None, None)`` miss)."""
    if isinstance(variant_id, int):
        hit = resolved.get(variant_id)
        if hit:
            return hit.get("sku"), hit.get("display_name")
    return None, None


def _base_row(
    *, kind: str, prefix: str, status_label: str, status_variant: str
) -> dict[str, Any]:
    """Shared row scaffold (kind + status bookkeeping)."""
    return {
        "kind": kind,
        "status_label": status_label,
        "status_variant": status_variant,
        "status_prefix": prefix,
        "error": None,
    }


def _prior_rows(prior_state: dict[str, Any] | None, key: str) -> list[dict[str, Any]]:
    if not isinstance(prior_state, dict):
        return []
    candidate = prior_state.get(key)
    return (
        [r for r in candidate if isinstance(r, dict)]
        if isinstance(candidate, list)
        else []
    )


def _key_of(row: dict[str, Any]) -> str | None:
    return str(row["id"]) if row.get("id") is not None else None


# ---------------------------------------------------------------------------
# Recipe rows (ingredients): SKU / Name / Qty per unit
# ---------------------------------------------------------------------------


def merge_recipe_rows_for_modify_card(
    prior_state: dict[str, Any] | None,
    actions: list[dict[str, Any]],
    resolved_variants: ResolvedVariants | None,
) -> list[dict[str, Any]]:
    """Project prior recipe rows + recipe-row actions into a unified row list.

    Existing rows (``prior_state["recipe_rows"]``, enriched ``RecipeRowInfo``
    dumps carrying resolved ``sku`` / ``display_name``) render unchanged; adds
    resolve their SKU/name from the new ``variant_id`` via ``resolved_variants``;
    updates decorate the ``planned_quantity_per_unit`` diff (and re-resolve on a
    variant swap); deletes preserve identity.
    """
    resolved = resolved_variants or {}

    def existing(row: dict[str, Any]) -> dict[str, Any]:
        return {
            **_base_row(
                kind="existing",
                prefix=STATUS_PREFIX["existing"],
                status_label="",
                status_variant=STATUS_VARIANTS[""],
            ),
            "id": row.get("id"),
            "variant_id": row.get("variant_id"),
            "sku": row.get("sku"),
            "display_name": row.get("display_name"),
            "quantity_label": _format_number(row.get("planned_quantity_per_unit")),
        }

    def orphan(target_id: str) -> dict[str, Any]:
        return {
            **_base_row(
                kind="existing",
                prefix=STATUS_PREFIX["existing"],
                status_label="",
                status_variant=STATUS_VARIANTS[""],
            ),
            "id": target_id,
            "variant_id": None,
            "sku": None,
            "display_name": None,
            "quantity_label": "—",
        }

    def add(action, *, status_label, status_variant, error) -> dict[str, Any]:
        ch = _changes_by_field(action.get("changes"))
        vid = ch.get("variant_id", {}).get("new")
        sku, name = _resolved_name(resolved, vid)
        qty = ch.get("planned_quantity_per_unit")
        return {
            **_base_row(
                kind="added",
                prefix=STATUS_PREFIX["added"],
                status_label=status_label,
                status_variant=status_variant,
            ),
            "id": "",
            "variant_id": vid,
            "sku": sku,
            "display_name": name,
            "quantity_label": _format_number(qty.get("new") if qty else None),
            "error": error,
        }

    def update(row, action, *, status_label, status_variant, error) -> None:
        row.update(
            _base_row(
                kind="updated",
                prefix=STATUS_PREFIX["updated"],
                status_label=status_label,
                status_variant=status_variant,
            )
        )
        row["error"] = error
        ch = _changes_by_field(action.get("changes"))
        qty = ch.get("planned_quantity_per_unit")
        if qty is not None:
            row["quantity_label"] = _format_number_diff(
                qty.get("old"),
                qty.get("new"),
                unknown_prior=bool(qty.get("is_unknown_prior")),
            )
        variant = ch.get("variant_id")
        if variant is not None:
            sku, name = _resolved_name(resolved, variant.get("new"))
            row["variant_id"] = variant.get("new")
            row["sku"] = sku
            row["display_name"] = name

    def delete(row, _action, *, status_label, status_variant, error) -> None:
        row.update(
            _base_row(
                kind="deleted",
                prefix=STATUS_PREFIX["deleted"],
                status_label=status_label,
                status_variant=status_variant,
            )
        )
        row["error"] = error

    return merge_collection_diff_rows(
        prior_rows=_prior_rows(prior_state, "recipe_rows"),
        actions=[
            a
            for a in actions
            if str(a.get("operation") or "").lower()
            in (_RECIPE_ADD | _RECIPE_UPDATE | _RECIPE_DELETE)
        ],
        spec=CollectionDiffSpec(
            add_ops=_RECIPE_ADD,
            update_ops=_RECIPE_UPDATE,
            delete_ops=_RECIPE_DELETE,
            key_of=_key_of,
            existing_row=existing,
            synth_orphan=orphan,
            add_row=add,
            apply_update=update,
            apply_delete=delete,
            sort_key=lambda r: 0,
        ),
    )


def prepare_recipe_table_rows(merged: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """SKU column carries the kind gutter; name falls back to ``variant <id>``."""
    out: list[dict[str, Any]] = []
    for r in merged:
        sku = r.get("sku") or "(unresolved)"
        name = r.get("display_name") or ""
        if not name and r.get("variant_id") is not None:
            name = f"variant {r['variant_id']}"
        out.append(
            {**r, "sku_label": f"{r['status_prefix']}{sku}", "display_name": name}
        )
    return out


# ---------------------------------------------------------------------------
# Operation rows: Operation name / workflow status
# ---------------------------------------------------------------------------


def merge_operation_rows_for_modify_card(
    prior_state: dict[str, Any] | None,
    actions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Project prior operation rows + operation-row actions into a row list.

    Cells: operation name + the operation's *workflow* status (NOT_STARTED /
    IN_PROGRESS / … — distinct from the diff-table action Status). Adds /
    updates decorate name + status; deletes preserve identity.
    """

    def existing(row: dict[str, Any]) -> dict[str, Any]:
        return {
            **_base_row(
                kind="existing",
                prefix=STATUS_PREFIX["existing"],
                status_label="",
                status_variant=STATUS_VARIANTS[""],
            ),
            "id": row.get("id"),
            "operation_label": _format_text(row.get("operation_name")),
            "op_status_label": _format_text(row.get("status")),
        }

    def orphan(target_id: str) -> dict[str, Any]:
        return {
            **_base_row(
                kind="existing",
                prefix=STATUS_PREFIX["existing"],
                status_label="",
                status_variant=STATUS_VARIANTS[""],
            ),
            "id": target_id,
            "operation_label": "—",
            "op_status_label": "—",
        }

    def add(action, *, status_label, status_variant, error) -> dict[str, Any]:
        ch = _changes_by_field(action.get("changes"))
        name = ch.get("operation_name", {}).get("new")
        op_status = ch.get("status", {}).get("new")
        return {
            **_base_row(
                kind="added",
                prefix=STATUS_PREFIX["added"],
                status_label=status_label,
                status_variant=status_variant,
            ),
            "id": "",
            "operation_label": _format_text(name),
            "op_status_label": _format_text(op_status),
            "error": error,
        }

    def update(row, action, *, status_label, status_variant, error) -> None:
        row.update(
            _base_row(
                kind="updated",
                prefix=STATUS_PREFIX["updated"],
                status_label=status_label,
                status_variant=status_variant,
            )
        )
        row["error"] = error
        ch = _changes_by_field(action.get("changes"))
        name = ch.get("operation_name")
        if name is not None:
            row["operation_label"] = _format_text_diff(name.get("old"), name.get("new"))
        op_status = ch.get("status")
        if op_status is not None:
            row["op_status_label"] = _format_text_diff(
                op_status.get("old"), op_status.get("new")
            )

    def delete(row, _action, *, status_label, status_variant, error) -> None:
        row.update(
            _base_row(
                kind="deleted",
                prefix=STATUS_PREFIX["deleted"],
                status_label=status_label,
                status_variant=status_variant,
            )
        )
        row["error"] = error

    return merge_collection_diff_rows(
        prior_rows=_prior_rows(prior_state, "operation_rows"),
        actions=[
            a
            for a in actions
            if str(a.get("operation") or "").lower()
            in (_OP_ADD | _OP_UPDATE | _OP_DELETE)
        ],
        spec=CollectionDiffSpec(
            add_ops=_OP_ADD,
            update_ops=_OP_UPDATE,
            delete_ops=_OP_DELETE,
            key_of=_key_of,
            existing_row=existing,
            synth_orphan=orphan,
            add_row=add,
            apply_update=update,
            apply_delete=delete,
            sort_key=lambda r: 0,
        ),
    )


def prepare_operation_table_rows(merged: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Operation column carries the kind gutter."""
    return [
        {**r, "operation_label_gutter": f"{r['status_prefix']}{r['operation_label']}"}
        for r in merged
    ]


# ---------------------------------------------------------------------------
# Productions: quantity / date
# ---------------------------------------------------------------------------


def merge_productions_for_modify_card(
    prior_state: dict[str, Any] | None,
    actions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Project prior production records + production actions into a row list.

    Existing rows (``ProductionInfo``: ``quantity`` / ``production_date``);
    adds read the ``completed_quantity`` / ``completed_date`` payload fields;
    updates decorate the ``production_date`` diff.
    """

    def existing(row: dict[str, Any]) -> dict[str, Any]:
        return {
            **_base_row(
                kind="existing",
                prefix=STATUS_PREFIX["existing"],
                status_label="",
                status_variant=STATUS_VARIANTS[""],
            ),
            "id": row.get("id"),
            "quantity_label": _format_number(row.get("quantity")),
            "date_label": _format_date(row.get("production_date")),
        }

    def orphan(target_id: str) -> dict[str, Any]:
        return {
            **_base_row(
                kind="existing",
                prefix=STATUS_PREFIX["existing"],
                status_label="",
                status_variant=STATUS_VARIANTS[""],
            ),
            "id": target_id,
            "quantity_label": "—",
            "date_label": "—",
        }

    def add(action, *, status_label, status_variant, error) -> dict[str, Any]:
        ch = _changes_by_field(action.get("changes"))
        qty = ch.get("completed_quantity", {}).get("new")
        date = ch.get("completed_date", {}).get("new")
        return {
            **_base_row(
                kind="added",
                prefix=STATUS_PREFIX["added"],
                status_label=status_label,
                status_variant=status_variant,
            ),
            "id": "",
            "quantity_label": _format_number(qty),
            "date_label": _format_date(date),
            "error": error,
        }

    def update(row, action, *, status_label, status_variant, error) -> None:
        row.update(
            _base_row(
                kind="updated",
                prefix=STATUS_PREFIX["updated"],
                status_label=status_label,
                status_variant=status_variant,
            )
        )
        row["error"] = error
        ch = _changes_by_field(action.get("changes"))
        date = ch.get("production_date")
        if date is not None:
            row["date_label"] = _format_date_diff(date.get("old"), date.get("new"))

    def delete(row, _action, *, status_label, status_variant, error) -> None:
        row.update(
            _base_row(
                kind="deleted",
                prefix=STATUS_PREFIX["deleted"],
                status_label=status_label,
                status_variant=status_variant,
            )
        )
        row["error"] = error

    return merge_collection_diff_rows(
        prior_rows=_prior_rows(prior_state, "productions"),
        actions=[
            a
            for a in actions
            if str(a.get("operation") or "").lower()
            in (_PROD_ADD | _PROD_UPDATE | _PROD_DELETE)
        ],
        spec=CollectionDiffSpec(
            add_ops=_PROD_ADD,
            update_ops=_PROD_UPDATE,
            delete_ops=_PROD_DELETE,
            key_of=_key_of,
            existing_row=existing,
            synth_orphan=orphan,
            add_row=add,
            apply_update=update,
            apply_delete=delete,
            sort_key=lambda r: 0,
        ),
    )


def prepare_production_table_rows(merged: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Quantity column carries the kind gutter."""
    return [
        {**r, "quantity_label_gutter": f"{r['status_prefix']}{r['quantity_label']}"}
        for r in merged
    ]
