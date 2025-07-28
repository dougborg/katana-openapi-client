from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

T = TypeVar("T", bound="UnlinkManufacturingOrderRequest")


@_attrs_define
class UnlinkManufacturingOrderRequest:
    sales_order_row_id: float

    def to_dict(self) -> dict[str, Any]:
        sales_order_row_id = self.sales_order_row_id

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "sales_order_row_id": sales_order_row_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        sales_order_row_id = d.pop("sales_order_row_id")

        unlink_manufacturing_order_request = cls(
            sales_order_row_id=sales_order_row_id,
        )

        return unlink_manufacturing_order_request
