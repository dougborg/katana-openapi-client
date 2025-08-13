import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="PriceListRow")


@_attrs_define
class PriceListRow:
    """Individual product variant pricing entry within a price list for customer-specific or market-specific pricing
    management

        Example:
            {'id': 5001, 'price_list_id': 1001, 'variant_id': 201, 'price': 249.99, 'currency': 'USD', 'created_at':
                '2024-01-15T10:00:00Z', 'updated_at': '2024-01-15T10:00:00Z'}
    """

    id: int
    price_list_id: int
    variant_id: int
    price: float
    created_at: Unset | datetime.datetime = UNSET
    updated_at: Unset | datetime.datetime = UNSET
    currency: Unset | str = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        price_list_id = self.price_list_id

        variant_id = self.variant_id

        price = self.price

        created_at: Unset | str = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: Unset | str = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        currency = self.currency

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "price_list_id": price_list_id,
                "variant_id": variant_id,
                "price": price,
            }
        )
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if currency is not UNSET:
            field_dict["currency"] = currency

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        price_list_id = d.pop("price_list_id")

        variant_id = d.pop("variant_id")

        price = d.pop("price")

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

        currency = d.pop("currency", UNSET)

        price_list_row = cls(
            id=id,
            price_list_id=price_list_id,
            variant_id=variant_id,
            price=price,
            created_at=created_at,
            updated_at=updated_at,
            currency=currency,
        )

        price_list_row.additional_properties = d
        return price_list_row

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
