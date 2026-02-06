from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="CreateStocktakeRowRequestStocktakeRowsItem")


@_attrs_define
class CreateStocktakeRowRequestStocktakeRowsItem:
    variant_id: int
    batch_id: int | None | Unset = UNSET
    notes: None | str | Unset = UNSET
    counted_quantity: float | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        variant_id = self.variant_id

        batch_id: int | None | Unset
        if isinstance(self.batch_id, Unset):
            batch_id = UNSET
        else:
            batch_id = self.batch_id

        notes: None | str | Unset
        if isinstance(self.notes, Unset):
            notes = UNSET
        else:
            notes = self.notes

        counted_quantity: float | None | Unset
        if isinstance(self.counted_quantity, Unset):
            counted_quantity = UNSET
        else:
            counted_quantity = self.counted_quantity

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "variant_id": variant_id,
            }
        )
        if batch_id is not UNSET:
            field_dict["batch_id"] = batch_id
        if notes is not UNSET:
            field_dict["notes"] = notes
        if counted_quantity is not UNSET:
            field_dict["counted_quantity"] = counted_quantity

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        variant_id = d.pop("variant_id")

        def _parse_batch_id(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        batch_id = _parse_batch_id(d.pop("batch_id", UNSET))

        def _parse_notes(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        notes = _parse_notes(d.pop("notes", UNSET))

        def _parse_counted_quantity(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        counted_quantity = _parse_counted_quantity(d.pop("counted_quantity", UNSET))

        create_stocktake_row_request_stocktake_rows_item = cls(
            variant_id=variant_id,
            batch_id=batch_id,
            notes=notes,
            counted_quantity=counted_quantity,
        )

        return create_stocktake_row_request_stocktake_rows_item
