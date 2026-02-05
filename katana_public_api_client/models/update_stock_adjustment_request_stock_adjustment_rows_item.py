from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.stock_adjustment_batch_transaction import (
        StockAdjustmentBatchTransaction,
    )


T = TypeVar("T", bound="UpdateStockAdjustmentRequestStockAdjustmentRowsItem")


@_attrs_define
class UpdateStockAdjustmentRequestStockAdjustmentRowsItem:
    variant_id: int
    quantity: float
    cost_per_unit: float | Unset = UNSET
    batch_transactions: list[StockAdjustmentBatchTransaction] | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        variant_id = self.variant_id

        quantity = self.quantity

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

        update_stock_adjustment_request_stock_adjustment_rows_item = cls(
            variant_id=variant_id,
            quantity=quantity,
            cost_per_unit=cost_per_unit,
            batch_transactions=batch_transactions,
        )

        return update_stock_adjustment_request_stock_adjustment_rows_item
