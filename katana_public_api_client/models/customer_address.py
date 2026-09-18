from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset
from ..models.address_entity_type import AddressEntityType

T = TypeVar("T", bound="CustomerAddress")


@_attrs_define
class CustomerAddress:
    """Customer address for billing and shipping purposes with complete contact information

    Example:
        {'id': 3001, 'customer_id': 2001, 'entity_type': 'billing', 'default': True, 'first_name': 'Sarah', 'last_name':
            'Johnson', 'company': 'Kitchen Pro Restaurants Ltd', 'phone': '+1-555-0123', 'line_1': '123 Restaurant Row',
            'line_2': 'Suite 200', 'city': 'Chicago', 'state': 'IL', 'zip': '60601', 'country': 'US', 'created_at':
            '2024-01-10T09:15:00Z', 'updated_at': '2024-01-10T09:15:00Z'}
    """

    id: int
    customer_id: int
    entity_type: AddressEntityType
    created_at: datetime.datetime | Unset = UNSET
    updated_at: datetime.datetime | Unset = UNSET
    deleted_at: datetime.datetime | Unset | None = UNSET
    default: bool | Unset = UNSET
    first_name: str | Unset | None = UNSET
    last_name: str | Unset | None = UNSET
    company: str | Unset | None = UNSET
    phone: str | Unset | None = UNSET
    line_1: str | Unset | None = UNSET
    line_2: str | Unset | None = UNSET
    city: str | Unset | None = UNSET
    state: str | Unset | None = UNSET
    zip_: str | Unset | None = UNSET
    country: str | Unset | None = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        customer_id = self.customer_id

        entity_type = self.entity_type.value

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        updated_at: str | Unset = UNSET
        if not isinstance(self.updated_at, Unset):
            updated_at = self.updated_at.isoformat()

        deleted_at: str | Unset | None
        if isinstance(self.deleted_at, Unset):
            deleted_at = UNSET
        elif isinstance(self.deleted_at, datetime.datetime):
            deleted_at = self.deleted_at.isoformat()
        else:
            deleted_at = self.deleted_at

        default = self.default

        first_name: str | Unset | None
        if isinstance(self.first_name, Unset):
            first_name = UNSET
        else:
            first_name = self.first_name

        last_name: str | Unset | None
        if isinstance(self.last_name, Unset):
            last_name = UNSET
        else:
            last_name = self.last_name

        company: str | Unset | None
        if isinstance(self.company, Unset):
            company = UNSET
        else:
            company = self.company

        phone: str | Unset | None
        if isinstance(self.phone, Unset):
            phone = UNSET
        else:
            phone = self.phone

        line_1: str | Unset | None
        if isinstance(self.line_1, Unset):
            line_1 = UNSET
        else:
            line_1 = self.line_1

        line_2: str | Unset | None
        if isinstance(self.line_2, Unset):
            line_2 = UNSET
        else:
            line_2 = self.line_2

        city: str | Unset | None
        if isinstance(self.city, Unset):
            city = UNSET
        else:
            city = self.city

        state: str | Unset | None
        if isinstance(self.state, Unset):
            state = UNSET
        else:
            state = self.state

        zip_: str | Unset | None
        if isinstance(self.zip_, Unset):
            zip_ = UNSET
        else:
            zip_ = self.zip_

        country: str | Unset | None
        if isinstance(self.country, Unset):
            country = UNSET
        else:
            country = self.country

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "customer_id": customer_id,
                "entity_type": entity_type,
            }
        )
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if deleted_at is not UNSET:
            field_dict["deleted_at"] = deleted_at
        if default is not UNSET:
            field_dict["default"] = default
        if first_name is not UNSET:
            field_dict["first_name"] = first_name
        if last_name is not UNSET:
            field_dict["last_name"] = last_name
        if company is not UNSET:
            field_dict["company"] = company
        if phone is not UNSET:
            field_dict["phone"] = phone
        if line_1 is not UNSET:
            field_dict["line_1"] = line_1
        if line_2 is not UNSET:
            field_dict["line_2"] = line_2
        if city is not UNSET:
            field_dict["city"] = city
        if state is not UNSET:
            field_dict["state"] = state
        if zip_ is not UNSET:
            field_dict["zip"] = zip_
        if country is not UNSET:
            field_dict["country"] = country

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        customer_id = d.pop("customer_id")

        entity_type = AddressEntityType(d.pop("entity_type"))

        _created_at = d.pop("created_at", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = datetime.datetime.fromisoformat(_created_at)

        _updated_at = d.pop("updated_at", UNSET)
        updated_at: datetime.datetime | Unset
        if isinstance(_updated_at, Unset):
            updated_at = UNSET
        else:
            updated_at = datetime.datetime.fromisoformat(_updated_at)

        def _parse_deleted_at(data: object) -> datetime.datetime | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                deleted_at_type_0 = datetime.datetime.fromisoformat(data)

                return deleted_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | Unset | None, data)

        deleted_at = _parse_deleted_at(d.pop("deleted_at", UNSET))

        default = d.pop("default", UNSET)

        def _parse_first_name(data: object) -> str | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(str | Unset | None, data)

        first_name = _parse_first_name(d.pop("first_name", UNSET))

        def _parse_last_name(data: object) -> str | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(str | Unset | None, data)

        last_name = _parse_last_name(d.pop("last_name", UNSET))

        def _parse_company(data: object) -> str | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(str | Unset | None, data)

        company = _parse_company(d.pop("company", UNSET))

        def _parse_phone(data: object) -> str | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(str | Unset | None, data)

        phone = _parse_phone(d.pop("phone", UNSET))

        def _parse_line_1(data: object) -> str | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(str | Unset | None, data)

        line_1 = _parse_line_1(d.pop("line_1", UNSET))

        def _parse_line_2(data: object) -> str | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(str | Unset | None, data)

        line_2 = _parse_line_2(d.pop("line_2", UNSET))

        def _parse_city(data: object) -> str | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(str | Unset | None, data)

        city = _parse_city(d.pop("city", UNSET))

        def _parse_state(data: object) -> str | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(str | Unset | None, data)

        state = _parse_state(d.pop("state", UNSET))

        def _parse_zip_(data: object) -> str | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(str | Unset | None, data)

        zip_ = _parse_zip_(d.pop("zip", UNSET))

        def _parse_country(data: object) -> str | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(str | Unset | None, data)

        country = _parse_country(d.pop("country", UNSET))

        customer_address = cls(
            id=id,
            customer_id=customer_id,
            entity_type=entity_type,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
            default=default,
            first_name=first_name,
            last_name=last_name,
            company=company,
            phone=phone,
            line_1=line_1,
            line_2=line_2,
            city=city,
            state=state,
            zip_=zip_,
            country=country,
        )

        customer_address.additional_properties = d
        return customer_address

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
