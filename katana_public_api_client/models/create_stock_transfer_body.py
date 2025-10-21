from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="CreateStockTransferBody")


@_attrs_define
class CreateStockTransferBody:
    """
    Attributes:
        from_location_id (int): Source location ID
        to_location_id (int): Destination location ID
        variant_id (int): Product variant ID
        quantity (float): Quantity to transfer
        notes (Union[Unset, str]): Transfer notes
    """

    from_location_id: int
    to_location_id: int
    variant_id: int
    quantity: float
    notes: Unset | str = UNSET

    def to_dict(self) -> dict[str, Any]:
        from_location_id = self.from_location_id

        to_location_id = self.to_location_id

        variant_id = self.variant_id

        quantity = self.quantity

        notes = self.notes

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "from_location_id": from_location_id,
                "to_location_id": to_location_id,
                "variant_id": variant_id,
                "quantity": quantity,
            }
        )
        if notes is not UNSET:
            field_dict["notes"] = notes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        from_location_id = d.pop("from_location_id")

        to_location_id = d.pop("to_location_id")

        variant_id = d.pop("variant_id")

        quantity = d.pop("quantity")

        notes = d.pop("notes", UNSET)

        create_stock_transfer_body = cls(
            from_location_id=from_location_id,
            to_location_id=to_location_id,
            variant_id=variant_id,
            quantity=quantity,
            notes=notes,
        )

        return create_stock_transfer_body
