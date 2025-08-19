from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset
from ..models.create_sales_order_address_request_entity_type import (
    CreateSalesOrderAddressRequestEntityType,
)

T = TypeVar("T", bound="CreateSalesOrderAddressRequest")


@_attrs_define
class CreateSalesOrderAddressRequest:
    """Request payload for creating a new sales order address

    Example:
        {'sales_order_id': 2001, 'entity_type': 'shipping', 'first_name': 'John', 'last_name': 'Johnson', 'company':
            "Johnson's Restaurant", 'address_line_1': '123 Main Street', 'city': 'Portland', 'state': 'OR', 'zip': '97201',
            'country': 'US', 'phone': '+1-555-0123'}

    Attributes:
        sales_order_id (int): ID of the sales order this address belongs to
        entity_type (CreateSalesOrderAddressRequestEntityType): Type of address (billing or shipping)
        address_line_1 (str): Primary address line
        city (str): City name
        country (str): Country code
        first_name (Union[Unset, str]): First name for the address contact
        last_name (Union[Unset, str]): Last name for the address contact
        company (Union[Unset, str]): Company name for the address
        address_line_2 (Union[Unset, str]): Secondary address line
        state (Union[Unset, str]): State or province
        zip_ (Union[Unset, str]): Postal code
        phone (Union[Unset, str]): Contact phone number
    """

    sales_order_id: int
    entity_type: CreateSalesOrderAddressRequestEntityType
    address_line_1: str
    city: str
    country: str
    first_name: Unset | str = UNSET
    last_name: Unset | str = UNSET
    company: Unset | str = UNSET
    address_line_2: Unset | str = UNSET
    state: Unset | str = UNSET
    zip_: Unset | str = UNSET
    phone: Unset | str = UNSET

    def to_dict(self) -> dict[str, Any]:
        sales_order_id = self.sales_order_id

        entity_type = self.entity_type.value

        address_line_1 = self.address_line_1

        city = self.city

        country = self.country

        first_name = self.first_name

        last_name = self.last_name

        company = self.company

        address_line_2 = self.address_line_2

        state = self.state

        zip_ = self.zip_

        phone = self.phone

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "sales_order_id": sales_order_id,
                "entity_type": entity_type,
                "address_line_1": address_line_1,
                "city": city,
                "country": country,
            }
        )
        if first_name is not UNSET:
            field_dict["first_name"] = first_name
        if last_name is not UNSET:
            field_dict["last_name"] = last_name
        if company is not UNSET:
            field_dict["company"] = company
        if address_line_2 is not UNSET:
            field_dict["address_line_2"] = address_line_2
        if state is not UNSET:
            field_dict["state"] = state
        if zip_ is not UNSET:
            field_dict["zip"] = zip_
        if phone is not UNSET:
            field_dict["phone"] = phone

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        sales_order_id = d.pop("sales_order_id")

        entity_type = CreateSalesOrderAddressRequestEntityType(d.pop("entity_type"))

        address_line_1 = d.pop("address_line_1")

        city = d.pop("city")

        country = d.pop("country")

        first_name = d.pop("first_name", UNSET)

        last_name = d.pop("last_name", UNSET)

        company = d.pop("company", UNSET)

        address_line_2 = d.pop("address_line_2", UNSET)

        state = d.pop("state", UNSET)

        zip_ = d.pop("zip", UNSET)

        phone = d.pop("phone", UNSET)

        create_sales_order_address_request = cls(
            sales_order_id=sales_order_id,
            entity_type=entity_type,
            address_line_1=address_line_1,
            city=city,
            country=country,
            first_name=first_name,
            last_name=last_name,
            company=company,
            address_line_2=address_line_2,
            state=state,
            zip_=zip_,
            phone=phone,
        )

        return create_sales_order_address_request
