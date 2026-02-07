from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="SerialNumberStockTransactionsItem")


@_attrs_define
class SerialNumberStockTransactionsItem:
    id: str
    resource_id: int
    resource_type: str
    quantity_change: int
    transaction_date: datetime.datetime | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        resource_id = self.resource_id

        resource_type = self.resource_type

        quantity_change = self.quantity_change

        transaction_date: None | str | Unset
        if isinstance(self.transaction_date, Unset):
            transaction_date = UNSET
        elif isinstance(self.transaction_date, datetime.datetime):
            transaction_date = self.transaction_date.isoformat()
        else:
            transaction_date = self.transaction_date

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "resource_id": resource_id,
                "resource_type": resource_type,
                "quantity_change": quantity_change,
            }
        )
        if transaction_date is not UNSET:
            field_dict["transaction_date"] = transaction_date

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        resource_id = d.pop("resource_id")

        resource_type = d.pop("resource_type")

        quantity_change = d.pop("quantity_change")

        def _parse_transaction_date(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                transaction_date_type_0 = isoparse(data)

                return transaction_date_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        transaction_date = _parse_transaction_date(d.pop("transaction_date", UNSET))

        serial_number_stock_transactions_item = cls(
            id=id,
            resource_id=resource_id,
            resource_type=resource_type,
            quantity_change=quantity_change,
            transaction_date=transaction_date,
        )

        serial_number_stock_transactions_item.additional_properties = d
        return serial_number_stock_transactions_item

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
