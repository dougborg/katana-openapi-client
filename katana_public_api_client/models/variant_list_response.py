from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.variant_response import VariantResponse


T = TypeVar("T", bound="VariantListResponse")


@_attrs_define
class VariantListResponse:
    """Response containing a paginated list of variants with their configuration attributes and parent product details

    Example:
        {'data': [{'id': 3001, 'sku': 'KNF-PRO-8PC-STL', 'sales_price': 299.99, 'type': 'product', 'config_attributes':
            [{'config_name': 'Piece Count', 'config_value': '8-piece'}, {'config_name': 'Handle Material', 'config_value':
            'Steel'}]}, {'id': 3002, 'sku': 'KNF-PRO-12PC-WD', 'sales_price': 399.99, 'type': 'product',
            'config_attributes': [{'config_name': 'Piece Count', 'config_value': '12-piece'}, {'config_name': 'Handle
            Material', 'config_value': 'Wood'}]}, {'id': 5001, 'sku': 'STEEL-304-1.5MM', 'sales_price': None,
            'purchase_price': 45.0, 'type': 'material', 'lead_time': 5, 'minimum_order_quantity': 1, 'config_attributes':
            [{'config_name': 'Grade', 'config_value': '304'}, {'config_name': 'Thickness', 'config_value': '1.5mm'}]},
            {'id': 5003, 'sku': 'ALU-6061-2.0MM', 'sales_price': None, 'purchase_price': 38.5, 'type': 'material',
            'lead_time': 3, 'minimum_order_quantity': 2, 'config_attributes': [{'config_name': 'Alloy', 'config_value':
            '6061'}, {'config_name': 'Thickness', 'config_value': '2.0mm'}]}]}
    """

    data: Unset | list["VariantResponse"] = UNSET
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
        from ..models.variant_response import VariantResponse

        d = dict(src_dict)
        data = []
        _data = d.pop("data", UNSET)
        for data_item_data in _data or []:
            data_item = VariantResponse.from_dict(data_item_data)

            data.append(data_item)

        variant_list_response = cls(
            data=data,
        )

        variant_list_response.additional_properties = d
        return variant_list_response

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
