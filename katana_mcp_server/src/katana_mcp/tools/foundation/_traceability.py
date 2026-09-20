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

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from katana_public_api_client.client_types import UNSET, Unset
from katana_public_api_client.domain.converters import to_unset
from katana_public_api_client.models import (
    ManufacturingOrderIngredientTraceabilityRequest,
    ManufacturingOrderTraceabilityRequest,
    TraceabilityRequest,
)


class ManufacturingOutputAllocation(BaseModel):
    """Allocate produced units to a batch and/or serial; output has no bin axis."""

    model_config = ConfigDict(extra="forbid")

    batch_id: int | None = Field(default=None, description="Produced batch ID")
    serial_number_id: int | None = Field(
        default=None, description="Existing serial number ID for one produced unit"
    )
    quantity: float = Field(default=1, gt=0, description="Produced allocation quantity")

    @model_validator(mode="after")
    def serial_is_one_unit(self) -> Self:
        if self.serial_number_id is not None and self.quantity != 1:
            raise ValueError("A serial allocation must have quantity 1")
        return self


class ManufacturingIngredientAllocation(BaseModel):
    """Draw consumed ingredients from a batch and/or bin; no serial axis."""

    model_config = ConfigDict(extra="forbid")

    batch_id: int | None = Field(default=None, description="Consumed batch ID")
    bin_location_id: int | None = Field(default=None, description="Source bin ID")
    quantity: float = Field(default=1, gt=0, description="Consumed allocation quantity")


def build_manufacturing_output_allocations(
    items: list[ManufacturingOutputAllocation] | None,
) -> list[ManufacturingOrderTraceabilityRequest] | Unset:
    """Omit absent allocations while retaining an explicit empty list."""
    if items is None:
        return UNSET
    return [
        ManufacturingOrderTraceabilityRequest(
            batch_id=to_unset(item.batch_id),
            serial_number_id=to_unset(item.serial_number_id),
            quantity=item.quantity,
        )
        for item in items
    ]


def build_manufacturing_ingredient_allocations(
    items: list[ManufacturingIngredientAllocation] | None,
) -> list[ManufacturingOrderIngredientTraceabilityRequest] | Unset:
    """Convert ingredient allocations without adding the forbidden serial axis."""
    if items is None:
        return UNSET
    return [
        ManufacturingOrderIngredientTraceabilityRequest(
            batch_id=to_unset(item.batch_id),
            bin_location_id=to_unset(item.bin_location_id),
            quantity=item.quantity,
        )
        for item in items
    ]


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
