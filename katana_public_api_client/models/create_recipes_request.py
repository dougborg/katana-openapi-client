from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.create_recipes_request_rows_item import CreateRecipesRequestRowsItem


T = TypeVar("T", bound="CreateRecipesRequest")


@_attrs_define
class CreateRecipesRequest:
    """Request payload for creating recipe rows (deprecated in favor of BOM rows)

    Example:
        {'keep_current_rows': True, 'rows': [{'ingredient_variant_id': 1001, 'product_variant_id': 2001, 'quantity':
            2.5, 'notes': 'Primary ingredient'}]}

    Attributes:
        rows (list['CreateRecipesRequestRowsItem']): Array of recipe rows to create
        keep_current_rows (Union[Unset, bool]): Existing ingredient lines are kept by default, and new lines will be
            added to existing
            product recipes. Set to false to delete all existing ingredient lines for related
            products and add the ingredients as new recipes.
    """

    rows: list["CreateRecipesRequestRowsItem"]
    keep_current_rows: Unset | bool = UNSET

    def to_dict(self) -> dict[str, Any]:
        rows = []
        for rows_item_data in self.rows:
            rows_item = rows_item_data.to_dict()
            rows.append(rows_item)

        keep_current_rows = self.keep_current_rows

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "rows": rows,
            }
        )
        if keep_current_rows is not UNSET:
            field_dict["keep_current_rows"] = keep_current_rows

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.create_recipes_request_rows_item import (
            CreateRecipesRequestRowsItem,
        )

        d = dict(src_dict)
        rows = []
        _rows = d.pop("rows")
        for rows_item_data in _rows:
            rows_item = CreateRecipesRequestRowsItem.from_dict(rows_item_data)

            rows.append(rows_item)

        keep_current_rows = d.pop("keep_current_rows", UNSET)

        create_recipes_request = cls(
            rows=rows,
            keep_current_rows=keep_current_rows,
        )

        return create_recipes_request
