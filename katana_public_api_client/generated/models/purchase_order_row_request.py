from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="PurchaseOrderRowRequest")


@_attrs_define
class PurchaseOrderRowRequest:
    quantity: float
    price_per_unit: float
    purchase_uom_conversion_rate: Unset | float = UNSET
    purchase_uom: Unset | str = UNSET

    def to_dict(self) -> dict[str, Any]:
        quantity = self.quantity

        price_per_unit = self.price_per_unit

        purchase_uom_conversion_rate = self.purchase_uom_conversion_rate

        purchase_uom = self.purchase_uom

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "quantity": quantity,
                "price_per_unit": price_per_unit,
            }
        )
        if purchase_uom_conversion_rate is not UNSET:
            field_dict["purchase_uom_conversion_rate"] = purchase_uom_conversion_rate
        if purchase_uom is not UNSET:
            field_dict["purchase_uom"] = purchase_uom

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        quantity = d.pop("quantity")

        price_per_unit = d.pop("price_per_unit")

        purchase_uom_conversion_rate = d.pop("purchase_uom_conversion_rate", UNSET)

        purchase_uom = d.pop("purchase_uom", UNSET)

        purchase_order_row_request = cls(
            quantity=quantity,
            price_per_unit=price_per_unit,
            purchase_uom_conversion_rate=purchase_uom_conversion_rate,
            purchase_uom=purchase_uom,
        )

        return purchase_order_row_request
