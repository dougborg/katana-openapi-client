from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.create_stocktake_request_stocktake_rows_item import (
        CreateStocktakeRequestStocktakeRowsItem,
    )


T = TypeVar("T", bound="CreateStocktakeRequest")


@_attrs_define
class CreateStocktakeRequest:
    """Request payload for creating a new stocktake to perform physical inventory counting

    Example:
        {'stocktake_number': 'STK-2024-003', 'location_id': 1, 'reason': 'Quarterly inventory count', 'additional_info':
            'Annual audit'}
    """

    stocktake_number: str
    location_id: int
    reason: str | Unset = UNSET
    additional_info: str | Unset = UNSET
    created_date: datetime.datetime | Unset = UNSET
    set_remaining_items_as_counted: bool | Unset = UNSET
    stocktake_rows: list[CreateStocktakeRequestStocktakeRowsItem] | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        stocktake_number = self.stocktake_number

        location_id = self.location_id

        reason = self.reason

        additional_info = self.additional_info

        created_date: str | Unset = UNSET
        if not isinstance(self.created_date, Unset):
            created_date = self.created_date.isoformat()

        set_remaining_items_as_counted = self.set_remaining_items_as_counted

        stocktake_rows: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.stocktake_rows, Unset):
            stocktake_rows = []
            for stocktake_rows_item_data in self.stocktake_rows:
                stocktake_rows_item = stocktake_rows_item_data.to_dict()
                stocktake_rows.append(stocktake_rows_item)

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "stocktake_number": stocktake_number,
                "location_id": location_id,
            }
        )
        if reason is not UNSET:
            field_dict["reason"] = reason
        if additional_info is not UNSET:
            field_dict["additional_info"] = additional_info
        if created_date is not UNSET:
            field_dict["created_date"] = created_date
        if set_remaining_items_as_counted is not UNSET:
            field_dict["set_remaining_items_as_counted"] = (
                set_remaining_items_as_counted
            )
        if stocktake_rows is not UNSET:
            field_dict["stocktake_rows"] = stocktake_rows

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.create_stocktake_request_stocktake_rows_item import (
            CreateStocktakeRequestStocktakeRowsItem,
        )

        d = dict(src_dict)
        stocktake_number = d.pop("stocktake_number")

        location_id = d.pop("location_id")

        reason = d.pop("reason", UNSET)

        additional_info = d.pop("additional_info", UNSET)

        _created_date = d.pop("created_date", UNSET)
        created_date: datetime.datetime | Unset
        if isinstance(_created_date, Unset):
            created_date = UNSET
        else:
            created_date = isoparse(_created_date)

        set_remaining_items_as_counted = d.pop("set_remaining_items_as_counted", UNSET)

        _stocktake_rows = d.pop("stocktake_rows", UNSET)
        stocktake_rows: list[CreateStocktakeRequestStocktakeRowsItem] | Unset = UNSET
        if _stocktake_rows is not UNSET:
            stocktake_rows = []
            for stocktake_rows_item_data in _stocktake_rows:
                stocktake_rows_item = CreateStocktakeRequestStocktakeRowsItem.from_dict(
                    stocktake_rows_item_data
                )

                stocktake_rows.append(stocktake_rows_item)

        create_stocktake_request = cls(
            stocktake_number=stocktake_number,
            location_id=location_id,
            reason=reason,
            additional_info=additional_info,
            created_date=created_date,
            set_remaining_items_as_counted=set_remaining_items_as_counted,
            stocktake_rows=stocktake_rows,
        )

        return create_stocktake_request
