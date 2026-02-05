from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.supplier_address import SupplierAddress


T = TypeVar("T", bound="Supplier")


@_attrs_define
class Supplier:
    """Supplier company or individual providing materials, products, or services for procurement operations

    Example:
        {'id': 4001, 'name': 'Premium Kitchen Supplies Ltd', 'email': 'orders@premiumkitchen.com', 'phone':
            '+1-555-0134', 'currency': 'USD', 'comment': 'Primary supplier for kitchen equipment and utensils. Reliable
            delivery times.', 'default_address_id': 4001, 'created_at': '2023-06-15T08:30:00Z', 'updated_at':
            '2024-01-15T14:20:00Z', 'deleted_at': None, 'addresses': [{'id': 4001, 'company': 'Premium Kitchen Supplies
            Ltd', 'street': '1250 Industrial Blvd', 'street2': 'Suite 200', 'city': 'Chicago', 'state': 'IL', 'zip':
            '60601', 'country': 'US', 'created_at': '2023-06-15T08:30:00Z', 'updated_at': '2023-06-15T08:30:00Z',
            'deleted_at': None}]}
    """

    id: int
    created_at: datetime.datetime | Unset = UNSET
    updated_at: datetime.datetime | Unset = UNSET
    deleted_at: datetime.datetime | None | Unset = UNSET
    name: str | Unset = UNSET
    email: str | Unset = UNSET
    phone: str | Unset = UNSET
    currency: str | Unset = UNSET
    comment: str | Unset = UNSET
    default_address_id: int | Unset = UNSET
    addresses: list[SupplierAddress] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: str | Unset = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        deleted_at: None | str | Unset
        if isinstance(self.deleted_at, Unset):
            deleted_at = UNSET
        elif isinstance(self.deleted_at, datetime.datetime):
            deleted_at = self.deleted_at.isoformat()
        else:
            deleted_at = self.deleted_at

        name = self.name

        email = self.email

        phone = self.phone

        currency = self.currency

        comment = self.comment

        default_address_id = self.default_address_id

        addresses: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.addresses, Unset):
            addresses = []
            for addresses_item_data in self.addresses:
                addresses_item = addresses_item_data.to_dict()
                addresses.append(addresses_item)

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
        if deleted_at is not UNSET:
            field_dict["deleted_at"] = deleted_at
        if name is not UNSET:
            field_dict["name"] = name
        if email is not UNSET:
            field_dict["email"] = email
        if phone is not UNSET:
            field_dict["phone"] = phone
        if currency is not UNSET:
            field_dict["currency"] = currency
        if comment is not UNSET:
            field_dict["comment"] = comment
        if default_address_id is not UNSET:
            field_dict["default_address_id"] = default_address_id
        if addresses is not UNSET:
            field_dict["addresses"] = addresses

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.supplier_address import SupplierAddress

        d = dict(src_dict)
        id = d.pop("id")

        _created_at = d.pop("created_at", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        _updated_at = d.pop("updated_at", UNSET)
        updated_at: datetime.datetime | Unset
        if isinstance(_updated_at, Unset):
            updated_at = UNSET
        else:
            updated_at = isoparse(_updated_at)

        def _parse_deleted_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                deleted_at_type_0 = isoparse(data)

                return deleted_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        deleted_at = _parse_deleted_at(d.pop("deleted_at", UNSET))

        name = d.pop("name", UNSET)

        email = d.pop("email", UNSET)

        phone = d.pop("phone", UNSET)

        currency = d.pop("currency", UNSET)

        comment = d.pop("comment", UNSET)

        default_address_id = d.pop("default_address_id", UNSET)

        _addresses = d.pop("addresses", UNSET)
        addresses: list[SupplierAddress] | Unset = UNSET
        if _addresses is not UNSET:
            addresses = []
            for addresses_item_data in _addresses:
                addresses_item = SupplierAddress.from_dict(addresses_item_data)

                addresses.append(addresses_item)

        supplier = cls(
            id=id,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
            name=name,
            email=email,
            phone=phone,
            currency=currency,
            comment=comment,
            default_address_id=default_address_id,
            addresses=addresses,
        )

        supplier.additional_properties = d
        return supplier

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
