from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="UpdateStockTransferBody")


@_attrs_define
class UpdateStockTransferBody:
    stock_transfer_number: str | Unset = UNSET
    transfer_date: datetime.datetime | Unset = UNSET
    order_created_date: datetime.datetime | Unset = UNSET
    expected_arrival_date: datetime.datetime | Unset = UNSET
    additional_info: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        stock_transfer_number = self.stock_transfer_number

        transfer_date: str | Unset = UNSET
        if not isinstance(self.transfer_date, Unset):
            transfer_date = self.transfer_date.isoformat()

        order_created_date: str | Unset = UNSET
        if not isinstance(self.order_created_date, Unset):
            order_created_date = self.order_created_date.isoformat()

        expected_arrival_date: str | Unset = UNSET
        if not isinstance(self.expected_arrival_date, Unset):
            expected_arrival_date = self.expected_arrival_date.isoformat()

        additional_info = self.additional_info

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if stock_transfer_number is not UNSET:
            field_dict["stock_transfer_number"] = stock_transfer_number
        if transfer_date is not UNSET:
            field_dict["transfer_date"] = transfer_date
        if order_created_date is not UNSET:
            field_dict["order_created_date"] = order_created_date
        if expected_arrival_date is not UNSET:
            field_dict["expected_arrival_date"] = expected_arrival_date
        if additional_info is not UNSET:
            field_dict["additional_info"] = additional_info

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        stock_transfer_number = d.pop("stock_transfer_number", UNSET)

        _transfer_date = d.pop("transfer_date", UNSET)
        transfer_date: datetime.datetime | Unset
        if isinstance(_transfer_date, Unset):
            transfer_date = UNSET
        else:
            transfer_date = isoparse(_transfer_date)

        _order_created_date = d.pop("order_created_date", UNSET)
        order_created_date: datetime.datetime | Unset
        if isinstance(_order_created_date, Unset):
            order_created_date = UNSET
        else:
            order_created_date = isoparse(_order_created_date)

        _expected_arrival_date = d.pop("expected_arrival_date", UNSET)
        expected_arrival_date: datetime.datetime | Unset
        if isinstance(_expected_arrival_date, Unset):
            expected_arrival_date = UNSET
        else:
            expected_arrival_date = isoparse(_expected_arrival_date)

        additional_info = d.pop("additional_info", UNSET)

        update_stock_transfer_body = cls(
            stock_transfer_number=stock_transfer_number,
            transfer_date=transfer_date,
            order_created_date=order_created_date,
            expected_arrival_date=expected_arrival_date,
            additional_info=additional_info,
        )

        return update_stock_transfer_body
