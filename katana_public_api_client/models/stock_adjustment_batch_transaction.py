from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="StockAdjustmentBatchTransaction")


@_attrs_define
class StockAdjustmentBatchTransaction:
    """Batch-specific transaction for tracking stock adjustments per batch

    Example:
        {'batch_id': 1001, 'quantity': 50}
    """

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

        stock_adjustment_batch_transaction = cls(
            batch_id=batch_id,
            quantity=quantity,
        )

        return stock_adjustment_batch_transaction
