from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="CreateSalesOrderRowRequest")


@_attrs_define
class CreateSalesOrderRowRequest:
    """Request payload for creating a new sales order row (line item)

    Example:
        {'sales_order_id': 2001, 'variant_id': 2101, 'quantity': 2, 'price_per_unit': 599.99, 'tax_rate_id': 301,
            'location_id': 1}
    """

    sales_order_id: int
    variant_id: int
    quantity: float
    price_per_unit: Unset | float = UNSET
    tax_rate_id: Unset | int = UNSET
    location_id: Unset | int = UNSET

    def to_dict(self) -> dict[str, Any]:
        sales_order_id = self.sales_order_id

        variant_id = self.variant_id

        quantity = self.quantity

        price_per_unit = self.price_per_unit

        tax_rate_id = self.tax_rate_id

        location_id = self.location_id

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "sales_order_id": sales_order_id,
                "variant_id": variant_id,
                "quantity": quantity,
            }
        )
        if price_per_unit is not UNSET:
            field_dict["price_per_unit"] = price_per_unit
        if tax_rate_id is not UNSET:
            field_dict["tax_rate_id"] = tax_rate_id
        if location_id is not UNSET:
            field_dict["location_id"] = location_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        sales_order_id = d.pop("sales_order_id")

        variant_id = d.pop("variant_id")

        quantity = d.pop("quantity")

        price_per_unit = d.pop("price_per_unit", UNSET)

        tax_rate_id = d.pop("tax_rate_id", UNSET)

        location_id = d.pop("location_id", UNSET)

        create_sales_order_row_request = cls(
            sales_order_id=sales_order_id,
            variant_id=variant_id,
            quantity=quantity,
            price_per_unit=price_per_unit,
            tax_rate_id=tax_rate_id,
            location_id=location_id,
        )

        return create_sales_order_row_request
