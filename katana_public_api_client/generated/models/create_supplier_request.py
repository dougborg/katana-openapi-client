from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.supplier_address_request import SupplierAddressRequest


T = TypeVar("T", bound="CreateSupplierRequest")


@_attrs_define
class CreateSupplierRequest:
    """
    Attributes:
        name (str): Business name of the supplier company or individual
        currency (Union[Unset, str]): Default currency code for transactions with this supplier (e.g., USD, EUR)
        email (Union[Unset, str]): Primary email address for supplier communication and order confirmations
        phone (Union[Unset, str]): Primary phone number for supplier contact and communication
        comment (Union[Unset, str]):
        addresses (Union[Unset, list['SupplierAddressRequest']]):
    """

    name: str
    currency: Union[Unset, str] = UNSET
    email: Union[Unset, str] = UNSET
    phone: Union[Unset, str] = UNSET
    comment: Union[Unset, str] = UNSET
    addresses: Union[Unset, list["SupplierAddressRequest"]] = UNSET

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        currency = self.currency

        email = self.email

        phone = self.phone

        comment = self.comment

        addresses: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.addresses, Unset):
            addresses = []
            for addresses_item_data in self.addresses:
                addresses_item = addresses_item_data.to_dict()
                addresses.append(addresses_item)

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "name": name,
            }
        )
        if currency is not UNSET:
            field_dict["currency"] = currency
        if email is not UNSET:
            field_dict["email"] = email
        if phone is not UNSET:
            field_dict["phone"] = phone
        if comment is not UNSET:
            field_dict["comment"] = comment
        if addresses is not UNSET:
            field_dict["addresses"] = addresses

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.supplier_address_request import SupplierAddressRequest

        d = dict(src_dict)
        name = d.pop("name")

        currency = d.pop("currency", UNSET)

        email = d.pop("email", UNSET)

        phone = d.pop("phone", UNSET)

        comment = d.pop("comment", UNSET)

        addresses = []
        _addresses = d.pop("addresses", UNSET)
        for addresses_item_data in _addresses or []:
            addresses_item = SupplierAddressRequest.from_dict(addresses_item_data)

            addresses.append(addresses_item)

        create_supplier_request = cls(
            name=name,
            currency=currency,
            email=email,
            phone=phone,
            comment=comment,
            addresses=addresses,
        )

        return create_supplier_request
