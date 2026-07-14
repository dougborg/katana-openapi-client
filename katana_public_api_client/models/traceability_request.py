from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="TraceabilityRequest")


@_attrs_define
class TraceabilityRequest:
    """Batch / serial / bin allocation supplied on a create-or-update row to
    trace the moved quantity to a specific batch, serial number, and/or
    bin location. Mirrors Katana's ``TraceabilityInputItemDto`` — the
    unified traceability input that supersedes the older per-entity
    ``serial_numbers`` arrays for attaching serial-tracked units to a row.

    Any axis may be null; a non-null ``serial_number_id`` attaches (or
    draws from) that serial number for the allocated ``quantity``. Katana
    marks ``quantity`` required on stock-adjustment traceability rows and
    treats it as the per-allocation amount everywhere else, so it is
    modelled as optional here to accept every valid payload shape.
    """

    batch_id: int | None | Unset = UNSET
    bin_location_id: int | None | Unset = UNSET
    serial_number_id: int | None | Unset = UNSET
    quantity: float | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        batch_id: int | None | Unset
        if isinstance(self.batch_id, Unset):
            batch_id = UNSET
        else:
            batch_id = self.batch_id

        bin_location_id: int | None | Unset
        if isinstance(self.bin_location_id, Unset):
            bin_location_id = UNSET
        else:
            bin_location_id = self.bin_location_id

        serial_number_id: int | None | Unset
        if isinstance(self.serial_number_id, Unset):
            serial_number_id = UNSET
        else:
            serial_number_id = self.serial_number_id

        quantity = self.quantity

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if batch_id is not UNSET:
            field_dict["batch_id"] = batch_id
        if bin_location_id is not UNSET:
            field_dict["bin_location_id"] = bin_location_id
        if serial_number_id is not UNSET:
            field_dict["serial_number_id"] = serial_number_id
        if quantity is not UNSET:
            field_dict["quantity"] = quantity

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)

        def _parse_batch_id(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        batch_id = _parse_batch_id(d.pop("batch_id", UNSET))

        def _parse_bin_location_id(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        bin_location_id = _parse_bin_location_id(d.pop("bin_location_id", UNSET))

        def _parse_serial_number_id(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        serial_number_id = _parse_serial_number_id(d.pop("serial_number_id", UNSET))

        quantity = d.pop("quantity", UNSET)

        traceability_request = cls(
            batch_id=batch_id,
            bin_location_id=bin_location_id,
            serial_number_id=serial_number_id,
            quantity=quantity,
        )

        return traceability_request
