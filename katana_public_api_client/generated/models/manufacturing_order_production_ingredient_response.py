import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="ManufacturingOrderProductionIngredientResponse")


@_attrs_define
class ManufacturingOrderProductionIngredientResponse:
    id: Unset | int = UNSET
    location_id: Unset | int = UNSET
    variant_id: Unset | int = UNSET
    manufacturing_order_id: Unset | int = UNSET
    manufacturing_order_recipe_row_id: Unset | int = UNSET
    production_id: Unset | int = UNSET
    quantity: Unset | float = UNSET
    production_date: Unset | datetime.datetime = UNSET
    cost: Unset | float = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        location_id = self.location_id

        variant_id = self.variant_id

        manufacturing_order_id = self.manufacturing_order_id

        manufacturing_order_recipe_row_id = self.manufacturing_order_recipe_row_id

        production_id = self.production_id

        quantity = self.quantity

        production_date: Unset | str = UNSET
        if not isinstance(self.production_date, Unset):
            production_date = self.production_date.isoformat()

        cost = self.cost

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if location_id is not UNSET:
            field_dict["location_id"] = location_id
        if variant_id is not UNSET:
            field_dict["variant_id"] = variant_id
        if manufacturing_order_id is not UNSET:
            field_dict["manufacturing_order_id"] = manufacturing_order_id
        if manufacturing_order_recipe_row_id is not UNSET:
            field_dict["manufacturing_order_recipe_row_id"] = (
                manufacturing_order_recipe_row_id
            )
        if production_id is not UNSET:
            field_dict["production_id"] = production_id
        if quantity is not UNSET:
            field_dict["quantity"] = quantity
        if production_date is not UNSET:
            field_dict["production_date"] = production_date
        if cost is not UNSET:
            field_dict["cost"] = cost

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id", UNSET)

        location_id = d.pop("location_id", UNSET)

        variant_id = d.pop("variant_id", UNSET)

        manufacturing_order_id = d.pop("manufacturing_order_id", UNSET)

        manufacturing_order_recipe_row_id = d.pop(
            "manufacturing_order_recipe_row_id", UNSET
        )

        production_id = d.pop("production_id", UNSET)

        quantity = d.pop("quantity", UNSET)

        _production_date = d.pop("production_date", UNSET)
        production_date: Unset | datetime.datetime
        if isinstance(_production_date, Unset):
            production_date = UNSET
        else:
            production_date = isoparse(_production_date)

        cost = d.pop("cost", UNSET)

        manufacturing_order_production_ingredient_response = cls(
            id=id,
            location_id=location_id,
            variant_id=variant_id,
            manufacturing_order_id=manufacturing_order_id,
            manufacturing_order_recipe_row_id=manufacturing_order_recipe_row_id,
            production_id=production_id,
            quantity=quantity,
            production_date=production_date,
            cost=cost,
        )

        manufacturing_order_production_ingredient_response.additional_properties = d
        return manufacturing_order_production_ingredient_response

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
