from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..models.create_serial_numbers_body_resource_type import (
    CreateSerialNumbersBodyResourceType,
)

T = TypeVar("T", bound="CreateSerialNumbersBody")


@_attrs_define
class CreateSerialNumbersBody:
    resource_type: CreateSerialNumbersBodyResourceType
    resource_id: int
    serial_numbers: list[str]

    def to_dict(self) -> dict[str, Any]:
        resource_type = self.resource_type.value

        resource_id = self.resource_id

        serial_numbers = self.serial_numbers

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "resource_type": resource_type,
                "resource_id": resource_id,
                "serial_numbers": serial_numbers,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        resource_type = CreateSerialNumbersBodyResourceType(d.pop("resource_type"))

        resource_id = d.pop("resource_id")

        serial_numbers = cast(list[str], d.pop("serial_numbers"))

        create_serial_numbers_body = cls(
            resource_type=resource_type,
            resource_id=resource_id,
            serial_numbers=serial_numbers,
        )

        return create_serial_numbers_body
