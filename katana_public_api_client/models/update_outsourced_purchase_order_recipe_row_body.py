from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="UpdateOutsourcedPurchaseOrderRecipeRowBody")


@_attrs_define
class UpdateOutsourcedPurchaseOrderRecipeRowBody:
    quantity: Unset | float = UNSET

    def to_dict(self) -> dict[str, Any]:
        quantity = self.quantity

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if quantity is not UNSET:
            field_dict["quantity"] = quantity

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        quantity = d.pop("quantity", UNSET)

        update_outsourced_purchase_order_recipe_row_body = cls(
            quantity=quantity,
        )

        return update_outsourced_purchase_order_recipe_row_body
