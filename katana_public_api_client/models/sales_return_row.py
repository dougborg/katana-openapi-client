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
    from ..models.sales_return_row_batch_transactions_item import (
        SalesReturnRowBatchTransactionsItem,
    )


T = TypeVar("T", bound="SalesReturnRow")


@_attrs_define
class SalesReturnRow:
    """Individual line item within a sales return specifying returned product, quantity, and refund details"""

    id: int
    sales_return_id: int
    variant_id: int
    quantity: str
    created_at: datetime.datetime | Unset = UNSET
    updated_at: datetime.datetime | Unset = UNSET
    fulfillment_row_id: int | Unset = UNSET
    sales_order_row_id: int | Unset = UNSET
    net_price_per_unit: None | str | Unset = UNSET
    reason_id: int | None | Unset = UNSET
    restock_location_id: int | None | Unset = UNSET
    batch_transactions: list[SalesReturnRowBatchTransactionsItem] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        sales_return_id = self.sales_return_id

        variant_id = self.variant_id

        quantity = self.quantity

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: str | Unset = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        fulfillment_row_id = self.fulfillment_row_id

        sales_order_row_id = self.sales_order_row_id

        net_price_per_unit: None | str | Unset
        if isinstance(self.net_price_per_unit, Unset):
            net_price_per_unit = UNSET
        else:
            net_price_per_unit = self.net_price_per_unit

        reason_id: int | None | Unset
        if isinstance(self.reason_id, Unset):
            reason_id = UNSET
        else:
            reason_id = self.reason_id

        restock_location_id: int | None | Unset
        if isinstance(self.restock_location_id, Unset):
            restock_location_id = UNSET
        else:
            restock_location_id = self.restock_location_id

        batch_transactions: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.batch_transactions, Unset):
            batch_transactions = []
            for batch_transactions_item_data in self.batch_transactions:
                batch_transactions_item = batch_transactions_item_data.to_dict()
                batch_transactions.append(batch_transactions_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "sales_return_id": sales_return_id,
                "variant_id": variant_id,
                "quantity": quantity,
            }
        )
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if fulfillment_row_id is not UNSET:
            field_dict["fulfillment_row_id"] = fulfillment_row_id
        if sales_order_row_id is not UNSET:
            field_dict["sales_order_row_id"] = sales_order_row_id
        if net_price_per_unit is not UNSET:
            field_dict["net_price_per_unit"] = net_price_per_unit
        if reason_id is not UNSET:
            field_dict["reason_id"] = reason_id
        if restock_location_id is not UNSET:
            field_dict["restock_location_id"] = restock_location_id
        if batch_transactions is not UNSET:
            field_dict["batch_transactions"] = batch_transactions

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.sales_return_row_batch_transactions_item import (
            SalesReturnRowBatchTransactionsItem,
        )

        d = dict(src_dict)
        id = d.pop("id")

        sales_return_id = d.pop("sales_return_id")

        variant_id = d.pop("variant_id")

        quantity = d.pop("quantity")

        _created_at = d.pop("created_at", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        _updated_at = d.pop("updated_at", UNSET)
        updated_at: datetime.datetime | Unset
        if isinstance(_updated_at, Unset):
            updated_at = UNSET
        else:
            updated_at = isoparse(_updated_at)

        fulfillment_row_id = d.pop("fulfillment_row_id", UNSET)

        sales_order_row_id = d.pop("sales_order_row_id", UNSET)

        def _parse_net_price_per_unit(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        net_price_per_unit = _parse_net_price_per_unit(
            d.pop("net_price_per_unit", UNSET)
        )

        def _parse_reason_id(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        reason_id = _parse_reason_id(d.pop("reason_id", UNSET))

        def _parse_restock_location_id(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        restock_location_id = _parse_restock_location_id(
            d.pop("restock_location_id", UNSET)
        )

        _batch_transactions = d.pop("batch_transactions", UNSET)
        batch_transactions: list[SalesReturnRowBatchTransactionsItem] | Unset = UNSET
        if _batch_transactions is not UNSET:
            batch_transactions = []
            for batch_transactions_item_data in _batch_transactions:
                batch_transactions_item = SalesReturnRowBatchTransactionsItem.from_dict(
                    batch_transactions_item_data
                )

                batch_transactions.append(batch_transactions_item)

        sales_return_row = cls(
            id=id,
            sales_return_id=sales_return_id,
            variant_id=variant_id,
            quantity=quantity,
            created_at=created_at,
            updated_at=updated_at,
            fulfillment_row_id=fulfillment_row_id,
            sales_order_row_id=sales_order_row_id,
            net_price_per_unit=net_price_per_unit,
            reason_id=reason_id,
            restock_location_id=restock_location_id,
            batch_transactions=batch_transactions,
        )

        sales_return_row.additional_properties = d
        return sales_return_row

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
