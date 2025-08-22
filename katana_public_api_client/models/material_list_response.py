from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.material import Material


T = TypeVar("T", bound="MaterialListResponse")


@_attrs_define
class MaterialListResponse:
    """Response containing a list of materials with pagination support for inventory and procurement management.

    Example:
        {'data': [{'id': 3201, 'name': 'Stainless Steel Sheet 304', 'uom': 'm²', 'category_name': 'Raw Materials',
            'default_supplier_id': 1501, 'additional_info': 'Food-grade stainless steel, 1.5mm thickness', 'batch_tracked':
            True, 'is_sellable': False, 'type': 'material', 'purchase_uom': 'sheet', 'purchase_uom_conversion_rate': 2.0,
            'variants': [{'id': 5001, 'sku': 'STEEL-304-1.5MM', 'sales_price': None, 'purchase_price': 45.0, 'type':
            'material', 'lead_time': 5, 'minimum_order_quantity': 1, 'config_attributes': [{'config_name': 'Grade',
            'config_value': '304'}, {'config_name': 'Thickness', 'config_value': '1.5mm'}], 'created_at':
            '2024-01-10T10:00:00Z', 'updated_at': '2024-01-15T14:30:00Z'}, {'id': 5002, 'sku': 'STEEL-316-1.5MM',
            'sales_price': None, 'purchase_price': 52.0, 'type': 'material', 'lead_time': 7, 'minimum_order_quantity': 1,
            'config_attributes': [{'config_name': 'Grade', 'config_value': '316'}, {'config_name': 'Thickness',
            'config_value': '1.5mm'}], 'created_at': '2024-01-10T10:00:00Z', 'updated_at': '2024-01-15T14:30:00Z'}],
            'configs': [{'id': 101, 'name': 'Grade', 'values': ['304', '316']}, {'id': 102, 'name': 'Thickness', 'values':
            ['1.5mm', '2.0mm']}], 'custom_field_collection_id': 201, 'supplier': None, 'created_at': '2024-01-10T10:00:00Z',
            'updated_at': '2024-01-15T14:30:00Z', 'archived_at': None}]}
    """

    data: Unset | list["Material"] = UNSET
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
        from ..models.material import Material

        d = dict(src_dict)
        data = []
        _data = d.pop("data", UNSET)
        for data_item_data in _data or []:
            data_item = Material.from_dict(data_item_data)

            data.append(data_item)

        material_list_response = cls(
            data=data,
        )

        material_list_response.additional_properties = d
        return material_list_response

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
