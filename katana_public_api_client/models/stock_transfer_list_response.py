from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.stock_transfer import StockTransfer


T = TypeVar("T", bound="StockTransferListResponse")


@_attrs_define
class StockTransferListResponse:
    """List of stock transfer records showing all inventory movements between locations and their transfer status

    Example:
        {'data': [{'id': 3001, 'stock_transfer_number': 'ST-2024-001', 'source_location_id': 1, 'target_location_id': 2,
            'status': 'COMPLETED', 'transfer_date': '2024-01-15T16:00:00.000Z', 'additional_info': 'Rebalancing inventory
            between warehouses', 'created_at': '2024-01-15T16:00:00.000Z', 'updated_at': '2024-01-15T16:00:00.000Z',
            'deleted_at': None}, {'id': 3002, 'stock_transfer_number': 'ST-2024-002', 'source_location_id': 2,
            'target_location_id': 3, 'status': 'DRAFT', 'transfer_date': '2024-01-16T11:30:00.000Z', 'additional_info':
            'Seasonal stock redistribution', 'created_at': '2024-01-16T11:30:00.000Z', 'updated_at':
            '2024-01-16T11:30:00.000Z', 'deleted_at': None}]}
    """

    data: Unset | list["StockTransfer"] = UNSET
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
        from ..models.stock_transfer import StockTransfer

        d = dict(src_dict)
        data = []
        _data = d.pop("data", UNSET)
        for data_item_data in _data or []:
            data_item = StockTransfer.from_dict(data_item_data)

            data.append(data_item)

        stock_transfer_list_response = cls(
            data=data,
        )

        stock_transfer_list_response.additional_properties = d
        return stock_transfer_list_response

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
