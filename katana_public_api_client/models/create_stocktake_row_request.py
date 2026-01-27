from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="CreateStocktakeRowRequest")


@_attrs_define
class CreateStocktakeRowRequest:
    """Request payload for creating a new stocktake row for counting specific variants

    Example:
        {'stocktake_id': 4001, 'variant_id': 3001, 'counted_quantity': 147.0, 'notes': 'Initial count'}
    """

    stocktake_id: int
    variant_id: int
    batch_id: int | Unset = UNSET
    counted_quantity: float | Unset = UNSET
    notes: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        stocktake_id = self.stocktake_id

        variant_id = self.variant_id

        batch_id = self.batch_id

        counted_quantity = self.counted_quantity

        notes = self.notes

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "stocktake_id": stocktake_id,
                "variant_id": variant_id,
            }
        )
        if batch_id is not UNSET:
            field_dict["batch_id"] = batch_id
        if counted_quantity is not UNSET:
            field_dict["counted_quantity"] = counted_quantity
        if notes is not UNSET:
            field_dict["notes"] = notes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:  # type: ignore[misc]
        d = dict(src_dict)
        stocktake_id = d.pop("stocktake_id")

        variant_id = d.pop("variant_id")

        batch_id = d.pop("batch_id", UNSET)

        counted_quantity = d.pop("counted_quantity", UNSET)

        notes = d.pop("notes", UNSET)

        create_stocktake_row_request = cls(
            stocktake_id=stocktake_id,
            variant_id=variant_id,
            batch_id=batch_id,
            counted_quantity=counted_quantity,
            notes=notes,
        )

        return create_stocktake_row_request
