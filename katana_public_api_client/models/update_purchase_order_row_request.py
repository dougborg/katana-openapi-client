from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.update_purchase_order_row_request_custom_fields_type_0 import (
        UpdatePurchaseOrderRowRequestCustomFieldsType0,
    )


T = TypeVar("T", bound="UpdatePurchaseOrderRowRequest")


@_attrs_define
class UpdatePurchaseOrderRowRequest:
    """Request payload for updating an existing purchase order line item's details and status

    Example:
        {'quantity': 275, 'price_per_unit': 2.95, 'purchase_uom': 'kg', 'received_date': '2024-02-15T14:30:00Z',
            'arrival_date': '2024-02-15T10:00:00Z'}
    """

    custom_fields: Unset | UpdatePurchaseOrderRowRequestCustomFieldsType0 | None = UNSET
    quantity: float | Unset = UNSET
    variant_id: int | Unset = UNSET
    tax_rate_id: int | Unset = UNSET
    tax_name: str | Unset = UNSET
    tax_rate: str | Unset = UNSET
    price_per_unit: float | Unset = UNSET
    purchase_uom_conversion_rate: float | Unset = UNSET
    purchase_uom: str | Unset = UNSET
    received_date: datetime.datetime | Unset = UNSET
    arrival_date: datetime.datetime | Unset = UNSET
    location_id: int | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        from ..models.update_purchase_order_row_request_custom_fields_type_0 import (
            UpdatePurchaseOrderRowRequestCustomFieldsType0,
        )

        custom_fields: dict[str, Any] | Unset | None
        if isinstance(self.custom_fields, Unset):
            custom_fields = UNSET
        elif isinstance(
            self.custom_fields, UpdatePurchaseOrderRowRequestCustomFieldsType0
        ):
            custom_fields = self.custom_fields.to_dict()
        else:
            custom_fields = self.custom_fields

        quantity = self.quantity

        variant_id = self.variant_id

        tax_rate_id = self.tax_rate_id

        tax_name = self.tax_name

        tax_rate = self.tax_rate

        price_per_unit = self.price_per_unit

        purchase_uom_conversion_rate = self.purchase_uom_conversion_rate

        purchase_uom = self.purchase_uom

        received_date: str | Unset = UNSET
        if not isinstance(self.received_date, Unset):
            received_date = self.received_date.isoformat()

        arrival_date: str | Unset = UNSET
        if not isinstance(self.arrival_date, Unset):
            arrival_date = self.arrival_date.isoformat()

        location_id = self.location_id

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if custom_fields is not UNSET:
            field_dict["custom_fields"] = custom_fields
        if quantity is not UNSET:
            field_dict["quantity"] = quantity
        if variant_id is not UNSET:
            field_dict["variant_id"] = variant_id
        if tax_rate_id is not UNSET:
            field_dict["tax_rate_id"] = tax_rate_id
        if tax_name is not UNSET:
            field_dict["tax_name"] = tax_name
        if tax_rate is not UNSET:
            field_dict["tax_rate"] = tax_rate
        if price_per_unit is not UNSET:
            field_dict["price_per_unit"] = price_per_unit
        if purchase_uom_conversion_rate is not UNSET:
            field_dict["purchase_uom_conversion_rate"] = purchase_uom_conversion_rate
        if purchase_uom is not UNSET:
            field_dict["purchase_uom"] = purchase_uom
        if received_date is not UNSET:
            field_dict["received_date"] = received_date
        if arrival_date is not UNSET:
            field_dict["arrival_date"] = arrival_date
        if location_id is not UNSET:
            field_dict["location_id"] = location_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.update_purchase_order_row_request_custom_fields_type_0 import (
            UpdatePurchaseOrderRowRequestCustomFieldsType0,
        )

        d = dict(src_dict)

        def _parse_custom_fields(
            data: object,
        ) -> Unset | UpdatePurchaseOrderRowRequestCustomFieldsType0 | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                custom_fields_type_0 = (
                    UpdatePurchaseOrderRowRequestCustomFieldsType0.from_dict(
                        cast(Mapping[str, Any], data)
                    )
                )

                return custom_fields_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(
                Unset | UpdatePurchaseOrderRowRequestCustomFieldsType0 | None, data
            )

        custom_fields = _parse_custom_fields(d.pop("custom_fields", UNSET))

        quantity = d.pop("quantity", UNSET)

        variant_id = d.pop("variant_id", UNSET)

        tax_rate_id = d.pop("tax_rate_id", UNSET)

        tax_name = d.pop("tax_name", UNSET)

        tax_rate = d.pop("tax_rate", UNSET)

        price_per_unit = d.pop("price_per_unit", UNSET)

        purchase_uom_conversion_rate = d.pop("purchase_uom_conversion_rate", UNSET)

        purchase_uom = d.pop("purchase_uom", UNSET)

        _received_date = d.pop("received_date", UNSET)
        received_date: datetime.datetime | Unset
        if isinstance(_received_date, Unset):
            received_date = UNSET
        else:
            received_date = datetime.datetime.fromisoformat(_received_date)

        _arrival_date = d.pop("arrival_date", UNSET)
        arrival_date: datetime.datetime | Unset
        if isinstance(_arrival_date, Unset):
            arrival_date = UNSET
        else:
            arrival_date = datetime.datetime.fromisoformat(_arrival_date)

        location_id = d.pop("location_id", UNSET)

        update_purchase_order_row_request = cls(
            custom_fields=custom_fields,
            quantity=quantity,
            variant_id=variant_id,
            tax_rate_id=tax_rate_id,
            tax_name=tax_name,
            tax_rate=tax_rate,
            price_per_unit=price_per_unit,
            purchase_uom_conversion_rate=purchase_uom_conversion_rate,
            purchase_uom=purchase_uom,
            received_date=received_date,
            arrival_date=arrival_date,
            location_id=location_id,
        )

        return update_purchase_order_row_request
