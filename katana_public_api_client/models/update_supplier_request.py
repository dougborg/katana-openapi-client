from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="UpdateSupplierRequest")


@_attrs_define
class UpdateSupplierRequest:
    """Request payload for updating an existing supplier's contact information and details

    Example:
        {'name': 'Premium Kitchen Supplies Ltd', 'email': 'orders@premiumkitchen.com', 'phone': '+1-555-0134',
            'currency': 'USD', 'comment': 'Primary supplier for kitchen equipment and utensils. Excellent customer
            service.'}

    Attributes:
        name (Union[Unset, str]): Business name of the supplier company or individual
        email (Union[Unset, str]): Primary email address for supplier communication and order confirmations
        phone (Union[Unset, str]): Primary phone number for supplier contact and communication
        currency (Union[Unset, str]): The supplier's currency (ISO 4217).
        comment (Union[Unset, str]): Optional notes or comments about the supplier relationship
    """

    name: Unset | str = UNSET
    email: Unset | str = UNSET
    phone: Unset | str = UNSET
    currency: Unset | str = UNSET
    comment: Unset | str = UNSET

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
