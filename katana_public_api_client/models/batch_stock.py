import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="BatchStock")


@_attrs_define
class BatchStock:
    """Batch inventory record showing current stock levels for a specific batch at a specific location

    Example:
        {'batch_id': 1109, 'batch_number': 'BAT-2024-001', 'batch_created_date': '2024-01-15T08:00:00.000Z',
            'expiration_date': '2025-10-23T10:37:05.085Z', 'location_id': 1, 'variant_id': 1001, 'quantity_in_stock':
            '25.00000', 'batch_barcode': '0317'}

    Attributes:
        batch_number (str): Unique batch number identifier
        variant_id (int): ID of the variant this batch belongs to
        expiration_date (Union[Unset, datetime.datetime]): Batch expiration date (ISO 8601)
        batch_created_date (Union[Unset, datetime.datetime]): Batch creation date (ISO 8601)
        batch_barcode (Union[None, Unset, str]): Optional barcode for the batch
        batch_id (Union[Unset, int]):
        location_id (Union[Unset, int]): ID of the location where the batch is stored
        quantity_in_stock (Union[Unset, str]): Current quantity in stock for this batch
    """

    batch_number: str
    variant_id: int
    expiration_date: Unset | datetime.datetime = UNSET
    batch_created_date: Unset | datetime.datetime = UNSET
    batch_barcode: None | Unset | str = UNSET
    batch_id: Unset | int = UNSET
    location_id: Unset | int = UNSET
    quantity_in_stock: Unset | str = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        batch_number = self.batch_number

        variant_id = self.variant_id

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

        batch_id = self.batch_id

        location_id = self.location_id

        quantity_in_stock = self.quantity_in_stock

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "batch_number": batch_number,
                "variant_id": variant_id,
            }
        )
        if expiration_date is not UNSET:
            field_dict["expiration_date"] = expiration_date
        if batch_created_date is not UNSET:
            field_dict["batch_created_date"] = batch_created_date
        if batch_barcode is not UNSET:
            field_dict["batch_barcode"] = batch_barcode
        if batch_id is not UNSET:
            field_dict["batch_id"] = batch_id
        if location_id is not UNSET:
            field_dict["location_id"] = location_id
        if quantity_in_stock is not UNSET:
            field_dict["quantity_in_stock"] = quantity_in_stock

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        batch_number = d.pop("batch_number")

        variant_id = d.pop("variant_id")

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

        batch_id = d.pop("batch_id", UNSET)

        location_id = d.pop("location_id", UNSET)

        quantity_in_stock = d.pop("quantity_in_stock", UNSET)

        batch_stock = cls(
            batch_number=batch_number,
            variant_id=variant_id,
            expiration_date=expiration_date,
            batch_created_date=batch_created_date,
            batch_barcode=batch_barcode,
            batch_id=batch_id,
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
