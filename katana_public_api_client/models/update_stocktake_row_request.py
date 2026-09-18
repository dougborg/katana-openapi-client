from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="UpdateStocktakeRowRequest")


@_attrs_define
class UpdateStocktakeRowRequest:
    """Request payload for updating an existing stocktake row

    Example:
        {'variant_id': 3001, 'batch_id': 501, 'counted_quantity': 148.0, 'notes': 'Recount confirmed minor variance'}
    """

    variant_id: int | Unset = UNSET
    batch_id: int | Unset | None = UNSET
    bin_location_id: int | Unset | None = UNSET
    notes: str | Unset | None = UNSET
    counted_quantity: float | Unset | None = UNSET

    def to_dict(self) -> dict[str, Any]:
        variant_id = self.variant_id

        batch_id: int | Unset | None
        if isinstance(self.batch_id, Unset):
            batch_id = UNSET
        else:
            batch_id = self.batch_id

        bin_location_id: int | Unset | None
        if isinstance(self.bin_location_id, Unset):
            bin_location_id = UNSET
        else:
            bin_location_id = self.bin_location_id

        notes: str | Unset | None
        if isinstance(self.notes, Unset):
            notes = UNSET
        else:
            notes = self.notes

        counted_quantity: float | Unset | None
        if isinstance(self.counted_quantity, Unset):
            counted_quantity = UNSET
        else:
            counted_quantity = self.counted_quantity

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if variant_id is not UNSET:
            field_dict["variant_id"] = variant_id
        if batch_id is not UNSET:
            field_dict["batch_id"] = batch_id
        if bin_location_id is not UNSET:
            field_dict["bin_location_id"] = bin_location_id
        if notes is not UNSET:
            field_dict["notes"] = notes
        if counted_quantity is not UNSET:
            field_dict["counted_quantity"] = counted_quantity

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        variant_id = d.pop("variant_id", UNSET)

        def _parse_batch_id(data: object) -> int | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | Unset | None, data)

        batch_id = _parse_batch_id(d.pop("batch_id", UNSET))

        def _parse_bin_location_id(data: object) -> int | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | Unset | None, data)

        bin_location_id = _parse_bin_location_id(d.pop("bin_location_id", UNSET))

        def _parse_notes(data: object) -> str | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(str | Unset | None, data)

        notes = _parse_notes(d.pop("notes", UNSET))

        def _parse_counted_quantity(data: object) -> float | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | Unset | None, data)

        counted_quantity = _parse_counted_quantity(d.pop("counted_quantity", UNSET))

        update_stocktake_row_request = cls(
            variant_id=variant_id,
            batch_id=batch_id,
            bin_location_id=bin_location_id,
            notes=notes,
            counted_quantity=counted_quantity,
        )

        return update_stocktake_row_request
