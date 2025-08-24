import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset
from ..models.update_sales_order_body_status import UpdateSalesOrderBodyStatus

T = TypeVar("T", bound="UpdateSalesOrderBody")


@_attrs_define
class UpdateSalesOrderBody:
    order_no: Unset | str = UNSET
    customer_id: Unset | int = UNSET
    order_created_date: Unset | datetime.datetime = UNSET
    delivery_date: Unset | datetime.datetime = UNSET
    picked_date: Unset | datetime.datetime = UNSET
    location_id: Unset | int = UNSET
    status: Unset | UpdateSalesOrderBodyStatus = UNSET
    currency: Unset | str = UNSET
    conversion_rate: Unset | float = UNSET
    conversion_date: Unset | str = UNSET
    additional_info: None | Unset | str = UNSET
    customer_ref: None | Unset | str = UNSET
    tracking_number: None | Unset | str = UNSET
    tracking_number_url: None | Unset | str = UNSET

    def to_dict(self) -> dict[str, Any]:
        order_no = self.order_no

        customer_id = self.customer_id

        order_created_date: Unset | str = UNSET
        if not isinstance(self.order_created_date, Unset):
            order_created_date = self.order_created_date.isoformat()

        delivery_date: Unset | str = UNSET
        if not isinstance(self.delivery_date, Unset):
            delivery_date = self.delivery_date.isoformat()

        picked_date: Unset | str = UNSET
        if not isinstance(self.picked_date, Unset):
            picked_date = self.picked_date.isoformat()

        location_id = self.location_id

        status: Unset | str = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        currency = self.currency

        conversion_rate = self.conversion_rate

        conversion_date = self.conversion_date

        additional_info: None | Unset | str
        if isinstance(self.additional_info, Unset):
            additional_info = UNSET
        else:
            additional_info = self.additional_info

        customer_ref: None | Unset | str
        if isinstance(self.customer_ref, Unset):
            customer_ref = UNSET
        else:
            customer_ref = self.customer_ref

        tracking_number: None | Unset | str
        if isinstance(self.tracking_number, Unset):
            tracking_number = UNSET
        else:
            tracking_number = self.tracking_number

        tracking_number_url: None | Unset | str
        if isinstance(self.tracking_number_url, Unset):
            tracking_number_url = UNSET
        else:
            tracking_number_url = self.tracking_number_url

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if order_no is not UNSET:
            field_dict["order_no"] = order_no
        if customer_id is not UNSET:
            field_dict["customer_id"] = customer_id
        if order_created_date is not UNSET:
            field_dict["order_created_date"] = order_created_date
        if delivery_date is not UNSET:
            field_dict["delivery_date"] = delivery_date
        if picked_date is not UNSET:
            field_dict["picked_date"] = picked_date
        if location_id is not UNSET:
            field_dict["location_id"] = location_id
        if status is not UNSET:
            field_dict["status"] = status
        if currency is not UNSET:
            field_dict["currency"] = currency
        if conversion_rate is not UNSET:
            field_dict["conversion_rate"] = conversion_rate
        if conversion_date is not UNSET:
            field_dict["conversion_date"] = conversion_date
        if additional_info is not UNSET:
            field_dict["additional_info"] = additional_info
        if customer_ref is not UNSET:
            field_dict["customer_ref"] = customer_ref
        if tracking_number is not UNSET:
            field_dict["tracking_number"] = tracking_number
        if tracking_number_url is not UNSET:
            field_dict["tracking_number_url"] = tracking_number_url

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        order_no = d.pop("order_no", UNSET)

        customer_id = d.pop("customer_id", UNSET)

        _order_created_date = d.pop("order_created_date", UNSET)
        order_created_date: Unset | datetime.datetime
        if isinstance(_order_created_date, Unset):
            order_created_date = UNSET
        else:
            order_created_date = isoparse(_order_created_date)

        _delivery_date = d.pop("delivery_date", UNSET)
        delivery_date: Unset | datetime.datetime
        if isinstance(_delivery_date, Unset):
            delivery_date = UNSET
        else:
            delivery_date = isoparse(_delivery_date)

        _picked_date = d.pop("picked_date", UNSET)
        picked_date: Unset | datetime.datetime
        if isinstance(_picked_date, Unset):
            picked_date = UNSET
        else:
            picked_date = isoparse(_picked_date)

        location_id = d.pop("location_id", UNSET)

        _status = d.pop("status", UNSET)
        status: Unset | UpdateSalesOrderBodyStatus
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = UpdateSalesOrderBodyStatus(_status)

        currency = d.pop("currency", UNSET)

        conversion_rate = d.pop("conversion_rate", UNSET)

        conversion_date = d.pop("conversion_date", UNSET)

        def _parse_additional_info(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        additional_info = _parse_additional_info(d.pop("additional_info", UNSET))

        def _parse_customer_ref(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        customer_ref = _parse_customer_ref(d.pop("customer_ref", UNSET))

        def _parse_tracking_number(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        tracking_number = _parse_tracking_number(d.pop("tracking_number", UNSET))

        def _parse_tracking_number_url(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        tracking_number_url = _parse_tracking_number_url(
            d.pop("tracking_number_url", UNSET)
        )

        update_sales_order_body = cls(
            order_no=order_no,
            customer_id=customer_id,
            order_created_date=order_created_date,
            delivery_date=delivery_date,
            picked_date=picked_date,
            location_id=location_id,
            status=status,
            currency=currency,
            conversion_rate=conversion_rate,
            conversion_date=conversion_date,
            additional_info=additional_info,
            customer_ref=customer_ref,
            tracking_number=tracking_number,
            tracking_number_url=tracking_number_url,
        )

        return update_sales_order_body
