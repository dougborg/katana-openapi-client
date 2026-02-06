from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="UpdatePriceListCustomerRequest")


@_attrs_define
class UpdatePriceListCustomerRequest:
    """Request payload for updating an existing price list customer assignment

    Example:
        {'customer_id': 2003}
    """

    customer_id: int | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        customer_id = self.customer_id

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if customer_id is not UNSET:
            field_dict["customer_id"] = customer_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        customer_id = d.pop("customer_id", UNSET)

        update_price_list_customer_request = cls(
            customer_id=customer_id,
        )

        return update_price_list_customer_request
