from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="CreateInventoryReorderPointBody")


@_attrs_define
class CreateInventoryReorderPointBody:
    variant_id: int
    location_id: int
    reorder_point: float
    reorder_quantity: Unset | float = UNSET

    def to_dict(self) -> dict[str, Any]:
        variant_id = self.variant_id

        location_id = self.location_id

        reorder_point = self.reorder_point

        reorder_quantity = self.reorder_quantity

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "variant_id": variant_id,
                "location_id": location_id,
                "reorder_point": reorder_point,
            }
        )
        if reorder_quantity is not UNSET:
            field_dict["reorder_quantity"] = reorder_quantity

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        variant_id = d.pop("variant_id")

        location_id = d.pop("location_id")

        reorder_point = d.pop("reorder_point")

        reorder_quantity = d.pop("reorder_quantity", UNSET)

        create_inventory_reorder_point_body = cls(
            variant_id=variant_id,
            location_id=location_id,
            reorder_point=reorder_point,
            reorder_quantity=reorder_quantity,
        )

        return create_inventory_reorder_point_body
