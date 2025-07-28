from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="UnlinkVariantBinLocationRequest")


@_attrs_define
class UnlinkVariantBinLocationRequest:
    location_id: int
    variant_id: int

    def to_dict(self) -> dict[str, Any]:
        location_id = self.location_id

        variant_id = self.variant_id

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "location_id": location_id,
                "variant_id": variant_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        location_id = d.pop("location_id")

        variant_id = d.pop("variant_id")

        unlink_variant_bin_location_request = cls(
            location_id=location_id,
            variant_id=variant_id,
        )

        return unlink_variant_bin_location_request
