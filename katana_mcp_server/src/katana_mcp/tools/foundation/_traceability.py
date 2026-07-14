"""Shared traceability input for create/update row tools.

Mirrors the wire ``TraceabilityRequest`` (Katana's ``TraceabilityInputItemDto``)
— the unified batch / serial / bin allocation that is the current way to attach
serial-tracked units to a row. Used by ``create_stock_adjustment``,
``create_stock_transfer``, ``fulfill_order`` and ``modify_sales_order``.

Bin transfers keep their own ``BinTransferTraceabilityInput`` (in
``bin_transfers.py``) because that DTO has no ``bin_location_id`` axis — the
row already carries explicit source/target bins.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from katana_public_api_client.client_types import UNSET, Unset
from katana_public_api_client.domain.converters import to_unset
from katana_public_api_client.models import TraceabilityRequest


class TraceabilityInput(BaseModel):
    """A single batch / serial / bin allocation on a create-or-update row.

    Set ``serial_number_id`` to attach (or draw from) a specific
    serial-tracked unit; ``batch_id`` / ``bin_location_id`` pin the
    allocation to a batch and/or bin. Any axis may be omitted.
    """

    model_config = ConfigDict(extra="forbid")

    serial_number_id: int | None = Field(
        default=None,
        description=(
            "Serial number ID to attach / draw for this allocation "
            "(serial-tracked variants). Look up via `list_serial_numbers`."
        ),
    )
    batch_id: int | None = Field(
        default=None,
        description="Batch ID to draw from (batch-tracked variants).",
    )
    bin_location_id: int | None = Field(
        default=None,
        description=("Bin location ID to draw from. Look up via `list_storage_bins`."),
    )
    quantity: float = Field(
        default=1.0,
        description=(
            "Quantity allocated to this axis. Must be non-zero. Serial numbers "
            "use 1; a stock-decrease adjustment that removes a serial-tracked "
            "unit uses a negative quantity (e.g. -1), matching Katana's "
            "non-zero traceability contract."
        ),
    )

    @field_validator("quantity")
    @classmethod
    def _reject_zero_quantity(cls, value: float) -> float:
        # Katana models traceability ``quantity`` as non-zero (negatives are
        # valid for stock-decrease adjustments), so guard only against 0 —
        # not against negatives, which ``gt=0`` would have wrongly rejected.
        if value == 0:
            raise ValueError("traceability quantity must be non-zero")
        return value


def build_traceability_requests(
    items: list[TraceabilityInput] | None,
) -> list[TraceabilityRequest] | Unset:
    """Convert MCP ``TraceabilityInput`` payloads to attrs ``TraceabilityRequest``
    rows.

    ``None`` (the field was omitted) maps to ``UNSET`` so the key is dropped
    from the wire body. An explicit empty list is passed through as ``[]`` —
    preserving caller intent rather than silently collapsing it to "omit", so
    a caller can send an empty ``traceability`` array distinctly from omitting
    the field.
    """
    if items is None:
        return UNSET
    return [
        TraceabilityRequest(
            serial_number_id=to_unset(item.serial_number_id),
            batch_id=to_unset(item.batch_id),
            bin_location_id=to_unset(item.bin_location_id),
            quantity=item.quantity,
        )
        for item in items
    ]
