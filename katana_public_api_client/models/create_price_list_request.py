import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="CreatePriceListRequest")


@_attrs_define
class CreatePriceListRequest:
    """Request payload for creating a new price list with market-specific pricing configurations and time-based validity

    Example:
        {'name': 'Premium Customer Pricing', 'currency': 'USD', 'is_default': False, 'markup_percentage': 25.0,
            'start_date': '2024-01-01T00:00:00Z', 'end_date': '2024-12-31T23:59:59Z'}

    Attributes:
        name (str): Descriptive name for the price list (e.g., "Premium Customer Pricing", "Wholesale Rates")
        currency (str): ISO 4217 currency code for all prices in this list (e.g., USD, EUR, GBP)
        is_default (Union[Unset, bool]): Whether this price list should be the default fallback for customers without
            specific price lists
        markup_percentage (Union[Unset, float]): Percentage markup applied to base costs to calculate pricing in this
            list
        start_date (Union[Unset, datetime.datetime]): Date and time when this price list becomes active
        end_date (Union[Unset, datetime.datetime]): Date and time when this price list expires
    """

    name: str
    currency: str
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

        field_dict.update(
            {
                "name": name,
                "currency": currency,
            }
        )
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
        name = d.pop("name")

        currency = d.pop("currency")

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

        create_price_list_request = cls(
            name=name,
            currency=currency,
            is_default=is_default,
            markup_percentage=markup_percentage,
            start_date=start_date,
            end_date=end_date,
        )

        return create_price_list_request
