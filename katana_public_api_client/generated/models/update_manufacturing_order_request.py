import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateManufacturingOrderRequest")


@_attrs_define
class UpdateManufacturingOrderRequest:
    planned_quantity: Unset | float = UNSET
    additional_info: Unset | str = UNSET
    production_deadline_date: Unset | datetime.datetime = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        planned_quantity = self.planned_quantity

        additional_info = self.additional_info

        production_deadline_date: Unset | str = UNSET
        if not isinstance(self.production_deadline_date, Unset):
            production_deadline_date = self.production_deadline_date.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if planned_quantity is not UNSET:
            field_dict["planned_quantity"] = planned_quantity
        if additional_info is not UNSET:
            field_dict["additional_info"] = additional_info
        if production_deadline_date is not UNSET:
            field_dict["production_deadline_date"] = production_deadline_date

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        planned_quantity = d.pop("planned_quantity", UNSET)

        additional_info = d.pop("additional_info", UNSET)

        _production_deadline_date = d.pop("production_deadline_date", UNSET)
        production_deadline_date: Unset | datetime.datetime
        if isinstance(_production_deadline_date, Unset):
            production_deadline_date = UNSET
        else:
            production_deadline_date = isoparse(_production_deadline_date)

        update_manufacturing_order_request = cls(
            planned_quantity=planned_quantity,
            additional_info=additional_info,
            production_deadline_date=production_deadline_date,
        )

        update_manufacturing_order_request.additional_properties = d
        return update_manufacturing_order_request

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
