from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="StockAdjustmentBatchTransaction")


@_attrs_define
class StockAdjustmentBatchTransaction:
    """Batch-specific transaction for tracking stock adjustments. Each
    entry pairs a quantity with the batch it applies to; ``batch_id``
    is nullable because some adjustments target unbatched stock (e.g.
    an aggregate correction to a non-batch-tracked variant) — Katana
    returns ``batch_id: null`` in that case.

        Example:
            {'batch_id': 1001, 'quantity': 50}
    """

    quantity: float
    batch_id: int | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        quantity = self.quantity

        batch_id: int | None | Unset
        if isinstance(self.batch_id, Unset):
            batch_id = UNSET
        else:
            batch_id = self.batch_id

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "quantity": quantity,
            }
        )
        if batch_id is not UNSET:
            field_dict["batch_id"] = batch_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        quantity = d.pop("quantity")

        def _parse_batch_id(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        batch_id = _parse_batch_id(d.pop("batch_id", UNSET))

        stock_adjustment_batch_transaction = cls(
            quantity=quantity,
            batch_id=batch_id,
        )

        return stock_adjustment_batch_transaction
