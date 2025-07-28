import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="SalesReturnRow")


@_attrs_define
class SalesReturnRow:
    id: int
    sales_return_id: int
    variant_id: int
    quantity: float
    return_reason_id: None | Unset | int = UNSET
    notes: None | Unset | str = UNSET
    unit_price: None | Unset | float = UNSET
    total_price: None | Unset | float = UNSET
    created_at: Unset | datetime.datetime = UNSET
    updated_at: Unset | datetime.datetime = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        sales_return_id = self.sales_return_id

        variant_id = self.variant_id

        quantity = self.quantity

        return_reason_id: None | Unset | int
        if isinstance(self.return_reason_id, Unset):
            return_reason_id = UNSET
        else:
            return_reason_id = self.return_reason_id

        notes: None | Unset | str
        if isinstance(self.notes, Unset):
            notes = UNSET
        else:
            notes = self.notes

        unit_price: None | Unset | float
        if isinstance(self.unit_price, Unset):
            unit_price = UNSET
        else:
            unit_price = self.unit_price

        total_price: None | Unset | float
        if isinstance(self.total_price, Unset):
            total_price = UNSET
        else:
            total_price = self.total_price

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
                "sales_return_id": sales_return_id,
                "variant_id": variant_id,
                "quantity": quantity,
            }
        )
        if return_reason_id is not UNSET:
            field_dict["return_reason_id"] = return_reason_id
        if notes is not UNSET:
            field_dict["notes"] = notes
        if unit_price is not UNSET:
            field_dict["unit_price"] = unit_price
        if total_price is not UNSET:
            field_dict["total_price"] = total_price
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        sales_return_id = d.pop("sales_return_id")

        variant_id = d.pop("variant_id")

        quantity = d.pop("quantity")

        def _parse_return_reason_id(data: object) -> None | Unset | int:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | int, data)

        return_reason_id = _parse_return_reason_id(d.pop("return_reason_id", UNSET))

        def _parse_notes(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        notes = _parse_notes(d.pop("notes", UNSET))

        def _parse_unit_price(data: object) -> None | Unset | float:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | float, data)

        unit_price = _parse_unit_price(d.pop("unit_price", UNSET))

        def _parse_total_price(data: object) -> None | Unset | float:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | float, data)

        total_price = _parse_total_price(d.pop("total_price", UNSET))

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

        sales_return_row = cls(
            id=id,
            sales_return_id=sales_return_id,
            variant_id=variant_id,
            quantity=quantity,
            return_reason_id=return_reason_id,
            notes=notes,
            unit_price=unit_price,
            total_price=total_price,
            created_at=created_at,
            updated_at=updated_at,
        )

        sales_return_row.additional_properties = d
        return sales_return_row

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
