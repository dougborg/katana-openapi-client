from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="SalesOrderRowBatchTransactionUpdate")


@_attrs_define
class SalesOrderRowBatchTransactionUpdate:
    """Batch allocation on a sales order row update. Omitting quantity sets the allocation to zero; it does not preserve
    its previous quantity (verified against the live API, #1053).

        Example:
            {'batch_id': 1109}
    """

    batch_id: int
    quantity: float | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        batch_id = self.batch_id

        quantity = self.quantity

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "batch_id": batch_id,
            }
        )
        if quantity is not UNSET:
            field_dict["quantity"] = quantity

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        batch_id = d.pop("batch_id")

        quantity = d.pop("quantity", UNSET)

        sales_order_row_batch_transaction_update = cls(
            batch_id=batch_id,
            quantity=quantity,
        )

        return sales_order_row_batch_transaction_update
