from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset
from ..models.manufacturing_operation_type import ManufacturingOperationType

if TYPE_CHECKING:
    from ..models.update_product_operation_row_request_custom_fields_type_0 import (
        UpdateProductOperationRowRequestCustomFieldsType0,
    )


T = TypeVar("T", bound="UpdateProductOperationRowRequest")


@_attrs_define
class UpdateProductOperationRowRequest:
    """Request payload for updating a product operation row"""

    custom_fields: Unset | UpdateProductOperationRowRequestCustomFieldsType0 | None = (
        UNSET
    )
    operation_id: int | Unset = UNSET
    operation_name: str | Unset = UNSET
    type_: ManufacturingOperationType | Unset = UNSET
    resource_id: int | Unset = UNSET
    resource_name: str | Unset = UNSET
    planned_time_parameter: float | Unset = UNSET
    planned_time_per_unit: float | Unset = UNSET
    cost_parameter: float | Unset = UNSET
    cost_per_hour: float | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.update_product_operation_row_request_custom_fields_type_0 import (
            UpdateProductOperationRowRequestCustomFieldsType0,
        )

        custom_fields: dict[str, Any] | Unset | None
        if isinstance(self.custom_fields, Unset):
            custom_fields = UNSET
        elif isinstance(
            self.custom_fields, UpdateProductOperationRowRequestCustomFieldsType0
        ):
            custom_fields = self.custom_fields.to_dict()
        else:
            custom_fields = self.custom_fields

        operation_id = self.operation_id

        operation_name = self.operation_name

        type_: str | Unset = UNSET
        if not isinstance(self.type_, Unset):
            type_ = self.type_.value

        resource_id = self.resource_id

        resource_name = self.resource_name

        planned_time_parameter = self.planned_time_parameter

        planned_time_per_unit = self.planned_time_per_unit

        cost_parameter = self.cost_parameter

        cost_per_hour = self.cost_per_hour

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if custom_fields is not UNSET:
            field_dict["custom_fields"] = custom_fields
        if operation_id is not UNSET:
            field_dict["operation_id"] = operation_id
        if operation_name is not UNSET:
            field_dict["operation_name"] = operation_name
        if type_ is not UNSET:
            field_dict["type"] = type_
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

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.update_product_operation_row_request_custom_fields_type_0 import (
            UpdateProductOperationRowRequestCustomFieldsType0,
        )

        d = dict(src_dict)

        def _parse_custom_fields(
            data: object,
        ) -> Unset | UpdateProductOperationRowRequestCustomFieldsType0 | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                custom_fields_type_0 = (
                    UpdateProductOperationRowRequestCustomFieldsType0.from_dict(
                        cast(Mapping[str, Any], data)
                    )
                )

                return custom_fields_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                Unset | UpdateProductOperationRowRequestCustomFieldsType0 | None, data
            )

        custom_fields = _parse_custom_fields(d.pop("custom_fields", UNSET))

        operation_id = d.pop("operation_id", UNSET)

        operation_name = d.pop("operation_name", UNSET)

        _type_ = d.pop("type", UNSET)
        type_: ManufacturingOperationType | Unset
        if isinstance(_type_, Unset):
            type_ = UNSET
        else:
            type_ = ManufacturingOperationType(_type_)

        resource_id = d.pop("resource_id", UNSET)

        resource_name = d.pop("resource_name", UNSET)

        planned_time_parameter = d.pop("planned_time_parameter", UNSET)

        planned_time_per_unit = d.pop("planned_time_per_unit", UNSET)

        cost_parameter = d.pop("cost_parameter", UNSET)

        cost_per_hour = d.pop("cost_per_hour", UNSET)

        update_product_operation_row_request = cls(
            custom_fields=custom_fields,
            operation_id=operation_id,
            operation_name=operation_name,
            type_=type_,
            resource_id=resource_id,
            resource_name=resource_name,
            planned_time_parameter=planned_time_parameter,
            planned_time_per_unit=planned_time_per_unit,
            cost_parameter=cost_parameter,
            cost_per_hour=cost_per_hour,
        )

        return update_product_operation_row_request
