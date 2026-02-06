from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.update_sales_return_row_body_batch_transactions_item import (
        UpdateSalesReturnRowBodyBatchTransactionsItem,
    )


T = TypeVar("T", bound="UpdateSalesReturnRowBody")


@_attrs_define
class UpdateSalesReturnRowBody:
    quantity: str | Unset = UNSET
    restock_location_id: int | Unset = UNSET
    reason_id: int | Unset = UNSET
    batch_transactions: list[UpdateSalesReturnRowBodyBatchTransactionsItem] | Unset = (
        UNSET
    )

    def to_dict(self) -> dict[str, Any]:
        quantity = self.quantity

        restock_location_id = self.restock_location_id

        reason_id = self.reason_id

        batch_transactions: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.batch_transactions, Unset):
            batch_transactions = []
            for batch_transactions_item_data in self.batch_transactions:
                batch_transactions_item = batch_transactions_item_data.to_dict()
                batch_transactions.append(batch_transactions_item)

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if quantity is not UNSET:
            field_dict["quantity"] = quantity
        if restock_location_id is not UNSET:
            field_dict["restock_location_id"] = restock_location_id
        if reason_id is not UNSET:
            field_dict["reason_id"] = reason_id
        if batch_transactions is not UNSET:
            field_dict["batch_transactions"] = batch_transactions

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.update_sales_return_row_body_batch_transactions_item import (
            UpdateSalesReturnRowBodyBatchTransactionsItem,
        )

        d = dict(src_dict)
        quantity = d.pop("quantity", UNSET)

        restock_location_id = d.pop("restock_location_id", UNSET)

        reason_id = d.pop("reason_id", UNSET)

        _batch_transactions = d.pop("batch_transactions", UNSET)
        batch_transactions: (
            list[UpdateSalesReturnRowBodyBatchTransactionsItem] | Unset
        ) = UNSET
        if _batch_transactions is not UNSET:
            batch_transactions = []
            for batch_transactions_item_data in _batch_transactions:
                batch_transactions_item = (
                    UpdateSalesReturnRowBodyBatchTransactionsItem.from_dict(
                        batch_transactions_item_data
                    )
                )

                batch_transactions.append(batch_transactions_item)

        update_sales_return_row_body = cls(
            quantity=quantity,
            restock_location_id=restock_location_id,
            reason_id=reason_id,
            batch_transactions=batch_transactions,
        )

        return update_sales_return_row_body
