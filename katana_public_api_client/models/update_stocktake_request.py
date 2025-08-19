import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset
from ..models.update_stocktake_request_status import UpdateStocktakeRequestStatus

T = TypeVar("T", bound="UpdateStocktakeRequest")


@_attrs_define
class UpdateStocktakeRequest:
    """Request payload for updating an existing stocktake

    Example:
        {'reference_no': 'STK-2024-003', 'location_id': 1, 'stocktake_date': '2024-01-17T09:00:00.000Z', 'notes':
            'Quarterly inventory count - updated', 'status': 'IN_PROGRESS'}
    """

    reference_no: Unset | str = UNSET
    location_id: Unset | int = UNSET
    stocktake_date: Unset | datetime.datetime = UNSET
    notes: Unset | str = UNSET
    status: Unset | UpdateStocktakeRequestStatus = UNSET

    def to_dict(self) -> dict[str, Any]:
        reference_no = self.reference_no

        location_id = self.location_id

        stocktake_date: Unset | str = UNSET
        if not isinstance(self.stocktake_date, Unset):
            stocktake_date = self.stocktake_date.isoformat()

        notes = self.notes

        status: Unset | str = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if reference_no is not UNSET:
            field_dict["reference_no"] = reference_no
        if location_id is not UNSET:
            field_dict["location_id"] = location_id
        if stocktake_date is not UNSET:
            field_dict["stocktake_date"] = stocktake_date
        if notes is not UNSET:
            field_dict["notes"] = notes
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        reference_no = d.pop("reference_no", UNSET)

        location_id = d.pop("location_id", UNSET)

        _stocktake_date = d.pop("stocktake_date", UNSET)
        stocktake_date: Unset | datetime.datetime
        if isinstance(_stocktake_date, Unset):
            stocktake_date = UNSET
        else:
            stocktake_date = isoparse(_stocktake_date)

        notes = d.pop("notes", UNSET)

        _status = d.pop("status", UNSET)
        status: Unset | UpdateStocktakeRequestStatus
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = UpdateStocktakeRequestStatus(_status)

        update_stocktake_request = cls(
            reference_no=reference_no,
            location_id=location_id,
            stocktake_date=stocktake_date,
            notes=notes,
            status=status,
        )

        return update_stocktake_request
