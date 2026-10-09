from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.stock_adjustment_batch_transaction import (
        StockAdjustmentBatchTransaction,
    )
    from ..models.stock_adjustment_traceability import StockAdjustmentTraceability


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
    traceability: list[StockAdjustmentTraceability] | Unset = UNSET
    deleted_at: datetime.datetime | Unset | None = UNSET

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

        traceability: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.traceability, Unset):
            traceability = []
            for traceability_item_data in self.traceability:
                traceability_item = traceability_item_data.to_dict()
                traceability.append(traceability_item)

        deleted_at: str | Unset | None
        if isinstance(self.deleted_at, Unset):
            deleted_at = UNSET
        elif isinstance(self.deleted_at, datetime.datetime):
            deleted_at = self.deleted_at.isoformat()
        else:
            deleted_at = self.deleted_at

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
        if traceability is not UNSET:
            field_dict["traceability"] = traceability
        if deleted_at is not UNSET:
            field_dict["deleted_at"] = deleted_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.stock_adjustment_batch_transaction import (
            StockAdjustmentBatchTransaction,
        )
        from ..models.stock_adjustment_traceability import (
            StockAdjustmentTraceability,
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
                    cast(Mapping[str, Any], batch_transactions_item_data)
                )

                batch_transactions.append(batch_transactions_item)

        _traceability = d.pop("traceability", UNSET)
        traceability: list[StockAdjustmentTraceability] | Unset = UNSET
        if _traceability is not UNSET:
            traceability = []
            for traceability_item_data in _traceability:
                traceability_item = StockAdjustmentTraceability.from_dict(
                    cast(Mapping[str, Any], traceability_item_data)
                )

                traceability.append(traceability_item)

        def _parse_deleted_at(data: object) -> datetime.datetime | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                deleted_at_type_0 = datetime.datetime.fromisoformat(data)

                return deleted_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | Unset | None, data)

        deleted_at = _parse_deleted_at(d.pop("deleted_at", UNSET))

        stock_adjustment_row = cls(
            variant_id=variant_id,
            quantity=quantity,
            id=id,
            cost_per_unit=cost_per_unit,
            batch_transactions=batch_transactions,
            traceability=traceability,
            deleted_at=deleted_at,
        )

        return stock_adjustment_row
