from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..models.serial_number_resource_type import SerialNumberResourceType

T = TypeVar("T", bound="DeleteSerialNumbersRequest")


@_attrs_define
class DeleteSerialNumbersRequest:
    """Request payload for deleting serial numbers from a resource. The
    delete is scoped to a single resource (``resource_type`` +
    ``resource_id``) and a list of serial-number IDs.

        Example:
            {'resource_type': 'ManufacturingOrder', 'resource_id': 3001, 'ids': [1001, 1002]}
    """

    resource_type: SerialNumberResourceType
    resource_id: int
    ids: list[int]

    def to_dict(self) -> dict[str, Any]:
        resource_type = self.resource_type.value

        resource_id = self.resource_id

        ids = self.ids

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "resource_type": resource_type,
                "resource_id": resource_id,
                "ids": ids,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        resource_type = SerialNumberResourceType(d.pop("resource_type"))

        resource_id = d.pop("resource_id")

        ids = cast(list[int], d.pop("ids"))

        delete_serial_numbers_request = cls(
            resource_type=resource_type,
            resource_id=resource_id,
            ids=ids,
        )

        return delete_serial_numbers_request
