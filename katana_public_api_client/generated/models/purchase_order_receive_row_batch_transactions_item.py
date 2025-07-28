from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="PurchaseOrderReceiveRowBatchTransactionsItem")


@_attrs_define
class PurchaseOrderReceiveRowBatchTransactionsItem:
    batch_id: int
    quantity: float

    def to_dict(self) -> dict[str, Any]:
        batch_id = self.batch_id

        quantity = self.quantity

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "batch_id": batch_id,
                "quantity": quantity,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        batch_id = d.pop("batch_id")

        quantity = d.pop("quantity")

        purchase_order_receive_row_batch_transactions_item = cls(
            batch_id=batch_id,
            quantity=quantity,
        )

        return purchase_order_receive_row_batch_transactions_item
