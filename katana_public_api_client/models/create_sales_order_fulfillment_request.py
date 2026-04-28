from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset
from ..models.sales_order_fulfillment_status import SalesOrderFulfillmentStatus

if TYPE_CHECKING:
    from ..models.sales_order_fulfillment_row_request import (
        SalesOrderFulfillmentRowRequest,
    )


T = TypeVar("T", bound="CreateSalesOrderFulfillmentRequest")


@_attrs_define
class CreateSalesOrderFulfillmentRequest:
    """Request payload for creating a new sales order fulfillment"""

    sales_order_id: int
    status: SalesOrderFulfillmentStatus
    sales_order_fulfillment_rows: list[SalesOrderFulfillmentRowRequest]
    picked_date: datetime.datetime | Unset = UNSET
    conversion_rate: float | Unset = UNSET
    conversion_date: datetime.datetime | Unset = UNSET
    tracking_number: str | Unset = UNSET
    tracking_url: str | Unset = UNSET
    tracking_carrier: str | Unset = UNSET
    tracking_method: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        sales_order_id = self.sales_order_id

        status = self.status.value

        sales_order_fulfillment_rows = []
        for sales_order_fulfillment_rows_item_data in self.sales_order_fulfillment_rows:
            sales_order_fulfillment_rows_item = (
                sales_order_fulfillment_rows_item_data.to_dict()
            )
            sales_order_fulfillment_rows.append(sales_order_fulfillment_rows_item)

        picked_date: str | Unset = UNSET
        if not isinstance(self.picked_date, Unset):
            picked_date = self.picked_date.isoformat()

        conversion_rate = self.conversion_rate

        conversion_date: str | Unset = UNSET
        if not isinstance(self.conversion_date, Unset):
            conversion_date = self.conversion_date.isoformat()

        tracking_number = self.tracking_number

        tracking_url = self.tracking_url

        tracking_carrier = self.tracking_carrier

        tracking_method = self.tracking_method

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "sales_order_id": sales_order_id,
                "status": status,
                "sales_order_fulfillment_rows": sales_order_fulfillment_rows,
            }
        )
        if picked_date is not UNSET:
            field_dict["picked_date"] = picked_date
        if conversion_rate is not UNSET:
            field_dict["conversion_rate"] = conversion_rate
        if conversion_date is not UNSET:
            field_dict["conversion_date"] = conversion_date
        if tracking_number is not UNSET:
            field_dict["tracking_number"] = tracking_number
        if tracking_url is not UNSET:
            field_dict["tracking_url"] = tracking_url
        if tracking_carrier is not UNSET:
            field_dict["tracking_carrier"] = tracking_carrier
        if tracking_method is not UNSET:
            field_dict["tracking_method"] = tracking_method

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.sales_order_fulfillment_row_request import (
            SalesOrderFulfillmentRowRequest,
        )

        d = dict(src_dict)
        sales_order_id = d.pop("sales_order_id")

        status = SalesOrderFulfillmentStatus(d.pop("status"))

        sales_order_fulfillment_rows = []
        _sales_order_fulfillment_rows = d.pop("sales_order_fulfillment_rows")
        for sales_order_fulfillment_rows_item_data in _sales_order_fulfillment_rows:
            sales_order_fulfillment_rows_item = (
                SalesOrderFulfillmentRowRequest.from_dict(
                    sales_order_fulfillment_rows_item_data
                )
            )

            sales_order_fulfillment_rows.append(sales_order_fulfillment_rows_item)

        _picked_date = d.pop("picked_date", UNSET)
        picked_date: datetime.datetime | Unset
        if isinstance(_picked_date, Unset):
            picked_date = UNSET
        else:
            picked_date = isoparse(_picked_date)

        conversion_rate = d.pop("conversion_rate", UNSET)

        _conversion_date = d.pop("conversion_date", UNSET)
        conversion_date: datetime.datetime | Unset
        if isinstance(_conversion_date, Unset):
            conversion_date = UNSET
        else:
            conversion_date = isoparse(_conversion_date)

        tracking_number = d.pop("tracking_number", UNSET)

        tracking_url = d.pop("tracking_url", UNSET)

        tracking_carrier = d.pop("tracking_carrier", UNSET)

        tracking_method = d.pop("tracking_method", UNSET)

        create_sales_order_fulfillment_request = cls(
            sales_order_id=sales_order_id,
            status=status,
            sales_order_fulfillment_rows=sales_order_fulfillment_rows,
            picked_date=picked_date,
            conversion_rate=conversion_rate,
            conversion_date=conversion_date,
            tracking_number=tracking_number,
            tracking_url=tracking_url,
            tracking_carrier=tracking_carrier,
            tracking_method=tracking_method,
        )

        return create_sales_order_fulfillment_request
