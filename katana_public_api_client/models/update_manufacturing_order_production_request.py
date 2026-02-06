from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="UpdateManufacturingOrderProductionRequest")


@_attrs_define
class UpdateManufacturingOrderProductionRequest:
    """Request payload for updating an existing production run within a manufacturing order.

    Example:
        {'production_date': '2024-01-21T16:00:00Z'}
    """

    production_date: datetime.datetime | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        production_date: str | Unset = UNSET
        if not isinstance(self.production_date, Unset):
            production_date = self.production_date.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if production_date is not UNSET:
            field_dict["production_date"] = production_date

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _production_date = d.pop("production_date", UNSET)
        production_date: datetime.datetime | Unset
        if isinstance(_production_date, Unset):
            production_date = UNSET
        else:
            production_date = isoparse(_production_date)

        update_manufacturing_order_production_request = cls(
            production_date=production_date,
        )

        update_manufacturing_order_production_request.additional_properties = d
        return update_manufacturing_order_production_request

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
