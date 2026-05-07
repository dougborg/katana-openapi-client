from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="SalesOrderFulfillmentRowRequest")


@_attrs_define
class SalesOrderFulfillmentRowRequest:
    """A fulfillment row item specifying which order row and quantity to fulfill"""

    sales_order_row_id: int | Unset = UNSET
    quantity: float | Unset = UNSET
    serial_numbers: list[int] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        sales_order_row_id = self.sales_order_row_id

        quantity = self.quantity

        serial_numbers: list[int] | Unset = UNSET
        if not isinstance(self.serial_numbers, Unset):
            serial_numbers = self.serial_numbers

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if sales_order_row_id is not UNSET:
            field_dict["sales_order_row_id"] = sales_order_row_id
        if quantity is not UNSET:
            field_dict["quantity"] = quantity
        if serial_numbers is not UNSET:
            field_dict["serial_numbers"] = serial_numbers

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        sales_order_row_id = d.pop("sales_order_row_id", UNSET)

        quantity = d.pop("quantity", UNSET)

        serial_numbers = cast(list[int], d.pop("serial_numbers", UNSET))

        sales_order_fulfillment_row_request = cls(
            sales_order_row_id=sales_order_row_id,
            quantity=quantity,
            serial_numbers=serial_numbers,
        )

        sales_order_fulfillment_row_request.additional_properties = d
        return sales_order_fulfillment_row_request

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
