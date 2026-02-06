from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

if TYPE_CHECKING:
    from ..models.create_stocktake_row_request_stocktake_rows_item import (
        CreateStocktakeRowRequestStocktakeRowsItem,
    )


T = TypeVar("T", bound="CreateStocktakeRowRequest")


@_attrs_define
class CreateStocktakeRowRequest:
    """Request payload for creating stocktake rows for counting specific variants

    Example:
        {'stocktake_id': 4001, 'stocktake_rows': [{'variant_id': 3001, 'counted_quantity': 147.0, 'notes': 'Initial
            count'}]}
    """

    stocktake_id: int
    stocktake_rows: list[CreateStocktakeRowRequestStocktakeRowsItem]

    def to_dict(self) -> dict[str, Any]:
        stocktake_id = self.stocktake_id

        stocktake_rows = []
        for stocktake_rows_item_data in self.stocktake_rows:
            stocktake_rows_item = stocktake_rows_item_data.to_dict()
            stocktake_rows.append(stocktake_rows_item)

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "stocktake_id": stocktake_id,
                "stocktake_rows": stocktake_rows,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.create_stocktake_row_request_stocktake_rows_item import (
            CreateStocktakeRowRequestStocktakeRowsItem,
        )

        d = dict(src_dict)
        stocktake_id = d.pop("stocktake_id")

        stocktake_rows = []
        _stocktake_rows = d.pop("stocktake_rows")
        for stocktake_rows_item_data in _stocktake_rows:
            stocktake_rows_item = CreateStocktakeRowRequestStocktakeRowsItem.from_dict(
                stocktake_rows_item_data
            )

            stocktake_rows.append(stocktake_rows_item)

        create_stocktake_row_request = cls(
            stocktake_id=stocktake_id,
            stocktake_rows=stocktake_rows,
        )

        return create_stocktake_row_request
