from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="InventorySafetyStockLevel")


@_attrs_define
class InventorySafetyStockLevel:
    """Safety stock level configuration to maintain minimum inventory buffers and prevent stockouts

    Example:
        {'location_id': 1, 'variant_id': 3001, 'value': 25.0}
    """

    location_id: int
    variant_id: int
    value: float

    def to_dict(self) -> dict[str, Any]:
        location_id = self.location_id

        variant_id = self.variant_id

        value = self.value

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "location_id": location_id,
                "variant_id": variant_id,
                "value": value,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        location_id = d.pop("location_id")

        variant_id = d.pop("variant_id")

        value = d.pop("value")

        inventory_safety_stock_level = cls(
            location_id=location_id,
            variant_id=variant_id,
            value=value,
        )

        return inventory_safety_stock_level
