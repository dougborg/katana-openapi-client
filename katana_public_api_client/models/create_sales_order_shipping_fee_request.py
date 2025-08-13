from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="CreateSalesOrderShippingFeeRequest")


@_attrs_define
class CreateSalesOrderShippingFeeRequest:
    """Request payload for adding a shipping fee to an existing sales order

    Example:
        {'sales_order_id': 2001, 'amount': 25.99, 'description': 'Express Shipping - Next Day Delivery', 'tax_rate_id':
            301}
    """

    sales_order_id: int
    amount: float
    description: Unset | str = UNSET
    tax_rate_id: Unset | int = UNSET

    def to_dict(self) -> dict[str, Any]:
        sales_order_id = self.sales_order_id

        amount = self.amount

        description = self.description

        tax_rate_id = self.tax_rate_id

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "sales_order_id": sales_order_id,
                "amount": amount,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if tax_rate_id is not UNSET:
            field_dict["tax_rate_id"] = tax_rate_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        sales_order_id = d.pop("sales_order_id")

        amount = d.pop("amount")

        description = d.pop("description", UNSET)

        tax_rate_id = d.pop("tax_rate_id", UNSET)

        create_sales_order_shipping_fee_request = cls(
            sales_order_id=sales_order_id,
            amount=amount,
            description=description,
            tax_rate_id=tax_rate_id,
        )

        return create_sales_order_shipping_fee_request
