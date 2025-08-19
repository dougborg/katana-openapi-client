from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset
from ..models.create_product_operation_rows_body_rows_item_type import (
    CreateProductOperationRowsBodyRowsItemType,
)

T = TypeVar("T", bound="CreateProductOperationRowsBodyRowsItem")


@_attrs_define
class CreateProductOperationRowsBodyRowsItem:
    product_variant_id: float
    operation_id: Unset | int = UNSET
    operation_name: Unset | str = UNSET
    resource_id: Unset | int = UNSET
    resource_name: Unset | str = UNSET
    type_: Unset | CreateProductOperationRowsBodyRowsItemType = (
        CreateProductOperationRowsBodyRowsItemType.PROCESS
    )
    cost_parameter: Unset | float = UNSET
    cost_per_hour: Unset | float = UNSET
    planned_time_parameter: Unset | int = UNSET
    planned_time_per_unit: Unset | int = UNSET

    def to_dict(self) -> dict[str, Any]:
        product_variant_id = self.product_variant_id

        operation_id = self.operation_id

        operation_name = self.operation_name

        resource_id = self.resource_id

        resource_name = self.resource_name

        type_: Unset | str = UNSET
        if not isinstance(self.type_, Unset):
            type_ = self.type_.value

        cost_parameter = self.cost_parameter

        cost_per_hour = self.cost_per_hour

        planned_time_parameter = self.planned_time_parameter

        planned_time_per_unit = self.planned_time_per_unit

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "product_variant_id": product_variant_id,
            }
        )
        if operation_id is not UNSET:
            field_dict["operation_id"] = operation_id
        if operation_name is not UNSET:
            field_dict["operation_name"] = operation_name
        if resource_id is not UNSET:
            field_dict["resource_id"] = resource_id
        if resource_name is not UNSET:
            field_dict["resource_name"] = resource_name
        if type_ is not UNSET:
            field_dict["type"] = type_
        if cost_parameter is not UNSET:
            field_dict["cost_parameter"] = cost_parameter
        if cost_per_hour is not UNSET:
            field_dict["cost_per_hour"] = cost_per_hour
        if planned_time_parameter is not UNSET:
            field_dict["planned_time_parameter"] = planned_time_parameter
        if planned_time_per_unit is not UNSET:
            field_dict["planned_time_per_unit"] = planned_time_per_unit

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        product_variant_id = d.pop("product_variant_id")

        operation_id = d.pop("operation_id", UNSET)

        operation_name = d.pop("operation_name", UNSET)

        resource_id = d.pop("resource_id", UNSET)

        resource_name = d.pop("resource_name", UNSET)

        _type_ = d.pop("type", UNSET)
        type_: Unset | CreateProductOperationRowsBodyRowsItemType
        if isinstance(_type_, Unset):
            type_ = UNSET
        else:
            type_ = CreateProductOperationRowsBodyRowsItemType(_type_)

        cost_parameter = d.pop("cost_parameter", UNSET)

        cost_per_hour = d.pop("cost_per_hour", UNSET)

        planned_time_parameter = d.pop("planned_time_parameter", UNSET)

        planned_time_per_unit = d.pop("planned_time_per_unit", UNSET)

        create_product_operation_rows_body_rows_item = cls(
            product_variant_id=product_variant_id,
            operation_id=operation_id,
            operation_name=operation_name,
            resource_id=resource_id,
            resource_name=resource_name,
            type_=type_,
            cost_parameter=cost_parameter,
            cost_per_hour=cost_per_hour,
            planned_time_parameter=planned_time_parameter,
            planned_time_per_unit=planned_time_per_unit,
        )

        return create_product_operation_rows_body_rows_item
