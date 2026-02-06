from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

if TYPE_CHECKING:
    from ..models.create_price_list_row_request_price_list_rows_item import (
        CreatePriceListRowRequestPriceListRowsItem,
    )


T = TypeVar("T", bound="CreatePriceListRowRequest")


@_attrs_define
class CreatePriceListRowRequest:
    """Request payload for adding product variants with specific pricing to a price list

    Example:
        {'price_list_id': 1001, 'price_list_rows': [{'variant_id': 201, 'adjustment_method': 'fixed', 'amount':
            249.99}]}
    """

    price_list_id: int
    price_list_rows: list[CreatePriceListRowRequestPriceListRowsItem]

    def to_dict(self) -> dict[str, Any]:
        price_list_id = self.price_list_id

        price_list_rows = []
        for price_list_rows_item_data in self.price_list_rows:
            price_list_rows_item = price_list_rows_item_data.to_dict()
            price_list_rows.append(price_list_rows_item)

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "price_list_id": price_list_id,
                "price_list_rows": price_list_rows,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.create_price_list_row_request_price_list_rows_item import (
            CreatePriceListRowRequestPriceListRowsItem,
        )

        d = dict(src_dict)
        price_list_id = d.pop("price_list_id")

        price_list_rows = []
        _price_list_rows = d.pop("price_list_rows")
        for price_list_rows_item_data in _price_list_rows:
            price_list_rows_item = CreatePriceListRowRequestPriceListRowsItem.from_dict(
                price_list_rows_item_data
            )

            price_list_rows.append(price_list_rows_item)

        create_price_list_row_request = cls(
            price_list_id=price_list_id,
            price_list_rows=price_list_rows,
        )

        return create_price_list_row_request
