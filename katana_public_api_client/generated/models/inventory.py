from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.location import Location
    from ..models.variant import Variant


T = TypeVar("T", bound="Inventory")


@_attrs_define
class Inventory:
    variant_id: int
    location_id: int
    reorder_point: str
    average_cost: str
    value_in_stock: str
    quantity_in_stock: str
    quantity_committed: str
    quantity_expected: str
    quantity_missing_or_excess: str
    quantity_potential: str
    variant: Union[Unset, "Variant"] = UNSET
    location: Union[Unset, "Location"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        variant_id = self.variant_id

        location_id = self.location_id

        reorder_point = self.reorder_point

        average_cost = self.average_cost

        value_in_stock = self.value_in_stock

        quantity_in_stock = self.quantity_in_stock

        quantity_committed = self.quantity_committed

        quantity_expected = self.quantity_expected

        quantity_missing_or_excess = self.quantity_missing_or_excess

        quantity_potential = self.quantity_potential

        variant: Unset | dict[str, Any] = UNSET
        if not isinstance(self.variant, Unset):
            variant = self.variant.to_dict()

        location: Unset | dict[str, Any] = UNSET
        if not isinstance(self.location, Unset):
            location = self.location.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "variant_id": variant_id,
                "location_id": location_id,
                "reorder_point": reorder_point,
                "average_cost": average_cost,
                "value_in_stock": value_in_stock,
                "quantity_in_stock": quantity_in_stock,
                "quantity_committed": quantity_committed,
                "quantity_expected": quantity_expected,
                "quantity_missing_or_excess": quantity_missing_or_excess,
                "quantity_potential": quantity_potential,
            }
        )
        if variant is not UNSET:
            field_dict["variant"] = variant
        if location is not UNSET:
            field_dict["location"] = location

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.location import Location
        from ..models.variant import Variant

        d = dict(src_dict)
        variant_id = d.pop("variant_id")

        location_id = d.pop("location_id")

        reorder_point = d.pop("reorder_point")

        average_cost = d.pop("average_cost")

        value_in_stock = d.pop("value_in_stock")

        quantity_in_stock = d.pop("quantity_in_stock")

        quantity_committed = d.pop("quantity_committed")

        quantity_expected = d.pop("quantity_expected")

        quantity_missing_or_excess = d.pop("quantity_missing_or_excess")

        quantity_potential = d.pop("quantity_potential")

        _variant = d.pop("variant", UNSET)
        variant: Unset | Variant
        if isinstance(_variant, Unset):
            variant = UNSET
        else:
            variant = Variant.from_dict(_variant)

        _location = d.pop("location", UNSET)
        location: Unset | Location
        if isinstance(_location, Unset):
            location = UNSET
        else:
            location = Location.from_dict(_location)

        inventory = cls(
            variant_id=variant_id,
            location_id=location_id,
            reorder_point=reorder_point,
            average_cost=average_cost,
            value_in_stock=value_in_stock,
            quantity_in_stock=quantity_in_stock,
            quantity_committed=quantity_committed,
            quantity_expected=quantity_expected,
            quantity_missing_or_excess=quantity_missing_or_excess,
            quantity_potential=quantity_potential,
            variant=variant,
            location=location,
        )

        inventory.additional_properties = d
        return inventory

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
