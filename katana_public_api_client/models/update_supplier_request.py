from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.update_supplier_request_custom_fields_type_0 import (
        UpdateSupplierRequestCustomFieldsType0,
    )


T = TypeVar("T", bound="UpdateSupplierRequest")


@_attrs_define
class UpdateSupplierRequest:
    """Request payload for updating an existing supplier's contact information and details

    Example:
        {'name': 'Premium Kitchen Supplies Ltd', 'email': 'orders@premiumkitchen.com', 'phone': '+1-555-0134',
            'currency': 'USD', 'comment': 'Primary supplier for kitchen equipment and utensils. Excellent customer
            service.'}
    """

    custom_fields: Unset | UpdateSupplierRequestCustomFieldsType0 | None = UNSET
    name: str | Unset = UNSET
    email: str | Unset = UNSET
    phone: str | Unset = UNSET
    currency: str | Unset = UNSET
    comment: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.update_supplier_request_custom_fields_type_0 import (
            UpdateSupplierRequestCustomFieldsType0,
        )

        custom_fields: dict[str, Any] | Unset | None
        if isinstance(self.custom_fields, Unset):
            custom_fields = UNSET
        elif isinstance(self.custom_fields, UpdateSupplierRequestCustomFieldsType0):
            custom_fields = self.custom_fields.to_dict()
        else:
            custom_fields = self.custom_fields

        name = self.name

        email = self.email

        phone = self.phone

        currency = self.currency

        comment = self.comment

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if custom_fields is not UNSET:
            field_dict["custom_fields"] = custom_fields
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
        from ..models.update_supplier_request_custom_fields_type_0 import (
            UpdateSupplierRequestCustomFieldsType0,
        )

        d = dict(src_dict)

        def _parse_custom_fields(
            data: object,
        ) -> Unset | UpdateSupplierRequestCustomFieldsType0 | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                custom_fields_type_0 = UpdateSupplierRequestCustomFieldsType0.from_dict(
                    cast(Mapping[str, Any], data)
                )

                return custom_fields_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(Unset | UpdateSupplierRequestCustomFieldsType0 | None, data)

        custom_fields = _parse_custom_fields(d.pop("custom_fields", UNSET))

        name = d.pop("name", UNSET)

        email = d.pop("email", UNSET)

        phone = d.pop("phone", UNSET)

        currency = d.pop("currency", UNSET)

        comment = d.pop("comment", UNSET)

        update_supplier_request = cls(
            custom_fields=custom_fields,
            name=name,
            email=email,
            phone=phone,
            currency=currency,
            comment=comment,
        )

        return update_supplier_request
