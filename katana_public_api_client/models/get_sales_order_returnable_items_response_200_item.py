from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

T = TypeVar("T", bound="GetSalesOrderReturnableItemsResponse200Item")


@_attrs_define
class GetSalesOrderReturnableItemsResponse200Item:
    variant_id: int
    fulfillment_row_id: int
    available_for_return_quantity: str
    net_price_per_unit: str
    location_id: int
    quantity_sold: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        variant_id = self.variant_id

        fulfillment_row_id = self.fulfillment_row_id

        available_for_return_quantity = self.available_for_return_quantity

        net_price_per_unit = self.net_price_per_unit

        location_id = self.location_id

        quantity_sold = self.quantity_sold

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "variant_id": variant_id,
                "fulfillment_row_id": fulfillment_row_id,
                "available_for_return_quantity": available_for_return_quantity,
                "net_price_per_unit": net_price_per_unit,
                "location_id": location_id,
                "quantity_sold": quantity_sold,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        variant_id = d.pop("variant_id")

        fulfillment_row_id = d.pop("fulfillment_row_id")

        available_for_return_quantity = d.pop("available_for_return_quantity")

        net_price_per_unit = d.pop("net_price_per_unit")

        location_id = d.pop("location_id")

        quantity_sold = d.pop("quantity_sold")

        get_sales_order_returnable_items_response_200_item = cls(
            variant_id=variant_id,
            fulfillment_row_id=fulfillment_row_id,
            available_for_return_quantity=available_for_return_quantity,
            net_price_per_unit=net_price_per_unit,
            location_id=location_id,
            quantity_sold=quantity_sold,
        )

        get_sales_order_returnable_items_response_200_item.additional_properties = d
        return get_sales_order_returnable_items_response_200_item

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
