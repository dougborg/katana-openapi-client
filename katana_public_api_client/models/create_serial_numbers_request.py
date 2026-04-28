from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset
from ..models.create_serial_number_resource_type import CreateSerialNumberResourceType

T = TypeVar("T", bound="CreateSerialNumbersRequest")


@_attrs_define
class CreateSerialNumbersRequest:
    """Request payload for creating serial numbers for a resource"""

    resource_id: int
    resource_type: CreateSerialNumberResourceType | Unset = UNSET
    serial_numbers: list[str] | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        resource_id = self.resource_id

        resource_type: str | Unset = UNSET
        if not isinstance(self.resource_type, Unset):
            resource_type = self.resource_type.value

        serial_numbers: list[str] | Unset = UNSET
        if not isinstance(self.serial_numbers, Unset):
            serial_numbers = self.serial_numbers

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "resource_id": resource_id,
            }
        )
        if resource_type is not UNSET:
            field_dict["resource_type"] = resource_type
        if serial_numbers is not UNSET:
            field_dict["serial_numbers"] = serial_numbers

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        resource_id = d.pop("resource_id")

        _resource_type = d.pop("resource_type", UNSET)
        resource_type: CreateSerialNumberResourceType | Unset
        if isinstance(_resource_type, Unset):
            resource_type = UNSET
        else:
            resource_type = CreateSerialNumberResourceType(_resource_type)

        serial_numbers = cast(list[str], d.pop("serial_numbers", UNSET))

        create_serial_numbers_request = cls(
            resource_id=resource_id,
            resource_type=resource_type,
            serial_numbers=serial_numbers,
        )

        return create_serial_numbers_request
