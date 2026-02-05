from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="UpdateCustomerRequest")


@_attrs_define
class UpdateCustomerRequest:
    """Request payload for updating an existing customer with contact and business information

    Example:
        {'name': 'Gourmet Bistro Group', 'first_name': 'Elena', 'last_name': 'Rodriguez', 'company': 'Gourmet Bistro
            Group Inc', 'email': 'procurement@gourmetbistro.com', 'phone': '+1-555-0125', 'comment': 'Premium restaurant
            chain - priority orders', 'currency': 'USD', 'reference_id': 'GBG-2024-003', 'category': 'Fine Dining',
            'discount_rate': 7.5, 'default_shipping_id': 2}
    """

    name: str | Unset = UNSET
    first_name: None | str | Unset = UNSET
    last_name: None | str | Unset = UNSET
    company: None | str | Unset = UNSET
    email: None | str | Unset = UNSET
    phone: None | str | Unset = UNSET
    comment: None | str | Unset = UNSET
    currency: None | str | Unset = UNSET
    reference_id: None | str | Unset = UNSET
    category: None | str | Unset = UNSET
    discount_rate: float | None | Unset = UNSET
    default_shipping_id: int | None | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        first_name: None | str | Unset
        if isinstance(self.first_name, Unset):
            first_name = UNSET
        else:
            first_name = self.first_name

        last_name: None | str | Unset
        if isinstance(self.last_name, Unset):
            last_name = UNSET
        else:
            last_name = self.last_name

        company: None | str | Unset
        if isinstance(self.company, Unset):
            company = UNSET
        else:
            company = self.company

        email: None | str | Unset
        if isinstance(self.email, Unset):
            email = UNSET
        else:
            email = self.email

        phone: None | str | Unset
        if isinstance(self.phone, Unset):
            phone = UNSET
        else:
            phone = self.phone

        comment: None | str | Unset
        if isinstance(self.comment, Unset):
            comment = UNSET
        else:
            comment = self.comment

        currency: None | str | Unset
        if isinstance(self.currency, Unset):
            currency = UNSET
        else:
            currency = self.currency

        reference_id: None | str | Unset
        if isinstance(self.reference_id, Unset):
            reference_id = UNSET
        else:
            reference_id = self.reference_id

        category: None | str | Unset
        if isinstance(self.category, Unset):
            category = UNSET
        else:
            category = self.category

        discount_rate: float | None | Unset
        if isinstance(self.discount_rate, Unset):
            discount_rate = UNSET
        else:
            discount_rate = self.discount_rate

        default_shipping_id: int | None | Unset
        if isinstance(self.default_shipping_id, Unset):
            default_shipping_id = UNSET
        else:
            default_shipping_id = self.default_shipping_id

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
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
        if default_shipping_id is not UNSET:
            field_dict["default_shipping_id"] = default_shipping_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name", UNSET)

        def _parse_first_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        first_name = _parse_first_name(d.pop("first_name", UNSET))

        def _parse_last_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        last_name = _parse_last_name(d.pop("last_name", UNSET))

        def _parse_company(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        company = _parse_company(d.pop("company", UNSET))

        def _parse_email(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        email = _parse_email(d.pop("email", UNSET))

        def _parse_phone(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        phone = _parse_phone(d.pop("phone", UNSET))

        def _parse_comment(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        comment = _parse_comment(d.pop("comment", UNSET))

        def _parse_currency(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        currency = _parse_currency(d.pop("currency", UNSET))

        def _parse_reference_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        reference_id = _parse_reference_id(d.pop("reference_id", UNSET))

        def _parse_category(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        category = _parse_category(d.pop("category", UNSET))

        def _parse_discount_rate(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        discount_rate = _parse_discount_rate(d.pop("discount_rate", UNSET))

        def _parse_default_shipping_id(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        default_shipping_id = _parse_default_shipping_id(
            d.pop("default_shipping_id", UNSET)
        )

        update_customer_request = cls(
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
            default_shipping_id=default_shipping_id,
        )

        return update_customer_request
