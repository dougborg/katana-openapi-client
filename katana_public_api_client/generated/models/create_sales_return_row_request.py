from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateSalesReturnRowRequest")


@_attrs_define
class CreateSalesReturnRowRequest:
    variant_id: int
    quantity: float
    return_reason_id: Unset | int = UNSET
    notes: Unset | str = UNSET

    def to_dict(self) -> dict[str, Any]:
        variant_id = self.variant_id

        quantity = self.quantity

        return_reason_id = self.return_reason_id

        notes = self.notes

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "variant_id": variant_id,
                "quantity": quantity,
            }
        )
        if return_reason_id is not UNSET:
            field_dict["return_reason_id"] = return_reason_id
        if notes is not UNSET:
            field_dict["notes"] = notes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        variant_id = d.pop("variant_id")

        quantity = d.pop("quantity")

        return_reason_id = d.pop("return_reason_id", UNSET)

        notes = d.pop("notes", UNSET)

        create_sales_return_row_request = cls(
            variant_id=variant_id,
            quantity=quantity,
            return_reason_id=return_reason_id,
            notes=notes,
        )

        return create_sales_return_row_request
