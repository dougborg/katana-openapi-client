from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.create_sales_order_row_request_attributes_item import (
        CreateSalesOrderRowRequestAttributesItem,
    )


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
    price_per_unit: float | Unset = UNSET
    tax_rate_id: int | Unset = UNSET
    location_id: int | Unset = UNSET
    attributes: list[CreateSalesOrderRowRequestAttributesItem] | Unset = UNSET
    total_discount: float | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        sales_order_id = self.sales_order_id

        variant_id = self.variant_id

        quantity = self.quantity

        price_per_unit = self.price_per_unit

        tax_rate_id = self.tax_rate_id

        location_id = self.location_id

        attributes: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.attributes, Unset):
            attributes = []
            for attributes_item_data in self.attributes:
                attributes_item = attributes_item_data.to_dict()
                attributes.append(attributes_item)

        total_discount = self.total_discount

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
        if attributes is not UNSET:
            field_dict["attributes"] = attributes
        if total_discount is not UNSET:
            field_dict["total_discount"] = total_discount

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.create_sales_order_row_request_attributes_item import (
            CreateSalesOrderRowRequestAttributesItem,
        )

        d = dict(src_dict)
        sales_order_id = d.pop("sales_order_id")

        variant_id = d.pop("variant_id")

        quantity = d.pop("quantity")

        price_per_unit = d.pop("price_per_unit", UNSET)

        tax_rate_id = d.pop("tax_rate_id", UNSET)

        location_id = d.pop("location_id", UNSET)

        _attributes = d.pop("attributes", UNSET)
        attributes: list[CreateSalesOrderRowRequestAttributesItem] | Unset = UNSET
        if _attributes is not UNSET:
            attributes = []
            for attributes_item_data in _attributes:
                attributes_item = CreateSalesOrderRowRequestAttributesItem.from_dict(
                    attributes_item_data
                )

                attributes.append(attributes_item)

        total_discount = d.pop("total_discount", UNSET)

        create_sales_order_row_request = cls(
            sales_order_id=sales_order_id,
            variant_id=variant_id,
            quantity=quantity,
            price_per_unit=price_per_unit,
            tax_rate_id=tax_rate_id,
            location_id=location_id,
            attributes=attributes,
            total_discount=total_discount,
        )

        return create_sales_order_row_request
