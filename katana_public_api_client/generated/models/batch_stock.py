import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="BatchStock")


@_attrs_define
class BatchStock:
    """
    Example:
        {'batch_id': 1109, 'batch_number': 'B2', 'batch_created_date': '2020-09-29T11:40:29.628Z', 'expiration_date':
            '2021-04-30T10:35:00.000Z', 'location_id': 1433, 'variant_id': 350880, 'quantity_in_stock': '10.00000',
            'batch_barcode': '0317'}
    """

    batch_id: Unset | int = UNSET
    batch_number: Unset | str = UNSET
    batch_created_date: Unset | datetime.datetime = UNSET
    expiration_date: Unset | datetime.datetime = UNSET
    location_id: Unset | int = UNSET
    variant_id: Unset | int = UNSET
    quantity_in_stock: Unset | str = UNSET
    batch_barcode: Unset | str = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        batch_id = self.batch_id

        batch_number = self.batch_number

        batch_created_date: Unset | str = UNSET
        if not isinstance(self.batch_created_date, Unset):
            batch_created_date = self.batch_created_date.isoformat()

        expiration_date: Unset | str = UNSET
        if not isinstance(self.expiration_date, Unset):
            expiration_date = self.expiration_date.isoformat()

        location_id = self.location_id

        variant_id = self.variant_id

        quantity_in_stock = self.quantity_in_stock

        batch_barcode = self.batch_barcode

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if batch_id is not UNSET:
            field_dict["batch_id"] = batch_id
        if batch_number is not UNSET:
            field_dict["batch_number"] = batch_number
        if batch_created_date is not UNSET:
            field_dict["batch_created_date"] = batch_created_date
        if expiration_date is not UNSET:
            field_dict["expiration_date"] = expiration_date
        if location_id is not UNSET:
            field_dict["location_id"] = location_id
        if variant_id is not UNSET:
            field_dict["variant_id"] = variant_id
        if quantity_in_stock is not UNSET:
            field_dict["quantity_in_stock"] = quantity_in_stock
        if batch_barcode is not UNSET:
            field_dict["batch_barcode"] = batch_barcode

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        batch_id = d.pop("batch_id", UNSET)

        batch_number = d.pop("batch_number", UNSET)

        _batch_created_date = d.pop("batch_created_date", UNSET)
        batch_created_date: Unset | datetime.datetime
        if isinstance(_batch_created_date, Unset):
            batch_created_date = UNSET
        else:
            batch_created_date = isoparse(_batch_created_date)

        _expiration_date = d.pop("expiration_date", UNSET)
        expiration_date: Unset | datetime.datetime
        if isinstance(_expiration_date, Unset):
            expiration_date = UNSET
        else:
            expiration_date = isoparse(_expiration_date)

        location_id = d.pop("location_id", UNSET)

        variant_id = d.pop("variant_id", UNSET)

        quantity_in_stock = d.pop("quantity_in_stock", UNSET)

        batch_barcode = d.pop("batch_barcode", UNSET)

        batch_stock = cls(
            batch_id=batch_id,
            batch_number=batch_number,
            batch_created_date=batch_created_date,
            expiration_date=expiration_date,
            location_id=location_id,
            variant_id=variant_id,
            quantity_in_stock=quantity_in_stock,
            batch_barcode=batch_barcode,
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
