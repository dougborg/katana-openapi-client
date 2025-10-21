from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="UpdateSalesOrderShippingFeeBody")


@_attrs_define
class UpdateSalesOrderShippingFeeBody:
    amount: Unset | float = UNSET
    description: Unset | str = UNSET

    def to_dict(self) -> dict[str, Any]:
        amount = self.amount

        description = self.description

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if amount is not UNSET:
            field_dict["amount"] = amount
        if description is not UNSET:
            field_dict["description"] = description

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        amount = d.pop("amount", UNSET)

        description = d.pop("description", UNSET)

        update_sales_order_shipping_fee_body = cls(
            amount=amount,
            description=description,
        )

        return update_sales_order_shipping_fee_body
