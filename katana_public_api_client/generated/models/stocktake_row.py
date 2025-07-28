import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="StocktakeRow")


@_attrs_define
class StocktakeRow:
    id: int
    stocktake_id: int
    variant_id: int
    system_quantity: float
    batch_id: None | Unset | int = UNSET
    actual_quantity: None | Unset | float = UNSET
    variance_quantity: None | Unset | float = UNSET
    notes: None | Unset | str = UNSET
    created_at: Unset | datetime.datetime = UNSET
    updated_at: Unset | datetime.datetime = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        stocktake_id = self.stocktake_id

        variant_id = self.variant_id

        system_quantity = self.system_quantity

        batch_id: None | Unset | int
        if isinstance(self.batch_id, Unset):
            batch_id = UNSET
        else:
            batch_id = self.batch_id

        actual_quantity: None | Unset | float
        if isinstance(self.actual_quantity, Unset):
            actual_quantity = UNSET
        else:
            actual_quantity = self.actual_quantity

        variance_quantity: None | Unset | float
        if isinstance(self.variance_quantity, Unset):
            variance_quantity = UNSET
        else:
            variance_quantity = self.variance_quantity

        notes: None | Unset | str
        if isinstance(self.notes, Unset):
            notes = UNSET
        else:
            notes = self.notes

        created_at: Unset | str = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: Unset | str = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "stocktake_id": stocktake_id,
                "variant_id": variant_id,
                "system_quantity": system_quantity,
            }
        )
        if batch_id is not UNSET:
            field_dict["batch_id"] = batch_id
        if actual_quantity is not UNSET:
            field_dict["actual_quantity"] = actual_quantity
        if variance_quantity is not UNSET:
            field_dict["variance_quantity"] = variance_quantity
        if notes is not UNSET:
            field_dict["notes"] = notes
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        stocktake_id = d.pop("stocktake_id")

        variant_id = d.pop("variant_id")

        system_quantity = d.pop("system_quantity")

        def _parse_batch_id(data: object) -> None | Unset | int:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | int, data)

        batch_id = _parse_batch_id(d.pop("batch_id", UNSET))

        def _parse_actual_quantity(data: object) -> None | Unset | float:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | float, data)

        actual_quantity = _parse_actual_quantity(d.pop("actual_quantity", UNSET))

        def _parse_variance_quantity(data: object) -> None | Unset | float:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | float, data)

        variance_quantity = _parse_variance_quantity(d.pop("variance_quantity", UNSET))

        def _parse_notes(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        notes = _parse_notes(d.pop("notes", UNSET))

        _created_at = d.pop("created_at", UNSET)
        created_at: Unset | datetime.datetime
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        _updated_at = d.pop("updated_at", UNSET)
        updated_at: Unset | datetime.datetime
        if isinstance(_updated_at, Unset):
            updated_at = UNSET
        else:
            updated_at = isoparse(_updated_at)

        stocktake_row = cls(
            id=id,
            stocktake_id=stocktake_id,
            variant_id=variant_id,
            system_quantity=system_quantity,
            batch_id=batch_id,
            actual_quantity=actual_quantity,
            variance_quantity=variance_quantity,
            notes=notes,
            created_at=created_at,
            updated_at=updated_at,
        )

        stocktake_row.additional_properties = d
        return stocktake_row

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
