from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="GetSalesOrderReturnableItemsResponse200DataItem")


@_attrs_define
class GetSalesOrderReturnableItemsResponse200DataItem:
    id: Unset | int = UNSET
    variant_id: Unset | int = UNSET
    product_id: Unset | int = UNSET
    quantity: Unset | float = UNSET
    returned_quantity: Unset | float = UNSET
    max_returnable_quantity: Unset | float = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        variant_id = self.variant_id

        product_id = self.product_id

        quantity = self.quantity

        returned_quantity = self.returned_quantity

        max_returnable_quantity = self.max_returnable_quantity

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if variant_id is not UNSET:
            field_dict["variant_id"] = variant_id
        if product_id is not UNSET:
            field_dict["product_id"] = product_id
        if quantity is not UNSET:
            field_dict["quantity"] = quantity
        if returned_quantity is not UNSET:
            field_dict["returned_quantity"] = returned_quantity
        if max_returnable_quantity is not UNSET:
            field_dict["max_returnable_quantity"] = max_returnable_quantity

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id", UNSET)

        variant_id = d.pop("variant_id", UNSET)

        product_id = d.pop("product_id", UNSET)

        quantity = d.pop("quantity", UNSET)

        returned_quantity = d.pop("returned_quantity", UNSET)

        max_returnable_quantity = d.pop("max_returnable_quantity", UNSET)

        get_sales_order_returnable_items_response_200_data_item = cls(
            id=id,
            variant_id=variant_id,
            product_id=product_id,
            quantity=quantity,
            returned_quantity=returned_quantity,
            max_returnable_quantity=max_returnable_quantity,
        )

        get_sales_order_returnable_items_response_200_data_item.additional_properties = d
        return get_sales_order_returnable_items_response_200_data_item

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
