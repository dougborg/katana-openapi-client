import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset
from ..models.update_sales_return_request_status import UpdateSalesReturnRequestStatus

T = TypeVar("T", bound="UpdateSalesReturnRequest")


@_attrs_define
class UpdateSalesReturnRequest:
    """Request payload for updating an existing sales return

    Example:
        {'customer_id': 1001, 'sales_order_id': 2001, 'order_no': 'SR-2023-001', 'return_location_id': 1, 'currency':
            'USD', 'order_created_date': '2023-10-10T10:00:00Z', 'additional_info': 'Customer reported damaged items during
            shipping', 'status': 'RETURNED'}

    Attributes:
        customer_id (Union[Unset, int]): ID of the customer initiating the return
        sales_order_id (Union[Unset, int]): ID of the original sales order being returned
        order_no (Union[Unset, str]): Return order reference number
        return_location_id (Union[Unset, int]): ID of the location where items are being returned to
        currency (Union[Unset, str]): Currency code (e.g., USD, EUR)
        order_created_date (Union[Unset, datetime.datetime]): Date when the original order was created
        additional_info (Union[Unset, str]): Optional notes or comments about the return
        status (Union[Unset, UpdateSalesReturnRequestStatus]): Status of the sales return
    """

    customer_id: Unset | int = UNSET
    sales_order_id: Unset | int = UNSET
    order_no: Unset | str = UNSET
    return_location_id: Unset | int = UNSET
    currency: Unset | str = UNSET
    order_created_date: Unset | datetime.datetime = UNSET
    additional_info: Unset | str = UNSET
    status: Unset | UpdateSalesReturnRequestStatus = UNSET

    def to_dict(self) -> dict[str, Any]:
        customer_id = self.customer_id

        sales_order_id = self.sales_order_id

        order_no = self.order_no

        return_location_id = self.return_location_id

        currency = self.currency

        order_created_date: Unset | str = UNSET
        if not isinstance(self.order_created_date, Unset):
            order_created_date = self.order_created_date.isoformat()

        additional_info = self.additional_info

        status: Unset | str = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if customer_id is not UNSET:
            field_dict["customer_id"] = customer_id
        if sales_order_id is not UNSET:
            field_dict["sales_order_id"] = sales_order_id
        if order_no is not UNSET:
            field_dict["order_no"] = order_no
        if return_location_id is not UNSET:
            field_dict["return_location_id"] = return_location_id
        if currency is not UNSET:
            field_dict["currency"] = currency
        if order_created_date is not UNSET:
            field_dict["order_created_date"] = order_created_date
        if additional_info is not UNSET:
            field_dict["additional_info"] = additional_info
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        customer_id = d.pop("customer_id", UNSET)

        sales_order_id = d.pop("sales_order_id", UNSET)

        order_no = d.pop("order_no", UNSET)

        return_location_id = d.pop("return_location_id", UNSET)

        currency = d.pop("currency", UNSET)

        _order_created_date = d.pop("order_created_date", UNSET)
        order_created_date: Unset | datetime.datetime
        if isinstance(_order_created_date, Unset):
            order_created_date = UNSET
        else:
            order_created_date = isoparse(_order_created_date)

        additional_info = d.pop("additional_info", UNSET)

        _status = d.pop("status", UNSET)
        status: Unset | UpdateSalesReturnRequestStatus
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = UpdateSalesReturnRequestStatus(_status)

        update_sales_return_request = cls(
            customer_id=customer_id,
            sales_order_id=sales_order_id,
            order_no=order_no,
            return_location_id=return_location_id,
            currency=currency,
            order_created_date=order_created_date,
            additional_info=additional_info,
            status=status,
        )

        return update_sales_return_request
