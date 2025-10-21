from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset
from ..models.update_sales_order_address_request_entity_type import (
    UpdateSalesOrderAddressRequestEntityType,
)

T = TypeVar("T", bound="UpdateSalesOrderAddressRequest")


@_attrs_define
class UpdateSalesOrderAddressRequest:
    """Request payload for updating an existing sales order address

    Example:
        {'address_line_1': '456 Oak Avenue', 'phone': '+1-555-0456'}

    Attributes:
        entity_type (Union[Unset, UpdateSalesOrderAddressRequestEntityType]): Type of address (billing or shipping)
        first_name (Union[Unset, str]): First name for the address contact
        last_name (Union[Unset, str]): Last name for the address contact
        company (Union[Unset, str]): Company name for the address
        address_line_1 (Union[Unset, str]): Primary address line
        address_line_2 (Union[Unset, str]): Secondary address line
        city (Union[Unset, str]): City name
        state (Union[Unset, str]): State or province
        zip_ (Union[Unset, str]): Postal code
        country (Union[Unset, str]): Country code
        phone (Union[Unset, str]): Contact phone number
    """

    entity_type: Unset | UpdateSalesOrderAddressRequestEntityType = UNSET
    first_name: Unset | str = UNSET
    last_name: Unset | str = UNSET
    company: Unset | str = UNSET
    address_line_1: Unset | str = UNSET
    address_line_2: Unset | str = UNSET
    city: Unset | str = UNSET
    state: Unset | str = UNSET
    zip_: Unset | str = UNSET
    country: Unset | str = UNSET
    phone: Unset | str = UNSET

    def to_dict(self) -> dict[str, Any]:
        entity_type: Unset | str = UNSET
        if not isinstance(self.entity_type, Unset):
            entity_type = self.entity_type.value

        first_name = self.first_name

        last_name = self.last_name

        company = self.company

        address_line_1 = self.address_line_1

        address_line_2 = self.address_line_2

        city = self.city

        state = self.state

        zip_ = self.zip_

        country = self.country

        phone = self.phone

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if entity_type is not UNSET:
            field_dict["entity_type"] = entity_type
        if first_name is not UNSET:
            field_dict["first_name"] = first_name
        if last_name is not UNSET:
            field_dict["last_name"] = last_name
        if company is not UNSET:
            field_dict["company"] = company
        if address_line_1 is not UNSET:
            field_dict["address_line_1"] = address_line_1
        if address_line_2 is not UNSET:
            field_dict["address_line_2"] = address_line_2
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
        _entity_type = d.pop("entity_type", UNSET)
        entity_type: Unset | UpdateSalesOrderAddressRequestEntityType
        if isinstance(_entity_type, Unset):
            entity_type = UNSET
        else:
            entity_type = UpdateSalesOrderAddressRequestEntityType(_entity_type)

        first_name = d.pop("first_name", UNSET)

        last_name = d.pop("last_name", UNSET)

        company = d.pop("company", UNSET)

        address_line_1 = d.pop("address_line_1", UNSET)

        address_line_2 = d.pop("address_line_2", UNSET)

        city = d.pop("city", UNSET)

        state = d.pop("state", UNSET)

        zip_ = d.pop("zip", UNSET)

        country = d.pop("country", UNSET)

        phone = d.pop("phone", UNSET)

        update_sales_order_address_request = cls(
            entity_type=entity_type,
            first_name=first_name,
            last_name=last_name,
            company=company,
            address_line_1=address_line_1,
            address_line_2=address_line_2,
            city=city,
            state=state,
            zip_=zip_,
            country=country,
            phone=phone,
        )

        return update_sales_order_address_request
