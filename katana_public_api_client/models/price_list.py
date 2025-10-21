import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="PriceList")


@_attrs_define
class PriceList:
    """Customer-specific pricing configuration with markup rules and time-based validity for flexible pricing management
    across different market segments

        Example:
            {'id': 1001, 'name': 'Premium Customer Pricing', 'currency': 'USD', 'is_default': False, 'markup_percentage':
                25.0, 'start_date': '2024-01-01T00:00:00Z', 'end_date': '2024-12-31T23:59:59Z', 'created_at':
                '2024-01-01T10:00:00Z', 'updated_at': '2024-01-15T14:30:00Z', 'deleted_at': None}

        Attributes:
            id (int): Unique identifier for the price list
            name (str): Descriptive name for the price list (e.g., "Premium Customer Pricing", "Wholesale Rates")
            created_at (Union[Unset, datetime.datetime]): Timestamp when the entity was first created
            updated_at (Union[Unset, datetime.datetime]): Timestamp when the entity was last updated
            deleted_at (Union[None, Unset, datetime.datetime]): Nullable deletion timestamp
            currency (Union[Unset, str]): ISO 4217 currency code for all prices in this list (e.g., USD, EUR, GBP)
            is_default (Union[Unset, bool]): Whether this price list is the default fallback for customers without specific
                price lists
            markup_percentage (Union[None, Unset, float]): Percentage markup applied to base costs to calculate pricing in
                this list
            start_date (Union[None, Unset, datetime.datetime]): Date and time when this price list becomes active
            end_date (Union[None, Unset, datetime.datetime]): Date and time when this price list expires
    """

    id: int
    name: str
    created_at: Unset | datetime.datetime = UNSET
    updated_at: Unset | datetime.datetime = UNSET
    deleted_at: None | Unset | datetime.datetime = UNSET
    currency: Unset | str = UNSET
    is_default: Unset | bool = UNSET
    markup_percentage: None | Unset | float = UNSET
    start_date: None | Unset | datetime.datetime = UNSET
    end_date: None | Unset | datetime.datetime = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        created_at: Unset | str = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: Unset | str = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        deleted_at: None | Unset | str
        if isinstance(self.deleted_at, Unset):
            deleted_at = UNSET
        elif isinstance(self.deleted_at, datetime.datetime):
            deleted_at = self.deleted_at.isoformat()
        else:
            deleted_at = self.deleted_at

        currency = self.currency

        is_default = self.is_default

        markup_percentage: None | Unset | float
        if isinstance(self.markup_percentage, Unset):
            markup_percentage = UNSET
        else:
            markup_percentage = self.markup_percentage

        start_date: None | Unset | str
        if isinstance(self.start_date, Unset):
            start_date = UNSET
        elif isinstance(self.start_date, datetime.datetime):
            start_date = self.start_date.isoformat()
        else:
            start_date = self.start_date

        end_date: None | Unset | str
        if isinstance(self.end_date, Unset):
            end_date = UNSET
        elif isinstance(self.end_date, datetime.datetime):
            end_date = self.end_date.isoformat()
        else:
            end_date = self.end_date

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
            }
        )
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if deleted_at is not UNSET:
            field_dict["deleted_at"] = deleted_at
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
        id = d.pop("id")

        name = d.pop("name")

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

        def _parse_deleted_at(data: object) -> None | Unset | datetime.datetime:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                deleted_at_type_0 = isoparse(data)

                return deleted_at_type_0
            except:  # noqa: E722
                pass
            return cast(None | Unset | datetime.datetime, data)

        deleted_at = _parse_deleted_at(d.pop("deleted_at", UNSET))

        currency = d.pop("currency", UNSET)

        is_default = d.pop("is_default", UNSET)

        def _parse_markup_percentage(data: object) -> None | Unset | float:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | float, data)

        markup_percentage = _parse_markup_percentage(d.pop("markup_percentage", UNSET))

        def _parse_start_date(data: object) -> None | Unset | datetime.datetime:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                start_date_type_0 = isoparse(data)

                return start_date_type_0
            except:  # noqa: E722
                pass
            return cast(None | Unset | datetime.datetime, data)

        start_date = _parse_start_date(d.pop("start_date", UNSET))

        def _parse_end_date(data: object) -> None | Unset | datetime.datetime:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                end_date_type_0 = isoparse(data)

                return end_date_type_0
            except:  # noqa: E722
                pass
            return cast(None | Unset | datetime.datetime, data)

        end_date = _parse_end_date(d.pop("end_date", UNSET))

        price_list = cls(
            id=id,
            name=name,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
            currency=currency,
            is_default=is_default,
            markup_percentage=markup_percentage,
            start_date=start_date,
            end_date=end_date,
        )

        price_list.additional_properties = d
        return price_list

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
