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
from ..models.stocktake_status import StocktakeStatus

T = TypeVar("T", bound="Stocktake")


@_attrs_define
class Stocktake:
    """Physical inventory count process for reconciling actual stock levels with system records"""

    id: int
    stocktake_number: str
    location_id: int
    status: StocktakeStatus
    created_at: datetime.datetime | Unset = UNSET
    updated_at: datetime.datetime | Unset = UNSET
    stocktake_created_date: datetime.datetime | Unset = UNSET
    started_date: datetime.datetime | None | Unset = UNSET
    completed_date: datetime.datetime | None | Unset = UNSET
    status_update_in_progress: bool | Unset = UNSET
    set_remaining_items_as_counted: bool | Unset = UNSET
    stock_adjustment_id: int | None | Unset = UNSET
    reason: None | str | Unset = UNSET
    additional_info: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        stocktake_number = self.stocktake_number

        location_id = self.location_id

        status = self.status.value

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: str | Unset = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        stocktake_created_date: str | Unset = UNSET
        if not isinstance(self.stocktake_created_date, Unset):
            stocktake_created_date = self.stocktake_created_date.isoformat()

        started_date: None | str | Unset
        if isinstance(self.started_date, Unset):
            started_date = UNSET
        elif isinstance(self.started_date, datetime.datetime):
            started_date = self.started_date.isoformat()
        else:
            started_date = self.started_date

        completed_date: None | str | Unset
        if isinstance(self.completed_date, Unset):
            completed_date = UNSET
        elif isinstance(self.completed_date, datetime.datetime):
            completed_date = self.completed_date.isoformat()
        else:
            completed_date = self.completed_date

        status_update_in_progress = self.status_update_in_progress

        set_remaining_items_as_counted = self.set_remaining_items_as_counted

        stock_adjustment_id: int | None | Unset
        if isinstance(self.stock_adjustment_id, Unset):
            stock_adjustment_id = UNSET
        else:
            stock_adjustment_id = self.stock_adjustment_id

        reason: None | str | Unset
        if isinstance(self.reason, Unset):
            reason = UNSET
        else:
            reason = self.reason

        additional_info: None | str | Unset
        if isinstance(self.additional_info, Unset):
            additional_info = UNSET
        else:
            additional_info = self.additional_info

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "stocktake_number": stocktake_number,
                "location_id": location_id,
                "status": status,
            }
        )
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if stocktake_created_date is not UNSET:
            field_dict["stocktake_created_date"] = stocktake_created_date
        if started_date is not UNSET:
            field_dict["started_date"] = started_date
        if completed_date is not UNSET:
            field_dict["completed_date"] = completed_date
        if status_update_in_progress is not UNSET:
            field_dict["status_update_in_progress"] = status_update_in_progress
        if set_remaining_items_as_counted is not UNSET:
            field_dict["set_remaining_items_as_counted"] = (
                set_remaining_items_as_counted
            )
        if stock_adjustment_id is not UNSET:
            field_dict["stock_adjustment_id"] = stock_adjustment_id
        if reason is not UNSET:
            field_dict["reason"] = reason
        if additional_info is not UNSET:
            field_dict["additional_info"] = additional_info

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        stocktake_number = d.pop("stocktake_number")

        location_id = d.pop("location_id")

        status = StocktakeStatus(d.pop("status"))

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

        _stocktake_created_date = d.pop("stocktake_created_date", UNSET)
        stocktake_created_date: datetime.datetime | Unset
        if isinstance(_stocktake_created_date, Unset):
            stocktake_created_date = UNSET
        else:
            stocktake_created_date = isoparse(_stocktake_created_date)

        def _parse_started_date(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                started_date_type_0 = isoparse(data)

                return started_date_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        started_date = _parse_started_date(d.pop("started_date", UNSET))

        def _parse_completed_date(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                completed_date_type_0 = isoparse(data)

                return completed_date_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        completed_date = _parse_completed_date(d.pop("completed_date", UNSET))

        status_update_in_progress = d.pop("status_update_in_progress", UNSET)

        set_remaining_items_as_counted = d.pop("set_remaining_items_as_counted", UNSET)

        def _parse_stock_adjustment_id(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        stock_adjustment_id = _parse_stock_adjustment_id(
            d.pop("stock_adjustment_id", UNSET)
        )

        def _parse_reason(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        reason = _parse_reason(d.pop("reason", UNSET))

        def _parse_additional_info(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        additional_info = _parse_additional_info(d.pop("additional_info", UNSET))

        stocktake = cls(
            id=id,
            stocktake_number=stocktake_number,
            location_id=location_id,
            status=status,
            created_at=created_at,
            updated_at=updated_at,
            stocktake_created_date=stocktake_created_date,
            started_date=started_date,
            completed_date=completed_date,
            status_update_in_progress=status_update_in_progress,
            set_remaining_items_as_counted=set_remaining_items_as_counted,
            stock_adjustment_id=stock_adjustment_id,
            reason=reason,
            additional_info=additional_info,
        )

        stocktake.additional_properties = d
        return stocktake

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
