from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="UpdateSalesReturnRowBody")


@_attrs_define
class UpdateSalesReturnRowBody:
    """
    Attributes:
        quantity (Union[Unset, float]): Quantity being returned
        reason (Union[Unset, str]): Reason for return
        notes (Union[Unset, str]): Additional notes
    """

    quantity: Unset | float = UNSET
    reason: Unset | str = UNSET
    notes: Unset | str = UNSET

    def to_dict(self) -> dict[str, Any]:
        quantity = self.quantity

        reason = self.reason

        notes = self.notes

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if quantity is not UNSET:
            field_dict["quantity"] = quantity
        if reason is not UNSET:
            field_dict["reason"] = reason
        if notes is not UNSET:
            field_dict["notes"] = notes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        quantity = d.pop("quantity", UNSET)

        reason = d.pop("reason", UNSET)

        notes = d.pop("notes", UNSET)

        update_sales_return_row_body = cls(
            quantity=quantity,
            reason=reason,
            notes=notes,
        )

        return update_sales_return_row_body
