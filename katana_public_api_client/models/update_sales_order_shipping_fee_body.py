from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="UpdateSalesOrderShippingFeeBody")


@_attrs_define
class UpdateSalesOrderShippingFeeBody:
    description: str | Unset = UNSET
    amount: int | Unset = UNSET
    tax_rate_id: int | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        description = self.description

        amount = self.amount

        tax_rate_id = self.tax_rate_id

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if description is not UNSET:
            field_dict["description"] = description
        if amount is not UNSET:
            field_dict["amount"] = amount
        if tax_rate_id is not UNSET:
            field_dict["tax_rate_id"] = tax_rate_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        description = d.pop("description", UNSET)

        amount = d.pop("amount", UNSET)

        tax_rate_id = d.pop("tax_rate_id", UNSET)

        update_sales_order_shipping_fee_body = cls(
            description=description,
            amount=amount,
            tax_rate_id=tax_rate_id,
        )

        return update_sales_order_shipping_fee_body
