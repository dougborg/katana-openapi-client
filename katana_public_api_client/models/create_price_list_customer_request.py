from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

if TYPE_CHECKING:
    from ..models.create_price_list_customer_request_price_list_customers_item import (
        CreatePriceListCustomerRequestPriceListCustomersItem,
    )


T = TypeVar("T", bound="CreatePriceListCustomerRequest")


@_attrs_define
class CreatePriceListCustomerRequest:
    """Request payload for assigning customers to a price list for custom pricing

    Example:
        {'price_list_id': 1002, 'price_list_customers': [{'customer_id': 2002}]}
    """

    price_list_id: int
    price_list_customers: list[CreatePriceListCustomerRequestPriceListCustomersItem]

    def to_dict(self) -> dict[str, Any]:
        price_list_id = self.price_list_id

        price_list_customers = []
        for price_list_customers_item_data in self.price_list_customers:
            price_list_customers_item = price_list_customers_item_data.to_dict()
            price_list_customers.append(price_list_customers_item)

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "price_list_id": price_list_id,
                "price_list_customers": price_list_customers,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.create_price_list_customer_request_price_list_customers_item import (
            CreatePriceListCustomerRequestPriceListCustomersItem,
        )

        d = dict(src_dict)
        price_list_id = d.pop("price_list_id")

        price_list_customers = []
        _price_list_customers = d.pop("price_list_customers")
        for price_list_customers_item_data in _price_list_customers:
            price_list_customers_item = (
                CreatePriceListCustomerRequestPriceListCustomersItem.from_dict(
                    price_list_customers_item_data
                )
            )

            price_list_customers.append(price_list_customers_item)

        create_price_list_customer_request = cls(
            price_list_id=price_list_id,
            price_list_customers=price_list_customers,
        )

        return create_price_list_customer_request
