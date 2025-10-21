from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="UpdateSalesOrderRowRequest")


@_attrs_define
class UpdateSalesOrderRowRequest:
    """Request payload for updating an existing sales order row

    Example:
        {'quantity': 3, 'price_per_unit': 549.99}
    """

    variant_id: Unset | int = UNSET
    quantity: Unset | float = UNSET
    price_per_unit: Unset | float = UNSET
    tax_rate_id: Unset | int = UNSET
    location_id: Unset | int = UNSET

    def to_dict(self) -> dict[str, Any]:
        variant_id = self.variant_id

        quantity = self.quantity

        price_per_unit = self.price_per_unit

        tax_rate_id = self.tax_rate_id

        location_id = self.location_id

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if variant_id is not UNSET:
            field_dict["variant_id"] = variant_id
        if quantity is not UNSET:
            field_dict["quantity"] = quantity
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
        variant_id = d.pop("variant_id", UNSET)

        quantity = d.pop("quantity", UNSET)

        price_per_unit = d.pop("price_per_unit", UNSET)

        tax_rate_id = d.pop("tax_rate_id", UNSET)

        location_id = d.pop("location_id", UNSET)

        update_sales_order_row_request = cls(
            variant_id=variant_id,
            quantity=quantity,
            price_per_unit=price_per_unit,
            tax_rate_id=tax_rate_id,
            location_id=location_id,
        )

        return update_sales_order_row_request
