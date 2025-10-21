from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="UpdateStocktakeRowRequest")


@_attrs_define
class UpdateStocktakeRowRequest:
    """Request payload for updating an existing stocktake row

    Example:
        {'actual_quantity': 148.0, 'variance_quantity': -2.0, 'notes': 'Recount confirmed minor variance'}

    Attributes:
        stocktake_id (Union[Unset, int]): ID of the stocktake this row belongs to
        variant_id (Union[Unset, int]): ID of the variant being counted
        batch_id (Union[Unset, int]): ID of the specific batch being counted (if applicable)
        system_quantity (Union[Unset, float]): System recorded quantity before counting
        actual_quantity (Union[Unset, float]): Actual counted quantity
        variance_quantity (Union[Unset, float]): Calculated variance between system and actual quantity
        notes (Union[Unset, str]): Optional notes about the count
    """

    stocktake_id: Unset | int = UNSET
    variant_id: Unset | int = UNSET
    batch_id: Unset | int = UNSET
    system_quantity: Unset | float = UNSET
    actual_quantity: Unset | float = UNSET
    variance_quantity: Unset | float = UNSET
    notes: Unset | str = UNSET

    def to_dict(self) -> dict[str, Any]:
        stocktake_id = self.stocktake_id

        variant_id = self.variant_id

        batch_id = self.batch_id

        system_quantity = self.system_quantity

        actual_quantity = self.actual_quantity

        variance_quantity = self.variance_quantity

        notes = self.notes

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if stocktake_id is not UNSET:
            field_dict["stocktake_id"] = stocktake_id
        if variant_id is not UNSET:
            field_dict["variant_id"] = variant_id
        if batch_id is not UNSET:
            field_dict["batch_id"] = batch_id
        if system_quantity is not UNSET:
            field_dict["system_quantity"] = system_quantity
        if actual_quantity is not UNSET:
            field_dict["actual_quantity"] = actual_quantity
        if variance_quantity is not UNSET:
            field_dict["variance_quantity"] = variance_quantity
        if notes is not UNSET:
            field_dict["notes"] = notes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        stocktake_id = d.pop("stocktake_id", UNSET)

        variant_id = d.pop("variant_id", UNSET)

        batch_id = d.pop("batch_id", UNSET)

        system_quantity = d.pop("system_quantity", UNSET)

        actual_quantity = d.pop("actual_quantity", UNSET)

        variance_quantity = d.pop("variance_quantity", UNSET)

        notes = d.pop("notes", UNSET)

        update_stocktake_row_request = cls(
            stocktake_id=stocktake_id,
            variant_id=variant_id,
            batch_id=batch_id,
            system_quantity=system_quantity,
            actual_quantity=actual_quantity,
            variance_quantity=variance_quantity,
            notes=notes,
        )

        return update_stocktake_row_request
