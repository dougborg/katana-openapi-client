from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="UpdateStockAdjustmentRequest")


@_attrs_define
class UpdateStockAdjustmentRequest:
    """Request payload for updating an existing stock adjustment

    Example:
        {'stock_adjustment_number': 'SA-2024-003', 'stock_adjustment_date': '2024-01-17T14:30:00.000Z', 'location_id':
            1, 'reason': 'Cycle count correction', 'additional_info': 'Cycle count correction - updated with final counts'}
    """

    stock_adjustment_number: str | Unset = UNSET
    stock_adjustment_date: datetime.datetime | Unset = UNSET
    location_id: int | Unset = UNSET
    reason: str | Unset = UNSET
    additional_info: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        stock_adjustment_number = self.stock_adjustment_number

        stock_adjustment_date: str | Unset = UNSET
        if not isinstance(self.stock_adjustment_date, Unset):
            stock_adjustment_date = self.stock_adjustment_date.isoformat()

        location_id = self.location_id

        reason = self.reason

        additional_info = self.additional_info

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if stock_adjustment_number is not UNSET:
            field_dict["stock_adjustment_number"] = stock_adjustment_number
        if stock_adjustment_date is not UNSET:
            field_dict["stock_adjustment_date"] = stock_adjustment_date
        if location_id is not UNSET:
            field_dict["location_id"] = location_id
        if reason is not UNSET:
            field_dict["reason"] = reason
        if additional_info is not UNSET:
            field_dict["additional_info"] = additional_info

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        stock_adjustment_number = d.pop("stock_adjustment_number", UNSET)

        _stock_adjustment_date = d.pop("stock_adjustment_date", UNSET)
        stock_adjustment_date: datetime.datetime | Unset
        if isinstance(_stock_adjustment_date, Unset):
            stock_adjustment_date = UNSET
        else:
            stock_adjustment_date = isoparse(_stock_adjustment_date)

        location_id = d.pop("location_id", UNSET)

        reason = d.pop("reason", UNSET)

        additional_info = d.pop("additional_info", UNSET)

        update_stock_adjustment_request = cls(
            stock_adjustment_number=stock_adjustment_number,
            stock_adjustment_date=stock_adjustment_date,
            location_id=location_id,
            reason=reason,
            additional_info=additional_info,
        )

        return update_stock_adjustment_request
