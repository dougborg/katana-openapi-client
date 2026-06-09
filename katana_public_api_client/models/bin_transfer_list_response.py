from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.bin_transfer import BinTransfer


T = TypeVar("T", bound="BinTransferListResponse")


@_attrs_define
class BinTransferListResponse:
    """Paginated list of bin transfer records.

    Example:
        {'data': [{'id': 1, 'bin_transfer_number': 'BT-1', 'location_id': 1, 'status': 'CREATED', 'created_date':
            '2026-05-22T10:00:00.000Z', 'departed_at': None, 'arrived_at': None, 'additional_info': 'urgent transfer',
            'bin_transfer_rows': [], 'created_at': '2026-05-22T10:00:00.000Z', 'updated_at': '2026-05-22T10:00:00.000Z',
            'deleted_at': None}]}
    """

    data: list[BinTransfer] | Unset = UNSET
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
        from ..models.bin_transfer import BinTransfer

        d = dict(src_dict)
        _data = d.pop("data", UNSET)
        data: list[BinTransfer] | Unset = UNSET
        if _data is not UNSET:
            data = []
            for data_item_data in _data:
                data_item = BinTransfer.from_dict(
                    cast(Mapping[str, Any], data_item_data)
                )

                data.append(data_item)

        bin_transfer_list_response = cls(
            data=data,
        )

        bin_transfer_list_response.additional_properties = d
        return bin_transfer_list_response

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
