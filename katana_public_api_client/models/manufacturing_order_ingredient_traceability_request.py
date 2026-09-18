from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="ManufacturingOrderIngredientTraceabilityRequest")


@_attrs_define
class ManufacturingOrderIngredientTraceabilityRequest:
    """Batch / bin allocation supplied on a manufacturing order recipe row
    or a production ingredient — the **input** side of manufacturing.
    Narrows ``TraceabilityRequest`` by dropping ``serial_number_id``:
    you are consuming ingredients from a batch in a bin, and serial
    attachment belongs to the produced output rather than the
    ingredient. Upstream models this as
    ``Omit<TraceabilityInputItemDto, 'serial_number_id'>`` and rejects
    the extra property.
    """

    batch_id: int | Unset | None = UNSET
    bin_location_id: int | Unset | None = UNSET
    quantity: float | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        batch_id: int | Unset | None
        if isinstance(self.batch_id, Unset):
            batch_id = UNSET
        else:
            batch_id = self.batch_id

        bin_location_id: int | Unset | None
        if isinstance(self.bin_location_id, Unset):
            bin_location_id = UNSET
        else:
            bin_location_id = self.bin_location_id

        quantity = self.quantity

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if batch_id is not UNSET:
            field_dict["batch_id"] = batch_id
        if bin_location_id is not UNSET:
            field_dict["bin_location_id"] = bin_location_id
        if quantity is not UNSET:
            field_dict["quantity"] = quantity

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_batch_id(data: object) -> int | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | Unset | None, data)

        batch_id = _parse_batch_id(d.pop("batch_id", UNSET))

        def _parse_bin_location_id(data: object) -> int | Unset | None:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | Unset | None, data)

        bin_location_id = _parse_bin_location_id(d.pop("bin_location_id", UNSET))

        quantity = d.pop("quantity", UNSET)

        manufacturing_order_ingredient_traceability_request = cls(
            batch_id=batch_id,
            bin_location_id=bin_location_id,
            quantity=quantity,
        )

        return manufacturing_order_ingredient_traceability_request
