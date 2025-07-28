import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="SalesOrderFulfillment")


@_attrs_define
class SalesOrderFulfillment:
    id: int
    sales_order_id: int
    tracking_number: None | Unset | str = UNSET
    tracking_number_url: None | Unset | str = UNSET
    shipped_date: None | Unset | datetime.datetime = UNSET
    estimated_delivery_date: None | Unset | datetime.datetime = UNSET
    actual_delivery_date: None | Unset | datetime.datetime = UNSET
    shipping_cost: None | Unset | float = UNSET
    shipping_method: None | Unset | str = UNSET
    carrier: None | Unset | str = UNSET
    notes: None | Unset | str = UNSET
    created_at: Unset | datetime.datetime = UNSET
    updated_at: Unset | datetime.datetime = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        sales_order_id = self.sales_order_id

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

        shipped_date: None | Unset | str
        if isinstance(self.shipped_date, Unset):
            shipped_date = UNSET
        elif isinstance(self.shipped_date, datetime.datetime):
            shipped_date = self.shipped_date.isoformat()
        else:
            shipped_date = self.shipped_date

        estimated_delivery_date: None | Unset | str
        if isinstance(self.estimated_delivery_date, Unset):
            estimated_delivery_date = UNSET
        elif isinstance(self.estimated_delivery_date, datetime.datetime):
            estimated_delivery_date = self.estimated_delivery_date.isoformat()
        else:
            estimated_delivery_date = self.estimated_delivery_date

        actual_delivery_date: None | Unset | str
        if isinstance(self.actual_delivery_date, Unset):
            actual_delivery_date = UNSET
        elif isinstance(self.actual_delivery_date, datetime.datetime):
            actual_delivery_date = self.actual_delivery_date.isoformat()
        else:
            actual_delivery_date = self.actual_delivery_date

        shipping_cost: None | Unset | float
        if isinstance(self.shipping_cost, Unset):
            shipping_cost = UNSET
        else:
            shipping_cost = self.shipping_cost

        shipping_method: None | Unset | str
        if isinstance(self.shipping_method, Unset):
            shipping_method = UNSET
        else:
            shipping_method = self.shipping_method

        carrier: None | Unset | str
        if isinstance(self.carrier, Unset):
            carrier = UNSET
        else:
            carrier = self.carrier

        notes: None | Unset | str
        if isinstance(self.notes, Unset):
            notes = UNSET
        else:
            notes = self.notes

        created_at: Unset | str = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: Unset | str = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "sales_order_id": sales_order_id,
            }
        )
        if tracking_number is not UNSET:
            field_dict["tracking_number"] = tracking_number
        if tracking_number_url is not UNSET:
            field_dict["tracking_number_url"] = tracking_number_url
        if shipped_date is not UNSET:
            field_dict["shipped_date"] = shipped_date
        if estimated_delivery_date is not UNSET:
            field_dict["estimated_delivery_date"] = estimated_delivery_date
        if actual_delivery_date is not UNSET:
            field_dict["actual_delivery_date"] = actual_delivery_date
        if shipping_cost is not UNSET:
            field_dict["shipping_cost"] = shipping_cost
        if shipping_method is not UNSET:
            field_dict["shipping_method"] = shipping_method
        if carrier is not UNSET:
            field_dict["carrier"] = carrier
        if notes is not UNSET:
            field_dict["notes"] = notes
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        sales_order_id = d.pop("sales_order_id")

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

        def _parse_shipped_date(data: object) -> None | Unset | datetime.datetime:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                shipped_date_type_0 = isoparse(data)

                return shipped_date_type_0
            except:  # noqa: E722
                pass
            return cast(None | Unset | datetime.datetime, data)

        shipped_date = _parse_shipped_date(d.pop("shipped_date", UNSET))

        def _parse_estimated_delivery_date(
            data: object,
        ) -> None | Unset | datetime.datetime:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                estimated_delivery_date_type_0 = isoparse(data)

                return estimated_delivery_date_type_0
            except:  # noqa: E722
                pass
            return cast(None | Unset | datetime.datetime, data)

        estimated_delivery_date = _parse_estimated_delivery_date(
            d.pop("estimated_delivery_date", UNSET)
        )

        def _parse_actual_delivery_date(
            data: object,
        ) -> None | Unset | datetime.datetime:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                actual_delivery_date_type_0 = isoparse(data)

                return actual_delivery_date_type_0
            except:  # noqa: E722
                pass
            return cast(None | Unset | datetime.datetime, data)

        actual_delivery_date = _parse_actual_delivery_date(
            d.pop("actual_delivery_date", UNSET)
        )

        def _parse_shipping_cost(data: object) -> None | Unset | float:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | float, data)

        shipping_cost = _parse_shipping_cost(d.pop("shipping_cost", UNSET))

        def _parse_shipping_method(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        shipping_method = _parse_shipping_method(d.pop("shipping_method", UNSET))

        def _parse_carrier(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        carrier = _parse_carrier(d.pop("carrier", UNSET))

        def _parse_notes(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        notes = _parse_notes(d.pop("notes", UNSET))

        _created_at = d.pop("created_at", UNSET)
        created_at: Unset | datetime.datetime
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        _updated_at = d.pop("updated_at", UNSET)
        updated_at: Unset | datetime.datetime
        if isinstance(_updated_at, Unset):
            updated_at = UNSET
        else:
            updated_at = isoparse(_updated_at)

        sales_order_fulfillment = cls(
            id=id,
            sales_order_id=sales_order_id,
            tracking_number=tracking_number,
            tracking_number_url=tracking_number_url,
            shipped_date=shipped_date,
            estimated_delivery_date=estimated_delivery_date,
            actual_delivery_date=actual_delivery_date,
            shipping_cost=shipping_cost,
            shipping_method=shipping_method,
            carrier=carrier,
            notes=notes,
            created_at=created_at,
            updated_at=updated_at,
        )

        sales_order_fulfillment.additional_properties = d
        return sales_order_fulfillment

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
