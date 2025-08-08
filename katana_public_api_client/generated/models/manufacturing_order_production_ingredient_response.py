import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="ManufacturingOrderProductionIngredientResponse")


@_attrs_define
class ManufacturingOrderProductionIngredientResponse:
    """Represents an ingredient used in manufacturing order production, tracking consumption and costs"""

    id: int
    location_id: int
    variant_id: int
    manufacturing_order_id: int
    manufacturing_order_recipe_row_id: int
    production_id: int
    quantity: float
    production_date: datetime.datetime
    cost: float
    created_at: Unset | datetime.datetime = UNSET
    updated_at: Unset | datetime.datetime = UNSET
    deleted_at: None | Unset | datetime.datetime = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        location_id = self.location_id

        variant_id = self.variant_id

        manufacturing_order_id = self.manufacturing_order_id

        manufacturing_order_recipe_row_id = self.manufacturing_order_recipe_row_id

        production_id = self.production_id

        quantity = self.quantity

        production_date = self.production_date.isoformat()

        cost = self.cost

        created_at: Unset | str = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: Unset | str = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        deleted_at: None | Unset | str
        if isinstance(self.deleted_at, Unset):
            deleted_at = UNSET
        elif isinstance(self.deleted_at, datetime.datetime):
            deleted_at = self.deleted_at.isoformat()
        else:
            deleted_at = self.deleted_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "location_id": location_id,
                "variant_id": variant_id,
                "manufacturing_order_id": manufacturing_order_id,
                "manufacturing_order_recipe_row_id": manufacturing_order_recipe_row_id,
                "production_id": production_id,
                "quantity": quantity,
                "production_date": production_date,
                "cost": cost,
            }
        )
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if deleted_at is not UNSET:
            field_dict["deleted_at"] = deleted_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        location_id = d.pop("location_id")

        variant_id = d.pop("variant_id")

        manufacturing_order_id = d.pop("manufacturing_order_id")

        manufacturing_order_recipe_row_id = d.pop("manufacturing_order_recipe_row_id")

        production_id = d.pop("production_id")

        quantity = d.pop("quantity")

        production_date = isoparse(d.pop("production_date"))

        cost = d.pop("cost")

        _created_at = d.pop("created_at", UNSET)
        created_at: Unset | datetime.datetime
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        _updated_at = d.pop("updated_at", UNSET)
        updated_at: Unset | datetime.datetime
        if isinstance(_updated_at, Unset):
            updated_at = UNSET
        else:
            updated_at = isoparse(_updated_at)

        def _parse_deleted_at(data: object) -> None | Unset | datetime.datetime:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                deleted_at_type_0 = isoparse(data)

                return deleted_at_type_0
            except:  # noqa: E722
                pass
            return cast(None | Unset | datetime.datetime, data)

        deleted_at = _parse_deleted_at(d.pop("deleted_at", UNSET))

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
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
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
