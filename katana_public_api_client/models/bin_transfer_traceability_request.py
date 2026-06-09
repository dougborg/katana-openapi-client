from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="BinTransferTraceabilityRequest")


@_attrs_define
class BinTransferTraceabilityRequest:
    """Batch/serial allocation supplied on a bin transfer row."""

    batch_id: int | None | Unset = UNSET
    serial_number_id: int | None | Unset = UNSET
    quantity: str | Unset = UNSET

    def to_dict(self) -> dict[str, Any]:
        batch_id: int | None | Unset
        if isinstance(self.batch_id, Unset):
            batch_id = UNSET
        else:
            batch_id = self.batch_id

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

        def _parse_serial_number_id(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        serial_number_id = _parse_serial_number_id(d.pop("serial_number_id", UNSET))

        quantity = d.pop("quantity", UNSET)

        bin_transfer_traceability_request = cls(
            batch_id=batch_id,
            serial_number_id=serial_number_id,
            quantity=quantity,
        )

        return bin_transfer_traceability_request
