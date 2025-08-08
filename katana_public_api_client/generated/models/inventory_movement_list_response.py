from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

if TYPE_CHECKING:
    from ..models.inventory_movement import InventoryMovement


T = TypeVar("T", bound="InventoryMovementListResponse")


@_attrs_define
class InventoryMovementListResponse:
    """Response containing historical inventory movements for audit and tracking

    Example:
        {'data': [{'id': 10001, 'variant_id': 3005, 'location_id': 101, 'resource_type': 'PurchaseOrderRow',
            'resource_id': 5001, 'caused_by_order_no': 'PO-240315-001', 'caused_by_resource_id': 5001, 'movement_date':
            '2024-03-15T10:30:00.000Z', 'quantity_change': 100.0, 'balance_after': 250.0, 'value_per_unit': 42.5,
            'value_in_stock_after': 10625.0, 'average_cost_after': 42.5, 'rank': 1, 'created_at':
            '2024-03-15T10:30:00.000Z', 'updated_at': '2024-03-15T10:30:00.000Z'}, {'id': 10002, 'variant_id': 3005,
            'location_id': 101, 'resource_type': 'SalesOrderRow', 'resource_id': 8001, 'caused_by_order_no':
            'SO-240315-001', 'caused_by_resource_id': 8001, 'movement_date': '2024-03-15T14:45:00.000Z', 'quantity_change':
            -45.0, 'balance_after': 205.0, 'value_per_unit': 42.5, 'value_in_stock_after': 8712.5, 'average_cost_after':
            42.5, 'rank': 2, 'created_at': '2024-03-15T14:45:00.000Z', 'updated_at': '2024-03-15T14:45:00.000Z'}]}
    """

    data: list["InventoryMovement"]
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
        from ..models.inventory_movement import InventoryMovement

        d = dict(src_dict)
        data = []
        _data = d.pop("data")
        for data_item_data in _data:
            data_item = InventoryMovement.from_dict(data_item_data)

            data.append(data_item)

        inventory_movement_list_response = cls(
            data=data,
        )

        inventory_movement_list_response.additional_properties = d
        return inventory_movement_list_response

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
