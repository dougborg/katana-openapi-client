from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateCustomerRequest")


@_attrs_define
class CreateCustomerRequest:
    name: str
    first_name: None | Unset | str = UNSET
    last_name: None | Unset | str = UNSET
    company: None | Unset | str = UNSET
    email: None | Unset | str = UNSET
    phone: None | Unset | str = UNSET
    comment: None | Unset | str = UNSET
    currency: None | Unset | str = UNSET
    reference_id: None | Unset | str = UNSET
    category: None | Unset | str = UNSET
    discount_rate: None | Unset | float = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        first_name: None | Unset | str
        if isinstance(self.first_name, Unset):
            first_name = UNSET
        else:
            first_name = self.first_name

        last_name: None | Unset | str
        if isinstance(self.last_name, Unset):
            last_name = UNSET
        else:
            last_name = self.last_name

        company: None | Unset | str
        if isinstance(self.company, Unset):
            company = UNSET
        else:
            company = self.company

        email: None | Unset | str
        if isinstance(self.email, Unset):
            email = UNSET
        else:
            email = self.email

        phone: None | Unset | str
        if isinstance(self.phone, Unset):
            phone = UNSET
        else:
            phone = self.phone

        comment: None | Unset | str
        if isinstance(self.comment, Unset):
            comment = UNSET
        else:
            comment = self.comment

        currency: None | Unset | str
        if isinstance(self.currency, Unset):
            currency = UNSET
        else:
            currency = self.currency

        reference_id: None | Unset | str
        if isinstance(self.reference_id, Unset):
            reference_id = UNSET
        else:
            reference_id = self.reference_id

        category: None | Unset | str
        if isinstance(self.category, Unset):
            category = UNSET
        else:
            category = self.category

        discount_rate: None | Unset | float
        if isinstance(self.discount_rate, Unset):
            discount_rate = UNSET
        else:
            discount_rate = self.discount_rate

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
            }
        )
        if first_name is not UNSET:
            field_dict["first_name"] = first_name
        if last_name is not UNSET:
            field_dict["last_name"] = last_name
        if company is not UNSET:
            field_dict["company"] = company
        if email is not UNSET:
            field_dict["email"] = email
        if phone is not UNSET:
            field_dict["phone"] = phone
        if comment is not UNSET:
            field_dict["comment"] = comment
        if currency is not UNSET:
            field_dict["currency"] = currency
        if reference_id is not UNSET:
            field_dict["reference_id"] = reference_id
        if category is not UNSET:
            field_dict["category"] = category
        if discount_rate is not UNSET:
            field_dict["discount_rate"] = discount_rate

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        def _parse_first_name(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        first_name = _parse_first_name(d.pop("first_name", UNSET))

        def _parse_last_name(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        last_name = _parse_last_name(d.pop("last_name", UNSET))

        def _parse_company(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        company = _parse_company(d.pop("company", UNSET))

        def _parse_email(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        email = _parse_email(d.pop("email", UNSET))

        def _parse_phone(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        phone = _parse_phone(d.pop("phone", UNSET))

        def _parse_comment(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        comment = _parse_comment(d.pop("comment", UNSET))

        def _parse_currency(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        currency = _parse_currency(d.pop("currency", UNSET))

        def _parse_reference_id(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        reference_id = _parse_reference_id(d.pop("reference_id", UNSET))

        def _parse_category(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        category = _parse_category(d.pop("category", UNSET))

        def _parse_discount_rate(data: object) -> None | Unset | float:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | float, data)

        discount_rate = _parse_discount_rate(d.pop("discount_rate", UNSET))

        create_customer_request = cls(
            name=name,
            first_name=first_name,
            last_name=last_name,
            company=company,
            email=email,
            phone=phone,
            comment=comment,
            currency=currency,
            reference_id=reference_id,
            category=category,
            discount_rate=discount_rate,
        )

        create_customer_request.additional_properties = d
        return create_customer_request

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
