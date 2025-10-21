from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="UpdateStockTransferBody")


@_attrs_define
class UpdateStockTransferBody:
    quantity: Unset | float = UNSET
    notes: Unset | str = UNSET

    def to_dict(self) -> dict[str, Any]:
        quantity = self.quantity

        notes = self.notes

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if quantity is not UNSET:
            field_dict["quantity"] = quantity
        if notes is not UNSET:
            field_dict["notes"] = notes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        quantity = d.pop("quantity", UNSET)

        notes = d.pop("notes", UNSET)

        update_stock_transfer_body = cls(
            quantity=quantity,
            notes=notes,
        )

        return update_stock_transfer_body
