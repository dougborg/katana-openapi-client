import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="CreatePurchaseOrderRowRequest")


@_attrs_define
class CreatePurchaseOrderRowRequest:
    """Request payload for adding a new line item to an existing purchase order

    Example:
        {'purchase_order_id': 156, 'quantity': 50, 'variant_id': 503, 'tax_rate_id': 1, 'group_id': 1, 'price_per_unit':
            8.75, 'purchase_uom_conversion_rate': 1.0, 'purchase_uom': 'pieces', 'arrival_date': '2024-02-15T10:00:00Z'}
    """

    purchase_order_id: int
    quantity: float
    variant_id: int
    price_per_unit: float
    tax_rate_id: Unset | int = UNSET
    group_id: Unset | int = UNSET
    purchase_uom_conversion_rate: Unset | float = UNSET
    purchase_uom: Unset | str = UNSET
    arrival_date: Unset | datetime.datetime = UNSET

    def to_dict(self) -> dict[str, Any]:
        purchase_order_id = self.purchase_order_id

        quantity = self.quantity

        variant_id = self.variant_id

        price_per_unit = self.price_per_unit

        tax_rate_id = self.tax_rate_id

        group_id = self.group_id

        purchase_uom_conversion_rate = self.purchase_uom_conversion_rate

        purchase_uom = self.purchase_uom

        arrival_date: Unset | str = UNSET
        if not isinstance(self.arrival_date, Unset):
            arrival_date = self.arrival_date.isoformat()

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "purchase_order_id": purchase_order_id,
                "quantity": quantity,
                "variant_id": variant_id,
                "price_per_unit": price_per_unit,
            }
        )
        if tax_rate_id is not UNSET:
            field_dict["tax_rate_id"] = tax_rate_id
        if group_id is not UNSET:
            field_dict["group_id"] = group_id
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
        purchase_order_id = d.pop("purchase_order_id")

        quantity = d.pop("quantity")

        variant_id = d.pop("variant_id")

        price_per_unit = d.pop("price_per_unit")

        tax_rate_id = d.pop("tax_rate_id", UNSET)

        group_id = d.pop("group_id", UNSET)

        purchase_uom_conversion_rate = d.pop("purchase_uom_conversion_rate", UNSET)

        purchase_uom = d.pop("purchase_uom", UNSET)

        _arrival_date = d.pop("arrival_date", UNSET)
        arrival_date: Unset | datetime.datetime
        if isinstance(_arrival_date, Unset):
            arrival_date = UNSET
        else:
            arrival_date = isoparse(_arrival_date)

        create_purchase_order_row_request = cls(
            purchase_order_id=purchase_order_id,
            quantity=quantity,
            variant_id=variant_id,
            price_per_unit=price_per_unit,
            tax_rate_id=tax_rate_id,
            group_id=group_id,
            purchase_uom_conversion_rate=purchase_uom_conversion_rate,
            purchase_uom=purchase_uom,
            arrival_date=arrival_date,
        )

        return create_purchase_order_row_request
