from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="UpdateStocktakeRowRequest")


@_attrs_define
class UpdateStocktakeRowRequest:
    """Request payload for updating an existing stocktake row

    Example:
        {'counted_quantity': 148.0, 'notes': 'Recount confirmed minor variance'}
    """

    counted_quantity: float | Unset = UNSET
    notes: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        counted_quantity = self.counted_quantity

        notes = self.notes

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if counted_quantity is not UNSET:
            field_dict["counted_quantity"] = counted_quantity
        if notes is not UNSET:
            field_dict["notes"] = notes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        counted_quantity = d.pop("counted_quantity", UNSET)

        notes = d.pop("notes", UNSET)

        update_stocktake_row_request = cls(
            counted_quantity=counted_quantity,
            notes=notes,
        )

        return update_stocktake_row_request
