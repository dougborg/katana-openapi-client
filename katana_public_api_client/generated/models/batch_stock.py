import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="BatchStock")


@_attrs_define
class BatchStock:
    id: int
    batch_number: str
    variant_id: int
    created_at: Unset | datetime.datetime = UNSET
    updated_at: Unset | datetime.datetime = UNSET
    expiration_date: Unset | datetime.datetime = UNSET
    batch_created_date: Unset | datetime.datetime = UNSET
    batch_barcode: None | Unset | str = UNSET
    location_id: Unset | int = UNSET
    quantity_in_stock: Unset | str = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        batch_number = self.batch_number

        variant_id = self.variant_id

        created_at: Unset | str = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: Unset | str = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        expiration_date: Unset | str = UNSET
        if not isinstance(self.expiration_date, Unset):
            expiration_date = self.expiration_date.isoformat()

        batch_created_date: Unset | str = UNSET
        if not isinstance(self.batch_created_date, Unset):
            batch_created_date = self.batch_created_date.isoformat()

        batch_barcode: None | Unset | str
        if isinstance(self.batch_barcode, Unset):
            batch_barcode = UNSET
        else:
            batch_barcode = self.batch_barcode

        location_id = self.location_id

        quantity_in_stock = self.quantity_in_stock

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "batch_number": batch_number,
                "variant_id": variant_id,
            }
        )
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if expiration_date is not UNSET:
            field_dict["expiration_date"] = expiration_date
        if batch_created_date is not UNSET:
            field_dict["batch_created_date"] = batch_created_date
        if batch_barcode is not UNSET:
            field_dict["batch_barcode"] = batch_barcode
        if location_id is not UNSET:
            field_dict["location_id"] = location_id
        if quantity_in_stock is not UNSET:
            field_dict["quantity_in_stock"] = quantity_in_stock

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        batch_number = d.pop("batch_number")

        variant_id = d.pop("variant_id")

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

        _expiration_date = d.pop("expiration_date", UNSET)
        expiration_date: Unset | datetime.datetime
        if isinstance(_expiration_date, Unset):
            expiration_date = UNSET
        else:
            expiration_date = isoparse(_expiration_date)

        _batch_created_date = d.pop("batch_created_date", UNSET)
        batch_created_date: Unset | datetime.datetime
        if isinstance(_batch_created_date, Unset):
            batch_created_date = UNSET
        else:
            batch_created_date = isoparse(_batch_created_date)

        def _parse_batch_barcode(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        batch_barcode = _parse_batch_barcode(d.pop("batch_barcode", UNSET))

        location_id = d.pop("location_id", UNSET)

        quantity_in_stock = d.pop("quantity_in_stock", UNSET)

        batch_stock = cls(
            id=id,
            batch_number=batch_number,
            variant_id=variant_id,
            created_at=created_at,
            updated_at=updated_at,
            expiration_date=expiration_date,
            batch_created_date=batch_created_date,
            batch_barcode=batch_barcode,
            location_id=location_id,
            quantity_in_stock=quantity_in_stock,
        )

        batch_stock.additional_properties = d
        return batch_stock

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
