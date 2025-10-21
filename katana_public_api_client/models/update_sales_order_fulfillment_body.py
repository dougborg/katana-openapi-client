from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="UpdateSalesOrderFulfillmentBody")


@_attrs_define
class UpdateSalesOrderFulfillmentBody:
    """
    Attributes:
        tracking_number (Union[Unset, str]): Shipment tracking number
        notes (Union[Unset, str]): Additional notes for the fulfillment
    """

    tracking_number: Unset | str = UNSET
    notes: Unset | str = UNSET

    def to_dict(self) -> dict[str, Any]:
        tracking_number = self.tracking_number

        notes = self.notes

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if tracking_number is not UNSET:
            field_dict["tracking_number"] = tracking_number
        if notes is not UNSET:
            field_dict["notes"] = notes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        tracking_number = d.pop("tracking_number", UNSET)

        notes = d.pop("notes", UNSET)

        update_sales_order_fulfillment_body = cls(
            tracking_number=tracking_number,
            notes=notes,
        )

        return update_sales_order_fulfillment_body
