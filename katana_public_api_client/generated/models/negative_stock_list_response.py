from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.negative_stock import NegativeStock


T = TypeVar("T", bound="NegativeStockListResponse")


@_attrs_define
class NegativeStockListResponse:
    """Response containing a list of variants with negative stock

    Example:
        {'data': [{'id': 8001, 'variant_id': 3005, 'location_id': 101, 'latest_negative_stock_date':
            '2024-03-14T16:45:00.000Z', 'name': 'Stainless Steel Grade 316 Sheet', 'sku': 'SS316-SHEET-3MM', 'category':
            'Raw Materials'}, {'id': 8002, 'variant_id': 3008, 'location_id': 102, 'latest_negative_stock_date':
            '2024-03-13T11:20:00.000Z', 'name': 'Titanium Alloy Rod 10mm', 'sku': 'TI-ROD-10MM', 'category': 'Raw
            Materials'}]}
    """

    data: Unset | list["NegativeStock"] = UNSET
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
        from ..models.negative_stock import NegativeStock

        d = dict(src_dict)
        data = []
        _data = d.pop("data", UNSET)
        for data_item_data in _data or []:
            data_item = NegativeStock.from_dict(data_item_data)

            data.append(data_item)

        negative_stock_list_response = cls(
            data=data,
        )

        negative_stock_list_response.additional_properties = d
        return negative_stock_list_response

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
