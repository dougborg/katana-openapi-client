from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="UpdatePriceListRowRequest")


@_attrs_define
class UpdatePriceListRowRequest:
    """Request payload for updating an existing price list row

    Example:
        {'price': 259.99, 'currency': 'USD'}
    """

    price_list_id: Unset | int = UNSET
    variant_id: Unset | int = UNSET
    price: Unset | float = UNSET
    currency: Unset | str = UNSET

    def to_dict(self) -> dict[str, Any]:
        price_list_id = self.price_list_id

        variant_id = self.variant_id

        price = self.price

        currency = self.currency

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if price_list_id is not UNSET:
            field_dict["price_list_id"] = price_list_id
        if variant_id is not UNSET:
            field_dict["variant_id"] = variant_id
        if price is not UNSET:
            field_dict["price"] = price
        if currency is not UNSET:
            field_dict["currency"] = currency

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        price_list_id = d.pop("price_list_id", UNSET)

        variant_id = d.pop("variant_id", UNSET)

        price = d.pop("price", UNSET)

        currency = d.pop("currency", UNSET)

        update_price_list_row_request = cls(
            price_list_id=price_list_id,
            variant_id=variant_id,
            price=price,
            currency=currency,
        )

        return update_price_list_row_request
