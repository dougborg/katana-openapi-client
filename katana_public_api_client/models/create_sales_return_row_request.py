from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="CreateSalesReturnRowRequest")


@_attrs_define
class CreateSalesReturnRowRequest:
    """Request payload for creating a new sales return row with product and quantity information"""

    sales_return_id: int
    variant_id: int
    fulfillment_row_id: int
    quantity: str
    restock_location_id: int | Unset = UNSET
    reason_id: int | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        sales_return_id = self.sales_return_id

        variant_id = self.variant_id

        fulfillment_row_id = self.fulfillment_row_id

        quantity = self.quantity

        restock_location_id = self.restock_location_id

        reason_id = self.reason_id

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "sales_return_id": sales_return_id,
                "variant_id": variant_id,
                "fulfillment_row_id": fulfillment_row_id,
                "quantity": quantity,
            }
        )
        if restock_location_id is not UNSET:
            field_dict["restock_location_id"] = restock_location_id
        if reason_id is not UNSET:
            field_dict["reason_id"] = reason_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        sales_return_id = d.pop("sales_return_id")

        variant_id = d.pop("variant_id")

        fulfillment_row_id = d.pop("fulfillment_row_id")

        quantity = d.pop("quantity")

        restock_location_id = d.pop("restock_location_id", UNSET)

        reason_id = d.pop("reason_id", UNSET)

        create_sales_return_row_request = cls(
            sales_return_id=sales_return_id,
            variant_id=variant_id,
            fulfillment_row_id=fulfillment_row_id,
            quantity=quantity,
            restock_location_id=restock_location_id,
            reason_id=reason_id,
        )

        return create_sales_return_row_request
