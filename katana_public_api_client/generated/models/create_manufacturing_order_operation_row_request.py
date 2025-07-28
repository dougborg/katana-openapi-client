from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

T = TypeVar("T", bound="CreateManufacturingOrderOperationRowRequest")


@_attrs_define
class CreateManufacturingOrderOperationRowRequest:
    manufacturing_order_id: int
    operation_id: int
    time: float
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        manufacturing_order_id = self.manufacturing_order_id

        operation_id = self.operation_id

        time = self.time

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "manufacturing_order_id": manufacturing_order_id,
                "operation_id": operation_id,
                "time": time,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        manufacturing_order_id = d.pop("manufacturing_order_id")

        operation_id = d.pop("operation_id")

        time = d.pop("time")

        create_manufacturing_order_operation_row_request = cls(
            manufacturing_order_id=manufacturing_order_id,
            operation_id=operation_id,
            time=time,
        )

        create_manufacturing_order_operation_row_request.additional_properties = d
        return create_manufacturing_order_operation_row_request

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
