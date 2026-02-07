from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="CreateInventoryReorderPointRequest")


@_attrs_define
class CreateInventoryReorderPointRequest:
    """Request payload for creating a new inventory reorder point"""

    variant_id: int
    location_id: int
    value: float

    def to_dict(self) -> dict[str, Any]:
        variant_id = self.variant_id

        location_id = self.location_id

        value = self.value

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "variant_id": variant_id,
                "location_id": location_id,
                "value": value,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        variant_id = d.pop("variant_id")

        location_id = d.pop("location_id")

        value = d.pop("value")

        create_inventory_reorder_point_request = cls(
            variant_id=variant_id,
            location_id=location_id,
            value=value,
        )

        return create_inventory_reorder_point_request
