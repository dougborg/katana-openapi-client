from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.manufacturing_order_traceability_request import (
        ManufacturingOrderTraceabilityRequest,
    )


T = TypeVar("T", bound="UpdateManufacturingOrderProductionRequest")


@_attrs_define
class UpdateManufacturingOrderProductionRequest:
    """Request payload for updating an existing production run within a manufacturing order.

    Example:
        {'production_date': '2024-01-21T16:00:00Z'}
    """

    production_date: datetime.datetime | Unset = UNSET
    traceability: list[ManufacturingOrderTraceabilityRequest] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        production_date: str | Unset = UNSET
        if not isinstance(self.production_date, Unset):
            production_date = self.production_date.isoformat()

        traceability: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.traceability, Unset):
            traceability = []
            for traceability_item_data in self.traceability:
                traceability_item = traceability_item_data.to_dict()
                traceability.append(traceability_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if production_date is not UNSET:
            field_dict["production_date"] = production_date
        if traceability is not UNSET:
            field_dict["traceability"] = traceability

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.manufacturing_order_traceability_request import (
            ManufacturingOrderTraceabilityRequest,
        )

        d = dict(src_dict)
        _production_date = d.pop("production_date", UNSET)
        production_date: datetime.datetime | Unset
        if isinstance(_production_date, Unset):
            production_date = UNSET
        else:
            production_date = datetime.datetime.fromisoformat(_production_date)

        _traceability = d.pop("traceability", UNSET)
        traceability: list[ManufacturingOrderTraceabilityRequest] | Unset = UNSET
        if _traceability is not UNSET:
            traceability = []
            for traceability_item_data in _traceability:
                traceability_item = ManufacturingOrderTraceabilityRequest.from_dict(
                    cast(Mapping[str, Any], traceability_item_data)
                )

                traceability.append(traceability_item)

        update_manufacturing_order_production_request = cls(
            production_date=production_date,
            traceability=traceability,
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
