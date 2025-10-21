import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset
from ..models.update_stock_adjustment_request_status import (
    UpdateStockAdjustmentRequestStatus,
)

T = TypeVar("T", bound="UpdateStockAdjustmentRequest")


@_attrs_define
class UpdateStockAdjustmentRequest:
    """Request payload for updating an existing stock adjustment

    Example:
        {'reference_no': 'SA-2024-003', 'location_id': 1, 'adjustment_date': '2024-01-17T14:30:00.000Z',
            'additional_info': 'Cycle count correction - updated', 'status': 'COMPLETED'}
    """

    reference_no: Unset | str = UNSET
    location_id: Unset | int = UNSET
    adjustment_date: Unset | datetime.datetime = UNSET
    additional_info: Unset | str = UNSET
    status: Unset | UpdateStockAdjustmentRequestStatus = UNSET

    def to_dict(self) -> dict[str, Any]:
        reference_no = self.reference_no

        location_id = self.location_id

        adjustment_date: Unset | str = UNSET
        if not isinstance(self.adjustment_date, Unset):
            adjustment_date = self.adjustment_date.isoformat()

        additional_info = self.additional_info

        status: Unset | str = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if reference_no is not UNSET:
            field_dict["reference_no"] = reference_no
        if location_id is not UNSET:
            field_dict["location_id"] = location_id
        if adjustment_date is not UNSET:
            field_dict["adjustment_date"] = adjustment_date
        if additional_info is not UNSET:
            field_dict["additional_info"] = additional_info
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        reference_no = d.pop("reference_no", UNSET)

        location_id = d.pop("location_id", UNSET)

        _adjustment_date = d.pop("adjustment_date", UNSET)
        adjustment_date: Unset | datetime.datetime
        if isinstance(_adjustment_date, Unset):
            adjustment_date = UNSET
        else:
            adjustment_date = isoparse(_adjustment_date)

        additional_info = d.pop("additional_info", UNSET)

        _status = d.pop("status", UNSET)
        status: Unset | UpdateStockAdjustmentRequestStatus
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = UpdateStockAdjustmentRequestStatus(_status)

        update_stock_adjustment_request = cls(
            reference_no=reference_no,
            location_id=location_id,
            adjustment_date=adjustment_date,
            additional_info=additional_info,
            status=status,
        )

        return update_stock_adjustment_request
