import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="BatchResponse")


@_attrs_define
class BatchResponse:
    batch_number: str
    variant_id: int
    expiration_date: Unset | str = UNSET
    batch_created_date: Unset | str = UNSET
    batch_barcode: None | Unset | str = UNSET
    id: Unset | int = UNSET
    created_at: Unset | datetime.datetime = UNSET
    updated_at: Unset | datetime.datetime = UNSET
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

        id = self.id

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
        if id is not UNSET:
            field_dict["id"] = id
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at

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

        id = d.pop("id", UNSET)

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

        batch_response = cls(
            batch_number=batch_number,
            variant_id=variant_id,
            expiration_date=expiration_date,
            batch_created_date=batch_created_date,
            batch_barcode=batch_barcode,
            id=id,
            created_at=created_at,
            updated_at=updated_at,
        )

        batch_response.additional_properties = d
        return batch_response

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
