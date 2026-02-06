from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.operator import Operator


T = TypeVar("T", bound="CreateManufacturingOrderOperationRowRequest")


@_attrs_define
class CreateManufacturingOrderOperationRowRequest:
    """Request payload for creating a new manufacturing order operation row to track production operation time and operator
    assignments

        Example:
            {'manufacturing_order_id': 1001, 'operation_id': 201, 'type': 'manual', 'operation_name': 'Assembly',
                'resource_id': 501, 'resource_name': 'Workstation A', 'planned_time_parameter': 1.0, 'planned_time_per_unit':
                15.0, 'cost_parameter': 1.0, 'cost_per_hour': 50.0, 'status': 'NOT_STARTED'}
    """

    manufacturing_order_id: int
    operation_id: int
    type_: str | Unset = UNSET
    operation_name: str | Unset = UNSET
    resource_id: int | Unset = UNSET
    resource_name: str | Unset = UNSET
    planned_time_parameter: float | Unset = UNSET
    planned_time_per_unit: float | Unset = UNSET
    cost_parameter: float | Unset = UNSET
    cost_per_hour: float | Unset = UNSET
    status: str | Unset = UNSET
    assigned_operators: list[Operator] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        manufacturing_order_id = self.manufacturing_order_id

        operation_id = self.operation_id

        type_ = self.type_

        operation_name = self.operation_name

        resource_id = self.resource_id

        resource_name = self.resource_name

        planned_time_parameter = self.planned_time_parameter

        planned_time_per_unit = self.planned_time_per_unit

        cost_parameter = self.cost_parameter

        cost_per_hour = self.cost_per_hour

        status = self.status

        assigned_operators: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.assigned_operators, Unset):
            assigned_operators = []
            for assigned_operators_item_data in self.assigned_operators:
                assigned_operators_item = assigned_operators_item_data.to_dict()
                assigned_operators.append(assigned_operators_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "manufacturing_order_id": manufacturing_order_id,
                "operation_id": operation_id,
            }
        )
        if type_ is not UNSET:
            field_dict["type"] = type_
        if operation_name is not UNSET:
            field_dict["operation_name"] = operation_name
        if resource_id is not UNSET:
            field_dict["resource_id"] = resource_id
        if resource_name is not UNSET:
            field_dict["resource_name"] = resource_name
        if planned_time_parameter is not UNSET:
            field_dict["planned_time_parameter"] = planned_time_parameter
        if planned_time_per_unit is not UNSET:
            field_dict["planned_time_per_unit"] = planned_time_per_unit
        if cost_parameter is not UNSET:
            field_dict["cost_parameter"] = cost_parameter
        if cost_per_hour is not UNSET:
            field_dict["cost_per_hour"] = cost_per_hour
        if status is not UNSET:
            field_dict["status"] = status
        if assigned_operators is not UNSET:
            field_dict["assigned_operators"] = assigned_operators

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.operator import Operator

        d = dict(src_dict)
        manufacturing_order_id = d.pop("manufacturing_order_id")

        operation_id = d.pop("operation_id")

        type_ = d.pop("type", UNSET)

        operation_name = d.pop("operation_name", UNSET)

        resource_id = d.pop("resource_id", UNSET)

        resource_name = d.pop("resource_name", UNSET)

        planned_time_parameter = d.pop("planned_time_parameter", UNSET)

        planned_time_per_unit = d.pop("planned_time_per_unit", UNSET)

        cost_parameter = d.pop("cost_parameter", UNSET)

        cost_per_hour = d.pop("cost_per_hour", UNSET)

        status = d.pop("status", UNSET)

        _assigned_operators = d.pop("assigned_operators", UNSET)
        assigned_operators: list[Operator] | Unset = UNSET
        if _assigned_operators is not UNSET:
            assigned_operators = []
            for assigned_operators_item_data in _assigned_operators:
                assigned_operators_item = Operator.from_dict(
                    assigned_operators_item_data
                )

                assigned_operators.append(assigned_operators_item)

        create_manufacturing_order_operation_row_request = cls(
            manufacturing_order_id=manufacturing_order_id,
            operation_id=operation_id,
            type_=type_,
            operation_name=operation_name,
            resource_id=resource_id,
            resource_name=resource_name,
            planned_time_parameter=planned_time_parameter,
            planned_time_per_unit=planned_time_per_unit,
            cost_parameter=cost_parameter,
            cost_per_hour=cost_per_hour,
            status=status,
            assigned_operators=assigned_operators,
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
