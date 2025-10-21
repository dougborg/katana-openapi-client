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
    """List of current inventory levels showing stock quantities for all variants across all locations

    Example:
        {'data': [{'id': 1001, 'variant_id': 3001, 'location_id': 1, 'quantity_on_hand': 150.0, 'quantity_allocated':
            25.0, 'quantity_available': 125.0, 'average_cost': 25.5, 'total_value': 3825.0, 'created_at':
            '2024-01-15T08:00:00.000Z', 'updated_at': '2024-01-15T12:30:00.000Z'}, {'id': 1002, 'variant_id': 3002,
            'location_id': 1, 'quantity_on_hand': 75.0, 'quantity_allocated': 10.0, 'quantity_available': 65.0,
            'average_cost': 45.0, 'total_value': 3375.0, 'created_at': '2024-01-15T08:00:00.000Z', 'updated_at':
            '2024-01-15T14:15:00.000Z'}]}

    Attributes:
        data (list['Inventory']): Array of inventory records with current stock levels and location details
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
