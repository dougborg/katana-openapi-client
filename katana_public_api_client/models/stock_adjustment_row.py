from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.stock_adjustment_batch_transaction import (
        StockAdjustmentBatchTransaction,
    )


T = TypeVar("T", bound="StockAdjustmentRow")


@_attrs_define
class StockAdjustmentRow:
    """Individual line item in a stock adjustment showing specific variant and quantity changes

    Example:
        {'id': 3001, 'variant_id': 501, 'quantity': 100, 'cost_per_unit': 123.45, 'batch_transactions': [{'batch_id':
            1001, 'quantity': 50}, {'batch_id': 1002, 'quantity': 50}]}
    """

    variant_id: int
    quantity: float
    id: int | Unset = UNSET
    cost_per_unit: float | Unset = UNSET
    batch_transactions: list[StockAdjustmentBatchTransaction] | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        variant_id = self.variant_id

        quantity = self.quantity

        id = self.id

        cost_per_unit = self.cost_per_unit

        batch_transactions: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.batch_transactions, Unset):
            batch_transactions = []
            for batch_transactions_item_data in self.batch_transactions:
                batch_transactions_item = batch_transactions_item_data.to_dict()
                batch_transactions.append(batch_transactions_item)

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "variant_id": variant_id,
                "quantity": quantity,
            }
        )
        if id is not UNSET:
            field_dict["id"] = id
        if cost_per_unit is not UNSET:
            field_dict["cost_per_unit"] = cost_per_unit
        if batch_transactions is not UNSET:
            field_dict["batch_transactions"] = batch_transactions

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.stock_adjustment_batch_transaction import (
            StockAdjustmentBatchTransaction,
        )

        d = dict(src_dict)
        variant_id = d.pop("variant_id")

        quantity = d.pop("quantity")

        id = d.pop("id", UNSET)

        cost_per_unit = d.pop("cost_per_unit", UNSET)

        _batch_transactions = d.pop("batch_transactions", UNSET)
        batch_transactions: list[StockAdjustmentBatchTransaction] | Unset = UNSET
        if _batch_transactions is not UNSET:
            batch_transactions = []
            for batch_transactions_item_data in _batch_transactions:
                batch_transactions_item = StockAdjustmentBatchTransaction.from_dict(
                    batch_transactions_item_data
                )

                batch_transactions.append(batch_transactions_item)

        stock_adjustment_row = cls(
            variant_id=variant_id,
            quantity=quantity,
            id=id,
            cost_per_unit=cost_per_unit,
            batch_transactions=batch_transactions,
        )

        return stock_adjustment_row
