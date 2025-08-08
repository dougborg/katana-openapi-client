from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.batch_stock import BatchStock


T = TypeVar("T", bound="BatchStockListResponse")


@_attrs_define
class BatchStockListResponse:
    """Response containing batch inventory levels across multiple batches

    Example:
        {'data': [{'id': 4001, 'batch_number': 'BATCH-ALU6061-240315', 'batch_created_date': '2024-03-15T10:30:00.000Z',
            'expiration_date': '2025-03-15T23:59:59.000Z', 'variant_id': 3001, 'batch_barcode': 'ALU6061240315',
            'location_id': 101, 'quantity_in_stock': '150.00000', 'created_at': '2024-03-15T10:30:00.000Z', 'updated_at':
            '2024-03-15T10:30:00.000Z'}, {'id': 4002, 'batch_number': 'BATCH-SS316-240314', 'batch_created_date':
            '2024-03-14T14:15:00.000Z', 'expiration_date': '2026-03-14T23:59:59.000Z', 'variant_id': 3005, 'batch_barcode':
            'SS316240314', 'location_id': 101, 'quantity_in_stock': '75.50000', 'created_at': '2024-03-14T14:15:00.000Z',
            'updated_at': '2024-03-14T14:15:00.000Z'}]}
    """

    data: Unset | list["BatchStock"] = UNSET
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
        from ..models.batch_stock import BatchStock

        d = dict(src_dict)
        data = []
        _data = d.pop("data", UNSET)
        for data_item_data in _data or []:
            data_item = BatchStock.from_dict(data_item_data)

            data.append(data_item)

        batch_stock_list_response = cls(
            data=data,
        )

        batch_stock_list_response.additional_properties = d
        return batch_stock_list_response

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
