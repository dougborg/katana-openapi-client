from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="StorageBin")


@_attrs_define
class StorageBin:
    """Core storage bin business properties

    Example:
        {'bin_name': 'A-01-SHELF-1', 'location_id': 1}
    """

    bin_name: str
    location_id: int

    def to_dict(self) -> dict[str, Any]:
        bin_name = self.bin_name

        location_id = self.location_id

        field_dict: dict[str, Any] = {}

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

        return storage_bin
