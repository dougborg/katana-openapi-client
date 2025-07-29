from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.update_sales_order_body_status import UpdateSalesOrderBodyStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateSalesOrderBody")


@_attrs_define
class UpdateSalesOrderBody:
    """
    Attributes:
        order_no (Union[Unset, str]): Updatable only when sales order status is NOT_SHIPPED or PENDING.
        customer_id (Union[Unset, int]): Updatable only when sales order status is NOT_SHIPPED or PENDING.
        order_created_date (Union[Unset, str]):
        delivery_date (Union[None, Unset, str]): Updatable only when sales order status is NOT_SHIPPED or PENDING.
        picked_date (Union[None, Unset, str]): Updatable only when sales order status is NOT_SHIPPED or PENDING.
        location_id (Union[Unset, int]): Updatable only when sales order status is NOT_SHIPPED or PENDING.
        status (Union[Unset, UpdateSalesOrderBodyStatus]): When the status is omitted, NOT_SHIPPED is used as default.
            Use PENDING when you want to create sales order quotes.
        currency (Union[Unset, str]): E.g. USD, EUR. All currently active currency codes in ISO 4217 format. Updatable
            only when sales order status is NOT_SHIPPED or PENDING.
        conversion_rate (Union[Unset, float]): Updatable only when sales order status is PACKED or DELIVERED, otherwise
            it will fail with 422.
        conversion_date (Union[Unset, str]): Updatable only when sales order status is PACKED or DELIVERED, otherwise it
            will fail with 422.
        additional_info (Union[None, Unset, str]):
        customer_ref (Union[None, Unset, str]):
        tracking_number (Union[None, Unset, str]):
        tracking_number_url (Union[None, Unset, str]):
    """

    order_no: Union[Unset, str] = UNSET
    customer_id: Union[Unset, int] = UNSET
    order_created_date: Union[Unset, str] = UNSET
    delivery_date: Union[None, Unset, str] = UNSET
    picked_date: Union[None, Unset, str] = UNSET
    location_id: Union[Unset, int] = UNSET
    status: Union[Unset, UpdateSalesOrderBodyStatus] = UNSET
    currency: Union[Unset, str] = UNSET
    conversion_rate: Union[Unset, float] = UNSET
    conversion_date: Union[Unset, str] = UNSET
    additional_info: Union[None, Unset, str] = UNSET
    customer_ref: Union[None, Unset, str] = UNSET
    tracking_number: Union[None, Unset, str] = UNSET
    tracking_number_url: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        order_no = self.order_no

        customer_id = self.customer_id

        order_created_date = self.order_created_date

        delivery_date: Union[None, Unset, str]
        if isinstance(self.delivery_date, Unset):
            delivery_date = UNSET
        else:
            delivery_date = self.delivery_date

        picked_date: Union[None, Unset, str]
        if isinstance(self.picked_date, Unset):
            picked_date = UNSET
        else:
            picked_date = self.picked_date

        location_id = self.location_id

        status: Union[Unset, str] = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        currency = self.currency

        conversion_rate = self.conversion_rate

        conversion_date = self.conversion_date

        additional_info: Union[None, Unset, str]
        if isinstance(self.additional_info, Unset):
            additional_info = UNSET
        else:
            additional_info = self.additional_info

        customer_ref: Union[None, Unset, str]
        if isinstance(self.customer_ref, Unset):
            customer_ref = UNSET
        else:
            customer_ref = self.customer_ref

        tracking_number: Union[None, Unset, str]
        if isinstance(self.tracking_number, Unset):
            tracking_number = UNSET
        else:
            tracking_number = self.tracking_number

        tracking_number_url: Union[None, Unset, str]
        if isinstance(self.tracking_number_url, Unset):
            tracking_number_url = UNSET
        else:
            tracking_number_url = self.tracking_number_url

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
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

        order_created_date = d.pop("order_created_date", UNSET)

        def _parse_delivery_date(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        delivery_date = _parse_delivery_date(d.pop("delivery_date", UNSET))

        def _parse_picked_date(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        picked_date = _parse_picked_date(d.pop("picked_date", UNSET))

        location_id = d.pop("location_id", UNSET)

        _status = d.pop("status", UNSET)
        status: Union[Unset, UpdateSalesOrderBodyStatus]
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = UpdateSalesOrderBodyStatus(_status)

        currency = d.pop("currency", UNSET)

        conversion_rate = d.pop("conversion_rate", UNSET)

        conversion_date = d.pop("conversion_date", UNSET)

        def _parse_additional_info(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        additional_info = _parse_additional_info(d.pop("additional_info", UNSET))

        def _parse_customer_ref(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        customer_ref = _parse_customer_ref(d.pop("customer_ref", UNSET))

        def _parse_tracking_number(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        tracking_number = _parse_tracking_number(d.pop("tracking_number", UNSET))

        def _parse_tracking_number_url(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

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

        update_sales_order_body.additional_properties = d
        return update_sales_order_body

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
