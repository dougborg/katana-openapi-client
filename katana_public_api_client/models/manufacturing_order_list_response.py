from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.manufacturing_order import ManufacturingOrder


T = TypeVar("T", bound="ManufacturingOrderListResponse")


@_attrs_define
class ManufacturingOrderListResponse:
    """Response containing a list of manufacturing orders with pagination support for retrieving production data.

    Example:
        {'data': [{'id': 3001, 'status': 'IN_PROGRESS', 'order_no': 'MO-2024-001', 'variant_id': 2101,
            'planned_quantity': 50, 'actual_quantity': 35, 'location_id': 1, 'order_created_date': '2024-01-15T08:00:00Z',
            'production_deadline_date': '2024-01-25T17:00:00Z', 'additional_info': 'Priority order for new product launch',
            'is_linked_to_sales_order': True, 'ingredient_availability': 'AVAILABLE', 'total_cost': 12500.0,
            'total_actual_time': 140.5, 'total_planned_time': 200.0, 'sales_order_id': 2001, 'sales_order_row_id': 2501,
            'sales_order_delivery_deadline': '2024-01-30T12:00:00Z', 'material_cost': 8750.0, 'subassemblies_cost': 2250.0,
            'operations_cost': 1500.0, 'serial_numbers': ['PKS-001-240115', 'PKS-002-240115', 'PKS-003-240115'],
            'created_at': '2024-01-15T08:00:00Z', 'updated_at': '2024-01-20T14:30:00Z', 'deleted_at': None}]}

    Attributes:
        data (Union[Unset, list['ManufacturingOrder']]): Array of manufacturing orders
    """

    data: Unset | list["ManufacturingOrder"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data: Unset | list[dict[str, Any]] = UNSET
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
        from ..models.manufacturing_order import ManufacturingOrder

        d = dict(src_dict)
        data = []
        _data = d.pop("data", UNSET)
        for data_item_data in _data or []:
            data_item = ManufacturingOrder.from_dict(data_item_data)

            data.append(data_item)

        manufacturing_order_list_response = cls(
            data=data,
        )

        manufacturing_order_list_response.additional_properties = d
        return manufacturing_order_list_response

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
