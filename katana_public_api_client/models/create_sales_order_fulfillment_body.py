from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="CreateSalesOrderFulfillmentBody")


@_attrs_define
class CreateSalesOrderFulfillmentBody:
    sales_order_id: int
    tracking_number: Unset | str = UNSET
    notes: Unset | str = UNSET

    def to_dict(self) -> dict[str, Any]:
        sales_order_id = self.sales_order_id

        tracking_number = self.tracking_number

        notes = self.notes

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "sales_order_id": sales_order_id,
            }
        )
        if tracking_number is not UNSET:
            field_dict["tracking_number"] = tracking_number
        if notes is not UNSET:
            field_dict["notes"] = notes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        sales_order_id = d.pop("sales_order_id")

        tracking_number = d.pop("tracking_number", UNSET)

        notes = d.pop("notes", UNSET)

        create_sales_order_fulfillment_body = cls(
            sales_order_id=sales_order_id,
            tracking_number=tracking_number,
            notes=notes,
        )

        return create_sales_order_fulfillment_body
