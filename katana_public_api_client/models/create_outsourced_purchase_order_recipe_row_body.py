from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="CreateOutsourcedPurchaseOrderRecipeRowBody")


@_attrs_define
class CreateOutsourcedPurchaseOrderRecipeRowBody:
    outsourced_purchase_order_id: int
    recipe_row_id: int
    quantity: float

    def to_dict(self) -> dict[str, Any]:
        outsourced_purchase_order_id = self.outsourced_purchase_order_id

        recipe_row_id = self.recipe_row_id

        quantity = self.quantity

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "outsourced_purchase_order_id": outsourced_purchase_order_id,
                "recipe_row_id": recipe_row_id,
                "quantity": quantity,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        outsourced_purchase_order_id = d.pop("outsourced_purchase_order_id")

        recipe_row_id = d.pop("recipe_row_id")

        quantity = d.pop("quantity")

        create_outsourced_purchase_order_recipe_row_body = cls(
            outsourced_purchase_order_id=outsourced_purchase_order_id,
            recipe_row_id=recipe_row_id,
            quantity=quantity,
        )

        return create_outsourced_purchase_order_recipe_row_body
