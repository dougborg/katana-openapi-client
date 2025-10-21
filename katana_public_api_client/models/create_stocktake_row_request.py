from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="CreateStocktakeRowRequest")


@_attrs_define
class CreateStocktakeRowRequest:
    """Request payload for creating a new stocktake row for counting specific variants

    Example:
        {'stocktake_id': 4001, 'variant_id': 3001, 'system_quantity': 150.0, 'actual_quantity': 147.0, 'notes': 'Minor
            count difference noted'}
    """

    stocktake_id: int
    variant_id: int
    system_quantity: float
    batch_id: Unset | int = UNSET
    actual_quantity: Unset | float = UNSET
    notes: Unset | str = UNSET

    def to_dict(self) -> dict[str, Any]:
        stocktake_id = self.stocktake_id

        variant_id = self.variant_id

        system_quantity = self.system_quantity

        batch_id = self.batch_id

        actual_quantity = self.actual_quantity

        notes = self.notes

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "stocktake_id": stocktake_id,
                "variant_id": variant_id,
                "system_quantity": system_quantity,
            }
        )
        if batch_id is not UNSET:
            field_dict["batch_id"] = batch_id
        if actual_quantity is not UNSET:
            field_dict["actual_quantity"] = actual_quantity
        if notes is not UNSET:
            field_dict["notes"] = notes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        stocktake_id = d.pop("stocktake_id")

        variant_id = d.pop("variant_id")

        system_quantity = d.pop("system_quantity")

        batch_id = d.pop("batch_id", UNSET)

        actual_quantity = d.pop("actual_quantity", UNSET)

        notes = d.pop("notes", UNSET)

        create_stocktake_row_request = cls(
            stocktake_id=stocktake_id,
            variant_id=variant_id,
            system_quantity=system_quantity,
            batch_id=batch_id,
            actual_quantity=actual_quantity,
            notes=notes,
        )

        return create_stocktake_row_request
