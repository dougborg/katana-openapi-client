from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.storage_bin import StorageBin


T = TypeVar("T", bound="StorageBinList")


@_attrs_define
class StorageBinList:
    """
    Example:
        {'data': [{'id': 12345, 'name': 'Bin-2', 'location_id': 12346, 'created_at': '2020-10-23T10:37:05.085Z',
            'updated_at': '2020-10-23T10:37:05.085Z', 'deleted_at': None}]}

    Attributes:
        data (Union[Unset, list['StorageBin']]):
    """

    data: Unset | list["StorageBin"] = UNSET
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
        from ..models.storage_bin import StorageBin

        d = dict(src_dict)
        data = []
        _data = d.pop("data", UNSET)
        for data_item_data in _data or []:
            data_item = StorageBin.from_dict(data_item_data)

            data.append(data_item)

        storage_bin_list = cls(
            data=data,
        )

        storage_bin_list.additional_properties = d
        return storage_bin_list

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
