import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="TaxRate")


@_attrs_define
class TaxRate:
    """Tax rate configuration for applying taxes to sales and purchase transactions based on jurisdiction and business
    requirements

        Example:
            {'id': 301, 'name': 'VAT 20%', 'rate': 20.0, 'is_default_sales': True, 'is_default_purchases': False,
                'display_name': 'VAT (20.0%)', 'created_at': '2024-01-15T09:30:00Z', 'updated_at': '2024-01-15T09:30:00Z'}

        Attributes:
            id (int): Unique identifier for the tax rate
            created_at (Union[Unset, datetime.datetime]): Timestamp when the entity was first created
            updated_at (Union[Unset, datetime.datetime]): Timestamp when the entity was last updated
            name (Union[Unset, str]): Descriptive name for the tax rate (e.g., "VAT 20%", "Sales Tax", "GST")
            rate (Union[Unset, float]): Tax rate as a percentage (e.g., 20.5 for 20.5% tax)
            is_default_sales (Union[Unset, bool]): Whether this tax rate is the default for sales transactions
            is_default_purchases (Union[Unset, bool]): Whether this tax rate is the default for purchase transactions
            display_name (Union[Unset, str]): Formatted display name for user interface presentation
    """

    id: int
    created_at: Unset | datetime.datetime = UNSET
    updated_at: Unset | datetime.datetime = UNSET
    name: Unset | str = UNSET
    rate: Unset | float = UNSET
    is_default_sales: Unset | bool = UNSET
    is_default_purchases: Unset | bool = UNSET
    display_name: Unset | str = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        created_at: Unset | str = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: Unset | str = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        name = self.name

        rate = self.rate

        is_default_sales = self.is_default_sales

        is_default_purchases = self.is_default_purchases

        display_name = self.display_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
            }
        )
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if name is not UNSET:
            field_dict["name"] = name
        if rate is not UNSET:
            field_dict["rate"] = rate
        if is_default_sales is not UNSET:
            field_dict["is_default_sales"] = is_default_sales
        if is_default_purchases is not UNSET:
            field_dict["is_default_purchases"] = is_default_purchases
        if display_name is not UNSET:
            field_dict["display_name"] = display_name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

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

        name = d.pop("name", UNSET)

        rate = d.pop("rate", UNSET)

        is_default_sales = d.pop("is_default_sales", UNSET)

        is_default_purchases = d.pop("is_default_purchases", UNSET)

        display_name = d.pop("display_name", UNSET)

        tax_rate = cls(
            id=id,
            created_at=created_at,
            updated_at=updated_at,
            name=name,
            rate=rate,
            is_default_sales=is_default_sales,
            is_default_purchases=is_default_purchases,
            display_name=display_name,
        )

        tax_rate.additional_properties = d
        return tax_rate

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
