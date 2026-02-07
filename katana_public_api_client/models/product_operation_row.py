from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="ProductOperationRow")


@_attrs_define
class ProductOperationRow:
    """Operation step assigned to a product's manufacturing process"""

    product_operation_row_id: int
    product_id: int | Unset = UNSET
    product_variant_id: int | Unset = UNSET
    operation_id: int | Unset = UNSET
    operation_name: str | Unset = UNSET
    type_: str | Unset = UNSET
    resource_id: int | None | Unset = UNSET
    resource_name: None | str | Unset = UNSET
    cost_per_hour: float | None | Unset = UNSET
    cost_parameter: None | str | Unset = UNSET
    planned_cost_per_unit: float | None | Unset = UNSET
    planned_time_per_unit: float | None | Unset = UNSET
    planned_time_parameter: None | str | Unset = UNSET
    rank: int | Unset = UNSET
    group_boundary: None | str | Unset = UNSET
    created_at: datetime.datetime | Unset = UNSET
    updated_at: datetime.datetime | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        product_operation_row_id = self.product_operation_row_id

        product_id = self.product_id

        product_variant_id = self.product_variant_id

        operation_id = self.operation_id

        operation_name = self.operation_name

        type_ = self.type_

        resource_id: int | None | Unset
        if isinstance(self.resource_id, Unset):
            resource_id = UNSET
        else:
            resource_id = self.resource_id

        resource_name: None | str | Unset
        if isinstance(self.resource_name, Unset):
            resource_name = UNSET
        else:
            resource_name = self.resource_name

        cost_per_hour: float | None | Unset
        if isinstance(self.cost_per_hour, Unset):
            cost_per_hour = UNSET
        else:
            cost_per_hour = self.cost_per_hour

        cost_parameter: None | str | Unset
        if isinstance(self.cost_parameter, Unset):
            cost_parameter = UNSET
        else:
            cost_parameter = self.cost_parameter

        planned_cost_per_unit: float | None | Unset
        if isinstance(self.planned_cost_per_unit, Unset):
            planned_cost_per_unit = UNSET
        else:
            planned_cost_per_unit = self.planned_cost_per_unit

        planned_time_per_unit: float | None | Unset
        if isinstance(self.planned_time_per_unit, Unset):
            planned_time_per_unit = UNSET
        else:
            planned_time_per_unit = self.planned_time_per_unit

        planned_time_parameter: None | str | Unset
        if isinstance(self.planned_time_parameter, Unset):
            planned_time_parameter = UNSET
        else:
            planned_time_parameter = self.planned_time_parameter

        rank = self.rank

        group_boundary: None | str | Unset
        if isinstance(self.group_boundary, Unset):
            group_boundary = UNSET
        else:
            group_boundary = self.group_boundary

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: str | Unset = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "product_operation_row_id": product_operation_row_id,
            }
        )
        if product_id is not UNSET:
            field_dict["product_id"] = product_id
        if product_variant_id is not UNSET:
            field_dict["product_variant_id"] = product_variant_id
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
        if cost_per_hour is not UNSET:
            field_dict["cost_per_hour"] = cost_per_hour
        if cost_parameter is not UNSET:
            field_dict["cost_parameter"] = cost_parameter
        if planned_cost_per_unit is not UNSET:
            field_dict["planned_cost_per_unit"] = planned_cost_per_unit
        if planned_time_per_unit is not UNSET:
            field_dict["planned_time_per_unit"] = planned_time_per_unit
        if planned_time_parameter is not UNSET:
            field_dict["planned_time_parameter"] = planned_time_parameter
        if rank is not UNSET:
            field_dict["rank"] = rank
        if group_boundary is not UNSET:
            field_dict["group_boundary"] = group_boundary
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        product_operation_row_id = d.pop("product_operation_row_id")

        product_id = d.pop("product_id", UNSET)

        product_variant_id = d.pop("product_variant_id", UNSET)

        operation_id = d.pop("operation_id", UNSET)

        operation_name = d.pop("operation_name", UNSET)

        type_ = d.pop("type", UNSET)

        def _parse_resource_id(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        resource_id = _parse_resource_id(d.pop("resource_id", UNSET))

        def _parse_resource_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        resource_name = _parse_resource_name(d.pop("resource_name", UNSET))

        def _parse_cost_per_hour(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        cost_per_hour = _parse_cost_per_hour(d.pop("cost_per_hour", UNSET))

        def _parse_cost_parameter(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        cost_parameter = _parse_cost_parameter(d.pop("cost_parameter", UNSET))

        def _parse_planned_cost_per_unit(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        planned_cost_per_unit = _parse_planned_cost_per_unit(
            d.pop("planned_cost_per_unit", UNSET)
        )

        def _parse_planned_time_per_unit(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        planned_time_per_unit = _parse_planned_time_per_unit(
            d.pop("planned_time_per_unit", UNSET)
        )

        def _parse_planned_time_parameter(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        planned_time_parameter = _parse_planned_time_parameter(
            d.pop("planned_time_parameter", UNSET)
        )

        rank = d.pop("rank", UNSET)

        def _parse_group_boundary(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        group_boundary = _parse_group_boundary(d.pop("group_boundary", UNSET))

        _created_at = d.pop("created_at", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        _updated_at = d.pop("updated_at", UNSET)
        updated_at: datetime.datetime | Unset
        if isinstance(_updated_at, Unset):
            updated_at = UNSET
        else:
            updated_at = isoparse(_updated_at)

        product_operation_row = cls(
            product_operation_row_id=product_operation_row_id,
            product_id=product_id,
            product_variant_id=product_variant_id,
            operation_id=operation_id,
            operation_name=operation_name,
            type_=type_,
            resource_id=resource_id,
            resource_name=resource_name,
            cost_per_hour=cost_per_hour,
            cost_parameter=cost_parameter,
            planned_cost_per_unit=planned_cost_per_unit,
            planned_time_per_unit=planned_time_per_unit,
            planned_time_parameter=planned_time_parameter,
            rank=rank,
            group_boundary=group_boundary,
            created_at=created_at,
            updated_at=updated_at,
        )

        product_operation_row.additional_properties = d
        return product_operation_row

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
