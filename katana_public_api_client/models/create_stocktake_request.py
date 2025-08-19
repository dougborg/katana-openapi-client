import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset
from ..models.create_stocktake_request_status import CreateStocktakeRequestStatus

T = TypeVar("T", bound="CreateStocktakeRequest")


@_attrs_define
class CreateStocktakeRequest:
    """Request payload for creating a new stocktake to perform physical inventory counting

    Example:
        {'reference_no': 'STK-2024-003', 'location_id': 1, 'stocktake_date': '2024-01-17T09:00:00.000Z', 'notes':
            'Quarterly inventory count', 'status': 'DRAFT'}
    """

    reference_no: str
    location_id: int
    stocktake_date: datetime.datetime
    notes: Unset | str = UNSET
    status: Unset | CreateStocktakeRequestStatus = CreateStocktakeRequestStatus.DRAFT

    def to_dict(self) -> dict[str, Any]:
        reference_no = self.reference_no

        location_id = self.location_id

        stocktake_date = self.stocktake_date.isoformat()

        notes = self.notes

        status: Unset | str = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "reference_no": reference_no,
                "location_id": location_id,
                "stocktake_date": stocktake_date,
            }
        )
        if notes is not UNSET:
            field_dict["notes"] = notes
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        reference_no = d.pop("reference_no")

        location_id = d.pop("location_id")

        stocktake_date = isoparse(d.pop("stocktake_date"))

        notes = d.pop("notes", UNSET)

        _status = d.pop("status", UNSET)
        status: Unset | CreateStocktakeRequestStatus
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = CreateStocktakeRequestStatus(_status)

        create_stocktake_request = cls(
            reference_no=reference_no,
            location_id=location_id,
            stocktake_date=stocktake_date,
            notes=notes,
            status=status,
        )

        return create_stocktake_request
