from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.negative_stock import NegativeStock


T = TypeVar("T", bound="NegativeStockListResponse")


@_attrs_define
class NegativeStockListResponse:
    """List of inventory records showing variants with negative stock levels that require immediate attention

    Example:
        {'data': [{'variant_id': 3001, 'location_id': 1, 'latest_negative_stock_date': '2024-01-15T16:30:00.000Z',
            'quantity_on_hand': -15.0, 'quantity_allocated': 25.0}, {'variant_id': 3003, 'location_id': 2,
            'latest_negative_stock_date': '2024-01-16T09:45:00.000Z', 'quantity_on_hand': -5.0, 'quantity_allocated':
            10.0}]}

    Attributes:
        data (Union[Unset, list['NegativeStock']]): Array of negative stock records with variant, location, and deficit
            information
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
