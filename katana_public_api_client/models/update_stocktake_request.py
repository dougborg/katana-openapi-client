from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset
from ..models.stocktake_status import StocktakeStatus

T = TypeVar("T", bound="UpdateStocktakeRequest")


@_attrs_define
class UpdateStocktakeRequest:
    """Request payload for updating an existing stocktake

    Example:
        {'stocktake_number': 'STK-2024-003', 'location_id': 1, 'reason': 'Quarterly inventory count - updated',
            'status': 'IN_PROGRESS'}
    """

    stocktake_number: str | Unset = UNSET
    location_id: int | Unset = UNSET
    reason: str | Unset = UNSET
    status: StocktakeStatus | Unset = UNSET
    additional_info: str | Unset = UNSET
    created_date: datetime.datetime | Unset = UNSET
    completed_date: datetime.datetime | Unset = UNSET
    set_remaining_items_as_counted: bool | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        stocktake_number = self.stocktake_number

        location_id = self.location_id

        reason = self.reason

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        additional_info = self.additional_info

        created_date: str | Unset = UNSET
        if not isinstance(self.created_date, Unset):
            created_date = self.created_date.isoformat()

        completed_date: str | Unset = UNSET
        if not isinstance(self.completed_date, Unset):
            completed_date = self.completed_date.isoformat()

        set_remaining_items_as_counted = self.set_remaining_items_as_counted

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if stocktake_number is not UNSET:
            field_dict["stocktake_number"] = stocktake_number
        if location_id is not UNSET:
            field_dict["location_id"] = location_id
        if reason is not UNSET:
            field_dict["reason"] = reason
        if status is not UNSET:
            field_dict["status"] = status
        if additional_info is not UNSET:
            field_dict["additional_info"] = additional_info
        if created_date is not UNSET:
            field_dict["created_date"] = created_date
        if completed_date is not UNSET:
            field_dict["completed_date"] = completed_date
        if set_remaining_items_as_counted is not UNSET:
            field_dict["set_remaining_items_as_counted"] = (
                set_remaining_items_as_counted
            )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        stocktake_number = d.pop("stocktake_number", UNSET)

        location_id = d.pop("location_id", UNSET)

        reason = d.pop("reason", UNSET)

        _status = d.pop("status", UNSET)
        status: StocktakeStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = StocktakeStatus(_status)

        additional_info = d.pop("additional_info", UNSET)

        _created_date = d.pop("created_date", UNSET)
        created_date: datetime.datetime | Unset
        if isinstance(_created_date, Unset):
            created_date = UNSET
        else:
            created_date = isoparse(_created_date)

        _completed_date = d.pop("completed_date", UNSET)
        completed_date: datetime.datetime | Unset
        if isinstance(_completed_date, Unset):
            completed_date = UNSET
        else:
            completed_date = isoparse(_completed_date)

        set_remaining_items_as_counted = d.pop("set_remaining_items_as_counted", UNSET)

        update_stocktake_request = cls(
            stocktake_number=stocktake_number,
            location_id=location_id,
            reason=reason,
            status=status,
            additional_info=additional_info,
            created_date=created_date,
            completed_date=completed_date,
            set_remaining_items_as_counted=set_remaining_items_as_counted,
        )

        return update_stocktake_request
