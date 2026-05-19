from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define

from ..models.create_serial_number_failure_reason import CreateSerialNumberFailureReason

T = TypeVar("T", bound="CreateSerialNumberFailedItem")


@_attrs_define
class CreateSerialNumberFailedItem:
    """Single per-string failure block on a ``CreateSerialNumbersResponse``.
    Carries the input ``serial_number`` string and a ``reason`` code so
    the caller can react without inspecting status code or response
    body shape.
    """

    serial_number: str
    reason: CreateSerialNumberFailureReason

    def to_dict(self) -> dict[str, Any]:
        serial_number = self.serial_number

        reason = self.reason.value

        field_dict: dict[str, Any] = {}

        field_dict.update(
            {
                "serial_number": serial_number,
                "reason": reason,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        serial_number = d.pop("serial_number")

        reason = CreateSerialNumberFailureReason(d.pop("reason"))

        create_serial_number_failed_item = cls(
            serial_number=serial_number,
            reason=reason,
        )

        return create_serial_number_failed_item
