from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset
from ..models.update_stock_adjustment_request_status import (
    UpdateStockAdjustmentRequestStatus,
)

if TYPE_CHECKING:
    from ..models.update_stock_adjustment_request_stock_adjustment_rows_item import (
        UpdateStockAdjustmentRequestStockAdjustmentRowsItem,
    )


T = TypeVar("T", bound="UpdateStockAdjustmentRequest")


@_attrs_define
class UpdateStockAdjustmentRequest:
    """Request payload for updating an existing stock adjustment

    Example:
        {'reference_no': 'SA-2024-003', 'location_id': 1, 'adjustment_date': '2024-01-17T14:30:00.000Z', 'reason':
            'Cycle count correction', 'additional_info': 'Cycle count correction - updated with final counts', 'status':
            'COMPLETED', 'stock_adjustment_rows': [{'variant_id': 501, 'quantity': 95, 'cost_per_unit': 123.45}]}
    """

    reference_no: str | Unset = UNSET
    location_id: int | Unset = UNSET
    adjustment_date: datetime.datetime | Unset = UNSET
    reason: str | Unset = UNSET
    additional_info: str | Unset = UNSET
    status: UpdateStockAdjustmentRequestStatus | Unset = UNSET
    stock_adjustment_rows: (
        list[UpdateStockAdjustmentRequestStockAdjustmentRowsItem] | Unset
    ) = UNSET

    def to_dict(self) -> dict[str, Any]:
        reference_no = self.reference_no

        location_id = self.location_id

        adjustment_date: str | Unset = UNSET
        if not isinstance(self.adjustment_date, Unset):
            adjustment_date = self.adjustment_date.isoformat()

        reason = self.reason

        additional_info = self.additional_info

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        stock_adjustment_rows: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.stock_adjustment_rows, Unset):
            stock_adjustment_rows = []
            for stock_adjustment_rows_item_data in self.stock_adjustment_rows:
                stock_adjustment_rows_item = stock_adjustment_rows_item_data.to_dict()
                stock_adjustment_rows.append(stock_adjustment_rows_item)

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if reference_no is not UNSET:
            field_dict["reference_no"] = reference_no
        if location_id is not UNSET:
            field_dict["location_id"] = location_id
        if adjustment_date is not UNSET:
            field_dict["adjustment_date"] = adjustment_date
        if reason is not UNSET:
            field_dict["reason"] = reason
        if additional_info is not UNSET:
            field_dict["additional_info"] = additional_info
        if status is not UNSET:
            field_dict["status"] = status
        if stock_adjustment_rows is not UNSET:
            field_dict["stock_adjustment_rows"] = stock_adjustment_rows

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.update_stock_adjustment_request_stock_adjustment_rows_item import (
            UpdateStockAdjustmentRequestStockAdjustmentRowsItem,
        )

        d = dict(src_dict)
        reference_no = d.pop("reference_no", UNSET)

        location_id = d.pop("location_id", UNSET)

        _adjustment_date = d.pop("adjustment_date", UNSET)
        adjustment_date: datetime.datetime | Unset
        if isinstance(_adjustment_date, Unset):
            adjustment_date = UNSET
        else:
            adjustment_date = isoparse(_adjustment_date)

        reason = d.pop("reason", UNSET)

        additional_info = d.pop("additional_info", UNSET)

        _status = d.pop("status", UNSET)
        status: UpdateStockAdjustmentRequestStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = UpdateStockAdjustmentRequestStatus(_status)

        _stock_adjustment_rows = d.pop("stock_adjustment_rows", UNSET)
        stock_adjustment_rows: (
            list[UpdateStockAdjustmentRequestStockAdjustmentRowsItem] | Unset
        ) = UNSET
        if _stock_adjustment_rows is not UNSET:
            stock_adjustment_rows = []
            for stock_adjustment_rows_item_data in _stock_adjustment_rows:
                stock_adjustment_rows_item = (
                    UpdateStockAdjustmentRequestStockAdjustmentRowsItem.from_dict(
                        stock_adjustment_rows_item_data
                    )
                )

                stock_adjustment_rows.append(stock_adjustment_rows_item)

        update_stock_adjustment_request = cls(
            reference_no=reference_no,
            location_id=location_id,
            adjustment_date=adjustment_date,
            reason=reason,
            additional_info=additional_info,
            status=status,
            stock_adjustment_rows=stock_adjustment_rows,
        )

        return update_stock_adjustment_request
