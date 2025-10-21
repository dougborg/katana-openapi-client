import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="Recipe")


@_attrs_define
class Recipe:
    """Recipe row representing ingredient requirements for product manufacturing (deprecated in favor of BOM rows)

    Example:
        {'id': 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', 'recipe_row_id': 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee',
            'product_item_id': 1, 'product_variant_id': 1, 'ingredient_variant_id': 1, 'quantity': 2, 'notes': 'some notes',
            'rank': 10000, 'created_at': '2021-04-05T12:00:00.000Z', 'updated_at': '2021-04-05T12:00:00.000Z'}

    Attributes:
        id (str): Unique identifier for the recipe row
        product_variant_id (int): ID of the product variant this recipe belongs to
        ingredient_variant_id (int): ID of the ingredient variant used in this recipe
        quantity (float): Required quantity of the ingredient
        recipe_row_id (Union[Unset, str]): Recipe row UUID identifier
        product_id (Union[Unset, int]): ID of the product that uses this recipe
        product_item_id (Union[Unset, int]): ID of the product item
        notes (Union[None, Unset, str]): Additional notes for this recipe row
        rank (Union[Unset, int]): Display order rank for recipe rows
        created_at (Union[Unset, datetime.datetime]): Timestamp when the recipe was created
        updated_at (Union[Unset, datetime.datetime]): Timestamp when the recipe was last updated
    """

    id: str
    product_variant_id: int
    ingredient_variant_id: int
    quantity: float
    recipe_row_id: Unset | str = UNSET
    product_id: Unset | int = UNSET
    product_item_id: Unset | int = UNSET
    notes: None | Unset | str = UNSET
    rank: Unset | int = UNSET
    created_at: Unset | datetime.datetime = UNSET
    updated_at: Unset | datetime.datetime = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        product_variant_id = self.product_variant_id

        ingredient_variant_id = self.ingredient_variant_id

        quantity = self.quantity

        recipe_row_id = self.recipe_row_id

        product_id = self.product_id

        product_item_id = self.product_item_id

        notes: None | Unset | str
        if isinstance(self.notes, Unset):
            notes = UNSET
        else:
            notes = self.notes

        rank = self.rank

        created_at: Unset | str = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: Unset | str = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "product_variant_id": product_variant_id,
                "ingredient_variant_id": ingredient_variant_id,
                "quantity": quantity,
            }
        )
        if recipe_row_id is not UNSET:
            field_dict["recipe_row_id"] = recipe_row_id
        if product_id is not UNSET:
            field_dict["product_id"] = product_id
        if product_item_id is not UNSET:
            field_dict["product_item_id"] = product_item_id
        if notes is not UNSET:
            field_dict["notes"] = notes
        if rank is not UNSET:
            field_dict["rank"] = rank
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        product_variant_id = d.pop("product_variant_id")

        ingredient_variant_id = d.pop("ingredient_variant_id")

        quantity = d.pop("quantity")

        recipe_row_id = d.pop("recipe_row_id", UNSET)

        product_id = d.pop("product_id", UNSET)

        product_item_id = d.pop("product_item_id", UNSET)

        def _parse_notes(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        notes = _parse_notes(d.pop("notes", UNSET))

        rank = d.pop("rank", UNSET)

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

        recipe = cls(
            id=id,
            product_variant_id=product_variant_id,
            ingredient_variant_id=ingredient_variant_id,
            quantity=quantity,
            recipe_row_id=recipe_row_id,
            product_id=product_id,
            product_item_id=product_item_id,
            notes=notes,
            rank=rank,
            created_at=created_at,
            updated_at=updated_at,
        )

        recipe.additional_properties = d
        return recipe

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
