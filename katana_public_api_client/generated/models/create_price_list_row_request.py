from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreatePriceListRowRequest")


@_attrs_define
class CreatePriceListRowRequest:
    price_list_id: int
    variant_id: int
    price: float
    currency: Unset | str = UNSET

    def to_dict(self) -> dict[str, Any]:
        price_list_id = self.price_list_id

        variant_id = self.variant_id

        price = self.price

        currency = self.currency

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "price_list_id": price_list_id,
                "variant_id": variant_id,
                "price": price,
            }
        )
        if currency is not UNSET:
            field_dict["currency"] = currency

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        price_list_id = d.pop("price_list_id")

        variant_id = d.pop("variant_id")

        price = d.pop("price")

        currency = d.pop("currency", UNSET)

        create_price_list_row_request = cls(
            price_list_id=price_list_id,
            variant_id=variant_id,
            price=price,
            currency=currency,
        )

        return create_price_list_row_request
