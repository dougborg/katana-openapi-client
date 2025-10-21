import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.supplier_address import SupplierAddress


T = TypeVar("T", bound="Supplier")


@_attrs_define
class Supplier:
    """Supplier company or individual providing materials, products, or services for procurement operations

    Example:
        {'id': 4001, 'name': 'Premium Kitchen Supplies Ltd', 'email': 'orders@premiumkitchen.com', 'phone':
            '+1-555-0134', 'currency': 'USD', 'comment': 'Primary supplier for kitchen equipment and utensils. Reliable
            delivery times.', 'default_address_id': 4001, 'created_at': '2023-06-15T08:30:00Z', 'updated_at':
            '2024-01-15T14:20:00Z', 'deleted_at': None, 'addresses': [{'id': 4001, 'company': 'Premium Kitchen Supplies
            Ltd', 'street': '1250 Industrial Blvd', 'street2': 'Suite 200', 'city': 'Chicago', 'state': 'IL', 'zip':
            '60601', 'country': 'US', 'created_at': '2023-06-15T08:30:00Z', 'updated_at': '2023-06-15T08:30:00Z',
            'deleted_at': None}]}

    Attributes:
        id (int): Unique identifier for the supplier
        created_at (Union[Unset, datetime.datetime]): Timestamp when the entity was first created
        updated_at (Union[Unset, datetime.datetime]): Timestamp when the entity was last updated
        deleted_at (Union[None, Unset, datetime.datetime]): Nullable deletion timestamp
        name (Union[Unset, str]): Business name of the supplier company or individual
        email (Union[Unset, str]): Primary email address for supplier communication and order confirmations
        phone (Union[Unset, str]): Primary phone number for supplier contact and communication
        currency (Union[Unset, str]): Default currency used for transactions with this supplier (ISO 4217 format)
        comment (Union[Unset, str]): Optional notes or comments about the supplier relationship
        default_address_id (Union[Unset, int]): Unique identifier of the default address for this supplier
        addresses (Union[Unset, list['SupplierAddress']]): List of addresses associated with this supplier
    """

    id: int
    created_at: Unset | datetime.datetime = UNSET
    updated_at: Unset | datetime.datetime = UNSET
    deleted_at: None | Unset | datetime.datetime = UNSET
    name: Unset | str = UNSET
    email: Unset | str = UNSET
    phone: Unset | str = UNSET
    currency: Unset | str = UNSET
    comment: Unset | str = UNSET
    default_address_id: Unset | int = UNSET
    addresses: Unset | list["SupplierAddress"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

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

        name = self.name

        email = self.email

        phone = self.phone

        currency = self.currency

        comment = self.comment

        default_address_id = self.default_address_id

        addresses: Unset | list[dict[str, Any]] = UNSET
        if not isinstance(self.addresses, Unset):
            addresses = []
            for addresses_item_data in self.addresses:
                addresses_item = addresses_item_data.to_dict()
                addresses.append(addresses_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
            }
        )
        if created_at is not UNSET:
            field_dict["created_at"] = created_at
        if updated_at is not UNSET:
            field_dict["updated_at"] = updated_at
        if deleted_at is not UNSET:
            field_dict["deleted_at"] = deleted_at
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
        if default_address_id is not UNSET:
            field_dict["default_address_id"] = default_address_id
        if addresses is not UNSET:
            field_dict["addresses"] = addresses

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.supplier_address import SupplierAddress

        d = dict(src_dict)
        id = d.pop("id")

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

        name = d.pop("name", UNSET)

        email = d.pop("email", UNSET)

        phone = d.pop("phone", UNSET)

        currency = d.pop("currency", UNSET)

        comment = d.pop("comment", UNSET)

        default_address_id = d.pop("default_address_id", UNSET)

        addresses = []
        _addresses = d.pop("addresses", UNSET)
        for addresses_item_data in _addresses or []:
            addresses_item = SupplierAddress.from_dict(addresses_item_data)

            addresses.append(addresses_item)

        supplier = cls(
            id=id,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
            name=name,
            email=email,
            phone=phone,
            currency=currency,
            comment=comment,
            default_address_id=default_address_id,
            addresses=addresses,
        )

        supplier.additional_properties = d
        return supplier

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
