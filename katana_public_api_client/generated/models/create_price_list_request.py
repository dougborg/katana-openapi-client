import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreatePriceListRequest")


@_attrs_define
class CreatePriceListRequest:
    """
    Attributes:
        name (str): Name of the price list
        currency (str): Currency code (e.g., USD, EUR)
        is_default (Union[Unset, bool]): Whether this is the default price list
        markup_percentage (Union[Unset, float]): Markup percentage for the price list
        start_date (Union[Unset, datetime.datetime]): When the price list becomes active
        end_date (Union[Unset, datetime.datetime]): When the price list expires
    """

    name: str
    currency: str
    is_default: Union[Unset, bool] = UNSET
    markup_percentage: Union[Unset, float] = UNSET
    start_date: Union[Unset, datetime.datetime] = UNSET
    end_date: Union[Unset, datetime.datetime] = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        currency = self.currency

        is_default = self.is_default

        markup_percentage = self.markup_percentage

        start_date: Union[Unset, str] = UNSET
        if not isinstance(self.start_date, Unset):
            start_date = self.start_date.isoformat()

        end_date: Union[Unset, str] = UNSET
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
        start_date: Union[Unset, datetime.datetime]
        if isinstance(_start_date, Unset):
            start_date = UNSET
        else:
            start_date = isoparse(_start_date)

        _end_date = d.pop("end_date", UNSET)
        end_date: Union[Unset, datetime.datetime]
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
