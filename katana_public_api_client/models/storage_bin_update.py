from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="StorageBinUpdate")


@_attrs_define
class StorageBinUpdate:
    """Storage bin fields for update operations (all optional for PATCH)

    Example:
        {'bin_name': 'A-01-SHELF-2', 'location_id': 2}
    """

    bin_name: Unset | str = UNSET
    location_id: Unset | int = UNSET

    def to_dict(self) -> dict[str, Any]:
        bin_name = self.bin_name

        location_id = self.location_id

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if bin_name is not UNSET:
            field_dict["bin_name"] = bin_name
        if location_id is not UNSET:
            field_dict["location_id"] = location_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        bin_name = d.pop("bin_name", UNSET)

        location_id = d.pop("location_id", UNSET)

        storage_bin_update = cls(
            bin_name=bin_name,
            location_id=location_id,
        )

        return storage_bin_update
