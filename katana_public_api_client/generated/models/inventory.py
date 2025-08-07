from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.deletable_entity import DeletableEntity
    from ..models.location_type_0 import LocationType0
    from ..models.variant import Variant


T = TypeVar("T", bound="Inventory")


@_attrs_define
class Inventory:
    """Current inventory status for a variant at a specific location

    Example:
        {'variant_id': 2001, 'location_id': 101, 'safety_stock_level': 50.0, 'reorder_point': 50.0, 'average_cost':
            25.75, 'value_in_stock': 1287.5, 'quantity_in_stock': 50.0, 'quantity_committed': 15.0, 'quantity_expected':
            25.0, 'quantity_missing_or_excess': 10.0, 'quantity_potential': 35.0}
    """

    variant_id: int
    location_id: int
    safety_stock_level: None | Unset | float = UNSET
    reorder_point: None | Unset | float = UNSET
    average_cost: None | Unset | float = UNSET
    value_in_stock: None | Unset | float = UNSET
    quantity_in_stock: None | Unset | float = UNSET
    quantity_committed: None | Unset | float = UNSET
    quantity_expected: None | Unset | float = UNSET
    quantity_missing_or_excess: None | Unset | float = UNSET
    quantity_potential: None | Unset | float = UNSET
    variant: Union[Unset, "Variant"] = UNSET
    location: Union["DeletableEntity", "LocationType0", Unset] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.location_type_0 import LocationType0

        variant_id = self.variant_id

        location_id = self.location_id

        safety_stock_level: None | Unset | float
        if isinstance(self.safety_stock_level, Unset):
            safety_stock_level = UNSET
        else:
            safety_stock_level = self.safety_stock_level

        reorder_point: None | Unset | float
        if isinstance(self.reorder_point, Unset):
            reorder_point = UNSET
        else:
            reorder_point = self.reorder_point

        average_cost: None | Unset | float
        if isinstance(self.average_cost, Unset):
            average_cost = UNSET
        else:
            average_cost = self.average_cost

        value_in_stock: None | Unset | float
        if isinstance(self.value_in_stock, Unset):
            value_in_stock = UNSET
        else:
            value_in_stock = self.value_in_stock

        quantity_in_stock: None | Unset | float
        if isinstance(self.quantity_in_stock, Unset):
            quantity_in_stock = UNSET
        else:
            quantity_in_stock = self.quantity_in_stock

        quantity_committed: None | Unset | float
        if isinstance(self.quantity_committed, Unset):
            quantity_committed = UNSET
        else:
            quantity_committed = self.quantity_committed

        quantity_expected: None | Unset | float
        if isinstance(self.quantity_expected, Unset):
            quantity_expected = UNSET
        else:
            quantity_expected = self.quantity_expected

        quantity_missing_or_excess: None | Unset | float
        if isinstance(self.quantity_missing_or_excess, Unset):
            quantity_missing_or_excess = UNSET
        else:
            quantity_missing_or_excess = self.quantity_missing_or_excess

        quantity_potential: None | Unset | float
        if isinstance(self.quantity_potential, Unset):
            quantity_potential = UNSET
        else:
            quantity_potential = self.quantity_potential

        variant: Unset | dict[str, Any] = UNSET
        if not isinstance(self.variant, Unset):
            variant = self.variant.to_dict()

        location: Unset | dict[str, Any]
        if isinstance(self.location, Unset):
            location = UNSET
        elif isinstance(self.location, LocationType0):
            location = self.location.to_dict()
        else:
            location = self.location.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "variant_id": variant_id,
                "location_id": location_id,
            }
        )
        if safety_stock_level is not UNSET:
            field_dict["safety_stock_level"] = safety_stock_level
        if reorder_point is not UNSET:
            field_dict["reorder_point"] = reorder_point
        if average_cost is not UNSET:
            field_dict["average_cost"] = average_cost
        if value_in_stock is not UNSET:
            field_dict["value_in_stock"] = value_in_stock
        if quantity_in_stock is not UNSET:
            field_dict["quantity_in_stock"] = quantity_in_stock
        if quantity_committed is not UNSET:
            field_dict["quantity_committed"] = quantity_committed
        if quantity_expected is not UNSET:
            field_dict["quantity_expected"] = quantity_expected
        if quantity_missing_or_excess is not UNSET:
            field_dict["quantity_missing_or_excess"] = quantity_missing_or_excess
        if quantity_potential is not UNSET:
            field_dict["quantity_potential"] = quantity_potential
        if variant is not UNSET:
            field_dict["variant"] = variant
        if location is not UNSET:
            field_dict["location"] = location

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.deletable_entity import DeletableEntity
        from ..models.location_type_0 import LocationType0
        from ..models.variant import Variant

        d = dict(src_dict)
        variant_id = d.pop("variant_id")

        location_id = d.pop("location_id")

        def _parse_safety_stock_level(data: object) -> None | Unset | float:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | float, data)

        safety_stock_level = _parse_safety_stock_level(
            d.pop("safety_stock_level", UNSET)
        )

        def _parse_reorder_point(data: object) -> None | Unset | float:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | float, data)

        reorder_point = _parse_reorder_point(d.pop("reorder_point", UNSET))

        def _parse_average_cost(data: object) -> None | Unset | float:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | float, data)

        average_cost = _parse_average_cost(d.pop("average_cost", UNSET))

        def _parse_value_in_stock(data: object) -> None | Unset | float:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | float, data)

        value_in_stock = _parse_value_in_stock(d.pop("value_in_stock", UNSET))

        def _parse_quantity_in_stock(data: object) -> None | Unset | float:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | float, data)

        quantity_in_stock = _parse_quantity_in_stock(d.pop("quantity_in_stock", UNSET))

        def _parse_quantity_committed(data: object) -> None | Unset | float:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | float, data)

        quantity_committed = _parse_quantity_committed(
            d.pop("quantity_committed", UNSET)
        )

        def _parse_quantity_expected(data: object) -> None | Unset | float:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | float, data)

        quantity_expected = _parse_quantity_expected(d.pop("quantity_expected", UNSET))

        def _parse_quantity_missing_or_excess(
            data: object,
        ) -> None | Unset | float:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | float, data)

        quantity_missing_or_excess = _parse_quantity_missing_or_excess(
            d.pop("quantity_missing_or_excess", UNSET)
        )

        def _parse_quantity_potential(data: object) -> None | Unset | float:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | float, data)

        quantity_potential = _parse_quantity_potential(
            d.pop("quantity_potential", UNSET)
        )

        _variant = d.pop("variant", UNSET)
        variant: Unset | Variant
        if isinstance(_variant, Unset):
            variant = UNSET
        else:
            variant = Variant.from_dict(_variant)

        def _parse_location(
            data: object,
        ) -> Union["DeletableEntity", "LocationType0", Unset]:
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_location_type_0 = LocationType0.from_dict(data)

                return componentsschemas_location_type_0
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            componentsschemas_location_type_1 = DeletableEntity.from_dict(data)

            return componentsschemas_location_type_1

        location = _parse_location(d.pop("location", UNSET))

        inventory = cls(
            variant_id=variant_id,
            location_id=location_id,
            safety_stock_level=safety_stock_level,
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
