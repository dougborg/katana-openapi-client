from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateSalesOrderBody")


@_attrs_define
class UpdateSalesOrderBody:
    order_no: Unset | str = UNSET
    customer_id: Unset | int = UNSET
    delivery_date: None | Unset | str = UNSET
    additional_info: None | Unset | str = UNSET
    customer_ref: None | Unset | str = UNSET
    tracking_number: None | Unset | str = UNSET
    tracking_number_url: None | Unset | str = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        order_no = self.order_no

        customer_id = self.customer_id

        delivery_date: None | Unset | str
        if isinstance(self.delivery_date, Unset):
            delivery_date = UNSET
        else:
            delivery_date = self.delivery_date

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
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if order_no is not UNSET:
            field_dict["order_no"] = order_no
        if customer_id is not UNSET:
            field_dict["customer_id"] = customer_id
        if delivery_date is not UNSET:
            field_dict["delivery_date"] = delivery_date
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

        def _parse_delivery_date(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        delivery_date = _parse_delivery_date(d.pop("delivery_date", UNSET))

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
            delivery_date=delivery_date,
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
