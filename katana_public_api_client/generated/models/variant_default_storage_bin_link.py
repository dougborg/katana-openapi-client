from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="VariantDefaultStorageBinLink")


@_attrs_define
class VariantDefaultStorageBinLink:
    variant_id: int
    bin_name: str
    location_id: Unset | int = UNSET

    def to_dict(self) -> dict[str, Any]:
        variant_id = self.variant_id

        bin_name = self.bin_name

        location_id = self.location_id

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "variant_id": variant_id,
                "bin_name": bin_name,
            }
        )
        if location_id is not UNSET:
            field_dict["location_id"] = location_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        variant_id = d.pop("variant_id")

        bin_name = d.pop("bin_name")

        location_id = d.pop("location_id", UNSET)

        variant_default_storage_bin_link = cls(
            variant_id=variant_id,
            bin_name=bin_name,
            location_id=location_id,
        )

        return variant_default_storage_bin_link
