from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="UpdatePriceListCustomerRequest")


@_attrs_define
class UpdatePriceListCustomerRequest:
    """Request payload for updating an existing price list customer assignment

    Example:
        {'price_list_id': 1003}

    Attributes:
        price_list_id (Union[Unset, int]): ID of the price list
        customer_id (Union[Unset, int]): ID of the customer to assign to price list
    """

    price_list_id: Unset | int = UNSET
    customer_id: Unset | int = UNSET

    def to_dict(self) -> dict[str, Any]:
        price_list_id = self.price_list_id

        customer_id = self.customer_id

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if price_list_id is not UNSET:
            field_dict["price_list_id"] = price_list_id
        if customer_id is not UNSET:
            field_dict["customer_id"] = customer_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        price_list_id = d.pop("price_list_id", UNSET)

        customer_id = d.pop("customer_id", UNSET)

        update_price_list_customer_request = cls(
            price_list_id=price_list_id,
            customer_id=customer_id,
        )

        return update_price_list_customer_request
