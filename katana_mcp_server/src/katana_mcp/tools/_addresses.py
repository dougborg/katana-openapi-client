"""Shared address-comparison helper used by impl and UI layers.

Lifted out of ``prefab_ui`` so that ``foundation/*`` impl modules can use
it without pulling the entire Prefab UI module into the tool-execution
path (which also avoided a latent circular-import risk: ``prefab_ui``
already imports a handful of foundation modules).
"""

from __future__ import annotations

from typing import Any

# The exact set of fields ``prefab_ui._render_address_block`` surfaces.
# ``entity_type`` is the label on each block (not part of equivalence);
# server-side fields (id, customer_id, timestamps) don't enter into the
# "is this the same physical place?" judgement.
_USER_VISIBLE_ADDRESS_FIELDS: tuple[str, ...] = (
    "first_name",
    "last_name",
    "company",
    "phone",
    "line_1",
    "line_2",
    "city",
    "state",
    "zip",
    "country",
)


def addresses_are_equivalent(a: dict[str, Any], b: dict[str, Any]) -> bool:
    """Two addresses are equivalent if every user-visible field matches.

    Falsy values (``None``, ``""``) collapse to ``None`` before the
    comparison so a blank string and an unset field don't surface as
    different addresses on the card.
    """
    return all(
        (a.get(k) or None) == (b.get(k) or None) for k in _USER_VISIBLE_ADDRESS_FIELDS
    )
