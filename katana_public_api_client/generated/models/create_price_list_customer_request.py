from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="CreatePriceListCustomerRequest")


@_attrs_define
class CreatePriceListCustomerRequest:
    price_list_id: int
    customer_id: int

    def to_dict(self) -> dict[str, Any]:
        price_list_id = self.price_list_id

        customer_id = self.customer_id

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "price_list_id": price_list_id,
                "customer_id": customer_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        price_list_id = d.pop("price_list_id")

        customer_id = d.pop("customer_id")

        create_price_list_customer_request = cls(
            price_list_id=price_list_id,
            customer_id=customer_id,
        )

        return create_price_list_customer_request
