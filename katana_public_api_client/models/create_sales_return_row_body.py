from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="CreateSalesReturnRowBody")


@_attrs_define
class CreateSalesReturnRowBody:
    """
    Attributes:
        sales_return_id (int): Sales return ID
        variant_id (int): Product variant ID
        quantity (float): Quantity being returned
        reason (Union[Unset, str]): Reason for return
        notes (Union[Unset, str]): Additional notes
    """

    sales_return_id: int
    variant_id: int
    quantity: float
    reason: Unset | str = UNSET
    notes: Unset | str = UNSET

    def to_dict(self) -> dict[str, Any]:
        sales_return_id = self.sales_return_id

        variant_id = self.variant_id

        quantity = self.quantity

        reason = self.reason

        notes = self.notes

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "sales_return_id": sales_return_id,
                "variant_id": variant_id,
                "quantity": quantity,
            }
        )
        if reason is not UNSET:
            field_dict["reason"] = reason
        if notes is not UNSET:
            field_dict["notes"] = notes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        sales_return_id = d.pop("sales_return_id")

        variant_id = d.pop("variant_id")

        quantity = d.pop("quantity")

        reason = d.pop("reason", UNSET)

        notes = d.pop("notes", UNSET)

        create_sales_return_row_body = cls(
            sales_return_id=sales_return_id,
            variant_id=variant_id,
            quantity=quantity,
            reason=reason,
            notes=notes,
        )

        return create_sales_return_row_body
