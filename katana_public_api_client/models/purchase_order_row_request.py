import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="PurchaseOrderRowRequest")


@_attrs_define
class PurchaseOrderRowRequest:
    """Request payload for creating a line item within a purchase order

    Example:
        {'quantity': 250, 'price_per_unit': 2.85, 'variant_id': 501, 'tax_rate_id': 1, 'purchase_uom': 'kg',
            'purchase_uom_conversion_rate': 1.0, 'arrival_date': '2024-08-20T14:45:00Z'}
    """

    quantity: float
    price_per_unit: float
    variant_id: int
    tax_rate_id: Unset | int = UNSET
    purchase_uom_conversion_rate: Unset | float = UNSET
    purchase_uom: Unset | str = UNSET
    arrival_date: Unset | datetime.datetime = UNSET

    def to_dict(self) -> dict[str, Any]:
        quantity = self.quantity

        price_per_unit = self.price_per_unit

        variant_id = self.variant_id

        tax_rate_id = self.tax_rate_id

        purchase_uom_conversion_rate = self.purchase_uom_conversion_rate

        purchase_uom = self.purchase_uom

        arrival_date: Unset | str = UNSET
        if not isinstance(self.arrival_date, Unset):
            arrival_date = self.arrival_date.isoformat()

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "quantity": quantity,
                "price_per_unit": price_per_unit,
                "variant_id": variant_id,
            }
        )
        if tax_rate_id is not UNSET:
            field_dict["tax_rate_id"] = tax_rate_id
        if purchase_uom_conversion_rate is not UNSET:
            field_dict["purchase_uom_conversion_rate"] = purchase_uom_conversion_rate
        if purchase_uom is not UNSET:
            field_dict["purchase_uom"] = purchase_uom
        if arrival_date is not UNSET:
            field_dict["arrival_date"] = arrival_date

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        quantity = d.pop("quantity")

        price_per_unit = d.pop("price_per_unit")

        variant_id = d.pop("variant_id")

        tax_rate_id = d.pop("tax_rate_id", UNSET)

        purchase_uom_conversion_rate = d.pop("purchase_uom_conversion_rate", UNSET)

        purchase_uom = d.pop("purchase_uom", UNSET)

        _arrival_date = d.pop("arrival_date", UNSET)
        arrival_date: Unset | datetime.datetime
        if isinstance(_arrival_date, Unset):
            arrival_date = UNSET
        else:
            arrival_date = isoparse(_arrival_date)

        purchase_order_row_request = cls(
            quantity=quantity,
            price_per_unit=price_per_unit,
            variant_id=variant_id,
            tax_rate_id=tax_rate_id,
            purchase_uom_conversion_rate=purchase_uom_conversion_rate,
            purchase_uom=purchase_uom,
            arrival_date=arrival_date,
        )

        return purchase_order_row_request
