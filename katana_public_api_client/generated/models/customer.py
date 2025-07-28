import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="Customer")


@_attrs_define
class Customer:
    id: int
    name: str
    first_name: None | Unset | str = UNSET
    last_name: None | Unset | str = UNSET
    company: None | Unset | str = UNSET
    email: None | Unset | str = UNSET
    phone: None | Unset | str = UNSET
    comment: None | Unset | str = UNSET
    currency: Unset | str = UNSET
    reference_id: None | Unset | str = UNSET
    category: None | Unset | str = UNSET
    discount_rate: None | Unset | float = UNSET
    default_billing_id: None | Unset | int = UNSET
    default_shipping_id: None | Unset | int = UNSET
    created_at: Unset | datetime.datetime = UNSET
    updated_at: Unset | datetime.datetime = UNSET
    deleted_at: None | Unset | datetime.datetime = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

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

        default_billing_id: None | Unset | int
        if isinstance(self.default_billing_id, Unset):
            default_billing_id = UNSET
        else:
            default_billing_id = self.default_billing_id

        default_shipping_id: None | Unset | int
        if isinstance(self.default_shipping_id, Unset):
            default_shipping_id = UNSET
        else:
            default_shipping_id = self.default_shipping_id

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

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
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
        if default_billing_id is not UNSET:
            field_dict["default_billing_id"] = default_billing_id
        if default_shipping_id is not UNSET:
            field_dict["default_shipping_id"] = default_shipping_id
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if deleted_at is not UNSET:
            field_dict["deleted_at"] = deleted_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

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

        currency = d.pop("currency", UNSET)

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

        def _parse_default_billing_id(data: object) -> None | Unset | int:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | int, data)

        default_billing_id = _parse_default_billing_id(
            d.pop("default_billing_id", UNSET)
        )

        def _parse_default_shipping_id(data: object) -> None | Unset | int:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | int, data)

        default_shipping_id = _parse_default_shipping_id(
            d.pop("default_shipping_id", UNSET)
        )

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

        customer = cls(
            id=id,
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
            default_billing_id=default_billing_id,
            default_shipping_id=default_shipping_id,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
        )

        customer.additional_properties = d
        return customer

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
