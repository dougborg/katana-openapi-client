import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="UpdatePriceListRequest")


@_attrs_define
class UpdatePriceListRequest:
    """Request payload for updating an existing price list

    Example:
        {'name': 'Premium Customer Pricing - Updated', 'markup_percentage': 30.0, 'end_date': '2025-12-31T23:59:59Z'}

    Attributes:
        name (Union[Unset, str]): Descriptive name for the price list
        currency (Union[Unset, str]): ISO 4217 currency code for all prices in this list
        is_default (Union[Unset, bool]): Whether this price list should be the default fallback
        markup_percentage (Union[Unset, float]): Percentage markup applied to base costs
        start_date (Union[Unset, datetime.datetime]): Date and time when this price list becomes active
        end_date (Union[Unset, datetime.datetime]): Date and time when this price list expires
    """

    name: Unset | str = UNSET
    currency: Unset | str = UNSET
    is_default: Unset | bool = UNSET
    markup_percentage: Unset | float = UNSET
    start_date: Unset | datetime.datetime = UNSET
    end_date: Unset | datetime.datetime = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        currency = self.currency

        is_default = self.is_default

        markup_percentage = self.markup_percentage

        start_date: Unset | str = UNSET
        if not isinstance(self.start_date, Unset):
            start_date = self.start_date.isoformat()

        end_date: Unset | str = UNSET
        if not isinstance(self.end_date, Unset):
            end_date = self.end_date.isoformat()

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if currency is not UNSET:
            field_dict["currency"] = currency
        if is_default is not UNSET:
            field_dict["is_default"] = is_default
        if markup_percentage is not UNSET:
            field_dict["markup_percentage"] = markup_percentage
        if start_date is not UNSET:
            field_dict["start_date"] = start_date
        if end_date is not UNSET:
            field_dict["end_date"] = end_date

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name", UNSET)

        currency = d.pop("currency", UNSET)

        is_default = d.pop("is_default", UNSET)

        markup_percentage = d.pop("markup_percentage", UNSET)

        _start_date = d.pop("start_date", UNSET)
        start_date: Unset | datetime.datetime
        if isinstance(_start_date, Unset):
            start_date = UNSET
        else:
            start_date = isoparse(_start_date)

        _end_date = d.pop("end_date", UNSET)
        end_date: Unset | datetime.datetime
        if isinstance(_end_date, Unset):
            end_date = UNSET
        else:
            end_date = isoparse(_end_date)

        update_price_list_request = cls(
            name=name,
            currency=currency,
            is_default=is_default,
            markup_percentage=markup_percentage,
            start_date=start_date,
            end_date=end_date,
        )

        return update_price_list_request
