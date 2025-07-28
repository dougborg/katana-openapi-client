from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateSalesOrderShippingFeeRequest")


@_attrs_define
class CreateSalesOrderShippingFeeRequest:
    sales_order_id: int
    amount: float
    currency: Unset | str = UNSET
    description: Unset | str = UNSET

    def to_dict(self) -> dict[str, Any]:
        sales_order_id = self.sales_order_id

        amount = self.amount

        currency = self.currency

        description = self.description

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "sales_order_id": sales_order_id,
                "amount": amount,
            }
        )
        if currency is not UNSET:
            field_dict["currency"] = currency
        if description is not UNSET:
            field_dict["description"] = description

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        sales_order_id = d.pop("sales_order_id")

        amount = d.pop("amount")

        currency = d.pop("currency", UNSET)

        description = d.pop("description", UNSET)

        create_sales_order_shipping_fee_request = cls(
            sales_order_id=sales_order_id,
            amount=amount,
            currency=currency,
            description=description,
        )

        return create_sales_order_shipping_fee_request
