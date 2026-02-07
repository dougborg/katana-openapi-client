from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.sales_order_fulfillment_sales_order_fulfillment_rows_item_batch_transactions_item import (
        SalesOrderFulfillmentSalesOrderFulfillmentRowsItemBatchTransactionsItem,
    )


T = TypeVar("T", bound="SalesOrderFulfillmentSalesOrderFulfillmentRowsItem")


@_attrs_define
class SalesOrderFulfillmentSalesOrderFulfillmentRowsItem:
    sales_order_row_id: int | Unset = UNSET
    quantity: float | Unset = UNSET
    batch_transactions: (
        list[SalesOrderFulfillmentSalesOrderFulfillmentRowsItemBatchTransactionsItem]
        | Unset
    ) = UNSET
    serial_numbers: list[int] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        sales_order_row_id = self.sales_order_row_id

        quantity = self.quantity

        batch_transactions: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.batch_transactions, Unset):
            batch_transactions = []
            for batch_transactions_item_data in self.batch_transactions:
                batch_transactions_item = batch_transactions_item_data.to_dict()
                batch_transactions.append(batch_transactions_item)

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
        if batch_transactions is not UNSET:
            field_dict["batch_transactions"] = batch_transactions
        if serial_numbers is not UNSET:
            field_dict["serial_numbers"] = serial_numbers

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.sales_order_fulfillment_sales_order_fulfillment_rows_item_batch_transactions_item import (
            SalesOrderFulfillmentSalesOrderFulfillmentRowsItemBatchTransactionsItem,
        )

        d = dict(src_dict)
        sales_order_row_id = d.pop("sales_order_row_id", UNSET)

        quantity = d.pop("quantity", UNSET)

        _batch_transactions = d.pop("batch_transactions", UNSET)
        batch_transactions: (
            list[
                SalesOrderFulfillmentSalesOrderFulfillmentRowsItemBatchTransactionsItem
            ]
            | Unset
        ) = UNSET
        if _batch_transactions is not UNSET:
            batch_transactions = []
            for batch_transactions_item_data in _batch_transactions:
                batch_transactions_item = SalesOrderFulfillmentSalesOrderFulfillmentRowsItemBatchTransactionsItem.from_dict(
                    batch_transactions_item_data
                )

                batch_transactions.append(batch_transactions_item)

        serial_numbers = cast(list[int], d.pop("serial_numbers", UNSET))

        sales_order_fulfillment_sales_order_fulfillment_rows_item = cls(
            sales_order_row_id=sales_order_row_id,
            quantity=quantity,
            batch_transactions=batch_transactions,
            serial_numbers=serial_numbers,
        )

        sales_order_fulfillment_sales_order_fulfillment_rows_item.additional_properties = d
        return sales_order_fulfillment_sales_order_fulfillment_rows_item

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
