from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.operator import Operator


T = TypeVar("T", bound="UpdateManufacturingOrderOperationRowRequest")


@_attrs_define
class UpdateManufacturingOrderOperationRowRequest:
    completed_by_operators: Unset | list["Operator"] = UNSET
    total_actual_time: Unset | float = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        completed_by_operators: Unset | list[dict[str, Any]] = UNSET
        if not isinstance(self.completed_by_operators, Unset):
            completed_by_operators = []
            for completed_by_operators_item_data in self.completed_by_operators:
                completed_by_operators_item = completed_by_operators_item_data.to_dict()
                completed_by_operators.append(completed_by_operators_item)

        total_actual_time = self.total_actual_time

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if completed_by_operators is not UNSET:
            field_dict["completed_by_operators"] = completed_by_operators
        if total_actual_time is not UNSET:
            field_dict["total_actual_time"] = total_actual_time

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.operator import Operator

        d = dict(src_dict)
        completed_by_operators = []
        _completed_by_operators = d.pop("completed_by_operators", UNSET)
        for completed_by_operators_item_data in _completed_by_operators or []:
            completed_by_operators_item = Operator.from_dict(
                completed_by_operators_item_data
            )

            completed_by_operators.append(completed_by_operators_item)

        total_actual_time = d.pop("total_actual_time", UNSET)

        update_manufacturing_order_operation_row_request = cls(
            completed_by_operators=completed_by_operators,
            total_actual_time=total_actual_time,
        )

        update_manufacturing_order_operation_row_request.additional_properties = d
        return update_manufacturing_order_operation_row_request

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
