from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

T = TypeVar("T", bound="InventorySafetyStockLevel")


@_attrs_define
class InventorySafetyStockLevel:
    """Safety stock level configuration to maintain minimum inventory buffers and prevent stockouts

    Example:
        {'location_id': 1, 'variant_id': 3001, 'value': 25.0}

    Attributes:
        location_id (int): ID of the location where the safety stock level applies
        variant_id (int): ID of the variant for which the safety stock level is set
        value (float): Minimum quantity to maintain as safety stock buffer
    """

    location_id: int
    variant_id: int
    value: float
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        location_id = self.location_id

        variant_id = self.variant_id

        value = self.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
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

        inventory_safety_stock_level.additional_properties = d
        return inventory_safety_stock_level

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
