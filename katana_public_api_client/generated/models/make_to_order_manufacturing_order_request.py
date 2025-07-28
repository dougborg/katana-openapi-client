from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="MakeToOrderManufacturingOrderRequest")


@_attrs_define
class MakeToOrderManufacturingOrderRequest:
    sales_order_row_id: float
    create_subassemblies: Unset | bool = False

    def to_dict(self) -> dict[str, Any]:
        sales_order_row_id = self.sales_order_row_id

        create_subassemblies = self.create_subassemblies

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "sales_order_row_id": sales_order_row_id,
            }
        )
        if create_subassemblies is not UNSET:
            field_dict["create_subassemblies"] = create_subassemblies

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        sales_order_row_id = d.pop("sales_order_row_id")

        create_subassemblies = d.pop("create_subassemblies", UNSET)

        make_to_order_manufacturing_order_request = cls(
            sales_order_row_id=sales_order_row_id,
            create_subassemblies=create_subassemblies,
        )

        return make_to_order_manufacturing_order_request
