from __future__ import annotations

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
        {'data': [{'id': 1, 'stock_transfer_number': 'ST-1', 'source_location_id': 1, 'target_location_id': 2,
            'transfer_date': '2021-10-06T11:47:13.846Z', 'order_created_date': '2021-10-01T11:47:13.846Z',
            'expected_arrival_date': '2021-10-20T11:47:13.846Z', 'additional_info': 'transfer additional info',
            'created_at': '2021-10-06T11:47:13.846Z', 'updated_at': '2021-10-06T11:47:13.846Z', 'deleted_at': None}]}
    """

    data: list[StockTransfer] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data: list[dict[str, Any]] | Unset = UNSET
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
        _data = d.pop("data", UNSET)
        data: list[StockTransfer] | Unset = UNSET
        if _data is not UNSET:
            data = []
            for data_item_data in _data:
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
