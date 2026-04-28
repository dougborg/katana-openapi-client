from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

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
    tracking_number: None | str | Unset = UNSET
    tracking_number_url: None | str | Unset = UNSET
    tracking_carrier: None | str | Unset = UNSET
    tracking_method: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        sales_order_id = self.sales_order_id

        return_location_id = self.return_location_id

        order_created_date: str | Unset = UNSET
        if not isinstance(self.order_created_date, Unset):
            order_created_date = self.order_created_date.isoformat()

        order_no = self.order_no

        additional_info = self.additional_info

        tracking_number: None | str | Unset
        if isinstance(self.tracking_number, Unset):
            tracking_number = UNSET
        else:
            tracking_number = self.tracking_number

        tracking_number_url: None | str | Unset
        if isinstance(self.tracking_number_url, Unset):
            tracking_number_url = UNSET
        else:
            tracking_number_url = self.tracking_number_url

        tracking_carrier: None | str | Unset
        if isinstance(self.tracking_carrier, Unset):
            tracking_carrier = UNSET
        else:
            tracking_carrier = self.tracking_carrier

        tracking_method: None | str | Unset
        if isinstance(self.tracking_method, Unset):
            tracking_method = UNSET
        else:
            tracking_method = self.tracking_method

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
        if tracking_number is not UNSET:
            field_dict["tracking_number"] = tracking_number
        if tracking_number_url is not UNSET:
            field_dict["tracking_number_url"] = tracking_number_url
        if tracking_carrier is not UNSET:
            field_dict["tracking_carrier"] = tracking_carrier
        if tracking_method is not UNSET:
            field_dict["tracking_method"] = tracking_method

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

        def _parse_tracking_number(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        tracking_number = _parse_tracking_number(d.pop("tracking_number", UNSET))

        def _parse_tracking_number_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        tracking_number_url = _parse_tracking_number_url(
            d.pop("tracking_number_url", UNSET)
        )

        def _parse_tracking_carrier(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        tracking_carrier = _parse_tracking_carrier(d.pop("tracking_carrier", UNSET))

        def _parse_tracking_method(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        tracking_method = _parse_tracking_method(d.pop("tracking_method", UNSET))

        create_sales_return_request = cls(
            sales_order_id=sales_order_id,
            return_location_id=return_location_id,
            order_created_date=order_created_date,
            order_no=order_no,
            additional_info=additional_info,
            tracking_number=tracking_number,
            tracking_number_url=tracking_number_url,
            tracking_carrier=tracking_carrier,
            tracking_method=tracking_method,
        )

        return create_sales_return_request
