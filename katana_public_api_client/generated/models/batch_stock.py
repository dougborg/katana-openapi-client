from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

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

    batch_number: str
    variant_id: int
    expiration_date: Unset | str = UNSET
    batch_created_date: Unset | str = UNSET
    batch_barcode: None | Unset | str = UNSET
    batch_id: Unset | int = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        batch_number = self.batch_number

        variant_id = self.variant_id

        expiration_date = self.expiration_date

        batch_created_date = self.batch_created_date

        batch_barcode: None | Unset | str
        if isinstance(self.batch_barcode, Unset):
            batch_barcode = UNSET
        else:
            batch_barcode = self.batch_barcode

        batch_id = self.batch_id

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

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        batch_number = d.pop("batch_number")

        variant_id = d.pop("variant_id")

        expiration_date = d.pop("expiration_date", UNSET)

        batch_created_date = d.pop("batch_created_date", UNSET)

        def _parse_batch_barcode(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        batch_barcode = _parse_batch_barcode(d.pop("batch_barcode", UNSET))

        batch_id = d.pop("batch_id", UNSET)

        batch_stock = cls(
            batch_number=batch_number,
            variant_id=variant_id,
            expiration_date=expiration_date,
            batch_created_date=batch_created_date,
            batch_barcode=batch_barcode,
            batch_id=batch_id,
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
