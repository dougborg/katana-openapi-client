from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.purchase_order_receive_row_batch_transactions_item import (
        PurchaseOrderReceiveRowBatchTransactionsItem,
    )


T = TypeVar("T", bound="PurchaseOrderReceiveRow")


@_attrs_define
class PurchaseOrderReceiveRow:
    purchase_order_row_id: int
    quantity: float
    received_date: Unset | str = UNSET
    batch_transactions: Unset | list["PurchaseOrderReceiveRowBatchTransactionsItem"] = (
        UNSET
    )

    def to_dict(self) -> dict[str, Any]:
        purchase_order_row_id = self.purchase_order_row_id

        quantity = self.quantity

        received_date = self.received_date

        batch_transactions: Unset | list[dict[str, Any]] = UNSET
        if not isinstance(self.batch_transactions, Unset):
            batch_transactions = []
            for batch_transactions_item_data in self.batch_transactions:
                batch_transactions_item = batch_transactions_item_data.to_dict()
                batch_transactions.append(batch_transactions_item)

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "purchase_order_row_id": purchase_order_row_id,
                "quantity": quantity,
            }
        )
        if received_date is not UNSET:
            field_dict["received_date"] = received_date
        if batch_transactions is not UNSET:
            field_dict["batch_transactions"] = batch_transactions

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.purchase_order_receive_row_batch_transactions_item import (
            PurchaseOrderReceiveRowBatchTransactionsItem,
        )

        d = dict(src_dict)
        purchase_order_row_id = d.pop("purchase_order_row_id")

        quantity = d.pop("quantity")

        received_date = d.pop("received_date", UNSET)

        batch_transactions = []
        _batch_transactions = d.pop("batch_transactions", UNSET)
        for batch_transactions_item_data in _batch_transactions or []:
            batch_transactions_item = (
                PurchaseOrderReceiveRowBatchTransactionsItem.from_dict(
                    batch_transactions_item_data
                )
            )

            batch_transactions.append(batch_transactions_item)

        purchase_order_receive_row = cls(
            purchase_order_row_id=purchase_order_row_id,
            quantity=quantity,
            received_date=received_date,
            batch_transactions=batch_transactions,
        )

        return purchase_order_receive_row
