from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset
from ..models.address_entity_type import AddressEntityType

T = TypeVar("T", bound="CreateSalesOrderRequestAddressesItem")


@_attrs_define
class CreateSalesOrderRequestAddressesItem:
    entity_type: AddressEntityType
    first_name: str | Unset = UNSET
    last_name: str | Unset = UNSET
    company: str | Unset = UNSET
    line_1: str | Unset = UNSET
    line_2: str | Unset = UNSET
    city: str | Unset = UNSET
    state: str | Unset = UNSET
    zip_: str | Unset = UNSET
    country: str | Unset = UNSET
    phone: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        entity_type = self.entity_type.value

        first_name = self.first_name

        last_name = self.last_name

        company = self.company

        line_1 = self.line_1

        line_2 = self.line_2

        city = self.city

        state = self.state

        zip_ = self.zip_

        country = self.country

        phone = self.phone

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "entity_type": entity_type,
            }
        )
        if first_name is not UNSET:
            field_dict["first_name"] = first_name
        if last_name is not UNSET:
            field_dict["last_name"] = last_name
        if company is not UNSET:
            field_dict["company"] = company
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
        if phone is not UNSET:
            field_dict["phone"] = phone

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        entity_type = AddressEntityType(d.pop("entity_type"))

        first_name = d.pop("first_name", UNSET)

        last_name = d.pop("last_name", UNSET)

        company = d.pop("company", UNSET)

        line_1 = d.pop("line_1", UNSET)

        line_2 = d.pop("line_2", UNSET)

        city = d.pop("city", UNSET)

        state = d.pop("state", UNSET)

        zip_ = d.pop("zip", UNSET)

        country = d.pop("country", UNSET)

        phone = d.pop("phone", UNSET)

        create_sales_order_request_addresses_item = cls(
            entity_type=entity_type,
            first_name=first_name,
            last_name=last_name,
            company=company,
            line_1=line_1,
            line_2=line_2,
            city=city,
            state=state,
            zip_=zip_,
            country=country,
            phone=phone,
        )

        return create_sales_order_request_addresses_item
