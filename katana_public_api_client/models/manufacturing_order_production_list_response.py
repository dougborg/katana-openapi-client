from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.manufacturing_order_production import ManufacturingOrderProduction


T = TypeVar("T", bound="ManufacturingOrderProductionListResponse")


@_attrs_define
class ManufacturingOrderProductionListResponse:
    """Response containing a list of production runs for manufacturing orders with pagination support for tracking
    production history.

        Example:
            {'data': [{'id': 3501, 'manufacturing_order_id': 3001, 'quantity': 25, 'production_date':
                '2024-01-20T14:30:00Z', 'ingredients': [{'id': 4001, 'location_id': 1, 'variant_id': 3101,
                'manufacturing_order_id': 3001, 'manufacturing_order_recipe_row_id': 3201, 'production_id': 3501, 'quantity':
                50.0, 'production_date': '2024-01-20T14:30:00Z', 'cost': 125.0, 'created_at': '2024-01-20T14:30:00Z',
                'updated_at': '2024-01-20T14:30:00Z', 'deleted_at': None}], 'operations': [{'id': 3801,
                'manufacturing_order_id': 3001, 'operation_id': 401, 'operation_name': 'Cut Steel Sheets', 'time': 15.0, 'cost':
                45.0, 'created_at': '2024-01-20T14:30:00Z', 'updated_at': '2024-01-20T14:30:00Z', 'deleted_at': None}],
                'serial_numbers': ['PKS-001-240120', 'PKS-002-240120'], 'created_at': '2024-01-20T14:30:00Z', 'updated_at':
                '2024-01-20T14:30:00Z', 'deleted_at': None}]}
    """

    data: Unset | list["ManufacturingOrderProduction"] = UNSET
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
        from ..models.manufacturing_order_production import ManufacturingOrderProduction

        d = dict(src_dict)
        data = []
        _data = d.pop("data", UNSET)
        for data_item_data in _data or []:
            data_item = ManufacturingOrderProduction.from_dict(data_item_data)

            data.append(data_item)

        manufacturing_order_production_list_response = cls(
            data=data,
        )

        manufacturing_order_production_list_response.additional_properties = d
        return manufacturing_order_production_list_response

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
