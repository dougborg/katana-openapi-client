from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="StorageBinUpdate")


@_attrs_define
class StorageBinUpdate:
    """Storage bin fields for update operations

    Example:
        {'bin_name': 'A-01-SHELF-2'}
    """

    bin_name: str

    def to_dict(self) -> dict[str, Any]:
        bin_name = self.bin_name

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "bin_name": bin_name,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        bin_name = d.pop("bin_name")

        storage_bin_update = cls(
            bin_name=bin_name,
        )

        return storage_bin_update
