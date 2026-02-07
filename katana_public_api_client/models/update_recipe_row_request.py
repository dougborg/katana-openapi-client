from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="UpdateRecipeRowRequest")


@_attrs_define
class UpdateRecipeRowRequest:
    """Request payload for updating a recipe row"""

    ingredient_variant_id: int | Unset = UNSET
    quantity: float | Unset = UNSET
    notes: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        ingredient_variant_id = self.ingredient_variant_id

        quantity = self.quantity

        notes = self.notes

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if ingredient_variant_id is not UNSET:
            field_dict["ingredient_variant_id"] = ingredient_variant_id
        if quantity is not UNSET:
            field_dict["quantity"] = quantity
        if notes is not UNSET:
            field_dict["notes"] = notes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        ingredient_variant_id = d.pop("ingredient_variant_id", UNSET)

        quantity = d.pop("quantity", UNSET)

        notes = d.pop("notes", UNSET)

        update_recipe_row_request = cls(
            ingredient_variant_id=ingredient_variant_id,
            quantity=quantity,
            notes=notes,
        )

        return update_recipe_row_request
