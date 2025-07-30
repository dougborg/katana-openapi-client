import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..models.serial_number_resource_type import SerialNumberResourceType
from ..types import UNSET, Unset

T = TypeVar("T", bound="SerialNumber")


@_attrs_define
class SerialNumber:
    id: Unset | int = UNSET
    transaction_id: Unset | str = UNSET
    serial_number: Unset | str = UNSET
    resource_type: Unset | SerialNumberResourceType = UNSET
    resource_id: Unset | int = UNSET
    transaction_date: Unset | datetime.datetime = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        transaction_id = self.transaction_id

        serial_number = self.serial_number

        resource_type: Unset | str = UNSET
        if not isinstance(self.resource_type, Unset):
            resource_type = self.resource_type.value

        resource_id = self.resource_id

        transaction_date: Unset | str = UNSET
        if not isinstance(self.transaction_date, Unset):
            transaction_date = self.transaction_date.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if transaction_id is not UNSET:
            field_dict["transaction_id"] = transaction_id
        if serial_number is not UNSET:
            field_dict["serial_number"] = serial_number
        if resource_type is not UNSET:
            field_dict["resource_type"] = resource_type
        if resource_id is not UNSET:
            field_dict["resource_id"] = resource_id
        if transaction_date is not UNSET:
            field_dict["transaction_date"] = transaction_date

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id", UNSET)

        transaction_id = d.pop("transaction_id", UNSET)

        serial_number = d.pop("serial_number", UNSET)

        _resource_type = d.pop("resource_type", UNSET)
        resource_type: Unset | SerialNumberResourceType
        if isinstance(_resource_type, Unset):
            resource_type = UNSET
        else:
            resource_type = SerialNumberResourceType(_resource_type)

        resource_id = d.pop("resource_id", UNSET)

        _transaction_date = d.pop("transaction_date", UNSET)
        transaction_date: Unset | datetime.datetime
        if isinstance(_transaction_date, Unset):
            transaction_date = UNSET
        else:
            transaction_date = isoparse(_transaction_date)

        serial_number = cls(
            id=id,
            transaction_id=transaction_id,
            serial_number=serial_number,
            resource_type=resource_type,
            resource_id=resource_id,
            transaction_date=transaction_date,
        )

        serial_number.additional_properties = d
        return serial_number

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
