import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset
from ..models.create_stock_adjustment_request_status import (
    CreateStockAdjustmentRequestStatus,
)

if TYPE_CHECKING:
    from ..models.create_stock_adjustment_request_stock_adjustment_rows_item import (
        CreateStockAdjustmentRequestStockAdjustmentRowsItem,
    )


T = TypeVar("T", bound="CreateStockAdjustmentRequest")


@_attrs_define
class CreateStockAdjustmentRequest:
    """Request payload for creating a new stock adjustment to correct inventory levels

    Example:
        {'reference_no': 'SA-2024-003', 'location_id': 1, 'adjustment_date': '2024-01-17T14:30:00.000Z', 'reason':
            'Cycle count correction', 'additional_info': 'Q1 2024 physical inventory', 'status': 'DRAFT',
            'stock_adjustment_rows': [{'variant_id': 501, 'quantity': 100, 'cost_per_unit': 123.45}, {'variant_id': 502,
            'quantity': -25, 'cost_per_unit': 234.56}]}
    """

    reference_no: str
    location_id: int
    adjustment_date: datetime.datetime
    stock_adjustment_rows: list["CreateStockAdjustmentRequestStockAdjustmentRowsItem"]
    reason: Unset | str = UNSET
    additional_info: Unset | str = UNSET
    status: Unset | CreateStockAdjustmentRequestStatus = (
        CreateStockAdjustmentRequestStatus.DRAFT
    )

    def to_dict(self) -> dict[str, Any]:
        reference_no = self.reference_no

        location_id = self.location_id

        adjustment_date = self.adjustment_date.isoformat()

        stock_adjustment_rows = []
        for stock_adjustment_rows_item_data in self.stock_adjustment_rows:
            stock_adjustment_rows_item = stock_adjustment_rows_item_data.to_dict()
            stock_adjustment_rows.append(stock_adjustment_rows_item)

        reason = self.reason

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
                "stock_adjustment_rows": stock_adjustment_rows,
            }
        )
        if reason is not UNSET:
            field_dict["reason"] = reason
        if additional_info is not UNSET:
            field_dict["additional_info"] = additional_info
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:  # type: ignore[misc]
        from ..models.create_stock_adjustment_request_stock_adjustment_rows_item import (
            CreateStockAdjustmentRequestStockAdjustmentRowsItem,
        )

        d = dict(src_dict)
        reference_no = d.pop("reference_no")

        location_id = d.pop("location_id")

        adjustment_date = isoparse(d.pop("adjustment_date"))

        stock_adjustment_rows = []
        _stock_adjustment_rows = d.pop("stock_adjustment_rows")
        for stock_adjustment_rows_item_data in _stock_adjustment_rows:
            stock_adjustment_rows_item = (
                CreateStockAdjustmentRequestStockAdjustmentRowsItem.from_dict(
                    stock_adjustment_rows_item_data
                )
            )

            stock_adjustment_rows.append(stock_adjustment_rows_item)

        reason = d.pop("reason", UNSET)

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
            stock_adjustment_rows=stock_adjustment_rows,
            reason=reason,
            additional_info=additional_info,
            status=status,
        )

        return create_stock_adjustment_request
