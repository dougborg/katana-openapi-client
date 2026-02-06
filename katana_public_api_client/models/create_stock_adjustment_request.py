from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.create_stock_adjustment_request_stock_adjustment_rows_item import (
        CreateStockAdjustmentRequestStockAdjustmentRowsItem,
    )


T = TypeVar("T", bound="CreateStockAdjustmentRequest")


@_attrs_define
class CreateStockAdjustmentRequest:
    """Request payload for creating a new stock adjustment to correct inventory levels

    Example:
        {'stock_adjustment_number': 'SA-2024-003', 'stock_adjustment_date': '2024-01-17T14:30:00.000Z', 'location_id':
            1, 'reason': 'Cycle count correction', 'additional_info': 'Q1 2024 physical inventory', 'stock_adjustment_rows':
            [{'variant_id': 501, 'quantity': 100, 'cost_per_unit': 123.45}, {'variant_id': 502, 'quantity': -25,
            'cost_per_unit': 234.56}]}
    """

    location_id: int
    stock_adjustment_rows: list[CreateStockAdjustmentRequestStockAdjustmentRowsItem]
    stock_adjustment_number: str | Unset = UNSET
    stock_adjustment_date: datetime.datetime | Unset = UNSET
    reason: str | Unset = UNSET
    additional_info: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        location_id = self.location_id

        stock_adjustment_rows = []
        for stock_adjustment_rows_item_data in self.stock_adjustment_rows:
            stock_adjustment_rows_item = stock_adjustment_rows_item_data.to_dict()
            stock_adjustment_rows.append(stock_adjustment_rows_item)

        stock_adjustment_number = self.stock_adjustment_number

        stock_adjustment_date: str | Unset = UNSET
        if not isinstance(self.stock_adjustment_date, Unset):
            stock_adjustment_date = self.stock_adjustment_date.isoformat()

        reason = self.reason

        additional_info = self.additional_info

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "location_id": location_id,
                "stock_adjustment_rows": stock_adjustment_rows,
            }
        )
        if stock_adjustment_number is not UNSET:
            field_dict["stock_adjustment_number"] = stock_adjustment_number
        if stock_adjustment_date is not UNSET:
            field_dict["stock_adjustment_date"] = stock_adjustment_date
        if reason is not UNSET:
            field_dict["reason"] = reason
        if additional_info is not UNSET:
            field_dict["additional_info"] = additional_info

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.create_stock_adjustment_request_stock_adjustment_rows_item import (
            CreateStockAdjustmentRequestStockAdjustmentRowsItem,
        )

        d = dict(src_dict)
        location_id = d.pop("location_id")

        stock_adjustment_rows = []
        _stock_adjustment_rows = d.pop("stock_adjustment_rows")
        for stock_adjustment_rows_item_data in _stock_adjustment_rows:
            stock_adjustment_rows_item = (
                CreateStockAdjustmentRequestStockAdjustmentRowsItem.from_dict(
                    stock_adjustment_rows_item_data
                )
            )

            stock_adjustment_rows.append(stock_adjustment_rows_item)

        stock_adjustment_number = d.pop("stock_adjustment_number", UNSET)

        _stock_adjustment_date = d.pop("stock_adjustment_date", UNSET)
        stock_adjustment_date: datetime.datetime | Unset
        if isinstance(_stock_adjustment_date, Unset):
            stock_adjustment_date = UNSET
        else:
            stock_adjustment_date = isoparse(_stock_adjustment_date)

        reason = d.pop("reason", UNSET)

        additional_info = d.pop("additional_info", UNSET)

        create_stock_adjustment_request = cls(
            location_id=location_id,
            stock_adjustment_rows=stock_adjustment_rows,
            stock_adjustment_number=stock_adjustment_number,
            stock_adjustment_date=stock_adjustment_date,
            reason=reason,
            additional_info=additional_info,
        )

        return create_stock_adjustment_request
