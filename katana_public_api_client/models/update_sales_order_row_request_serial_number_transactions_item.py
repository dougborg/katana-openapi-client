from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="UpdateSalesOrderRowRequestSerialNumberTransactionsItem")


@_attrs_define
class UpdateSalesOrderRowRequestSerialNumberTransactionsItem:
    serial_number_id: int | Unset = UNSET
    quantity: float | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        serial_number_id = self.serial_number_id

        quantity = self.quantity

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if serial_number_id is not UNSET:
            field_dict["serial_number_id"] = serial_number_id
        if quantity is not UNSET:
            field_dict["quantity"] = quantity

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        serial_number_id = d.pop("serial_number_id", UNSET)

        quantity = d.pop("quantity", UNSET)

        update_sales_order_row_request_serial_number_transactions_item = cls(
            serial_number_id=serial_number_id,
            quantity=quantity,
        )

        update_sales_order_row_request_serial_number_transactions_item.additional_properties = d
        return update_sales_order_row_request_serial_number_transactions_item

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
