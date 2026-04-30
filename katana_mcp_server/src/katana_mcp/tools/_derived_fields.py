"""Registry of server-computed (derived) fields per entity-operation.

Katana computes some fields server-side from other inputs and rejects them
on update — for example, ``landed_cost`` on a purchase-order row is
distributed from PO-level additional costs and cannot be patched directly.
Trying to set such a field via ``modify_<entity>`` produces a generic 422
"At least 1 field is required" because every other patched field was also
derived (the request body collapsed to empty). This registry replaces that
generic failure with a named, actionable error before the API round-trip.

## Layered defense

The primary defense is **the MCP-layer patch models** (``PORowUpdate`` etc.)
not exposing derived fields at all — so callers literally cannot pass them.
Pydantic's default ``extra="ignore"`` silently drops unknown fields at
validation time, which means a caller who tries to set ``landed_cost`` on
``PORowUpdate`` won't even reach this check; their field gets dropped on
construction. That's intentional and good — it's the cleanest UX.

This registry is **defense-in-depth** for the case where a derived field
sneaks onto the MCP-layer patch model — either via a future code change
that widens the model, or via direct construction (in tests, alternate
tool entry points). The dispatch-layer check fires before
``execute_plan`` so the caller sees a named "this field is derived" error
instead of a partial-apply failure mid-plan.

## Adding entries

Keep entries narrow and verified. Each entry records a real rejection
observed against the live Katana API. The PR B audit (driven by
``spec-auditor``) will broaden the registry by sweeping the OpenAPI spec
for fields present on response schemas but absent from
``Update*Request`` schemas.
"""

from __future__ import annotations

from collections.abc import Iterable

from katana_mcp.tools._modification import FieldChange

# ----------------------------------------------------------------------------
# Registry
# ----------------------------------------------------------------------------

# Each entry: derived field name → short workaround hint (or None for "no
# workaround, the field is just not settable"). The hint is appended to the
# error message so the caller sees the canonical alternative.
_DerivedFieldMap = dict[str, str | None]

# Outer key: ``entity_type`` (matches the value passed to ``run_modify_plan``).
# Inner key: ``operation`` string (matches ``ActionSpec.operation`` — the value
# of the per-entity ``*Operation`` enum, e.g. ``"update_row"``).
DERIVED_FIELDS: dict[str, dict[str, _DerivedFieldMap]] = {
    "purchase_order": {
        # PORowUpdate-level derived fields. Currently the MCP-layer
        # PORowUpdate model does NOT expose any of these — pydantic
        # silently drops them at construction. The entries here are
        # registered against future drift: if any of these get added to
        # PORowUpdate, the dispatch check fires before the API call.
        "update_row": {
            "landed_cost": (
                "use modify_purchase_order(add_additional_costs=[...]) with "
                "distribution_method=BY_VALUE — Katana recomputes per-row "
                "landed_cost from distributed additional costs"
            ),
            "total": "computed from quantity * price_per_unit + tax",
            "total_in_base_currency": (
                "computed from total * conversion_rate at the PO header level"
            ),
            "conversion_rate": "set via the PO header (update_header.currency)",
            "conversion_date": "set via the PO header",
        },
    },
}


# ----------------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------------


class DerivedFieldError(ValueError):
    """Raised when a planned action sets a server-derived field.

    Subclasses :class:`ValueError` so it surfaces through the standard
    MCP tool error path without special handling — the message carries
    the field name and workaround hint.
    """


def _lookup(entity_type: str, operation: str) -> _DerivedFieldMap:
    """Look up the derived-field map for ``(entity_type, operation)``.

    Returns an empty dict when no entries exist — callers can iterate
    without a None check.
    """
    return DERIVED_FIELDS.get(entity_type, {}).get(operation, {})


def check_derived_fields(
    *,
    entity_type: str,
    operation: str,
    target_id: int | None,
    diff: Iterable[FieldChange],
) -> None:
    """Raise :class:`DerivedFieldError` if ``diff`` references derived fields.

    Called from the modification dispatcher before plan execution. Walks
    the diff once and raises on the first hit (fail-fast — no partial
    enumeration). The error message names the field, identifies it as
    derived, and includes the registered workaround hint when available.

    Args:
        entity_type: Stable entity-type tag passed to ``run_modify_plan``
            (e.g. ``"purchase_order"``).
        operation: ``ActionSpec.operation`` string for the planned action
            (e.g. ``"update_row"``).
        target_id: Optional id of the action target — used to make the
            error message specific. ``None`` for create-style actions.
        diff: Iterable of :class:`FieldChange` from the action plan.
    """
    derived = _lookup(entity_type, operation)
    if not derived:
        return

    for change in diff:
        if change.field not in derived:
            continue
        hint = derived[change.field]
        target = f" (target {target_id})" if target_id is not None else ""
        msg = (
            f"Field {change.field!r} on {entity_type} {operation}{target} "
            f"is derived — Katana computes it server-side and rejects it "
            f"on update."
        )
        if hint:
            msg = f"{msg} To set this value: {hint}."
        raise DerivedFieldError(msg)


__all__ = [
    "DERIVED_FIELDS",
    "DerivedFieldError",
    "check_derived_fields",
]
