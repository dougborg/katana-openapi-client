from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="VariantDefaultStorageBinLink")


@_attrs_define
class VariantDefaultStorageBinLink:
    """Link defining the default storage bin assignment for a specific variant to optimize warehouse picking and storage

    Example:
        {'location_id': 1, 'variant_id': 3001, 'bin_name': 'A-01-SHELF-1'}

    Attributes:
        variant_id (int): ID of the variant to link to the storage bin
        bin_name (str): Name of the storage bin to set as default for this variant
        location_id (Union[Unset, int]): ID of the location where the storage bin is located
    """

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
