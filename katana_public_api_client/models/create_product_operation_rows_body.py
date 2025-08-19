from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.create_product_operation_rows_body_rows_item import (
        CreateProductOperationRowsBodyRowsItem,
    )


T = TypeVar("T", bound="CreateProductOperationRowsBody")


@_attrs_define
class CreateProductOperationRowsBody:
    rows: list["CreateProductOperationRowsBodyRowsItem"]
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
        from ..models.create_product_operation_rows_body_rows_item import (
            CreateProductOperationRowsBodyRowsItem,
        )

        d = dict(src_dict)
        rows = []
        _rows = d.pop("rows")
        for rows_item_data in _rows:
            rows_item = CreateProductOperationRowsBodyRowsItem.from_dict(rows_item_data)

            rows.append(rows_item)

        keep_current_rows = d.pop("keep_current_rows", UNSET)

        create_product_operation_rows_body = cls(
            rows=rows,
            keep_current_rows=keep_current_rows,
        )

        return create_product_operation_rows_body
