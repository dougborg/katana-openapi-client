from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.create_stock_transfer_body_stock_transfer_rows_item import (
        CreateStockTransferBodyStockTransferRowsItem,
    )


T = TypeVar("T", bound="CreateStockTransferBody")


@_attrs_define
class CreateStockTransferBody:
    source_location_id: int
    target_location_id: int
    stock_transfer_number: str | Unset = UNSET
    transfer_date: datetime.datetime | Unset = UNSET
    order_created_date: datetime.datetime | Unset = UNSET
    expected_arrival_date: datetime.datetime | Unset = UNSET
    additional_info: str | Unset = UNSET
    stock_transfer_rows: list[CreateStockTransferBodyStockTransferRowsItem] | Unset = (
        UNSET
    )

    def to_dict(self) -> dict[str, Any]:
        source_location_id = self.source_location_id

        target_location_id = self.target_location_id

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

        stock_transfer_rows: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.stock_transfer_rows, Unset):
            stock_transfer_rows = []
            for stock_transfer_rows_item_data in self.stock_transfer_rows:
                stock_transfer_rows_item = stock_transfer_rows_item_data.to_dict()
                stock_transfer_rows.append(stock_transfer_rows_item)

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "source_location_id": source_location_id,
                "target_location_id": target_location_id,
            }
        )
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
        if stock_transfer_rows is not UNSET:
            field_dict["stock_transfer_rows"] = stock_transfer_rows

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.create_stock_transfer_body_stock_transfer_rows_item import (
            CreateStockTransferBodyStockTransferRowsItem,
        )

        d = dict(src_dict)
        source_location_id = d.pop("source_location_id")

        target_location_id = d.pop("target_location_id")

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

        _stock_transfer_rows = d.pop("stock_transfer_rows", UNSET)
        stock_transfer_rows: (
            list[CreateStockTransferBodyStockTransferRowsItem] | Unset
        ) = UNSET
        if _stock_transfer_rows is not UNSET:
            stock_transfer_rows = []
            for stock_transfer_rows_item_data in _stock_transfer_rows:
                stock_transfer_rows_item = (
                    CreateStockTransferBodyStockTransferRowsItem.from_dict(
                        stock_transfer_rows_item_data
                    )
                )

                stock_transfer_rows.append(stock_transfer_rows_item)

        create_stock_transfer_body = cls(
            source_location_id=source_location_id,
            target_location_id=target_location_id,
            stock_transfer_number=stock_transfer_number,
            transfer_date=transfer_date,
            order_created_date=order_created_date,
            expected_arrival_date=expected_arrival_date,
            additional_info=additional_info,
            stock_transfer_rows=stock_transfer_rows,
        )

        return create_stock_transfer_body
