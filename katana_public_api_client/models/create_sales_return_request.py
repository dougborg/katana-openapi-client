from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="CreateSalesReturnRequest")


@_attrs_define
class CreateSalesReturnRequest:
    """Request payload for creating a new sales return to process customer product returns and refunds

    Example:
        {'sales_order_id': 2001, 'order_created_date': '2023-10-10T10:00:00Z', 'return_location_id': 1, 'order_no':
            'SR-2023-001', 'additional_info': 'Customer reported damaged items during shipping'}
    """

    sales_order_id: int
    return_location_id: int
    order_created_date: datetime.datetime | Unset = UNSET
    order_no: str | Unset = UNSET
    additional_info: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        sales_order_id = self.sales_order_id

        return_location_id = self.return_location_id

        order_created_date: str | Unset = UNSET
        if not isinstance(self.order_created_date, Unset):
            order_created_date = self.order_created_date.isoformat()

        order_no = self.order_no

        additional_info = self.additional_info

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "sales_order_id": sales_order_id,
                "return_location_id": return_location_id,
            }
        )
        if order_created_date is not UNSET:
            field_dict["order_created_date"] = order_created_date
        if order_no is not UNSET:
            field_dict["order_no"] = order_no
        if additional_info is not UNSET:
            field_dict["additional_info"] = additional_info

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        sales_order_id = d.pop("sales_order_id")

        return_location_id = d.pop("return_location_id")

        _order_created_date = d.pop("order_created_date", UNSET)
        order_created_date: datetime.datetime | Unset
        if isinstance(_order_created_date, Unset):
            order_created_date = UNSET
        else:
            order_created_date = isoparse(_order_created_date)

        order_no = d.pop("order_no", UNSET)

        additional_info = d.pop("additional_info", UNSET)

        create_sales_return_request = cls(
            sales_order_id=sales_order_id,
            return_location_id=return_location_id,
            order_created_date=order_created_date,
            order_no=order_no,
            additional_info=additional_info,
        )

        return create_sales_return_request
