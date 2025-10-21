from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="SalesOrderShippingFee")


@_attrs_define
class SalesOrderShippingFee:
    """Shipping fee record associated with a sales order, tracking shipping costs and applicable taxes

    Example:
        {'id': 2801, 'sales_order_id': 2001, 'amount': 25.99, 'tax_rate_id': 301, 'description': 'UPS Ground Shipping'}
    """

    id: int
    sales_order_id: int
    amount: str
    tax_rate_id: Unset | int = UNSET
    description: None | Unset | str = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        sales_order_id = self.sales_order_id

        amount = self.amount

        tax_rate_id = self.tax_rate_id

        description: None | Unset | str
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "sales_order_id": sales_order_id,
                "amount": amount,
            }
        )
        if tax_rate_id is not UNSET:
            field_dict["tax_rate_id"] = tax_rate_id
        if description is not UNSET:
            field_dict["description"] = description

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        sales_order_id = d.pop("sales_order_id")

        amount = d.pop("amount")

        tax_rate_id = d.pop("tax_rate_id", UNSET)

        def _parse_description(data: object) -> None | Unset | str:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | Unset | str, data)

        description = _parse_description(d.pop("description", UNSET))

        sales_order_shipping_fee = cls(
            id=id,
            sales_order_id=sales_order_id,
            amount=amount,
            tax_rate_id=tax_rate_id,
            description=description,
        )

        sales_order_shipping_fee.additional_properties = d
        return sales_order_shipping_fee

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
