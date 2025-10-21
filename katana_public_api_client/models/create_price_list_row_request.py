from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="CreatePriceListRowRequest")


@_attrs_define
class CreatePriceListRowRequest:
    """Request payload for adding a product variant with specific pricing to a price list for customer-specific pricing
    management

        Example:
            {'price_list_id': 1001, 'variant_id': 201, 'price': 249.99, 'currency': 'USD'}

        Attributes:
            price_list_id (int): ID of the price list to add the variant pricing to
            variant_id (int): ID of the product variant to set custom pricing for
            price (float): Custom price for this variant in the price list's currency
            currency (Union[Unset, str]): ISO 4217 currency code (must match the price list's currency)
    """

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
