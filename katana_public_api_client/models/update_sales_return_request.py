from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset
from ..models.update_sales_return_request_status import UpdateSalesReturnRequestStatus

T = TypeVar("T", bound="UpdateSalesReturnRequest")


@_attrs_define
class UpdateSalesReturnRequest:
    """Request payload for updating an existing sales return

    Example:
        {'status': 'RETURNED_ALL', 'return_date': '2023-10-12T10:00:00Z', 'order_no': 'SR-2023-001',
            'return_location_id': 1, 'additional_info': 'Customer reported damaged items during shipping'}
    """

    status: UpdateSalesReturnRequestStatus | Unset = UNSET
    return_date: datetime.datetime | Unset = UNSET
    order_created_date: datetime.datetime | Unset = UNSET
    return_location_id: int | Unset = UNSET
    order_no: str | Unset = UNSET
    additional_info: None | str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        return_date: str | Unset = UNSET
        if not isinstance(self.return_date, Unset):
            return_date = self.return_date.isoformat()

        order_created_date: str | Unset = UNSET
        if not isinstance(self.order_created_date, Unset):
            order_created_date = self.order_created_date.isoformat()

        return_location_id = self.return_location_id

        order_no = self.order_no

        additional_info: None | str | Unset
        if isinstance(self.additional_info, Unset):
            additional_info = UNSET
        else:
            additional_info = self.additional_info

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if status is not UNSET:
            field_dict["status"] = status
        if return_date is not UNSET:
            field_dict["return_date"] = return_date
        if order_created_date is not UNSET:
            field_dict["order_created_date"] = order_created_date
        if return_location_id is not UNSET:
            field_dict["return_location_id"] = return_location_id
        if order_no is not UNSET:
            field_dict["order_no"] = order_no
        if additional_info is not UNSET:
            field_dict["additional_info"] = additional_info

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _status = d.pop("status", UNSET)
        status: UpdateSalesReturnRequestStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = UpdateSalesReturnRequestStatus(_status)

        _return_date = d.pop("return_date", UNSET)
        return_date: datetime.datetime | Unset
        if isinstance(_return_date, Unset):
            return_date = UNSET
        else:
            return_date = isoparse(_return_date)

        _order_created_date = d.pop("order_created_date", UNSET)
        order_created_date: datetime.datetime | Unset
        if isinstance(_order_created_date, Unset):
            order_created_date = UNSET
        else:
            order_created_date = isoparse(_order_created_date)

        return_location_id = d.pop("return_location_id", UNSET)

        order_no = d.pop("order_no", UNSET)

        def _parse_additional_info(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        additional_info = _parse_additional_info(d.pop("additional_info", UNSET))

        update_sales_return_request = cls(
            status=status,
            return_date=return_date,
            order_created_date=order_created_date,
            return_location_id=return_location_id,
            order_no=order_no,
            additional_info=additional_info,
        )

        return update_sales_return_request
