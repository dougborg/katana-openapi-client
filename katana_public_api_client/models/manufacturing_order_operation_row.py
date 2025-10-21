import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset
from ..models.manufacturing_order_operation_row_status import (
    ManufacturingOrderOperationRowStatus,
)

if TYPE_CHECKING:
    from ..models.assigned_operator import AssignedOperator


T = TypeVar("T", bound="ManufacturingOrderOperationRow")


@_attrs_define
class ManufacturingOrderOperationRow:
    """Represents an individual operation step within a manufacturing order, tracking production operations, operator
    assignments, time, and costs.

        Example:
            {'id': 3801, 'status': 'IN_PROGRESS', 'type': 'Production', 'rank': 1, 'manufacturing_order_id': 3001,
                'operation_id': 401, 'operation_name': 'Cut Steel Sheets', 'resource_id': 501, 'resource_name': 'Laser Cutting
                Machine', 'assigned_operators': [{'id': 101, 'operator_id': 101, 'name': 'John Smith', 'working_area':
                'Production Floor A', 'resource_id': 501}], 'completed_by_operators': [], 'active_operator_id': 101,
                'planned_time_per_unit': 15.0, 'planned_time_parameter': 1.0, 'total_actual_time': 12.5,
                'planned_cost_per_unit': 45.0, 'total_actual_cost': 37.5, 'cost_per_hour': 180.0, 'cost_parameter': 1.0,
                'group_boundary': 0, 'is_status_actionable': True, 'completed_at': None, 'created_at': '2024-01-15T08:00:00Z',
                'updated_at': '2024-01-20T14:30:00Z', 'deleted_at': None}

        Attributes:
            id (int): Unique identifier
            created_at (Union[Unset, datetime.datetime]): Timestamp when the entity was first created
            updated_at (Union[Unset, datetime.datetime]): Timestamp when the entity was last updated
            deleted_at (Union[None, Unset, datetime.datetime]): Nullable deletion timestamp
            status (Union[Unset, ManufacturingOrderOperationRowStatus]): Current status of the operation
            type_ (Union[Unset, str]): Type classification of the operation
            rank (Union[Unset, float]): Order/sequence of this operation within the manufacturing process
            manufacturing_order_id (Union[Unset, int]): ID of the manufacturing order this operation belongs to
            operation_id (Union[Unset, int]): ID of the operation template or definition
            operation_name (Union[Unset, str]): Name of the operation being performed
            resource_id (Union[Unset, int]): ID of the resource (machine/workstation) used for this operation
            resource_name (Union[Unset, str]): Name of the resource (machine/workstation) used
            assigned_operators (Union[Unset, list['AssignedOperator']]): Operators assigned to perform this operation
            completed_by_operators (Union[Unset, list['AssignedOperator']]): Operators who have completed work on this
                operation
            active_operator_id (Union[Unset, float]): ID of the currently active operator working on this operation
            planned_time_per_unit (Union[Unset, float]): Planned time per unit for this operation
            planned_time_parameter (Union[Unset, float]): Parameter for calculating planned time
            total_actual_time (Union[Unset, float]): Total actual time spent on this operation
            planned_cost_per_unit (Union[Unset, float]): Planned cost per unit for this operation
            total_actual_cost (Union[Unset, float]): Total actual cost incurred for this operation
            cost_per_hour (Union[Unset, float]): Hourly cost rate for this operation
            cost_parameter (Union[Unset, float]): Parameter for calculating operation costs
            group_boundary (Union[Unset, float]): Group boundary setting for operation grouping
            is_status_actionable (Union[Unset, bool]): Whether the current status allows for operator actions
            completed_at (Union[None, Unset, datetime.datetime]): Date and time when the operation was completed, null if
                not completed
    """

    id: int
    created_at: Unset | datetime.datetime = UNSET
    updated_at: Unset | datetime.datetime = UNSET
    deleted_at: None | Unset | datetime.datetime = UNSET
    status: Unset | ManufacturingOrderOperationRowStatus = UNSET
    type_: Unset | str = UNSET
    rank: Unset | float = UNSET
    manufacturing_order_id: Unset | int = UNSET
    operation_id: Unset | int = UNSET
    operation_name: Unset | str = UNSET
    resource_id: Unset | int = UNSET
    resource_name: Unset | str = UNSET
    assigned_operators: Unset | list["AssignedOperator"] = UNSET
    completed_by_operators: Unset | list["AssignedOperator"] = UNSET
    active_operator_id: Unset | float = UNSET
    planned_time_per_unit: Unset | float = UNSET
    planned_time_parameter: Unset | float = UNSET
    total_actual_time: Unset | float = UNSET
    planned_cost_per_unit: Unset | float = UNSET
    total_actual_cost: Unset | float = UNSET
    cost_per_hour: Unset | float = UNSET
    cost_parameter: Unset | float = UNSET
    group_boundary: Unset | float = UNSET
    is_status_actionable: Unset | bool = UNSET
    completed_at: None | Unset | datetime.datetime = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        created_at: Unset | str = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: Unset | str = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        deleted_at: None | Unset | str
        if isinstance(self.deleted_at, Unset):
            deleted_at = UNSET
        elif isinstance(self.deleted_at, datetime.datetime):
            deleted_at = self.deleted_at.isoformat()
        else:
            deleted_at = self.deleted_at

        status: Unset | str = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        type_ = self.type_

        rank = self.rank

        manufacturing_order_id = self.manufacturing_order_id

        operation_id = self.operation_id

        operation_name = self.operation_name

        resource_id = self.resource_id

        resource_name = self.resource_name

        assigned_operators: Unset | list[dict[str, Any]] = UNSET
        if not isinstance(self.assigned_operators, Unset):
            assigned_operators = []
            for assigned_operators_item_data in self.assigned_operators:
                assigned_operators_item = assigned_operators_item_data.to_dict()
                assigned_operators.append(assigned_operators_item)

        completed_by_operators: Unset | list[dict[str, Any]] = UNSET
        if not isinstance(self.completed_by_operators, Unset):
            completed_by_operators = []
            for completed_by_operators_item_data in self.completed_by_operators:
                completed_by_operators_item = completed_by_operators_item_data.to_dict()
                completed_by_operators.append(completed_by_operators_item)

        active_operator_id = self.active_operator_id

        planned_time_per_unit = self.planned_time_per_unit

        planned_time_parameter = self.planned_time_parameter

        total_actual_time = self.total_actual_time

        planned_cost_per_unit = self.planned_cost_per_unit

        total_actual_cost = self.total_actual_cost

        cost_per_hour = self.cost_per_hour

        cost_parameter = self.cost_parameter

        group_boundary = self.group_boundary

        is_status_actionable = self.is_status_actionable

        completed_at: None | Unset | str
        if isinstance(self.completed_at, Unset):
            completed_at = UNSET
        elif isinstance(self.completed_at, datetime.datetime):
            completed_at = self.completed_at.isoformat()
        else:
            completed_at = self.completed_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
            }
        )
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if deleted_at is not UNSET:
            field_dict["deleted_at"] = deleted_at
        if status is not UNSET:
            field_dict["status"] = status
        if type_ is not UNSET:
            field_dict["type"] = type_
        if rank is not UNSET:
            field_dict["rank"] = rank
        if manufacturing_order_id is not UNSET:
            field_dict["manufacturing_order_id"] = manufacturing_order_id
        if operation_id is not UNSET:
            field_dict["operation_id"] = operation_id
        if operation_name is not UNSET:
            field_dict["operation_name"] = operation_name
        if resource_id is not UNSET:
            field_dict["resource_id"] = resource_id
        if resource_name is not UNSET:
            field_dict["resource_name"] = resource_name
        if assigned_operators is not UNSET:
            field_dict["assigned_operators"] = assigned_operators
        if completed_by_operators is not UNSET:
            field_dict["completed_by_operators"] = completed_by_operators
        if active_operator_id is not UNSET:
            field_dict["active_operator_id"] = active_operator_id
        if planned_time_per_unit is not UNSET:
            field_dict["planned_time_per_unit"] = planned_time_per_unit
        if planned_time_parameter is not UNSET:
            field_dict["planned_time_parameter"] = planned_time_parameter
        if total_actual_time is not UNSET:
            field_dict["total_actual_time"] = total_actual_time
        if planned_cost_per_unit is not UNSET:
            field_dict["planned_cost_per_unit"] = planned_cost_per_unit
        if total_actual_cost is not UNSET:
            field_dict["total_actual_cost"] = total_actual_cost
        if cost_per_hour is not UNSET:
            field_dict["cost_per_hour"] = cost_per_hour
        if cost_parameter is not UNSET:
            field_dict["cost_parameter"] = cost_parameter
        if group_boundary is not UNSET:
            field_dict["group_boundary"] = group_boundary
        if is_status_actionable is not UNSET:
            field_dict["is_status_actionable"] = is_status_actionable
        if completed_at is not UNSET:
            field_dict["completed_at"] = completed_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.assigned_operator import AssignedOperator

        d = dict(src_dict)
        id = d.pop("id")

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

        def _parse_deleted_at(data: object) -> None | Unset | datetime.datetime:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                deleted_at_type_0 = isoparse(data)

                return deleted_at_type_0
            except:  # noqa: E722
                pass
            return cast(None | Unset | datetime.datetime, data)

        deleted_at = _parse_deleted_at(d.pop("deleted_at", UNSET))

        _status = d.pop("status", UNSET)
        status: Unset | ManufacturingOrderOperationRowStatus
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = ManufacturingOrderOperationRowStatus(_status)

        type_ = d.pop("type", UNSET)

        rank = d.pop("rank", UNSET)

        manufacturing_order_id = d.pop("manufacturing_order_id", UNSET)

        operation_id = d.pop("operation_id", UNSET)

        operation_name = d.pop("operation_name", UNSET)

        resource_id = d.pop("resource_id", UNSET)

        resource_name = d.pop("resource_name", UNSET)

        assigned_operators = []
        _assigned_operators = d.pop("assigned_operators", UNSET)
        for assigned_operators_item_data in _assigned_operators or []:
            assigned_operators_item = AssignedOperator.from_dict(
                assigned_operators_item_data
            )

            assigned_operators.append(assigned_operators_item)

        completed_by_operators = []
        _completed_by_operators = d.pop("completed_by_operators", UNSET)
        for completed_by_operators_item_data in _completed_by_operators or []:
            completed_by_operators_item = AssignedOperator.from_dict(
                completed_by_operators_item_data
            )

            completed_by_operators.append(completed_by_operators_item)

        active_operator_id = d.pop("active_operator_id", UNSET)

        planned_time_per_unit = d.pop("planned_time_per_unit", UNSET)

        planned_time_parameter = d.pop("planned_time_parameter", UNSET)

        total_actual_time = d.pop("total_actual_time", UNSET)

        planned_cost_per_unit = d.pop("planned_cost_per_unit", UNSET)

        total_actual_cost = d.pop("total_actual_cost", UNSET)

        cost_per_hour = d.pop("cost_per_hour", UNSET)

        cost_parameter = d.pop("cost_parameter", UNSET)

        group_boundary = d.pop("group_boundary", UNSET)

        is_status_actionable = d.pop("is_status_actionable", UNSET)

        def _parse_completed_at(data: object) -> None | Unset | datetime.datetime:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                completed_at_type_0 = isoparse(data)

                return completed_at_type_0
            except:  # noqa: E722
                pass
            return cast(None | Unset | datetime.datetime, data)

        completed_at = _parse_completed_at(d.pop("completed_at", UNSET))

        manufacturing_order_operation_row = cls(
            id=id,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
            status=status,
            type_=type_,
            rank=rank,
            manufacturing_order_id=manufacturing_order_id,
            operation_id=operation_id,
            operation_name=operation_name,
            resource_id=resource_id,
            resource_name=resource_name,
            assigned_operators=assigned_operators,
            completed_by_operators=completed_by_operators,
            active_operator_id=active_operator_id,
            planned_time_per_unit=planned_time_per_unit,
            planned_time_parameter=planned_time_parameter,
            total_actual_time=total_actual_time,
            planned_cost_per_unit=planned_cost_per_unit,
            total_actual_cost=total_actual_cost,
            cost_per_hour=cost_per_hour,
            cost_parameter=cost_parameter,
            group_boundary=group_boundary,
            is_status_actionable=is_status_actionable,
            completed_at=completed_at,
        )

        manufacturing_order_operation_row.additional_properties = d
        return manufacturing_order_operation_row

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
