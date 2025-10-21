from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

T = TypeVar("T", bound="StorageBin")


@_attrs_define
class StorageBin:
    """Core storage bin business properties

    Example:
        {'bin_name': 'A-01-SHELF-1', 'location_id': 1}

    Attributes:
        bin_name (str): Name of the storage bin
        location_id (int): Unique identifier of the location where storage bin is located
    """

    bin_name: str
    location_id: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        bin_name = self.bin_name

        location_id = self.location_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "bin_name": bin_name,
                "location_id": location_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        bin_name = d.pop("bin_name")

        location_id = d.pop("location_id")

        storage_bin = cls(
            bin_name=bin_name,
            location_id=location_id,
        )

        storage_bin.additional_properties = d
        return storage_bin

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
