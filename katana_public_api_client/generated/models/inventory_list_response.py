from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

if TYPE_CHECKING:
    from ..models.inventory import Inventory


T = TypeVar("T", bound="InventoryListResponse")


@_attrs_define
class InventoryListResponse:
    """Response containing real-time inventory status across multiple variants

    Example:
        {'data': [{'variant_id': 3005, 'location_id': 101, 'safety_stock_level': 75.0, 'reorder_point': 75.0,
            'average_cost': 42.5, 'value_in_stock': 6375.0, 'quantity_in_stock': 150.0, 'quantity_committed': 45.0,
            'quantity_expected': 100.0, 'quantity_missing_or_excess': 130.0, 'quantity_potential': 105.0}, {'variant_id':
            3008, 'location_id': 101, 'safety_stock_level': 25.0, 'reorder_point': 25.0, 'average_cost': 85.75,
            'value_in_stock': 1715.0, 'quantity_in_stock': 20.0, 'quantity_committed': 12.0, 'quantity_expected': 50.0,
            'quantity_missing_or_excess': 33.0, 'quantity_potential': 8.0}]}
    """

    data: list["Inventory"]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = []
        for data_item_data in self.data:
            data_item = data_item_data.to_dict()
            data.append(data_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "data": data,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.inventory import Inventory

        d = dict(src_dict)
        data = []
        _data = d.pop("data")
        for data_item_data in _data:
            data_item = Inventory.from_dict(data_item_data)

            data.append(data_item)

        inventory_list_response = cls(
            data=data,
        )

        inventory_list_response.additional_properties = d
        return inventory_list_response

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
