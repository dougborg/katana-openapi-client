import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset
from ..models.create_stock_adjustment_request_status import (
    CreateStockAdjustmentRequestStatus,
)

T = TypeVar("T", bound="CreateStockAdjustmentRequest")


@_attrs_define
class CreateStockAdjustmentRequest:
    """Request payload for creating a new stock adjustment to correct inventory levels

    Example:
        {'reference_no': 'SA-2024-003', 'location_id': 1, 'adjustment_date': '2024-01-17T14:30:00.000Z',
            'additional_info': 'Cycle count correction', 'status': 'DRAFT'}
    """

    reference_no: str
    location_id: int
    adjustment_date: datetime.datetime
    additional_info: Unset | str = UNSET
    status: Unset | CreateStockAdjustmentRequestStatus = (
        CreateStockAdjustmentRequestStatus.DRAFT
    )

    def to_dict(self) -> dict[str, Any]:
        reference_no = self.reference_no

        location_id = self.location_id

        adjustment_date = self.adjustment_date.isoformat()

        additional_info = self.additional_info

        status: Unset | str = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "reference_no": reference_no,
                "location_id": location_id,
                "adjustment_date": adjustment_date,
            }
        )
        if additional_info is not UNSET:
            field_dict["additional_info"] = additional_info
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        reference_no = d.pop("reference_no")

        location_id = d.pop("location_id")

        adjustment_date = isoparse(d.pop("adjustment_date"))

        additional_info = d.pop("additional_info", UNSET)

        _status = d.pop("status", UNSET)
        status: Unset | CreateStockAdjustmentRequestStatus
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = CreateStockAdjustmentRequestStatus(_status)

        create_stock_adjustment_request = cls(
            reference_no=reference_no,
            location_id=location_id,
            adjustment_date=adjustment_date,
            additional_info=additional_info,
            status=status,
        )

        return create_stock_adjustment_request
