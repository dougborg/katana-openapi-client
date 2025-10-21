from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="CreateRecipesRequestRowsItem")


@_attrs_define
class CreateRecipesRequestRowsItem:
    """
    Attributes:
        quantity (float): Required quantity of the ingredient
        ingredient_variant_id (int): ID of the ingredient variant
        product_variant_id (float): ID of the product variant
        notes (Union[Unset, str]): Additional notes for this recipe row
    """

    quantity: float
    ingredient_variant_id: int
    product_variant_id: float
    notes: Unset | str = UNSET

    def to_dict(self) -> dict[str, Any]:
        quantity = self.quantity

        ingredient_variant_id = self.ingredient_variant_id

        product_variant_id = self.product_variant_id

        notes = self.notes

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "quantity": quantity,
                "ingredient_variant_id": ingredient_variant_id,
                "product_variant_id": product_variant_id,
            }
        )
        if notes is not UNSET:
            field_dict["notes"] = notes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        quantity = d.pop("quantity")

        ingredient_variant_id = d.pop("ingredient_variant_id")

        product_variant_id = d.pop("product_variant_id")

        notes = d.pop("notes", UNSET)

        create_recipes_request_rows_item = cls(
            quantity=quantity,
            ingredient_variant_id=ingredient_variant_id,
            product_variant_id=product_variant_id,
            notes=notes,
        )

        return create_recipes_request_rows_item
