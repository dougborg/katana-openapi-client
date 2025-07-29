from collections.abc import Mapping
from typing import Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateSupplierRequest")


@_attrs_define
class UpdateSupplierRequest:
    """
    Attributes:
        name (Union[Unset, str]):
        email (Union[Unset, str]):
        phone (Union[Unset, str]):
        currency (Union[Unset, str]): The supplier's currency (ISO 4217).
        comment (Union[Unset, str]):
    """

    name: Union[Unset, str] = UNSET
    email: Union[Unset, str] = UNSET
    phone: Union[Unset, str] = UNSET
    currency: Union[Unset, str] = UNSET
    comment: Union[Unset, str] = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        email = self.email

        phone = self.phone

        currency = self.currency

        comment = self.comment

        field_dict: dict[str, Any] = {}

        field_dict.update({})
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

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name", UNSET)

        email = d.pop("email", UNSET)

        phone = d.pop("phone", UNSET)

        currency = d.pop("currency", UNSET)

        comment = d.pop("comment", UNSET)

        update_supplier_request = cls(
            name=name,
            email=email,
            phone=phone,
            currency=currency,
            comment=comment,
        )

        return update_supplier_request
