from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.inventory_signal import InventorySignal


T = TypeVar("T", bound="InventorySignalListResponse")


@_attrs_define
class InventorySignalListResponse:
    """Response containing a list of inventory replenishment signals with pagination support.

    Example:
        {'data': [{'variant_id': 1, 'avg_daily_demand_30d': '3.50000000000000000000', 'reorder_point':
            '49.00000000000000000000', 'days_of_stock_left': 12, 'stock_risk': 1, 'in_stock': '42.00000000000000000000',
            'committed': '0.00000000000000000000', 'safety_stock_breach_at': '2026-08-24T00:00:00.000Z',
            'expected_before_safety_stock_breach': '30.00000000000000000000', 'safety_stock': '0.00000000000000000000',
            'lead_time_used': 14, 'lead_time_source': 'sku', 'demand_calculated_at': '2026-08-12T07:00:00.000Z'}]}
    """

    data: list[InventorySignal] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.data, Unset):
            data = []
            for data_item_data in self.data:
                data_item = data_item_data.to_dict()
                data.append(data_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if data is not UNSET:
            field_dict["data"] = data

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.inventory_signal import InventorySignal

        d = dict(src_dict)
        _data = d.pop("data", UNSET)
        data: list[InventorySignal] | Unset = UNSET
        if _data is not UNSET:
            data = []
            for data_item_data in _data:
                data_item = InventorySignal.from_dict(
                    cast(Mapping[str, Any], data_item_data)
                )

                data.append(data_item)

        inventory_signal_list_response = cls(
            data=data,
        )

        inventory_signal_list_response.additional_properties = d
        return inventory_signal_list_response

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
