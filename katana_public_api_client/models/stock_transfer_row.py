from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.stock_transfer_row_batch_transactions_item import (
        StockTransferRowBatchTransactionsItem,
    )


T = TypeVar("T", bound="StockTransferRow")


@_attrs_define
class StockTransferRow:
    """Line item in a stock transfer showing the product variant and quantity being moved"""

    variant_id: int
    quantity: float
    id: int | Unset = UNSET
    cost_per_unit: float | Unset = UNSET
    batch_transactions: list[StockTransferRowBatchTransactionsItem] | Unset = UNSET
    deleted_at: datetime.datetime | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

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

        deleted_at: None | str | Unset
        if isinstance(self.deleted_at, Unset):
            deleted_at = UNSET
        elif isinstance(self.deleted_at, datetime.datetime):
            deleted_at = self.deleted_at.isoformat()
        else:
            deleted_at = self.deleted_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
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
        if deleted_at is not UNSET:
            field_dict["deleted_at"] = deleted_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.stock_transfer_row_batch_transactions_item import (
            StockTransferRowBatchTransactionsItem,
        )

        d = dict(src_dict)
        variant_id = d.pop("variant_id")

        quantity = d.pop("quantity")

        id = d.pop("id", UNSET)

        cost_per_unit = d.pop("cost_per_unit", UNSET)

        _batch_transactions = d.pop("batch_transactions", UNSET)
        batch_transactions: list[StockTransferRowBatchTransactionsItem] | Unset = UNSET
        if _batch_transactions is not UNSET:
            batch_transactions = []
            for batch_transactions_item_data in _batch_transactions:
                batch_transactions_item = (
                    StockTransferRowBatchTransactionsItem.from_dict(
                        batch_transactions_item_data
                    )
                )

                batch_transactions.append(batch_transactions_item)

        def _parse_deleted_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                deleted_at_type_0 = isoparse(data)

                return deleted_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        deleted_at = _parse_deleted_at(d.pop("deleted_at", UNSET))

        stock_transfer_row = cls(
            variant_id=variant_id,
            quantity=quantity,
            id=id,
            cost_per_unit=cost_per_unit,
            batch_transactions=batch_transactions,
            deleted_at=deleted_at,
        )

        stock_transfer_row.additional_properties = d
        return stock_transfer_row

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
