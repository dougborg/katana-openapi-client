import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset
from ..models.update_purchase_order_request_status import (
    UpdatePurchaseOrderRequestStatus,
)

T = TypeVar("T", bound="UpdatePurchaseOrderRequest")


@_attrs_define
class UpdatePurchaseOrderRequest:
    """Request payload for updating an existing purchase order's details, status, and line items

    Example:
        {'order_no': 'PO-2024-0156-REVISED', 'expected_arrival_date': '2024-02-20', 'status': 'PARTIALLY_RECEIVED',
            'additional_info': 'Delivery delayed due to weather - updated schedule'}
    """

    order_no: Unset | str = UNSET
    supplier_id: Unset | int = UNSET
    currency: Unset | str = UNSET
    tracking_location_id: Unset | int = UNSET
    status: Unset | UpdatePurchaseOrderRequestStatus = UNSET
    expected_arrival_date: Unset | str = UNSET
    order_created_date: Unset | datetime.datetime = UNSET
    location_id: Unset | int = UNSET
    additional_info: Unset | str = UNSET

    def to_dict(self) -> dict[str, Any]:
        order_no = self.order_no

        supplier_id = self.supplier_id

        currency = self.currency

        tracking_location_id = self.tracking_location_id

        status: Unset | str = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        expected_arrival_date = self.expected_arrival_date

        order_created_date: Unset | str = UNSET
        if not isinstance(self.order_created_date, Unset):
            order_created_date = self.order_created_date.isoformat()

        location_id = self.location_id

        additional_info = self.additional_info

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if order_no is not UNSET:
            field_dict["order_no"] = order_no
        if supplier_id is not UNSET:
            field_dict["supplier_id"] = supplier_id
        if currency is not UNSET:
            field_dict["currency"] = currency
        if tracking_location_id is not UNSET:
            field_dict["tracking_location_id"] = tracking_location_id
        if status is not UNSET:
            field_dict["status"] = status
        if expected_arrival_date is not UNSET:
            field_dict["expected_arrival_date"] = expected_arrival_date
        if order_created_date is not UNSET:
            field_dict["order_created_date"] = order_created_date
        if location_id is not UNSET:
            field_dict["location_id"] = location_id
        if additional_info is not UNSET:
            field_dict["additional_info"] = additional_info

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        order_no = d.pop("order_no", UNSET)

        supplier_id = d.pop("supplier_id", UNSET)

        currency = d.pop("currency", UNSET)

        tracking_location_id = d.pop("tracking_location_id", UNSET)

        _status = d.pop("status", UNSET)
        status: Unset | UpdatePurchaseOrderRequestStatus
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = UpdatePurchaseOrderRequestStatus(_status)

        expected_arrival_date = d.pop("expected_arrival_date", UNSET)

        _order_created_date = d.pop("order_created_date", UNSET)
        order_created_date: Unset | datetime.datetime
        if isinstance(_order_created_date, Unset):
            order_created_date = UNSET
        else:
            order_created_date = isoparse(_order_created_date)

        location_id = d.pop("location_id", UNSET)

        additional_info = d.pop("additional_info", UNSET)

        update_purchase_order_request = cls(
            order_no=order_no,
            supplier_id=supplier_id,
            currency=currency,
            tracking_location_id=tracking_location_id,
            status=status,
            expected_arrival_date=expected_arrival_date,
            order_created_date=order_created_date,
            location_id=location_id,
            additional_info=additional_info,
        )

        return update_purchase_order_request
